# Google Agent Development Kit: Python and TypeScript

> ADK is a service-oriented agent framework with replaceable models, tools, sessions, artifacts, memory, and execution nodes. Its strongest architectural feature is the explicit event stream linking agent work to session state and workflow recovery. At these pins, Python ADK already contains a substantial workflow/replay implementation; TypeScript has related abstractions but explicitly documents a narrower rehydration implementation. Build on ADK for application agents and orchestrated services, while assessing language parity and backend durability separately.

| | Python ADK | TypeScript ADK |
|---|---|---|
| Repository / pin | `google/adk-python` @ `69c0b00fc60a` | `google/adk-js` @ `120c28252e57` |
| License | Apache-2.0 | Apache-2.0 |
| Version at pin | `2.12.0` [A27] | `@google/adk` `2.3.0` [J1] |
| Size | 2,936 tracked files | 1,164 tracked files |
| Category | `agent-framework` | `agent-framework` |
| History scope | 2026-10-14 snapshot; first release not reconstructed | 2026-10-14 snapshot; separate package/version history |

A version in a pinned manifest is evidence about that checkout, not a claim about the latest published registry artifact. This study does not assume that identical class names imply feature parity.

## 1. Layering & package map

```text
App(root agent/node, plugins, compaction/cache/resume policy)
  -> Runner(session, artifact, memory, credential services)
     -> BaseAgent / LlmAgent / Workflow nodes
        -> request processors -> BaseLlm -> response processors
        -> tools / toolsets / subordinate agents
     -> Events -> session service and consuming host
```

The application container accepts a `BaseNode` root, including a traditional agent. That detail matters: orchestration is not limited to an LLM choosing among tools. Plugins and app-wide cache, compaction, and resumability configuration sit above individual agents. The runner wires execution to persistence and other services rather than requiring each agent to discover global storage. [A1] [A2]

Python distributes this machinery under `google.adk`; the TypeScript repository separates `core`, development tooling, and integrations. The JS core exports Node and browser entry points, so a browser-capable package is a real packaging decision, though it does not mean every server-only tool works in a browser. The TS runner exposes separate session, artifact, memory, credential, plugin, and resumability dependencies, preserving the architectural separation. [J1] [J2]

## 2. Agent loop

The Python `BaseLlmFlow.run_async` repeatedly executes one model step and yields its events. It stops when aborted, when no event arrives, or when the last event is final or unexpectedly partial. `_run_one_step_async` prepares a request, runs preprocessors, evaluates resume decisions, invokes the model, and postprocesses responses. Partial streaming chunks share an event identity; a fresh identity is created after a complete response. This is more structured than collecting strings and appending them to a chat list. [A3] [A4]

The resume branch runs before making a fresh model call. It can pause for unanswered work or replay outstanding function calls from recorded model output. The live/CFC path is deliberately separated because it already performs live tool postprocessing: doing normal postprocessing again would execute tools twice. These branches are strong evidence that streaming and recovery are part of the core control flow rather than UI decorations. [A4] [A6]

The flow also offers named request-processor replacement, insertion, and removal. Applications can alter prompt assembly or request policy without replacing the whole runner. That flexibility comes with a larger behavioral contract: a processor can emit events or end an invocation, so its effects must be understood alongside callbacks and tools. [A5] [A4]

Parallelism exists at multiple levels. The inspected `ParallelAgent` concurrently consumes child async generators and merges their events through a queue, waiting for upstream consumption before advancing each child. It also propagates failures and cancels children on an exit request. At this pin that class is deprecated in favor of `Workflow`, with an explicit caveat that Workflow cannot yet be an `LlmAgent` subagent. An architecture comparison that simply lists legacy sequential/parallel/loop agents misses this migration. [A21]

## 3. Model / provider abstraction

`BaseLlm` is an extensible model contract with explicit capability reporting. Its fallback can infer capabilities from names for backward compatibility, but new integrations can override the capability property. This is important for combinations such as output schemas plus tools: request construction should follow capabilities, not just a vendor string. The source tree contains Gemini, Anthropic, LiteLLM, and other adapters; the neutral contract is real, while provider feature equivalence remains adapter-specific. [A13]

ADK's internal request and content conventions are closely related to Google GenAI types. Provider neutrality therefore means adapters can translate into this representation, not that the framework is equally idiomatic for every provider. Python's dependency manifest includes `google-genai`, and its rich multimodal surface is part of that choice. TypeScript has its own `BaseLlm` interface and model implementations; Python adapter availability should not be mechanically copied into the JS feature matrix. [A28] [J4]

Static and dynamic instructions have distinct placement. When `static_instruction` is set, changing instructions can move into user content after the stable system prefix. The source explicitly says setting a static instruction alone does not enable explicit caching; that requires app-level cache configuration. This avoids overstating a prompt-layout optimization as a cache service. [A14]

## 4. Tool system

Python functions become `FunctionTool` instances. Function declaration generation uses Pydantic/JSON-schema machinery and is cached because repeating schema construction on every model call is expensive. The tool can require confirmation unconditionally or through a function of its arguments. Context injection and filtering keep runtime services out of the model-facing argument schema. [A15] [A17]

Argument preprocessing has a significant qualification: the inspected stronger validation/coercion path is feature-gated, and unsupported annotations can fall through. A consumer should verify the applicable feature configuration instead of assuming every Python annotation becomes a strict universal security boundary. Validation failures return correction guidance to the model; application exceptions and argument errors are distinguished separately. [A16] [A17]

MCP is exposed as a toolset with connection parameters, authentication, resource access, and per-tool confirmation policy. This is an integration into the same tool abstraction, not a separate agent loop. The chapter verifies MCP client functionality; it does not infer a generic MCP server export merely from the presence of MCP imports. [A25]

## 5. Context management

Prompt assembly combines instructions, session events, tool declarations, and processor behavior. Dynamic instruction placeholders resolve from session state; stable instructions enable a predictable prefix. App-level compaction and context caching are separate settings and can be configured independently. A session store, a memory service, and a context cache solve different problems: preserving a conversation, retrieving useful information, and reusing provider computation respectively. [A14] [A1] [J2]

Python compaction supports token-threshold logic and invocation-based sliding windows. The implementation examines existing compaction events, chooses an eligible event range, preserves a self-contained prefix, and produces a new summary event. It does not simply delete the first N messages. A trace records compaction configuration and error status; summarizer failure does not make the entire otherwise usable history invalid. [A23] [A22]

The runner's post-invocation compaction is best-effort derived work. It appends compaction results to the session and discards stale work if another turn superseded the snapshot. This design separates user-visible agent execution from maintenance of a smaller context projection. It is also why stored events and the request sent to the model are not interchangeable representations. [A10]

No default recursive `AGENTS.md` discovery was established from these core paths. ADK applications can supply project instructions or skills, but that is a separate policy from the root agent's `instruction` field. The matrix marks instruction-file compatibility as unverified unless a specific integration is separately inspected.

## 6. State, sessions & durability

The runner uses a session service rather than hard-coding a storage format. Python's database session service accepts a database URL or existing SQLAlchemy async engine. In-memory operation remains possible, but enabling resumability does not magically persist an in-memory session across process death. Deployment must choose a persistent service and preserve the identifiers used for recovery. [A24] [A2]

Python resume logic examines outstanding function responses, interrupt IDs, agent authorship, and branch identity. A partial response to several awaited calls keeps the invocation paused until all required responses exist. The author check prevents a restored client-supplied function-call event from automatically becoming executable agent work. These are concrete recovery semantics and security considerations, not merely a transcript reload. [A7]

Workflow replay indexes events by node path, reconstructs relevant histories, and tracks the completion sequence for the current invocation. It separates completed children from interrupted children and uses terminal outcome evidence to determine which can be fast-forwarded. This supports recovering orchestration decisions, but it still cannot prove that an external side effect happened exactly once if a worker dies between the effect and recording its outcome. Tool authors must design for that gap. [A8] [A9]

The runner exposes rewind for state and artifact history, which should not be confused with undoing arbitrary external systems. The same qualification applies to checkpoints: a previous logical application state is not a reverse transaction for a sent email or a remote provisioning request. [A12]

TypeScript's rehydration source explicitly calls itself the static-graph subset and names the chronological barrier for deterministic parallel/dynamic replay as a continuation. It also explains a different identity strategy: the TS runner creates a fresh invocation ID per turn, so interrupted workflow history is delimited using pause/completion boundaries. These are material differences from Python's current-invocation filtering. They justify separate durability scores. [J3] [A9]

## 7. Safety & sandboxing

ADK separates authorization from execution isolation. `require_confirmation` gates a tool invocation; it does not sandbox the Python function. An ordinary function can use the host process's privileges once admitted. Applications must decide which operations deserve confirmation and which execution environment handles model-generated code. [A15] [A17]

The Python `ContainerCodeExecutor` provides real container controls: network disabled unless explicitly enabled, all Linux capabilities dropped, no-new-privileges, and a finite execution timeout. The code comments specifically connect network isolation to metadata access, SSRF, and exfiltration. These controls apply to that executor, not automatically to every tool, MCP server, plugin, or workflow function. [A19] [A20]

Credentials are a runner service and MCP integrations have auth-specific parameters. This is useful for application integration, but the audit did not verify complete secret redaction across every trace/export surface. No blanket claim of enterprise policy enforcement is made. [J2] [A25]

## 8. Extensibility

Plugins apply across the runner's agents; callbacks are agent-local. Plugin order matters: a returned value can short-circuit subsequent plugins and agent callbacks, while in-place modifications propagate to later callbacks. This allows logging, caching, request rewriting, and policy gates, but also means plugin composition needs deliberate tests. A callback that silently suppresses another policy is an integration concern. [A18]

Named request processors provide a second extension seam inside the model flow. Tools and toolsets provide a third. Services—session, memory, artifacts, credentials—are a fourth. These independent seams explain ADK's high flexibility rating: applications can replace storage without replacing the model adapter, or replace prompt processing without reimplementing session persistence. [A5] [A2] [J2]

The source includes skill-toolset implementations in both languages, but this chapter does not claim universal compatibility with every other product's skill discovery or execution conventions. MCP client support is more directly evidenced by the inspected toolset contract. [A25]

## 9. Multi-agent

ADK supports hierarchical agents and explicit workflow nodes. The legacy parallel implementation demonstrates concurrent children and event merging; the newer workflow replay machinery adds node-specific histories and resume ordering. Those mechanisms are application orchestration, not Git worktree isolation. A coding application must still provide independent repositories or execution environments when children may edit concurrently. [A21] [A8] [A9]

An important design choice is to allow orchestration outside the model. A workflow can express routing, dependencies, and interruption points in code rather than rely on a manager prompt to remember them. That generally makes control flow easier to inspect and recover, while making the framework larger than a small embeddable agent loop. [A1] [A9]

## 10. Surfaces & integration

The core surface is an in-process SDK. A host consumes async events from a runner, can use its own services, and can build a CLI or HTTP application around it. The repositories also include development servers, web development tooling, evaluation tooling, and deployment integration. Those product surfaces increase integration value, but the SDK does not require adopting a coding terminal. [A2] [J1] [A28]

The TS browser export broadens deployment possibilities, while server integrations remain subject to their runtime requirements. The appropriate comparison is ADK versus other application frameworks, not ADK versus a fully configured Codex/OpenCode developer workstation. A complete product still needs authentication, session ownership rules, deployment monitoring, and tool policy suited to its users. [J1] [J2]

## 11. Observability & evals

OpenTelemetry dependencies and explicit compaction spans are present in Python. Spans record both contextual attributes and failures, including failures that are intentionally recovered rather than propagated. `AgentEvaluator` provides an evaluation entry point over eval sets, with separate evaluation modules for trajectories and response quality. This is stronger evidence than a README claim that the framework is observable. [A28] [A22] [A26]

No evaluation was executed here. The presence of evaluators does not establish accuracy, latency, cost, or production readiness for a particular application. It establishes that the framework supplies mechanisms for measuring those properties once appropriate datasets and providers are configured.

## 12. Notable design decisions & trade-offs

The event is the unifying abstraction: streaming, persistence, tool responses, interrupts, compaction, and workflow reconstruction all operate on explicit events. This reduces the number of independent state formats an application must reconcile. The trade-off is complexity in event ownership, IDs, branches, ordering, and distinguishing derived summaries from original evidence. [A4] [A7] [A9] [A10]

ADK also makes language parity a real engineering question. Its two implementations have similar high-level objects but different replay details and model integrations. Choose a language based on the required behavior at the pinned version, not on a shared framework name. The deprecation of older composite agents further argues for checking current source before copying familiar examples. [J3] [A21]

## 13. Scorecard

Paired values are **Python / TypeScript**; scores apply only to the verified scope.

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 5 / 4 | Many replaceable services and processing seams; Python inspected more deeply. |
| Integration | 4 / 4 | SDK plus development/deployment/evaluation tooling. |
| Embeddability | 5 / 5 | First-class in-process frameworks. |
| Durability | 4 / 3 | Python replay and persistent session backend; TS narrower rehydration at pin. |
| Safety | 4 / 3 | Python hardened container executor plus confirmations; TS executor parity not established. |
| Extensibility | 4 / 4 | Plugins, callbacks, tools, services, MCP. |
| Multi-agent | 5 / 4 | Workflows and parallel agents; replay parity differs. |
| Provider neutrality | 4 / 3 | Extensible contracts; Python broader inspected adapter surface. |
| Maturity | 4 / 3 | Versioned 2.x packages, with ongoing migrations and uneven parity. |
| Minimalism | 2 / 3 | Service and workflow framework, not a tiny loop. |

## 14. When to build on it / when not to

Choose ADK when explicit sessions, tooling, workflow composition, and cloud-facing integration are central. Python is the better-supported choice in this evidence set for the newer resumable workflow behavior. TypeScript is attractive when its browser/Node packaging and core APIs match the application, after checking the relevant recovery semantics. [A24] [A9] [J1] [J3]

A smaller harness can be preferable when the application only needs a model/tool loop and wants to own every surrounding policy. ADK's framework services offer considerable functionality, but they add configuration and lifecycle concepts. For strong side-effect guarantees, pair persistent execution state with idempotent tools; do not rely on the word "resumability" alone. [A7] [A9]

## 15. Evidence index

Verification: static inspection of the pinned manifests, model loop, resume decisions, replay indexing, parallel-agent merge, compaction, tool schema/confirmation paths, container settings, plugin semantics, and TS rehydration. The references were checked for file existence and valid line bounds. No repository code or tests were executed, and this is not an independent adversarial review. Broader provider/deployment claims remain qualified where only package surfaces were inspected.

[A1]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/apps/app.py#L53-L94 "src/google/adk/apps/app.py:L53-L94"
[A2]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/runners.py#L228-L340 "src/google/adk/runners.py:L228-L340"
[A3]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/flows/llm_flows/base_llm_flow.py#L332-L353 "src/google/adk/flows/llm_flows/base_llm_flow.py:L332-L353"
[A4]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/flows/llm_flows/base_llm_flow.py#L377-L449 "src/google/adk/flows/llm_flows/base_llm_flow.py:L377-L449"
[A5]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/flows/llm_flows/base_llm_flow.py#L174-L275 "src/google/adk/flows/llm_flows/base_llm_flow.py:L174-L275"
[A6]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/flows/llm_flows/core/_resume.py#L46-L79 "src/google/adk/flows/llm_flows/core/_resume.py:L46-L79"
[A7]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/flows/llm_flows/core/_resume.py#L97-L146 "src/google/adk/flows/llm_flows/core/_resume.py:L97-L146"
[A8]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/workflow/utils/_replay_manager.py#L185-L229 "src/google/adk/workflow/utils/_replay_manager.py:L185-L229"
[A9]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/workflow/utils/_replay_manager.py#L246-L314 "src/google/adk/workflow/utils/_replay_manager.py:L246-L314"
[A10]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/runners.py#L924-L959 "src/google/adk/runners.py:L924-L959"
[A11]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/runners.py#L1267-L1367 "src/google/adk/runners.py:L1267-L1367"
[A12]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/runners.py#L1394-L1455 "src/google/adk/runners.py:L1394-L1455"
[A13]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/models/base_llm.py#L36-L100 "src/google/adk/models/base_llm.py:L36-L100"
[A14]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/agents/llm_agent.py#L327-L378 "src/google/adk/agents/llm_agent.py:L327-L378"
[A15]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/tools/function_tool.py#L51-L95 "src/google/adk/tools/function_tool.py:L51-L95"
[A16]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/tools/function_tool.py#L145-L183 "src/google/adk/tools/function_tool.py:L145-L183"
[A17]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/tools/function_tool.py#L251-L300 "src/google/adk/tools/function_tool.py:L251-L300"
[A18]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/plugins/base_plugin.py#L41-L74 "src/google/adk/plugins/base_plugin.py:L41-L74"
[A19]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/code_executors/container_code_executor.py#L318-L345 "src/google/adk/code_executors/container_code_executor.py:L318-L345"
[A20]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/code_executors/container_code_executor.py#L180-L195 "src/google/adk/code_executors/container_code_executor.py:L180-L195"
[A21]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/agents/parallel_agent.py#L92-L174 "src/google/adk/agents/parallel_agent.py:L92-L174"
[A22]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/apps/compaction.py#L110-L145 "src/google/adk/apps/compaction.py:L110-L145"
[A23]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/apps/compaction.py#L790-L907 "src/google/adk/apps/compaction.py:L790-L907"
[A24]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/sessions/database_session_service.py#L310-L355 "src/google/adk/sessions/database_session_service.py:L310-L355"
[A25]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/tools/mcp_tool/mcp_toolset.py#L116-L195 "src/google/adk/tools/mcp_tool/mcp_toolset.py:L116-L195"
[A26]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/evaluation/agent_evaluator.py#L118-L170 "src/google/adk/evaluation/agent_evaluator.py:L118-L170"
[A27]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/src/google/adk/version.py#L15-L16 "src/google/adk/version.py:L15-L16"
[A28]: https://github.com/google/adk-python/blob/69c0b00fc60a35f0a20882f8cddea052e43ba66a/pyproject.toml#L8-L55 "pyproject.toml:L8-L55"
[J1]: https://github.com/google/adk-js/blob/120c28252e57d0bc1ba32c2daabbc0964a4dd50e/core/package.json#L1-L30 "core/package.json:L1-L30"
[J2]: https://github.com/google/adk-js/blob/120c28252e57d0bc1ba32c2daabbc0964a4dd50e/core/src/runner/runner.ts#L90-L129 "core/src/runner/runner.ts:L90-L129"
[J3]: https://github.com/google/adk-js/blob/120c28252e57d0bc1ba32c2daabbc0964a4dd50e/core/src/workflow/utils/rehydration_utils.ts#L7-L67 "core/src/workflow/utils/rehydration_utils.ts:L7-L67"
[J4]: https://github.com/google/adk-js/blob/120c28252e57d0bc1ba32c2daabbc0964a4dd50e/core/src/models/base_llm.ts#L1-L110 "core/src/models/base_llm.ts:L1-L110"
