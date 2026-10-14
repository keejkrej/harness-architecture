# Agent loops, context and memory

The common loop is simple: construct a request, stream a model result, execute its tool calls, append results and decide whether to continue. Most architectural differences appear in **who owns each transition**, what can interrupt it, how state is projected into the next request, and what the host can replace.

## Loop ownership

| Shape | Representative implementations | What the host gains; what it owns |
|---|---|---|
| Small in-memory loop | [Pi core](../harnesses/pi-core.md), [AI SDK ToolLoopAgent](../harnesses/ai-sdk.md), [mini-swe-agent](../harnesses/mini-swe-aider.md) | Straightforward embedding and inspection; persistence, lifecycle and policy often remain host responsibilities |
| Graph runtime and agents built on it | [Deep Agents](../harnesses/deepagents.md), [LangGraph](../harnesses/adjacent-frameworks.md) | Explicit state and graph checkpoints; needs deliberate checkpointer/runtime configuration |
| Workflow or task runtime owns transitions | [Pi Durable](../harnesses/pi-durable.md), [Eve](../harnesses/eve.md), [Mastra](../harnesses/mastra.md), [ADK workflows](../harnesses/google-adk.md) | Durable boundaries and waits; effect/replay contracts become part of tool design |
| Replaceable kernel plugin | [DeepSeek Harness](../harnesses/deepseek-harness.md) | Broad replacement of loop and services; plugin order, presets and deployment still form a substantial system |
| Product state machine / service | [OpenCode V2](../harnesses/opencode.md), [Kimi Code](../harnesses/kimi-code.md), [Goose](../harnesses/goose.md) | Multiple clients and rich lifecycle state; internal modularity is not always a stable external API |
| Product loop behind a protocol | [Codex](../harnesses/codex.md), [Grok Build](../harnesses/grok-build.md), [historical Claude Code](../harnesses/claude-code.md) | Reuse a complete agent from another UI; loop semantics remain owned by the product |
| Serializable agent over event history | [OpenHands](../harnesses/openhands.md) | Swap tools, context reducers, models and workspaces; conversation manager still owns run lifecycle |

Some implementations span categories. Flue adds its runtime and durable steps around a Pi Agent; an AI SDK WorkflowAgent differs from core ToolLoopAgent; an integrated product can export a small model library without exposing its full loop. Classify the actual package being embedded.

## Parallelism and steering are semantic choices

“Supports parallel tools” can mean a batch of independent calls, a graph superstep, or a scheduler that prevents conflicting filesystem access. Kimi declares file-access conflicts for scheduling. Grok uses per-path write locks. Deep Agents delegates tool execution to the LangChain/LangGraph graph. These choices affect observable ordering, cancellation and what survives when only one call fails. [Kimi tool scheduler](../harnesses/kimi-code.md), [Grok execution pipeline](../harnesses/grok-build.md), [Deep Agents graph boundary](../harnesses/deepagents.md).

Likewise, accepting a new user message does not imply immediately preempting a running tool. Pi exposes steering and follow-up queues. Codex has typed submissions, turn steering and task cancellation. OpenCode's inbox and execution drain separate session admission from turn processing. Hosts should define when newly accepted input becomes part of the model request, whether tool results from the previous turn remain valid, and what happens to queued input on restart. [Pi](../harnesses/pi-core.md), [Codex](../harnesses/codex.md), [OpenCode](../harnesses/opencode.md).

## Context is a projection, not the whole session

A useful separation is the **authoritative history**, the **current model-visible context**, and **large artifacts** retained elsewhere. Compaction changes the projection; it need not delete the event history. Tool-output spilling stores content outside the prompt; it is not by itself summarization or long-term memory.

| Technique | Examples and implications |
|---|---|
| Summary plus retained recent turns | Pi coding agent, Codex, Kimi, Gemini/Qwen and many products; cheaper active context, but information can be omitted |
| Structured compaction or provider compact endpoint | Codex and OpenAI-facing paths in several SDKs; useful provider feature with portability constraints |
| Filesystem-backed large tool output | Deep Agents, DeepSeek Harness, Pi Durable and others; model needs a discoverable path and tools to retrieve it |
| Branch/event-aware projection | Pi's session tree, Kimi wire branches, OpenHands event tree, OpenCode session events; resume must reconstruct the intended branch |
| Context recovery hints after compaction | Kimi explicitly points the model back to its on-disk event history; usefulness depends on retaining searchable artifacts |
| Replaceable context manager/middleware | Deep Agents backends/middleware, Strands managers, OpenHands condensers; more host control at the cost of correctness obligations |

Sources and exact triggers are in the context sections of [Pi coding agent](../harnesses/pi-coding-agent.md), [Codex](../harnesses/codex.md), [Kimi](../harnesses/kimi-code.md), [Deep Agents](../harnesses/deepagents.md), [DeepSeek Harness](../harnesses/deepseek-harness.md), [Strands](../harnesses/strands.md) and [OpenHands](../harnesses/openhands.md). Thresholds are version/model-dependent; comparing a single percentage across systems would hide their different token accounting and reserved-output rules.

## Instruction files, skills and memory

These terms overlap in product descriptions but have different lifecycles:

- **Project instructions** establish policy/context discovered from files such as AGENTS.md or CLAUDE.md. Discovery roots, hierarchy, trust and reload behavior are part of the harness.
- **Skills** package task instructions and sometimes scripts/resources. A catalog can expose only descriptions until a skill is selected, conserving context.
- **Session memory** records interaction history and enables resume.
- **Cross-session memory** stores or distills information for later conversations. It needs retention, provenance and deletion policy beyond a transcript.
- **Workspace artifacts** are files the agent reads/writes as task state. Whether they survive a worker or sandbox restart depends on the environment.

The Pi ecosystem keeps these responsibilities in separate layers. Eve's filesystem-oriented authoring, Deep Agents' backends, OpenHands' skill triggers, and product memory systems in Codex/Kimi/Grok choose different assembly points. None of the names alone establishes retrieval quality or memory correctness. [Pi layering](../harnesses/pi-core.md), [Eve](../harnesses/eve.md), [Deep Agents](../harnesses/deepagents.md), [OpenHands](../harnesses/openhands.md).

## Provider neutrality has several levels

Separate the model transport from the internal message representation, supported capabilities and authentication route. Pi-ai and AI SDK are explicit provider abstraction layers. Kimi uses its own Kosong abstraction. OpenCode V2 has its own model library and an AI SDK provider bridge. Qwen supports multiple providers while retaining a Gemini-shaped internal interface. Codex accepts Responses-compatible endpoints but remains Responses-shaped; multiple endpoint choices are not equivalent to native Anthropic/Gemini support. [Pi](../harnesses/pi-core.md), [AI SDK](../harnesses/ai-sdk.md), [Kimi](../harnesses/kimi-code.md), [OpenCode](../harnesses/opencode.md), [Gemini/Qwen](../harnesses/gemini-cli.md), [Codex](../harnesses/codex.md).

Reusing another product's OAuth credentials or API endpoint is not reusing its harness. Conversely, an ACP adapter that launches another agent delegates the full loop, even if the parent labels it a “provider.” This distinction is essential for a correct [dependency map](landscape.md).
