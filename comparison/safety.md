# Permissions and execution boundaries

A permission engine decides whether an action is authorized. A sandbox constrains what the action can do once started. A worktree separates files for collaboration. A parser or language interpreter restricts a particular execution interface. These are complementary controls, with different failure modes.

This is a static implementation comparison, not a security audit. The presence of a policy type or sandbox adapter does not establish its deployment configuration, completeness or resistance to attack.

## Available controls versus defaults

| System | Authorization | Execution boundary and practical qualification |
|---|---|---|
| [Pi core / coding agent](../harnesses/pi-coding-agent.md) | Tool hooks and extension-defined gates; project trust in product | No built-in OS confinement or complete approval policy; host owns it |
| [Pi Durable](../harnesses/pi-durable.md) | Tool filters and hooks | Durable effects are not automatically isolated; ExecutionEnv and host policy matter |
| [AI SDK](../harnesses/ai-sdk.md) | Tool approval requests and validation | Executing a JS tool runs application code; no universal local sandbox |
| [Flue](../harnesses/flue.md) | Application hooks, not a general approval engine | Local runtime is unconfined; selected sandbox adapters relocate execution |
| [Eve](../harnesses/eve.md) | Authenticated ingress and identity-aware approvals | Trusted Node tools can act outside the selected coding sandbox |
| [DeepSeek Harness](../harnesses/deepseek-harness.md) | Plugin-based guards and approval modes | Native confinement is principally about writes; broad reads/network and full-access minimal preset need separate attention |
| [Deep Agents](../harnesses/deepagents.md) | HITL interrupts and filesystem permissions | File-path rules do not govern every command run by an execution backend |
| [Mastra](../harnesses/mastra.md) | Tool approvals and guardrails | Native/remote sandbox support is optional; product shell approval does not itself isolate commands |
| [Strands](../harnesses/strands.md) | Interventions, policy/Cedar integration and HITL | Default local environment is explicitly not a sandbox; Docker/SSH are alternate environments |
| [Codex](../harnesses/codex.md) | Exec policy, approval policy, managed permissions and reviewer | Native platform backends plus network policy; the selected permission profile still determines the actual restriction |
| [OpenCode V2](../harnesses/opencode.md) | Resource rules, approval persistence and managed deny policy | No built-in OS sandbox; plugins run in-process; workspace drivers can relocate effects |
| [Grok Build](../harnesses/grok-build.md) | Rules, hooks, classifier and managed policy | Optional whole-process and per-command mechanisms; platform coverage and fail-open behavior differ |
| [Kimi Code](../harnesses/kimi-code.md) | Ordered policy chain and path checks | No OS sandbox identified; absolute outside-workspace file paths can be admitted; headless mode forces permissive auto mode after configured denials |
| [Goose](../harnesses/goose.md) | Inspectors, per-tool permissions, hooks and SmartApprove | Auto is default; egress inspector logs rather than blocks; containerized MCP does not cover all local tools |
| [OpenHands](../harnesses/openhands.md) | Risk analyzers and confirmation policies | LocalWorkspace runs on host; container workspace is a separate choice; ACP-hosted agents bypass its normal confirmation policy |
| [OpenAI Agents SDK](../harnesses/openai-agents-sdk.md) | Guardrails and approval interruptions | Isolation depends on sandbox backend; local JS and Linux Python paths do not provide shell confinement |
| [Gemini CLI / Qwen](../harnesses/gemini-cli.md) | Tiered policies in Gemini; different rules/classifier in Qwen | Optional process and per-tool controls; Windows network restriction is attempted throttling with a permissive failure path; UI, SDK and headless defaults differ |

## Four recurrent mistakes

### Calling every execution backend a sandbox

Local filesystem and shell abstractions are useful for portability, even when they impose no security boundary. OpenAI Agents SDK's JS `fileIOProtection` explicitly does not confine shell commands. OpenHands' local workspace executes on the host. Strands names its local option `NotASandboxLocalEnvironment`. These are not missing details to fill with an assumed container. [OpenAI local protection contract](https://github.com/openai/openai-agents-js/blob/89a9ddf1e241e75f2e0ad4c15d89de9e215ebac6/packages/agents-core/src/sandbox/sandboxes/unixLocal.ts#L130-L137), [Strands analysis](../harnesses/strands.md), [OpenHands analysis](../harnesses/openhands.md).

### Treating Plan mode as enforced read-only execution

Several products block edit tools while leaving shell commands available. Grok documents that Plan mode does not gate shell redirection. OpenCode's Explore agent grants shell access and relies on the prompt for read-only behavior. Kimi separates Plan mode from its permission chain. If a read-only phase is a requirement, verify OS/filesystem policy and every available tool path; a mode name is insufficient. [Grok](../harnesses/grok-build.md), [OpenCode](../harnesses/opencode.md), [Kimi](../harnesses/kimi-code.md).

### Assuming controls transfer across host surfaces

Gemini's in-repo SDK sets its policy default to ALLOW, whereas headless policy defaults can deny. Kimi's print host omits an interactive dangerous-command policy, and its ACP labels do not match the actual engine ordering of auto/yolo decisions. OpenHands' ACP wrapper approves the external agent's permission requests; the wrapper's usual confirmation policy does not transparently govern the child. These differences are why the chapter identifies the calling surface alongside the feature. [Gemini SDK config](https://github.com/google-gemini/gemini-cli/blob/65454d01f98f0983a4fee0773528fb42433131da/packages/sdk/src/session.ts#L74-L96), [Kimi policy ordering](https://github.com/MoonshotAI/kimi-code/blob/d4b9dc4a2d6ff72413964feda2563f0adf8e04d2/packages/agent-core-v2/src/agent/permissionPolicy/permissionPolicyService.ts#L39-L64), [OpenHands ACP analysis](../harnesses/openhands.md).

### Assuming containerizing tools also contains the host

An MCP client can launch one server in Docker while other tools remain in the agent process. Goose's developer shell constructs a local process directly. Eve's user-authored Node tools run as trusted application code. Even a well-confined coding sandbox cannot constrain a privileged host callback, plugin or credential service invoked beside it. [Goose local spawn](https://github.com/aaif-goose/goose/blob/9686d674000a5fbb8139214863289e4820714771/crates/goose/src/agents/platform_extensions/developer/shell.rs#L540-L587), [Eve tool boundaries](../harnesses/eve.md).

## Architectural consequences

For an embedded service, write down which process holds credentials, which process runs model-selected commands, and which process validates approval. Trace every tool to its actual executor. Include MCP servers, hooks, plugins, workflow scripts and remote-agent adapters; they can have different authority from the ordinary file tools.

Keep approval policy and enforcement configuration separate in the host API. Codex makes this separation explicit: approval policy is not the filesystem/network profile. This is a reusable design lesson even if Codex's full runtime is too large or model-specific for the application. [Codex policy and platform analysis](../harnesses/codex.md).

For multi-agent workloads, a separate context or git worktree is useful for coordination but does not isolate credentials, network access or OS identity. A subagent that shares its parent's host process can still exercise that process's authority through its tools. Compare [multi-agent boundaries](extensibility-multi-agent.md) before treating isolation in a scorecard as a deployment guarantee.
