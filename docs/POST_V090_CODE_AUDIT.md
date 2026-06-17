# Post-v0.9.0 Code And Documentation Audit

Date: 2026-06-18

This audit records the current state after the `v0.9.0` tag and GitHub release
were published. It is meant as handoff material for the next agent or
maintainer. It corrects stale v0.7/v0.8 wording and distinguishes the real
published code from the broader V14 plan.

## Verified Release State

- `pyproject.toml` records `version = "0.9.0"`.
- `cosheaf/__init__.py` records `__version__ = "0.9.0"`.
- `python -m cosheaf.cli version --json` reports `0.9.0`.
- `docs/releases/v0.9.0.md` exists.
- GitHub release `v0.9.0` exists and is published:
  <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.9.0>.
- Local `main` was at `4c00cb1 V14 F.1: v0.9.0 RC metadata (#423)` before this
  documentation closeout branch was created.

## Code Audit Findings

The current workflow implementation is present but thin:

- `cosheaf/workflow/engine.py` defines workflow DTOs, authority notices,
  `start_workflow`, `append_step`, and `assess_readiness`.
- `cosheaf/workflow/cli.py` registers `workflow start`, `workflow step`, and
  `workflow readiness`.
- `workflow start` returns a JSON record but does not write
  `.cosheaf/workflows/<workflow-id>/workflow.json`.
- `workflow step` creates an in-memory `WorkflowStep` but only prints
  `ephemeral, not persisted`.
- `workflow readiness` prints that readiness is not yet assessable from
  persisted state.

Therefore, the current code does not yet satisfy the full V14 Phase B-F target.
It is a published initial workflow surface, not a completed issue-to-handoff
workflow engine.

Local quality checks during this closeout also found that the current codebase
does not pass the normal full verification ladder:

- `make lint` fails with ruff issues in existing Python code, including
  `cosheaf/actions/builtins.py`, `cosheaf/actions/cli.py`,
  `cosheaf/actions/registry.py`, `cosheaf/actions/workers.py`,
  `cosheaf/cli.py`, `cosheaf/orchestrator_fsm/*`, `cosheaf/workflow/*`, and
  `cosheaf/research/loop_executor.py`.
- `make typecheck` fails with mypy issues in `cosheaf/librarian/retrieval.py`,
  `cosheaf/actions/builtins.py`, `cosheaf/actions/workers.py`, and
  `cosheaf/research/loop_executor.py`.
- These failures were observed on a documentation closeout branch and were not
  fixed in this docs-only pass.

Checks that did pass during this closeout:

- `python -m cosheaf.cli version --json`;
- `python -m cosheaf.cli workflow --help`;
- `python -m cosheaf.cli workflow start --issue issue.audit.v090 --query "documentation closeout" --json`;
- `make validate`;
- `make gate`;
- `git diff --check` reported only expected CRLF working-copy warnings and no
  whitespace errors.

## V14 Items Still Missing

- persistent workflow runtime storage;
- workflow show/run commands;
- bounded local-action execution through workflow run;
- rejected non-whitelisted action tests for workflow run;
- draft proposal generation from workflow output;
- workflow handoff build/show/scan/export commands;
- workflow scanner integration;
- `cosheaf eval reviewable-workflow --json`;
- workspace-template reviewable-workflow demo target;
- public-KB policy guard that workflow packets cannot become source metadata,
  accepted proof, human review, verifier/gate pass, accepted status, accepted
  refutation, or promotion authority.

## Downstream State Observed During Closeout

The workspace-template branch `release-v090-pins` was checked out locally and
contained partial `v0.9.0` pin updates. Its README and Makefile referenced
`v0.9.0`, but several scripts still defaulted to `v0.8.0`, and some docs still
mentioned `v0.7.0`.

The public KB local `main` still installed the framework from `v0.7.0` in
`.github/workflows/ci.yml` and README text. That downstream repository still
needs a dedicated pin/policy closeout PR for `v0.9.0` or for whichever release
the maintainer chooses as the supported public-KB baseline.

## Authority Boundary

The audit found no reason to widen authority boundaries. Workflow, loop,
operator-session, MCP, provider, eval, and handoff outputs remain review
context only. They must not be used as:

- accepted knowledge;
- source metadata;
- human review;
- verifier pass;
- gate pass;
- accepted refutation;
- promotion authority.

No automatic theorem proving, Lean semantic alignment, default hosted-provider
execution, arbitrary shell execution, accepted-write path, or multi-user
permission surface is established by `v0.9.0`.

## Recommended Next Work

1. Finish this documentation closeout PR and merge it.
2. Fix the current framework lint/typecheck failures before treating v0.9.0 as
   a fully green baseline.
3. Fix downstream workspace-template pin/script/doc drift in a separate PR.
4. Fix public-KB framework pin and workflow-output policy drift in a separate
   PR.
5. Continue V14 implementation from persistent workflow storage and tests
   rather than treating `v0.9.0` as a complete workflow engine.
