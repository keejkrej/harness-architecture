# Crush

> Crush is a Go terminal coding product built on Charm's Fantasy model/tool-loop library. The useful distinction is between its reusable dependency and its product harness: Fantasy is an embedding candidate; Crush's session coordinator, tools, permissions, and UI live in Go `internal` packages. Crush is attractive when you want a configurable terminal agent or a local server, rather than a supported in-process coding-agent SDK.

| | |
|---|---|
| Repository | `charmbracelet/crush` @ `a48dabea1a3562b24c39cc7f0dec10e867f8499b` |
| License | FSL-1.1-MIT; the pinned version is not simply MIT |
| Languages / size | Go; 1,242 tracked files, not a measurement of harness LOC |
| Version | Source snapshot after stable v0.98.1; nightly releases also exist |
| Release evidence | [v0.98.1](https://github.com/charmbracelet/crush/releases/tag/v0.98.1), published 2026-10-09; first release not reconstructed from the shallow clone |
| Category | `integrated-product` |

## 1. Layering & package map

```text
Cobra CLI / Bubble Tea terminal UI / HTTP clients
                 ↓
workspace + backend + coordinator
                 ↓
sessionAgent: history, queue, summaries, streamed persistence
                 ↓
Fantasy agent + provider adapters + typed tools
                 ↓
shell/files/LSP/MCP              SQLite sessions and messages
```

The manifest directly depends on Fantasy, Catwalk, Bubble Tea, the Go MCP SDK, and SQLite drivers. Fantasy supplies the generation/tool-loop abstraction; Catwalk supplies provider/model metadata; Crush assembles a coding environment around them. This is a dependency edge, not evidence that Crush uses Pi or AI SDK. [go.mod:1–58](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/go.mod#L1-L58)

The coordinator constructs agents from configuration and separately constructs their tools. Its interfaces are exported Go symbols but belong to `internal/agent`, so they are not a general external import contract. For a new host, the HTTP boundary is more realistic than directly importing the coordinator. [coordinator.go:123–195](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/coordinator.go#L123-L195)

## 2. Agent loop

`sessionAgent.Run` is the product loop wrapper. It obtains history, persists the incoming user message, constructs a Fantasy agent with the active model, system prompt and tools, and calls `agent.Stream`. Streaming callbacks persist assistant text, reasoning, calls and results. This makes the conversation observable before the whole response finishes. [agent.go:788–856](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L788-L856), [agent.go:974–1094](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L974-L1094)

The prepare-step callback refreshes tools and drains queued follow-ups. Cancellation is sequence-aware: prompts accepted after cancellation are not accidentally discarded with older queued work. Calls carrying their own run ID retain their own terminal completion rather than being silently folded into another turn. This matters for concurrent HTTP clients as well as the terminal UI. [agent.go:857–890](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L857-L890)

Stopping includes context pressure and repeated-tool-call detection. Context-window metadata of zero disables automatic summarization instead of treating an unknown model as immediately full. A turn halted for summarization can queue a continuation if unfinished tool work remains. Cancellation uses Go contexts; provider/authentication recovery has additional coordinator logic. These are ordinary retry/continuation mechanisms, not durable workflow replay. [agent.go:1096–1121](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L1096-L1121), [agent.go:1265–1279](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L1265-L1279), [coordinator.go:1518–1604](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/coordinator.go#L1518-L1604)

## 3. Model / provider abstraction

Crush imports Fantasy adapters for Anthropic, Azure, Bedrock, Google, OpenAI, OpenAI-compatible APIs, OpenRouter and Vercel. Provider neutrality is consequently substantial, but provider-specific options are still managed by the coordinator. Reasoning effort and wire-level compatibility are not erased by the common interface. [coordinator.go:48–55](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/coordinator.go#L48-L55), [coordinator.go:467–545](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/coordinator.go#L467-L545)

The message conversion layer handles provider media limitations. Cache controls are attached to the final tool, system message and recent messages where appropriate. Token/cost accounting is persisted per session, and the loop explicitly distinguishes estimated usage from provider-reported usage. A cost number therefore needs its provenance preserved when building dashboards. [agent.go:783–786](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L783-L786), [agent.go:892–907](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L892-L907), [agent.go:2037–2094](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L2037-L2094)

## 4. Tool system

Tools are Fantasy agent tools with typed Go inputs. The assembly includes Bash, jobs, downloads, edits, multi-edit, fetch, glob, grep, listing, Sourcegraph, todos, view and write. LSP configuration adds diagnostics, references, definitions, call hierarchy, rename and symbol replacement. Interactive questions are excluded from noninteractive and child-agent contexts. This is a fairly opinionated coding toolset, rather than a minimal generic function registry. [coordinator.go:845–925](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/coordinator.go#L845-L925)

Bash output has a 30,000-width limit; truncation retains head and tail and can reference a file containing full output. This separates a bounded model observation from the complete execution artifact. The number is a display-width policy, not an exact token budget. [bash.go:428–451](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/tools/bash.go#L428-L451)

## 5. Context management

Prompt templates receive provider/model identity, working directory, platform/date, Git state, project/global context files and a skill catalogue. Files and directories can contribute context; this is broader than automatically including every repository file. The README documents shared `AGENTS.md` instructions and configurable initialization names. [prompt.go:23–49](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/prompt/prompt.go#L23-L49), [prompt.go:100–135](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/prompt/prompt.go#L100-L135), [README.md:529–545](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/README.md#L529-L545)

Summarization runs a model call, writes a summary message and updates the session's summary pointer. Subsequent requests read the history tail beginning at that summary. Original storage and active model context are therefore separate concepts. Summaries incorporate unfinished todos but are lossy model outputs; they do not provide exact semantic reconstruction of every previous observation. [agent.go:1412–1465](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L1412-L1465), [agent.go:1515–1551](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L1515-L1551), [agent.go:1793–1817](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent.go#L1793-L1817)

## 6. State, sessions & durability

SQLite stores sessions and messages; the database config enables WAL, foreign keys, a busy timeout and migrations. Sessions contain a summary pointer, usage, cost and todos, and child tasks have parent/session linkage. This is durable conversation state with resume, not just a transient chat array. [connect.go:17–39](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/db/connect.go#L17-L39), [session.go:102–142](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/session/session.go#L102-L142), [session.go:197–230](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/session/session.go#L197-L230)

`crush run --session` and `--continue` expose resumption. Nothing in the examined run/persistence path establishes an exactly-once transaction encompassing arbitrary shell side effects and a saved tool result. A crash after an external action can still leave ambiguity; the durability score is therefore 3. HTTP panic recovery improves connection/error behavior, but should not be confused with recovering a previously running agent after process death. [run.go:61–77](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/cmd/run.go#L61-L77), [recover.go:9–37](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/server/recover.go#L9-L37)

## 7. Safety & sandboxing

The permission service supports allowlisted tool/action combinations, per-session autoapproval, explicit grants/denials and a global skip mode. PreToolUse hooks can stamp an individual call as approved, while still producing permission notifications. This is an application approval boundary. No OS confinement implementation was established in the examined shell/tool path; running in an externally supplied container is a separate deployment choice. [permission.go:188–231](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/permission/permission.go#L188-L231), [permission.go:250–285](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/permission/permission.go#L250-L285)

Approving a shell command authorizes the process it launches; it is not proof of path or network isolation. The matrix marks OS sandboxing unknown rather than deriving it from permissions. Secret-provider configuration and MCP OAuth exist, but this review did not establish a complete secret-redaction guarantee across every log/tool output.

## 8. Extensibility

MCP supports stdio, HTTP and SSE, including OAuth and special handling for sessionless servers. Agent Skills can come from global or repository directories, and skills may be user-invocable or excluded from model-triggered discovery. These are practical extension points without changing the loop. [README.md:415–493](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/README.md#L415-L493), [README.md:604–685](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/README.md#L604-L685)

Hooks are narrower than a general lifecycle plugin platform: the examined event constant is `PreToolUse`. Hooks can allow, deny, halt, add context and rewrite tool input; aggregation makes denial dominate approval. Arbitrary in-process plugin replacement of the coordinator was not demonstrated. [hooks.go:13–22](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/hooks/hooks.go#L13-L22), [hooks.go:68–93](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/hooks/hooks.go#L68-L93)

## 9. Multi-agent

The `agent` tool is explicitly constructed as a parallel Fantasy tool and runs a configured task agent with parent session, assistant message and tool-call linkage. That supports delegated parallel work, but does not establish a general workflow DAG or automatic Git worktree allocation. Recognizing a checkout that happens to be a worktree is different from creating isolated worktrees for children. [agent_tool.go:18–67](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/agent/agent_tool.go#L18-L67)

## 10. Surfaces & integration

The product offers a terminal interface, a one-shot noninteractive command and a client/server path. The server implements HTTP, with Unix socket defaults, Windows named pipes and optional TCP addressing. A versioned `/v1` endpoint catalogue drives both routing and API documentation. This is a meaningful host boundary, even though it is not an in-process SDK. ACP, a separate web chat UI and an IDE extension were not verified. [run.go:31–36](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/cmd/run.go#L31-L36), [server.go:63–99](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/server/server.go#L63-L99), [endpoints.go:8–58](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/server/endpoints.go#L8-L58)

## 11. Observability & evals

Streaming persistence and session usage are useful audit inputs. Product telemetry uses PostHog, with environment and version attributes; that is distinct from a vendor-neutral OpenTelemetry trace graph. Tests cover cancellation, streaming, permissions and server lifecycle, but no comparative benchmark result is inferred merely from test filenames. [event.go:13–60](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/internal/event/event.go#L13-L60)

## 12. Notable design decisions & trade-offs

Crush combines a replaceable inference library with an intentionally integrated application. Its queue semantics, incremental message updates and versioned server API make it considerably more than a TUI wrapped around a single completion call. Conversely, reproducing its harness inside another application means accepting internal package coupling or owning a fork. The legal boundary matters independently: the license names FSL-1.1-MIT and includes a competing-use restriction, so treating this snapshot as an unrestricted MIT library would be incorrect. [LICENSE.md:1–52](https://github.com/charmbracelet/crush/blob/a48dabea1a3562b24c39cc7f0dec10e867f8499b/LICENSE.md#L1-L52)

## 13. Scorecard

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 3 | Providers, tools, skills and a pre-tool hook; fixed product coordinator |
| Integration | 4 | TUI, LSP, MCP, sessions, auth and local server |
| Embeddability | 2 | HTTP/subprocess boundary; harness packages are internal |
| Durability | 3 | SQLite conversation state and resume; no demonstrated activity replay |
| Safety | 3 | Explicit approvals and allowlists; confinement not established |
| Extensibility | 4 | MCP, skills and input-rewriting hooks |
| Multi-agent | 3 | Parallel child-agent tool with session linkage |
| Provider neutrality | 5 | Multiple Fantasy provider adapters and compatible APIs |
| Maturity | 3 | Active 0.x product; no claim of a stable embedding API |
| Minimalism | 3 | Legible Go structure, but substantial application coordination |

## 14. When to build on it / when not to

Use Crush as a configurable developer-facing terminal agent or control it through its local API when its established interaction model suits the host. Study Fantasy separately if the requirement is an importable Go agent loop. Do not select Crush solely because its repository is available: in-process API support, product licensing and the absence of verified OS confinement may each change the engineering decision.

## 15. Evidence index

The principal evidence is the pinned manifest, `internal/agent/{agent,coordinator,agent_tool}.go`, `internal/permission`, `internal/session`, `internal/server`, and `internal/hooks`, linked above. Release metadata was read from the first-party GitHub API on **2026-10-14**. Review was static: no dependency installation, product execution or sandbox escape test was performed. Negative findings are limited to inspected surfaces, and unknown matrix entries deliberately avoid converting an incomplete search into a categorical absence.
