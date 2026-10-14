# Python frameworks, composable harnesses, and the current Letta lineage

> Pydantic AI, smolagents, and Microsoft Agent Framework are three different foundations: typed graph execution plus capabilities, a compact code-agent loop, and middleware/workflow orchestration. At these pins both Pydantic and Microsoft also ship opinionated harness layers. Letta must be handled separately: its old Python repository is now a landing page pointing to a TypeScript product. This chapter inspects that current source instead of inventing architecture from the retired server.

| System | Pin / version | License / language / size | Architectural scope |
|---|---|---|---|
| Pydantic AI + Harness | `b82f0f258f4d`; VCS-derived core version; harness has separate 0.x policy | MIT; Python; 4,320 tracked files | Core framework and composable harness are separate matrix records [P1] [P2] |
| smolagents | `96f33faaf028`; `1.27.0.dev0` | Apache-2.0; Python; 185 files | Code/tool agent library [S1] |
| Microsoft Agent Framework | `95511ff025d8`; Python core `1.21.0` | MIT; Python and C#; 5,532 files | Python implementation inspected; .NET parity not assumed [M1] [M10] |
| Letta Code | `5333d2060f07`; `0.34.14` | Apache-2.0; TypeScript; 2,597 files | Stateful terminal/server product [L1] [L2] |

The original `letta-ai/letta` pin contains only 12 tracked files. Its README says active source moved to `letta-ai/letta-code` and the `archive` branch contains the retired V1 API server. The new clone above was added solely for static evidence. Versioned manifests are snapshot facts; first-release dates and registry-latest status were not reconstructed. [L0]

## 1. Layering & package map

```text
Pydantic: Agent -> typed graph nodes -> model/toolsets
                  + capabilities -> workspace, compaction, persistence, children
                  + durable engine adapters -> external execution backend
smolagents: MultiStepAgent -> CodeAgent | ToolCallingAgent -> model
                            | PythonExecutor | tool invocation
Microsoft: Agent -> client/function invocation + middleware + context providers
           Workflow -> executors/edges/supersteps -> checkpoint storage
           create_harness_agent -> selected batteries on that same base
Letta: terminal/headless/App Server -> approval/tool execution -> local backend
       local backend -> ProviderTurnExecutor -> PiStreamAdapter -> pi-ai
       memory filesystem + compiled prompts + JSONL transcripts + recovery evidence
```

Pydantic's harness is not an unrelated agent implementation. `Coder` is a `CombinedCapability`, and the runnable coder is an ordinary `Agent` with a workspace capability and `Coder`. That makes it possible to add or omit policies without forking a special coding loop. [P5] [P6] [P13]

Microsoft uses a different composition mechanism: its factory wires function invocation, history, compaction, todo, mode, memory, and optional skills/background agents. The core graph/workflow engine remains separate from that opinionated construction. smolagents places most loop policy in a base class and varies the action executor. Letta has a provider adapter boundary but the main value is its product-owned state and execution lifecycle. [M2] [M4] [S3] [L3]

## 2. Agent loop

**Pydantic AI.** The graph contains distinct user-prompt, model-request, and tool-call handling nodes. The model-request node has streaming and suspended-response state, making an interrupted generation an explicit continuation case. Capabilities hook into the run rather than only wrapping the final output. This is useful for validation, budgets, traces, and durable model/tool boundaries, but is a larger abstraction than a raw `while tools` loop. [P4] [P7] [P11]

**smolagents.** `_run_stream` iterates until a final answer or max steps. It optionally emits planning steps, creates an `ActionStep`, streams model/action outputs, checks final-answer validators, and records timing and callbacks in `finally`. Implementation-generation errors propagate; model-caused agent errors are stored as feedback and the loop continues. Interrupts set an explicit switch. The tool-calling variant executes multiple tool calls with a thread pool; code agents instead generate a program for their Python executor. [S3] [S4]

**Microsoft.** Distinguish three loops: provider/function invocation, optional `AgentLoopMiddleware` that reruns an entire agent using a predicate or judge, and workflow supersteps. The outer middleware defaults to ten iterations and can inject feedback messages. The workflow runner executes a superstep, commits pending state only on success, discards pending state on failure, checkpoints, and stops when there are no messages or the iteration budget is exhausted. These are different continuation contracts and should not be collapsed into one "agent loop" feature. [M5] [M8]

**Letta.** The local executor uses `PiStreamAdapter` for model transport but converts tool calls into Letta approval-request events. The higher-level headless/runtime path classifies approvals, executes admitted tools, formats returns, and continues the conversation. A one-shot headless run denies tools needing interactive user responses because it has no control channel for them. A completed provider stream is therefore not necessarily a completed agent turn. [L3] [L4] [L5]

## 3. Model / provider abstraction

Pydantic models and tool outputs use typed internal messages, with model-request handling independent from the harness capabilities. Its durable adapters route model I/O through external execution boundaries. This decoupling lets the same agent be used interactively or under a durable engine, with important configuration constraints. The older Temporal wrapper is deprecated in favor of a capability API at this pin; copying an older tutorial without checking the migration would misrepresent the current direction. [P4] [P10]

smolagents supplies model adapters and normalizes responses into chat/message/action structures. Its official README lists inference-client, LiteLLM, local Transformers, and OpenAI-compatible integrations; that supports provider breadth but not identical feature support. Token usage is included in run results, while model pricing and cache behavior depend on the adapter. [S8] [S2]

Microsoft separates the agent interface from chat clients, with packages for several vendor integrations. The inspected generic middleware consumes `AgentResponse`/updates rather than one provider's objects. Its broad Python/.NET positioning is documented, but this chapter's behavior claims are specifically about Python source. [M10] [M5]

Letta Code directly depends on `@earendil-works/pi-ai`. Its local execution factory constructs a provider adapter, so broad provider support is inherited through a concrete dependency edge. It does not follow that Letta uses Pi's entire coding harness, session engine, or durable package: the inspected approval, transcript, memory, and recovery machinery is Letta-specific. [L2] [L3] [L8]

## 4. Tool system

Pydantic `Coder` composes five file operations and a shell tool, plus delegation. File tools have output/read bounds and retry policy; general output truncation is another capability. Commands are explicitly unrestricted inside the chosen workspace, and can outlive a run. The workspace is therefore the important safety/placement boundary; the presence of typed tool schemas does not make shell execution safe by itself. [P5] [P6]

Pydantic's approval-required wrapper raises a deferred approval condition before executing an unapproved tool. The harness also represents a model retry as data when crossing a durable-operation boundary, then raises it again outside that boundary. This subtle choice avoids losing the retry outcome merely because workflow engines record returned values differently from raised exceptions. [P12] [P11]

smolagents exposes Python functions/tools to code or dispatches named tool calls. Tool-call results are yielded as they finish and then assembled into memory. An executor is selected from local, Docker, E2B, Modal, or Blaxel. A crucial restriction appears in the actual factory: managed agents are rejected with remote code execution at this pin. Do not advertise both features as freely composable. [S4] [S5]

Microsoft harness file access is opt-in and can separately disable write tools or approval requirements. Letta runs its local tool batch after approval classification, preserving tool call/return pairs for stream consumers. These are more product-like admission policies than the minimal smolagents default. [M4] [L5]

## 5. Context management

Pydantic Harness exports distinct capabilities for clearing tool results, deduplicating reads, sliding windows, summarization, tiered/fallback compaction, memory, repository context, and output limits. `Coder`'s defaults are narrower than that catalog: it installs `ClearToolResults`, bounded output truncation, repository context, and optional caching. It does not automatically enable every exported summarizer or persistence backend. This distinction is essential when comparing a package's capabilities with its defaults. [P3] [P6] [P9]

smolagents records task, plan, action, and final-answer steps. `run(reset=False)` can retain history across calls; passing additional variables puts them in executor state. Its planning steps are model-guidance updates, not proven crash-recovery checkpoints or automatic summarization. The inspected loop accumulates memory and exposes callbacks, leaving application-specific pruning to extensions. [S2] [S3]

Microsoft orders history before compaction and other context providers. Its harness distinguishes per-model-call compaction from post-run compaction over persisted history. Default file memory lives under `agent-file-memory` and is scoped by session; skill providers and background agents are opt-in. These choices reduce accidental sharing of memory across sessions while still allowing explicitly shared stores. [M3] [M4]

Letta treats memory as a filesystem with a Git revision and compiles selected committed memory into the system prompt. Conversation compaction is separate: the local module defines all-history and sliding-window modes, with sliding window the default and a retained-percentage setting. Persistent agent memory is therefore not just another name for the conversation summary. [L7] [L6]

## 6. State, sessions & durability

**Pydantic has two distinct layers.** `StepPersistence` logs lifecycle events, maintains a tool-effect ledger, and stores continuable snapshots at settled tool boundaries. If a process dies between tool-start and tool-end, the effect remains visibly started—an unknown-after-crash state. Default continuation selects complete snapshots; interrupted frontiers require explicitly consulting unresolved effects. Its default store is in memory, so durable storage must be chosen. [P7]

External durable execution is a separate integration. Temporal moves model requests, tool calls, and MCP communication into activities, while current capability-based APIs replace the older wrapper. This supplies workflow replay semantics with a backend; it does not guarantee exactly-once effects inside an activity. The harness's explicit unknown-effect ledger is especially useful because it refuses to disguise that uncertainty as success. [P10] [P11] [P7]

**smolagents** maintains in-process memory and executor state. Its `save` method exports code, tool modules, configuration, prompt YAML, and an app skeleton. That is reproducible agent packaging, not a snapshot of every executing program and not a durable workflow continuation protocol. Keeping a memory object between runs likewise does not survive process death automatically. [S7] [S2]

**Microsoft** stores committed workflow state, messages, executor state, partial edge/fan-in state, pending human-input events, topology signature, and checkpoint lineage. A checkpoint chain is not ordered solely by iteration count, because more than one checkpoint can exist at a human-interaction boundary. Restoring a workflow needs compatible topology and a persistent storage implementation. An ordinary `AgentSession` with history alone should not receive the workflow engine's durability score. [M7] [M8]

**Letta** uses versioned local transcript manifests and JSONL session entries. Its App Server recovery path goes further: it acquires recovery ownership, records evidence before tool execution, checkpoints exact settled results, and checks that the recovery claim is still held. This is meaningful recovery engineering, yet an external side effect can still be ambiguous between execution and evidence commit. The chapter gives it more than simple transcript-resume credit without claiming transactional replay. [L8] [L9]

## 7. Safety & sandboxing

Pydantic's local workspace is not equivalent to an isolated sandbox. `Coder` says to attach a sandbox capability for untrusted work; its default shell has an empty denied-command list. `BubblewrapSandbox` wraps a workspace and defaults network sharing off, with a seccomp filter blocking socket connections. The exported E2B/Modal and other sandbox capabilities offer alternative execution placement. These protections apply when configured, not automatically to every arbitrary Python tool. [P5] [P6] [P8] [P3]

smolagents explicitly documents that the local restricted interpreter is **not a security sandbox**. Import/builtin restrictions, output length, and timeout controls are useful guardrails, but remote execution is the recommended isolation route for untrusted code. The inability to combine managed agents with remote execution is a practical architecture constraint, not a footnote. [S6] [S5]

Microsoft's approval middleware is opt-in and stores standing rules in the session. Its documentation warns that rules are not tied to a particular tool instance; reusing a session with a different tool of the same name can reuse an old approval. The application must scope or invalidate those rules when tools change, especially for MCP. This is a concrete example of why "has approvals" is not a complete security rating. [M6]

Letta includes Seatbelt and Bubblewrap launch wrapping, but the inspected memory-confinement policy is specific: normal agents can still read the filesystem except denied other-agent memory roots, and write restrictions depend on the selected profile. If no backend is available, the wrapper returns null and the caller can use a static guard tier. This is partial OS confinement with fallback, not a universal default network/filesystem sandbox. [L10] [L11] [L15]

## 8. Extensibility

Pydantic's capability composition is its strongest interface: workspace providers, toolsets, compaction, spend limits, skills, subagents, and durable operations can share one Agent. `Coder` demonstrates that an opinionated bundle can remain assembled from ordinary pieces. The separate harness package is marked alpha and follows a 0.x versioning policy, so stability claims about the core should not automatically cover every harness component. [P2] [P3] [P6]

smolagents provides tools, managed agents, step callbacks, configurable prompts, executors, and Hub export/import. Its README also identifies MCP and LangChain tool adapters. The scope remains small enough to understand, but a plugin marketplace or durable host is not supplied by the base loop. [S8] [S3] [S7]

Microsoft uses middleware, context/history providers, tools, chat clients, skills, and workflow executors. Letta has a mod API with explicit tool, command, provider, permission, UI, and event capabilities, as well as permission hooks. A mod can therefore participate in product behavior beyond merely adding an MCP tool. [M2] [M4] [L14] [L15]

## 9. Multi-agent

Pydantic `Coder` can delegate a self-contained task to a fresh run of the same bound agent, including its other capabilities. It can also discover disk-defined delegates when configured. A fresh run is a context boundary; separate workspace isolation depends on how capabilities/workspaces are supplied. The default should not be read as "a new Git worktree per child." [P5] [P6]

smolagents exposes managed agents as callable tools/code functions, with the remote-executor incompatibility already noted. Microsoft supports both background-agent providers and workflow composition. Its agent-as-tool API explicitly warns that child approvals are not propagated into the calling agent and recommends a workflow when approvals need durable coordination. That is a valuable distinction between simple delegation and recoverable handoff. [S5] [M4] [M9]

Letta spawns headless subagent processes or submits remote turns; existing agents use separate conversations for thread safety. Newly spawned subagents are stateless with respect to memory filesystem mode. Memory-update workers are a special case: they edit a private worktree of the memory repository, merge completed work, discard cancellation, and preserve conflicts rather than guessing. This verifies worktree usage for memory workers, not universal coding-task worktree isolation. [L12] [L13]

## 10. Surfaces & integration

Pydantic core is an in-process Python SDK, with a separate CLI capable of loading the harness coder. smolagents is likewise an in-process library and can export a Gradio-style application skeleton to a Hub Space. Neither requires adopting a terminal product to use its loop. [P13] [S7]

Microsoft provides in-process Python/.NET libraries, developer UI, hosting integrations, and orchestration packages; this chapter verifies Python behavior and treats other language/API parity as a separate evaluation. The framework repository's Go direction points to a separate repository. [M10]

Letta Code is an integrated terminal/headless/App Server product with client/server and channel surfaces. The old landing repository points to an Agent SDK for TypeScript, but that SDK was not separately cloned here; its stability and exact in-process versus server boundary are not inferred from a documentation link. The inspected product package exposes selected client/helper modules and the CLI, so its embeddability score remains conservative. [L0] [L1]

## 11. Observability & evals

Pydantic's graph and durable capability boundaries expose structured lifecycle points. Harness StepPersistence is especially useful for operational inspection because it records started/completed/failed model and tool work and unresolved effects. Its exported trajectory/tool judges and Logfire integration show available instrumentation surfaces, but were not performance-tested. [P7] [P3]

smolagents records timings, errors, token usage, steps, and callbacks; final-answer checks can reject an answer and continue. Microsoft documents OpenTelemetry integration and has separate evaluation/lab packages. Letta's provider-turn boundary reports request identity, model, duration, token usage, and errors, while its recovery evidence records effect boundaries. These are different observability planes; none alone proves task quality. [S3] [M10] [L9] [L3]

## 12. Notable design decisions & trade-offs

The most important update to common comparisons is that Pydantic and Microsoft are no longer only bare application frameworks at these pins. Both offer opinionated harness assembly on top of their existing abstractions. Pydantic emphasizes additive capabilities and workspace placement; Microsoft emphasizes middleware/context providers and workflow checkpoints. Choosing between them should include how their extension model fits the host application. [P6] [M2]

smolagents keeps the code-agent idea compact and approachable, with a direct cost: integration and crash recovery are application responsibilities. Letta takes the opposite direction, investing heavily in persistent identity, memory, product surfaces, and recovery. Its new TypeScript source is a current product architecture, not a continuation of assumptions about the retired Python server. [S3] [S7] [L0] [L9]

## 13. Scorecard

Each column is a separate record: **Pydantic core / Pydantic Harness / smolagents / Microsoft / Letta Code**. Harness scores include explicitly available optional capabilities, not an assertion that all are enabled by default.

| Dimension | Scores | Rationale |
|---|---|---|
| Flexibility | 5 / 5 / 4 / 5 / 4 | Replaceable models/capabilities; small subclass seams; middleware/workflows; product mods. |
| Integration | 3 / 4 / 2 / 4 / 5 | Core SDK through complete terminal/server product. |
| Embeddability | 5 / 5 / 5 / 5 / 3 | In-process libraries versus product/server-oriented Letta. |
| Durability | 4 / 4 / 1 / 4 / 4 | Configured engines/ledgers/checkpoints/recovery; smol default is memory. |
| Safety | 3 / 4 / 3 / 3 / 3 | Approvals or optional isolation; none warrants universal default confinement claims. |
| Extensibility | 4 / 5 / 3 / 5 / 5 | Capability catalog and mods richer than small callback/tool APIs. |
| Multi-agent | 3 / 4 / 3 / 5 / 4 | Delegation through workflow and persistent product orchestration. |
| Provider neutrality | 5 / 5 / 5 / 5 / 5 | Broad adapter interfaces; provider feature parity remains qualified. |
| Maturity | 4 / 2 / 4 / 4 / 3 | Established core versions; Pydantic Harness alpha; Letta 0.x migration. |
| Minimalism | 3 / 2 / 4 / 2 / 1 | Small smol loop; substantial full frameworks/products. |

## 14. When to build on it / when not to

Use Pydantic core for typed application agents and add Harness capabilities when workspace tools, context management, or persisted run evidence are needed. Validate the alpha harness API and choose storage/sandbox backends deliberately. Use smolagents for a small code-agent experiment or a controlled agent library where you can own the missing operational policies. [P2] [P6] [S5]

Use Microsoft when middleware composition, explicit workflows, human interaction, and an existing Python/.NET application ecosystem are central. Use Letta Code when persistent agent identity and memory plus terminal/server surfaces are the product you want; assess its separate SDK before treating the product repository as a drop-in Python library. [M7] [M10] [L0] [L7]

## 15. Evidence index

Verification performed: static inspection of selected graph/loop code, capability/factory assembly, tool execution, executor selection, persistence/recovery boundaries, approval rules, sandbox scope, subagent behavior, and package manifests. Letta Code was cloned after the original repository's explicit redirect. All references below were validated for file existence and line bounds. No source package was imported, built, installed, or tested. The analysis is not a full security audit or an independent adversarial verification; .NET parity, SDK promises, release-origin dates, and live deployment behavior remain outside the checked scope.

[P1]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/pyproject.toml#L1-L30 "pyproject.toml:L1-L30"
[P2]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/src/pydantic_ai_harness/pyproject.toml#L1-L40 "src/pydantic_ai_harness/pyproject.toml:L1-L40"
[P3]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/src/pydantic_ai_harness/pydantic_ai_harness/__init__.py#L7-L75 "src/pydantic_ai_harness/pydantic_ai_harness/__init__.py:L7-L75"
[P4]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/pydantic_ai_slim/pydantic_ai/_agent_graph.py#L1380-L1445 "pydantic_ai_slim/pydantic_ai/_agent_graph.py:L1380-L1445"
[P5]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/src/pydantic_ai_harness/pydantic_ai_harness/coder/_capability.py#L23-L101 "src/pydantic_ai_harness/pydantic_ai_harness/coder/_capability.py:L23-L101"
[P6]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/src/pydantic_ai_harness/pydantic_ai_harness/coder/_capability.py#L123-L158 "src/pydantic_ai_harness/pydantic_ai_harness/coder/_capability.py:L123-L158"
[P7]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/src/pydantic_ai_harness/pydantic_ai_harness/step_persistence/_capability.py#L49-L123 "src/pydantic_ai_harness/pydantic_ai_harness/step_persistence/_capability.py:L49-L123"
[P8]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/src/pydantic_ai_harness/pydantic_ai_harness/bubblewrap_sandbox/_capability.py#L12-L42 "src/pydantic_ai_harness/pydantic_ai_harness/bubblewrap_sandbox/_capability.py:L12-L42"
[P9]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/src/pydantic_ai_harness/pydantic_ai_harness/compaction/_summarizing_compaction.py#L1-L85 "src/pydantic_ai_harness/pydantic_ai_harness/compaction/_summarizing_compaction.py:L1-L85"
[P10]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/pydantic_ai_slim/pydantic_ai/durable_exec/temporal/_agent.py#L102-L180 "pydantic_ai_slim/pydantic_ai/durable_exec/temporal/_agent.py:L102-L180"
[P11]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/src/pydantic_ai_harness/pydantic_ai_harness/_durable.py#L1-L45 "src/pydantic_ai_harness/pydantic_ai_harness/_durable.py:L1-L45"
[P12]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/pydantic_ai_slim/pydantic_ai/toolsets/approval_required.py#L1-L32 "pydantic_ai_slim/pydantic_ai/toolsets/approval_required.py:L1-L32"
[P13]: https://github.com/pydantic/pydantic-ai/blob/b82f0f258f4d6aa3d53355583735584f47068c2d/src/pydantic_ai_harness/pydantic_ai_harness/coder/_agent.py#L1-L15 "src/pydantic_ai_harness/pydantic_ai_harness/coder/_agent.py:L1-L15"
[S1]: https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/pyproject.toml#L1-L21 "pyproject.toml:L1-L21"
[S2]: https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/agents.py#L436-L499 "src/smolagents/agents.py:L436-L499"
[S3]: https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/agents.py#L540-L623 "src/smolagents/agents.py:L540-L623"
[S4]: https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/agents.py#L1361-L1442 "src/smolagents/agents.py:L1361-L1442"
[S5]: https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/agents.py#L1598-L1618 "src/smolagents/agents.py:L1598-L1618"
[S6]: https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/local_python_executor.py#L1688-L1765 "src/smolagents/local_python_executor.py:L1688-L1765"
[S7]: https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/agents.py#L892-L930 "src/smolagents/agents.py:L892-L930"
[S8]: https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/README.md#L34-L53 "README.md:L34-L53"
[M1]: https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/python/packages/core/pyproject.toml#L1-L30 "python/packages/core/pyproject.toml:L1-L30"
[M2]: https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/python/packages/core/agent_framework/_harness/_agent.py#L1-L35 "python/packages/core/agent_framework/_harness/_agent.py:L1-L35"
[M3]: https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/python/packages/core/agent_framework/_harness/_agent.py#L100-L143 "python/packages/core/agent_framework/_harness/_agent.py:L100-L143"
[M4]: https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/python/packages/core/agent_framework/_harness/_agent.py#L146-L215 "python/packages/core/agent_framework/_harness/_agent.py:L146-L215"
[M5]: https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/python/packages/core/agent_framework/_harness/_loop.py#L229-L274 "python/packages/core/agent_framework/_harness/_loop.py:L229-L274"
[M6]: https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/python/packages/core/agent_framework/_harness/_tool_approval.py#L379-L440 "python/packages/core/agent_framework/_harness/_tool_approval.py:L379-L440"
[M7]: https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/python/packages/core/agent_framework/_workflows/_checkpoint.py#L34-L103 "python/packages/core/agent_framework/_workflows/_checkpoint.py:L34-L103"
[M8]: https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/python/packages/core/agent_framework/_workflows/_runner.py#L108-L180 "python/packages/core/agent_framework/_workflows/_runner.py:L108-L180"
[M9]: https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/python/packages/core/agent_framework/_agents.py#L652-L695 "python/packages/core/agent_framework/_agents.py:L652-L695"
[M10]: https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/README.md#L11-L60 "README.md:L11-L60"
[L0]: https://github.com/letta-ai/letta/blob/5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a/README.md#L1-L39 "README.md:L1-L39"
[L1]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/package.json#L1-L59 "package.json:L1-L59"
[L2]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/package.json#L143-L165 "package.json:L143-L165"
[L3]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/backend/local/local-executor-factory.ts#L1-L73 "src/backend/local/local-executor-factory.ts:L1-L73"
[L4]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/backend/dev/provider-turn-executor.ts#L478-L543 "src/backend/dev/provider-turn-executor.ts:L478-L543"
[L5]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/headless.ts#L2578-L2648 "src/headless.ts:L2578-L2648"
[L6]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/backend/local/compaction.ts#L21-L45 "src/backend/local/compaction.ts:L21-L45"
[L7]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/backend/local/system-prompt-compilation.ts#L13-L90 "src/backend/local/system-prompt-compilation.ts:L13-L90"
[L8]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/backend/local/local-transcript.ts#L24-L49 "src/backend/local/local-transcript.ts:L24-L49"
[L9]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/websocket/listener/recovery.ts#L570-L671 "src/websocket/listener/recovery.ts:L570-L671"
[L10]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/sandbox/policy.ts#L3-L53 "src/sandbox/policy.ts:L3-L53"
[L11]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/sandbox/wrap.ts#L1-L43 "src/sandbox/wrap.ts:L1-L43"
[L12]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/agent/subagents/manager.ts#L134-L199 "src/agent/subagents/manager.ts:L134-L199"
[L13]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/agent/subagents/memory-worker.ts#L67-L96 "src/agent/subagents/memory-worker.ts:L67-L96"
[L14]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/mods/types.ts#L1-L90 "src/mods/types.ts:L1-L90"
[L15]: https://github.com/letta-ai/letta-code/blob/5333d2060f0719882d622d0f05b1c9feffc987b8/src/permissions/checker.ts#L4-L57 "src/permissions/checker.ts:L4-L57"
