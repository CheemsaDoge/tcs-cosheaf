# Agent Handoff: v0.9.0 Documentation And CI Closeout

## Current state checked on 2026-06-18

| Repo | Local branch | Local status |
|------|--------------|--------------|
| tcs-cosheaf | docs-v090-handoff-closeout | documentation and CI closeout branch |
| tcs-cosheaf-workspace-template | release-v090-pins | clean local branch, partial v0.9.0 pin updates |
| tcs-kb-public | main | clean, still pinned to v0.7.0 in CI/docs |

## Open coordination

- Issue: <https://github.com/CheemsaDoge/tcs-cosheaf/issues/424>
- Pull request: <https://github.com/CheemsaDoge/tcs-cosheaf/pull/425>
- Branch: `docs-v090-handoff-closeout`
- Base branch: `main`
- Initial closeout commit: `c21cb1d Close out v0.9.0 docs and code audit`
- Author/committer: `CheemsaDoge <cheemsadoge@gmail.com>`

PR #425 is open and not draft. The first CI run for the documentation-only
closeout failed on lint/typecheck but passed test/validate/gate:

| Check | Last completed result |
|-------|----------------|
| lint | failure |
| typecheck | failure |
| test | success |
| validate | success |
| gate | success |

Follow-up commits on this branch now repair those local lint/typecheck
failures. Re-check PR #425 before acting on it; do not merge while any required
check is red or queued.

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

The normal verification ladder is green locally on this checkout after the
code-quality closeout:

- `make lint`: passed.
- `make typecheck`: passed for 201 source files.
- `make test`: passed with 753 tests.
- `make validate`: passed for 20 YAML records.
- `make gate`: passed.
- `git diff --check`: no whitespace errors; PowerShell reported only expected
  LF/CRLF working-copy warnings.

The code-quality repair was deliberately narrow: it fixes ruff formatting,
import order, mypy type mismatches, and current-model compatibility in the
existing action/librarian/FSM/workflow/research-loop surfaces. It does not add
persistent workflow storage, `workflow show/run`, draft proposals, handoff
commands, eval workflow support, provider defaults, accepted writes, or theorem
checking.

## Next-agent checklist

1. Re-check PR #425 status and CI before editing:

   ```powershell
   $env:HTTP_PROXY='http://127.0.0.1:3067'
   $env:HTTPS_PROXY='http://127.0.0.1:3067'
   gh pr view 425 --repo CheemsaDoge/tcs-cosheaf `
     --json mergeStateStatus,statusCheckRollup,url
   ```

2. Wait for the GitHub CI run for the latest pushed commit.
3. If CI stays green, merge PR #425 normally. If CI fails, fix only the failing
   check and rerun the normal verification ladder.
4. After merge, continue downstream drift fixes in separate PRs.

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
