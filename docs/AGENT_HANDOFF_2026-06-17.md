# Agent Handoff: v0.9.0 Documentation Closeout

## Current state checked on 2026-06-18

| Repo | Local branch | Local status |
|------|--------------|--------------|
| tcs-cosheaf | docs-v090-handoff-closeout | documentation closeout branch |
| tcs-cosheaf-workspace-template | release-v090-pins | clean local branch, partial v0.9.0 pin updates |
| tcs-kb-public | main | clean, still pinned to v0.7.0 in CI/docs |

## Framework release state

- `pyproject.toml` records `version = "0.9.0"`.
- `cosheaf/__init__.py` records `__version__ = "0.9.0"`.
- `python -m cosheaf.cli version --json` reports `0.9.0`.
- GitHub release `v0.9.0` is published:
  <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.9.0>.

## Code audit result

The current `cosheaf workflow` implementation is present but thin:

- `workflow start` emits a workflow JSON record and authority notice.
- `workflow step` prints an ephemeral step status and does not persist state.
- `workflow readiness` reports that persisted readiness is not assessable yet.
- Persistent `.cosheaf/workflows/<workflow-id>/` storage, `workflow show`,
  bounded `workflow run`, draft proposals, workflow handoffs, scanner
  integration, and `cosheaf eval reviewable-workflow --json` are not complete.

Do not describe `v0.9.0` as a complete issue-to-handoff workflow engine. It is
a published initial reviewable-workflow surface.

The normal verification ladder is not green on this checkout:

- `make lint` fails with ruff issues across existing V13/V14 Python code,
  including `cosheaf/actions/*`, `cosheaf/orchestrator_fsm/*`,
  `cosheaf/workflow/*`, and `cosheaf/research/loop_executor.py`.
- `make typecheck` fails with mypy issues in `cosheaf/librarian/retrieval.py`,
  `cosheaf/actions/*`, and `cosheaf/research/loop_executor.py`.
- `make validate`, `make gate`, workflow CLI smoke, version JSON, and
  `git diff --check` passed for this documentation closeout.

The lint/typecheck failures were not fixed in this docs-only handoff pass.

## Downstream drift to fix after this branch

Workspace-template:

- README and Makefile mention `v0.9.0`.
- Several scripts still default to `v0.8.0`.
- Some docs still mention `v0.7.0`.

Public KB:

- `.github/workflows/ci.yml` still installs
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.7.0`.
- README still says CI installs from the published `v0.7.0` framework tag.

These require separate downstream PRs. Do not hide them in the framework
closeout summary.

## Key invariants

- No accepted writes without the promotion workflow.
- No human review creation by agents.
- Skipped is not pass.
- No default hosted provider path.
- No automatic theorem proving or Lean semantic-alignment claim.
- Workflow, loop, operator, handoff, eval, MCP, and provider outputs are review
  context only.
- No agent prefixes in branch, PR, or issue titles.

## Verification commands

Run before PR closeout when feasible:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

For docs-only handoff work, at minimum run:

```bash
python -m cosheaf.cli version --json
git diff --check
```

## Operator notes

- GitHub CLI/proxy fallback:
  `HTTP_PROXY=http://127.0.0.1:3067` and
  `HTTPS_PROXY=http://127.0.0.1:3067`.
- Git author should be `CheemsaDoge <cheemsadoge@gmail.com>`.
- Three repos are under `H:\ai4tcs\`.
- Runtime outputs under `.cosheaf/` and `context/TASKS/` should not be
  committed unless a task explicitly asks for persisted review-context
  artifacts.
