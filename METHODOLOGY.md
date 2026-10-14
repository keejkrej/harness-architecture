# Methodology

## Evidence hierarchy

1. **Source code** at the pinned commit in [`SOURCES.md`](SOURCES.md). This is the primary evidence. Architectural claims cite code as `path/to/file.ts:L10-L42` with a GitHub permalink to the pinned commit.
2. **In-repo docs**: READMEs, `docs/`, `AGENTS.md`, CHANGELOGs, and RFCs/ADRs.
3. **Official release notes and announcements** from GitHub releases and vendor blogs. These are used for dates and intent.
4. **Third-party write-ups**. These are used only for context and always attributed. A third-party claim is never stated as fact unless the code confirms it.

Nothing from the cloned repos was executed or installed. All reading was static.

## Scope and evidence limits

This is a source snapshot dated **2026-10-14**, not an exhaustive market census, adoption ranking, benchmark, or security audit. Selection began with the user's named systems, expanded to prominent public frameworks and coding agents, and followed implementation dependencies and successors. No usage or market-share estimates determine the scores.

The main chapters are deep dives; `harnesses/adjacent-frameworks.md` is an explicitly shallower breadth pass over general orchestration, retrieval and optimization frameworks. Grouped chapters separate their systems and use distinct matrix records where their behavior differs. A library, its product shell and a subprocess client are not interchangeable units. Read the record name and chapter scope before comparing scores.

The study focuses on open-source implementations. **Crush's FSL release, the proprietary historical Claude Code mirror, and the Claude SDK's closed runtime are labeled exceptions**, not open-source building blocks. The Claude snapshot is included at the user's request and is analyzed in prose with file citations; its source and prompts are not reproduced. A public repository or a permissive client wrapper alone does not make its runtime open source.

Source code outranks READMEs, design notes and familiar descriptions of earlier releases. A manifest's development version is not a published release; a feature behind a flag is not a default. Hosted services, external workflow engines and container providers are dependencies whose internal guarantees were not audited here. An absence claim means no implementation was identified in the reviewed scope, not proof about every downstream extension.

Static inspection cannot establish runtime correctness, throughput, token efficiency, security against attacks, real crash behavior, or API compatibility in a deployed application. Approximate LOC figures exclude files using each chapter's stated boundaries; some include inline tests, generated code or bundled schemas. They are orientation aids, not normalized complexity measurements. Release histories and popularity counts in inherited deep dives were not all independently re-collected during the continuation review.

## What counts as a "harness"

An **agent harness** is everything around the model that turns it into an agent: the loop, tool execution, context and memory management, state and persistence, safety controls, orchestration, and the extension and host surfaces. The systems studied fall along a spectrum:

| Category | Meaning | Examples |
|---|---|---|
| `llm-library` | Provider abstraction plus a primitive tool loop. You build the harness yourself. | AI SDK core, pi-ai |
| `harness-library` | An embeddable loop or harness with no product UI required; the amount of context/state machinery varies | pi-agent-core, Pi Durable, Deep Agents, Strands |
| `agent-framework` | Builds and deploys agents, usually with workflows, memory and deployment targets | Eve, Mastra, OpenAI Agents SDK, ADK |
| `integrated-product` | A complete end-user agent (CLI/TUI/IDE/app) whose harness is tightly coupled to the product | Codex, Grok Build, Kimi Code, historical Claude Code |
| `hybrid` | A product deliberately split into a reusable harness and a product shell | Pi coding agent, OpenCode V2, OpenHands, Goose |
| `execution-runtime` | An execution/sandbox substrate with no model loop; included as adjacent infrastructure, not a harness candidate | Rivet AgentOS |

Integration and flexibility both count as merits. The scorecard rates them separately.

## Dimensions (each harness doc covers all of them)

1. **Identity & provenance**: license, language, size, versions, release history
2. **Layering & package map**: what the layers are and how the packages depend on each other
3. **Agent loop**: turn structure, streaming, stop conditions, steering/interrupt, parallel tool calls, retries
4. **Model/provider abstraction**: message model, provider coverage, reasoning/thinking, prompt caching, cost
5. **Tool system**: definition API, schemas, built-ins, execution, output truncation
6. **Context management**: prompt assembly, project instruction files, compaction and summarization, spill-to-disk
7. **State, sessions & durability**: storage format, resume/fork/branch, checkpoints, crash recovery
8. **Safety & sandboxing**: permission model, approvals, OS or container sandboxes, network policy
9. **Extensibility**: plugins, hooks, skills, MCP, custom tools/commands, extension API
10. **Multi-agent**: subagents, handoffs, parallelism, worktrees, workflows
11. **Surfaces & integration**: TUI, headless mode, SDK, RPC, ACP, HTTP server, IDE, web, deployment targets
12. **Observability & evals**: tracing, telemetry, eval harnesses

## Scorecard rubric (1–5)

| Score | 1 | 3 | 5 |
|---|---|---|---|
| **Flexibility**: how much can be reshaped without forking | Fixed product; settings only | Plugins/hooks/SDK, but the loop is fixed | Every layer can be replaced or composed |
| **Integration**: batteries included end-to-end | Bare loop | Tools, sessions and a CLI | Full product: UI surfaces, sandbox, auth, cloud |
| **Embeddability**: use in-process as a library | CLI only | SDK that wraps a subprocess or server | First-class in-process library with a stable API |
| **Durability**: persistence, resume, recovery | In-memory only | Session files and resume | Durable execution with checkpoint replay and crash recovery |
| **Safety**: sandboxing and permissions | None | Approval prompts and allowlists | OS-level sandbox, policy engine and network control |
| **Extensibility**: plugins, hooks, skills, MCP | None | MCP and custom tools | Rich extension API, hooks, skills and plugin distribution |
| **Multi-agent** | None | Subagent tool | Parallel orchestration, handoffs, worktrees, workflows |
| **Provider neutrality** | Single vendor | A few providers or OpenAI-compatible | Broad unified provider abstraction |
| **Maturity** | Preview or RC | Active releases and documented use | Stable versioned API, established releases and compatibility practices |
| **Minimalism**: a small, legible core | Very large or complex | Moderate | A core you can read in an afternoon |

Scores are relative judgments made from the code, not benchmarks. Each chapter gives its rationale. A source-review pass challenged load-bearing claims; it did not prove every sentence. `null` / `?` means unassessable, not absent. Integration, minimalism and flexibility intentionally trade off; the matrix does not add them into a misleading overall ranking. Safety rates available controls, not demonstrated resistance to attacks. Embeddability rates the harness execution boundary, not merely the existence of a package called SDK.

Feature cells are `yes`, `partial`, `no` or `unknown`: confirmed in the stated scope; qualified/optional/host-dependent; not provided in that scope; or not established. The legacy data key `durable_resume` deliberately remains a coarse discovery field. It does **not** mean durable execution: use the [durability analysis](comparison/durability.md) and state summaries to distinguish transcript loading, turn recovery, checkpoint replay and external side effects. Similarly, approval rules, a git worktree, a language interpreter and an OS sandbox are separate mechanisms.

## Process

1. Clone every repo at a pinned commit (see `SOURCES.md`).
2. Write the deep dives from [`harnesses/_TEMPLATE.md`](harnesses/_TEMPLATE.md), and identify additional systems for a bounded breadth pass.
3. Challenge load-bearing claims against source: loop ownership, embedding, recovery, side effects, permissions, licensing and dependency edges. Record actual sampled checks and unresolved questions in `data/*.json`; do not claim exhaustive semantic verification.
4. Mechanically validate every recognized GitHub blob/tree permalink against the manifest, tracked paths and line bounds in the pinned clones. Modified worktree paths are checked through the committed git blob. Validate local links, record fields and unique slugs separately. These checks establish referential integrity, not that a citation proves the adjacent claim.
5. Write cross-cutting synthesis in `comparison/`, generate the matrix, check completeness and run an independent final review. The [verification report](comparison/verification.md) records the completed checks and limitations.

## Reproduction

Clone repositories at the SHAs in [`SOURCES.md`](SOURCES.md) into a sibling `harness-sources/` directory, then run:

```text
python scripts/validate_research.py
python scripts/build_matrix.py --check
```

Without source clones, `python scripts/validate_research.py --skip-source-files` checks records, local links and pin consistency only. CI uses this lighter check plus matrix freshness; the full path/line validation is a local research check. Generate the matrix with `python scripts/build_matrix.py` after editing records.
