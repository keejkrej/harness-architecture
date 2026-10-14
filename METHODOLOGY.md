# Methodology

## Evidence hierarchy

1. **Source code** at the pinned commit in [`SOURCES.md`](SOURCES.md). This is the primary evidence. Architectural claims cite code as `path/to/file.ts:L10-L42` with a GitHub permalink to the pinned commit.
2. **In-repo docs**: READMEs, `docs/`, `AGENTS.md`, CHANGELOGs, and RFCs/ADRs.
3. **Official release notes and announcements** from GitHub releases and vendor blogs. These are used for dates and intent.
4. **Third-party write-ups**. These are used only for context and always attributed. A third-party claim is never stated as fact unless the code confirms it.

Nothing from the cloned repos was executed or installed. All reading was static.

## What counts as a "harness"

An **agent harness** is everything around the model that turns it into an agent: the loop, tool execution, context and memory management, state and persistence, safety controls, orchestration, and the extension and host surfaces. The systems studied fall along a spectrum:

| Category | Meaning | Examples |
|---|---|---|
| `llm-library` | Provider abstraction plus a primitive tool loop. You build the harness yourself. | AI SDK core, pi-ai |
| `harness-library` | An embeddable, opinionated harness (tools, compaction, sessions) with no product UI required | pi-agent-core, Deep Agents, Flue, Strands |
| `agent-framework` | Builds and deploys agents, usually with workflows, memory and deployment targets | Eve, Mastra, OpenAI Agents SDK, ADK |
| `integrated-product` | A complete end-user agent (CLI/TUI/IDE/app) whose harness is tightly coupled to the product | Codex, OpenCode, Grok Build, Kimi Code, Claude Code |
| `hybrid` | A product deliberately split into a reusable harness and a product shell | Pi coding agent, DeepSeek Harness, Goose |

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
| **Maturity** | Preview or RC | Active 0.x with real users | Stable 1.x+ with a versioned API and large user base |
| **Minimalism**: a small, legible core | Very large or complex | Moderate | A core you can read in an afternoon |

Scores are relative judgments made from the code, not benchmarks. Each harness doc justifies its scores, and an adversarial verifier re-checked them against the source.

## Process

1. Clone every repo at a pinned commit (see `SOURCES.md`).
2. Have one researcher agent per harness read the code and write `harnesses/<slug>.md` from [`harnesses/_TEMPLATE.md`](harnesses/_TEMPLATE.md).
3. Have one adversarial verifier per doc resolve every citation, try to refute the main claims against the code, and fix errors in place.
4. Run cross-cutting synthesis per dimension (`comparison/`) and build the matrix and scorecard.
5. Run a completeness critique, then close the gaps it found.
