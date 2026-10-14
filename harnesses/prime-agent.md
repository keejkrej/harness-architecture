# Prime Agent

> Prime Agent is an integrated coding/research product built around a persistent Python control environment, a Rust agent runtime, and daemon-owned sessions. Its distinctive contribution is making context and orchestration programmable: large values can remain in the REPL, while children, tools, skills, and editable harness memory are called from code. It is a strong architecture reference for long-running personal agents. Its process isolation is explicitly not a security sandbox, and its snapshots are best-effort recovery rather than transactional replay of arbitrary Python effects.

| | |
|---|---|
| Repository / pin | `PrimeIntellect-ai/prime-agent` @ `791ce3d8f93a` |
| License / languages | MIT; Rust plus Python runtime [P1] |
| Size | 1,573 tracked files; nine workspace crates plus Python runtime |
| Version at pin | Rust workspace `0.10.0` [P1] |
| Category | `hybrid`: modular native harness inside a daemon/TUI product |
| History evidence | Snapshot 2026-10-14; source contains deliberate compatibility with earlier TS formats; first public release date not reconstructed |

The source at this pin is important: descriptions of an earlier TypeScript implementation do not accurately describe the current package map. Comments preserve TS contract names to document compatibility, but the checked-in workspace is Rust and the RLM execution process is Python. [P1] [P2] [P10]

## 1. Layering & package map

```text
pa-cli / pa-tui / ACP client
          -> pa-daemon: sessions, workers, children, schedules
             -> pa-core: session engine, prompts, compaction, kernels, refinement
                -> pa-agent: provider-independent event/tool loop
                   -> pa-ai + pa-models + pa-types
                -> Python rlm.repl: persistent namespace and host requests
pa-telemetry: event sinks shared by the product
```

The low-level agent loop is separated from product state. Its `AgentMessage` representation allows custom harness messages, while conversion to provider messages happens only at the model boundary. The core can therefore store information useful to the UI or runtime without blindly sending everything to the model. Tool definitions similarly separate model-facing schemas/execution from TUI rendering. [P2] [P8]

The daemon is the continuity boundary described by the product: a terminal attachment can disappear while the agent continues. The persistent Python environment belongs beneath the session engine rather than to the terminal. These separations make headless and editor surfaces practical, but they also mean that extracting a small library from the product requires deciding who owns the daemon, kernel, and session lifecycle. [P30] [P27]

## 2. Agent loop

`pa-agent` exposes configurable conversion, context transformation, dynamic system prompt, API-key lookup, stop hooks, steering, follow-up messages, continuation messages, and before/after tool callbacks. The default configuration allows parallel tool execution, but a tool can force sequential execution for its batch. These are actual control points rather than only configuration flags. [P2] [P3] [P6]

The loop first drains steering, emits turn/message events, and streams an assistant response. Error and abort stop reasons end the run without dispatching another tool batch. Otherwise it executes tools, appends tool-result messages, emits turn end, checks cancellation and stop policy, then polls steering again. After tool-driven work is exhausted it considers follow-up and continuation messages. A goal driver can therefore request more work even after the model would otherwise stop, without embedding an infinite loop in the terminal UI. [P4] [P5] [P31]

Sequential tool execution checks abort between calls. Parallel execution emits completion events in completion order, but emits final tool-result message events in the assistant's original order. That distinction preserves responsive UI updates while giving the next model request a stable conversational ordering. A single sequential-only tool makes the whole batch sequential, protecting stateful backing resources. [P6] [P7]

Provider retry is a shared policy with a default three retries, a two-second base delay, and a cap on server-requested waits. It excludes local lifecycle failures and treats context overflow as the responsibility of compaction recovery. This avoids replaying a broken request unchanged when the correct action is to reduce context or fix a local failure. [P19]

## 3. Model / provider abstraction

The workspace separates types, model metadata, and provider transport from the agent loop. Provider modules cover Anthropic, Bedrock, Google, OpenAI-style completions/responses, Mistral, and other paths. The loop receives a model and reasoning level but does not hard-code one provider. API-key lookup can happen dynamically before each request. [P1] [P2] [P3] [P32]

Provider-neutral messages are not synonymous with lossless cross-provider behavior. Reasoning blocks, cache metadata, token usage, and service tiers require adapter handling. The loop's explicit service-tier and thinking fields preserve these capabilities where supported; they do not prove that every adapter implements the same feature set. The chapter does not reproduce model price tables or claim compatibility from names alone. [P3]

The distinction between custom agent messages and model messages also matters for cost and context. Session bookkeeping, progress state, and branch summaries can be retained as harness records and projected selectively into the next request. That is a more flexible architecture than using a vendor's raw conversation array as the only durable state. [P2] [P17]

## 4. Tool system

A tool definition contains a name, description, JSON schema, prompt snippet, optional argument normalization, execution scheduling constraint, and asynchronous executor. Results support text, images, structured details, error flags, and streamed updates. Cancellation flows into tool execution. This is a reusable low-level interface even though the main product emphasizes its Python control tool. [P8] [P9]

The RLM runtime is a CPython process speaking newline-delimited JSON. Cells use top-level `await` in one persistent namespace. The protocol bounds stream frames, result text, and large display/host-request payloads so a pathological value does not force unbounded host buffering. These are resource and protocol protections, not a restriction on what Python can do with user privileges. [P10] [P11]

The key model-facing move is to let the agent write code that calls tools and child agents. A large response can stay in a variable while code extracts only the relevant portion for the conversation. This reduces pressure to serialize all intermediate data into the model context, at the cost of a second state space: variables, imports, and running tasks can matter just as much as chat messages. [P10] [P24]

## 5. Context management

Prime combines conventional conversation compaction with REPL state and continual harness entries. `compact_session` chooses a cut, runs a summarizer, persists a compaction entry, and rebuilds context. It also carries a harness digest and can attach an `ipython_state` notice. Compaction is therefore responsible for telling the model about the surrounding state, not just shrinking older prose. [P18]

The continual harness is structured data with kinds `prompt`, `memory`, `skill`, `subagent`, and `factory`. Entries have versions, source, metadata, timestamps, and local/global scope. Refinement events record trigger, changes, evidence, and outcome. This is a concrete mechanism for editable supplemental behavior; it is not evidence that the model's weights have been trained or that refinement necessarily improves task success. [P20]

The Python store checks file modification times before mutation so a long-lived kernel does not overwrite refinement updates made by the host process. Its search ranks entries using query-term frequency across the corpus and field matches, then recency. This is inspectable lexical retrieval, not a hidden embedding store. The snapshot method returns the structured harness state. [P21] [P22]

The product says refinements leave the immutable base system prompt intact and modify supplemental state. That is a meaningful boundary: an application can review small persisted entries and refinement evidence independently from base instructions. It remains the application's responsibility to evaluate whether a learned rule is appropriate outside the task that produced it. [P30] [P20]

Project instructions also have a concrete file-discovery policy: global agent-directory context is loaded first, then ancestor directories from root toward the working directory. Each directory prefers `AGENTS.md`, its uppercase extension, then the corresponding `CLAUDE.md` names. Only the first readable candidate per directory is used; this is distinct from the mutable refinement store. [P33]

## 6. State, sessions & durability

There are several persistence planes. Session entries record messages, custom state, model/thinking changes, labels, compaction, and branch summaries. The session manager rewrites using an atomic-write path and has a pre-model flush operation. These mechanisms improve transcript integrity and admission durability; they do not make all tools transactional. [P17] [P16]

The Python namespace is persisted separately as a dill payload plus JSON manifest. Snapshotting is best-effort per variable: unpicklable or oversized objects are skipped and reported. The defaults cap the overall payload at 256 MiB and a single variable at 16 MiB. A restored session therefore cannot assume every variable survives. Restore results explicitly report failures. [P15] [P13]

Snapshot framing is validated so structural damage fails restoration rather than silently accepting an arbitrary prefix. The unpickler also refuses to reopen raw file-descriptor numbers from the old process. These are valuable recovery safeguards, but live subprocesses, sockets, and external side effects remain qualitatively different from serializable values. A Python function can have already modified the world before a snapshot or transcript records the result. [P12] [P14]

A separate RLM ledger records parent/child relationships, including spawn, rename, delete, depth, and usage snapshots. Its replay parser skips malformed records with errors rather than discarding the entire ledger. This recovers orchestration structure; it does not replay every child operation exactly once. The distinction explains the durability score of four: more than conversation resume, but not a universal workflow transaction engine. [P26]

## 7. Safety & sandboxing

The official README explicitly says model-generated Python and project commands execute with the user's permissions, and worker/kernel process boundaries are not a security sandbox. The persistent interpreter can import modules and call host services; a separate process is a lifecycle boundary, not a confinement policy. That statement agrees with the inspected runtime architecture. [P30] [P10]

The loop supports before-tool hooks that can block execution, but an extension hook is not evidence of a default comprehensive approval system. Resource caps, abort signals, and safe snapshot parsing protect availability and state integrity; they do not prevent file access or network access by allowed Python. For hostile code, an embedding host needs an external sandbox and credential policy. [P2] [P11] [P14]

The low safety score is therefore deliberate and narrow: it rates built-in confinement/permission protection under this study's rubric, not code quality. Prime is explicit about the trust model, which is preferable to treating a worker process as if it were a VM.

## 8. Extensibility

The low-level loop's hooks and replaceable conversion/stream functions support deep customization. The product adds executable Python skills. A skill is imported as a Python module with a callable `run`, and the helper can expose it as a command-line interface using signature-derived parsing. This goes beyond loading a Markdown prompt: a skill can contain reusable executable behavior. [P2] [P3] [P23]

MCP-related kernel and core modules exist, and the runtime reserves `mcp` as a bootstrap name rather than snapshotting it. The executable environment recreates connection machinery after startup. This chapter verifies that MCP participates in the runtime architecture but does not assert a server-export contract or every supported transport from that evidence alone. [P10]

Continual harness entries offer another extension plane: named subagent specifications and factory definitions can be edited and persisted. Factory validation is explicit code, not merely a prompt naming an orchestration pattern. These mechanisms increase flexibility while broadening the amount of state and executable material that must be trusted and versioned. [P20] [P29]

MCP has an explicit split: Rust manages authentication, catalogs and host requests, while the Python kernel owns generic protocol clients. The kernel registry exposes connection/tool listing, schema discovery and invocation; configuring a service need not require a new Python skill module. This client boundary is reusable but still executes under the privileged worker model described above. [P34] [P35]

## 9. Multi-agent

The Python API exposes real `spawn`, session creation, model discovery, child listing, result collection, deletion, and renaming. These operations are host requests, so children are owned by the daemon/session system rather than fake Python objects pretending to be agents. Callers can await selected results, perform other computation, or retain children for later work. [P24] [P25]

The child ledger supplies stable relationship evidence, and session metadata can account for usage even after a child is deleted. This is useful for long-running orchestration where children outlive a single chat response. It also highlights a cost-control issue: parent completion and child completion need explicit policy, because background work is not naturally bounded by a single model turn. [P26] [P31]

Factory specifications and the runtime executor support more structured composition. This chapter does not equate every factory path with a fully proven durable workflow engine; the source includes validation and orchestration machinery, but crash guarantees for every external node effect were not tested. Similarly, a child agent is not automatically in a separate Git worktree. That filesystem isolation must be verified or supplied independently. [P29] [P24]

## 10. Surfaces & integration

The Rust workspace separates CLI, TUI, daemon, core, agent, transport, models, types, and telemetry. ACP stdio mode is explicitly served over a daemon session, allowing editors to attach without owning a separate implementation of the loop. Print/headless paths are present in the CLI source, while the principal user experience remains the integrated terminal product. [P1] [P27]

For an embedding decision, distinguish modular code from a stable distributed SDK. `pa-agent` presents useful reusable interfaces, but the audit did not establish a separately versioned library compatibility promise for all internal crates. The Python `rlm` module is primarily the runtime control API used inside Prime's kernel, not a replacement for a provider-independent Python agent framework. [P2] [P24]

## 11. Observability & evals

The loop emits ordered events and waits for event listeners, so observers see causal order and can participate in failure handling. The telemetry crate exports event types, clients, file/no-op/mock/analytics sinks, and batching controls. These are concrete telemetry facilities, but the inspected public exports do not establish an OpenTelemetry exporter; the matrix leaves OTel unverified. [P2] [P28]

Session traces, refinement evidence, and child-ledger records make the system inspectable at several levels. None is an automatic quality guarantee. A successful refinement record may still encode a bad rule, and a cleanly restored snapshot may still miss an external action. The repository includes scripted loop and kernel recovery tests; this research did not run them or claim their results.

## 12. Notable design decisions & trade-offs

Prime makes the model's working environment a first-class stateful program. That enables code-based filtering, reuse of intermediate values, parallel child orchestration, and executable skills. The benefit is greatest for research or coding tasks with large intermediate artifacts; the cost is that conversation history alone no longer explains the full execution state. [P10] [P24] [P15]

The separate continual harness store is also distinctive. It gives supplemental instructions and reusable agent specifications lifecycle and provenance. Local/global scope prevents every session-specific adaptation from automatically becoming universal behavior, while versioned entries and refinement evidence make changes reviewable. This is architectural support for learning from work, not an empirical claim that the self-improvement process is reliable. [P20] [P21]

Finally, the Rust port preserves older wire and session contracts instead of treating the rewrite as a clean slate. That reduces migration friction but leaves compatibility concepts spread across implementation comments and types. The package boundary is clearer than the overall product's simplicity might suggest. [P1] [P17]

## 13. Scorecard

| Dimension | Score | Rationale |
|---|---:|---|
| Flexibility | 5 | Loop hooks, programmable runtime, skills, and editable harness state. |
| Integration | 4 | Daemon, TUI, ACP, sessions, goals, children, and compaction. |
| Embeddability | 3 | Modular internal crates; full product/runtime lifecycle remains substantial. |
| Durability | 4 | Session persistence, kernel snapshots, child ledger, and recovery semantics; no exactly-once effects. |
| Safety | 1 | Explicitly user-privileged execution; worker processes are not sandboxes. |
| Extensibility | 4 | Executable skills and broad hooks/control interfaces. |
| Multi-agent | 5 | Background children, collection, messaging-related daemon machinery, structured specifications. |
| Provider neutrality | 5 | Separate unified transport/model layers with several provider families. |
| Maturity | 3 | Active 0.10 product with migration complexity; adoption not independently measured. |
| Minimalism | 2 | Small low-level loop inside a much larger stateful native product. |

## 14. When to build on it / when not to

Choose Prime as an architecture reference or integrated base when long-lived programmable workspaces, recursive delegation, and editable supplemental memory are core requirements. Its separation of terminal attachment from agent lifecycle and its honest snapshot reporting are particularly useful patterns. [P15] [P24] [P27]

For a generic embedded service needing a small stable API or strong default confinement, assess lower-level libraries and external execution environments before adopting the full Prime stack. Any production workflow with irreversible operations must add idempotency and explicit side-effect recovery even if the session and Python namespace resume successfully. [P2] [P13] [P30]

## 15. Evidence index

Verification: static inspection of workspace manifests, low-level loop/configuration, batch dispatch, provider retry, tool contracts, REPL framing, namespace snapshot/restore guards, session persistence, compaction, refinement state, child APIs/ledger, ACP, and telemetry exports. All reference paths and line bounds were checked against the pinned clone. No code, tests, dependencies, or installers from the clone were executed. This chapter reports researcher checks, not independent adversarial verification.

[P1]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/Cargo.toml#L1-L42 "Cargo.toml:L1-L42"
[P2]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-agent/src/agent_loop/mod.rs#L1-L89 "crates/pa-agent/src/agent_loop/mod.rs:L1-L89"
[P3]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-agent/src/agent_loop/mod.rs#L91-L140 "crates/pa-agent/src/agent_loop/mod.rs:L91-L140"
[P4]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-agent/src/agent_loop/run.rs#L21-L130 "crates/pa-agent/src/agent_loop/run.rs:L21-L130"
[P5]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-agent/src/agent_loop/run.rs#L155-L244 "crates/pa-agent/src/agent_loop/run.rs:L155-L244"
[P6]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-agent/src/agent_loop/tools.rs#L31-L79 "crates/pa-agent/src/agent_loop/tools.rs:L31-L79"
[P7]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-agent/src/agent_loop/tools.rs#L81-L159 "crates/pa-agent/src/agent_loop/tools.rs:L81-L159"
[P8]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/tools/tool_definition.rs#L47-L104 "crates/pa-core/src/tools/tool_definition.rs:L47-L104"
[P9]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/tools/tool_definition.rs#L106-L149 "crates/pa-core/src/tools/tool_definition.rs:L106-L149"
[P10]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/repl.py#L1-L67 "prime-agent-runtime/src/rlm/repl.py:L1-L67"
[P11]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/repl.py#L113-L149 "prime-agent-runtime/src/rlm/repl.py:L113-L149"
[P12]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/repl.py#L731-L770 "prime-agent-runtime/src/rlm/repl.py:L731-L770"
[P13]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/repl.py#L771-L888 "prime-agent-runtime/src/rlm/repl.py:L771-L888"
[P14]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/repl.py#L1070-L1092 "prime-agent-runtime/src/rlm/repl.py:L1070-L1092"
[P15]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/kernel/state_snapshot.rs#L1-L56 "crates/pa-core/src/kernel/state_snapshot.rs:L1-L56"
[P16]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/session/manager/persist.rs#L1-L120 "crates/pa-core/src/session/manager/persist.rs:L1-L120"
[P17]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/session/mod.rs#L1-L42 "crates/pa-core/src/session/mod.rs:L1-L42"
[P18]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/session_engine/compact_session.rs#L1-L123 "crates/pa-core/src/session_engine/compact_session.rs:L1-L123"
[P19]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/session_engine/provider_retry.rs#L1-L90 "crates/pa-core/src/session_engine/provider_retry.rs:L1-L90"
[P20]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/refinement/mod.rs#L1-L109 "crates/pa-core/src/refinement/mod.rs:L1-L109"
[P21]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/harness.py#L389-L445 "prime-agent-runtime/src/rlm/harness.py:L389-L445"
[P22]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/harness.py#L1276-L1324 "prime-agent-runtime/src/rlm/harness.py:L1276-L1324"
[P23]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/skill.py#L1-L36 "prime-agent-runtime/src/rlm/skill.py:L1-L36"
[P24]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/__init__.py#L153-L243 "prime-agent-runtime/src/rlm/__init__.py:L153-L243"
[P25]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/__init__.py#L339-L447 "prime-agent-runtime/src/rlm/__init__.py:L339-L447"
[P26]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-daemon/src/rlm_ledger/replay.rs#L1-L95 "crates/pa-daemon/src/rlm_ledger/replay.rs:L1-L95"
[P27]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-daemon/src/acp/mod.rs#L1-L52 "crates/pa-daemon/src/acp/mod.rs:L1-L52"
[P28]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-telemetry/src/lib.rs#L36-L70 "crates/pa-telemetry/src/lib.rs:L36-L70"
[P29]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/factory.py#L487-L520 "prime-agent-runtime/src/rlm/factory.py:L487-L520"
[P30]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/README.md#L38-L101 "README.md:L38-L101"
[P31]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/session_engine/goal_driver.rs#L1-L80 "crates/pa-core/src/session_engine/goal_driver.rs:L1-L80"
[P32]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-ai/src/providers/mod.rs#L1-L19 "crates/pa-ai/src/providers/mod.rs:L1-L19"
[P33]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/resources/mod.rs#L1-L66 "crates/pa-core/src/resources/mod.rs:L1-L66"
[P34]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/crates/pa-core/src/mcp/mod.rs#L1-L59 "crates/pa-core/src/mcp/mod.rs:L1-L59"
[P35]: https://github.com/PrimeIntellect-ai/prime-agent/blob/791ce3d8f93aa863af63271e4646e46e38032a86/prime-agent-runtime/src/rlm/mcp.py#L1-L52 "prime-agent-runtime/src/rlm/mcp.py:L1-L52"
