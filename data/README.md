# Comparison records

Each JSON file is an object with a `records` array. A chapter may produce several records when a library, product, predecessor or sibling framework deserves a distinct comparison. `doc_path` points to the evidence and score rationale. These are judgments from static source review, not benchmark results.

Required identity fields: `slug`, `name`, `vendor`, `repo`, `license`, `language`, `version`, `category`, `one_liner`, `doc_path`. Categories are defined in [the methodology](../METHODOLOGY.md).

`scores` contains integers 1–5, or `null` when unassessable: `flexibility`, `integration`, `embeddability`, `durability`, `safety`, `extensibility`, `multi_agent`, `provider_neutrality`, `maturity`, `minimalism`.

`features` contains `yes`, `partial`, `no` or `unknown`: `mcp_client`, `mcp_server`, `skills`, `hooks`, `plugins`, `subagents`, `acp`, `headless`, `in_process_sdk`, `http_server`, `durable_resume`, `compaction`, `os_sandbox`, `approvals`, `plan_mode`, `worktrees`, `otel`, `web_ui`, `ide`, `agents_md`. Optional `features_notes` qualifies scope. In particular, `durable_resume` is not an exactly-once or durable-execution guarantee.

`dims` contains short prose for `loop`, `providers`, `tools`, `context`, `state`, `safety`, `extensibility`, `multi_agent`, `surfaces`, `observability`. `builds_on`, `used_by` and `key_insights` are arrays. Dependency, fork, protocol adapter and format-compatibility relationships must be described explicitly rather than inferred from a shared model provider.

Optional verification metadata records the review that actually happened. Mechanical citation checks and sampled semantic review are separate. Keep chapter scorecards and records consistent, then regenerate [the matrix](../comparison/matrix.md).
