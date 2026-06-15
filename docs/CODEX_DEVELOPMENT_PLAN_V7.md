# TCS-Cosheaf Development Plan V7

Status: completed accelerated plan for the published `v0.3.0` Checked
Evidence + Research Run Loop release after the published `v0.2.4` Artifact
Failure Memory + Attempt Traceability release.

Target:

```text
v0.3.0 Checked Evidence + Research Run Loop
```

One-line direction:

```text
Cosheaf should turn external-agent research into auditable evidence: separate
candidate counterexamples from checked counterexample evidence, record complete
reproducible research runs, and let Codex-style operators drive the loop
through CLI/Git instead of embedding GPT/Claude as the default runtime.
```

## Versioning Decision

This line is named `v0.3.0`. The `v0.2.x` series is treated as the completed
CLI-agent, provider, evidence, and failure-memory foundation. `v0.3.0` starts
the checked-evidence research-run loop.

Near-roadmap version meaning:

```text
v0.2.x = CLI-agent/provider/evidence/failure-memory foundation
v0.3.x = checked evidence + reproducible research run loop
v0.4.x = strategy planner + research task graph
v0.5.x = deeper formal verification
v0.6.x = research memory learning + benchmark eval
v0.7.x = bounded autonomous multi-run operator
v1.0.0 = AI math collaborator MVP
```

## Acceleration Decision

The earlier V7 plan was too granular. This plan merges tightly coupled audit,
taxonomy, model, CLI, docs, tests, security, and eval work into larger
implementation boundaries while keeping the same safety rules.

Development rule:

```text
One implementation boundary = one PR.
Do not split taxonomy, model, CLI, docs, tests, and evals into separate PRs
when they are tightly coupled.
```

Removed as separate tasks:

- standalone taxonomy audit PR;
- standalone design-only PR after kickoff;
- standalone security PR when security tests belong with the feature PR;
- standalone eval PR when the eval is directly tied to the same surface;
- separate workspace/public-KB policy PRs unless framework code is already
  stable.

Added to speed useful capability:

- checked counterexample evidence model, schema, CLI, context/readiness
  surfacing, and tests in one PR;
- research-run model, schema, CLI, export, evidence report, and replay-plan
  support in one PR;
- external operator runbook plus workspace demo after framework surfaces land;
- public KB policy plus at most one draft-only example after framework
  surfaces land;
- release closeout only after the larger increments land.

## Baseline

At plan start:

- `tcs-cosheaf` package metadata and runtime version are `0.2.4`.
- The public `v0.2.4` tag and GitHub release are published.
- `tcs-cosheaf-workspace-template` pins active demos and install paths to
  `tcs-cosheaf@v0.2.4`.
- `tcs-kb-public` CI installs `tcs-cosheaf@v0.2.4`.
- V6 is complete. Artifact-level `failure_log` exists, has CLI read/write
  surfaces, is indexed in memory/context, and remains non-authoritative.
- WorkerBundle v2 already preserves `counterexample_candidates`, failed
  attempts, uncertainty, verifier requests, and review-only warnings.
- `VerifierEvidenceRecord` v1 already exists for verifier outputs.
- Structured local run logging exists, but it is not yet a full
  external-operator research-run provenance ledger.
- CLI remains the primary interface for Codex-style external agents.
- MCP remains optional adapter work and is not required for `v0.3.0`.

## Non-Negotiable Invariants

Knowledge lifecycle:

- Accepted artifacts require validation, gates, human review where policy
  requires it, source metadata for accepted public artifacts, and explicit
  promotion.
- Worker/provider/Codex/verifier output must not write directly to
  `kb/accepted/`.
- AI/provider/Codex review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier, provider, SAT, SMT, Lean, lake, optional-tool, network, or
  operator steps are not passes.
- Public KB accepted artifacts require source metadata and human review.
- Public KB artifacts must not depend on private KB artifacts.
- Private KB artifacts may depend on accepted public artifacts.

Checked evidence:

- A `candidate_counterexample` is proposed refuting evidence only.
- A `checked_counterexample_evidence` record is durable evidence that a
  specified method checked a candidate.
- A candidate cannot become checked merely because an agent, provider,
  WorkerBundle, or run record says so.
- A checked counterexample still does not automatically mark human review,
  rewrite accepted knowledge, promote artifacts, or refute artifacts by itself.
- A verifier request is not a verifier result.
- A verifier result is not human review.
- Lean `#check` remains import/symbol resolution unless a separate checker
  records stronger evidence.

Research runs:

- A research run record is provenance, not proof, human review, verifier pass,
  gate success, accepted status, or promotion evidence.
- Run records must be repository-local, deterministic, redacted, and
  reviewable.
- Run records must not store API keys, bearer tokens, full environment dumps,
  hidden reasoning, or unapproved private artifact text.
- Runtime sidecars under `.cosheaf/` remain generated outputs unless
  explicitly exported through a controlled command.

External operator:

- Codex is an external operator that calls CLI, edits files, runs tests, and
  opens PRs.
- Do not embed GPT, Claude, or any hosted model as the default Cosheaf runtime
  in this line.
- Hosted provider calls remain explicit, default-off, policy-scoped,
  previewed, consented, and excluded from CI/default tests.
- MCP remains optional and non-blocking.
- Branch, issue, and PR titles must not use `codex/` or `codex-` prefixes.

## Compressed Milestones

```text
Phase 0: Kickoff audit + plan/ADR landing
Phase 1: Checked counterexample evidence core
Phase 2: Research run record and CLI core
Phase 3: External operator workflow and demos
Phase 4: Integration, eval, and three-repo smoke
Phase 5: v0.3.0 release candidate and publication
```

## Phase 0: Kickoff Audit + Plan/ADR Landing

Task: `post-v024-v030-kickoff`

Goal: land the `v0.3.0` direction and perform only the minimum state audit
needed to start implementation.

Allowed changes:

- `docs/POST_V024_V030_KICKOFF_AUDIT.md`
- `docs/CODEX_DEVELOPMENT_PLAN_V7.md`
- `docs/ADR/0024-checked-evidence-research-run-loop.md`
- `docs/ROADMAP.md`
- `context/CURRENT_MILESTONE.md`
- `context/PROJECT_STATE.md`

Forbidden:

- No model/schema/runtime behavior changes.
- No provider or MCP behavior changes.
- No accepted KB changes.
- No version bump.

Acceptance:

- This accelerated plan replaces the slower V7 task split.
- V6 is marked completed, not active.
- The next functional task can start immediately after this PR merges.
- Required checks: `make lint`, `make typecheck`, `make test`,
  `make validate`, `make gate`, `git diff --check`.

## Phase 1: Checked Counterexample Evidence Core

Task: `checked-counterexample-evidence-core`

Goal: implement candidate-vs-checked counterexample evidence as a usable
framework feature in one PR: docs, model, schema, CLI, context/readiness
surfacing, security tests, and deterministic eval fixtures.

Required model shape:

```yaml
schema_version: 1
evidence_id: checked-counterexample.<target>.<candidate>.h<digest>
target_artifact_id: claim.example
candidate_id: candidate.example
candidate_source: worker_bundle | failure_log | artifact | manual_note | verifier
check_method: verifier_result | manual_review_reference | executable_check | proof_sketch_review | other
checked_result: checked_refutes | checked_does_not_refute | inconclusive | error | skipped
verifier_evidence_ids: []
review_record_paths: []
evidence_paths: []
created_at: <timezone-aware timestamp>
checker: <tool/person/process label>
limitations: []
```

Required CLI:

```text
cosheaf counterexample evidence validate --input-json <path> --json
cosheaf counterexample evidence show --evidence <path-or-id> --json
cosheaf counterexample evidence stage --input-json <path> --json --dry-run
cosheaf counterexample evidence stage --input-json <path> --json
```

Controlled staging path:

```text
reviews/evidence/checked-counterexamples/<evidence-id>.yaml
```

Key requirements:

- `checked_refutes` requires at least one verifier evidence ID, review record
  path, or evidence path.
- `skipped` must include limitation text saying skipped is not pass.
- All paths are repository-local.
- Staging refuses `kb/accepted/`, readonly public roots, path traversal,
  absolute paths, and authority spoofing.
- CLI output must say checked evidence is evidence for review, not human review
  or accepted refutation.
- Context and readiness reports must separate candidate evidence from checked
  evidence.
- Public-only context must not leak private candidate or checked evidence text.

Forbidden:

- No automatic artifact refutation.
- No accepted status changes.
- No promotion behavior changes.
- No human-review creation.
- No provider calls.
- No MCP expansion.

## Phase 2: Research Run Record and CLI Core

Task: `research-run-record-cli-core`

Goal: implement full research-run provenance in one PR: model, schema, CLI
lifecycle, command recording, evidence report, export, replay planning, docs,
tests, and security boundaries.

Required CLI:

```text
cosheaf run start --issue <issue-id> --operator external --json
cosheaf run append-command --run <run-id> --input-json <path> --json
cosheaf run append-artifact --run <run-id> --artifact <artifact-id> --json
cosheaf run append-output --run <run-id> --input-json <path> --json
cosheaf run finalize --run <run-id> --status <status> --json
cosheaf run show <run-id> --json
cosheaf run evidence-report --run <run-id> --json
cosheaf run export-review --run <run-id> --json --dry-run
cosheaf run export-review --run <run-id> --json
cosheaf run replay-plan --run <run-id> --json
```

Controlled paths:

```text
.cosheaf/runs/<run-id>/run.json
reviews/runs/<run-id>.yaml
```

Forbidden:

- No hidden chain-of-thought.
- No secrets or `.env` dumps.
- No full environment dump.
- No accepted writes.
- No human-review spoofing.
- No provider/MCP expansion.

## Phase 3: External Operator Workflow and Demos

Framework docs should describe a CLI/Git operator loop:

1. Read `AGENTS.md`, milestone, issue, and relevant docs.
2. Start a research run record.
3. Inspect workspace and baseline validate/gate.
4. Search memory and build context.
5. Read known failures and candidate/checked evidence.
6. Make issue-scoped edits.
7. Record commands and outputs.
8. Stage bundles, failure logs, checked evidence, or review requests only
   through controlled CLI paths.
9. Re-run checks.
10. Finalize and export the run record.
11. Open PR with run summary, commands, skipped rows, limitations, non-goals,
    and authority boundaries.

Downstream `tcs-cosheaf-workspace-template` should add a runnable research-run
demo after framework commands exist. `tcs-kb-public` should add checked
evidence policy and at most one draft-only example if useful.

## Phase 4: Integration, Eval, and Three-Repo Smoke

Add or update `cosheaf.evals.checked_evidence_run_loop`, fixtures under
`evals/checked_evidence_run_loop/`, `scripts/ecosystem_smoke.py`, and relevant
evaluation/security docs.

Default evals must require no hosted provider, API key, MCP, network, SAT,
SMT, Lean, or lake. Optional rows are skipped, not pass.

## Phase 5: v0.3.0 Release

After implementation and downstream demos/policies landed, the project
prepared `release-v030-readiness-and-rc`, then completed
`release-v030-publication-closeout`.

Readiness questions:

- Is checked evidence implemented and clearly separated from candidate
  evidence?
- Are research run records reproducible and safe to review?
- Can Codex-style agents operate the loop through CLI/Git without embedded
  model runtime?
- Do workspace-template and public KB have needed policy/demo surfaces?
- Are security/eval suites in place?
- Are open issues/PRs empty or intentionally deferred?

The release-candidate PR bumped package metadata to `0.3.0` after readiness
passed. It did not create the public tag. Downstream pins updated only after
the maintainer published the tag/release and release smoke from `@v0.3.0`
passed.

## Completion Definition

`v0.3.0` is complete only when:

- checked counterexample evidence is a durable, typed, non-authoritative
  evidence surface;
- candidate counterexamples cannot be mistaken for checked evidence in CLI,
  context, reports, or evals;
- research runs can be started, appended, finalized, shown, exported, and
  summarized through evidence reports;
- Codex-style external operator workflow is documented and demoed through
  CLI/Git;
- default tests do not require hosted providers, API keys, MCP, SAT, SMT,
  Lean, lake, or network;
- security/eval suites cover authority escalation, private leakage,
  skipped-not-pass, and secret redaction;
- workspace-template and public KB downstream policy/demo surfaces are
  aligned;
- release notes remain conservative and do not claim production readiness,
  automatic theorem proving, automatic accepted promotion, AI-as-human-review,
  or informal/formal semantic alignment.
