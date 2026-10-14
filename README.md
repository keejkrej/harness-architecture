# AI agent harness architecture research

A source-based comparison of **53 components across 54 pinned repositories**, captured on **2026-10-14**. Thirty research chapters cover model libraries, embeddable harnesses, application frameworks, coding products and adjacent execution runtimes. The aim is to decide **what we can build on**, and to understand the architecture we would inherit.

This is static source research, not a benchmark, market-share ranking or security audit. Every listed source repository was cloned; no researched code was installed or executed. The inventory includes explicitly labeled source-available and historical proprietary exceptions. See [methodology](METHODOLOGY.md), [source pins](SOURCES.md) and [verification](comparison/verification.md).

## Start here

1. [Recommendations](comparison/recommendations.md): conditional shortlists for building a product or embedding an existing agent.
2. [Landscape and relationships](comparison/landscape.md): distinguish libraries, frameworks and products; trace dependency, fork and protocol boundaries.
3. [Embedding](comparison/embedding.md): in-process libraries versus services, subprocess SDKs and private/internal APIs.
4. [Generated comparison matrix](comparison/matrix.md): identities, ten score dimensions, twenty feature fields, dependencies and per-dimension summaries for all 53 records.

For specific architectural questions:

- [Durability](comparison/durability.md): transcript resume, turn recovery, checkpoint replay and external-effect ambiguity.
- [Loops, context and memory](comparison/loops-context.md): loop ownership, steering, parallel tools, compaction and provider boundaries.
- [Permissions and execution](comparison/safety.md): approvals, sandbox selection, platform differences and host-specific defaults.
- [Extensions and multiple agents](comparison/extensibility-multi-agent.md): hooks, middleware, plugins, delegation, handoffs, workflows and child-session ownership.

## Main conclusions

**Pi core, Pi coding agent and Pi Durable are distinct foundations.** The v1 change removed experimental session/durable machinery from core; current core remains an in-memory loop. Pi Durable calls Pi-ai directly and owns a separate durable task model. The coding agent adds its own tools, context, session tree, extension API and host surfaces. [Pi core and v1](harnesses/pi-core.md), [coding agent](harnesses/pi-coding-agent.md), [Durable](harnesses/pi-durable.md).

**“SDK” does not identify the execution boundary.** Cline now has public Agents/Core packages, and OpenCode V2 has a real embedded host. Codex and Claude product SDKs drive subprocesses. OpenClaw's public AI library is distinct from its private agent-core. Kilo's public subprocess SDK and private embedding prototype also deserve different treatment. [Embedding comparison](comparison/embedding.md).

**Persistence and recovery need mechanism-level comparisons.** Saving messages, restoring an interrupted turn and replaying recorded execution steps are different capabilities. Even a durable workflow can repeat an external effect after a crash. Storage defaults, worker ownership, tool replay policies and recovery configuration belong in the decision. [Durability comparison](comparison/durability.md).

**Safety features need a host and executor attached to the claim.** A permission rule, plan mode, worktree or local workspace object is not an OS sandbox. Product, SDK, headless and ACP surfaces can apply different policies; Windows, Linux and macOS implementations can have materially different limits. [Safety comparison](comparison/safety.md).

## Research chapters

The main chapters follow the shared architecture template. Grouped chapters give distinct systems separate matrix records where their behavior differs. The eight general frameworks in the last row receive an explicitly shallower breadth review; coverage is not uniform.

| Area | Chapters and scope |
|---|---|
| Pi ecosystem | [Pi core: Pi-ai + agent-core, including v1](harnesses/pi-core.md); [Pi coding agent](harnesses/pi-coding-agent.md); [Pi Durable](harnesses/pi-durable.md) |
| Named harness candidates | [DeepSeek Harness](harnesses/deepseek-harness.md); [Flue](harnesses/flue.md); [Eve](harnesses/eve.md); [Vercel AI SDK](harnesses/ai-sdk.md) |
| Additional reusable libraries/frameworks | [Deep Agents](harnesses/deepagents.md); [Mastra](harnesses/mastra.md); [Strands](harnesses/strands.md); [OpenAI Agents SDK](harnesses/openai-agents-sdk.md); [Google ADK Python/TypeScript](harnesses/google-adk.md) |
| Product cores and complete coding agents | [Codex](harnesses/codex.md); [OpenCode V2](harnesses/opencode.md); [Grok Build](harnesses/grok-build.md); [Kimi Code and predecessor](harnesses/kimi-code.md); [Gemini CLI / Qwen Code](harnesses/gemini-cli.md); [OpenHands](harnesses/openhands.md); [Goose](harnesses/goose.md) |
| More product implementations | [Hermes Agent](harnesses/hermes-agent.md); [OpenClaw and OpenClaw AI](harnesses/openclaw.md); [Mistral Vibe](harnesses/mistral-vibe.md); [Cline Agents/Core/apps and Kilo](harnesses/cline-kilo.md); [Crush / Fantasy boundary](harnesses/crush.md) |
| Python and current Letta lineage | [Pydantic AI/Harness, smolagents, Microsoft Agent Framework and TypeScript Letta Code](harnesses/python-frameworks.md) |
| Focused and experimental designs | [mini-swe-agent / Aider](harnesses/mini-swe-aider.md); [Prime Agent](harnesses/prime-agent.md); [fx/libfx, Rivet AgentOS and OpenHarness](harnesses/experimental.md) |
| Historical / closed-runtime comparison | [Historical Claude Code, current Claude Agent SDK and claw-code](harnesses/claude-code.md) |
| Broader frameworks, bounded review | [LangGraph, CrewAI, Agno, LlamaIndex, Haystack, DSPy, AutoGen and Semantic Kernel](harnesses/adjacent-frameworks.md) |

The versions above refer to the pinned source, not a promise that a registry's latest release has identical behavior. Pi's reviewed manifests are 1.2.0; the chapters explicitly trace the v1 architectural changes. Placeholder/dev versions, private packages, stale ADRs, optional integrations and migration notices are called out where relevant.

## Reading and maintaining the evidence

Architectural claims link to immutable source paths and line ranges. Synthesis pages link to the chapters containing that evidence. Scores are qualitative 1–5 judgments with written rationales, not measured performance. There is no overall score: integration, flexibility, minimalism and embeddability can pull in different directions. A feature marked partial can depend on the host, backend or configuration; unknown means the review did not establish it.

Crush's reviewed FSL release is source-available. The Claude source chapter is a historical proprietary-code exception; its source and prompts are not reproduced here, and it is not recommended as an open-source reuse foundation. A public client wrapper does not make a closed agent runtime open source.

The [verification report](comparison/verification.md) distinguishes mechanical checks from sampled semantic review and records corrections and remaining limits. The study is broad but does not claim to cover every product on the market or every transitive dependency.

To update the matrix from the [structured records](data/README.md):

```text
python scripts/build_matrix.py
python scripts/validate_research.py --skip-source-files
python scripts/build_matrix.py --check
```

For the full source-path and line-range audit, clone the manifest's repositories into sibling `harness-sources/` at their exact pins and run `python scripts/validate_research.py`. CI checks record structure, local link targets, Markdown table widths, source-pin consistency and generated matrix freshness; it does not download the source clones or run agents.
