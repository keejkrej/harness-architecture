# fx, agentOS, and OpenHarness: three different experimental directions

> fx is a native coding agent with an intentionally reusable JavaScript engine and a real durable-session layer. agentOS is execution infrastructure—a WebAssembly/V8 operating environment that can sit beneath many harnesses, not an agent loop. OpenHarness is an opinionated Python coding product with tools, permissions, compaction, plugins, and swarms. They belong in the landscape, but a single combined score would be meaningless.

| | fx / libfx | agentOS | OpenHarness |
|---|---|---|---|
| Repository / pin | `vercel-labs/fx` @ `b877f4dcc57d` | `rivet-dev/agentos` @ `4d48628304c1` | `HKUDS/OpenHarness` @ `9b2efd795c6a` |
| License | Apache-2.0 | Apache-2.0 | MIT |
| Languages | Zig core; JS SDK | TypeScript + Rust, packaged guest programs | Python; TS UI |
| Tracked files | 1,170 | 2,797 | 480 |
| Version at pin | `libfx` manifest `0.0.0` placeholder | core manifest `0.0.1` | `openharness-ai` `0.1.9` |
| Category | `hybrid` | `execution-runtime` | `hybrid` |
| Evidence scope | 2026-10-14 snapshot, explicitly experimental | 2026-10-12 snapshot; performance claims not reproduced | 2026-06-04 snapshot; product-port intent in manifest |

The version values above are source metadata, not claims about the current package registry or first release. fx's README calls the product experimental. OpenHarness describes itself as a Python port of a coding assistant; this chapter analyzes its public code and does not infer official compatibility or affiliation. [F1] [F2] [A2] [O1]

## 1. Layering & package map

```text
fx CLI / ACP / Node addon / WebAssembly
   -> Zig agent runtime + tools + permissions + compactor
libfx createFxAgent -> JS durable-session core -> fx harness adapter -> engine
                     -> local / Workflow World backend
agentOS JS API -> native sidecar -> Rust kernel/VFS + Wasm/V8 execution
                -> explicit mounts, host functions, permission policy
OpenHarness CLI / terminal UI -> QueryEngine -> run_query -> API client
                                                -> tool registry + permission checker
                    sessions / compaction / hooks / plugins / swarm
```

fx has two deliberate reuse boundaries. `createFxEngine` is a single conversation engine without the higher session store; `createFxAgent` uses a durable-session factory whose small harness contract can drive that engine. The JS session layer therefore does not need to know every Zig tool or UI detail. This is stronger embeddability evidence than a CLI with a JSON output flag alone. [F3] [F4] [F5]

agentOS exposes a library API but places execution in a shared native sidecar. `AgentOs.create` forwards package references and VM configuration rather than staging a conventional host install per agent. "In-process library" describes how an application calls it; it should not be read as all untrusted guest execution sharing the ordinary Node JavaScript context. [A4] [A5]

OpenHarness keeps the model request loop separate from its `BaseTool`/registry and execution context. Yet sessions, prompt conventions, hooks, and coding tools make it a product-oriented harness, not a bare provider library. [O2] [O5]

## 2. Agent loop

fx's native runtime has an explicit step-limited loop, prompt/context reconstruction, model streaming, tool admission, interruption, and finalization components. It schedules eligible prefixes of read-only operations together and has separate concurrent subagent/host-tool handling. Host concurrency is bounded; single-threaded builds cannot use the same concurrency behavior as native threaded builds. This matters when comparing the Node addon and WASM surfaces. [F13] [F12]

The durable JS worker is an outer loop: queue a prompt, acquire a session lease, drive pending turns, and yield/requeue work when time is exhausted. That is different from the inner LLM/tool loop. Keeping them separate allows server lifecycle recovery without forcing the Zig engine to own a cloud scheduler. [F4] [F5]

agentOS has no model/tool decision loop in the inspected API. It evaluates code, executes processes, stores files, and exposes capabilities to callers. An agent harness can use it as an environment tool, but model choice, conversation policy, termination, and agent delegation belong above it. The code-execution example takes an already-produced program and evaluates it directly. [A11]

OpenHarness's `run_query` checks automatic compaction before a model request, streams text/status events, handles completed model messages, and exits when there are no tool uses. One tool runs directly; several run with `asyncio.gather(return_exceptions=True)`, and failures become tool-result blocks so sibling calls are not silently abandoned. It then appends all results and makes the next model request, bounded by `max_turns` when configured. [O2] [O3]

## 3. Model / provider abstraction

fx's SDK accepts a model and instructions separately from tools and execution host. Its documented default transport is AI Gateway, with subscription and OpenAI-compatible paths also available. Broad model access through a gateway is different from implementing every provider natively; provider neutrality should be interpreted with that routing dependency in mind. [F3] [F1]

OpenHarness has provider/auth detection for Anthropic, OpenAI-compatible endpoints, Copilot, and subscription-oriented paths. Its tool schema is shaped like Anthropic Messages input schemas, and adapters translate requests as needed. The provider helper explicitly marks voice support unavailable in several paths, which cautions against deriving capabilities solely from a UI mode or a vendor name. [O14] [O5]

agentOS is model-independent in a more literal sense: the execution API has no required model provider. This is not scored as "5 providers" because the provider axis is inapplicable to its role. It can host model-produced programs from any caller while making no decision about inference, reasoning tokens, or prompt caches. [A3] [A11]

## 4. Tool system

libfx lets JS hosts supply tools to the native engine. The durable adapter wraps tool execution so no tool starts before the worker's claim is valid. It also requires each tool to declare whether repeating a call is safe. This is an unusually explicit integration contract: idempotency cannot be guessed from a tool's name or description. [F7]

The native coding product adds filesystem, shell, search, web, subagent, and related capabilities. Tool-result accounting tracks successes, errors, writes, and repeated identical failures; it preserves tool-result identities in the conversation. Execution scheduling distinguishes read-only tools from writers rather than treating every generated tool batch as freely parallel. [F11] [F12]

agentOS offers process, filesystem, JavaScript/TypeScript, networking, mounts, and trusted host-function interfaces. A host function is the bridge to privileged application behavior; the guest need not receive a raw credential merely to request that behavior. That capability remains only as narrow as the callback and policy the host supplies. [A3] [A6] [A8]

OpenHarness tools declare a Pydantic input model, an async executor, and whether a specific invocation is read-only. Registry schema generation exports those models. The query path parses/normalizes tool arguments before extracting paths and asking the permission checker. This separation makes schema errors and permission decisions visible before execution. [O5] [O4]

## 5. Context management

fx has one compactor used by manual compaction, automatic compaction, and overflow recovery. It retains recent turns, assigns handles to older messages/tools/compactions, produces notes, validates them against saved records, and exposes search over the saved material. The interesting architecture is that compaction produces a smaller model projection while original records remain addressable. It is not a promise that summarization is lossless. [F10]

The product discovers skills, MCP, and project instructions; its SDK lets applications supply their own tools and instructions. The CLI's defaults and an embedded engine's context policy should be assessed separately. A custom JS host does not automatically inherit every local project-discovery decision merely by importing the library. [F14] [F3]

OpenHarness uses a cheap microcompaction stage that clears older tool results and a full LLM summary path when needed, plus reactive compaction for prompt-too-long failures. Project instruction discovery walks upward looking for `CLAUDE.md`, `.claude/CLAUDE.md`, and rules files, with per-file character bounds. This qualifies as project instruction support; it does not prove literal `AGENTS.md` compatibility. [O9] [O13] [O2]

agentOS has files and persistent runtime contexts, not semantic agent memory. An application can place memories or transcripts there, but context assembly, summarization, retrieval relevance, and instruction hierarchy remain application responsibilities. [A8] [A10]

## 6. State, sessions & durability

**fx/libfx.** The session log contains inputs, a chained sequence of lease claims/releases and harness records, and checkpoints. A new lease fences the previous holder's future writes. Consumed input IDs are retained for deduplication, and the worker can continue a turn after deployment or deadline interruption. This is genuine execution-lifecycle machinery rather than simply serializing chat messages. [F4]

The important caveat is effect ambiguity. On resume, a tool left running is rerun only if explicitly marked idempotent and rerun is permitted. Otherwise the model is told the tool may have partly run and the turn continues without automatically repeating it. That is a safe acknowledgment of uncertainty, not exactly-once external execution. [F6] [F7]

Backend choice changes guarantees. The local backend uses Workflow's local World for storage, checks process liveness, and explicitly marks its queue non-durable because queued messages die with the process. A persistent conversation is therefore recoverable when work is supplied again, but does not imply a persistent autonomous wake-up queue. Browser memory mode is weaker still; hosted World/queue integration has different lifecycle properties. [F8] [F4]

**agentOS.** A configured SQLite database can persist VM-owned filesystem/runtime state, and the sample uses a native root filesystem backed by `chunked_sqlite` to read a file after disposing and recreating the VM. That verifies a durable storage configuration. It does not establish that every in-flight guest process, live network connection, or model-side decision resumes after a host crash. A live VM retaining state across calls is a separate property from crash recovery. [A3] [A10] [A8]

**OpenHarness.** Session snapshots store model, system prompt, normalized messages, usage, and selected tool metadata. They are written atomically as both `latest.json` and a session-ID file under a project-derived directory. This supports session reload and history inspection, but the two writes and tool side effects are not one transaction. There is no verified workflow replay mechanism here comparable to libfx's lease/record protocol. [O6]

## 7. Safety & sandboxing

fx's permission gate supports allow/deny/ask results and an explicitly unrestricted mode. If no custom decider exists, its fallback admits read-only, non-irreversible actions and denies others. The product's automatic mode adds a model-based action classifier, but model review remains an application policy check, not OS isolation. The audit did not establish a built-in general OS sandbox for ordinary fx shell execution. [F9] [F1]

agentOS provides the execution boundary itself. Its kernel policy has scopes for filesystem, network, processes, environment, and host functions. Defaults belong to the sidecar: the public AgentOS profile permits virtual-machine operations and limits external network access to a service allowlist, while `secure-exec` explicitly selects the stricter secure profile. A caller's omitted scope retains sidecar defaults. Do not mistake host-adapter `allowAll` variables for the guest policy, or assume every wrapper selects identical defaults. [A3] [A5] [A6] [A7] [A8]

This is WebAssembly/V8 and a virtualized operating environment, not a conventional hardware VM. Native software compatibility, mounts, trusted callbacks, and sidecar security are relevant deployment considerations. Vendor speed and cost comparisons were not reproduced, and this static review is not a sandbox escape audit. [A1] [A4]

OpenHarness separates permission checks from sandbox backends. The checker blocks configured sensitive paths, applies tool and path rules, supports plan/default/full-auto modes, and can require confirmation. Rule order matters: explicit tool allow rules occur before later path/command checks, so policy authors should inspect how broad allowances interact. Pattern checks cannot substitute for isolation of arbitrary shell commands. [O7]

Its Docker backend disables networking even when domain allow/deny settings are supplied, because that backend does not implement those finer rules. It binds the project directory and optional extra mounts and applies resource limits when configured. This is real optional isolation, with a concrete scope; it does not imply every execution path runs in Docker. [O8]

## 8. Extensibility

fx exposes native/WASM engine APIs, custom JS tools, instructions, MCP clients, and skills, plus CLI ACP integration. Its durable layer depends on a small harness interface, suggesting it can be studied independently from terminal rendering. The architecture is flexible, but the source's experimental status and placeholder package version argue against assuming stable compatibility. [F2] [F3] [F4] [F14]

agentOS extends through guest software packages, mounts, host functions, runtime options, and execution contexts. This is an environment extension model rather than an agent plugin system. Adding an agent protocol or MCP server is a host integration task, not a feature proven by the VM API. [A3] [A4]

OpenHarness plugin objects can contribute skills, commands, agents, tools, hooks, and MCP server configuration. Hook events include session start/end, pre/post compaction, pre/post tool use, prompt submission, notification, stop, and subagent stop. This is a rich product extension catalog, though a static type definition does not by itself establish marketplace quality or compatibility with another product's plugin packages. [O11] [O12]

## 9. Multi-agent

fx has native subagent tooling and dedicated concurrent-subagent scheduling. Its durable session layer runs one worker per session; this does not prevent many independent sessions running concurrently. These are two concurrency scopes and should be kept distinct when embedding it in a server. [F12] [F4]

agentOS can supply independent execution environments to multiple agents, but does not itself implement model-level handoffs, child prompts, supervisor policies, or conversation merging. Its multi-agent score is not applicable. Multiple VMs are an isolation facility that orchestration can use. [A4] [A5]

OpenHarness has swarm and worktree modules, with validated worktree names and metadata linking a worktree to an agent. Worktree isolation helps avoid file-edit collisions, but it is neither a security boundary nor an automatic merge policy. The implementation is evidence of a deliberate coding-agent collaboration surface, not proof that concurrent work is always conflict-free. [O10]

## 10. Surfaces & integration

fx offers a terminal CLI, headless `ask`, ACP, and libfx through a native Node addon or WASM. That gives it unusually direct placement in a server or browser compared with integrated-only coding products. Durability, credentials, tools, and streaming still need host-specific configuration. [F3] [F14]

agentOS's primary surface is a JS library with a native runtime/sidecar, and the repository includes hosted usage patterns. Its `secure-exec` wrapper offers a smaller code-execution interface over the same environment. The app supplies its own model loop and user interface. [A8] [A4]

OpenHarness exposes CLI/headless behavior and terminal UI code around the Python engine. The chapter does not infer ACP or a general authenticated HTTP agent service from UI presence. Core classes are importable, but an independently versioned stable SDK promise was not established. [O1] [O2] [O5]

## 11. Observability & evals

fx records tool accounting and compaction traces; the durable log exposes worker leases, records, input identities, and checkpoints. These help distinguish a model failure from a worker failure or an ambiguous tool effect. Its repository also contains model-checking specifications and crash tests, but those were not executed in this study. [F11] [F10] [F4]

agentOS reports process output, exit status, execution outcomes, timeouts, and resource-oriented options. These are execution diagnostics, not task-quality evaluations. OpenHarness emits model text, retry status, turn completion, tool start/completion, and error events, and persists usage with its snapshots. Neither should receive an unqualified OTel checkmark merely because it logs events. [A11] [O2] [O3] [O6]

## 12. Notable design decisions & trade-offs

fx demonstrates that a small distribution artifact can contain a substantial harness. Native implementation and fast startup do not mean the internal architecture is a tiny loop: durable coordination, policy, compaction, protocol support, and UI still require considerable machinery. The reusable engine/durable adapter boundary is more informative than binary-size marketing. [F4] [F5] [F10]

agentOS addresses a different missing layer: giving code a useful OS-like environment without handing it the host. It can complement Pydantic, Pi, AI SDK, or a custom loop. Comparing it directly against those libraries on provider adapters or compaction creates misleading rankings. [A3] [A11]

OpenHarness prioritizes feature integration familiar from coding assistants. That produces a relatively compact public Python implementation with many recognizable policy seams, while making maturity, compatible plugin behavior, and durable orchestration separate questions requiring validation. [O1] [O11] [O6]

## 13. Scorecard

Values are **fx / agentOS / OpenHarness**. `—` means the rubric dimension is not applicable to an execution runtime, not a score of one.

| Dimension | Scores | Rationale |
|---|---|---|
| Flexibility | 4 / 4 / 4 | Engine/host boundary; configurable execution substrate; product hooks/plugins. |
| Integration | 4 / 3 / 4 | Integrated coding products; AgentOS integrates execution but no agent UX. |
| Embeddability | 5 / 5 / 3 | Explicit SDKs versus importable product internals. |
| Durability | 4 / 3 / 3 | Leases/checkpoints with effect ambiguity; persisted environment; session snapshots. |
| Safety | 3 / 4 / 4 | Application approvals; Wasm/V8 policy substrate; optional Docker plus approvals. |
| Extensibility | 4 / 4 / 5 | SDK tools/skills; environment plugins/callbacks; broad product plugin contributions. |
| Multi-agent | 4 / — / 4 | Subagents versus an execution substrate versus coding swarms/worktrees. |
| Provider neutrality | 4 / — / 4 | Gateway/compatible transports; no model layer; several API families. |
| Maturity | 2 / 2 / 2 | Explicit experimental or early 0.x source metadata; no independent adoption estimate. |
| Minimalism | 2 / 2 / 3 | Native packaging hides complexity; execution OS is substantial; compact product codebase. |

## 14. When to build on it / when not to

Choose libfx when the same native agent engine should serve a terminal, JavaScript host, and durable session application. Evaluate backend queue semantics and explicitly classify tool idempotency before relying on crash continuation. [F6] [F7] [F8]

Choose agentOS when the missing requirement is a controllable environment for model-generated programs. Pair it with a separate agent loop, and validate compatibility and security for the guest workloads and host functions you actually expose. Choose OpenHarness as an inspectable Python coding product or a source of product integration patterns, while adding stronger workflow guarantees if session snapshots are insufficient. [A3] [A4] [O6]

## 15. Evidence index

Verification: static inspection of SDK/package metadata, durable-session contracts, lease/queue policy, ambiguous-tool handling, native tool scheduling/accounting, compactor interfaces, AgentOS creation/default profiles/permissions and persistence example, OpenHarness loop/tool/approval/snapshot/plugin/worktree paths. All citations were checked for local file existence and line bounds. No cloned program, build, dependency install, benchmark, or test was run. These checks do not constitute a sandbox audit, performance reproduction, or independent adversarial review.

[F1]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/README.md#L15-L37 "README.md:L15-L37"
[F2]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/sdk/package.json#L1-L35 "sdk/package.json:L1-L35"
[F3]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/sdk/README.md#L1-L49 "sdk/README.md:L1-L49"
[F4]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/sdk/durable.js#L1-L76 "sdk/durable.js:L1-L76"
[F5]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/sdk/fx-harness.js#L17-L51 "sdk/fx-harness.js:L17-L51"
[F6]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/sdk/fx-harness.js#L134-L156 "sdk/fx-harness.js:L134-L156"
[F7]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/sdk/fx-harness.js#L164-L197 "sdk/fx-harness.js:L164-L197"
[F8]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/sdk/durable/local.mjs#L1-L37 "sdk/durable/local.mjs:L1-L37"
[F9]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/src/core/permissions/permission_gate.zig#L71-L122 "src/core/permissions/permission_gate.zig:L71-L122"
[F10]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/src/core/compactor/compactor.zig#L1-L85 "src/core/compactor/compactor.zig:L1-L85"
[F11]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/src/core/agent/runtime/tool_batch.zig#L16-L99 "src/core/agent/runtime/tool_batch.zig:L16-L99"
[F12]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/src/core/agent/runtime/parallel_execution.zig#L19-L70 "src/core/agent/runtime/parallel_execution.zig:L19-L70"
[F13]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/src/core/agent/runtime/orchestrator.zig#L6994-L7058 "src/core/agent/runtime/orchestrator.zig:L6994-L7058"
[F14]: https://github.com/vercel-labs/fx/blob/b877f4dcc57dfb2c0654d5bb18012215c0fdf1b3/README.md#L75-L91 "README.md:L75-L91"
[A1]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/README.md#L25-L35 "README.md:L25-L35"
[A2]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/packages/core/package.json#L1-L20 "packages/core/package.json:L1-L20"
[A3]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/packages/core/src/agent-os.ts#L607-L644 "packages/core/src/agent-os.ts:L607-L644"
[A4]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/packages/core/src/agent-os.ts#L2819-L2858 "packages/core/src/agent-os.ts:L2819-L2858"
[A5]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/packages/core/src/agent-os.ts#L2908-L2963 "packages/core/src/agent-os.ts:L2908-L2963"
[A6]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/packages/core/src/sidecar/permissions.ts#L40-L77 "packages/core/src/sidecar/permissions.ts:L40-L77"
[A7]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/crates/vm-config/src/lib.rs#L6-L75 "crates/vm-config/src/lib.rs:L6-L75"
[A8]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/secure-exec/src/runtime.ts#L40-L70 "secure-exec/src/runtime.ts:L40-L70"
[A9]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/examples/embedded/permissions.ts#L1-L20 "examples/embedded/permissions.ts:L1-L20"
[A10]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/examples/embedded/persistence.ts#L1-L26 "examples/embedded/persistence.ts:L1-L26"
[A11]: https://github.com/rivet-dev/agentos/blob/4d48628304c1ddedafc9d55f60752093fcf6f3d2/examples/js-ai-agent-code-exec/src/index.ts#L1-L32 "examples/js-ai-agent-code-exec/src/index.ts:L1-L32"
[O1]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/pyproject.toml#L5-L34 "pyproject.toml:L5-L34"
[O2]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/engine/query.py#L700-L760 "src/openharness/engine/query.py:L700-L760"
[O3]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/engine/query.py#L792-L884 "src/openharness/engine/query.py:L792-L884"
[O4]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/engine/query.py#L887-L980 "src/openharness/engine/query.py:L887-L980"
[O5]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/tools/base.py#L17-L80 "src/openharness/tools/base.py:L17-L80"
[O6]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/services/session_storage.py#L54-L128 "src/openharness/services/session_storage.py:L54-L128"
[O7]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/permissions/checker.py#L75-L154 "src/openharness/permissions/checker.py:L75-L154"
[O8]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/sandbox/docker_backend.py#L80-L128 "src/openharness/sandbox/docker_backend.py:L80-L128"
[O9]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/services/compact/__init__.py#L1-L65 "src/openharness/services/compact/__init__.py:L1-L65"
[O10]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/swarm/worktree.py#L21-L55 "src/openharness/swarm/worktree.py:L21-L55"
[O11]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/plugins/types.py#L17-L59 "src/openharness/plugins/types.py:L17-L59"
[O12]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/hooks/events.py#L8-L20 "src/openharness/hooks/events.py:L8-L20"
[O13]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/prompts/claudemd.py#L8-L48 "src/openharness/prompts/claudemd.py:L8-L48"
[O14]: https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/api/provider.py#L13-L87 "src/openharness/api/provider.py:L13-L87"
