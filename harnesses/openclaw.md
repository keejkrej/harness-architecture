# OpenClaw and OpenClaw AI

> OpenClaw is an integrated personal-agent platform whose central abstraction is a gateway owning channels, sessions, tools, policy and delivery. At this pin it is **not simply a wrapper around the current Pi coding-agent package**: Pi-derived code has been incorporated into OpenClaw-owned packages, and the remaining direct Pi dependency is its TUI. The product can replace both its agent harness and context engine through plugins. Separately, `@openclaw/ai` is a reusable model/streaming library; the agent-core and gateway-SDK workspace packages are private.

| | |
|---|---|
| Repository | `openclaw/openclaw` @ `f13a8d0ac04d3b0284ada075978ad19677cf67a2` |
| License | MIT; incorporated Pi code is acknowledged in third-party notices |
| Languages / size | Primarily TypeScript, with native applications; 55,741 tracked files, not harness LOC |
| Version at pin | Root and AI package: 2026.10.3; private agent-core: 0.0.0-private |
| Release evidence | [v2026.10.5-beta.3](https://github.com/openclaw/openclaw/releases/tag/v2026.10.5-beta.3), published 2026-10-13; release tag and manifest are distinct facts |
| Category | Product: `integrated-product`; OpenClaw AI: `llm-library` |

Manifest versions and licensing are primary evidence. This review does not reconstruct the first public release or claim a popularity ranking. [Manifest][O1], [Pi notice][O2]

## 1. Layering & package map

```text
Channels / Control UI / CLI / native clients / ACP
                     ↓
Gateway: authenticated control, sessions, routing, delivery
                     ↓
Harness + provider + context-engine plugin contracts
        ↙                                      ↘
OpenClaw embedded harness                 Codex / other harness plugins
        ↓
private @openclaw/agent-core → @openclaw/ai → providers
        ↓
policy-aware tools → host / configured sandbox / remote workspace
```

The built-in harness delegates attempts to `runEmbeddedAttempt`, with explicit host-owned transcript, cancellation and finalization machinery. A plugin can register an alternate harness; the Codex extension actually does so. This is a replacement seam within a large product, rather than proof that all product services are independently embeddable. [O3], [O4], [O5]

The dependency distinction matters. `@openclaw/agent-core` is private despite its exports. `@openclaw/sdk` is also private and depends on gateway client/protocol packages. `@openclaw/ai` instead documents a reusable inference runtime with an explicit provider registry and inert host-policy defaults. Its internal subpaths carry no semver guarantee. [O6], [O7], [O8]

## 2. Agent loop

The embedded loop lives in `packages/agent-core/src/agent-loop.ts`. `runAgentLoop` copies the message context, separates operator/system updates from ordinary prompt input and emits lifecycle events. A continuation entry point can run existing history without introducing a new prompt. The outer product runner prepares workspace, models, skills, tools, prompt and transcript ownership before invoking execution. [O9], [O10]

The loop has nested continuation conditions for outstanding tool calls and pending messages. Steering is checked at execution checkpoints; sequential tails can be skipped to process newly accepted input. Parallel tool groups still pass through admission and completion handling. This is a policy-aware scheduler, not indiscriminate `Promise.all` over every model call. [O11]

An aborted or failed turn interacts with transcript and delivery custody. The product records whether a tool may have produced side effects and restricts blind retries to a narrow safe-tool set. Even a matching name is insufficient when multiple registered tools own that name. These safeguards reduce duplicate effects without claiming a distributed exactly-once guarantee. [O12]

## 3. Model / provider abstraction

OpenClaw AI exports common model contracts, registry, host configuration and streaming primitives. Applications explicitly register built-in providers into an isolated registry; importing the package does not globally register them. Provider IDs, credentials, catalogue policy, retries and failover deliberately remain application responsibilities. This makes it useful below a harness, but incomplete as a turnkey agent runtime. [O8], [O13]

The product supplies those missing policies and can select a native external harness per provider/model route. Harness support is explicit: a plugin can report support, reject a route or request fallback to the built-in runtime. The contract carries prepared authentication and transport requirements, so selecting a model is also selecting an execution path and its authority. [O14]

The root manifest shows SDKs for multiple model families and the workspace AI package. It does not depend on current Pi AI or Pi agent-core as published packages. Pi ancestry should therefore be recorded as incorporated-code lineage; Pi TUI remains a direct dependency. [O2], [O15]

## 4. Tool system

Tool construction combines filesystem/process tools with channel, memory, search and plugin capabilities, then applies provider, conversation and policy filtering. The core file-tool assembly distinguishes host and sandboxed read/write/edit operations and binds action descriptors. The same advertised tool name can consequently have a different execution environment. [O16], [O17]

Tool results have context-sensitive character budgets. The examined default live cap is 16,000 characters, rising to 32,000 or 64,000 for larger contexts, with an additional maximum context-share calculation. These are bounded heuristics, not exact tokenizer counts. Retaining full execution artifacts and deciding which text enters a model request are separate concerns. [O18]

MCP is both an ingestion and exposure mechanism in the wider product. The client configures stdio, SSE or Streamable HTTP servers and subjects their tools to the same profile and tool-policy controls. [O35] The reviewed loopback MCP server exposes gateway-scoped tools to local clients over an authenticated HTTP endpoint bound to localhost. It should not be described as an unauthenticated public tool server. [O19]

## 5. Context management

Workspace bootstrap includes `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, optional root `MEMORY.md` and first-run `BOOTSTRAP.md`. Files are bounded before prompt injection. These are product-owned conventions for a persistent personal agent, rather than a coding-only project prompt. The skills search path includes workspace, `.agents/skills`, user, managed, bundled and extra roots. [O20]

More unusually, context management itself is replaceable. `ContextEngine` has assembly and compaction contracts plus optional bootstrap, maintenance and after-turn operations. It can supply an assembled model projection and explain token-pressure authority. A persistent external harness may receive context once per epoch instead of the entire projection every turn. The host still retains request-admission responsibility. [O21], [O22]

Plugin registration exposes separate context-engine and compaction-provider seams. This enables substantial reshaping without editing the central loop, although the host must reconcile transcript custody, delivery and compatibility across engines. It is a broader extension point than merely swapping a summary prompt. [O4]

## 6. State, sessions & durability

Active session rows and transcripts live in per-agent SQLite storage, with a shared database for broader gateway state. The pinned docs explicitly distinguish active SQLite history from JSONL migration inputs, archives, imports and exports. Package metadata declares SQLite/Postgres engine support; this review does not establish every cross-engine operational guarantee. [O1], [O23]

Gateway restart recovery is more than manually reopening a saved chat. It records recovery custody for admitted turns, preserves committed input and available tool results, and tries to continue an eligible interrupted session. Recovery revalidates the original caller's authority, and a later completed reply/user turn closes old replay eligibility. New input remains queued while recovery waits. [O24]

The code reinforces the limit: read/search/history tools form a narrow audited replay-safe set, owner declarations matter, and side-effecting work is treated differently. Delivery recovery restores exact host-owned constraints, including suppression and restart-safe tool restrictions. This supports a durability score of 4: selective restart continuation and delivery recovery are present, while arbitrary tool effects are not established as deterministic journal replay. [O12], [O25]

Incognito sessions are an intentional exception to durable storage: the docs describe in-memory session/transcript state and expiry on gateway restart. They still permit explicit tool-driven writes elsewhere. A storage policy therefore must not be mistaken for disabling all persistence by agent tools. [O26]

## 7. Safety & sandboxing

The product supports real optional container confinement. Docker creation validates security-sensitive configuration and can set a read-only root, network mode, dropped capabilities, `no-new-privileges`, seccomp/AppArmor profiles and resource limits. This is materially different from approval prompts alone. [O27]

However, the first-party README explicitly says main-session tools run on the host unless sandboxing is configured. The score reflects available controls, not a claim that a default installation confines all tools. Workspace/child policy also affects delegation: sender-restricted children cannot escape their inherited root by requesting a different cwd, project or worktree. [O28], [O29]

Public plugin contracts, private ownership checks and authenticated MCP/ACP access serve different trust boundaries. The built-in harness uses an object-identity check, so an untrusted plugin cannot become the built-in implementation merely by copying its ID. That is a useful example of treating identity as authority-bearing state rather than a cosmetic name. [O3]

## 8. Extensibility

OpenClaw has substantial public plugin surfaces: tools, hooks, channels, providers, context engines, compaction providers and alternate agent harnesses. The hook catalogue includes model input/output and before/after tool calls. These can reshape execution and observability without modifying the product's source. [O4], [O30]

This is distinct from using `@openclaw/ai` alone. The inference library supplies registry/streaming and host transport hooks; it does not include skills, a gateway, conversation persistence, approval UI or subagents. Conversely, a product plugin inherits the gateway lifecycle and cannot assume it owns process-global policy. [O8]

## 9. Multi-agent

Subagent planning resolves child model/thinking settings, inherits execution identity and checks workspace policy. It supports explicit worktree requests subject to caller restrictions. The central platform also routes separate configured agents with their own workspace/session stores. These are different forms of multi-agent support: routing a message to another configured identity is not the same operation as spawning a child task. [O29], [O31], [O20]

External harness plugins add another axis: a child can involve a different runtime rather than another invocation of the embedded loop. The Codex extension demonstrates native harness registration. The review does not infer universal compatibility across every external agent, nor that child side effects can always be replayed safely after restart. [O5], [O12]

## 10. Surfaces & integration

The gateway is the control plane for CLI, channel adapters, browser Control UI and native clients, with a WebSocket protocol and HTTP surfaces. ACP is implemented by an `AgentSideConnection` bridge to the gateway, rather than a second independent agent loop. The MCP loopback server supplies another integration direction. [O32], [O33], [O19]

For a new application, choose the actual boundary required: import OpenClaw AI for inference primitives; build an OpenClaw plugin to participate in its lifecycle; or drive a running gateway as a client. Private workspace package exports do not constitute a separately supported agent-harness distribution. This is why product embeddability scores lower than product flexibility. [O6], [O7], [O8]

## 11. Observability & evals

Diagnostics can be exported through the bundled `diagnostics-otel` service plugin. This is optional integration, not proof that every content-bearing model trace is exported by default. Hook events and gateway lifecycle state provide additional instrumentation points. [O34], [O30]

The repository contains extensive focused tests for steering, replay safety, restart authority, sandbox arguments and protocol behavior. Their existence supports architectural inspection but does not establish measured reliability, security certification or a benchmark win. No source in this clone was executed for this review.

## 12. Notable design decisions & trade-offs

OpenClaw combines high product integration with unusually broad harness replacement. That flexibility costs a large compatibility surface: tool authority, transcript ownership, context epochs, authenticated caller identity and final message delivery must remain coherent when the underlying agent changes.

Its Pi relationship has also changed from the simple package dependency commonly associated with earlier architectures. Incorporated code and public provider primitives coexist with a private, product-specific agent core. The current graph is a stronger basis for a build decision than a statement that OpenClaw either “is Pi” or has no Pi connection.

## 13. Scorecard

| Dimension | Product | OpenClaw AI | Rationale |
|---|---:|---:|---|
| Flexibility | 5 | 5 | Replaceable harness/context/provider contracts; configurable inference registry |
| Integration | 5 | 1 | Complete gateway product versus model primitives |
| Embeddability | 3 | 5 | Product protocols/plugins; directly importable AI package |
| Durability | 4 | 1 | Selective restart and delivery recovery; inference library has no session store |
| Safety | 4 | 1 | Optional container policy and approvals; library delegates host policy |
| Extensibility | 5 | 3 | Rich product plugin lifecycle versus provider/transport extension |
| Multi-agent | 5 | 1 | Routed agents, children, worktrees and alternate harnesses; absent in AI layer |
| Provider neutrality | 5 | 5 | Multiple provider adapters and application-controlled registry |
| Maturity | 4 | 3 | Versioned product; reusable package boundary has narrower evidence |
| Minimalism | 1 | 3 | Very large integrated platform; much smaller responsibility at AI layer |

## 14. When to build on it / when not to

Use OpenClaw when channels, persistent personal context, routing and ongoing operation are central requirements. Its plugin seams let you change a surprising amount of harness behavior while retaining that product. Use OpenClaw AI when only model transport/streaming is needed and the application will own policy, storage and orchestration.

Do not adopt the complete gateway merely to obtain a minimal coding loop. Do not depend on private agent-core exports as if they were a stable published SDK, or assume main-session execution is sandboxed by default. These are concrete distinctions between reuse paths, rather than an overall ranking.

## 15. Evidence index

Pinned source and in-repository documentation are linked below. GitHub release metadata was checked **2026-10-14**. No runtime, network-isolation or crash-injection tests were run. Negative feature claims apply to the layer named; the inference library's missing features are often present in the complete product.

[O1]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/package.json#L1-L25
[O2]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/THIRD_PARTY_NOTICES.md#L1-L15
[O3]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/harness/builtin-openclaw.ts#L82-L107
[O4]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/plugins/plugin-api.types.ts#L373-L389
[O5]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/extensions/codex/index.ts#L260-L277
[O6]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/packages/agent-core/package.json#L1-L25
[O7]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/packages/sdk/package.json#L1-L29
[O8]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/packages/ai/README.md#L1-L50
[O9]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/packages/agent-core/src/agent-loop.ts#L85-L144
[O10]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/embedded-agent-runner/run/attempt.ts#L30-L99
[O11]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/packages/agent-core/src/agent-loop.ts#L573-L646
[O12]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/tool-replay-safety.ts#L1-L87
[O13]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/packages/ai/src/index.ts#L1-L5
[O14]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/harness/types.ts#L27-L65
[O15]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/package.json#L2280-L2301
[O16]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/agent-tools.ts#L1-L80
[O17]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/core-coding-tools.ts#L13-L51
[O18]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/tool-result-limits.ts#L1-L63
[O19]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/gateway/mcp-http.ts#L60-L65
[O20]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/docs/concepts/agent.md#L8-L93
[O21]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/context-engine/types.ts#L1-L43
[O22]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/context-engine/types.ts#L350-L383
[O23]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/docs/concepts/agent.md#L93-L105
[O24]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/docs/concepts/session.md#L246-L305
[O25]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/agent-command-restart-recovery.ts#L33-L67
[O26]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/docs/concepts/session.md#L160-L170
[O27]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/sandbox/docker.ts#L193-L279
[O28]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/README.md#L70-L81
[O29]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/subagents/spawn/subagent-spawn-child-plan.ts#L33-L62
[O30]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/plugins/hook-types.ts#L96-L123
[O31]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/agents/subagents/spawn/subagent-spawn-plan.ts#L35-L84
[O32]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/docs/concepts/architecture.md#L9-L25
[O33]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/src/acp/server.ts#L1-L34
[O34]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/extensions/diagnostics-otel/index.ts#L1-L11

[O35]: https://github.com/openclaw/openclaw/blob/f13a8d0ac04d3b0284ada075978ad19677cf67a2/docs/tools/mcp.md#L10-L24
