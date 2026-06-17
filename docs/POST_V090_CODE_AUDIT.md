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

## Code Audit Findings At Publication Closeout

At the publication closeout captured by this audit, the workflow
implementation was present but thin:

- `cosheaf/workflow/engine.py` defines workflow DTOs, authority notices,
  `start_workflow`, `append_step`, and `assess_readiness`.
- `cosheaf/workflow/cli.py` registers `workflow start`, `workflow step`, and
  `workflow readiness`.
- `workflow start` returns a JSON record but does not write
  `.cosheaf/workflows/<workflow-id>/workflow.json`.
- `workflow step` created an in-memory `WorkflowStep` but only printed
  `ephemeral, not persisted`.
- `workflow readiness` printed that readiness was not yet assessable from
  persisted state.

Therefore, the code audited here did not yet satisfy the full V14 Phase B-F
target. It was a published initial workflow surface, not a completed
issue-to-handoff workflow engine. A later V14 B.1 follow-up adds persistent
workflow runtime storage, `workflow show`, persisted `workflow step`, bounded
`workflow run`, and persisted readiness reports; draft proposals, workflow
handoffs, scanner integration, and reviewable-workflow evals remain future
work.

Initial local quality checks during this closeout found that the documentation
branch did not pass the normal full verification ladder:

- `make lint` fails with ruff issues in existing Python code, including
  `cosheaf/actions/builtins.py`, `cosheaf/actions/cli.py`,
  `cosheaf/actions/registry.py`, `cosheaf/actions/workers.py`,
  `cosheaf/cli.py`, `cosheaf/orchestrator_fsm/*`, `cosheaf/workflow/*`, and
  `cosheaf/research/loop_executor.py`.
- `make typecheck` fails with mypy issues in `cosheaf/librarian/retrieval.py`,
  `cosheaf/actions/builtins.py`, `cosheaf/actions/workers.py`, and
  `cosheaf/research/loop_executor.py`.
- These failures were observed on the initial documentation closeout branch.

Follow-up code-quality commits in PR #425 repaired those lint/typecheck
failures without adding new V14 runtime capability. The repair scope was
limited to ruff formatting/import cleanup, existing-model type alignment, and
current API compatibility in the action registry, librarian, FSM, workflow, and
research-loop local-action surfaces.

Checks that now pass locally on PR #425:

- `python -m cosheaf.cli version --json`;
- `python -m cosheaf.cli workflow --help`;
- `python -m cosheaf.cli workflow start --issue issue.audit.v090 --query "documentation closeout" --json`;
- `make lint`;
- `make typecheck`;
- `make test` with 753 tests;
- `make validate`;
- `make gate`;
- `git diff --check` reported only expected LF/CRLF working-copy warnings and
  no whitespace errors.

## V14 Items Still Missing After The Publication Closeout

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

## Recommended Next Work Recorded During Publication Closeout

1. Finish PR #425 by waiting for GitHub CI on the latest pushed commit and
   merge only after required checks are green.
2. Keep the v0.9.0 workflow surface described as initial/thin despite the
   green quality ladder.
3. Fix downstream workspace-template pin/script/doc drift in a separate PR.
4. Fix public-KB framework pin and workflow-output policy drift in a separate
   PR.
5. Continue V14 implementation from persistent workflow storage and tests
   rather than treating `v0.9.0` as a complete workflow engine. This item is
   addressed by the later V14 B.1 workflow-core follow-up; proposal, handoff,
   scanner, eval, and downstream policy work remain.
