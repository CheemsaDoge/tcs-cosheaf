# Current Milestone

## Milestone

`v0.3.0` Checked Evidence + Research Run Loop published release closeout.

## Goal

Record that the post-`v0.2.4` checked-evidence and research-run loop line has
been implemented, packaged, tagged, smoke-tested, released, and aligned across
the workspace-template and public KB downstream repositories.

This milestone does not claim production hosted multi-agent readiness. It does
not add a web UI, multi-user permissions, automatic theorem proving,
automatic Lean autoformalization, automatic accepted promotion,
AI-as-human-review, provider/MCP authority expansion, or automatic
informal/formal semantic alignment.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.3.0`.
- Remote tags `v0.1.1`, `v0.2.0`, `v0.2.1`, `v0.2.2`, `v0.2.3`, `v0.2.4`,
  and `v0.3.0` exist.
- The GitHub release `v0.3.0 Checked Evidence + Research Run Loop` is
  published and is not a production-readiness claim.
- Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.3.0` passed.
- `tcs-cosheaf-workspace-template` active demo, Makefile, CLI-agent,
  provider-preview, fake-provider smoke, verifier-evidence, failure-memory,
  checked-evidence, and research-run paths pin or install `@v0.3.0`.
- `tcs-kb-public` CI installs `tcs-cosheaf` from `@v0.3.0`.
- `docs/CODEX_DEVELOPMENT_PLAN_V6.md` and ADR 0023 are completed durable
  records for the `v0.2.4` artifact failure-memory line.
- `docs/POST_V024_V6_COMPLETION_AUDIT.md` records that V6 is complete and not
  the active task queue.
- `docs/CODEX_DEVELOPMENT_PLAN_V7.md` is the completed accelerated `v0.3.0`
  plan.
- ADR 0024 records the checked-evidence and research-run-loop direction.
- `docs/POST_V024_V030_KICKOFF_AUDIT.md` records the kickoff state audit.
- `docs/releases/v0.3.0.md` records release-candidate verification,
  publication closeout, release smoke, and downstream pin alignment.
- The checked counterexample evidence core is implemented and merged through
  PR #335: model, schema, CLI, controlled staging, context surfacing,
  promotion-readiness warnings, security tests, eval fixtures, and docs. It
  remains non-authoritative review evidence.
- The research-run record CLI core is implemented through PR #337: model,
  schema, lifecycle CLI, command/artifact/output append paths, evidence report,
  review export, replay plan, security tests, eval fixtures, and docs. It
  remains non-authoritative provenance.
- The external operator workflow docs, workspace-template research-run demo,
  and public KB checked-evidence policy are merged downstream surfaces for the
  v0.3.0 run loop.
- The integration/eval/ecosystem smoke task is merged through PR #341. The
  ecosystem matrix includes checked-evidence eval, research-run eval,
  workspace-template research-run demo, and public KB checked-evidence policy
  smoke rows. Optional network and external-tool rows remain skipped, not
  pass, when unavailable.

## Completed Scope

The completed line is:

```text
v0.3.0 Checked Evidence + Research Run Loop
```

Completed compressed milestones:

1. Kickoff audit + plan/ADR landing.
2. Checked counterexample evidence core.
3. Research run record and CLI core.
4. External operator workflow and downstream demos/policies.
5. Integration, eval, and three-repository smoke.
6. v0.3.0 release candidate and publication closeout.

## Current And Next Functional Tasks

Current closeout task:

```text
release-v030-publication-closeout
```

This task is documentation/status closeout only. It records the already
completed public tag, GitHub release, release smoke, workspace-template pin
update, and public KB CI pin update. It does not add runtime behavior.

After this closeout lands, new work should start from a new issue-scoped plan
or the next approved longplan. Do not treat the completed v0.3.0 release as an
open queue for feature expansion.

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
implementation and publication for `v0.3.0` are complete. Checked
counterexample evidence is now a durable review-evidence surface, but it
remains separate from human review, accepted refutation, accepted status, and
promotion authority. Research-run records are provenance, not proof or review
authority. Continue to avoid treating failure memory, counterexample
candidates, verifier requests, verifier evidence, checked evidence,
research-run records, provider output, evals, validation, gates, or context
retrieval as human review, proof, accepted status, verifier pass, gate pass, or
promotion authority.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
