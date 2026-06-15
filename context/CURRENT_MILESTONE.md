# Current Milestone

## Milestone

`v0.3.0` Checked Evidence + Research Run Loop release candidate.

## Goal

Prepare the post-`v0.2.4` checked-evidence and research-run loop line for a
conservative `v0.3.0` release candidate. The implementation now separates
candidate counterexamples from checked counterexample evidence, records
reproducible research-run provenance, and lets Codex-style external operators
drive the loop through CLI/Git.

This milestone does not claim production hosted multi-agent readiness. It does
not add a web UI, multi-user permissions, automatic theorem proving,
automatic Lean autoformalization, automatic accepted promotion,
AI-as-human-review, provider/MCP authority expansion, or automatic
informal/formal semantic alignment.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.3.0` in the
  release-candidate PR.
- Remote tags `v0.1.1`, `v0.2.0`, `v0.2.1`, `v0.2.2`, `v0.2.3`, and
  `v0.2.4` exist.
- The public `v0.3.0` tag and GitHub release do not exist yet; they are
  publication-closeout work after the release-candidate PR merges.
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
  main branch through PR #337: model, schema, lifecycle CLI,
  command/artifact/output append paths, evidence report, review export, replay
  plan, security tests, eval fixtures, and docs. It remains non-authoritative
  provenance.
- The external operator workflow docs, workspace-template research-run demo,
  and public KB checked-evidence policy are merged downstream surfaces for the
  v0.3.0 run loop.
- The integration/eval/ecosystem smoke task is merged through PR #341. The
  ecosystem matrix includes checked-evidence eval, research-run eval,
  workspace-template research-run demo, and public KB checked-evidence policy
  smoke rows. Optional network and external-tool rows remain skipped, not
  pass, when unavailable.

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
release-v030-readiness-and-rc
```

This task audits readiness, adds conservative `v0.3.0` release-candidate
notes, updates release/status docs, and bumps package metadata to `0.3.0`
without changing runtime behavior.

After this PR lands and main is re-synced, proceed to:

```text
release-v030-publication-closeout
```

That follow-up task should verify no existing `v0.3.0` tag, create the
annotated tag from reviewed main, publish a conservative GitHub release, run
release smoke from `@v0.3.0`, and update downstream workspace-template and
public KB pins only after release smoke passes.

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

The V6 artifact failure-memory line is complete. The accelerated V7 functional
implementation for `v0.3.0` is complete enough for release-candidate
packaging. Checked counterexample evidence is now a durable review-evidence
surface, but it remains separate from human review, accepted refutation,
accepted status, and promotion authority. Research-run records are provenance,
not proof or review authority. Continue to avoid treating failure memory,
counterexample candidates, verifier requests, verifier evidence, checked
evidence, research-run records, provider output, evals, validation, gates, or
context retrieval as human review, proof, accepted status, verifier pass, gate
pass, or promotion authority.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
