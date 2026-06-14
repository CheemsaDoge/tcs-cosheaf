# TCS-Cosheaf Development Plan v6

Status: completed after the published `v0.2.4` release closeout

Target:

```text
v0.2.4 Artifact Failure Memory + Attempt Traceability
```

This completed plan followed the published `v0.2.3` Verification Evidence Hardening
release, the post-v0.2.3 documentation closeout, and
[`docs/POST_V023_STATE_AUDIT.md`](POST_V023_STATE_AUDIT.md). The audit
confirmed that WorkerBundle v2, draft review requests, verifier evidence evals,
failure/counterexample evals, and read-only promotion-readiness reports already
preserve failure and counterexample context, but durable artifact records do
not yet expose an artifact-level `failure_log` at the start of V6.

The goal of `v0.2.4` is to make failed attempts, dead directions, blocked
approaches, and lessons learned visible on long-lived artifact records and in
retrieval/context surfaces without turning failure memory into proof, verifier
success, human review, checked refutation, or promotion evidence.

## Baseline

At the start of this plan:

- `tcs-cosheaf` package metadata and `cosheaf.__version__` are `0.2.3`.
- The `v0.2.3` tag and GitHub release are published.
- `tcs-cosheaf-workspace-template` active workflows pin or default to
  `tcs-cosheaf@v0.2.3`.
- `tcs-kb-public` CI installs `tcs-cosheaf@v0.2.3`.
- `docs/CODEX_DEVELOPMENT_PLAN_V5.md` is completed historical context.
- WorkerBundle v2 already preserves `failed_attempts`, `uncertainty`,
  `verification_requests`, legacy `counterexamples`, typed
  `counterexample_candidates`, dependency questions, risk flags, and next
  steps.
- `cosheaf review request-from-bundle` can preserve WorkerBundle failure and
  counterexample evidence in draft informational review requests.
- Base artifact records currently have `evidence`, `sources`,
  `formalizations`, `alignment`, `verification_policy`, `review`, and `risk`,
  but no structured artifact-level `failure_log`.

## Non-Negotiable Invariants

Knowledge lifecycle:

- Accepted artifacts require validation, gates, review where policy requires
  it, and explicit promotion.
- Worker/provider/verifier output must not write directly to `kb/accepted/`.
- AI/provider review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier, provider, SAT, SMT, or Lean results are not passes.
- Public KB accepted artifacts require complete source metadata and human
  review.
- Public KB artifacts must not depend on private KB artifacts.
- Private KB artifacts may depend on public accepted artifacts.

Failure memory:

- `failure_log` is research memory, not proof, not verifier success, not human
  review, and not accepted-status evidence by itself.
- A failed attempt can explain why a direction failed, but it must not refute a
  claim unless a separate checked counterexample or reviewed refutation path
  exists.
- Agent/provider-generated failure entries must identify their origin and must
  not claim human review.
- Failure records may be useful for retrieval and review, but they must not
  bypass validation, gates, reviewer judgment, or promotion.
- Existing artifacts must remain valid. The first schema change must be
  backward compatible: `failure_log` is optional with default empty list.

Provider, MCP, and tool boundary:

- Real provider calls remain default-off and require explicit configuration,
  credentials, policy scope, context preview, network permission, and operator
  consent.
- CI and default tests must not make live provider calls or require API keys.
- Provider output may become WorkerBundle, draft proposal, draft artifact
  input, or review context only.
- MCP remains optional and read-only unless a separate maintainer-approved
  issue explicitly changes that scope.
- No new default hosted-provider, MCP, SAT, SMT, Lean, lake, CSLib, mathlib, or
  network dependency may be introduced.

Branch and PR naming:

- Do not use `codex/` or `codex-` prefixes in issue names, branch names, or PR
  titles.
- Keep each task to one issue, one branch, one PR, and one reviewable
  increment.

## Phase A: Post-v0.2.3 State Audit And Plan Landing

### A.1 Post-v0.2.3 State Audit

Status: complete in [`docs/POST_V023_STATE_AUDIT.md`](POST_V023_STATE_AUDIT.md).

The audit confirmed:

- `BaseArtifact` has no `failure_log` field.
- `schemas/artifact.schema.json` has no `failure_log` property.
- Existing failure memory is preserved in WorkerBundle, review-request,
  verifier evidence eval, failure/counterexample eval, and readiness surfaces.
- Three-repository pins are aligned on `v0.2.3`.

### A.2 Land V6 Plan And ADR

Status: this document and ADR 0023.

This task records the active `v0.2.4` plan and the architecture decision for
artifact-level failure memory. It is documentation only: it does not implement
schemas, models, CLI commands, retrieval, context-pack rendering,
promotion-readiness reporting, workspace-template demos, or public KB policy
changes.

## Phase B: Artifact Failure Schema Design

### B.1 Artifact Failure Log Schema ADR

Define the artifact-level `failure_log` schema before runtime changes.

Proposed fields:

- `failure_id`
- `attempted_at`
- `recorded_by`
- `origin`
- `attempt_kind`
- `target`
- `direction`
- `summary`
- `failed_because`
- `evidence_paths`
- `related_verifier_results`
- `related_counterexample_candidates`
- `next_possible_directions`
- `status`
- `limitations`

The design must explain authority boundaries for every field, distinguish
artifact `failure_log` from WorkerBundle `failed_attempts`, and state how public
KB accepted artifacts may carry failure memory only through ordinary
source/review/promotion policy.

### B.2 Artifact Failure Log Model And Schema

Implement optional artifact-level `failure_log` in Pydantic models and JSON
Schema.

Requirements:

- `failure_log` is optional and defaults to an empty list.
- Existing artifacts without `failure_log` continue to validate.
- Each entry requires `failure_id`, `attempted_at`, `origin`, `attempt_kind`,
  `direction`, `summary`, `failed_because`, `status`, and `limitations`.
- Timestamps are timezone-aware.
- Repository-local evidence paths are normalized and must not target accepted
  writes.
- `related_verifier_results` and `related_counterexample_candidates` are
  references only.

Tests must cover existing fixture compatibility, valid failure logs, invalid
timestamps, empty directions, invalid IDs, unsafe paths, and schema/model
agreement.

## Phase C: Failure Log CLI And Controlled Writes

### C.1 Artifact Failure Log Read CLI

Add read-only CLI support:

```bash
cosheaf artifact failures <artifact-id> --json
```

The command must return stable JSON, include public/private root scope metadata
where relevant, return an empty list for artifacts without `failure_log`, and
never treat failure records as proof, refutation, verifier results, human
review, or gate success.

### C.2 Artifact Failure Log Draft Write CLI

Add a narrow controlled write path:

```bash
cosheaf artifact failure add --artifact <artifact-id> --input-json <path> --json
cosheaf artifact failure add --artifact <artifact-id> --input-json <path> --dry-run --json
```

The command must support dry-run, reject accepted-path mutation, reject readonly
public roots, reject authority spoofing, update `updated_at` only on actual
writes, and report `accepted_write_performed=false`.

### C.3 Failure Log From WorkerBundle

Bridge WorkerBundle v2 `failed_attempts` and typed counterexample candidates
into artifact failure-log proposals or controlled draft writes:

```bash
cosheaf artifact failure plan-from-bundle --bundle <path> --target-artifact <artifact-id> --json
cosheaf artifact failure add-from-bundle --bundle <path> --target-artifact <artifact-id> --dry-run --json
```

WorkerBundle failures become artifact failure-log proposals or draft writes,
not accepted knowledge. Candidate counterexamples remain candidate evidence.
Agent/provider origin must be preserved.

## Phase D: Retrieval, Context, And Review Surfacing

### D.1 Failure Log Memory Index

Make failure logs visible to memory search and artifact cards so agents avoid
repeating known failed directions.

Requirements:

- Failure-log text is labeled as failed or unresolved attempt memory.
- Retrieval preserves public/private root scope.
- Failure logs do not boost an artifact into accepted truth ranking by
  themselves.
- Public-only context excludes private failure logs.

### D.2 Context Pack Failure Sections

Add explicit context-pack sections for known failed directions:

```text
Known failed directions
- artifact id
- direction
- failed_because
- status
- next_possible_directions
- source/origin label
```

The section must not render any failure entry as proof, refutation, verifier
pass, or human review.

### D.3 Promotion Readiness Failure Memory

Update read-only promotion-readiness reports to mention unresolved failure-log
entries without making them automatic blockers by default.

Failure logs should be warnings or evidence notes unless an existing gate or
verification policy already makes the underlying issue blocking.
`accepted_write_performed=false` must remain true for readiness reports.

## Phase E: Workspace And Public KB Demonstrations

### E.1 Workspace Failure Log Demo

Demonstrate artifact-level failure memory in the user-facing workspace without
accepted writes, promotion, human-review spoofing, real provider calls, network
requirements, or API keys. Demo output must remain under ignored runtime paths.

### E.2 Public KB Failure Log Policy

Update public KB policy so failure logs can be used safely for reviewed public
knowledge without encouraging unreviewed failure dumping. Failure logs in
accepted public artifacts require ordinary source/review discipline.

## Phase F: Security, Evaluation, And Regression

### F.1 Artifact Failure Log Security Regression

Add negative tests for failure-log misuse:

- trying to mark human review;
- trying to mark verifier pass;
- pointing to accepted direct-write paths;
- leaking private content in public-only context;
- claiming a candidate counterexample as checked without evidence;
- provider/agent-generated failure trying to promote accepted status.

### F.2 Artifact Failure Log Eval Suite

Add deterministic eval coverage for failure memory retrieval and governance:

- `failure_retrieval_recall`
- `repeat_failed_direction_rate`
- `failure_scope_leak_count`
- `failure_authority_violation_count`
- `candidate_counterexample_mislabel_count`

The eval must use deterministic fixtures only: no hosted provider call, no
accepted write, and no MCP expansion.

Implementation status as of 2026-06-15: complete through the Python-level
`cosheaf.evals.artifact_failure_memory` harness and
`evals/artifact_failure_memory/cases.yaml`. The later G.1 readiness audit,
G.2 release-candidate task, and G.3 publication closeout are complete.

## Phase G: v0.2.4 Release Readiness

### G.1 v0.2.4 Release Readiness Audit

Decide whether `v0.2.4` is ready to enter release-candidate work. The audit
must answer:

1. Is artifact-level `failure_log` implemented and backward compatible?
2. Do existing artifacts still validate?
3. Are failure entries clearly non-authoritative?
4. Do context packs surface failed directions without leaking private data?
5. Does promotion readiness mention failures without changing promotion rules?
6. Are WorkerBundle and review-request bridges aligned?
7. Are workspace and public KB policy surfaces updated?
8. Are open issues/PRs empty or intentionally deferred?

Implementation status as of 2026-06-15: the readiness-audit draft is recorded
in `docs/releases/v0.2.4.md`. The audit PR and required checks passed, and the
later G.2 release-candidate and G.3 publication closeout tasks are complete.

### G.2 v0.2.4 Release Candidate

Prepare `v0.2.4` as the Artifact Failure Memory + Attempt Traceability release
candidate after the readiness audit.

Release-candidate work may update version metadata and release docs only. It
must not add runtime behavior beyond release metadata, and it must not claim
production readiness, automatic theorem proving, accepted-promotion
automation, or AI-as-human-review.

Implementation status as of 2026-06-15: the release-candidate branch updates
package metadata and `cosheaf.__version__` to `0.2.4` and converts
`docs/releases/v0.2.4.md` into release-candidate notes. Tag publication,
GitHub release creation, release smoke, and downstream pin updates were
completed later by G.3 after the release-candidate PR passed and merged.

### G.3 v0.2.4 Publication Closeout

Publish the reviewed release after the release-candidate PR merges cleanly and
main is re-synced.

Publication-closeout work may update status documentation only. It must not add
runtime behavior, change schema, change verifier or promotion semantics, expand
provider/MCP authority, write accepted knowledge, mark human review, or claim
production readiness.

Implementation status as of 2026-06-15: the annotated `v0.2.4` tag and GitHub
release are published, release smoke from `@v0.2.4` passed, workspace-template
active pins moved to `@v0.2.4`, public KB CI moved to `@v0.2.4`, and this plan
is complete. Future work should start from a post-v0.2.4 state audit or a
separate maintainer-approved plan.

## Per-PR Requirements

Each PR summary must include:

```text
Goal:
Scope:
Files changed:
Tests run:
Commands unavailable:
Invariants checked:
Security/privacy impact:
Known limitations:
Follow-up tasks:
```

Every PR should run or honestly report:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

Additional checks for schema/interface tasks:

- `python -m pytest tests/test_schema_files_exist.py`
- relevant CLI JSON tests
- relevant security/eval tests
- stale documentation scan for older current-plan wording

## Stop Rules

Stop and request maintainer decision if a task requires:

- making `failure_log` required for all existing artifacts;
- changing accepted promotion semantics;
- allowing agent/provider/MCP/verifier output to write `kb/accepted/` directly;
- treating failure memory as proof, verifier result, checked counterexample,
  human review, or accepted refutation;
- sending private failure-log content to a provider without explicit policy,
  preview, network permission, and consent;
- adding real provider calls to CI/default tests;
- making MCP primary or adding controlled-write/provider MCP tools;
- changing public/private dependency policy;
- mass-updating public KB accepted artifacts without a separate review plan.
