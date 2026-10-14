# State, resume and durable execution

The consequential question is **what happens after the process dies between a tool changing the world and recording its result**. A saved chat transcript, a replayable event stream and an execution journal answer different parts of that question. This comparison describes mechanisms observed in source; no crash-injection experiments were run.

## Five distinct guarantees

| Mechanism | What survives | What it does not establish |
|---|---|---|
| Conversation persistence | Messages and completed tool results | Recovery of an unfinished call |
| Filesystem snapshot | Selected workspace state | Reversal of network requests, database writes or payments |
| Turn recovery | Enough intent to continue an interrupted turn | Whether an external effect already happened |
| Execution checkpoint/replay | Recorded transitions or completed step results | Exactly-once effects in another system |
| External idempotency or transaction | A stable effect identity, checked by the effect owner | Correctness of unrelated tools or unrecorded steps |

The first four are frequently described as “durable.” Only the actual recovery protocol tells you what can repeat. The matrix's `durable_resume` field is a discovery aid; it collapses these mechanisms and must not be used as a guarantee.

## What the implementations actually do

| System / scope | Persistence and recovery unit | Boundary to account for |
|---|---|---|
| [Pi core](../harnesses/pi-core.md) | In-memory Agent state | Host supplies persistence; v1 moved the experimental durable harness out of core |
| [Pi coding agent](../harnesses/pi-coding-agent.md) | Append-only JSONL tree, branch/fork and compaction entries | Resume reconstructs context; unfinished tools are not checkpoint-replayed |
| [Pi Durable](../harnesses/pi-durable.md) | Transactional task/checkpoint state plus transcripts and documents; generation, compaction and tool tasks | Safe tools can repeat; unsafe tools are not blindly retried; abandon policies and host single-writer assumptions matter |
| [Flue](../harnesses/flue.md) | Conversation log, submission ledger and optional named durable steps | Ordinary interrupted tool calls can have unknown outcomes; an effect can happen before its step result is recorded |
| [Eve](../harnesses/eve.md) | Workflow-owned sessions and turns, durable waits and step boundaries | Workflow retry can repeat a tool's effect; approval records authorize actions but do not deduplicate them |
| [AI SDK core](../harnesses/ai-sdk.md) | No built-in store | Core is in-memory; optional WorkflowAgent is a different scope with an external runtime |
| [DeepSeek Harness](../harnesses/deepseek-harness.md) | Versioned append log, durable inbox and write-ahead intent/checkpoints | Repairs interrupted work as unknown outcomes rather than providing general deterministic work replay |
| [Deep Agents](../harnesses/deepagents.md) | LangGraph checkpoints when a checkpointer is configured | Default `None` does not add cross-invocation persistence; the SDK is not a worker scheduler |
| [Mastra](../harnesses/mastra.md) | Workflow snapshots and optional durable-agent recovery | `durable: true` alone does not mean running snapshots persist: recovery policy, custom snapshot policy or shutdown handling controls that |
| [Strands](../harnesses/strands.md) | Session snapshots and persisted interrupt state | A checkpoint marker alone is not the conversation snapshot, nor an automatic crash-resume daemon |
| [OpenAI Agents SDK](../harnesses/openai-agents-sdk.md) | Session history, serializable RunState, sandbox snapshot/reattach | Session history differs from approval continuation; general durable execution is delegated to Temporal/DBOS/Restate/Dapr integrations |
| [OpenCode V2](../harnesses/opencode.md) | SQLite events/projections, execution claims, bounded restart recovery, git-tree snapshots | Recovery is explicitly at-least-once; replaying session events is not replaying arbitrary tool execution |
| [Codex](../harnesses/codex.md) | Rollout JSONL, state DB, storage barriers and supported turn suspension/recovery | Recovery is turn-granular and restricted by task/environment state; no exactly-once tool journal |
| [Grok Build](../harnesses/grok-build.md) | Interactive session JSONL and interruption markers; separately, journaled Rhai workflows | A workflow can replay recorded host results; that does not make the interactive model turn replayable |
| [Kimi Code](../harnesses/kimi-code.md) | Per-agent wire logs, branching records, tail repair and file-history blobs | Transcript recovery does not replay an unfinished model/tool call; file history is not a general filesystem restore contract |
| [Goose](../harnesses/goose.md) | SQLite conversation/effect state; approval continuation reconstructed from persisted messages | Resume logic recognizes pending/unapplied approvals, not every arbitrary mid-inference or mid-tool crash |
| [OpenHands](../harnesses/openhands.md) | File-per-event tree, autosaved base state and server leases | Server recovery marks a failed run and records an orphan error; later SDK continuation can execute unmatched actions |
| [Historical Claude Code](../harnesses/claude-code.md) | JSONL parent chains, sidechains and interrupted-turn continuation | Historical proprietary snapshot; no deterministic effect replay; filesystem rewind only covers tracked edits |

The additional chapters cover distinct mechanisms in [Google ADK](../harnesses/google-adk.md), [Mistral Vibe](../harnesses/mistral-vibe.md), [Pydantic and Microsoft harnesses](../harnesses/python-frameworks.md), and [fx](../harnesses/experimental.md). Do not infer their current behavior from older package names or architecture diagrams.

## Pi v1 is a meaningful architectural split

Pi core's loop and Pi Durable are different foundations. The durable package calls **pi-ai directly** and models generation, tools and compaction as tasks. It is not persistence added around `Agent` from pi-agent-core. The coding agent remains another consumer, with its own JSONL session model. This separation gives a host a choice between a small callback/event loop and a transactional task model; it also means extensions and recovery expectations do not transfer automatically. See the [v1 release analysis](../harnesses/pi-core.md) and [durable task protocol](../harnesses/pi-durable.md).

Pi Durable's explicit safe/unsafe tool policy is particularly useful design evidence. A framework can know that a call was admitted without knowing whether an external side effect completed. Keeping “unknown” as a first-class outcome is often more honest than retrying everything or claiming everything resumes. Safe/replayable is a tool-author contract, not a proof supplied by the runtime.

## Events, execution and ownership

OpenCode's source explicitly describes its recovery as at-least-once and requires exclusive ownership of the database when sweeping orphaned claims. Its embedded host also defaults to an **in-memory database**. Persistent recovery therefore requires both storage configuration and correct process ownership; importing the SDK is insufficient. [Restart ownership contract](https://github.com/anomalyco/opencode/blob/8ffbcc2c81d1ff558618137204c36954797d7a6f/packages/core/src/session/execution/restart.ts#L35-L61), [embedded host defaults](https://github.com/anomalyco/opencode/blob/8ffbcc2c81d1ff558618137204c36954797d7a6f/packages/sdk/src/internal/host.ts#L30-L56).

Goose demonstrates a different recovery shape. A persisted approval can park work without keeping a coroutine alive. On load, its resume routine looks for pending confirmations or an unapplied persisted answer and returns nothing otherwise. This is useful, concrete resumability, but it is narrower than a universal durable task engine. [Approval continuation](https://github.com/aaif-goose/goose/blob/9686d674000a5fbb8139214863289e4820714771/crates/goose/src/agents/agent.rs#L712-L765).

OpenHands shows why “does not automatically retry” should not be renamed “at-most-once.” The server inserts an error for the first orphaned action, while the in-process agent executes unmatched actions when stepped again. A tool may already have made a remote change before the missing observation. The recovery path does not establish an end-to-end execution guarantee. [Server recovery](https://github.com/OpenHands/software-agent-sdk/blob/95cb37b7f04ff281e92bfb3c3fc66573db2df38a/openhands-agent-server/openhands/agent_server/event_service.py#L1328-L1371), [pending actions](https://github.com/OpenHands/software-agent-sdk/blob/95cb37b7f04ff281e92bfb3c3fc66573db2df38a/openhands-sdk/openhands/sdk/agent/agent.py#L714-L723).

## What to test before choosing a runtime

These are proposed acceptance experiments, **not results of this study**:

1. Kill the worker after a tool performs a remote write but before its result is persisted. Inspect whether recovery repeats, marks unknown, abandons or requires intervention.
2. Kill it during parallel tools. Verify that completed siblings survive and unmatched results cannot become paired with the wrong call.
3. Persist an approval, restart, and answer twice. Verify scoping, expiry and whether an answer can authorize altered arguments.
4. Run two workers against one store. Verify leases, fencing and whether stale workers can still perform effects after losing ownership.
5. Upgrade code between suspension and recovery. Verify checkpoint/schema migrations and workflow replay compatibility.
6. Restore a conversation without its sandbox, credentials or workspace. Determine which state can actually be reconstructed.

For business effects, carry an idempotency key across the harness boundary and let the destination enforce it. For file operations, decide whether recovery should restore a snapshot, inspect current state, or stop for reconciliation. These are application policies even when the harness supplies the checkpoint machinery.
