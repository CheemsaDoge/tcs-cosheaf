# Current Milestone

## Milestone

`v0.3.0` Checked Evidence + Research Run Loop implementation.

## Goal

Start the post-`v0.2.4` line that turns external-agent research into auditable
evidence. The immediate goal is to separate candidate counterexamples from
checked counterexample evidence, then add a reproducible research-run record
that Codex-style external operators can drive through CLI/Git.

This milestone does not claim production hosted multi-agent readiness. It does
not add a web UI, multi-user permissions, automatic theorem proving,
automatic Lean autoformalization, automatic accepted promotion,
AI-as-human-review, provider/MCP authority expansion, or automatic
informal/formal semantic alignment.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.2.4` on
  `main`.
- Remote tags `v0.1.1`, `v0.2.0`, `v0.2.1`, `v0.2.2`, `v0.2.3`, and
  `v0.2.4` exist.
- The GitHub release `v0.2.4 Artifact Failure Memory` is published and is not
  a production-readiness claim.
- `tcs-cosheaf-workspace-template` pins active demo, Makefile, CLI-agent,
  provider-preview, fake-provider smoke, verifier-evidence, and failure-memory
  demo paths to `@v0.2.4`.
- `tcs-kb-public` CI installs `tcs-cosheaf` from `@v0.2.4`.
- `docs/CODEX_DEVELOPMENT_PLAN_V6.md` and ADR 0023 are completed durable
  records for the `v0.2.4` artifact failure-memory line.
- `docs/POST_V024_V6_COMPLETION_AUDIT.md` records that V6 is complete and not
  the active task queue.
- `docs/CODEX_DEVELOPMENT_PLAN_V7.md` is the active accelerated `v0.3.0`
  plan.
- ADR 0024 records the checked-evidence and research-run-loop direction.
- `docs/POST_V024_V030_KICKOFF_AUDIT.md` records the kickoff state audit.
- The checked counterexample evidence core is implemented and merged through
  PR #335: model, schema, CLI, controlled staging, context surfacing,
  promotion-readiness warnings, security tests, eval fixtures, and docs. It
  remains non-authoritative review evidence.
- The research-run record CLI core is now implemented on the active
  development branch: model, schema, lifecycle CLI, command/artifact/output
  append paths, evidence report, review export, replay plan, security tests,
  eval fixtures, and docs. It remains non-authoritative provenance.

## Active Scope

The active line is:

```text
v0.3.0 Checked Evidence + Research Run Loop
```

Compressed milestones:

1. Kickoff audit + plan/ADR landing.
2. Checked counterexample evidence core.
3. Research run record and CLI core.
4. External operator workflow and downstream demos/policies.
5. Integration, eval, and three-repository smoke.
6. v0.3.0 release candidate and publication closeout.

## Current And Next Functional Tasks

Current functional task:

```text
research-run-record-cli-core
```

This task implements external-operator research-run provenance with start,
append, finalize, show, evidence-report, export-review, and replay-plan CLI
surfaces without provider/MCP expansion or accepted-write authority.

After this PR lands, proceed to:

```text
external-operator-workflow-docs
```

That next task should update operator-facing docs and templates so Codex-style
agents run the checked-evidence and research-run loop through CLI/Git.

## Explicit Boundaries

- CLI remains the first agent interface and the human/CI oracle.
- Codex-style agents are external operators that call CLI, edit files, run
  tests, and open PRs.
- Do not embed GPT, Claude, or any hosted model as the default Cosheaf runtime
  in this milestone.
- Real provider calls remain default-off and require explicit configuration,
  credentials, policy scope, context preview, network permission, and operator
  consent.
- No real provider calls run in CI or default tests.
- MCP remains optional and non-blocking.
- No controlled-write MCP, provider MCP tools, direct accepted writes, or
  accepted-promotion bypass is part of this milestone.
- Worker/provider/Codex/verifier output may become draft/proposal/bundle/run
  evidence context only.
- A `candidate_counterexample` is not checked counterexample evidence.
- Checked counterexample evidence is evidence for review, not human review,
  accepted refutation, accepted status, or promotion authorization by itself.
- A research run record is provenance, not proof, verifier pass, gate pass,
  human review, accepted status, or promotion authorization.
- Accepted knowledge still requires validation, gates, human review where
  policy requires it, verifier evidence where applicable, and explicit
  promotion.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier, provider, SAT, SMT, Lean, lake, optional-tool, network, or
  operator results are not passes.
- Public KB accepted artifacts still require complete source metadata and
  human review.
- Formal links remain metadata unless a checker actually records a result.
- A successful Lean `#check` remains symbol/import resolution, not
  informal/formal semantic alignment.

## Current Operating State

The V6 artifact failure-memory line is complete. New work follows the
accelerated V7 plan for `v0.3.0`. Checked counterexample evidence is now a
durable review-evidence surface, but it remains separate from human review,
accepted refutation, accepted status, and promotion authority. Continue to
avoid treating failure memory, counterexample candidates, verifier requests,
verifier evidence, checked evidence, research-run records, provider output,
evals, validation, gates, or context retrieval as human review, proof, accepted
status, verifier pass, gate pass, or promotion authority.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
