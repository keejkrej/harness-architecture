"""Validate research records, Markdown links, and citations against pinned clones.

This checks referential integrity, not whether a cited line proves a claim.
No code from the researched projects is imported or executed.
"""

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from build_matrix import CATEGORY_ORDER, DIM_KEYS, FEATURE_KEYS, SCORE_KEYS

ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROW = re.compile(r"^\| `([^`]+)` \| \[([^\]]+)\]\([^)]*\) \|.*?https://github.com/[^/]+/[^/]+/tree/([0-9a-f]{40})", re.M)
GITHUB = re.compile(r"https://github\.com/([^/]+/[^/]+)/(blob|tree)/([^/\s]+)/([^\s<>\)`]+)")
LINK = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)")
REFERENCE = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*(\S+)", re.M)


def git(directory, *args):
    result = subprocess.run(["git", "-C", str(directory), *args], capture_output=True, check=True)
    return result.stdout.decode("utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=ROOT.parent / "harness-sources")
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--skip-source-files", action="store_true", help="Check records, links and pinned URLs without requiring local source clones")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    errors = []
    warnings = []
    manifest = SOURCE_ROW.findall((ROOT / "SOURCES.md").read_text(encoding="utf-8"))
    if not manifest:
        errors.append("No pinned source rows found")
    repos = {}
    for directory, repo, sha in manifest:
        clone = args.sources / directory
        if args.skip_source_files:
            repos[repo.lower()] = (clone, sha, None, set())
            continue
        try:
            head = git(clone, "rev-parse", "HEAD").strip()
            if head != sha:
                errors.append(f"{directory}: HEAD {head} differs from pin {sha}")
                continue
            dirty = set(git(clone, "diff", "HEAD", "--name-only", "-z").split("\0")) - {""}
            if dirty:
                warnings.append(f"{directory}: {len(dirty)} modified paths; their citations read pinned git blobs")
            tracked = set(git(clone, "ls-files", "-z").split("\0"))
            repos[repo.lower()] = (clone, sha, tracked, dirty)
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f"{directory}: cannot verify clone ({exc})")
    counts = Counter()
    unique_citations = set()
    lengths = {}
    for doc in sorted(ROOT.rglob("*.md")):
        if ".git" in doc.parts or doc.name == "_TEMPLATE.md":
            continue
        body = doc.read_text(encoding="utf-8-sig")
        rel = doc.relative_to(ROOT).as_posix()
        fences = re.findall(r"^\s*```", body, re.M)
        if len(fences) % 2:
            errors.append(f"{rel}: unclosed code fence")
        in_fence = False
        table_columns = None
        for line_number, content in enumerate(body.splitlines(), 1):
            if content.lstrip().startswith("```"):
                in_fence = not in_fence
                table_columns = None
            if in_fence:
                continue
            if not content.startswith("|"):
                table_columns = None
                continue
            columns = len(re.split(r"(?<!\\)\|", content)) - 2
            if table_columns is None:
                table_columns = columns
            elif columns != table_columns:
                errors.append(f"{rel}:{line_number}: table has {columns} columns; expected {table_columns} (escape pipes inside cells)")
        for match in GITHUB.finditer(body):
            repo, kind, sha, tail = match.groups()
            line = body[:match.start()].count("\n") + 1
            label = f"{rel}:{line}"
            if repo.lower() not in repos:
                errors.append(f"{label}: source repo {repo} is absent from SOURCES.md")
                continue
            clone, pin, tracked, dirty = repos[repo.lower()]
            if not re.fullmatch(r"[0-9a-f]{40}", sha) or sha != pin:
                errors.append(f"{label}: unpinned or different commit {repo}@{sha}")
                continue
            parsed = urlsplit("https://example.invalid/" + tail)
            path = unquote(parsed.path.lstrip("/")).rstrip("/")
            if ".." in Path(path).parts:
                errors.append(f"{label}: unsafe source path {path}")
                continue
            unique_citations.add(match.group())
            counts[rel] += 1
            if tracked is None:
                continue
            if kind == "tree":
                if path not in tracked and not any(p.startswith(path + "/") for p in tracked):
                    errors.append(f"{label}: missing tree {repo}/{path}")
                continue
            if path not in tracked:
                errors.append(f"{label}: missing blob {repo}/{path}")
                continue
            if not parsed.fragment:
                continue
            span = re.fullmatch(r"L(\d+)(?:-L?(\d+))?", parsed.fragment)
            if not span:
                continue  # Heading fragments need rendered-source semantics.
            cache_key = (repo, path)
            if cache_key not in lengths:
                source = git(clone, "show", f"{pin}:{path}").encode("utf-8") if path in dirty else (clone / path).read_bytes()
                lengths[cache_key] = len(source.splitlines())
            start, end = int(span[1]), int(span[2] or span[1])
            if not (1 <= start <= end <= lengths[cache_key]):
                errors.append(f"{label}: range {parsed.fragment} outside {repo}/{path} ({lengths[cache_key]} lines)")
        if not args.source_only:
            for match in [*LINK.finditer(body), *REFERENCE.finditer(body)]:
                target = unquote(match[1].strip("<>"))
                if urlsplit(target).scheme or target.startswith("#"):
                    continue
                path = target.split("#", 1)[0]
                if path and not (doc.parent / path).exists():
                    errors.append(f"{rel}:{body[:match.start()].count(chr(10)) + 1}: missing local link {target}")
    records = []
    if not args.source_only:
        for path in sorted((ROOT / "data").glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
                if not payload.get("records"):
                    errors.append(f"{path.name}: no records")
                for record in payload.get("records", []):
                    records.append(record)
                    slug = record.get("slug", path.name)
                    required = ("slug", "name", "vendor", "repo", "language", "license", "version", "category", "one_liner", "doc_path", "builds_on", "used_by", "key_insights")
                    for key in required:
                        if key not in record:
                            errors.append(f"{slug}: missing {key}")
                    if record.get("category") not in CATEGORY_ORDER:
                        errors.append(f"{slug}: invalid category")
                    if not (ROOT / record.get("doc_path", "missing")).is_file():
                        errors.append(f"{slug}: missing chapter")
                    for key, _ in FEATURE_KEYS:
                        if record.get("features", {}).get(key) not in {"yes", "partial", "no", "unknown"}:
                            errors.append(f"{slug}: invalid/missing feature {key}")
                    for key, _ in SCORE_KEYS:
                        value = record.get("scores", {}).get(key)
                        if key not in record.get("scores", {}) or (value is not None and (type(value) is not int or not 1 <= value <= 5)):
                            errors.append(f"{slug}: invalid/missing score {key}")
                    for key, _ in DIM_KEYS:
                        if not record.get("dims", {}).get(key):
                            errors.append(f"{slug}: missing dimension {key}")
            except (ValueError, TypeError, KeyError) as exc:
                errors.append(f"{path.name}: {exc}")
        duplicates = [k for k, v in Counter(r.get("slug") for r in records).items() if v > 1]
        if duplicates:
            errors.append(f"Duplicate record slugs: {duplicates}")
        represented = {r.get("doc_path") for r in records}
        for chapter in (ROOT / "harnesses").glob("*.md"):
            if chapter.name != "_TEMPLATE.md" and chapter.relative_to(ROOT).as_posix() not in represented:
                errors.append(f"{chapter.name}: no comparison record")
    report = {"source_file_validation": not args.skip_source_files, "source_repositories": len(repos), "citation_occurrences": sum(counts.values()), "unique_citations": len(unique_citations), "source_files_with_line_checks": len(lengths), "records": len(records), "citations_by_document": dict(counts), "errors": errors, "warnings": sorted(set(warnings))}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "citations_by_document"}, indent=2, ensure_ascii=False))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
