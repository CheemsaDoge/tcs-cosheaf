# Current Milestone

## Milestone

`v0.2.4` Artifact Failure Memory + Attempt Traceability implementation.

## Goal

Implement the active V6 plan for `v0.2.4` Artifact Failure Memory + Attempt
Traceability after the post-`v0.2.3` state audit and plan landing. The line
targets durable artifact-level failure memory for failed attempts, dead
directions, blocked approaches, and lessons learned while preserving all
review, verifier, gate, promotion, public/private, provider, and MCP
boundaries.

This milestone does not claim production hosted multi-agent readiness. It does
not add a web UI, multi-user permissions, automatic theorem proving,
automatic Lean autoformalization, automatic accepted promotion,
AI-as-human-review, provider/MCP authority expansion, or automatic
informal/formal semantic alignment.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.2.3`.
- Remote tags `v0.1.1`, `v0.2.0`, `v0.2.1`, `v0.2.2`, and `v0.2.3` exist.
- The GitHub release `v0.2.3 Verification Evidence Hardening` is published and
  is not a production-readiness claim.
- The GitHub release `v0.2.2 Provider Transport + Agent Workflow Hardening`
  is published and is not a production-readiness claim.
- `tcs-cosheaf-workspace-template` pins active demo, Makefile, CLI-agent,
  provider-preview, fake-provider smoke, and verifier-evidence demo paths to
  `@v0.2.3`.
- `tcs-kb-public` CI installs `tcs-cosheaf` from `@v0.2.3`.
- `docs/CODEX_DEVELOPMENT_PLAN_V4.md` is historical/completed after the
  `v0.2.2` release closeout.
- `docs/CODEX_DEVELOPMENT_PLAN_V5.md` is the completed durable record of the
  v0.2.3 verification-evidence hardening plan.
- ADR 0022 records the `v0.2.3` Verification Evidence Hardening decision.
- `docs/POST_V023_STATE_AUDIT.md` records the current artifact failure-memory
  gap after v0.2.3.
- `docs/CODEX_DEVELOPMENT_PLAN_V6.md` is the active durable plan for the
  `v0.2.4` artifact failure-memory line.
- ADR 0023 records the artifact failure-memory decision and authority
  boundaries.
- Artifact-level `failure_log` is now implemented as optional
  `BaseArtifact`/`schemas/artifact.schema.json` metadata with default empty
  list behavior. It remains non-authoritative research memory.
- `cosheaf artifact failures <artifact-id> --json` provides read-only
  failure-log inspection with artifact path, root scope metadata, failure
  entries, and an explicit non-authority notice.
- `cosheaf artifact failure add --artifact <artifact-id> --input-json <path>
  --json` provides controlled append-only draft/pre-accepted failure-log writes
  with dry-run, accepted-path refusal, readonly-root refusal, and
  authority-spoofing rejection.
- `cosheaf artifact failure plan-from-bundle --bundle <path> --target-artifact
  <artifact-id> --json` and `cosheaf artifact failure add-from-bundle` bridge
  WorkerBundle v2 `failed_attempts` into proposed or controlled
  `failure_log` entries without granting proof, review, verifier, checked
  counterexample, accepted-status, or promotion authority.
- Artifact-level `failure_log` memory is visible in `ArtifactCard` metadata
  through `failure_count` and `recent_failure_directions`. `cosheaf memory
  search` indexes recent failure directions with explicit non-authority
  warnings, and context packs include compact failure summaries for visible
  cards while preserving public/private filtering.
- Context packs now render explicit `Known Failed Directions` sections in
  `CONTEXT.md` and `KNOWN_FAILURES.md` when visible artifacts carry
  `failure_log` entries. `RETRIEVAL_AUDIT.json` exposes the same structured
  entries in `failure_memory` and counts them in
  `context_payload.failure_entry_count`.
- Promotion-readiness reports now surface unresolved artifact failure memory as
  `unresolved_failure_memory` warning reasons. These warnings are distinct
  from verifier failures and are not promotion blockers by themselves.
- `docs/VERIFIER_EVIDENCE_AUDIT.md` records the current verifier adapter,
  result-state, logging, gate, promotion, Lean `#check`, and sidecar boundary.
- `tcs-cosheaf` is the framework package for CLI, schema, validation, gates,
  index/query, context packs, local task/orchestrator dry-runs, service-layer
  entry points, provider gateway, hosted-worker dispatch, evaluation,
  verifier adapters, and observability scaffolding.
- `tcs-kb-public` is the reusable public KB and must stay public, citable,
  source-reviewed, and human-reviewed before accepted knowledge is added.
- `tcs-cosheaf-workspace-template` is the user-facing entry point with readonly
  public KB plus writable private KB overlay.

## v0.2.3 Scope

`v0.2.3` is Verification Evidence Hardening. It should deepen reviewable
evidence around optional verifier and failure workflows:

- Verifier evidence model and normalized result taxonomy.
- Explicit distinction between `verifier_request`, `verifier_result`,
  `candidate_counterexample`, and `checked_counterexample`.
- SAT optional backend ergonomics, command metadata, timeout handling, and
  unavailable-tool skips.
- SMT optional backend ergonomics, `sat`/`unsat`/`unknown` handling, command
  metadata, timeout handling, and unavailable-tool skips.
- Plain Lean and external Lean library reference checker ergonomics, with
  `#check` documented as symbol/import resolution only.
- Failure and counterexample evidence workflows that preserve failed attempts
  and candidates without treating them as proof or checked refutation.
- Promotion-readiness reporting that explains missing evidence without
  bypassing validation, gates, review, verifier requirements, or promotion.
- Three-repository readiness checks for framework, workspace-template, and
  public KB.

## Explicit Boundaries

- CLI remains the first agent interface and the human/CI oracle.
- Real provider calls remain default-off and require explicit configuration,
  credentials, policy scope, context preview, network permission, and operator
  consent.
- No real provider calls run in CI or default tests.
- `v0.2.3` does not expand provider authority, add provider MCP tools, add
  controlled-write MCP, or make MCP the primary path.
- Worker/provider output may become draft/proposal/bundle/review context only.
- A `verifier_request` is not a `verifier_result`.
- A `candidate_counterexample` is not a `checked_counterexample`.
- Accepted knowledge still requires validation, gates, human review where
  policy requires it, verifier evidence where applicable, and explicit
  promotion.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier, provider, SAT, SMT, or Lean results are not passes.
- Public KB accepted artifacts still require complete source metadata and
  human review.
- Formal links remain metadata unless a checker actually records a result.
- A successful Lean `#check` remains symbol/import resolution, not
  informal/formal semantic alignment.

## Current Operating State

The active task line is implementing V6 in focused issue/branch/PR increments.
The plan and ADR have landed, optional artifact `failure_log` model/schema
support is implemented, read-only failure-log CLI inspection is implemented,
controlled draft/pre-accepted failure-log append support is implemented, and
WorkerBundle-to-failure-log planning/controlled append support is implemented.
Failure-log memory indexing is implemented for artifact cards, memory search,
compact context-pack card summaries, and explicit context-pack failure
sections. Promotion-readiness failure-memory warning reporting is implemented.
New work should continue from workspace/public-KB failure-log demonstration and
policy surfaces, while avoiding runtime authority expansion, default real
provider calls, generated review-as-human-review, accepted writes, artifact
promotion bypasses, and treating skipped verifier results as passes.

## Recently Completed Tasks

D.3 Lean external reference ergonomics improved optional external Lean
`#check` debugging without adding a mandatory Lean or lake dependency. The
task added fake-backend tests for missing import and missing symbol stderr log
preservation, clearer manifest diagnostics for unknown `library_ref` values,
and documentation that a successful external Lean `#check` means only import
and symbol resolution.

The task does not fetch CSLib, mathlib, or any Lean library, does not vendor
Lean code, does not claim theorem proving, does not claim informal/formal
semantic alignment, does not write accepted knowledge, and keeps missing
Lean/lake as `skipped`, not `pass`.

E.1 typed counterexample candidate records added optional WorkerBundle v2
`counterexample_candidates` with candidate ID, optional target claim,
construction summary, evidence paths, verifier-request IDs, status, and
limitations. E.1 keeps legacy string `counterexamples` backward-compatible.
Reducers preserve typed candidates as review warnings and never convert them
into accepted refutations, verifier results, human review, or promotion
authority. `checked_false` and `checked_true` candidate statuses require
evidence paths in the bundle schema, but they still do not change accepted
artifact status.

E.2 failure-preserving review request generation added
`cosheaf review request-from-bundle --bundle <path>`. It validates WorkerBundle
v2 manifests and writes or previews draft informational review requests under
`reviews/requests/`, preserving assumptions, uncertainty, failed attempts,
verifier requests, legacy and typed counterexample candidates, dependency
questions, risk flags, next steps, confidence, and candidate limitations as
findings. It rejects accepted-path and human-reviewed-authority spoofing before
writing anything and never creates verifier results, human review, accepted
knowledge, or promotion authority.

G.1 verifier evidence eval suite added `cosheaf.evals.verifier_evidence` and
`evals/verifier_evidence/cases.yaml`. The deterministic Python-level harness
scores pass/failed/skipped verifier evidence readiness boundaries, typed
candidate counterexample review-only behavior, and Lean external `#check`
symbol-resolution-only limitations. It uses fake evidence records and typed
fixtures only: no SAT, SMT, Lean, lake, hosted provider, MCP, accepted write,
human review, or promotion is performed.

G.2 three-repository readiness matrix extends `scripts/ecosystem_smoke.py
--matrix` with framework verifier-evidence eval smoke, an optional verifier
availability probe, workspace-template verifier-evidence demo coverage, and a
separate public KB verifier-policy self-test. The matrix keeps network rows
opt-in, counts optional verifier absence as skipped rather than pass, and
continues to identify the failing repository and command for failures.

G.3 v0.2.3 release readiness audit added `docs/releases/v0.2.3.md` as a
readiness-audit draft and recorded that main could enter the release-candidate
task. The audit kept package metadata at `0.2.2`, created no tag, changed no
runtime behavior, and answered verifier evidence, optional-tool,
skipped-not-pass, counterexample, promotion-readiness, workspace/public KB, and open
issue/PR readiness questions.

G.4 v0.2.3 release candidate updated package metadata and release notes to
`0.2.3`, then the maintainer release action published the annotated `v0.2.3`
tag and GitHub release after main was re-synced. Release smoke from
`git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.3` passed, and
downstream workspace-template plus public KB active pins were updated to
`v0.2.3` through focused PRs.

## Next Focus

After promotion-readiness failure-memory reporting lands, proceed to workspace
failure-log demonstration and public-KB failure-log policy. Retrieval,
context-pack, readiness, workspace, and policy work must keep failure memory
labeled as failed or unresolved attempt memory, preserve public/private scope,
and avoid promoting failure memory into proof, verifier success, human review,
checked counterexample evidence, accepted status, or promotion evidence by
itself.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
