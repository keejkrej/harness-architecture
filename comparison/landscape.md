# Landscape and implementation relationships

The inventory is organized by **the component you would reuse**, rather than by brand. A provider SDK, an in-process agent loop, a durable worker and a complete coding product solve different integration problems. The [matrix](matrix.md) gives each separable component a record; the [methodology](../METHODOLOGY.md) defines the categories and evidence limits.

## Six architectural families

| Family | Candidates in this study | Boundary to examine |
|---|---|---|
| Provider/model libraries | Pi-ai, AI SDK core, OpenClaw AI; DSPy also adds programming/optimization abstractions | Message representation, streaming, tool schemas and provider capability loss; the host usually owns lifecycle |
| Embeddable agent harnesses | Pi agent-core/coding-agent/Durable, Flue, Deep Agents, Strands, Cline Agents/Core, Pydantic AI/Harness | Whether the loop, tool executor, context projection and persistence can be composed without a product process |
| Application and orchestration frameworks | Eve, Mastra, OpenAI Agents SDK, Google ADK, Microsoft Agent Framework, LangGraph, CrewAI, Agno, LlamaIndex, Haystack | Runtime/storage dependencies, graph/workflow semantics, deployment and operational ownership |
| Products with reusable internal or public layers | OpenCode V2, OpenHands, Goose, DeepSeek Harness; Cline has distinct public library records | Public API stability versus internal modularity; transport, server and workspace boundaries |
| Integrated coding/personal agents | Codex, Grok Build, Kimi Code, Gemini/Qwen, Hermes, Vibe, OpenClaw, Kilo, Crush, Letta Code, Aider | Reuse the whole agent through its protocol or fork the implementation; do not assume an SDK exports the loop |
| Experimental loops and adjacent execution | Prime Agent, mini-swe-agent, fx, OpenHarness, Rivet AgentOS | Scope, maturity and whether the project supplies an agent at all; AgentOS is an execution substrate |

This is a navigation taxonomy, not a claim that every project fits exactly one box. For example, AI SDK's core loop is small while its optional Workflow integration has a different recovery boundary. Eve is authored as an application and deployed with a runtime; it is not equivalent to importing a small function. DeepSeek has unusually replaceable plugins but still exposes its SDK through a product process. [AI SDK](../harnesses/ai-sdk.md), [Eve](../harnesses/eve.md), [DeepSeek Harness](../harnesses/deepseek-harness.md).

## Dependency, incorporation and protocol edges

The arrow below reads “uses the implementation of.” Forks, incorporated code and remote delegation are named separately. Each linked chapter contains pinned package/import evidence.

| Relationship | What is established at the reviewed pin |
|---|---|
| Pi agent-core → Pi-ai | The ordinary agent loop uses the provider layer; its state is in memory |
| Pi coding-agent → Pi agent-core + Pi-ai | AgentSession adds tools, context handling, session trees, extensions and UI/SDK/RPC surfaces |
| Pi Durable → Pi-ai + Chord | A separate durable-task loop, **not** a durable wrapper around current pi-agent-core |
| Flue → Pi agent-core + Pi-ai | Flue adds agent authoring, lifecycle, execution adapters and optional durable steps |
| DeepSeek Harness → optional Pi-ai adapter | An optional model-provider implementation; the kernel/agent loop is its own plugin system |
| OpenClaw → incorporated Pi-derived code; direct Pi TUI package | Its private agent-core is now OpenClaw-owned; current use is not simply an installed pi-agent-core dependency. OpenClaw AI is separately reusable |
| Eve → AI SDK ToolLoopAgent + Vercel Workflow | Workflow owns durable session/turn transitions; the inner model step uses AI SDK |
| Mastra → AI SDK provider interfaces/adapters | Mastra owns its agent/workflow loop. Mastra Code's Pi TUI use is a UI dependency |
| Deep Agents → LangChain create_agent → LangGraph | Deep Agents assembles middleware/backends into a graph returned by LangChain; checkpoint/runtime behavior belongs to the configured graph stack |
| Cline Core → Cline Agents → Cline LLMs / AI SDK integrations | Public packages separate the basic runtime, host services and product applications |
| OpenCode V2 → own core/model packages, with AI SDK bridge | Its real embedded host is distinct from the older server-client SDK description |
| Kilo ← OpenCode fork lineage | The reviewed Kilo declares OpenCode lineage; older Cline-era descriptions do not explain this pin |
| Crush → Fantasy | Fantasy supplies the model/agent machinery; Crush adds coordinator, tools, sessions and user surfaces |
| OpenHands SDK → own Agent/event contracts | Local and remote workspaces host its loop; ACP adapters can instead delegate to an external agent |
| Claude Agent SDK → Claude Code child process | The library exposes callbacks and control protocol; the closed child owns the agent loop |

Evidence: [Pi core](../harnesses/pi-core.md), [Pi coding agent](../harnesses/pi-coding-agent.md), [Pi Durable](../harnesses/pi-durable.md), [Flue](../harnesses/flue.md), [DeepSeek](../harnesses/deepseek-harness.md), [OpenClaw](../harnesses/openclaw.md), [Eve](../harnesses/eve.md), [Mastra](../harnesses/mastra.md), [Deep Agents](../harnesses/deepagents.md), [Cline/Kilo](../harnesses/cline-kilo.md), [OpenCode](../harnesses/opencode.md), [Crush](../harnesses/crush.md), [OpenHands](../harnesses/openhands.md), [Claude](../harnesses/claude-code.md).

Three other relationships should stay separate. A project can call an OpenAI-compatible endpoint without using the OpenAI Agents SDK. It can launch Codex or Claude via ACP without incorporating their loop. It can recommend migration to Microsoft Agent Framework without depending on MAF: the AutoGen and Semantic Kernel successor notices are product direction, not runtime edges. [Provider boundaries](loops-context.md), [adjacent frameworks](../harnesses/adjacent-frameworks.md).

## Version changes that alter the comparison

| Familiar description | What the pinned implementation requires you to distinguish |
|---|---|
| “Pi now has durability in core” | Pi v1 removed experimental session/durable machinery from core; Pi Durable is a separate task runtime using Pi-ai |
| “OpenCode's SDK only calls a server” | V2 includes a real in-process host; its default database is ephemeral unless configured |
| “Cline is an IDE task class” | Current Cline exposes an SDK monorepo with Agents, LLMs and Core packages |
| “OpenClaw just uses Pi's agent package” | Incorporated Pi lineage, a current private OpenClaw core, public OpenClaw AI and direct Pi TUI dependency are different facts |
| “Vibe saves JSONL but cannot replay” | The default unified Rust/Python runtime journals inputs, effects and results; the legacy loop and its ADR describe a different path |
| “WorkflowAgent.generate is not implemented” | AI SDK's reviewed implementation includes it; an old design note is stale |
| “A durability flag guarantees crash snapshots” | Mastra's running-state checkpoints also depend on its recovery/custom policy or orderly shutdown |
| “All Microsoft frameworks are equally current choices” | The reviewed AutoGen and Semantic Kernel repositories point to MAF; retain them for lineage/migration comparisons |

These are source observations, not promises about future releases. All names, versions and source pins are in [the manifest](../SOURCES.md) and the linked chapters.

## Breadth and exclusions

The research follows the named candidates and expands through widely discussed public frameworks, product implementations, useful minimal baselines and implementation dependencies. It does not establish which are most popular: stars, downloads, enterprise adoption and developer mindshare measure different things, and were not normalized here.

The general-purpose frameworks in [the breadth chapter](../harnesses/adjacent-frameworks.md) receive shorter, bounded reviews than the original deep dives. Retrieval and optimization stacks are useful comparisons even when they are not the right substrate for a coding product. Rivet AgentOS is explicitly adjacent infrastructure, so its model-loop scores are unassessable.

Closed products without a reviewable implementation are not assigned invented architecture scores. Nor does the study claim a full review of every hosted service, deployment backend, language port, external adapter, workflow engine or transitive dependency mentioned in the chapters. Fantasy and Vercel Workflow are analyzed through their consumer boundaries here, not as separately audited complete runtimes. Publicly accessible code is not automatically open source: Crush's FSL pin and the historical proprietary Claude snapshot are marked exceptions throughout.
