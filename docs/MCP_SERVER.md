# Optional MCP Adapter Design

## Purpose

This document defines the TCS-Cosheaf MCP adapter boundary and current
implementation status. The current implementation is a local stdio
JSON-RPC surface with governance-safe prompt templates, operator-oriented
read-only tools, and controlled draft/review/runtime write tools. It does not
add external dependencies, change gates, write accepted knowledge, promote
artifacts, create human review, call hosted providers, or expose arbitrary
shell/filesystem authority.

MCP is optional. CLI remains the human and CI oracle, with typed services as
the shared implementation boundary. MCP may be useful for assistants that
support resources/tools, but it does not replace the CLI workflow or repository
policy.

The current adapter exposes typed, whitelisted service calls over MCP-style
resources and tools. Write-capable tools wrap existing Cosheaf service-layer
operations for draft/proposal/review-context/runtime records only. The adapter
must not expose arbitrary shell, arbitrary filesystem access, direct accepted
promotion, or private KB context outside an explicit policy scope.

## Current Status

Available commands:

```bash
cosheaf mcp list-tools
cosheaf mcp serve --stdio
```

`cosheaf mcp serve --stdio` reads one line-delimited JSON-RPC request from
stdin and writes one JSON-RPC response to stdout for each request. It is a
minimal local stdio surface, not an HTTP server and not a hosted service.

Current read-only/runtime-inspection tools:

- `workspace_info`
- `validate`
- `gate`
- `gate_pr_checklist`
- `gate_run`
- `memory_cards`
- `memory_search`
- `context_build`
- `context_show`
- `strategy_plan`
- `strategy_show`
- `strategy_graph`
- `strategy_next`
- `run_show`
- `run_evidence_report`
- `eval_strategy_planner`
- `eval_research_run_loop`
- `orchestrator_plan`

Current controlled draft/review/runtime write tools:

- `draft_artifact_create_or_update`
- `source_note_draft_create`
- `worker_bundle_validate`
- `worker_bundle_stage`
- `review_request_from_bundle`
- `checked_counterexample_evidence_validate`
- `checked_counterexample_evidence_stage`
- `failure_log_add_draft`
- `research_run_start`
- `research_run_append_command`
- `research_run_append_artifact`
- `research_run_append_output`
- `research_run_finalize`
- `research_run_export_review_dry_run`
- `research_run_export_review`
- `strategy_update_from_run`
- `strategy_export_review_dry_run`
- `strategy_export_review`

Current read-only resources:

- `cosheaf://workspace`
- `cosheaf://issues/{issue_id}`
- `cosheaf://artifacts/public/{artifact_id}/card`
- `cosheaf://artifacts/private/{artifact_id}/card`
- `cosheaf://context/public/{issue_id}`
- `cosheaf://context/private/{issue_id}`
- `cosheaf://gate/latest`

Legacy public aliases remain available for compatibility:

- `cosheaf://artifacts/{artifact_id}/card`
- `cosheaf://context/{issue_id}`

Current prompts:

- `start_issue_work`
- `reason_about_issue`
- `verify_draft`
- `prepare_review_bundle`
- `public_kb_contribution_check`

Prompt templates contain governance instructions only. They include the
accepted/draft distinction, instruct agents to use artifact IDs, forbid
accepted knowledge writes and promotion, and require final test/validate/gate
checks. Prompt templates do not include artifact text or private KB content.

The current tools call the Python service layer directly. They do not shell out
to the CLI. `gate`, `gate_pr_checklist`, and `gate_run` may write
deterministic runtime reports under ignored runtime directories such as
`.cosheaf/`. `context_build` may write a deterministic context pack under
`context/TASKS/`. `strategy_plan` may write a runtime strategy plan under
`.cosheaf/strategy/`. These runtime side effects do not write accepted
knowledge, promote artifacts, or mark human review. Controlled write tools may
create or update only draft/pre-accepted artifacts, draft source notes, draft
informational review requests, checked-evidence review records, failure-log
entries on writable non-accepted artifacts, research-run runtime records, or
strategy review exports through existing service-layer policy checks.

Public-mode MCP resources and search results do not expose private artifact
cards. Private-scoped artifact-card or context resource requests return a
structured `private_resource_denied` error unless a later private policy mode
explicitly permits them.

## Read-Only Operator Core

The read-only operator core keeps MCP in its intended place after the
CLI/provider hardening work: MCP is an optional read-only adapter, not a
provider transport, and not a replacement for ordinary CLI-first workflows.

The read-only smoke is covered by `tests/test_mcp_server.py`, including tool
whitelist checks, gate and PR-checklist reporting, public artifact cards,
public-scope strategy output, run/evidence reads, eval smoke reports,
private-resource denial, public-only context build, forbidden-tool rejection,
governance-safe prompts, stdio `tools/list` behavior, and controlled
draft/review/runtime write smoke.

The current B.1 decision is:

- keep the B.1 read-only tool set listed above;
- keep stdio as the only implemented MCP transport;
- keep private-scoped resources denied unless a later approved policy mode
  explicitly permits them;
- keep controlled-write MCP outside the B.1 read-only authority model and
  constrained to Phase C service-layer wrappers;
- do not add provider MCP tools, arbitrary shell, arbitrary filesystem access,
  accepted writes, accepted promotion shortcuts, human-review mutation, or
  verifier-result mutation.

Future MCP maintenance should keep both read-only and controlled-write tools
compatible with existing service contracts. Controlled draft/review/runtime
write tools must keep accepted writes, promotion, and human-review creation
absent.

## Transport

The current MCP transport is stdio.

Stdio keeps the adapter local, operator-launched, easy to test in CI with fake
clients, and free from network listener security questions. HTTP or hosted
transports require a later ADR and separate approval.

## Optional Session Recording

`tools/call` arguments may include an optional `session_id` for operator
session recording. The adapter strips `session_id` before invoking the
existing whitelisted tool, then appends bounded metadata to:

```text
.cosheaf/operator-sessions/<session-id>/events.jsonl
```

Calls without `session_id` remain stateless. Recorded events include tool name,
session mode, argument names/counts, status, a bounded result summary,
timestamp, and warning codes. They do not store full tool payloads, full
context packs, full artifact YAML, raw stdout/stderr, provider payloads,
secrets, hidden reasoning, environment dumps, or private query text in
public-only sessions.

Session recording does not make MCP authoritative. It is runtime review
metadata only and cannot create human review, accepted status, verifier pass,
gate pass, proof, accepted refutation, or promotion authority.

## Authority Model

MCP does not create new knowledge authority. It is an optional access surface
over the same service layer and repository invariants used by CLI and CI.

MCP resources expose context and data, not authority. Reading an artifact card,
context pack, gate report, or workspace policy through MCP does not mark
anything reviewed, accepted, verified, or promoted.

MCP tools are whitelisted service calls, not shell commands. A tool may call a
typed service such as workspace info, validation, gate execution, memory
search, context building, or bundle validation. It must not accept free-form
shell commands or unrestricted filesystem paths.

MCP prompts are workflow templates. They may help an agent ask for bounded
context, draft a PR summary, or follow review steps. Prompts do not grant
permission and do not override repository policy, gates, human review, or
promotion requirements.

Implemented prompts are static templates. They may include caller-provided
`issue_id` or `artifact_id` values, but they do not read issue text, artifact
statements, private KB records, provider credentials, environment variables, or
other repository content.

## Resource Taxonomy

Read-only resources may expose:

- workspace metadata and KB root policy;
- public memory cards and public context previews;
- issue-scoped context packs generated by existing context services;
- validation and gate summaries;
- retrieval audit metadata that does not include hidden private records;
- formal-link metadata with explicit warnings that links are not proof;
- task, run, or bundle metadata when policy allows it.

Resources must preserve root-scope metadata such as `public`, `private`,
`workspace`, or `framework`. Public-mode resources must not include private
artifact IDs, private artifact text, private-derived summaries, provider
credentials, environment dumps, or secrets.

## Tool Taxonomy

### Read-Only Tools

Implemented read-only tools include:

- `workspace_info`: returns workspace and KB root policy metadata.
- `validate`: runs or returns validation results.
- `gate`: runs gatekeeper and returns structured report metadata.
- `gate_pr_checklist`: runs gatekeeper with a repository-local PR checklist.
- `gate_run`: legacy alias for gatekeeper report metadata.
- `memory_cards`: lists public compact artifact cards.
- `memory_search`: searches bounded public artifact cards.
- `context_build`: builds an issue-scoped public-only context pack.
- `context_show`: builds and returns public-only context text.
- `strategy_plan`: builds a public-scoped runtime strategy plan.
- `strategy_show`: reads one public-scoped runtime strategy plan.
- `strategy_graph`: reads one public-scoped strategy task graph.
- `strategy_next`: reads public-scoped strategy next-step guidance.
- `run_show`: reads one research-run provenance record.
- `run_evidence_report`: returns read-only evidence counts for a run.
- `eval_strategy_planner`: runs deterministic strategy-planner eval smoke.
- `eval_research_run_loop`: runs deterministic research-run loop eval smoke.
- `orchestrator_plan`: creates a deterministic plan without executing workers.

Later read-only tools may include:

- `context.preview_provider_send`: returns provider-send preview metadata only.
- `task.list`: lists local task records.

Read-only tools must still respect public/private policy. A tool that triggers
local computation such as validation, gate execution, context building,
strategy planning, or eval smoke is still read-only if it only writes
deterministic runtime reports under ignored sidecar directories and does not
change source-of-truth artifacts.

### Controlled-Write Tools

Implemented controlled-write tools include:

- `draft_artifact_create_or_update`: creates or previews one controlled
  draft/pre-accepted artifact write.
- `source_note_draft_create`: creates or previews one draft source-note record.
- `worker_bundle_validate`: validates a WorkerBundle v2 manifest for review.
- `worker_bundle_stage`: validates/stages a WorkerBundle v2 manifest for
  review without task completion or promotion.
- `review_request_from_bundle`: creates or previews a draft informational
  review request from a WorkerBundle.
- `checked_counterexample_evidence_validate`: validates checked
  counterexample evidence without writing.
- `checked_counterexample_evidence_stage`: stages or previews checked
  counterexample evidence under review evidence paths.
- `failure_log_add_draft`: appends or previews one failure-log entry on a
  writable non-accepted artifact.
- `research_run_start`: creates one repository-local research-run provenance
  record.
- `research_run_append_command`: appends one sanitized command record to a
  research run.
- `research_run_append_artifact`: appends one artifact read/touched marker to
  a research run.
- `research_run_append_output`: appends one repository-local output/reference
  record to a research run.
- `research_run_finalize`: finalizes one research-run provenance record.
- `research_run_export_review_dry_run`: previews a research-run review export.
- `research_run_export_review`: writes a research-run review-context export.
- `strategy_update_from_run`: updates a runtime strategy plan from
  research-run provenance.
- `strategy_export_review_dry_run`: previews a strategy-plan review export.
- `strategy_export_review`: writes a strategy-plan review-context export.

Controlled writes wrap existing safe write semantics, require explicit tool
scope, remain narrow, typed, repository-local, and are blocked from readonly
public roots or accepted paths by shared service-layer policy checks.

Controlled-write MCP must never write to accepted paths, run accepted
promotion, mark human review complete, mutate verifier results, bypass gates,
or become required for ordinary CLI-first work.

### Forbidden Tools

The MCP adapter must not expose tools for:

- arbitrary shell execution;
- arbitrary filesystem read or write;
- reading environment variables or credential stores;
- dumping repository-private context in public mode;
- direct writes to `kb/accepted/`, `kb/public/accepted/`, or equivalent
  accepted lifecycle paths;
- `artifact promote` or accepted-promotion shortcuts;
- changing verifier results outside normal verifier adapters;
- marking AI or MCP output as human review;
- bypassing validation, gates, review, reducer, or promotion workflow;
- fetching or sending private KB context without explicit policy scope and
  configured root allowlist.

## Private KB Exposure

Private KB exposure requires all of:

- an MCP server configuration that allowlists the private root name or path;
- request-level `policy_mode=private_research`;
- explicit operator confirmation or configured consent for the operation;
- tool-specific scope validation before retrieval or context construction;
- structured output that labels private root scopes and risk flags.

Public mode must use public KB scope only for provider-send previews and must
not reveal private artifact IDs in output or audit details. Retrieval score,
PageRank, issue references, or pinned artifacts must not bypass scope filters.

## Structured Outputs

Tool outputs should use structured content where possible. Structured outputs
should map to existing service DTOs such as workspace info, validation results,
gate results, memory search results, context build results, provider context
previews, worker bundle submit results, draft write results, and `ErrorResult`.

Every expected error should include:

- `code`;
- `message`;
- `remediation`;
- `blocking`.

Skipped, unavailable, and denied results are not passes.

## Threat Model

MCP risks include:

- a broad tool accidentally becoming shell access;
- private KB leakage through resources, prompts, logs, or tool outputs;
- accepted knowledge writes through a convenient agent path;
- model output being confused with proof, validation, gate success, or human
  review;
- stale prompts or Skill text overriding current repository policy.

Required mitigations:

- expose only whitelisted service calls;
- keep stdio as the current transport;
- keep controlled writes narrow and service-layer-backed;
- reject accepted paths, readonly public roots, promotion attempts, human-review
  authority claims, and verifier/gate authority spoofing;
- preserve public/private root metadata in every relevant result;
- use `ContextSendPolicyService` for provider-send previews;
- keep accepted promotion outside MCP authority;
- keep negative tests for every controlled-write tool.

## Implementation Sequence

MCP implementation is optional and should not block CLI/provider work.

If the maintainer approves more MCP work, use this order:

1. Keep the current read-only stdio adapter constrained and tested.
2. Keep controlled-write MCP tools aligned with existing service-layer
   contracts and negative authorization tests.
3. Add security regression tests for any new private leakage or forbidden-tool
   surface.
4. Add provider-facing MCP tools only through a separate approved task; they
   must remain default-off and tested without network or API keys.

Each implementation step must be its own issue, branch, and PR.
