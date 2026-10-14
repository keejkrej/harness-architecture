# DeepSeek Harness (dsh)

> **Verdict.** DeepSeek Harness is a full agent product (Web UI, Electron desktop, headless CLI, TypeScript/Python SDKs, ACP server). It is assembled from 336 npm packages that are all plugins on a vendored copy of the Cordis plugin framework. Even the agent loop is a plugin. It registers a factory on `ctx.agents` and can be replaced from YAML ([architecture](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/architecture.md#L9-L11)). It occupies the whole stack: provider adapters, the loop, the session data plane, the sandbox, multi-agent orchestration and UI. The kernel is about 22k LOC. Everything else is optional composition. The loop is built around one invariant: every model request must be reconstructable from an append-only session log. That invariant is pursued with unusual rigour, and it also feeds a co-designed DeepSeek API path. On that path, the system prompt and tool list can change mid-conversation without invalidating the KV cache, and by default the session log itself is uploaded alongside each request. Build on dsh if you want a heavily instrumented, recomposable agent platform and can track a pre-stable, fast-moving API. Avoid it if you want a small, legible library to embed in-process.

| | |
|---|---|
| Repo(s) | `deepseek-ai/deepseek-harness` @ `571902028a75` (2026-10-14, merge of PR #6241) |
| License | MIT (vendored Cordis/cosmokit/schemastery also MIT) |
| Language(s) | TypeScript (ESM, Node ≥22.19). Plus a small C native addon (Landlock launcher, flock) and a Python SDK |
| Size | 16,083 tracked files. **packages/**: 336 packages in 52 groups, 431k LOC of non-test TS source (Web client 144k, experimental 58k, extensions 23k of which ~15k generated catalogs, api 22k, session 18k, core 14.5k, llm 14.4k). Tests: 589k LOC. Kernel (vendored Cordis+Loader 3.8k, `packages/core` 14.5k, `llm/llm` 4.1k) ≈ 22k LOC. apps/ 16.7k (Electron desktop 15k). native/ 0.8k (C+TS). python/ 5.2k |
| Version at pin | `0.2.1-alpha.3` (root and every package `package.json`) |
| Release history | Repo created 2026-08-13 ("developer preview"). Third-party reports tie the launch to DeepSeek-V4-Pro-0813 GA the same day. First GitHub release `dsh-v0.1.0-rc.7` on 2026-08-17. 27 prereleases follow, through `dsh-v0.1.7-rc.2` (09-24), `dsh-v0.2.0-rc.1` (09-28) and `dsh-v0.2.1-alpha.3` (10-14). There is no stable release. Internal Agent Notes date from 2026-06-11 |
| Category | `hybrid` |

---

## 1. Layering & package map

### Kernel vs plugin boundary

The architecture document states the core thesis directly: "Every part of the product is a plugin, including the model adapter, the tool registry, the session log, and the agent loop itself… There is no privileged core to patch" ([`docs/architecture.md:L9-L11`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/architecture.md#L9-L11)). The code supports the claim.

- The only non-plugin substrate is **Cordis** (`vendor/cordis`, upstream `cordiverse/cordis` 4.0.0-rc.7) plus its Loader. Both are vendored as source with a logged list of local modifications, including lifecycle hardening of `fiber.ts` ([`vendor/README.md:L17-L18`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/vendor/README.md#L17-L18), [`vendor/README.md:L38`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/vendor/README.md#L38)). Cordis supplies services (`ctx.<key>`), `inject` dependencies, typed events with five dispatch modes (`emit`, `waterfall`, `parallel`, `serial`, `bail`), and reversible `ctx.effect()` registrations. A third-party listing says Cordis is the kernel of Shigma's Koishi chatbot framework; the repo itself only cites a Cordis paper ([`README.md:L7`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/README.md#L7)).
- `packages/core/*` contains the **service definitions** plus one default driver ([`docs/architecture.md:L55-L65`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/architecture.md#L55-L65)):

| Package | Owns | `ctx` key | LOC |
|---|---|---|---|
| `core/session` | append-only `SessionEvent` log, surface, in-memory store | `ctx.sessions` | 3,324 |
| `core/system-prompt` | prompt sections, runtime context, variables | `ctx.systemPrompt` | 691 |
| `core/tools` | scoped tool registry, guarded pipeline, PTC transport | `ctx.tools` | 5,755 |
| `core/agent` | `Agent` interface, live registry, `agent/*` events, factory slot | `ctx.agents` | 1,656 |
| `core/agent-loop` | **default** driver (`ReactLoopAgent`) | `ctx.agentLoop` | 2,478 |
| `core/scope` | per-agent scoped registration primitive | (library) | 471 |
| `llm/llm` | message/stream vocabulary, adapter registry | `ctx.llm` | 4,088 |

The loop is swappable for a concrete reason. `AgentRegistry.setFactory()` holds a single `AgentFactory` slot ([`packages/core/agent/src/index.ts:L171-L200`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent/src/index.ts#L171-L200), [`L360-L370`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent/src/index.ts#L360-L370)). `AgentLoop` is an ordinary `Service` that fills that slot inside an effect ([`packages/core/agent-loop/src/index.ts:L341-L342`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/index.ts#L341-L342), [`L388`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/index.ts#L388)). Consumers such as ACP, the SDK server and the UI program against `dsh-agent` only. The packages README states the rule: "`dsh-agent-loop` is swappable; UI, hook, and tool plugins use `dsh-agent`" ([`packages/README.md:L98`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/README.md#L98)).

The repo vocabulary for every non-kernel capability is a **capability seam**: a Service Definition, Service Provider and Consumer triple, usually with a model-facing tool as the consumer ([`AGENTS.md:L139`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/AGENTS.md#L139)). Examples: `fs` → `fs-local`/`fs-ssh` → `tool-fs`; `sandbox` → `sandbox-local`/`sandbox-ssh`; `subagent` → six providers → `tool-subagent`; `ptc-runtime` → `ptc-runtime-node`/`ptc-runtime-python` → `run_code`; `spill` → `spill-local` → `spill-policy`.

### Package map

```mermaid
flowchart TB
  subgraph Vendor["vendor/ (MIT, pinned upstream SHAs)"]
    cordis[cordis 4.0.0-rc.7] --> loader[cordis-plugin-loader] --> include[include / group / hmr / timer]
  end
  subgraph Kernel["packages/core + llm/llm (~22k LOC)"]
    llm[ctx.llm LlmRuntime] --- sessions[ctx.sessions]
    tools[ctx.tools ToolRuntime] --- sp[ctx.systemPrompt]
    agents[ctx.agents AgentRegistry] -->|setFactory| loop[ctx.agentLoop ReactLoopAgent]
    scope[dsh-scope]
  end
  subgraph Seams["capability families (each: definition / provider / consumer)"]
    prov[llm-deepseek, llm-pi-ai, llm-retry, token-meter]
    data[session-persistence-jsonl, session-projection, session-query-sqlite, storage]
    exec[subprocess, shell, terminal, sandbox(-local/-windows-acl/-ssh), fs, ptc-runtime]
    ctxm[compaction, spill, context, skill, mcp]
    orch[subagent x6 providers, workflow, jobs, goal, schedule, plan, todo]
    hum[interaction: approval, user-questions, commands, permission-presets]
  end
  subgraph Comp["composition"]
    bundles["bundle/: base, web-app, headless, sdk-app, sdk-minimal, acp-app"]
    presets["agent presets: standard, ptc, minimal, cordis(Creator)"]
  end
  subgraph Surfaces
    web["host + api (Typert RPC) + client (64 ui-* pkgs)"]
    desk[apps/desktop Electron]
    sdk[sdk JSON-RPC + python/]
    acp[acp server]
    headless[headless runner]
  end
  Vendor --> Kernel --> Seams --> Comp --> Surfaces
```

### Composition: profiles, bundles, patches, presets

A running `dsh` is a Loader tree built from ordered layers. The **profile** (`web`, `headless`, `sdk`, `sdk-minimal`, `acp`) stacks **bundles**, then its own `cordis.patch.yml`, then the home patch, then `--patch` overlays. A patch replaces a row by `id` or inserts rows ([`docs/architecture.md:L13-L27`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/architecture.md#L13-L27)). `dsh-base` is one large insert of about 90 rows: LLM, sessions, sandbox, approval, tools, compaction, subagents, telemetry ([`packages/bundle/base/cordis.patch.yml:L15-L522`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L15-L522)). `sdk-minimal` deliberately skips `dsh-base` and spells out a complete explicit tree, which is the closest thing to a minimal kernel listing ([`packages/bundle/sdk-minimal/cordis.patch.yml:L1-L172`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/sdk-minimal/cordis.patch.yml#L1-L172)).

**Agent presets** are a second, per-session composition level. Each preset is a `@deepseek-ai/dsh-agent-preset` row whose `config.plugins` is a child Loader tree mounted per Agent scope. Service rows inside a preset get `isolate` realms (e.g. `isolate: {compaction: true}`). The Web app ships four presets, verified against the preset files, the UI locale strings ([`ui-agent-preset/src/client/locales.ts:L50-L61`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/client/ui-agent-preset/src/client/locales.ts#L50-L61)) and the recorded tool-schema snapshots:

| Preset id (UI name) | order | Composition | Model-visible tools (Linux/macOS) |
|---|---|---|---|
| `standard` (Standard mode) | 1 | persona, AGENTS.md, time context, bash, fs, fs-search, jobs, schedule, skills, goal, plan-mode group, compaction group (basic + `/compact` + tool-result pruner), delegation group (subagent, subagent_fork, workflow), ask-user, todo, web, present ([`presets/standard.patch.yml:L5-L125`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/web-app/presets/standard.patch.yml#L5-L125)) | **31**: `ask_user_question bash create_goal edit exit_plan_mode get_goal glob grep interrupt_agent job_kill job_list job_output list_agents present read read_image schedule_{create,delete,list,update} send_message skill subagent subagent_fork todo_write update_goal web_fetch web_search workflow working_directory write` ([snapshot](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/snapshots/web/fresh-round-trip/tool-schemas.expected.json)) |
| `ptc` (PTC mode) | 2 | standard, with workflow disabled, plus `dsh-agent-tool-presentation {mode: ptc}` ([`presets/ptc.patch.yml:L104-L126`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/web-app/presets/ptc.patch.yml#L104-L126)) | **1** on the wire (`run_code`). The other tools become a generated TypeScript SDK in the prompt ([snapshot](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/snapshots/web/ptc-round/tool-schemas.expected.json)) |
| `minimal` (Minimal mode) | 3 | `persona {complete: true, includeRuntimeContext: false}`, `tool-fs` with only `readImage`, compaction-basic, persistent PTY bash ([`presets/minimal.patch.yml:L5-L78`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/web-app/presets/minimal.patch.yml#L5-L78)) | **3**: `bash read_image working_directory` ([snapshot](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/snapshots/web/minimal-preset/tool-schemas.expected.json)) |
| `cordis` (Creator mode) | 4 | standard plus `tool-cordis` (read-only `cordis_inspect_list/query`), preset-authoring skills, and `plugin_manager` when a profile context exists ([`presets/cordis.patch.yml:L120-L133`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/web-app/presets/cordis.patch.yml#L120-L133)) | standard set + inspection/plugin tools |

The minimal preset's persistent-bash description replaces the stock one. Its wording closely resembles Anthropic's reference `bash` tool text ("does NOT need to be XML-escaped", "State is persistent across command calls…"); this is an unverified observation. The `sdk-minimal` profile reuses the same three-tool shape. In-repo `BENCHMARK.md` points benchmark runs at that profile through the Python SDK ([`BENCHMARK.md:L1-L3`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/BENCHMARK.md#L1-L3)). That fits third-party reports that DeepSeek's V4-Pro-0813 Terminal-Bench 2.1 score of 87.9 was run in "minimal mode" on DeepSeek's own harness (DataNorth, 2026-08-14; vendor-reported, not verified).

---

## 2. Agent loop

**Where.** `ReactLoopAgent` in [`packages/core/agent-loop/src/agent.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts) (705 LOC) holds the turn and step machine. The `AgentLoop` factory service in [`index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/index.ts) (929 LOC) owns creation, resume, publication and fused-abort teardown. Tool scheduling is in [`tool-calls.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/tool-calls.ts).

**Vocabulary.** A *step* is one model request plus the tools it calls. A *turn* is zero or more steps ([`docs/architecture.md:L79-L106`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/architecture.md#L79-L106)). The driver is a three-state `Phase` union: `idle | maintenance | running` ([`agent.ts:L42-L50`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts#L42-L50)). `maintenance` lets `/compact` and agent setup take exclusive ownership without opening a turn ([`L183-L204`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts#L183-L204)).

**Input model.** The agent has one durable inbox with two targets, `next-turn` and `next-step`. Its state is a session projection folded from `agent/inbox/spliced` events, so pending input survives restarts ([`inbox.ts:L26-L66`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/inbox.ts#L26-L66)). Three verbs sit on top ([`agent.ts:L154-L181`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts#L154-L181)):
- `followup` targets `next-turn` and wakes the driver.
- `steer` targets `next-step` and wakes the driver.
- `inject` targets `next-step` without waking: plugin context that "waits for a waking message".

`cancel(cause)` clears the inbox unless `keepInbox` is set, then aborts the phase controller. The cause is a closed union `user | parent | disposed | hook`.

**One turn, step by step** ([`turn()` L298-L398](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts#L298-L398), [`step()` L400-L561](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts#L400-L561)):

```text
turn/start                                  (durable)
 loop:
  preStep: claim inbox(target) → ctx.systemPrompt.assemble()
           → waterfall agent/pre-step  (enter{messages, startsRequestSeries?} | reject)   L267-L288
  reject → turn ends 'blocked';  empty first claim → 'completed' with no step
  step/start                                (durable)
  step():
   retry-loop:
    prepareRequest: seed config (options or logged header) → waterfall agent/request
                    → ctx.llm.prepareCall() binds adapter + model info            L564-L613
    refresh runtime context; project system prompt (in-history vs. consolidate)
    append system/message*, user/message* (first attempt only)                    L416-L440
    buildRequest: log request/header (initial|resume|change|series), developer/message
                  tool-addition/removal, request/context; deriveMessages() and deep-freeze   L616-L704
    stream: preparedCall.stream(req) ?? ctx.llm.stream(req)  (llm/stream waterfall)
            → agent/assistant-stream frames (live, non-durable)
    finish=error|aborted → assistant/attempt (durable) → waterfall agent/request-error
            → {kind:'retry'} continues retry-loop, else throw LlmError               L504-L527
    else assistant/message (durable, embeds compact stream + usage)
    max-tokens → step ends 'max-tokens' (sticky for the turn)
    tool calls → executeToolCalls()                                                  L547-L555
  step/end                                  (durable, in finally)
  if turn may end and inbox.nextStep empty → serial agent/turn-stopping (listeners may steer)
 until no tool results owed and no next-step input
turn/end {reason: completed|max-tokens|blocked|aborted{cause}|error{failure}}      (durable, in finally)
if inbox has pending → next turn with a fresh AbortController
```

Design points:

- **Requests are pure functions of the log.** `buildRequest` calls `session.deriveMessages()`, deep-freezes every message, and marks the request with `markAgentLoopRequest`. `llm/stream` listeners can therefore read loop requests but cannot rewrite them ([`agent.ts:L686-L703`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts#L686-L703); waterfall contract at [`packages/llm/llm/src/index.ts:L58-L77`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/index.ts#L58-L77)). This enforces the repo rule "Model-visible ⟺ logged" ([`AGENTS.md:L137`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/AGENTS.md#L137)).
- **Streaming.** Live UI incrementality comes from process-local `agent/assistant-stream` frames. Durability comes from one settled `assistant/message` or `assistant/attempt`, each embedding the compact stream that produced it ([`docs/architecture.md:L118-L120`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/architecture.md#L118-L120)). On user abort mid-stream, partial content is committed with `interrupted: true` so visible text is preserved ([`agent.ts:L462-L503`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts#L462-L503)).
- **Stop conditions.** The loop has no step cap of its own. A turn ends when the assistant emits no tool calls, a tool result sets `concludesTurn` (e.g. `exit_plan_mode`), `max-tokens` occurs, a pre-step rejects, or an abort or error happens. "Keep going" behaviour is supplied by plugins: `agent/turn-stopping` listeners can steer (used by the hooks bridges for Stop hooks), and the goal round driver opens new turns while a goal is armed ([`goal-round-driver/src/index.ts:L262-L302`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/goal/goal-round-driver/src/index.ts#L262-L302)).
- **Parallel tool calls.** Calls run in model order. Each call is classified live through `ctx.tools.executionMode()`: `isConcurrencySafe(args) === true` → `parallel`, otherwise `exclusive`. Exclusive calls form barriers. Parallel calls fill a rolling pool capped by `maxParallelToolCalls` (default **10**, a volatile config). Results and `additionalContexts` commit strictly in model order, even when dispatch overlaps ([`tool-calls.ts:L60-L102`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/tool-calls.ts#L60-L102), [`L122-L247`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/tool-calls.ts#L122-L247), [`constants.ts:L6`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/constants.ts#L6)). Read-only tools such as `read`, `read_image`, `web_fetch` and `web_search` opt in ([`tool-fs/src/read.ts:L136`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/fs/tool-fs/src/read.ts#L136)).
- **Abort and error recovery.** On abort, started calls drain and commit. Unstarted calls receive synthetic `ABORTED_BEFORE_DISPATCH` results so the log stays replay-valid ([`tool-calls.ts:L250-L260`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/tool-calls.ts#L250-L260)). If a step throws, `ToolCallRecovery` writes missing `tool/result` events before `step/end` ([`agent.ts:L333-L359`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts#L333-L359)).
- **Retries are plugins.** The loop only asks `agent/request-error` whether to retry. `dsh-llm-retry` answers from the adapter's `retryPolicy` (`normal` bounded, or `always` unbounded). It logs `llm/retry` / `llm/retry-started` before backoff ([`llm-retry/src/index.ts:L188-L190`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-retry/src/index.ts#L188-L190), [`L243`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-retry/src/index.ts#L243); [`retry-policy.ts:L39-L51`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/retry-policy.ts#L39-L51)). Compaction answers the same waterfall for `CONTEXT_WINDOW_EXCEEDED` (§5).

---

## 3. Model / provider abstraction

**Message model.** `Message` is a role map (`system | developer | user | assistant | tool-result`), and every message carries an id and a `source`. Content is a **merge-extensible** `ContentBlockMap`: `text`, `reasoning`, `image` (content-addressed attachment ref, optionally `offloaded`), `file` (always projected to handle text, never sent natively), `tool-call` (raw JSON argument string), and the developer-message-only `tool-addition` / `tool-removal` ([`packages/llm/llm/src/types.ts:L60-L150`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/types.ts#L60-L150)). The adapter stream protocol is a small block-indexed union: `block-start`, `text-delta`, `reasoning-delta`, `tool-call-delta`, `block-end`, `usage`, `finish`. An opaque `ReplayEnvelope` lets each adapter round-trip provider-private state such as thinking signatures ([`types.ts:L470-L483`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/types.ts#L470-L483)). `GenerateOptions` carries `sessionId`, `toolHistory` and `purpose: 'compaction' | 'session-title'` ([`L529-L571`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/types.ts#L529-L571)).

**Adapter seam.** `LlmAdapter` has one required method, `stream()`. Optional methods are `providerInfo`, `providerRetryPolicy`, `listModels`, `prepareCall` (binds exact model metadata to an adapter generation) and image sizing ([`packages/llm/llm/src/index.ts:L202-L303`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/index.ts#L202-L303)). `LlmRuntime.registerAdapter(providers, adapter)` is all-or-nothing and returns a disposer plus atomic `replace()` ([`L401-L431`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/index.ts#L401-L431)). `prepareCall()` resolves defaults (`adapterDefaults`) and captures retry policy, modalities and update modes into a `PreparedLlmCall` ([`L956-L975`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/index.ts#L956-L975)). Adapter throws are normalized to terminal `finish` chunks inside `stream()` ([`L1155-L1180`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/index.ts#L1155-L1180)).

**Shipped adapters.**

| Package | Wire | Notes |
|---|---|---|
| `llm-deepseek` (+ `-api-key`, `-account`) | **Anthropic Messages** dialect at `https://api.deepseek.com/anthropic`, `anthropic-version: 2023-06-01`, Files API beta. Hand-rolled over `eventsource-parser`, no SDK ([`config.ts:L115`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-deepseek/src/config.ts#L115), [`adapter.ts:L144`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-deepseek/src/adapter.ts#L144)) | Default catalog: `deepseek-flash` ("DeepSeek-V4.1-Flash", text+image, `systemPromptUpdate: 'in-history'`, `toolUpdate: 'addition-only'`) and `deepseek-v4-pro` ([`models.ts:L6-L21`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-deepseek/src/models.ts#L6-L21)). 1M context and 256k max output defaults ([`defaults.ts:L5-L8`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-deepseek/src/defaults.ts#L5-L8)). Thinking replayed natively |
| `llm-pi-ai` | **Pi's `@earendil-works/pi-ai` ^1.1.0** ([`package.json:L46`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-pi-ai/package.json#L46)) | Described as a "design-verification twin of dsh-llm-deepseek" ([`package.json:L3`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-pi-ai/package.json#L3)). `PiAiAdapter extends LlmAdapter` ([`adapter.ts:L231`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-pi-ai/src/adapter.ts#L231)) exposes pi-ai's protocol families (`openai-completions`, `openai-responses`, `azure-openai-responses`, `openai-codex-responses`, `anthropic-messages`, `bedrock-converse-stream`, `mistral-conversations`…) with per-protocol compat gates ([`catalog.ts:L338-L344`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-pi-ai/src/catalog.ts#L338-L344)), plus OAuth sign-in. Mounted **dormant** in base: zero routes until settings add providers ([`base/cordis.patch.yml:L128-L136`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L128-L136)) |

**Reasoning.** `reasoning` is a first-class content block. Effort is an adapter-owned `ReasoningEffortId` resolved per exact model and recorded in the `request/header` envelope (`adapterDefaults` distinguishes adapter-chosen from caller-chosen values). Compaction summaries keep text only, never reasoning.

**KV-cache co-design** is the most DeepSeek-specific part of the abstraction. Models declare two optional capabilities ([`types.ts:L405-L426`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/types.ts#L405-L426)):
- `systemPromptUpdate: 'in-history'`: a changed prompt is appended as a later `system/message` after cached history instead of rewriting message 0.
- `toolUpdate: 'addition-only' | 'in-history'`: new tools arrive as `tool-addition` blocks in a developer message referencing a `deferLoading` declaration. `ToolSchema.deferLoading` "uses Anthropic's defer_loading terminology" ([`L491-L502`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/types.ts#L491-L502)).

The loop emits exactly these developer messages when the tool set changes between requests ([`agent.ts:L652-L666`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts#L652-L666)). Incapable routes fall back to consolidating the prompt and starting a new "request series". The same discipline explains several product decisions. Plan mode keeps the whole tool catalog visible "for request-cache stability" ([`base/cordis.patch.yml:L340`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L340)). The approval policy travels in runtime context after history, not in the system prompt ([`user-approval/src/index.ts:L150-L170`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/interaction/user-approval/src/index.ts#L150-L170)). Fork subagents keep the parent route "so the inherited history remains eligible for KV Cache reuse" ([`base/cordis.patch.yml:L386-L395`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L386-L395)).

**Token and cost accounting.** `dsh-token-meter` prices the durable surface deterministically from the log. It uses a fixed heuristic for text, adapter-declared image pricing where available, and reuses provider usage only for an identical envelope. It publishes `tokenUsage`, `contextPressure` and `contextBreakdown` projections. `TokenUsage` tracks `cacheReadTokens` and `cacheWriteTokens`. No currency or cost computation was found in the core or LLM packages; accounting is in tokens.

**DeepSeek wire extensions (important).** The official adapter adds HTTP headers `x-deepseek-harness-user-id` (anonymous UUID), `x-deepseek-harness-session-id` and `x-deepseek-harness-compact`. It also adds request-body fields `dsh_plugin_packages` (the active plugin package inventory) and **`dsh_session_log`**, an incremental, watermark-acknowledged upload of the canonical session log ([`docs/deepseek-llm-api-wire-extensions.md:L22-L29`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/deepseek-llm-api-wire-extensions.md#L22-L29), [`L74-L80`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/deepseek-llm-api-wire-extensions.md#L74-L80)). The doc states the field "may expose the Session working directory, system-prompt snapshots, user and Assistant content, embedded Assistant streams, failed-attempt output, tool arguments and results, compaction summaries, feedback, and plugin-owned events" ([`L158-L160`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/deepseek-llm-api-wire-extensions.md#L158-L160)). The plugin defaults to `enabled: true` with an 8 MiB per-request cap ([`session-log-deepseek/src/index.ts:L39-L54`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/session/session-log-deepseek/src/index.ts#L39-L54), [`L186-L230`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/session/session-log-deepseek/src/index.ts#L186-L230)). It is mounted in `dsh-base` and even in `sdk-minimal` ([`base/cordis.patch.yml:L43-L44`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L43-L44), [`sdk-minimal/cordis.patch.yml:L17-L24`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/sdk-minimal/cordis.patch.yml#L17-L24)). It applies only to `deepseek-official` routes; pi-ai routes do not send it.

---

## 4. Tool system

**Definition API.** A `ToolDefinition` combines a `ToolSchema` with these members ([`packages/core/tools/src/index.ts:L224-L301`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/index.ts#L224-L301)):
- `output: {schema, render, presentationMeta?}` (mandatory): a tool returns a canonical lossless-JSON *value* validated against `output.schema`, and `render()` projects it to model content.
- `execute(args, exec)`.
- `projectContent` / `finalizeContent` hooks.
- `timeoutMs`, which is never model-visible.
- `isConcurrencySafe(args)`.
- `presentCall` / `presentResult`: pure UI projections that must work identically on live streams and on log replay.

Authors use `defineTool()` with a bespoke `ParameterSchemaSpec` (`{type:'string', required:true}` style) that compiles to a supported JSON-Schema subset and infers argument types ([`schema.ts:L554`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/schema.ts#L554)). MCP tools enter as raw JSON Schema under the name `mcp__<server>__<tool>` ([`mcp-client/src/tools.ts:L82`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/mcp/mcp-client/src/tools.ts#L82)). `register()` is global or agent-scoped; scoped tools shadow globals ([`L1066-L1071`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/index.ts#L1066-L1071)).

**Execution pipeline.** Each call passes four scope-filtered events ([`index.ts:L143-L210`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/index.ts#L143-L210)):

```text
tool/call (durable) → tools/pre-execute  waterfall → PreToolDecision allow|deny|cancel|ask
                    → [ask → ctx.approval → allowed-once | rejected | cancelled | unavailable]
                    → tools/execute      waterfall (around: timeout, checkpoint, metrics; may swap exec.signal only)
                    → body
                    → tools/post-execute waterfall → PostToolDecision accept{content|value, additionalContexts} | block{feedback}
                    → finalizeContent → tools/result (emit) → tool/result (durable, cites tool/call seq)
```

Arguments cannot be rewritten in `pre-execute` because they are already logged ([`L600-L621`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/index.ts#L600-L621)). Policies built on this pipeline include:
- `dsh-tool-call-timeout-policy` on `tools/execute`, enforcing `timeoutMs` ([`timeout-policy/src/index.ts:L56`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/guard/timeout-policy/src/index.ts#L56)).
- `dsh-repeat-tool-reminder`: advisory reminders after 3/5/8 identical consecutive calls ([`repeat-tool-reminder/src/index.ts:L220-L236`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/guard/repeat-tool-reminder/src/index.ts#L220-L236)).
- `dsh-spill-policy` on `tools/post-execute`: results over `maxInlineTokens: 12500` become head and tail plus a path to the full spilled file ([`spill-policy/src/index.ts:L133`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/spill/spill-policy/src/index.ts#L133), [`base/cordis.patch.yml:L411-L417`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L411-L417)).
- `fs-observation-policy` on the `fs/write-intent` and `fs/edit-intent` gates, enforcing read-before-write ([`fs-observation-policy/src/index.ts:L119-L127`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/fs/fs-observation-policy/src/index.ts#L119-L127)).

**Programmatic tool calling (PTC).** `ptc-runtime` is exactly this. With `tools.mode: 'ptc'`, or per scope via `tools.presentAs('ptc')` ([`index.ts:L980-L990`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/index.ts#L980-L990)), the registry sends one reserved tool, `run_code`. All other visible tools are rendered as a generated TypeScript (or experimental Python) SDK section of the system prompt ([`index.ts:L672-L698`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/index.ts#L672-L698); [`ptc.ts:L1-L7`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/ptc.ts#L1-L7), [`L320-L345`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/ptc.ts#L320-L345)). The program's binding calls re-enter the **complete guarded pipeline**: approvals, timeouts and spill all apply, and calls are scheduled under the same parallel/exclusive contract (`maxParallelSubCalls` default 10). Each sub-dispatch is logged as `tool/ptc-dispatch-start` / `tool/ptc-dispatch`, but only the outer `run_code` result enters model history. `dsh-ptc-runtime-node` runs programs in a fresh Node process under the same OS sandbox as bash, with a 512 MB heap cap, 120 s default and 600 s maximum deadlines, and an opt-in `persistent-in-memory` REPL. This is closer to Anthropic's "programmatic tool calling" or Cloudflare's "code mode" than to smolagents' in-process Python executor.

**Built-ins.** The [generated tool catalog](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/tool-catalog.md) is produced by booting every `tool-*` package. It lists about 30 tool packages covering 60+ names. Beyond the Standard set in §1, they include `str_replace_editor`, `lsp`, six `terminal_*` PTY tools, `session_*` history search, `ralph`, nine agent-team tools, `create_worktree`, `plugin_manager`, MCP resource tools, and Stagehand/Playwright/CUA browser and computer-use tools (experimental).

**Approvals inside tools.** Bash, pwsh, the fs tools and `run_code` accept `sandbox_permissions` + `justification` arguments. `approveEscalation()` validates strict widening (`read-only → workspace-write → danger-full-access`) and routes through `ctx.approval.request()` before execution ([`sandbox/src/escalation.ts:L28-L41`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/sandbox/sandbox/src/escalation.ts#L28-L41), [`L171-L200`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/sandbox/sandbox/src/escalation.ts#L171-L200)). The mode names and the escalate-with-justification pattern mirror OpenAI Codex's sandbox vocabulary; the shared vocabulary is evident, the lineage is an inference.

---

## 5. Context management

**System prompt assembly.** `ctx.systemPrompt` has three kinds of contribution, and each is a disposer-returning registration ([`system-prompt/src/index.ts:L429-L470`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/system-prompt/src/index.ts#L429-L470), [`L478`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/system-prompt/src/index.ts#L478), [`L513`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/system-prompt/src/index.ts#L513), [`L561`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/system-prompt/src/index.ts#L561)):
- **sections**: stable prompt text. Tools add usage guidance, e.g. "Use the glob tool — not shell find".
- **contexts**: volatile runtime facts such as time, cwd and permission policy. These are rendered into a `runtime-context` **user message** and re-projected on each attempt, so volatile facts never touch the cached system prefix ([`agent.ts:L267-L288`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts#L267-L288)).
- **variables**: `{{model}}`, `{{provider}}`.

The identity header ("You are an AI agent powered by DeepSeek Harness.") is switchable with `includeHarnessIdentity`. The recorded Standard-mode prompt is about 5.8 KB with about 40 KB of tool schemas.

**Instruction files.** `dsh-agent-instructions` loads a user-global `AGENTS.md` plus the project chain of `AGENTS.md` / `CLAUDE.md` and their `.local.md` overlays ([`agent-instructions/src/config.ts:L12-L13`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/context/agent-instructions/src/config.ts#L12-L13)), within a 64 KiB budget that drops broader files first. Nested files are discovered on successful filesystem operations rather than through file watching.

**Compaction** (`dsh-compaction-basic`, 1.7k LOC). It is triggered by a serial `agent/pre-step` listener that prices the latest routed envelope through `ctx.tokenMeter` ([`compaction-basic/src/index.ts:L158-L175`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/compaction/compaction-basic/src/index.ts#L158-L175)). The default trigger is `floor(min(W×0.8, W−O−65536))`, and the retained tail is the newest 16% of `W−O` ([`README.md:L62`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/compaction/compaction-basic/README.md#L62)). The algorithm:
1. Select the oldest *balanced* span, never shadowing the system head (node 0).
2. Append `compaction/start`; this unmatched marker acts as the durable lock.
3. Summarize with a direct `ctx.llm.stream()` call. The call replays the exact system prompt, tools and shadowed messages so it is a genuine prefix hit on the provider KV cache; only the trailing instruction is uncached ([`README.md:L108`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/compaction/compaction-basic/README.md#L108)).
4. Reject summaries that do not shrink the span.
5. Append `compaction/summary` plus a replacement `user/message` (`<compacted-summary>…`) with `surfaceOp: {op:'replace', startSeq, endSeq}`, then append `compaction/end`.

On a provider-confirmed `CONTEXT_WINDOW_EXCEEDED`, the `agent/request-error` listener performs a maximal reduction and returns `{kind:'retry'}` only if the surface replacement generation advanced ([`L190-L232`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/compaction/compaction-basic/src/index.ts#L190-L232)). Two companion plugins run without a model call:
- `compaction-tool-result-pruner` (threshold 8192 chars, keeps 4096 head and 1024 tail) prunes oversized results first ([`base/cordis.patch.yml:L423-L430`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L423-L430)).
- `compaction-image-offload` replaces the oldest images with placeholders when a route rejects the image budget.

The original events stay in the log. Only the *surface* (the model-visible projection) changes, so compaction is non-destructive and auditable.

**Spill-to-disk** is a seam (`spill` / `spill-local` / `spill-policy`). It covers tool results (above) and capped `glob` results.

**Memory.** There is no long-term memory store in the shipped presets. The adjacent mechanisms are:
- `session-query` (+ SQLite FTS, off by default: `openAt: never`) with opt-in `session_*` tools for searching past sessions ([`base/cordis.patch.yml:L149-L161`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L149-L161)).
- Durable per-session goals and todos.
- **Skills** from `.dsh/skills`, `.agents/skills`, `$DSH_HOME/skills` and `~/.agents/skills`, file-watched and loaded through the `skill` tool ([`skill-filesystem/src/index.ts:L249-L257`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/skill/skill-filesystem/src/index.ts#L249-L257)).

A user guide describes MCP-based memory (`docs/user/guide/mcp-memory.md`).

---

## 6. State, sessions & durability

**The log.** `SessionEventMap` is a merge-extensible, discriminated, append-only event vocabulary with contiguous `seq` numbers. The format is at version 4 ([`core/session/src/types.ts:L90`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/types.ts#L90), [`L282-L300`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/types.ts#L282-L300)). This repository declares **62** event types, generated into `KNOWN_SESSION_EVENT_TYPES`. They span `turn/*`, `step/*`, messages, `tool/*`, `request/header`, `compaction/*`, `approval/*`, `goal/change`, `team/*`, `workspace/changes` and more ([`known-event-types.ts:L22-L85`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/known-event-types.ts#L22-L85)). Readers refuse unknown types unless the envelope carries `ignorable: true` ([`types.ts:L494-L517`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/types.ts#L494-L517)). Message-bearing events declare `surfaceOp: 'append' | {op:'replace', startSeq, endSeq}` ([`L463-L479`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/types.ts#L463-L479)). `Session.deriveMessages()` folds the surface incrementally ([`core/session/src/index.ts:L984`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/index.ts#L984)). UI state and the Python/TS SDK views are typed **projections** folded from committed events (`ctx.sessionProjections`).

**Storage.** `SessionPersistence` is an abstract service with `create/open(read|write)/stat/list/export` ([`session-persistence/src/index.ts:L137-L203`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/session/session-persistence/src/index.ts#L137-L203)). The shipped backend `session-persistence-jsonl` (5.1k LOC) writes `$DSH_HOME/sessions/<id>/session.vN.jsonl.zstd` (checksummed zstd frames by default, plain JSONL optional) with exclusive `wx` generation publication and kernel locks ([`session-persistence-jsonl/src/index.ts:L69`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/session/session-persistence-jsonl/src/index.ts#L69), [`generation.ts:L730`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/session/session-persistence-jsonl/src/generation.ts#L730)). Format upgrades are adjacent migration packages (`session-format-v0-to-v1` … `v3-to-v4`, about 6.6k LOC in total). Opening an old session for writing publishes a version-named successor next to the untouched original ([`docs/architecture.md:L122`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/architecture.md#L122)). Four format bumps in two months show both how fast the project moves and how seriously it treats persisted data.

**Write-ahead semantics.** `dsh-session-checkpoint-policy` flushes the session through `llm/stream` before the first chunk is requested, through `tools/execute` before any top-level tool body runs, and on every `agent/pre-step`. A checkpoint failure blocks the side effect ([`session-checkpoint-policy/src/index.ts:L64-L80`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/session/session-checkpoint-policy/src/index.ts#L64-L80)).

**Crash recovery.** `resume()` takes write ownership first, reads the log, and appends **synthetic closers** for an interrupted tail turn: missing tool errors, `step/end` and `turn/end` ([`agent-loop/src/index.ts:L884-L892`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/index.ts#L884-L892)). The synthetic results carry carefully worded guidance: a recorded-but-unfinished call reads "Its outcome is unknown… retry only if the operation is read-only or idempotent" ([`core/session/src/repair.ts:L33-L35`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/repair.ts#L33-L35), [`L209-L211`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/repair.ts#L209-L211)). The durable inbox restores queued messages. Scheduled follow-ups and jobs resume the original session.

**Fork.** `buildForkSeed()` copies an inclusive event prefix, appends `session/end-seed {inherited:true}`, and closes any open tail with `forked` results ([`core/session/src/fork.ts:L21-L30`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/fork.ts#L21-L30)). It is used for user forks and for the `subagent_fork` provider.

**What is missing.**
- No file-level undo or rewind. `workspace-changes` snapshots git and file-tool edits per turn for *diff display* only.
- No deterministic re-execution of in-flight work. The model is told the outcome is unknown, rather than the call being replayed.
- Background workflows and PTC REPL state are process-local.

The result is "durable log + write-ahead + semantic repair", not Temporal-style durable execution.

---

## 7. Safety & sandboxing

**Modes.** `SandboxMode = 'read-only' | 'workspace-write' | 'danger-full-access'`. The base bundle defaults to `workspace-write` with approval `ask` (`DSH_PERMISSION_MODE` overrides) and ships three permission presets that pair sandbox mode with approval policy ([`base/cordis.patch.yml:L240-L276`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L240-L276)). The session's mode is durable (`sandbox/mode`, `permission/preset` events).

**OS backends** (`sandbox-local`). Selection is platform-first and probes run only between competing candidates. Linux tries `bwrap`, then a Landlock launcher shipped as a C native addon. macOS uses Seatbelt (`sandbox-exec`). Windows uses a restricted-token plus ACL runner. If none is available, the call **fails closed** with `SANDBOX_UNAVAILABLE` ([`sandbox-local/src/index.ts:L150-L166`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/sandbox/sandbox-local/src/index.ts#L150-L166)). Enforcement is reported as `full` or `partial`; Windows ACL and older Landlock ABIs report `partial`. The profiles are short and readable ([`profiles.ts:L16-L58`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/sandbox/sandbox-local/src/profiles.ts#L16-L58)):
- bwrap: `--ro-bind / /`, private PID namespace and `/proc`, plus a writable workspace and tmpfs `/tmp` in `workspace-write`.
- Landlock: read-only `/` and read-write workspace and `/tmp`.
- Seatbelt: `(allow default) (deny file-write*)` plus write allow-lists.

**Gaps.** The profiles govern **file writes only**:
- No `--unshare-net`, and the Seatbelt profile is allow-default, so sandboxed commands keep **network access**.
- Reads are unconfined.

The only network policy is in `web_fetch`, which "accepts only public HTTP(S) destinations, resolves and validates every destination, and pins every actual connection" ([`base/cordis.patch.yml:L460-L461`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L460-L461)). The in-process `fs-sandbox` fence reuses the same `writableRoots()` helper so the fs tools and the shell agree.

**Approvals.** `ApprovalService` applies a session policy (`ask` | `never`) before the composed answerers. Outcomes are exactly `allowed-once | rejected | cancelled | unavailable` ([`user-approval/src/index.ts:L55-L68`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/interaction/user-approval/src/index.ts#L55-L68)). There is **no "always allow" grant**: wider standing authority comes from switching the permission preset. Every ask and outcome is logged (`approval/asked`, `approval/decided`). With no answerer (headless), asks fail closed. Experimental `auto-review` lets the current model judge each pending action, the equivalent of Codex's guardian or Claude Code's auto mode.

**Defaults that matter.**
- `sdk-minimal` runs `danger-full-access` with no approval plugin ([`sdk-minimal/cordis.patch.yml:L70-L74`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/sdk-minimal/cordis.patch.yml#L70-L74)). It is intended for disposable benchmark containers.
- `plugin_manager` requires `danger-full-access` or per-call approval and warns that package installs can run build scripts.
- `SAFETY.md` disclaims security: "has not undergone a security audit and must not be treated as secure" ([`SAFETY.md:L7-L15`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/SAFETY.md#L7-L15)).

**Secrets and data egress.**
- Credentials resolve per request from `$DSH_HOME/.credentials.yaml`, then the environment, then `.env`. They are never materialized into the process environment ([`base/cordis.patch.yml:L113-L126`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L113-L126)).
- The Web UI masks keys detected in messages.
- The default `dsh_session_log` upload to DeepSeek (§3) is the main egress consideration and is opt-out.
- OTel session upload is `FEEDBACK_ONLY` (§11).

---

## 8. Extensibility

- **Plugins.** Every package is a Cordis plugin. `src/` declares about **93 typed events** (`@mode` tags: 65 emit, 18 waterfall, 4 bail, 3 parallel, 2 serial). The waterfall events are the interception points: `agent/pre-step`, `agent/request`, `agent/request-error`, `llm/stream`, the `tools/*` events, and `approval/request`, among others. Registrations are effects and unwind on unload ([`AGENTS.md:L133-L138`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/AGENTS.md#L133-L138)). The "where new behavior goes" table maps each goal to a seam, from "Add a model provider → register its adapter on `ctx.llm`" to "Store sessions in a new backend → implement `SessionPersistence`" ([`docs/architecture.md:L138-L163`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/architecture.md#L138-L163)). Per-agent scoping comes from `dsh-scope`: listeners tagged with an agent scope receive only that agent's events ([`core/scope/src/index.ts:L1-L6`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/scope/src/index.ts#L1-L6)).
- **Configuration as the extension surface.** `cordis.yml` rows accept `!!js` expressions in `config` and `disabled`. Patches replace rows by id. `dsh --dump-config` prints the effective tree, so any row can be overridden. HMR reloads configuration live.
- **Distribution.** "Bundles" are npm packages with a `dsh.bundle` patch. `dsh plugin --profile <p> add <pkg>` (pnpm) and the `plugin_manager` tool install them, with peer-version gating and explicit approval of build scripts. Community discovery uses the `dsh-plugin` GitHub topic.
- **Skills.** A dedicated seam (`dsh-skill` registry plus filesystem and Office providers). The catalog is injected via `agent.inject()`.
- **MCP.** Client only (`dsh-mcp-client`: stdio/HTTP, tools and resources, no prompt templates). No server is enabled by default. ACP sessions can mount per-session MCP servers. dsh does **not** expose itself as an MCP server.
- **Hooks.** Native hooks are in-process Cordis listeners. Shell-command hooks exist only through experimental bridges:
  - `hooks-claude-code` reads a Claude Code `hooks.json` and maps `deny/ask/allow` onto `PreToolDecision` ([`hooks-claude-code/src/index.ts:L248`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/experimental/hooks-claude-code/src/index.ts#L248)).
  - `hooks-codex` handles five Codex hook points.
  - `claude-code-mods` (3.8k LOC) is an alpha compatibility layer that runs Claude Code "mods" `register(on, options)` modules.
- **Commands.** Commands (`ctx.commands`, e.g. `/compact`, `/goal`, `/plan`, `/feedback`) dispatch without a model turn.
- **Runtime self-modification.** Creator mode gives the model read-only inspection of live Host and Client APIs (`cordis_inspect_*`) and makes persistent changes through bundles and `plugin_manager`. The `cordis-host-runner` can run process-local dynamic definitions in a `node:vm` realm behind a whitelisted context façade. Its README states that no model tool creates dynamic definitions at this pin.

---

## 9. Multi-agent

**Subagent seam.** `ctx.subagents` (`dsh-subagent`, 5.1k LOC) is a provider registry with a durable catalog, timing and identity projections, continuable children, and a recursion cap `maxDepth` that defaults to **1** ([`subagent/src/index.ts:L186-L196`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/subagent/subagent/src/index.ts#L186-L196)). Six providers ship:

| Provider | Mechanism | Evidence |
|---|---|---|
| `spawn` (in-process) | fresh child `Agent`, zero parent context, preset/model/output-schema/depth capabilities | [`subagent-spawn-in-process/src/index.ts:L37-L59`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/subagent/subagent-spawn-in-process/src/index.ts#L37-L59) |
| `fork` (in-process) | seeds the child with the parent log prefix, keeps the route for a KV-cache hit, one-shot | [`base/cordis.patch.yml:L386-L395`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L386-L395) |
| `codex` | spawns the pinned `@openai/codex` **0.153.4** `app-server --stdio` | [`subagent-codex/src/run.ts:L132-L137`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/subagent/subagent-codex/src/run.ts#L132-L137), [`package.json:L51`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/subagent/subagent-codex/package.json#L51) |
| `claude-code` | `@anthropic-ai/claude-agent-sdk` **0.3.263** | [`subagent-claude-code/package.json:L48`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/subagent/subagent-claude-code/package.json#L48) |
| `acp` | any ACP agent via `@agentclientprotocol/sdk` 1.4.0 | [`subagent-acp/package.json:L39`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/subagent/subagent-acp/package.json#L39) |
| `dsh-sdk` | another dsh process over the SDK JSON-RPC | `packages/subagent/subagent-dsh-sdk` |

`tool-subagent` instances bind one provider each and register distinct tools (`subagent`, `subagent_fork`). Each delegation returns a child id promptly. `tool-subagent-control` registers `send_message`, `interrupt_agent` and `list_agents` for continuable children. Children persist as their own sessions linked by `parentSession`. Recent releases let subagents select their own agent preset.

**Workflows.** `workflow-ptc` runs a model-authored **JavaScript** script in a fresh, sandboxed Node process. The script has `agent()`, `parallel()`, `pipeline()`, `phase()` and `log()` hooks ([`workflow-ptc/src/runtime.ts:L86-L89`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/workflow/workflow-ptc/src/runtime.ts#L86-L89)). Each `agent()` is a subagent from the configured provider. The `workflow` tool runs in the foreground or as a `ctx.jobs` background job. The ptc-runtime substrate is shared with PTC mode. `tool-ralph` is a fixed "fresh agent per round" loop on top of it.

**Other coordination.**
- `jobs`: generic background jobs (bash, PTY sends, workflows), with completion notices injected into the session.
- `goal`: same-session objective with an automatic round driver.
- `schedule`: cron, interval and one-shot follow-ups owned by the Host.
- Experimental **Agent Teams**: a Lead, durable teammates, a shared task board and inbox messaging, with nine tools.
- Experimental `worktree`: `create_worktree` makes a branch and checkout and changes the session directory.

Parallelism is real: in-process children run concurrently on the same Cordis context, and workflow `parallel()` fans out.

---

## 10. Surfaces & integration

| Surface | Implementation | Reuse notes |
|---|---|---|
| **Web UI** (`dsh web`) | `host-webserver` on `127.0.0.1:3080`, launch-token cookie, Typert RPC gateway (`@Remote` decorated services) plus WebSocket session streams; 64 `client/*` packages (144k LOC React) | Remote and reverse-proxy deployments via `--public-url`/`--trusted-host`. The RPC is an internal BFF contract generated from service types, not a published public API |
| **Desktop** | `apps/desktop` Electron (15k LOC). Private Desktop Host runs the same profile runner and Web app; the profile lives in `$DSH_HOME/profiles/desktop` | Product shell only |
| **Headless** (`dsh headless "task"`) | one-shot; `--json` NDJSON projection of *committed* events only; `--session-id` resume; exit 0/1; credentials from env only ([`headless/cordis.patch.yml:L35-L43`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/headless/cordis.patch.yml#L35-L43)) | CI-friendly; no interactive approvals (fail closed) |
| **SDK** (TS `dsh-sdk-client`, Python `deepseek-harness`) | newline-delimited JSON-RPC over stdio to a spawned `dsh --profile sdk\|sdk-minimal`. Methods: `initialize`, `session/prompt`, `session/resume`, `session/wait`, `session/working-directory/{get,set}`, `shutdown`. Notifications: `session.event` (raw log events), `session.status`, `subagent.started/finished` ([`sdk/protocol/src/types.ts:L137-L153`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/sdk/protocol/src/types.ts#L137-L153)). The client version-locks to the same `dsh` ([`sdk/client/src/launch.ts:L55-L60`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/sdk/client/src/launch.ts#L55-L60)). The Python runtime wheel bundles the CLI | Narrow: **no cancel/interrupt and no approval callback** in the protocol at this pin. Customization goes through profile + patch files, not code |
| **ACP server** (`dsh acp`) | "automation-only" ACP v1: sessions, model/effort selection, per-session MCP servers, cancel, `session/request_permission` with one-shot allow/reject ([`acp/acp/src/index.ts:L156-L172`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/acp/acp/src/index.ts#L156-L172)); defaults to `deepseek-v4-flash` ([`acp-app/cordis.patch.yml:L15-L20`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/acp-app/cordis.patch.yml#L15-L20)) | The best programmatic surface for orchestrators (e.g. as a subagent backend in other ACP-capable harnesses). Fork, delete and transcript replay are unsupported |
| **Webhooks** (experimental) | `ctx.webhookRuntime` + `webhook-github` start sessions from GitHub deliveries (`docs/user/guide/github-review.md`) | |
| **In-process** | All 335 non-private packages are published to npm. `dsh-app-boot` retains "direct-config helpers… only for lower-level embedders and tests", and the docs say direct in-process plugin mounting is not a supported application launcher ([`docs/architecture.md:L41-L45`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/architecture.md#L41-L45)) | Technically feasible. You become a Cordis host and track pre-stable APIs |
| **Browser worker** (experimental) | `webworker-runtime` runs the whole plugin tree in a Web Worker from a packed VFS | Preview deployments |

There is no shipped TUI. The CLI help mentions `dsh tui` only as an example of a *custom* profile name. There is no IDE extension; editors can reach dsh only through ACP.

**Reusability assessment.** The cheapest integrations are ACP (standard protocol) and headless `--json`. The SDK is good for batch runs but cannot interrupt. Reshaping is cheap: a patch file can swap the model adapter, remove tools, change compaction thresholds or mount a remote sandbox, with no forking. Deep in-process embedding is possible because every capability is an npm package with typed seams. It does require adopting Cordis's lifecycle model and a 0.x API that the project states will break.

---

## 11. Observability & evals

- **Telemetry.** `dsh-otel` provides OTel **log** channels only; no tracing SDK dependency was found. `session-telemetry-otel` exports a session-log prefix to `dsh-otel-collector.deepseeksvc.com` only after explicit user feedback (`FEEDBACK_ONLY`, or `DISABLED`; `DSH_TELEMETRY_DISABLED` opts out) ([`session-telemetry-otel/src/index.ts:L31-L37`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/session/session-telemetry-otel/src/index.ts#L31-L37), [`base/cordis.patch.yml:L202-L232`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml#L202-L232)). Desktop adds product analytics.
- **Introspection.** Because the log is canonical, observability is mostly *log projection*: `session-stats`, `session-turn-outline`, token meter projections, `session-log-export`, an experimental `inspector` profile with a `session-inspector`, and opt-in SQLite full-text search.
- **Evals and benchmarks.**
  - `benchmarks/` holds **performance** gates (session open, long-session browser, stream reconnect, terminal I/O), not task evals.
  - `BENCHMARK.md` only points at the Python SDK minimal variant.
  - Quality assurance is snapshot-based: about 1,677 files under `snapshots/` (web/sdk/acp/session) replay recorded sessions keylessly through shipped profiles. Each scenario asserts the system prompt, tool schemas and UI renderings.
  - CI requires **per-file 100% coverage** on `packages/*/*/src` ([`AGENTS.md`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/AGENTS.md)).
  - 76 `verify-*` gate scripts run in `scripts/`.
  - The process is itself heavily agent-driven: 1,266 English Agent Notes and 40 repo skills under `.agents/`.

---

## 12. Notable design decisions & trade-offs

1. **The loop is a plugin, and so is everything around it.** `AgentFactory` is one slot. The loop exposes waterfalls at every decision point (pre-step admission, request config, request errors, streams, tool pre/around/post, turn stopping). As a result, retry, compaction, checkpointing, steering-on-stop, goals and approvals are all external plugins. *Cost:* behaviour is emergent from listener order across about 90 base rows. Understanding why a request looked the way it did requires `--dump-config` plus the log.
2. **"Model-visible ⟺ logged" as a hard invariant.** Requests are deep-frozen derivations of the log. Compaction is a surface *replacement* event rather than a deletion. Tool-set deltas are developer messages that cite historical request headers. This gives exact fork, resume, replay and telemetry for free. *Cost:* every new model-visible feature needs a session event type, a format review and, sometimes, a migration package (four format versions in two months).
3. **Harness and model co-design for the KV cache.** `in-history` system-prompt updates, `addition-only` tool updates with `deferLoading`, runtime context delivered as a trailing user message, a stable tool catalog in plan mode, prefix-replaying compaction summaries, and same-route forks. These are measurable cost decisions on the DeepSeek path. Other providers get the consolidate-and-restart fallback.
4. **Default session-log upload to the model vendor.** `dsh_session_log` is documented and opt-out, but on by default. It sends more than the API would otherwise see: failed attempts, pre-compaction originals, cwd, and plugin events. *Inference:* this is a data channel for DeepSeek's agentic training and eval pipeline. Anyone evaluating dsh for sensitive code should disable `session-log-deepseek` or route through pi-ai.
5. **Fail-closed safety, but file-scoped.** Sandboxes never silently degrade and report `full` or `partial` enforcement. Escalation must strictly widen and requires justification. There is no "always allow". The sandbox does not restrict network or reads, so exfiltration is out of scope for the OS layer.
6. **PTC as a presentation mode, not a separate agent.** Turning the tool registry into a code SDK while preserving the guarded pipeline, approvals and the log for every nested call is a clean generalization. It is reused for the workflow engine.
7. **Interoperability by absorption.** Instead of competing with Codex and Claude Code, dsh drives them as subagent backends, reads their hooks files and Claude Code mods, reads `CLAUDE.md`, and uses pi-ai for long-tail providers. dsh can act as an orchestration layer over other harnesses.
8. **Process over minimalism.** 589k lines of tests against 431k lines of source, a 100% per-file coverage gate, bilingual docs, generated catalogs, and explicit fiber teardown semantics everywhere (the `AgentLoop.prepare()` teardown alone is about 180 lines, [`index.ts:L497-L676`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/index.ts#L497-L676)). The engineering is solid, but reading the core in an afternoon is not realistic.

---

## 13. Scorecard

| Dimension | Score (1–5) | Rationale |
|---|---|---|
| Flexibility | **5** | Every layer is a replaceable Cordis service, including the loop (`AgentRegistry.setFactory`), adapters, persistence, sandbox, fs and subprocess worlds. Composition is YAML patches plus per-session presets with isolated realms. |
| Integration | **5** | A full product: Web UI, Electron desktop, headless, TS/Python SDK, ACP, three-OS sandbox, credential store and account login, scheduling, webhooks, plugin manager. |
| Embeddability | **3** | The supported programmatic surfaces are out-of-process: an SDK that spawns `dsh` over stdio JSON-RPC, and ACP. In-process Cordis mounting works with published packages but is explicitly not a supported launcher, and the APIs are pre-stable. |
| Durability | **4** | Append-only versioned log, write-ahead checkpoints before model and tool side effects, synthetic crash closers, durable inbox, fork, migrations. No replay-based durable execution or undo. |
| Safety | **4** | Fail-closed OS sandboxes (bwrap/Landlock/Seatbelt/Windows ACL), justified escalation, logged approvals, permission presets. No network isolation or read confinement, and session-log egress is on by default. |
| Extensibility | **5** | About 93 typed events with waterfalls, capability seams, npm bundle distribution with a plugin manager, skills, MCP client, Claude Code/Codex hook bridges, Claude Code mods compatibility. |
| Multi-agent | **5** | Spawn, fork and continuable subagents, six providers including Codex, Claude Code and ACP, a JS workflow engine with `parallel`/`pipeline`, background jobs, goals, Agent Teams and worktrees (the last two experimental). |
| Provider neutrality | **4** | A narrow `LlmAdapter` seam with the pi-ai adapter covering OpenAI, Anthropic, Bedrock, Mistral, Azure and custom gateways. DeepSeek is the default and the only route with the cache co-design and wire extensions. |
| Maturity | **2** | Only prereleases (`0.2.1-alpha.3`); the README warns "THERE WILL BE COMPATIBILITY-BREAKING CHANGES". Offsetting this are a very large user base (~250k stars), 44 contributors and strict CI. |
| Minimalism | **1** | 336 packages and 431k LOC of source. Even the kernel is about 22k LOC with dense lifecycle code. |

---

## 14. When to build on it / when not to

**Build on it when:**
- You want a **recomposable agent platform**: different presets per session, swapping the sandbox for SSH or remote execution, adding providers, or intercepting every request or tool through typed waterfalls without forking.
- You need **auditability and reproducibility**: the canonical event log, exact request reconstruction, fork, resume and keyless snapshot replay are best-in-class among the systems in this study.
- You run **DeepSeek models at scale** and care about cache hit rates. The in-history update protocol is unique, and the `sdk-minimal` profile is a clean benchmark scaffold.
- You want to **orchestrate other agents**: Codex app-server, Claude Agent SDK and ACP children under one session log and one approval model.

**Avoid it when:**
- You need a **small in-process library** with a stable API. Use pi-agent-core, the Vercel AI SDK, Pydantic AI or Strands instead.
- You need **network-level isolation** from the host sandbox. Wrap dsh in a container or VM, as `SAFETY.md` itself advises.
- You cannot accept vendor-side session-log upload (unless you disable it), or you need a stable 1.x surface.
- You want a terminal TUI. None ships; the product is Web, desktop and headless.

---

## 15. Evidence index

**Pinned source:** `deepseek-ai/deepseek-harness` @ [`571902028a75c64c1d767f4ae5fd099485f0ddf0`](https://github.com/deepseek-ai/deepseek-harness/tree/571902028a75c64c1d767f4ae5fd099485f0ddf0) (2026-10-14).

Architecture and process
- [`docs/architecture.md`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/architecture.md): kernel and plugin thesis, profiles, turn flow, extension map
- [`AGENTS.md`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/AGENTS.md): package layout and invariants (L133–L161)
- [`vendor/README.md`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/vendor/README.md): vendored Cordis manifest and local modifications
- [`docs/cordis-primer.md`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/cordis-primer.md), [`docs/tool-catalog.md`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/tool-catalog.md), [`docs/deepseek-llm-api-wire-extensions.md`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/docs/deepseek-llm-api-wire-extensions.md)
- [`SAFETY.md`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/SAFETY.md), [`BENCHMARK.md`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/BENCHMARK.md)

Kernel
- [`packages/core/agent-loop/src/agent.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/agent.ts): `ReactLoopAgent` turn/step machine
- [`packages/core/agent-loop/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/index.ts): `AgentLoop` factory, create/resume, repair
- [`packages/core/agent-loop/src/tool-calls.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent-loop/src/tool-calls.ts): parallel/exclusive scheduler
- [`packages/core/agent/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent/src/index.ts), [`runtime-types.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/agent/src/runtime-types.ts): `Agent`, `AgentFactory`, `agent/*` events
- [`packages/core/tools/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/index.ts), [`ptc.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/ptc.ts), [`schema.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/tools/src/schema.ts)
- [`packages/core/session/src/types.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/types.ts), [`repair.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/repair.ts), [`fork.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/fork.ts), [`known-event-types.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/session/src/known-event-types.ts)
- [`packages/core/system-prompt/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/system-prompt/src/index.ts), [`packages/core/scope/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/core/scope/src/index.ts)
- [`packages/llm/llm/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/index.ts), [`types.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm/src/types.ts)

Providers, context, safety, multi-agent, surfaces
- [`llm-deepseek/src/models.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-deepseek/src/models.ts), [`llm-pi-ai/package.json`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-pi-ai/package.json), [`llm-retry/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/llm/llm-retry/src/index.ts)
- [`session-log-deepseek/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/session/session-log-deepseek/src/index.ts), [`session-checkpoint-policy/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/session/session-checkpoint-policy/src/index.ts), [`session-persistence/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/session/session-persistence/src/index.ts)
- [`compaction-basic/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/compaction/compaction-basic/src/index.ts), [`compaction-basic/README.md`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/compaction/compaction-basic/README.md), [`spill-policy/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/spill/spill-policy/src/index.ts)
- [`sandbox-local/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/sandbox/sandbox-local/src/index.ts), [`profiles.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/sandbox/sandbox-local/src/profiles.ts), [`sandbox/src/escalation.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/sandbox/sandbox/src/escalation.ts), [`user-approval/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/interaction/user-approval/src/index.ts)
- [`subagent/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/subagent/subagent/src/index.ts), [`subagent-codex/src/run.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/subagent/subagent-codex/src/run.ts), [`workflow-ptc/src/runtime.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/workflow/workflow-ptc/src/runtime.ts)
- [`bundle/base/cordis.patch.yml`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/base/cordis.patch.yml), [`bundle/web-app/presets/`](https://github.com/deepseek-ai/deepseek-harness/tree/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/web-app/presets), [`bundle/sdk-minimal/cordis.patch.yml`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/sdk-minimal/cordis.patch.yml)
- [`sdk/protocol/src/types.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/sdk/protocol/src/types.ts), [`acp/acp/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/acp/acp/src/index.ts), [`python/sdk/src/deepseek_harness/api.py`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/python/sdk/src/deepseek_harness/api.py)
- Snapshots: [`snapshots/web/fresh-round-trip/tool-schemas.expected.json`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/snapshots/web/fresh-round-trip/tool-schemas.expected.json), [`snapshots/web/minimal-preset/tool-schemas.expected.json`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/snapshots/web/minimal-preset/tool-schemas.expected.json), [`snapshots/web/ptc-round/tool-schemas.expected.json`](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/snapshots/web/ptc-round/tool-schemas.expected.json)

Measurements (performed 2026-10-14 on the pinned clone, static only)
- `git ls-files | wc -l` → 16,083. `ls -d packages/*/*/` → 336 packages (52 groups; 46 experimental, 64 client). 335 `package.json` files lack `"private": true`.
- Non-test `packages/**/src/**/*.ts(x)` → 431,339 LOC. Test files (`*.spec.*`, `tests/`) → 588,715 LOC. `vendor/*/src` → 6,417. `apps/` → 16,658. `native/` (C/TS) → 813. `python/**/*.py` → 5,173.

External sources (accessed 2026-10-14)
- GitHub releases (`gh release list -R deepseek-ai/deepseek-harness`): 27 prereleases from `dsh-v0.1.0-rc.7` (2026-08-17) to `dsh-v0.2.1-alpha.3` (2026-10-14). Release notes for `dsh-v0.2.1-alpha.3`, `dsh-v0.2.0-rc.1` and `dsh-v0.1.0-rc.7`.
- `gh api repos/deepseek-ai/deepseek-harness`: created 2026-08-13T11:56Z, description "DeepSeek Harness: Everything is a Plugin.", 249,617 stars and 30,007 forks; 44 contributors (API pagination).
- DataNorth, "DeepSeek releases V4-Pro-0813 and open sources Harness v0.1" (dated 2026-08-14): https://datanorth.ai/news/deepseek-releases-v4-pro-0813-and-harness-v0-1. Third-party source: same-day release with V4-Pro-0813; Terminal-Bench 2.1 87.9 "on DeepSeek's own harness" in minimal mode (vendor-reported; not verified here).
- AI Native Landscape listing: https://landscape.jimmysong.io/projects/deepseek-harness/ (open-sourced 2026-08-13, MIT). A separate web-search summary attributes Cordis's origin to the Koishi framework; single source, unverified.
- Launch coverage (not relied on for facts): https://www.kucoin.com/news/flash/deepseek-launches-v4-pro-and-harness-sets-new-github-star-growth-record ; https://oodaloop.com/briefs/technology/deepseek-harness-launches-as-open-source-rival-to-claude-code-alongside-v4-pro-on-api-with-higher-prices/
