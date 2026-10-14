# <Name>

> One-paragraph verdict: what it is, which layer of the stack it occupies, and who should build on it.

| | |
|---|---|
| Repo(s) | `<owner/repo>` @ `<sha12>` |
| License | |
| Language(s) | |
| Size | tracked files / approx LOC of the harness core |
| Version at pin | |
| Release history | first public release → key milestones |
| Category | `llm-library` \| `harness-library` \| `agent-framework` \| `integrated-product` \| `hybrid` \| `execution-runtime` |

## 1. Layering & package map
A diagram (mermaid or ASCII) of the packages/crates/modules and how they depend on each other. Say what each layer owns.

## 2. Agent loop
Where the loop lives (file:line) and how a turn proceeds, step by step: streaming, stop conditions, steering/interrupts/queued messages, parallel tool calls, retries and error recovery.

## 3. Model / provider abstraction
Internal message model, provider adapters, reasoning/thinking handling, prompt caching, token and cost accounting.

## 4. Tool system
Definition API and schema technology, the built-in tool list, execution pipeline, output truncation, approvals.

## 5. Context management
System prompt assembly, project instruction files (AGENTS.md etc.), compaction and summarization strategy (trigger, algorithm), spill-to-disk, memory.

## 6. State, sessions & durability
Session storage format and location, resume/fork/branch, checkpointing and undo, crash recovery, durable-execution semantics.

## 7. Safety & sandboxing
Permission model, approval modes, OS or container sandboxes, network policy, secret handling.

## 8. Extensibility
Plugins, hooks (which events), skills, MCP (client/server), custom tools and commands, extension API surface, distribution.

## 9. Multi-agent
Subagents, handoffs, parallelism, worktree isolation, workflow engines.

## 10. Surfaces & integration
TUI/GUI, headless/print mode, SDKs, RPC/JSON protocols, ACP, HTTP server, IDE, web, deployment targets.

## 11. Observability & evals
Tracing (OTel?), telemetry, cost tracking, eval and benchmark harnesses.

## 12. Notable design decisions & trade-offs
The interesting, non-obvious choices and what they cost.

## 13. Scorecard
| Dimension | Score (1–5) | Rationale |
|---|---|---|
| Flexibility | | |
| Integration | | |
| Embeddability | | |
| Durability | | |
| Safety | | |
| Extensibility | | |
| Multi-agent | | |
| Provider neutrality | | |
| Maturity | | |
| Minimalism | | |

## 14. When to build on it / when not to

## 15. Evidence index
Key files with permalinks, and external sources (with dates).
