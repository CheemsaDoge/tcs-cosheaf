# v0.4.0 Code Audit Closeout

Date: 2026-06-16

Scope: post-release audit for the published `v0.4.0` Strategy Planner +
Research Task Graph line. This is an audit record only. It does not add runtime
behavior, provider calls, MCP requirements, accepted writes, human review, or
promotion authority.

## Audited Surfaces

- Strategy DTOs: `cosheaf/strategy/models.py`
- Strategy planner: `cosheaf/strategy/planner.py`
- Strategy storage and review export: `cosheaf/strategy/storage.py`
- Strategy CLI commands: `cosheaf/cli.py`
- Strategy eval: `cosheaf/evals/strategy_planner.py`
- Strategy tests: `tests/test_strategy_models.py`,
  `tests/test_strategy_planner.py`, `tests/test_strategy_cli.py`,
  `tests/evals/test_strategy_planner_eval.py`, and
  `tests/security/test_strategy_planner_security.py`
- Ecosystem smoke integration: `scripts/ecosystem_smoke.py` and
  `tests/test_ecosystem_smoke.py`

## Findings

- Strategy plans persist runtime output under `.cosheaf/strategy/` by default.
- Explicit review export writes only under `reviews/strategy/`.
- Strategy DTOs include the non-authority notice and
  `accepted_write_performed: false`.
- Strategy task nodes reject direct `kb/accepted/` write paths, absolute paths,
  parent traversal paths, hidden-reasoning authority fields, and provider/API
  key-looking text in summaries or notes.
- `update-from-run` preserves failed and skipped research-run command status;
  skipped remains skipped and is not treated as pass.
- CLI JSON payloads expose strategy output as guidance only and do not claim
  proof, verifier pass, gate pass, human review, accepted status, accepted
  refutation, or promotion authority.
- The strategy-planner eval and ecosystem-smoke rows are deterministic local
  checks by default. Network release-smoke remains opt-in and skipped unless
  explicitly enabled.

## Boundaries Confirmed

- No default hosted provider call is part of the strategy planner.
- MCP is not required for strategy-planner workflows.
- Strategy commands do not promote artifacts.
- Strategy commands do not create human review.
- Strategy commands do not write accepted knowledge.
- Strategy plans, eval results, context summaries, and review exports remain
  advisory review context only.

## Verification

For the closeout PR, the framework repository was checked with:

- `make lint`
- `make typecheck`
- `make test`
- `make validate`
- `make gate`
- `git diff --check`

`make test` reported `651 passed`. `make gate` reported `Gate verdict: pass`.
Generated gate reports stayed under ignored `.cosheaf/` runtime output.

## Follow-Up

Future strategy work should start from a new issue and keep the same authority
boundaries unless a maintainer explicitly approves a separate design change.
