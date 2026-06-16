# Roadmap

TCS-Cosheaf has prepared the `v0.6.0` Operator Session + Review Handoff release
candidate after the published `v0.5.0` Operator MCP + Codex Application Layer
release and the published `v0.4.0` Strategy Planner + Research Task Graph
release. `v0.6.0` is a replayable, redacted, review-context handoff layer over
the existing CLI/MCP/service surfaces. The public `v0.6.0` tag, GitHub release,
post-tag release smoke, and downstream workspace/public-KB pin updates are not
complete yet; `v0.5.0` remains the latest published downstream baseline. This
follows the published `v0.3.0` Checked Evidence and Research Run Loop release,
the published `v0.2.4` Artifact Failure Memory and Attempt Traceability
release, the published `v0.2.3` Verification Evidence Hardening release, the
published `v0.2.2` Provider Transport and Agent Workflow Hardening release, the
published `v0.2.1` CLI Agent Access and Hosted Provider Gateway prerelease, the
published `v0.2.0` local-MVP release, and the earlier `v0.1.1` Formal Link
Layer support baseline. The project is still not production-ready. This roadmap
records durable direction and named milestones; live issue state belongs in
GitHub issues.

## Active Release Focus: v0.6.0 Operator Session + Review Handoff

The active post-`v0.5.0` line is `v0.6.0` Operator Session + Review Handoff.
`v0.5.0` exposed a safe optional operator MCP layer and CLI-first runbooks.
`v0.6.0` adds the missing audit layer around a whole operator session. Package
metadata now records the `0.6.0` release candidate; publication and downstream
pin alignment remain follow-up work.

The active plan is
[`docs/CODEX_DEVELOPMENT_PLAN_V10.md`](CODEX_DEVELOPMENT_PLAN_V10.md), with
the kickoff audit in
[`docs/POST_V050_STATE_AUDIT.md`](POST_V050_STATE_AUDIT.md) and the
architecture decision in
[`docs/ADR/0027-operator-session-review-handoff.md`](ADR/0027-operator-session-review-handoff.md).

This line has now added the core session, recording, scanning, runtime
handoff-bundle, explicit handoff-export surfaces, downstream demo/policy
coverage, ecosystem smoke rows, and release-candidate metadata:

- add strict operator-session records and runtime storage under ignored
  `.cosheaf/operator-sessions/` paths;
- add CLI commands to start, inspect, append safe checks/references to, scan,
  and finalize operator sessions;
- optionally record bounded MCP tool-call metadata when a session ID is
  supplied;
- scan sessions and handoff candidates for secrets, private/public leakage,
  hidden reasoning markers, provider payloads, accepted-write attempts, and
  authority overclaims;
- build compact runtime handoff bundles from finalized sessions; and
- export explicit review-context YAML under `reviews/operator/`.
- verify downstream workspace-template and public KB handoff policy coverage
  through deterministic ecosystem smoke rows.

This line will not make sessions, MCP recordings, scans, handoff bundles, or
handoff exports proof, verifier evidence, verifier pass, gate pass, human
review, accepted status, accepted refutation, public KB source metadata, or
promotion authority. It will not add production hosted multi-agent SaaS, web
UI, multi-user permissions, default hosted provider calls, API-key
requirements, accepted writes, promotion through operator sessions, human-review
creation, verifier-result mutation, automatic theorem proving, automatic Lean
alignment, or replacement of GitHub PR review.

The publication closeout still needs to create the public `v0.6.0` tag and
GitHub release, run post-tag release smoke, update downstream pins, and record
the final evidence. Until then, downstream repositories should keep using the
latest published `v0.5.0` baseline unless they intentionally test from a local
checkout.

## Completed Release Focus: v0.5.0 Operator MCP + Codex Application Layer

The completed post-`v0.4.0` line is `v0.5.0` Operator MCP + Codex Application
Layer. The public tag and GitHub release are published, release smoke from
`@v0.5.0` passed, and downstream workspace/public-KB pins are updated.
`v0.4.0` records planned research processes through strategy
plans; `v0.5.0` makes those workflows safer and easier for Codex-style
operators to drive through optional MCP tools and documented CLI fallback.

The completed plan is
[`docs/CODEX_DEVELOPMENT_PLAN_V9.md`](CODEX_DEVELOPMENT_PLAN_V9.md), with the
kickoff audit in
[`docs/POST_V040_STATE_AUDIT.md`](POST_V040_STATE_AUDIT.md) and the
architecture decision in
[`docs/ADR/0026-operator-mcp-codex-application-layer.md`](ADR/0026-operator-mcp-codex-application-layer.md).

This line:

- expanded the existing minimal read-only MCP surface into an optional operator
  MCP tool layer for workspace, validate, gate, memory, context, strategy,
  research-run evidence, and eval smoke;
- added controlled MCP write tools that wrap existing safe draft/proposal,
  review-context, and runtime write semantics;
- keeps CLI as the human and CI oracle, with documented fallback when MCP is
  unavailable;
- added operator runbooks, workspace-template demo coverage, and public KB
  policy smoke for operator/MCP outputs; and
- published a conservative `v0.5.0` release after tests, docs, downstream
  demo/policy, tag-based release smoke, and pin updates passed.

This line does not make MCP output proof, evidence, verifier pass, gate pass,
human review, accepted status, accepted refutation, or promotion authority. It
does not expose accepted writes, promotion, human-review creation, arbitrary
shell, or default hosted provider calls through MCP.

## Completed Release Focus: v0.4.0 Strategy Planner + Research Task Graph

The completed post-`v0.3.0` line is `v0.4.0` Strategy Planner + Research Task
Graph. `v0.3.0` records checked evidence and reproducible external-operator
research runs; `v0.4.0` adds the planning layer that decides what to try next.

The completed plan is
[`docs/CODEX_DEVELOPMENT_PLAN_V8.md`](CODEX_DEVELOPMENT_PLAN_V8.md), with the
architecture decision in
[`docs/ADR/0025-strategy-planner-task-graph.md`](ADR/0025-strategy-planner-task-graph.md).

This line:

- models research problems with issue, domain, target-artifact, constraint, and
  desired-evidence metadata;
- models directed research task graphs with prerequisites, blocked-by edges,
  expected evidence, and related artifacts or evidence;
- produces deterministic strategy plans with ranked next steps and explanations;
- uses failure memory, candidate counterexamples, checked counterexample
  evidence, and research-run provenance without changing their authority;
- integrates compact strategy references into context and read-only readiness
  surfaces without private leakage;
- adds deterministic eval and security coverage for strategy-planner
  boundaries;
- adds workspace-template strategy demos and public KB strategy-plan policy;
  and
- published a conservative `v0.4.0` release after implementation, downstream
  integration, evals, and smoke coverage pass.

This line will not make strategy plans proof, evidence, verifier pass, gate
pass, human review, accepted status, accepted refutation, or promotion
authority. Provider calls remain explicit and default-off. MCP remains
optional and non-blocking.

## Completed Release Focus: v0.3.0 Checked Evidence + Research Run Loop

The post-`v0.2.4` line is `v0.3.0` Checked Evidence + Research Run Loop.
The `v0.2.x` series is treated as the completed CLI-agent, provider,
verification-evidence, and artifact failure-memory foundation. `v0.3.0` starts
the next stage: durable checked evidence and reproducible external-operator
research runs.

The completed plan is
[`docs/CODEX_DEVELOPMENT_PLAN_V7.md`](CODEX_DEVELOPMENT_PLAN_V7.md), with the
kickoff audit in
[`docs/POST_V024_V030_KICKOFF_AUDIT.md`](POST_V024_V030_KICKOFF_AUDIT.md) and
ADR 0024 in
[`docs/ADR/0024-checked-evidence-research-run-loop.md`](ADR/0024-checked-evidence-research-run-loop.md).

This line:

- kept `candidate_counterexample` metadata separated from durable
  `checked_counterexample_evidence`;
- added the reviewable, repository-local checked-evidence model, schema,
  CLI, context/readiness surfacing, security tests, and eval fixtures;
- added research-run records with start, append, finalize, show,
  evidence-report, export-review, and replay-plan CLI surfaces;
- kept Codex-style agents as external CLI/Git operators rather than embedding
  GPT, Claude, or any hosted model as the default runtime;
- kept the workspace-template research-run demo and public KB checked-evidence
  policy aligned with the framework surfaces;
- integrated checked-evidence and research-run evals into the three-repository
  smoke matrix without requiring network, hosted providers, MCP, SAT, SMT,
  Lean, or lake by default; and
- published a conservative `v0.3.0` release only after implementation,
  downstream alignment, evals, and smoke coverage passed.

The implementation, downstream demo/policy surfaces, and integration/eval smoke
matrix have landed. The public `v0.3.0` tag and GitHub release are published,
release smoke from `@v0.3.0` passed, and downstream workspace/public KB pins
now use `v0.3.0`.

This line does not make checked evidence human review, proof, accepted
refutation, accepted status, or promotion authority by itself. Research-run
records are provenance, not proof, verifier pass, gate pass, human review,
accepted status, or promotion authorization. Provider calls remain explicit,
default-off, policy-scoped, previewed, consented, and excluded from CI/default
tests. MCP remains optional and non-blocking.

## Current Release Candidate: v0.6.0

Package metadata and `cosheaf.__version__` record `0.6.0` in the release
candidate. `docs/releases/v0.6.0.md` records the conservative release scope and
limitations. The public `v0.6.0` tag and GitHub release are not published yet,
post-tag release smoke has not run, and downstream workspace/public-KB pins
remain on `@v0.5.0` until publication closeout.

The `v0.6.0` candidate includes bounded operator-session records, optional MCP
session recording, leak scanning, runtime handoff bundles, review-context
handoff export, downstream operator-session demo coverage, public KB
operator-handoff policy checks, and ecosystem smoke rows.

This candidate does not make sessions, MCP recordings, scans, handoff bundles,
or handoff exports proof, source metadata, checked evidence, verifier pass,
gate pass, human review, accepted status, accepted refutation, or promotion
authority. It does not add default hosted provider calls, API-key requirements,
accepted writes, promotion semantics changes, web UI, production hosted
multi-agent runtime, or automatic theorem proving.

## Latest Published Release: v0.5.0

At publication time, package metadata and `cosheaf.__version__` recorded
`0.5.0`. `docs/releases/v0.5.0.md` records the conservative release scope. The
public `v0.5.0` tag and GitHub release are published, release smoke from
`@v0.5.0` passed, and downstream workspace/public-KB pin updates are complete.

The `v0.5.0` release includes the optional read-only operator MCP
surface, controlled draft/review/runtime MCP tools, operator runbook and
workspace demo docs, public KB operator policy smoke, and optional
documentation-only operator Skill package.

This release does not make MCP or operator output proof, checked
evidence, verifier pass, gate pass, human review, accepted status, accepted
refutation, or promotion authority. It does not add default hosted provider
calls, API-key requirements, accepted writes, promotion semantics changes, web
UI, production hosted multi-agent runtime, or automatic theorem proving.

## Previous Published Release: v0.4.0

`docs/releases/v0.4.0.md` records the conservative release scope. The public
`v0.4.0` tag and GitHub release are published, and release smoke from
`@v0.4.0` passed. Downstream workspace/public-KB pin updates are complete.

The `v0.4.0` line now has strategy/task-graph model and schema support,
deterministic strategy CLI surfaces, run-loop integration, context/retrieval
surfacing, promotion-readiness advisory warnings, strategy review export,
strategy-planner evals, security coverage, workspace-template strategy demo,
public KB strategy-plan policy, and framework ecosystem-smoke rows.

This release does not make strategy plans proof, evidence, verifier
pass, gate pass, human review, accepted status, accepted refutation, or
promotion authority. Provider calls remain explicit and default-off. MCP
remains optional and non-blocking.

## Previous Published Baseline: v0.3.0

The previous published release before `v0.4.0` was `v0.3.0`. Its public tag
and GitHub release are published and release smoke from `@v0.3.0` passed.
Downstream workspace/public KB active pins now use `v0.5.0`; `v0.3.0` remains a
historical checked-evidence and research-run baseline for users who
intentionally pin that older line.

The previous published baseline was `v0.2.4`. It packaged optional
artifact-level `failure_log` support, read-only and controlled draft
failure-log CLI surfaces, WorkerBundle failure-log bridges,
retrieval/context/promotion-readiness surfacing, workspace-template
demonstration, public KB policy, and security/eval regression coverage without
turning failure memory into proof, verifier success, checked counterexample
evidence, human review, accepted status, or promotion evidence.

## Completed Baseline: v0.2.3 Published Release

The `v0.2.3` release packages the post-`v0.2.2`
verification/evidence-hardening line. It adds normalized verifier evidence
records, read-only promotion-readiness reporting, optional SAT/SMT/Lean result
depth fixtures, Lean external reference ergonomics, typed counterexample
candidate records, failure-preserving review-request generation,
verifier-evidence eval coverage, and an expanded three-repository readiness
matrix without overclaiming production readiness, automatic theorem proving,
Lean autoformalization, informal/formal semantic alignment, accepted-knowledge
automation, or provider/MCP authority expansion.

Completed `v0.2.3` work includes:

- Package metadata and release notes for `v0.2.3`.
- Verifier evidence status audit and ADR 0022.
- `VerifierEvidenceRecord` v1 model and schema.
- Read-only `cosheaf promotion readiness` reports.
- SAT and SMT optional result-depth fake-backend fixtures.
- Lean external reference diagnostics and fake-backend coverage.
- Typed WorkerBundle v2 counterexample candidate records.
- Failure-preserving draft review-request generation from WorkerBundle v2.
- Verifier-evidence eval suite.
- Three-repository `v0.2.3` readiness matrix.
- Published `v0.2.3` tag and GitHub release.
- Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.3`.
- Workspace-template `@v0.2.3` active pin update and demo/provider/verifier
  smoke regression.
- Public KB `@v0.2.3` CI pin update, validation, gate, PR-checklist, and
  repository-local policy guard regression.

The 2026-06-14 release action verified that the annotated `v0.2.3` tag
resolves to the reviewed release-candidate main commit and that release smoke
installed `tcs-cosheaf==0.2.3` from the tag. Downstream workspace-template and
public KB active pins now use `v0.2.3`.

## Completed Release Focus: v0.2.2 Provider Transport + Agent Workflow Hardening

The `v0.2.2` release packages the post-`v0.2.1` provider transport
and agent workflow hardening work. It is a framework release for
explicit default-off real-provider calls, provider context-send policy checks,
provider log scanning, failure/counterexample preservation, deterministic
provider/failure evals, and three-repository smoke coverage without
overclaiming production readiness, automatic theorem proving, Lean
autoformalization, or accepted-knowledge automation.

Completed `v0.2.2` work includes:

- Package metadata and release notes for `v0.2.2`.
- Stable JSON/error contracts for core agent-facing CLI commands.
- Controlled draft/proposal/bundle/source-note/review-request CLI write
  surfaces.
- CLI operator workflow documentation and optional operator Skill package.
- Provider gateway design, fake provider path, and OpenAI-compatible mocked
  transport boundary.
- Provider CLI commands for list, config-check, preview-send, and fake-run.
- Role-specific hosted worker service over fake or mocked provider calls.
- Internal orchestrator dispatch to hosted workers when explicitly configured.
- Agent-access security regression coverage and agent workflow evaluation
  suite.
- Optional stdlib OpenAI-compatible HTTP transport object, default-off and
  explicitly configured/injected.
- Explicit provider `real-run` CLI path with inline preview, consent, network,
  endpoint/key, and private-context checks.
- Provider context-send policy matrix and provider log leak scanner.
- WorkerBundle failure/counterexample preservation and role-contract
  hardening.
- Provider malformed-output recovery plus provider-workflow and
  failure/counterexample eval suites.
- Three-repository ecosystem smoke matrix.
- Required framework verification for the release-candidate PR.
- Published `v0.2.2` tag and GitHub release.
- Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.2`.
- Published `v0.2.1` tag and prerelease.
- Workspace-template `@v0.2.2` pin update and demo/provider fake smoke
  regression.
- Workspace-template provider setup docs and public-only provider preview
  smoke for the `v0.2.2` path.
- Public KB `@v0.2.2` CI pin update, validation, gate, PR-checklist, and
  repository-local policy guard regression.
- Public KB source-note/backlog refresh and one draft-only foundation
  tightening.
- A post-`v0.2.0` rollback audit that identified no code or KB revert scope,
  but did identify MCP-first roadmap language that needed rewrite.

The 2026-06-14 pre-tag audit verified that the package metadata and runtime
version report `0.2.2`, release docs avoid production overclaims, provider
transport remains default-off, CI/default tests avoid real provider calls, and
the default ecosystem matrix counts network rows as skipped rather than pass.
The public `v0.2.2` tag and release are published. Downstream repositories that
need the `v0.2.2` provider-transport/workflow-hardening baseline may still pin
to `v0.2.2`.

## Completed Release Focus: v0.2.3 Verification Evidence Hardening

The completed durable `v0.2.3` plan is
[`docs/CODEX_DEVELOPMENT_PLAN_V5.md`](CODEX_DEVELOPMENT_PLAN_V5.md), with ADR
0022 recording the architecture decision. `v0.2.3` focuses on
verification/evidence hardening: normalized verifier evidence, SAT/SMT/Lean
optional backend ergonomics, failure/counterexample evidence workflow,
promotion-readiness reporting, and three-repo eval/smoke coverage. It does not
expand provider/MCP authority, make real provider calls default-on, weaken
human review, or treat Lean `#check` as informal/formal semantic alignment.

The verifier evidence status audit, verifier evidence record v1, read-only
promotion-readiness reporting, SAT result-depth fixtures, SMT result-depth
fixtures, Lean external reference ergonomics, and typed counterexample
candidate records are complete. Failure-preserving review-request generation
is also implemented through `cosheaf review request-from-bundle`, which writes
or previews draft informational review requests from WorkerBundle review-only
fields without granting accepted-write authority, making review decisions, or
treating candidate counterexamples as accepted refutations. The v0.2.3
three-repository readiness matrix now includes verifier-evidence eval,
workspace verifier-evidence demo, public KB verifier-policy self-test, and
optional verifier availability coverage without adding provider or MCP
authority.

The v0.2.3 release readiness audit, release-candidate PR, maintainer release
action, release smoke from `@v0.2.3`, and downstream workspace/public KB pin
updates are complete. The release answers the readiness questions for verifier
evidence stability, optional SAT/SMT/Lean testing without mandatory tools,
skipped-not-pass enforcement, counterexample candidate boundaries, read-only
promotion readiness, workspace/public KB compatibility, and open issue/PR
state.

This completed plan is not an active queue for further v0.2.3 work. Future
runtime expansion, provider work, release work, or KB growth should start from
a new issue-scoped plan and preserve the same review, gate, public/private,
and skipped-not-pass boundaries.

## Completed Release Focus: v0.2.4 Artifact Failure Memory

The post-v0.2.3 state audit is tracked in
[`docs/POST_V023_STATE_AUDIT.md`](POST_V023_STATE_AUDIT.md). It identified
that WorkerBundle v2, draft review requests, verifier evidence evals,
failure/counterexample evals, and promotion-readiness reports already preserved
failure and counterexample context before durable artifact-level failure
memory existed.

The completed `v0.2.4` plan is
[`docs/CODEX_DEVELOPMENT_PLAN_V6.md`](CODEX_DEVELOPMENT_PLAN_V6.md), with ADR
0023 recording the artifact failure-memory architecture decision. The completed
line added Artifact Failure Memory + Attempt Traceability through small
issue-scoped PRs:

- optional `failure_log` schema and model support;
- read-only and controlled draft/pre-accepted failure-log CLI surfaces;
- WorkerBundle failed-attempt planning and controlled append bridges without
  granting authority;
- failure-memory surfacing in artifact cards, memory search, context packs,
  and promotion-readiness reports without treating it as proof, verifier
  success, human review, checked refutation, or promotion evidence;
- workspace-template demonstration and public KB policy surfaces; and
- security regression and deterministic eval coverage for retrieval,
  public/private scope, authority, and candidate-counterexample boundaries.

The v0.2.4 readiness audit, release-candidate packaging, tag publication,
GitHub release, release smoke from `@v0.2.4`, and downstream workspace/public
KB pin updates are tracked in
[`docs/releases/v0.2.4.md`](releases/v0.2.4.md). The V6 completion/code-surface
audit is tracked in
[`docs/POST_V024_V6_COMPLETION_AUDIT.md`](POST_V024_V6_COMPLETION_AUDIT.md).

Future work building on this completed focus must not make failure memory
authoritative by itself. It must not change accepted-promotion semantics, add
default real provider calls, make MCP primary, leak private failure content
into public-only context, or mass-update accepted public KB artifacts.

## v0.2.1 Prerelease Baseline

The `v0.2.1` prerelease packages the CLI-first agent-access and hosted
provider gateway surfaces that landed after the `v0.2.0` local-MVP tag. It is a
pin-able framework version for coding-agent workflows, deterministic fake
provider runs, and explicit provider-worker orchestration.

Completed `v0.2.1` work included:

- Package metadata and release notes for `v0.2.1`.
- Stable JSON/error contracts for core agent-facing CLI commands.
- Controlled draft/proposal/bundle/source-note/review-request CLI write
  surfaces.
- CLI operator workflow documentation and optional operator Skill package.
- Provider gateway design, fake provider path, and OpenAI-compatible mocked
  transport boundary.
- Provider CLI commands for list, config-check, preview-send, and fake-run.
- Role-specific hosted worker service over fake or mocked provider calls.
- Internal orchestrator dispatch to hosted workers when explicitly configured.
- Agent-access security regression coverage and agent workflow evaluation
  suite.
- Required framework verification for the release-candidate PR.
- Published `v0.2.1` tag and prerelease.
- Workspace-template `@v0.2.1` pin update and demo/provider fake smoke
  regression.
- Public KB `@v0.2.1` CI pin update, validation, gate, PR-checklist, and
  repository-local policy guard regression.
- A post-`v0.2.0` rollback audit that identified no code or KB revert scope,
  but did identify MCP-first roadmap language that needed rewrite.

## Completed Release Focus: v0.2.2 Provider Transport + Agent Workflow Hardening

The completed release focus after the prerelease and downstream compatibility checks is
tracked in
[`docs/CODEX_DEVELOPMENT_PLAN_V4.md`](CODEX_DEVELOPMENT_PLAN_V4.md) and
ADR 0020. The target is `v0.2.2 Provider Transport + Agent Workflow
Hardening`. The release notes are tracked in
[`docs/releases/v0.2.2.md`](releases/v0.2.2.md); they record the conservative
scope and the required verification ladder.

This still does not mean turning the project into a production hosted
multi-agent platform. It means improving the controlled agent-facing access
layer across the framework package, workspace template, and public KB:

- CLI is the primary agent interface for coding agents.
- CLI output for agent-facing commands should remain stable, structured, and
  machine-readable where needed.
- The service layer is the shared implementation boundary for CLI, hosted
  provider workers, internal orchestrator code, and optional MCP.
- Hosted model API/provider support remains explicit, default-off, and
  implemented behind configuration, consent, policy scope, fake or mocked
  tests, and no-real-API-in-CI rules.
- Local-only execution remains fallback, offline, and CI/testing mode. It is
  not the permanent product boundary.
- External agents can operate Cosheaf through CLI first.
- The internal orchestrator may call hosted API workers only when policy,
  configuration, consent, and context-sending rules permit.
- MCP is an optional adapter for assistants that need resources/tools rather
  than shell access. It is not required for ordinary CLI-first work.
- V9 has reopened a narrow controlled-write MCP scope for draft, review-context,
  and runtime outputs only. It still does not allow accepted writes, promotion,
  human-review creation, verifier-result mutation, arbitrary shell, or hosted
  provider calls.
- Skill is an optional operator runbook, not a source of truth and not an
  authority expansion.

Real API calls are planned by design, but they must not run in CI. CI and
default tests must use fake or mocked providers. Missing credentials or
unavailable optional tools must be reported as unavailable or skipped, never as
pass.

ADR 0015 records the earlier CLI-first direction change. ADR 0020 records the
post-`v0.2.1` provider/workflow hardening line. ADR 0021 records the real
OpenAI-compatible HTTP transport boundary and threat model. Runtime
implementation has begun with an optional stdlib HTTP transport object that
follows that default-off, explicit-consent, no-real-provider-in-CI boundary.
The provider `real-run` CLI now exists as a deliberately hard-to-trigger path
with inline preview, confirmation, network, endpoint/key, and redacted-log
checks. Hosted worker CLI commands remain separate future work.
WorkerBundle v2 now preserves assumptions, uncertainty, failed attempts,
candidate counterexamples, verification requests, dependency questions, risk
flags, and next steps as review-only reducer warnings; candidate
counterexamples are not accepted refutations and verification requests are not
verifier results.
Role contracts now request those structures explicitly: reasoner separates
conjectures/proof ideas/assumptions, verifier separates concerns from tool
results, counterexampleer separates candidate from verified counterexamples,
formalizer separates symbol resolution from semantic-alignment questions, and
librarian summaries must not invent claims.
Malformed WorkerBundle provider output now stays typed as
`provider_output_validation_failed`; the gateway can perform one logged
schema-reminder retry when configured, without coercing malformed output into
draft or accepted knowledge.
Provider context-send previews now have a tested policy matrix: `public`
policy mode previews public scope only, private scope requires
`private_research` plus explicit consent, workspace/framework scope cards are
excluded from provider previews, and previews stay metadata-only.

## Completed Baseline

Completed framework scaffold pieces include:

- Typed artifact models and initial schemas.
- Filesystem-backed artifact loading and deterministic YAML writing.
- Repository validation CLI.
- Artifact creation, lifecycle movement, and controlled accepted-artifact
  promotion workflow.
- Workspace-aware readonly public KB plus writable private KB root loading.
- Dependency graph and deterministic index rebuild outputs.
- Read-only SQLite query API over rebuilt index output, including artifact,
  status, type, domain, dependency, reverse-dependency, formalization, and
  formal-policy queries through `ArtifactIndexQuery`.
- Gatekeeper reports with machine-readable JSON and human-readable Markdown.
- Local G8 PR checklist gate for explicit PR body markdown files.
- G9 accepted-public source metadata gate.
- G10 Formal Link Gate for formal-link metadata and verifier-result
  consistency.
- Ranked context-pack generation for issue-scoped agent work.
- Deterministic artifact-card retrieval, lexical and SQLite FTS/BM25 search,
  memory graph/PageRank, Personalized PageRank, and context-pack v2
  integration.
- Local task, worker contract, orchestrator state-machine contract,
  deterministic planner, worker-bundle v2 reducer, local worker runner, and
  local-only orchestrator dry-run.
- Provider-neutral model interface with deterministic fake-provider tests.
- Optional stdlib OpenAI-compatible HTTP transport object for explicitly
  configured and injected real-provider calls, tested with local fixtures only.
- Explicit provider `real-run` CLI path that is default-off, requires inline
  context preview, send confirmation, explicit network permission,
  endpoint/API-key environment configuration, and writes redacted runtime logs.
- WorkerBundle v2 failure/counterexample preservation fields that remain
  backward-compatible with existing bundles and reducer-only.
- Role prompt/output contracts for structured uncertainty, failures, verifier
  requests, candidate counterexamples, formal-link limitations, and
  no-claim-invention librarian summaries.
- Provider malformed-output recovery for WorkerBundle payloads with logged
  output-validation retry metadata.
- Context-send policy matrix coverage for provider previews, including stable
  denial error codes and metadata-only preview boundaries.
- Verifier adapter protocol, Python checker adapter, minimal optional SAT
  DIMACS adapter, minimal optional SMT-LIB adapter, minimal optional plain Lean
  adapter, and optional external Lean library reference checker.
- Optional MarkItDown local source-ingestion staging adapter.
- Optional Headroom experiment scaffold and CodeGraph developer-tool probe.
- Retrieval/context evaluation harnesses, structured run logging, and optional
  OpenTelemetry run-log export scaffolding.
- Read-only MCP stdio surface. This exists as optional adapter work and must
  not be treated as the primary agent path or a release blocker. The
  post-`v0.2.1` optional-adapter review keeps this surface read-only and does
  not add controlled-write MCP or provider MCP tools.
- Graph-theory, SAT/CNF, and formal-link pilot workflows that remain draft or
  example material and do not bypass review or promotion.
- GitHub Actions CI and collaboration templates.

## Agent Access Boundaries

Agent access must preserve existing governance:

- CLI commands are the first path for external coding agents.
- Controlled write surfaces must be explicit and limited to
  draft/proposal/bundle/task/run surfaces.
- MCP, if used, must not expose arbitrary shell, direct promotion, or
  accepted-path writes.
- Skill is an operator manual. It must not widen permissions or become a
  source of truth.
- Hosted workers may return worker bundles, typed sub-results, or draft
  proposals only.
- External agents must not directly edit accepted paths.
- Internal orchestration must not bypass reducer, validation, gates, review, or
  promotion.
- Provider calls must use explicit policy scope, timeout, cancellation, and
  audit metadata.
- Private KB context must not be sent to a provider unless the policy mode and
  operator consent explicitly allow it.
- API keys and secrets must not be committed or logged.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier or provider results are not passes.

## Formal Link Boundary

The framework now has an optional external Lean library reference checker. It
can generate a temporary Lean file with:

```lean
import <module>
#check <symbol>
```

and run either `lean <tempfile>` or configured `lake env lean <tempfile>` when
the tool is available. This support is intentionally narrow:

- Missing Lean/lake is `skipped`, not `pass`.
- A successful `#check` only means the import and symbol resolved.
- It does not fetch CSLib/mathlib, manage external library checkouts, copy Lean
  proof bodies, autoformalize natural language, or prove informal/formal
  semantic alignment.
- Alignment review remains human-reviewed metadata.

## Public KB Direction

The public KB should grow through small source-reviewed and human-reviewed PRs.
Do not resume theorem/proof-sketch expansion until backlog, source-note, and
review policy are in place for the relevant area.

Near-term public KB work should remain:

- Foundation backlog maintenance.
- Source-note convention cleanup.
- Small accepted foundation definitions with complete source metadata and
  human review.
- No mass imports.
- No private conjectures or unreviewed LLM output under accepted public paths.

Recent downstream hardening refreshed the public KB source-note/backlog policy
and tightened one draft foundation artifact without promoting it to accepted
knowledge.

## Next Named Milestones

### v0.2.0 Local MVP

`v0.2.0` is the bounded local-MVP milestone after release hardening. It turns
the existing local, deterministic surfaces into a coherent pin-able framework
version without changing the knowledge-governance boundary.

Out of scope for `v0.2.0`:

- Production hosted multi-agent runtime.
- Automatic theorem proving.
- Automatic accepted-artifact promotion.
- Web UI.
- Multi-user authentication or permissions.
- Full CSLib/mathlib ingestion, vendoring, or semantic-alignment automation.

ADR 0014 records this scope decision.

### v0.2.1 CLI Agent Access + Hosted Provider Gateway

`v0.2.1` packages the access layer around the existing local-MVP substrate:

- Fixed CLI-first execution plan installed as current project memory.
- Workspace-template pin audit against the `v0.2.0` baseline.
- Shared service layer used by CLI first, then hosted workers and optional MCP.
- Stable JSON/error contracts for agent-facing CLI commands.
- Controlled draft/proposal/bundle/source-note/review-request write CLI
  surfaces.
- CLI operator workflow docs and workspace demo path.
- Provider gateway design, fake/mocked test surface, and OpenAI-compatible
  mocked transport boundary.
- Provider CLI commands for inspection, config checks, preview, and fake runs.
- Hosted worker contracts and execution service that produce validated worker
  bundles or typed review-only sub-results, not accepted knowledge.
- Internal orchestrator dispatch to hosted workers only when explicitly
  configured.
- Skill/operator package that instructs agents how to use CLI first and MCP as
  optional adapter.
- Optional read-only MCP adapter retained as nonblocking compatibility surface.

Out of scope for `v0.2.1` unless separately approved:

- Default-on hosted API calls.
- Default real hosted provider calls.
- CI that requires network access, API keys, or real provider calls.
- Direct accepted writes by CLI draft tools, MCP tools, hosted workers,
  external agents, or the internal orchestrator.
- Replacing human review with AI review.
- Web UI, SaaS behavior, multi-user auth, or production operations.

### Verification Depth

- Improve external Lean library reference checking ergonomics without vendoring
  CSLib or mathlib.
- Expand SAT backend coverage beyond the minimal optional DIMACS invocation
  path.
- Expand SMT backend coverage beyond the minimal optional SMT-LIB invocation
  path.
- Expand Lean support beyond the minimal optional plain-file and
  external-reference invocation paths.
- Keep all external formal tools optional; unavailable tools must produce
  skipped verifier results.

### Query, Review, And Showcase Ergonomics

- Improve CLI-facing query ergonomics on top of existing index/query APIs when
  users need non-Python inspection flows.
- Improve release/demo smoke coverage across all three repositories.
- Keep README/showcase docs conservative and newcomer-friendly.

## Non-Goals

TCS-Cosheaf does not aim to provide:

- A production hosted multi-agent system by default.
- A web UI.
- Model training.
- Automatic theorem proving.
- Full Lean autoformalization.
- CSLib/mathlib replacement or vendoring.
- Automatic informal/formal semantic alignment checking.
- Automatic accepted-artifact promotion.
- Multi-user permission system.
- Claims about project adoption, production usage, users, stars, or downloads.
