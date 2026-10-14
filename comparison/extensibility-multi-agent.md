# Extensions and multiple agents

Extensibility is about **which behavior can be replaced and with what authority**. Multi-agent support is about **how independently executing work is admitted, owned, observed and completed**. Counting plugins or subagent tools does not answer either question.

## Extension seams

| Seam | Representative systems | Architectural consequence |
|---|---|---|
| Callbacks/hooks around a fixed loop | Pi core, OpenAI Agents SDK, Strands, many product hooks | Small surface, but a callback may only observe or veto rather than replace the transition |
| Session/tool/UI extensions | Pi coding agent, Hermes, Grok, Crush | Rich customization around product conventions; permissions and callback authority still matter |
| Composable request/state middleware | Deep Agents, Mastra processors, Cline runtime/core | Explicit assembly points; order and state contracts can affect correctness |
| Replaceable kernel services | DeepSeek's Cordis plugins; OpenClaw harness/context-engine registrations | Whole subsystems can be replaced; plugin trust and compatibility become core responsibilities |
| Filesystem application conventions | Eve; skills/agent definitions across products | Easy authoring and deployment, with runtime rules governing discovery and execution |
| Graph/workflow composition | LangGraph, Mastra, ADK, CrewAI Flows, MAF | Branches, joins and waits are explicit; checkpoint/replay semantics differ by runtime |
| Tool/remote-agent protocols | MCP, ACP, A2A adapters across the inventory | Useful interoperability, but schema/protocol agreement does not imply shared permission, memory or recovery semantics |

Evidence and exact hook behavior: [Pi](../harnesses/pi-coding-agent.md), [OpenAI](../harnesses/openai-agents-sdk.md), [Strands](../harnesses/strands.md), [Hermes](../harnesses/hermes-agent.md), [Grok](../harnesses/grok-build.md), [Crush](../harnesses/crush.md), [Deep Agents](../harnesses/deepagents.md), [Mastra](../harnesses/mastra.md), [Cline](../harnesses/cline-kilo.md), [DeepSeek](../harnesses/deepseek-harness.md), [OpenClaw](../harnesses/openclaw.md), [Eve](../harnesses/eve.md), [ADK](../harnesses/google-adk.md), [Python frameworks](../harnesses/python-frameworks.md), [adjacent frameworks](../harnesses/adjacent-frameworks.md).

A hook that rewrites tool input can alter what an approval ought to cover. A plugin registering an arbitrary tool can bypass the normal filesystem executor entirely. A remote MCP server holds its own credentials and executes its own implementation. Review the sequence of hooks, policy evaluation and dispatch, not just whether all three exist.

## Different meanings of “multi-agent”

| Pattern | What happens | Examples to inspect |
|---|---|---|
| Agent as tool | Parent delegates a request and consumes a result | Deep Agents, Strands, OpenAI Agents SDK, many products |
| Handoff | Active conversational control moves to another configured agent | OpenAI Agents SDK; selected framework handoff models |
| Graph/workflow | Scheduler owns branches, joins, loops and/or messages | LangGraph, Mastra, ADK, MAF, CrewAI Flow/Crew combinations |
| Child session with mailbox/lifecycle | Child has identity, events, steering/cancellation and independent progress | Codex, Kimi, OpenCode, Hermes, Vibe, OpenClaw |
| Durable task tree | Parent/child ownership and waits are persisted execution concepts | Pi Durable, Eve and Flue's durable task/delegate facilities, with different effect contracts |
| Remote harness adapter | The child is another product/process implementing a protocol | ACP-backed providers and delegates in several products; OpenHands' ACP agent wrapper |
| Shared REPL/program state | Delegation is coupled to a programmable reasoning environment | Prime Agent's RLM-oriented daemon and Python authoring surface |

These labels describe mechanisms, not interchangeable APIs. A handoff does not necessarily start another process. An agent-as-tool may run synchronously in the same process. A durable child reference does not ensure that every child tool is replay-safe. [OpenAI](../harnesses/openai-agents-sdk.md), [Codex](../harnesses/codex.md), [Kimi](../harnesses/kimi-code.md), [OpenCode](../harnesses/opencode.md), [Vibe](../harnesses/mistral-vibe.md), [Pi Durable](../harnesses/pi-durable.md), [Flue](../harnesses/flue.md), [Eve](../harnesses/eve.md), [Prime](../harnesses/prime-agent.md).

## Five independent boundaries

**Context:** Does the child inherit all messages, a summary or only an explicit task? What artifacts remain accessible after compaction? Context isolation can improve specialization without changing filesystem or credential access.

**Scheduling:** Who enforces concurrency and depth limits, and what happens when a parent is cancelled? Compare a structured task tree to fire-and-forget background work. Strands' persisted sessions, for example, do not make its unfinished process-local background work durable. Vibe exposes specific child/depth/turn limits in the current unified runtime. [Strands](../harnesses/strands.md), [Vibe](../harnesses/mistral-vibe.md).

**Workspace:** Are files shared, copied, checked out into a worktree or placed in another sandbox? A worktree helps prevent accidental edits to the same checkout, but shared credentials and network identity remain. Hermes' child-worktree option, OpenClaw's workspace constraints and product worktree managers should be evaluated separately from context isolation. [Hermes](../harnesses/hermes-agent.md), [OpenClaw](../harnesses/openclaw.md), [safety](safety.md).

**Authority:** Whose approval can authorize the child? Can it broaden a parent's filesystem scope or spawn another harness with different defaults? OpenHands' external ACP wrapper is a concrete example where its ordinary confirmation policy does not govern every child request. [OpenHands](../harnesses/openhands.md).

**Recovery:** After a worker dies, can a parent rediscover the child, distinguish running from abandoned work and consume its result only once? Durable task identifiers, stored session records and a running coroutine are different ownership mechanisms. Evaluate the [state comparison](durability.md) alongside this one.

## Choosing composition deliberately

For fixed business processes, explicit graph/workflow state is easier to inspect than an unconstrained manager that repeatedly delegates. For exploratory coding, a child-session API with streaming, steering, cancellation and workspace control may fit better than a fixed DAG. For research into reasoning programs, Prime or DSPy provides a different abstraction from a coding-agent product. These are design judgments from the reviewed interfaces, not measured quality claims. [Prime](../harnesses/prime-agent.md), [DSPy](../harnesses/adjacent-frameworks.md).

The minimum useful evaluation is one interrupted parent, two children, a shared resource and a pending approval. Verify result attribution, cancellation, stale ownership, duplicate delivery and cleanup. No multi-agent throughput, coordination-quality or adversarial isolation benchmark was executed for this study.
