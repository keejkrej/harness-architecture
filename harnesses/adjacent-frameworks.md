# Adjacent frameworks and runtime foundations

**Breadth tier, source snapshot 2026-10-14.** These eight systems broaden the comparison beyond coding harnesses. Each section inspects the pinned implementation at its main loop, state, tool and embedding boundaries; it is not the same exhaustive package tour as the dedicated chapters. No cloned code was executed, installed, built or imported. Popularity and vendor benchmark claims are not used as evidence.

Scores use the shared rubric and describe the stated library/runtime scope. A high durability score requires the named storage/host configuration; it never implies exactly-once external effects. `partial` features in the data records identify optional integrations, narrower APIs or application-owned implementation. Where this review did not establish a feature, the data uses `unknown` rather than inferring absence.

| System | Audited version / source status | Architectural role |
|---|---|---|
| [LangGraph](#langgraph) | 1.2.15 | Graph execution/checkpoint substrate |
| [CrewAI](#crewai) | 1.15.28 | Crews plus event-driven Flows |
| [Agno](#agno) | 3.1.3 | SDK plus AgentOS server runtime |
| [LlamaIndex core agents](#llama-index) | 0.14.25 | Retrieval/memory plus agent workflows |
| [Haystack](#haystack) | 3.5.0-rc0 | Component pipelines plus agent harness features |
| [DSPy](#dspy) | 3.4.0 | Optimizable model programs and optional loops |
| [AutoGen](#autogen) | Python Core/AgentChat 0.7.5 (maintenance mode) | Message runtime and teams; maintenance mode |
| [Semantic Kernel](#semantic-kernel) | Python 1.45.0; vendor directs users to MAF | Plugin/service SDK; MAF successor transition |

<a id="langgraph"></a>
## LangGraph

LangGraph is a **runtime foundation**, particularly relevant when comparing Pi Durable with libraries that inherit their execution engine. The pinned Python package is **1.2.15, MIT**; LangGraph.js is a separate implementation and was not audited here. This chapter scores the Python library, not LangSmith hosting. Its manifest and the compiled-graph API expose that boundary clearly. [Package metadata](https://github.com/langchain-ai/langgraph/blob/36bf3887f074f2b05f42409c8a67e3a33ed1d1ba/libs/langgraph/pyproject.toml), [StateGraph and compilation](https://github.com/langchain-ai/langgraph/blob/36bf3887f074f2b05f42409c8a67e3a33ed1d1ba/libs/langgraph/langgraph/graph/state.py).

A `StateGraph` describes nodes, edges, state channels and reducers. Compilation produces a runnable graph. The underlying `Pregel` engine follows plan → parallel execution → channel update supersteps: writes made during a step become visible in the next step. This is a reusable scheduler for arbitrary application functions, not a hard-coded model/tool conversation loop. Conditional edges and subgraphs let a host implement routing, handoffs, parallel branches or an entirely non-agent workflow. Model access and tool definitions are supplied by nodes or higher layers. [Pregel runtime](https://github.com/langchain-ai/langgraph/blob/36bf3887f074f2b05f42409c8a67e3a33ed1d1ba/libs/langgraph/langgraph/pregel/main.py).

Persistence is a **configured contract**. `compile(checkpointer=None)` is a valid default; cross-process durability needs a persistent saver and a host that resumes work. `BaseCheckpointSaver` distinguishes checkpoint state from task-level pending writes. SQLite and Postgres are separate packages, while in-memory savers are useful for development but do not survive process loss. These mechanisms should not be credited as an included hosted worker/control plane. [Checkpoint contract](https://github.com/langchain-ai/langgraph/blob/36bf3887f074f2b05f42409c8a67e3a33ed1d1ba/libs/checkpoint/langgraph/checkpoint/base/__init__.py), [SQLite package](https://github.com/langchain-ai/langgraph/blob/36bf3887f074f2b05f42409c8a67e3a33ed1d1ba/libs/checkpoint-sqlite/pyproject.toml), [Checkpoint coordination](https://github.com/langchain-ai/langgraph/blob/36bf3887f074f2b05f42409c8a67e3a33ed1d1ba/libs/langgraph/langgraph/pregel/_loop.py).

The `interrupt()` contract is especially important for approval workflows: resuming **restarts the node from its beginning**, and resume values match interrupts within the task. Effects before the interrupt can therefore repeat. Checkpointing and human approval do not make external transactions exactly once; place side effects behind appropriate task boundaries and use service-level idempotency where repetition matters. The runtime offers control-flow suspension, not an OS sandbox or an approval user interface. A node remains ordinary application code with its host's authority. [Interrupt and Command semantics](https://github.com/langchain-ai/langgraph/blob/36bf3887f074f2b05f42409c8a67e3a33ed1d1ba/libs/langgraph/langgraph/types.py).

At this pin, the old prebuilt `create_react_agent` surface is deprecated in favor of `langchain.agents.create_agent`. That helps locate Deep Agents correctly: Deep Agents supplies middleware and tools; LangChain assembles its agent loop; LangGraph runs and checkpoints the graph. Use LangGraph directly when graph topology, state transitions and recovery boundaries are the design problem. Use a higher harness when you want ready-made filesystem tools, skill loading and compaction conventions. [Prebuilt-agent deprecation](https://github.com/langchain-ai/langgraph/blob/36bf3887f074f2b05f42409c8a67e3a33ed1d1ba/libs/prebuilt/langgraph/prebuilt/chat_agent_executor.py).

The tradeoff is explicit control versus conceptual surface area. Channels, reducers, supersteps, task writes and interrupt replay are useful primitives, but they require more decisions than a small `while` loop. This breadth review confirmed those source boundaries; it did not run crash, concurrency or storage conformance tests.

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 5 | Graph nodes, channels and control flow are host-defined. |
| Integration | 2 | Runtime infrastructure; harness tools and product shell are external. |
| Embeddability | 5 | First-class compiled graphs in process. |
| Durability | 5 | Persistent saver enables checkpoint recovery; host invocation still required. |
| Safety | 2 | Interrupt/gating seams; no OS isolation. |
| Extensibility | 4 | Nodes, reducers, stores and callbacks compose broadly. |
| Multi-agent | 5 | Conditional/parallel graphs and nested workflows. |
| Provider neutrality | 5 | Model calls are supplied by nodes. |
| Maturity | 5 | Versioned 1.x runtime with separate storage packages. |
| Minimalism | 2 | Runtime semantics require more than a small loop. |

<a id="crewai"></a>
## CrewAI

CrewAI is a **Python orchestration framework** whose current surface is broader than the familiar role-playing crew abstraction. The pin declares **1.15.28** in package source and carries an MIT license. Its open-source framework and the commercial AMP control plane are distinct scopes; AMP deployment and governance claims are not credited as local-library capabilities here. [Version and public exports](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/lib/crewai/src/crewai/__init__.py), [License](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/LICENSE), [Framework versus AMP](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/README.md).

A `Crew` groups agents and tasks and selects sequential or hierarchical processing. Hierarchical execution uses a managing agent; sequential execution follows the task plan. Inside an agent, `CrewAgentExecutor` chooses native function calling when the model supports it and tools are available, otherwise a textual ReAct parser/loop. The loop enforces an iteration cap and handles tool observations before requesting another answer. It is not a LangGraph wrapper. The relevant comparison is an opinionated task/agent system with its own executor, rather than a provider SDK alone. [Crew orchestration](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/lib/crewai/src/crewai/crew.py), [Executor paths](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/lib/crewai/src/crewai/agents/crew_agent_executor.py).

Flows add event-driven application control. The historical `crewai.flow.flow` module now re-exports a split DSL, serializable definition and runtime; the public class also composes conversational behavior. Decorators such as `start`, `listen` and `router` describe dependencies while the runtime handles kickoff, listener dispatch and pause/resume. This gives developers a useful choice between model-directed crew execution and explicitly arranged business logic. It also means that a description limited to crews misses a major part of the architecture. [Flow split](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/lib/crewai/src/crewai/flow/flow.py), [Flow runtime](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/lib/crewai/src/crewai/flow/runtime/__init__.py).

Durability is configurable rather than implied by creating an agent. Event-triggered `CheckpointConfig` can capture runtime entities into JSON or SQLite-backed checkpoints, with lineage and restore support. The listener is registered lazily when an entity enables checkpointing. `RuntimeState` serializes entities and event records and reconstructs them from a checkpoint; Flow persistence also has an explicit SQLite implementation. This is stronger than only retaining a task's final text, but the inspected code does not establish transactional exactly-once execution of arbitrary tool effects. A crash between an external effect and the chosen checkpoint event remains an application concern. [Checkpoint listener](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/lib/crewai/src/crewai/state/checkpoint_listener.py), [Runtime serialization/restore](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/lib/crewai/src/crewai/state/runtime.py), [Flow state storage](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/lib/crewai/src/crewai/flow/persistence/sqlite.py).

Tools are ordinary callable integrations, and a `BaseTool.run` eventually invokes application `_run` logic. Configuration, tool validation, human feedback and trace events do not automatically restrict that code's filesystem or network authority. Any isolated code-execution integration must be assessed separately from the framework. The library is embeddable; the CLI and commercial control plane are additional surfaces. It is most relevant when the application vocabulary is agents, tasks, crews and flows, and less directly suited to owning a minimal coding-agent turn protocol. [Tool execution boundary](https://github.com/crewAIInc/crewAI/blob/aaaa312cbac806dcd8142040af15324576b01468/lib/crewai/src/crewai/tools/base_tool.py).

The breadth review inspected executor selection, Flow ownership and snapshot machinery. It did not prove that every event-triggered checkpoint is a safe replay point, nor audit all optional integrations.

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 4 | Own executor plus configurable Crews/Flows. |
| Integration | 3 | Tasks, flows, memory and CLI; AMP excluded. |
| Embeddability | 5 | Python framework classes run in process. |
| Durability | 4 | Opt-in entity/Flow checkpoints and restore; effect replay not proven. |
| Safety | 2 | Human gates and validation; arbitrary tools retain host rights. |
| Extensibility | 4 | Tool, event, Flow and integration surfaces. |
| Multi-agent | 5 | Sequential/hierarchical crews plus event-driven flows. |
| Provider neutrality | 4 | Own LLM abstraction with multiple providers. |
| Maturity | 4 | Versioned 1.x; breadth review does not measure adoption. |
| Minimalism | 2 | Multiple executor/runtime/persistence concepts. |

<a id="agno"></a>
## Agno

Agno combines a **Python agent framework with an optional AgentOS server runtime**. The package is **3.1.3**, licensed Apache-2.0. Its README separates SDK authoring, the AgentOS runtime and a management UI. These are related surfaces, but importing `Agent` does not imply that a FastAPI server, database or scheduler has been deployed. It is also unrelated to the Rivet AgentOS project covered elsewhere in this survey. [Package metadata](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/pyproject.toml), [Product layering](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/README.md).

The `Agent` holds model, tool, memory, history and database configuration while helper modules own execution. `Model.response` contains the repeated model/tool-call loop; application-level run handling adds session persistence, streaming and continuation. Tools use a typed `Function` surface with confirmation, requested user input and external-execution flags. These permit a host to pause and resolve a requirement instead of blindly executing every model call. They remain authorization/orchestration mechanisms, not confinement of the underlying Python function. [Agent configuration](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/agno/agent/agent.py), [Model/tool loop](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/agno/models/base.py), [Tool contract](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/agno/tools/function.py).

The checkpoint API needs particular care. Its annotation advertises `runs`, `tool-batch` and `tools`, but **`checkpoint="tools"` raises `NotImplementedError` at this pin**, despite the 3.x package version. With no override, initialization selects `runs`, which persists terminal run state. `tool-batch` installs an after-tool-results callback that synchronizes the current messages/tools and writes a running checkpoint. It provides finer recovery boundaries than end-of-run history, but a crash during a batch can still leave an unrecorded external effect. [Supported checkpoint levels](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/agno/agent/_init.py), [Checkpoint and continuation implementation](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/agno/agent/_run.py).

The AgentOS checkpoint timeline is derived from markers inside the persisted run row; it is not a separate immutable execution journal. Snapshot previews copy and truncate that row, and continuation uses message indices rather than display checkpoint IDs. A persistent database and a caller that requests continuation are still part of the recovery design. The existence of a scheduler does not by itself establish automatic recovery of every orphaned tool call. [Checkpoint timeline and snapshots](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/agno/os/checkpoints.py).

`Team` adds leader/delegation semantics and `Workflow` arranges explicit application steps. AgentOS wraps these in FastAPI, lifecycle management, auth integrations and scheduler startup. This makes Agno a plausible alternative to broad frameworks such as Mastra or Eve when the desired product is a service with teams, memory and operational surfaces. It is a larger assembly than a small embeddable harness loop. [Team model](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/agno/team/team.py), [Workflow runtime](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/agno/workflow/workflow.py), [AgentOS host](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/agno/os/app.py).

For safety, inspect the actual tool backend. The supplied `ShellTools` invokes `subprocess.run` on the host; a confirmation flag does not turn it into a container or OS sandbox. Server identity controls and tool isolation solve separate problems. This review scores explicit permission hooks and resumable records while reserving a full durable-execution claim until recovery ownership and effect semantics are tested. [Shell execution](https://github.com/agno-agi/agno/blob/160d246d6e95386ef60f995be6ceed108ca62057/libs/agno/agno/tools/shell.py).

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 4 | Agents, Teams, Workflows and provider/tool seams. |
| Integration | 4 | SDK plus FastAPI AgentOS, auth and scheduling. |
| Embeddability | 5 | Ordinary in-process Python API. |
| Durability | 4 | Tool-batch checkpoints/continuation; tools-level checkpoint unsupported. |
| Safety | 3 | Tool confirmation and server auth; shell remains host code. |
| Extensibility | 4 | Toolkits, hooks and server integrations. |
| Multi-agent | 5 | Teams and explicit workflows. |
| Provider neutrality | 5 | Model abstraction with broad integration catalog. |
| Maturity | 4 | Versioned 3.x; one typed capability remains unimplemented. |
| Minimalism | 2 | Broad framework/server surface. |

<a id="llama-index"></a>
## LlamaIndex core agents

LlamaIndex is a **data-oriented framework with an agent workflow layer**, not only a retrieval library. The audited core is **0.14.25, MIT**. Its agent code depends on the separate `llama-index-workflows>=2.14.0,<3` package. The local `Workflow` and `Context` modules are re-exports from that dependency, so claims about the underlying scheduler or persistent workflow service cannot be established from this clone alone. [Core package and workflow dependency](https://github.com/run-llama/llama_index/blob/619d74664e8404612038bc15a1a40c686037277c/llama-index-core/pyproject.toml), [Workflow re-export](https://github.com/run-llama/llama_index/blob/619d74664e8404612038bc15a1a40c686037277c/llama-index-core/llama_index/core/workflow/workflow.py), [Context re-export](https://github.com/run-llama/llama_index/blob/619d74664e8404612038bc15a1a40c686037277c/llama-index-core/llama_index/core/workflow/context.py).

`BaseWorkflowAgent` is itself a Workflow and a Pydantic model. Its step methods prepare context, call the model, interpret the output, execute tools and collect results. `FunctionAgent` supplies provider tool-calling behavior through the LLM's async chat-with-tools interface. Iteration limits and early stopping are explicit; a forced limit can fail or request a final generated answer. This differs from wrapping a complete coding CLI: callers compose the agent as a Python object and receive a workflow handler/event stream. [Agent workflow steps](https://github.com/run-llama/llama_index/blob/619d74664e8404612038bc15a1a40c686037277c/llama-index-core/llama_index/core/agent/workflow/base_agent.py), [Function-calling agent](https://github.com/run-llama/llama_index/blob/619d74664e8404612038bc15a1a40c686037277c/llama-index-core/llama_index/core/agent/workflow/function_agent.py).

`AgentWorkflow` manages multiple named agents and a model-visible handoff tool. Its handoff function checks permitted targets and stores the requested next agent in workflow context. This is genuine control transfer inside a workflow, rather than only running a second agent as a tool. The graph nevertheless does not imply separate processes or workspaces for each participant; isolation must be designed by the application. [Multi-agent handoffs](https://github.com/run-llama/llama_index/blob/619d74664e8404612038bc15a1a40c686037277c/llama-index-core/llama_index/core/agent/workflow/multi_agent_workflow.py).

Memory and retrieval are the distinctive strengths. The `Memory` implementation uses a chat-store abstraction with token limits, a short-term/history ratio and flushable memory blocks. SQL-backed history is available, and external retrieval integrations can supply long-term facts or documents. Persisted chat memory must be distinguished from an atomic checkpoint of currently executing model/tool work. This review confirms the former and an external workflow dependency, but does not claim a built-in exactly-once tool journal or self-restarting worker. [Memory and chat-store configuration](https://github.com/run-llama/llama_index/blob/619d74664e8404612038bc15a1a40c686037277c/llama-index-core/llama_index/core/memory/memory.py).

Tools use `FunctionTool` wrappers around synchronous or asynchronous callables, with schemas and callbacks. The wrapper calls the supplied function directly; callbacks can transform results but do not sandbox the implementation. Agent workflow events carry tool calls/results and progress through the host. Human review can be constructed using workflow events and application policy, but this limited audit did not establish a uniform default approval engine. [FunctionTool execution](https://github.com/run-llama/llama_index/blob/619d74664e8404612038bc15a1a40c686037277c/llama-index-core/llama_index/core/tools/function_tool.py), [Agent event protocol](https://github.com/run-llama/llama_index/blob/619d74664e8404612038bc15a1a40c686037277c/llama-index-core/llama_index/core/agent/workflow/workflow_events.py).

LlamaIndex belongs on the shortlist when the agent's main job is reasoning over an existing retrieval/indexing stack and handing work between specialists. Compared with Pi or AI SDK core it supplies more data and memory conventions; compared with Eve it leaves more deployment and durable-runtime ownership outside this audited package. The breadth score intentionally withholds a high durability or safety rating until the chosen workflow backend, storage and tool execution environment are specified.

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 4 | Agent subclasses, tools, memory and workflow composition. |
| Integration | 3 | Data/memory/tool conventions; deployment runtime external. |
| Embeddability | 4 | In-process API with external workflow dependency. |
| Durability | 2 | Chat/context persistence confirmed; running-task recovery not audited. |
| Safety | 2 | Callbacks and host policies; direct callable tools. |
| Extensibility | 4 | Large integration/tool/memory surface. |
| Multi-agent | 4 | Named-agent workflow with controlled handoffs. |
| Provider neutrality | 5 | LLM abstraction and external provider packages. |
| Maturity | 4 | Established core but 0.x API. |
| Minimalism | 2 | Retrieval plus workflow and memory layers. |

<a id="haystack"></a>
## Haystack

Haystack is a **component/pipeline framework with a substantive agent layer**. The pinned tree identifies itself as **3.5.0-rc0**, Apache-2.0; this is a source prerelease, not evidence that that version is a stable published release. The architecture below follows this pin rather than older Haystack 2.x descriptions. [Pinned version](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/VERSION.txt), [Package metadata](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/pyproject.toml).

The `Agent` is an ordinary Haystack component. It accepts a tool-capable chat generator, tools/toolsets, prompt templates and a typed state schema. Its sync and async methods own a model/tool loop, with a default maximum of 100 steps and tool concurrency of four. Exit conditions can be text or selected tool names. At this pin, the agent calls its internal tool-calling helpers directly; it should not be described as merely wiring an old `ToolInvoker` component into a pipeline. [Agent loop and configuration](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/haystack/components/agents/agent.py), [Tool-call execution helpers](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/haystack/components/agents/tool_calling.py).

State is explicit and mergeable. Tools can map inputs from state and outputs back into it, and per-field handlers control replacement versus accumulation. Six hook phases cover before/after the run, before the model, before/after tools and exit handling. A before-tool hook may replace pending calls; an exit hook can request another iteration. These are useful harness seams for policy and context management, while preserving Haystack's component conventions. [State and merge schema](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/haystack/components/agents/state/state.py), [Hook protocol](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/haystack/hooks/protocol.py).

This version also includes progressive-disclosure skills: `SkillToolset` reads SKILL.md metadata during warmup and exposes `load_skill`/`read_skill_file`. `ConfirmationHook` applies per-tool or wildcard confirmation strategies before execution and can confirm, modify or reject calls. These are real higher-level agent features, not just generic RAG plumbing. Neither tool schemas nor confirmation restrict Python tool code at the OS boundary. The `Tool` contract still invokes supplied callables, and an application must choose an isolated execution backend where required. [Skill loading](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/haystack/tools/skills/skill_toolset.py), [Confirmation policies](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/haystack/hooks/human_in_the_loop/hooks.py), [Callable tool boundary](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/haystack/tools/tool.py).

Multi-agent composition is concrete: `AgentTool` wraps another Agent, delegates a task and returns its final answer without injecting all of the child's internal steps into the caller's context. Pipelines can also compose agents with retrieval, indexing and processing components. The parent and child remain application objects; separate worktrees or process isolation are not implied. [Agent-as-tool composition](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/haystack/tools/agent_tool.py).

Persistence is narrower than a durable conversation service. `Pipeline.run` accepts a breakpoint, a pipeline snapshot and a snapshot callback, supporting explicit pause/restore workflows. This does not establish an automatic durable journal of every inner agent tool, nor exactly-once remote effects. The application owns storage and resumption around the inspected library. HTTP/MCP serving through Hayhooks and the enterprise platform are separate products, as the README states. [Pipeline snapshot surface](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/haystack/core/pipeline/pipeline.py), [Separate deployment surfaces](https://github.com/deepset-ai/haystack/blob/122a617bd661de20cbf882f00010627b0ed7278f/README.md).

Choose this architecture when agent behavior should share component APIs with a data/retrieval pipeline. Its current hook, skill and approval surfaces deserve comparison with harness libraries, while deployment and crash recovery still need a concrete host design.

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 4 | Components, state handlers, tools and six hook phases. |
| Integration | 3 | Agent and data pipeline tools; hosting separate. |
| Embeddability | 5 | Agent and Pipeline are in-process classes. |
| Durability | 3 | Explicit pipeline snapshots, not an automatic inner-tool journal. |
| Safety | 3 | Confirmation policies; no default OS isolation. |
| Extensibility | 4 | Hooks, toolsets, skills and custom components. |
| Multi-agent | 4 | AgentTool delegation plus pipelines. |
| Provider neutrality | 5 | ChatGenerator abstraction and external providers. |
| Maturity | 3 | Pin is an RC; no stable-release assumption. |
| Minimalism | 3 | Agent loop/component boundary is readable; broader framework adds weight. |

<a id="dspy"></a>
## DSPy

DSPy belongs in the comparison as a **programming and optimization layer**, not a complete coding-agent harness. The pin is **3.4.0, MIT**. Its central abstractions are signatures, predictors and composable Python modules; optimizers improve prompts or related program parameters against a metric. This lets it complement another harness rather than replace session management, approvals or a deployment runtime. The package still carries an Alpha classifier, so the major version alone is not a stability guarantee. [Version and package scope](https://github.com/stanfordnlp/dspy/blob/1af633fecbb2b8acec7e3ed9acd6db1cde6d341c/pyproject.toml), [License](https://github.com/stanfordnlp/dspy/blob/1af633fecbb2b8acec7e3ed9acd6db1cde6d341c/LICENSE), [Module composition](https://github.com/stanfordnlp/dspy/blob/1af633fecbb2b8acec7e3ed9acd6db1cde6d341c/dspy/primitives/module.py).

The built-in `ReAct` is a compact agent loop: it predicts a thought, tool name and arguments, calls a tool, appends an observation and stops on the `finish` tool or its iteration budget. It then runs a separate extraction predictor to produce the requested output signature. The default cap is 20 iterations. The trajectory is a local dictionary inside each forward call; error handling can report tool errors to the model and truncate old trajectory entries on context overflow. Truncation is context management, not durable session compaction or checkpoint recovery. [ReAct implementation](https://github.com/stanfordnlp/dspy/blob/1af633fecbb2b8acec7e3ed9acd6db1cde6d341c/dspy/predict/react.py).

A notable current change is the model layer. `LM` now supports a normalized `lm15.Request`/`Response` contract. Its `auto` engine prefers the bundled lm15 backend for representable requests, with LiteLLM retained as a compatibility backend; custom engines can implement the canonical contract. OpenAI-style `messages=` dictionaries are marked for removal in 3.5. Describing current DSPy as simply a thin LiteLLM wrapper would therefore miss an active architectural transition. [LM engines and migration](https://github.com/stanfordnlp/dspy/blob/1af633fecbb2b8acec7e3ed9acd6db1cde6d341c/dspy/clients/lm.py).

`Tool` wraps callables and supports MCP tool adaptation. These host functions remain application code. `CodeAct` adds a different execution path using an interpreter factory; the default `PythonInterpreter` launches Deno/Pyodide and runs model-generated Python in a WASM environment with explicit filesystem, environment and network grants. Its isolation applies to interpreted code, not automatically to host tools exposed through the bridge. A language/runtime sandbox is also distinct from isolating an arbitrary host shell. [Tool and MCP adaptation](https://github.com/stanfordnlp/dspy/blob/1af633fecbb2b8acec7e3ed9acd6db1cde6d341c/dspy/adapters/types/tool.py), [CodeAct interpreter boundary](https://github.com/stanfordnlp/dspy/blob/1af633fecbb2b8acec7e3ed9acd6db1cde6d341c/dspy/predict/code_act.py), [Interpreter capabilities](https://github.com/stanfordnlp/dspy/blob/1af633fecbb2b8acec7e3ed9acd6db1cde6d341c/dspy/primitives/python_interpreter.py).

Saving a DSPy module means serializing learned program state or the program itself; it is not a journal of an active run. `save_program=True` uses cloudpickle, while state-only persistence can use JSON. Nothing in the inspected ReAct loop resumes an interrupted external tool from such an artifact. Distributed scheduling, approval queues and durable side-effect handling should be supplied by the surrounding application. [Program/state persistence](https://github.com/stanfordnlp/dspy/blob/1af633fecbb2b8acec7e3ed9acd6db1cde6d341c/dspy/primitives/base_module.py).

The differentiator is optimization: GEPA consumes metric feedback and reflects on candidate text components to improve the program. This is a different axis from harness durability or product integration and should not disappear into a single overall score. DSPy is useful inside an agent when reasoning/tool-selection policies need systematic improvement and evaluation. It is less direct when the immediate requirement is a finished coding environment or a persistent conversation server. [GEPA optimizer](https://github.com/stanfordnlp/dspy/blob/1af633fecbb2b8acec7e3ed9acd6db1cde6d341c/dspy/teleprompt/gepa/gepa.py).

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 5 | Ordinary Python module composition and custom engines. |
| Integration | 2 | Optimization/programming layer; no finished harness. |
| Embeddability | 4 | First-class library, with normalized-model migration underway. |
| Durability | 1 | Program artifacts and local trajectories are not active-run checkpoints. |
| Safety | 2 | Optional WASM interpreter; host tools remain privileged. |
| Extensibility | 4 | Modules, tools, callbacks, MCP adaptation and optimizers. |
| Multi-agent | 2 | Composable calls/batches, not an agent orchestration runtime. |
| Provider neutrality | 5 | lm15 and LiteLLM-compatible backends/custom engines. |
| Maturity | 4 | 3.x with explicit Alpha metadata and API transition. |
| Minimalism | 4 | ReAct is compact; optimizer machinery is optional. |

<a id="autogen"></a>
## AutoGen

AutoGen remains architecturally important, but its **current maintenance status changes the selection decision**. The pinned README states that it is in maintenance mode, will receive no new features or enhancements, and recommends Microsoft Agent Framework for new users. This is a first-party status statement, not an inference from release cadence. The inspected Python Core and AgentChat packages are **0.7.5**; code is MIT-licensed. .NET code also exists, but this section's implementation evidence is Python. [Maintenance and migration notice](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/README.md), [AgentChat version](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-agentchat/pyproject.toml), [Code license](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/LICENSE-CODE).

AutoGen separates a message-oriented **Core runtime**, higher-level **AgentChat**, and **Extensions** for model clients, tools and code executors. `SingleThreadedAgentRuntime` uses one asyncio message queue, while each agent handles typed messages. Group chats embed that runtime by default and add conversation managers and termination conditions. This makes its center of gravity multi-agent messaging and conversational coordination, rather than filesystem-oriented coding-agent machinery. [Message runtime](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-core/src/autogen_core/_single_threaded_agent_runtime.py), [Group-chat assembly](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_base_group_chat.py).

`AssistantAgent` performs model calls and tool execution, but its default `max_tool_iterations` is **one**. A higher setting permits repeated tool/model cycles. Whether it produces a model-reflected final answer or a tool-result summary is controlled separately by `reflect_on_tool_use`. The class explicitly warns that an instance is neither thread-safe nor coroutine-safe; sharing one mutable agent across concurrent conversations is not a valid isolation strategy. Handoffs and bounded model contexts are configurable collaborators. [Assistant loop and concurrency contract](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-agentchat/src/autogen_agentchat/agents/_assistant_agent.py).

Teams supply higher-order control. For example, Swarm selects the next participant from handoff messages. Such composition is useful when responsibility shifts between specialists and termination must be explicit. It does not imply that each participant has a distinct process or durable mailbox. The runtime's state-save method serializes instantiated agents and specifically excludes subscription state; the inspected path does not serialize the live message queue. State export/import can restore a conversation at an application-chosen boundary, but is not crash-safe replay of arbitrary in-flight tool work. [Swarm handoffs](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_swarm_group_chat.py), [State save/load limits](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-core/src/autogen_core/_single_threaded_agent_runtime.py).

Code execution has an explicit backend boundary. The Docker executor creates/uses a container with configured bind mounts; isolation and accessible data depend on those choices. `CodeExecutorAgent` exposes an approval callback contract, but this does not prove a universal authorization policy for all AssistantAgent functions. Ordinary callable tools still run where the application places them. Approval, a Docker backend and a conversation-state snapshot should be evaluated as separate mechanisms. [Docker executor](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-ext/src/autogen_ext/code_executors/docker/_docker_code_executor.py), [Code approval contract](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-agentchat/src/autogen_agentchat/agents/_code_executor_agent.py).

AutoGen is therefore valuable for understanding actor/message and team patterns, and for evaluating an existing deployment or migration. For new work the vendor's recommended successor deserves direct comparison; the accompanying Microsoft Agent Framework chapter is the relevant next step. This breadth review does not infer feature parity between the two projects.

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 4 | Runtime, agents, model contexts and team managers are composable. |
| Integration | 3 | Teams/executors/Studio; no complete coding product. |
| Embeddability | 5 | First-class in-process APIs. |
| Durability | 3 | Explicit agent/team state save/load; queue not durably journaled. |
| Safety | 3 | Code approval callback and optional Docker; no universal tool policy. |
| Extensibility | 4 | Core messages, AgentChat components and Extensions. |
| Multi-agent | 5 | Swarm/handoffs and multiple team managers. |
| Provider neutrality | 4 | Model-client abstraction and extension providers. |
| Maturity | 3 | Maintenance mode; vendor directs new users to successor. |
| Minimalism | 2 | Core/runtime/AgentChat/extensions require several concepts. |

<a id="semantic-kernel"></a>
## Semantic Kernel

Semantic Kernel is a **model/service and plugin orchestration SDK** with Python, .NET and Java surfaces. The pin's README now presents Microsoft Agent Framework 1.0 as its enterprise-ready successor and links migration guidance. That does not by itself establish that every Semantic Kernel feature is deprecated or that every implementation has stopped maintenance; the narrower, supportable conclusion is that the vendor directs new framework selection toward MAF. The inspected Python package is **1.45.0**, MIT. [Successor and language scope](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/README.md), [Python version](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/__init__.py), [License](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/LICENSE).

A `Kernel` composes function/plugin registration, service selection, filters and reliability helpers. Native functions, prompt functions and connectors become capabilities in that host. `ChatCompletionAgent` layers an agent identity/instructions and a thread abstraction over the kernel and a chat-completion service. Its local `ChatHistoryAgentThread` keeps a `ChatHistory`; remote agent-service implementations have different ownership and storage boundaries and should not be treated as interchangeable persistence guarantees. [Kernel composition](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/kernel.py), [Plugin/function registry](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/functions/kernel_function_extension.py), [Agent and local thread](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/agents/chat_completion/chat_completion_agent.py).

The function-call loop is visible in `ChatCompletionClientBase`. With automatic invocation enabled, it requests completions, collects requested functions, appends the assistant message and invokes calls concurrently through `kernel.invoke_function_call`. It repeats up to the configured maximum and makes a final request with function calling disabled when the limit is reached. `FunctionChoiceBehavior` controls automatic/required/disabled invocation and available functions. This places loop behavior partly in the service connector layer, rather than in a single universal agent scheduler. [Automatic invocation loop](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/connectors/ai/chat_completion_client_base.py), [Function-choice policy](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/connectors/ai/function_choice_behavior.py).

Persistence for the local chat path is explicitly exportable: `ChatHistory` can serialize, restore and write history to a file. That is useful conversation state, but it does not serialize a running function, an external side effect or a durable task queue. The in-process multi-agent runtime uses asyncio tasks/queues, while orchestration classes add sequential, concurrent, group-chat and handoff patterns. An application requiring restart-safe business workflows must select a concrete process/runtime/storage integration and verify it; local history serialization alone does not establish that property. [History persistence](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/contents/chat_history.py), [In-process runtime](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/agents/runtime/in_process/in_process_runtime.py), [Group-chat coordination](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/agents/orchestration/group_chat.py).

The plugin system is an integration boundary, not an OS sandbox. Function filters can intercept execution and MCP plugins can connect via stdio or network transports, but native plugin code retains host privileges. An application may implement an approval policy or use a remote constrained service; neither is implied merely by adding a kernel plugin. This distinction matters when comparing Semantic Kernel's enterprise integration vocabulary with Codex-style command sandboxing. [Execution filters](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/filters/kernel_filters_extension.py), [MCP plugin transports](https://github.com/microsoft/semantic-kernel/blob/5b4a3269a6803f7832568e66313c31d714a1f009/python/semantic_kernel/connectors/mcp.py).

Its main relevance here is existing enterprise/plugin integrations, .NET-oriented deployment choices and migration lineage. The source supports a reusable, embeddable SDK with broad orchestration, while the recommended successor and local-state limits should remain visible in any adoption comparison. This section does not claim parity across Python, .NET and Java or across local and hosted agent services.

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 4 | Plugins/services/filters and orchestration collaborators. |
| Integration | 3 | Integration SDK; product hosting depends on application. |
| Embeddability | 5 | First-class in-process SDKs. |
| Durability | 2 | Local chat serialization; no audited durable function queue. |
| Safety | 2 | Filters/remote-service policies, not host OS isolation. |
| Extensibility | 4 | Native/prompt/OpenAPI/MCP plugins and filters. |
| Multi-agent | 5 | Group/handoff/sequential/concurrent orchestration. |
| Provider neutrality | 4 | Multiple service connectors with cloud-provider tilt. |
| Maturity | 4 | Stable Python 1.x, with vendor successor transition. |
| Minimalism | 2 | Several services, thread types and orchestration layers. |

## Limits of this comparison

These are static architectural findings, not performance or recovery benchmarks. Optional storage, sandbox, protocol and hosted-platform integrations were not exhaustively audited. Python source is the primary implementation evidence for these eight records; parallel language ports and external workflow packages may differ. In particular, LlamaIndex delegates its workflow runtime to another package, LangGraph needs a configured persistent saver and host, and AutoGen/Semantic Kernel migration notices are narrower than a claim that every existing feature has disappeared.
