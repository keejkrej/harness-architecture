# Cline SDK, Cline applications, and Kilo Code

> These are no longer adequately described as two variants of one VS Code task loop. At the pins, **Cline has a deliberately layered, publicly exported SDK**: `@cline/agents` supplies a host-independent loop; `@cline/core` adds the coding harness; `@cline/sdk` re-exports core. **Current Kilo CLI is an OpenCode fork**, with a private extracted core, native and AI SDK inference paths, a subprocess/server SDK, and its own sandbox package. For a new in-process harness, Cline deserves a library evaluation. For a ready coding product with custom clients, evaluate Kilo's protocol boundary.

| | Cline | Kilo |
|---|---|---|
| Repository / pin | `cline/cline` @ `789f79e46d3ba579717e8dc8be35fe28af935b06` | `Kilo-Org/kilocode` @ `4ee8d1b3b1f8cadefa925c9959dcbda7f87100da` |
| License | Apache-2.0 SDK | MIT |
| Language / size | TypeScript; 4,280 tracked files | TypeScript; 10,935 tracked files |
| Version at pin | SDK packages 0.0.93; product release line separately versioned | CLI/core/SDK 7.8.9 |
| Release evidence | [v4.1.24 product release](https://github.com/cline/cline/releases/tag/v4.1.24), 2026-10-13 | [v7.8.9](https://github.com/Kilo-Org/kilocode/releases/tag/v7.8.9), 2026-10-13 |
| Classification | Harness libraries plus integrated applications | Integrated product |

Versions above come from package manifests and release metadata, not an assumption that the product release and SDK versions match. First public release dates and the exact migration dates were not reconstructed from these shallow snapshots. The old Cline/Roo association is historical context; current architectural lineage is explicitly documented as OpenCode in Kilo's own README. [Cline SDK manifest][C1], [Kilo CLI manifest][K1], [Kilo lineage][K2].

## 1. Layering & package map

```text
Cline applications (CLI, desktop, IDE hosts)
  → @cline/sdk → @cline/core (sessions, tools, teams, hub, storage)
                       → @cline/agents (loop, tools supplied by host)
                            → @cline/llms → AI SDK providers

Kilo CLI / VS Code / other clients
  → OpenCode-derived product services + Kilo additions
    → private @opencode-ai/core, @opencode-ai/llm
    → @kilocode/sandbox and provider integrations
External @kilocode/sdk → spawn `kilo serve` + HTTP client
```

Cline's package split is functional: the agents README explicitly excludes host tools, storage and team orchestration; core owns those responsibilities. The SDK's implementation is a one-line re-export of core, so it is not a fourth independent engine. The lower-level agent API accepts either provider configuration or a preconstructed model. This creates a usable seam for custom hosts. [C2], [C3], [C4]

Kilo has extracted an Effect-based core package, but marks it `private: true`. A second private package, `@opencode-ai/sdk-next`, contains a real in-process embedding prototype: it builds the application layer, routes HTTP requests through an in-memory fetch handler and returns a client with tool registration. Its manifest still says `private: true`; this is a distinct boundary from the published subprocess SDK. Source exports do not by themselves make it a supported published library. [K26], [K27] Its CLI package remains `packages/opencode`, and contribution rules explicitly preserve upstream code while adding Kilo-specific directories. [K3], [K4]

## 2. Agent loop

**Cline:** `AgentRuntime` initializes plugins/hooks, appends input, prepares a model request, streams assistant events, executes tool calls and repeats until completion, cancellation or an iteration limit. `run`, `continue`, `abort`, `snapshot` and `restore` are explicit APIs. Provider retries and context-overflow recovery are separate paths; restoring messages is not equivalent to restoring a suspended process. [C5], [C6]

Tool scheduling defaults to sequential. A tool can override the execution mode; only adjacent parallel calls overlap, preserving sequential barriers between batches. That is more precise than saying all calls are parallel or all calls are serial. Before/after hooks exist at run, model and tool boundaries, with a common event observer. [C7], [C8]

**Kilo:** the CLI session processor consumes a normalized LLM event stream and returns `compact`, `stop` or `continue`. It captures a file snapshot before generation because an AI SDK tool may execute before a start-step event is emitted. Retry eligibility checks whether text, reasoning or tool activity has already occurred, reducing unsafe retries after visible work. [K5]

The extracted core has a session runner and a coordinator that serializes execution per session while allowing different sessions to run concurrently. A coalesced wake schedules follow-up work; interruption waits for cleanup. These structures are real, but the repository also retains V1 bridging code, so this review does not flatten every path into one newly extracted engine. [K6], [K7]

## 3. Model / provider abstraction

Cline's `@cline/llms` provides gateway, provider and model abstractions, backed by AI SDK implementations. Its manifest includes Anthropic, OpenAI, Google, Vertex, Bedrock, Mistral, OpenRouter, compatible endpoints, Ollama and optional agent-product adapters. The pinned dependency is AI SDK 7, while Kilo's root catalogue pins AI SDK 6. These packages therefore share a dependency family, not necessarily identical provider behavior. [C9], [K8]

Kilo supports both a native `@opencode-ai/llm` runtime path and an AI SDK bridge. The latter maps text/reasoning/tool events and preserves cache token counts and provider billing metadata. A native-runtime support check can report an unsupported route; merely finding native adapter files does not prove every provider takes that path. [K9], [K10]

Both systems retain provider-specific behavior behind normalized interfaces. Reasoning replay, cache accounting and token ceilings should be tested against the intended provider before migration; a shared message type is not a promise of lossless equivalence across vendors.

## 4. Tool system

Cline's low-level `AgentTool` takes a JSON Schema and an execution function with cancellation and progress reporting. It does not ship a filesystem or shell just because the loop is installed. Core supplies default tools and executors, MCP integration, approvals and delegation. This distinction is useful when embedding in a browser, where a Node coding toolbox would be inappropriate. [C2], [C3]

The higher-level spawn tool uses a Zod schema and forwards explicit tool sets, lifecycle hooks, extensions and tool policies into children. A host can therefore constrain a delegate instead of inheriting an opaque global toolbox. [C10]

Kilo's task tool supports resumable task IDs, foreground/background execution and model-selection additions. It preserves child-session identity in its output. File effects are coupled to snapshots, while the inference layer normalizes tool execution results. Neither system's tool schema alone is a security boundary: execution policy and the runtime doing the work determine authority. [K11], [K5]

## 5. Context management

Cline core owns compaction rather than forcing it into the runtime-independent loop. Its prepare-turn integration budgets messages against the outgoing request, supports basic and agentic compaction, and records whether compaction was manual, automatic or overflow recovery. Provider-reported previous request usage can inform preparation. Rules, `AGENTS.md`, skills and workflows are loaded separately, with structured skill frontmatter and plugin provenance. [C11], [C12]

Kilo's compaction layer combines token-pressure handling with tool-output pruning. Its inspected constants protect a recent budget and retain skills; serialized old tool results can become bounded excerpts. Instruction discovery understands `AGENTS.md` and optionally `CLAUDE.md`, with Kilo-specific restrictions against project instruction settings reading outside the project root. [K12], [K13]

Context reduction is not deletion of all original history. The active model projection, display transcript, stored messages and file snapshots serve different purposes. Integrators should ask which one an export or restore operation returns rather than assuming they are interchangeable.

## 6. State, sessions & durability

The bare Cline agent owns an in-memory conversation and supports restoring messages. Core adds SQLite sessions, metadata, artifacts and team state. The examined store opens `sessions.db` and applies the session schema. File checkpoint restoration has a transaction helper that preserves tracked and untracked workspace contents behind a private Git reference until commit or rollback. That is a file-recovery mechanism, not a journal of arbitrary external effects. [C13], [C14]

Kilo's SQLite/Drizzle session schema stores parent/workspace IDs, usage, cost, permissions and revert metadata. Its coordinator can drain recorded work and resume conversations, but the evidence reviewed here does not establish deterministic, per-effect crash replay comparable to Vibe's unified write-ahead runtime. The score remains 3 rather than inferring full durability from the word `durable` in a runner comment. [K14], [K6]

For both, an external command can finish before its result is durably saved. The application can preserve conversation continuity without guaranteeing exactly-once effects. The Cline agent package alone is scored 1 for durability; core and applications receive 3 because they add persistence and resume.

## 7. Safety & sandboxing

Cline supplies approvals and host policy hooks. Even the low-level loop enforces disabled-tool policy and can request approval; when approval is required but no callback exists, it denies the call. [C19] Its desktop approval bridge denies when IPC is unconfigured and times out to denial. Plugin execution can use a child process or worker thread; the source names this a sandbox, but the mechanism examined is process/worker separation, not proof of filesystem/network confinement. The matrix therefore does not equate Cline's plugin sandbox with an OS sandbox. [C15], [C16]

Kilo's separate sandbox package contains actual platform backends: Seatbelt on macOS and Bubblewrap on Linux. Windows returns an unavailable result. A configured confinement attempt fails if support is unavailable; the unprofiled path can pass through normally. Its public exports include filesystem, HTTP/network and environment controls. Thus OS sandbox support is real but platform- and activation-dependent, not universal default confinement. [K15], [K16]

These differences justify a higher safety score for Kilo than for the bare Cline SDK. They do not establish that all optional tools, remote providers or extension subprocesses are confined in every deployment. This review did not execute adversarial sandbox tests.

## 8. Extensibility

Cline exposes both low-level lifecycle hooks and a higher-level plugin system. Plugin registration includes tools, commands, rules and message builders, with import/setup/hook/tool timeouts and a consecutive-failure threshold. MCP and skill packages belong to the core layer. This is a significantly more deliberate extension API than modifying private IDE internals. [C8], [C17]

Kilo's plugin service loads `@kilocode/plugin` hooks, provider/auth integrations and workspace adapters, with Kilo additions alongside OpenCode-derived functionality. Its MCP, skills and custom tools should be evaluated as product extension points; the external SDK is a client interface rather than an alternate way to import the whole loop. [K17], [K18]

## 9. Multi-agent

Cline core explicitly owns subagents and teams. The spawn tool accepts per-child configuration, and the public core documentation identifies storage-backed team state and a SQLite team store. The loop-only package intentionally has none of that orchestration. Durable team records do not automatically make every child task survive process death. [C3], [C10]

Kilo supplies background task sessions and a managed worktree API with create/remove/reset operations. These are complementary facilities; a task call does not prove every child automatically receives a separate worktree. Cross-session serialization and resumable task identifiers give a stronger orchestration base than a stateless recursive model call. [K11], [K19]

## 10. Surfaces & integration

Cline's SDK is genuinely in-process: `ClineCore.create`, `start` and `dispose` are documented, and the public SDK manifest exports the built package. Hosts can select local, hub or remote runtime abstractions. The repository includes CLI, VS Code and desktop applications; the README explicitly says the JetBrains plugin is not open-sourced here. It is therefore incorrect to count the whole advertised IDE ecosystem as source-audited. [C1], [C3], [C18]

Kilo's `createKilo` starts a server and creates a client. `createKiloServer` actually launches the `kilo serve` executable with host/port/configuration options, then parses its ready message. This makes embedding operationally convenient, but it remains subprocess integration. CLI, IDE clients and hosted cloud features are advertised; hosted backend behavior was not independently reconstructed from this repository. [K18], [K20]

Additional verified integration surfaces include Cline core's HTTP/WebSocket hub and Kilo's ACP bridge. Cline core models `act`/`plan` explicitly; the product documents switching between those modes. Shared web UI components and IDE webviews are present, while Kilo also advertises a hosted cloud experience whose deployment was not inspected. [C22], [C23], [K28] Kilo has an MCP client with stdio, SSE and Streamable HTTP transports, `SKILL.md` discovery, and a built-in plan agent whose edit policy denies arbitrary writes while allowing plan documents. These are product capabilities; they do not turn the subprocess SDK into an in-process loop. [C21], [K22], [K23], [K24], [K25]

## 11. Observability & evals

Cline emits lifecycle, stream and usage events. Its Langfuse integration constructs an OpenTelemetry `NodeTracerProvider` and span processor, rather than merely declaring an unused dependency. [C20] Core's compaction integration explicitly documents a telemetry gap: compaction performed via plugin message builders is not covered by that specific instrumentation. This is a useful reminder that an OTel dependency is not proof every execution path has an equivalent trace. [C8], [C9], [C11]

Kilo core constructs an OTLP trace exporter and batch span processor when an endpoint is configured; without one its tracing layer is empty. It also preserves provider usage/billing metadata in its AI SDK bridge. [K21] The repository has focused unit, integration and protocol testing surfaces. This review reports those mechanisms, not benchmark scores or a claim that either product is empirically more reliable. [K3], [K9]

## 12. Notable design decisions & trade-offs

The comparison changes depending on the layer selected. Cline's agent loop is small in responsibility, but obtaining its full coding behavior requires core. Kilo has internal modularity and strong product integration. Its published SDK keeps the process boundary, while its private SDK-next demonstrates a separate in-process approach. Neither package count nor an `SDK` name alone answers the embedding question.

Cline's public SDK remains labelled experimental at 0.0.93, despite a much older product release lineage. Treat API stability and product maturity separately. Kilo is simultaneously maintaining its OpenCode-derived product and extracting core services; consumers of internal source exports inherit that migration churn. The safest architecture claim is the one supported by the current import graph, rather than the reputation of an earlier release.

## 13. Scorecard

Scores cover the low-level loop, the coding harness, and the two products separately. `@cline/sdk` and `@cline/core` are one implementation for this purpose.

| Dimension | Cline agents | Cline SDK/core | Cline product | Kilo | Rationale |
|---|---:|---:|---:|---:|---|
| Flexibility | 5 | 4 | 4 | 4 | Supplied model/tools/hooks versus product-specific services |
| Integration | 1 | 3 | 5 | 5 | Libraries omit UI; products include multiple clients |
| Embeddability | 5 | 5 | 4 | 3 | Cline public in-process packages; Kilo public subprocess SDK/private embedding prototype |
| Durability | 1 | 3 | 3 | 3 | Core/product storage and resume; bare loop is memory-only |
| Safety | 2 | 3 | 3 | 4 | Host policy versus actual optional platform confinement |
| Extensibility | 4 | 5 | 5 | 4 | Hooks, plugins, MCP and host extension mechanisms |
| Multi-agent | 1 | 4 | 4 | 4 | Teams belong to Cline core; Kilo task/worktree orchestration |
| Provider neutrality | 5 | 5 | 5 | 5 | Broad provider adapters plus compatible endpoints |
| Maturity | 2 | 2 | 4 | 4 | Experimental SDK distinct from established product lines |
| Minimalism | 4 | 2 | 1 | 1 | Responsibility separation does not make full products small |

## 14. When to build on it / when not to

Start with Cline agents when you need your own tools and runtime policy, and with Cline core when you want sessions, coding tools, plugins and teams already assembled. Budget for experimental API change. Choose a Cline application when the desired experience is already its IDE, terminal or desktop product.

Choose Kilo when an OpenCode-derived integrated product, its local server and optional Linux/macOS confinement fit the requirements. Use its published SDK to control that service; the private SDK-next is an experimental source-level reuse option. Do not choose it on the assumption that its current engine is a reusable Cline fork, or that `@kilocode/sdk` removes the server dependency.

## 15. Evidence index

All source references below resolve to the pinned commits. Release metadata was checked through GitHub's first-party API on **2026-10-14**. Research was static; no cloned source was executed. Historic Cline/Roo lineage is not used to infer current Kilo behavior. Unknown matrix entries cover surfaces not established by this review.

[C1]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/sdk/package.json#L1-L36
[C2]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/agents/README.md#L1-L28
[C3]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/README.md#L1-L122
[C4]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/sdk/src/index.ts#L1
[C5]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/agents/src/agent-runtime.ts#L623-L686
[C6]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/agents/src/agent-runtime.ts#L787-L850
[C7]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/agents/src/agent-runtime.ts#L2333-L2372
[C8]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/agents/src/agent-runtime.ts#L707-L740
[C9]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/llms/package.json#L51-L80
[C10]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/src/extensions/tools/team/spawn-agent-tool.ts#L29-L100
[C11]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/src/extensions/context/compaction.ts#L254-L310
[C12]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/src/extensions/config/user-instruction-config-loader.ts#L11-L80
[C13]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/src/services/storage/sqlite-session-store.ts#L20-L60
[C14]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/src/session/checkpoint-restore.ts#L15-L69
[C15]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/src/runtime/tools/tool-approval.ts#L29-L40
[C16]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/src/extensions/plugin/plugin-sandbox.ts#L37-L66
[C17]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/src/extensions/plugin/plugin-registry.ts#L29-L40
[C18]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/README.md#L115-L135
[K1]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/package.json#L1-L29
[K2]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/README.md#L159-L163
[K3]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/core/package.json#L1-L80
[K4]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/AGENTS.md#L175-L180
[K5]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/session/processor.ts#L116-L177
[K6]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/core/src/session/runner/index.ts#L1-L28
[K7]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/core/src/session/run-coordinator.ts#L1-L70
[K8]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/package.json#L33-L72
[K9]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/session/llm/ai-sdk.ts#L1-L70
[K10]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/session/llm/native-runtime.ts#L1-L49
[K11]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/tool/task.ts#L30-L90
[K12]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/session/compaction.ts#L39-L95
[K13]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/session/instruction.ts#L65-L106
[K14]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/core/src/session/sql.ts#L24-L60
[K15]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/kilo-sandbox/src/backend.ts#L38-L94
[K16]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/kilo-sandbox/src/index.ts#L1-L8
[K17]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/plugin/index.ts#L1-L60
[K18]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/sdk/js/src/index.ts#L1-L21
[K19]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/worktree/index.ts#L25-L48
[K20]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/sdk/js/src/server.ts#L55-L86

[C19]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/agents/src/agent-runtime.ts#L2465-L2505

[C20]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/llms/src/services/langfuse-telemetry.ts#L405-L419
[C21]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/src/hub/server/hub-websocket-server.ts#L492-L499
[K21]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/core/src/observability/otlp.ts#L50-L79
[K22]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/acp/agent.ts#L1-L26
[K23]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/mcp/index.ts#L15-L26
[K24]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/skill/index.ts#L27-L41
[K25]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/opencode/src/agent/agent.ts#L184-L203

[C22]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/sdk/packages/core/src/types/chat-schema.ts#L1-L19
[C23]: https://github.com/cline/cline/blob/789f79e46d3ba579717e8dc8be35fe28af935b06/README.md#L140-L146
[K26]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/sdk-next/package.json#L1-L19
[K27]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/packages/sdk-next/src/opencode.ts#L1-L42
[K28]: https://github.com/Kilo-Org/kilocode/blob/4ee8d1b3b1f8cadefa925c9959dcbda7f87100da/README.md#L76-L84
