# Conditional shortlists for building on a harness

There is no defensible single winner across these systems. The useful choice depends on how much of the agent you want to own, what must survive a restart, and whether you want an application framework or an existing coding product. These are **source-based architectural recommendations**, not benchmark results or claims of production reliability. See [embedding](embedding.md), [durability](durability.md), [safety](safety.md) and the [matrix](matrix.md) for the tradeoffs.

## Start with these comparisons

| Need | First candidates to compare | Why they belong together | Decisive trial |
|---|---|---|---|
| A small TypeScript loop under your control | Pi core, AI SDK ToolLoopAgent, Cline Agents | Embeddable primitives, different provider/message/tool contracts | Implement the same tool, streaming UI, cancellation and custom context transformation |
| A ready coding harness inside your own host | Pi coding agent, Cline Core, OpenCode V2; Deep Agents if its graph/backend model fits | More tools/context/session machinery than a bare loop | Embed without the bundled UI; supply persistent storage and your own authorization/executor |
| Durable TypeScript agent work | Pi Durable, Flue, Eve, Mastra DurableAgent, AI SDK Workflow integration | Different placements of task/checkpoint/workflow ownership | Kill between effect and result; resume approvals; test worker ownership and an upgrade |
| A Python agent framework | Pydantic AI/Harness, OpenAI Agents SDK, Strands, Google ADK; MAF for its workflow/messaging ecosystem | Typed/tool-driven APIs with different state, handoff and hosting contracts | Build one realistic run, interrupt it, resume state and replace the execution backend |
| Explicit graph/workflow orchestration | LangGraph, Mastra, ADK, MAF, CrewAI Flows | Branches, waits and state are modeled directly | Inspect persisted transitions and recovery of parallel branches; avoid inferring hosted features from local SDKs |
| A Python coding workspace agent | OpenHands SDK, Pydantic Harness, Strands harness | Compare reusable tool, context and workspace contracts | Run with the intended workspace/confirmation policy and inspect what survives restart |
| A complete agent behind a protocol | Codex, OpenCode, Grok Build, Kimi, Goose, Vibe, Letta Code; Gemini/Qwen for their specific ecosystems | Useful headless/server/protocol surfaces without rebuilding the product loop | Disconnect/reconnect a client, answer an approval, cancel work and verify terminal state |
| A channel/gateway personal-agent product | OpenClaw, Hermes, Eve | Long-lived identity, routing, sessions and extensible ingress | Verify caller authority, delivery recovery and whether plugins can act outside the coding sandbox |
| Learn the smallest coding-agent loop | mini-swe-agent and Pi core; Aider for a specialized edit/repo-map design | Legible baselines expose which features larger systems add | Trace one request through model, tool/edit and result; do not assume equivalent deployment features |
| Study replacement seams or new runtime designs | DeepSeek Harness, Prime Agent, fx, OpenHarness, Vibe's unified runtime | Plugin kernels, programmable reasoning, explicit effects and small prototypes offer different design lessons | Inspect one extension/recovery path end-to-end; maturity and API stability need separate validation |

Chapter evidence: [Pi core](../harnesses/pi-core.md), [AI SDK](../harnesses/ai-sdk.md), [Cline](../harnesses/cline-kilo.md), [Pi coding agent](../harnesses/pi-coding-agent.md), [OpenCode](../harnesses/opencode.md), [Deep Agents](../harnesses/deepagents.md), [Pi Durable](../harnesses/pi-durable.md), [Flue](../harnesses/flue.md), [Eve](../harnesses/eve.md), [Mastra](../harnesses/mastra.md), [Python frameworks](../harnesses/python-frameworks.md), [OpenAI SDK](../harnesses/openai-agents-sdk.md), [Strands](../harnesses/strands.md), [ADK](../harnesses/google-adk.md), [adjacent frameworks](../harnesses/adjacent-frameworks.md), [OpenHands](../harnesses/openhands.md), [Codex](../harnesses/codex.md), [Grok](../harnesses/grok-build.md), [Kimi](../harnesses/kimi-code.md), [Goose](../harnesses/goose.md), [Vibe](../harnesses/mistral-vibe.md), [Gemini/Qwen](../harnesses/gemini-cli.md), [OpenClaw](../harnesses/openclaw.md), [Hermes](../harnesses/hermes-agent.md), [mini-swe-agent/Aider](../harnesses/mini-swe-aider.md), [DeepSeek](../harnesses/deepseek-harness.md), [Prime](../harnesses/prime-agent.md), [experimental runtimes](../harnesses/experimental.md).

## For the original “library we can build on” question

Begin with **Pi core versus Pi coding agent versus Pi Durable**, treating them as three different levels rather than successive editions of one abstraction. Core gives a small in-memory loop; coding-agent gives an embeddable product harness; Durable gives a separate execution model with explicit replay contracts. The v1 split is central to understanding the ecosystem.

Next compare **AI SDK, Flue, Deep Agents, Cline Core and Strands** against the layer you actually need. AI SDK is useful when you already own application state and policy. Flue layers authoring and runtime facilities over Pi. Deep Agents gives a graph/middleware/backend composition. Cline's current public packages provide a more directly embeddable option than its older IDE-centric reputation suggests. Strands separates the model-driven SDK from harness defaults and environment adapters.

Bring **Eve and Mastra** into the comparison when you want an application/runtime framework, and **OpenCode V2 or OpenHands** when a product-scale reusable core is valuable. These can save considerable assembly, but their host/state/deployment contracts are larger than a minimal loop. DeepSeek is particularly instructive when replacing kernel services through plugins matters more than having a tiny standalone library.

Keep **Codex, Grok Build and Kimi Code** as protocol-integration and architecture references. Their sophisticated product behavior is useful, but reproducing it by importing internal modules is a different commitment from using a supported harness library. The same distinction applies to historical Claude Code versus the current Claude Agent SDK: the SDK is a client for the closed runtime, not an open in-process implementation of its loop.

## What changes the shortlist

- **Crash-safe business effects:** require destination idempotency or reconciliation in addition to framework checkpoints. No score in this study proves exactly-once arbitrary remote effects.
- **Untrusted code execution:** choose the actual executor and policy profile. Approval prompts, plan modes, language interpreters and local workspace adapters are insufficient evidence of OS isolation.
- **Minimal operational footprint:** include the database, worker, sandbox provider and service runtime in the comparison; package size alone misses these dependencies.
- **Model portability:** test the message/tool/reasoning features you use across providers. An OpenAI-compatible endpoint does not imply native support for every provider protocol.
- **Stable public integration:** prefer published, documented entry points over private packages and internal imports; a high product version does not establish independent SDK stability.
- **Reuse license:** inspect the pinned license and relevant packages. Crush's reviewed FSL version is a source-available exception; the proprietary historical Claude source is an architecture reference, not an open-source building block.

## A bounded selection experiment

Pick three candidates that solve the same integration problem. Give each the same model, tools, workspace, policy and test task. Measure integration effort, inspect event/state artifacts, and execute the six [recovery experiments](durability.md#what-to-test-before-choosing-a-runtime). Add a platform-specific sandbox check and a second model provider only if those are requirements.

Choose weights before scoring the result: for example, embeddability and recovery may matter much more than a bundled UI or plugin marketplace. The repository's 1–5 ratings expose architectural differences; they deliberately have no sum. An empirical trial can justify a choice that static source inspection alone cannot.
