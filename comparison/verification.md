# Verification and limits

The study combines static source investigation, sampled adversarial review and mechanical integrity checks. These are different forms of evidence. A valid source permalink proves that the file and line range exist at a commit; it does not prove the interpretation beside it.

## Scope

The snapshot includes **54 pinned source repositories, 30 research chapters and 53 distinct comparison records**. The main deep dives are substantially longer than the bounded eight-framework breadth chapter. Several chapters contain more than one library, language implementation, product layer or historical predecessor; those records are not 53 interchangeable end-user products.

All inspected clones are listed in [SOURCES.md](../SOURCES.md). Research involved source, manifests, tests, design notes, changelogs and selected first-party release/announcement material. No cloned code was imported, installed, built or executed. No provider calls, sandbox attack tests, performance benchmarks or crash-injection experiments were run.

## Semantic review actually performed

The original detailed drafts were preserved, then checked against the pinned implementation at load-bearing boundaries: loop ownership, public embedding APIs, durable state, crash ambiguity, default policy, execution confinement, version changes, license and implementation lineage. This was targeted review, not exhaustive independent verification of every sentence.

| Review group | Recorded scope |
|---|---|
| Ten initial library/harness chapters | 80 explicit source spot-check groups; corrections and unresolved issues recorded in each JSON file |
| Nine original product/SDK groups | 42 explicit continuation-review claim groups, followed by independent review of selected claims, scorecards and metadata |
| Five additional product chapters | Researcher checklists plus independent samples of current package boundaries, Vibe runtime/recovery, Hermes scheduling and Crush license |
| Five additional framework chapters | Researcher source checklists for loops, state, permissions, defaults, adapters and scope; no claim of a second exhaustive review |
| Eight adjacent frameworks | 64 bounded claim groups covering identity, loop, tool, state, safety, orchestration and embedding/migration boundaries |
| Seven cross-cutting synthesis chapters | Independent consistency review against chapters and targeted source reads; recommendations are architectural inferences |

Claim groups differ in granularity and may overlap; these counts are not a count of all facts verified. [Structured metadata](../data/README.md) retains the actual checklists and limitations. Approximate source-size totals, every release milestone and dynamic popularity figures in inherited deep dives were not independently reconstructed. They do not support a popularity ranking or an overall winner.

## Material corrections from review

| Area | Corrected interpretation |
|---|---|
| Pi | Durable uses Pi-ai directly, not current agent-core; v1 core remains in memory; safe/unsafe tool recovery policies limit replay |
| AI SDK | WorkflowAgent.generate exists at the pin despite a stale design note; core has no durable store |
| Mastra | DurableAgent's running snapshots depend on recovery/custom policy or orderly shutdown; the durable flag alone is insufficient |
| Flue/Eve | A recorded step or approval does not close the effect-before-result crash window |
| OpenCode | V2 has true embedding, but its default database is in memory; restart recovery is explicitly at-least-once and requires storage ownership |
| OpenHands | Server orphan handling is not a general at-most-once guarantee; later SDK continuation can execute unmatched actions |
| OpenAI Agents SDK | Local protection is backend-specific; duplicate agent names can use stable identities; approval/session-write reconciliation is not a universal execution guarantee |
| Kimi | Default file-path checks reject relative escapes but permit absolute outside-workspace paths; sensitive-file checks vary by tool |
| Gemini | Windows network-disabled mode attempts throttling and continues after setup failure; this is not equivalent to network isolation |
| Product lineage | Cline now has public Agents/Core layers; Kilo declares OpenCode lineage; OpenClaw's incorporated Pi code differs from a current Pi core package dependency |
| Vibe | Unified Rust/Python runtime is default and journals effects; legacy ADR claims do not describe that path |
| Broader frameworks | Agno's typed tools checkpoint mode is rejected by implementation; AutoGen/Semantic Kernel successor notices are not dependencies; smolagents remote code execution rejects managed agents |
| Scope/licensing | Rivet AgentOS has no model loop; current Letta Code is TypeScript; Crush's FSL and historical Claude's proprietary code are explicit exceptions |

The corrected chapter and record are the authority for exact scope and source references. Review also removed unsupported comparative superlatives, fixed source-line ranges and directory links, and escaped pipes that broke Markdown tables.

## Mechanical checks

`scripts/validate_research.py` verifies:

- Every manifest clone's HEAD matches its pin in the full local check.
- Recognized GitHub blob/tree references use the manifest's full commit, point to tracked paths, and stay within file line bounds when a line fragment is present.
- Unlisted source repositories and different/moving commits are errors, rather than silently accepted evidence.
- Inline and reference-definition local link targets exist; fenced code blocks and table column counts are structurally consistent.
- Records contain the required fields, valid feature/score values, dimension summaries and unique slugs; every chapter has a record.

`scripts/build_matrix.py --check` independently verifies that the committed matrix is exactly reproducible from the records. It rejects duplicate slugs and empty input. CI runs the clone-free validator and matrix freshness check; full source-path/line validation is performed locally.

The completed local audit found **5,058 citation occurrences, 4,764 unique source references and 2,053 source files with line-range checks**, with no integrity errors. These counts include repeated citations and do not count distinct verified claims. A pre-existing modification in one historical Claude clone was left untouched; the validator reads the pinned git blob for any modified cited path. That warning concerns local checkout provenance, not a failure of the committed citations.

Negative-fixture checks also confirmed rejection of an unknown source repository, a moving commit, a missing local reference target, a malformed table and duplicate record slugs. These fixtures were temporary and removed after the check.

## What these checks do not establish

The checker does not fetch every external web link, validate rendered heading anchors, prove Mermaid rendering, parse arbitrary Markdown as a full CommonMark engine, verify that every source range supports its adjacent sentence, or establish cross-language/backend parity. Full source validation requires the sibling clones; the CI mode deliberately cannot establish file existence or line bounds upstream.

The study does not prove compatibility with a deployed API, successful runtime recovery, security against adversarial tools/prompts, summarization quality, correctness of a hosted backend, provider feature parity or production operational maturity. Package versions and an available feature are not evidence that a default deployment enables it.

The proposed [recovery experiments](durability.md#what-to-test-before-choosing-a-runtime) and [selection trial](recommendations.md#a-bounded-selection-experiment) are follow-up work for choosing an implementation, not experiments already completed here.
