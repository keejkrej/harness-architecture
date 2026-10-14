# Building on a harness

For a new application, choose the **execution boundary** before comparing product features. Decide whether your process owns the loop, connects to a persistent agent service, or starts an existing product. These choices determine what can be replaced, how failures propagate and which interfaces must remain compatible.

## Four integration contracts

| Contract | Examples | What the application can control | Cost to account for |
|---|---|---|---|
| Direct in-process library | Pi core/coding agent/Durable, AI SDK, Flue, Deep Agents, Strands, Cline Agents/Core, OpenAI Agents SDK, Pydantic AI, ADK | Construct agent/tool objects; observe events; often replace providers, context and storage | Host lifecycle, credentials, cancellation, concurrency and policy; libraries vary considerably in what is included |
| Framework application/runtime | Eve, Mastra deployments, LangGraph deployments, ADK workflow applications | Define agents, tools and workflows within runtime conventions | Storage, worker deployment, runtime upgrades, serialization and recovery contracts |
| Agent service or subprocess | Codex app-server/SDK, Grok stream protocol, Kimi wire/ACP, Claude Agent SDK, product gateways | Start/resume sessions, stream messages and answer approvals through a protocol | Product owns loop semantics; transport errors and child lifecycle need handling; protocol compatibility is separate from SDK package compatibility |
| Source fork or internal imports | Internal modules in many products; unpublished SDK prototypes | Potentially change everything | No independent public API promise; coupling to product auth, storage, UI and build infrastructure |

Each row is a contract, not an exclusive project category. OpenCode V2 supports an embedded host as well as a server. OpenHands separates an in-process agent from local/remote workspaces and server clients. Cline's public Core is distinct from its applications. A Python module being importable from a checkout does not itself establish a supported standalone SDK. [OpenCode](../harnesses/opencode.md), [OpenHands](../harnesses/openhands.md), [Cline](../harnesses/cline-kilo.md), [Hermes](../harnesses/hermes-agent.md), [Vibe](../harnesses/mistral-vibe.md).

## Where the actual seam is

| Candidate | Useful reusable seam | Responsibility that remains visible |
|---|---|---|
| [Pi core](../harnesses/pi-core.md) | Pi-ai transport/messages plus Agent loop and callbacks | Product tools, context policy, persistent sessions, sandbox and delegation |
| [Pi coding agent](../harnesses/pi-coding-agent.md) | AgentSession SDK and extension API | Host authorization/isolation; sessions do not turn arbitrary tools into durable effects |
| [Pi Durable](../harnesses/pi-durable.md) | Task/agent runtime, store and execution-environment interfaces | Single-writer operation, tool replay policy, scheduler/hosting and user surfaces |
| [Flue](../harnesses/flue.md) | Agent authoring/runtime, interceptors and runtime/sandbox adapters | Deployment adapter semantics; opt-in step boundaries and side-effect reconciliation |
| [AI SDK](../harnesses/ai-sdk.md) | Model adapters, generate/stream and ToolLoopAgent; UI bindings | Long-lived state, lifecycle, policy and tools; Workflow integration is an additional choice |
| [Deep Agents](../harnesses/deepagents.md) | Graph factory, middleware, backends and subagent configuration | Checkpointer selection, worker service and backend execution isolation |
| [Strands](../harnesses/strands.md) | Agent, hooks, session/context managers and harness factory | Persistence policy, execution environment and background-worker lifecycle |
| [OpenAI Agents SDK](../harnesses/openai-agents-sdk.md) | Runner, tool/guardrail/handoff contracts, state and sandbox-agent interfaces | Backend-specific isolation; durable workflow deployment; Python/JS feature differences |
| [Mastra](../harnesses/mastra.md) | Agent/workflow/workspace/storage/processor interfaces | Durable recovery policy and deployment; code-product features are a separate layer |
| [Eve](../harnesses/eve.md) | Filesystem-authored agent application and extensible server runtime | Workflow/Nitro deployment and trusted application callbacks |
| [Cline Agents/Core](../harnesses/cline-kilo.md) | Small runtime versus larger session/tool/host services | Choose the layer deliberately; Core brings more infrastructure than Agents |
| [OpenCode V2](../harnesses/opencode.md) | Embedded routes and explicit host/services; also HTTP/SDK clients | Persistent database configuration, ownership on restart and product-sized state machinery |
| [OpenHands](../harnesses/openhands.md) | Agent/conversation, tools, condensers and workspace contracts | Confirmation policy and executor backend; remote-agent wrappers have different control semantics |
| [Pydantic AI/Harness](../harnesses/python-frameworks.md) | Typed Python agent contracts; separate harness/persistence facilities | Which runtime owns durable steps; unknown tool outcomes still need explicit policy |

The strongest evidence for embeddability is a public entry point constructing the execution engine and accepting host dependencies. A generated REST client, a helper that runs `serve`, and a private package with useful exports are different evidence. This is why the matrix gives Cline's public library separate rows, qualifies Kilo's private embedding prototype, and does not assign Claude Agent SDK the same embedding score as a directly executed loop.

## A host API worth demanding

Use the source chapters to check these concrete seams before committing to a candidate:

1. **Run ownership:** who starts, stops, resumes and serializes a session? Can two callers accidentally run it at once?
2. **State ownership:** can the application choose the durable store and tenant/session identity? What state remains only in memory?
3. **Tool admission and execution:** can the host validate identity, arguments and approval before the side effect? Can it move execution into another process or machine?
4. **Context assembly:** can it inspect the actual model request, transform messages and retain artifacts after compaction?
5. **Events and backpressure:** can a slow or disconnected UI resume observation without restarting execution or losing terminal status?
6. **Provider substitution:** which model features survive the adapter, and which paths require one vendor's protocol?
7. **Recovery and upgrades:** which persisted schemas and code versions must match? How are in-flight effects classified after a crash?
8. **Extension authority:** do plugins, hooks and MCP servers run with the host's credentials? Can the host restrict them independently?

These are proposed integration checks, not executed compatibility tests. The study did not build a common adapter against every framework. The shortlist in [recommendations](recommendations.md) is therefore a starting point for a small application-specific trial, with [recovery experiments](durability.md#what-to-test-before-choosing-a-runtime) and explicit [execution boundaries](safety.md).
