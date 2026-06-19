# ADR 0036: Forge Boundary

Status: accepted

Date: 2026-06-19

## Context

Cosheaf development currently uses external git and GitHub commands for
issue-driven repository workflow. The framework also has local issue YAML
records and an application facade that future CLI, MCP, server, and dashboard
surfaces should share.

Cosheaf needs a typed boundary that can describe intended actions, run limited
local git actions, and perform narrowly confirmed GitHub issue/PR actions
without pushing branches, storing credentials, or changing knowledge authority.

## Decision

Introduce `cosheaf.forge` as the Git/GitHub workflow boundary. It exposes:

- `ForgeCredentialProvider` protocol for future explicit credential lookup;
- `LocalGitPlan`;
- `GitHubIssuePlan`;
- `GitHubPrPlan`;
- `ForgePreviewResult`; and
- `ForgeActionResult`.

The CLI exposes:

```bash
cosheaf forge status --json
cosheaf forge issue preview --from issues/open/<issue-id>.yaml --json
cosheaf forge issue create --from issues/open/<issue-id>.yaml --confirm --json
cosheaf forge pr preview --base main --head <branch> --json
cosheaf forge pr create --base main --head <branch> --draft --confirm --json
cosheaf forge pr submit --base main --head <branch> --draft --confirm --json
cosheaf forge branch create <branch> --confirm --json
cosheaf forge commit --message <message> --confirm --json
cosheaf forge push --branch <branch> --confirm --json
cosheaf forge sync --json
```

The app facade exposes corresponding `forge_status`,
`forge_issue_preview`, `forge_pr_preview`, `forge_branch_create`, and
`forge_commit` methods, plus `forge_github_issue_create`,
`forge_push`, `forge_github_pr_create`, `forge_github_pr_submit`, and
`forge_sync`.

Forge previews remain dry-run only. Confirmed actions are limited to local
branch creation, local commits, explicit branch pushes, GitHub issue creation,
and GitHub PR creation/submission. `forge sync` is a read-only reconciliation
placeholder in A4.3.

## Authority Boundary

Forge previews are planning output only. They do not perform git commits, git
pushes, GitHub issue creation, GitHub PR creation, token storage, network
calls, human review, verifier passes, gate passes, artifact acceptance,
refutation, or promotion.

Every preview result must serialize the dry-run and no-write flags and include
authority-boundary warning text.

Confirmed local git actions may create a local branch, local commit, or push a
non-protected branch only after `--confirm`. Branch creation and push refuse
`main`/`master`. They must not read or store tokens or change
accepted/promotion rules. `forge commit` must refuse untracked or unstaged
ambiguity, require staged changes, run repository validation and gatekeeper
first, and stop on validation or gate failure.

Confirmed GitHub actions may create a GitHub issue or pull request only after
`--confirm`. `forge pr submit` additionally runs validation/gate and pushes the
non-protected head branch before `gh pr create`. GitHub calls use `shell=False`
and rely on credentials outside the repository, such as authenticated `gh` state
or environment tokens supported by `gh`. Forge must not read token values, store
tokens, close local issues, or treat GitHub issue/PR/merge state as accepted
knowledge. When possible, GitHub issue creation links the returned
URL into the local issue record's `external_links` while leaving local issue
status unchanged.

## Consequences

- CLI and future server surfaces can share the same typed forge service.
- Tests prove preview paths do not shell out or mutate files, local action
  paths shell out only to local `git`, and confirmed GitHub action paths require
  `--confirm`.
- Operators can use `cosheaf forge` for local branch/commit actions and for
  confirmed GitHub issue/PR creation, but still use external tools for pushes
  and merges.

## Rejected Options

- Add unconfirmed `gh` subprocess calls.
- Read or persist GitHub tokens during dry-run previews.
- Treat GitHub issue/PR state as artifact review, verifier, gate, or accepted
  knowledge authority.
- Let future server code shell out to CLI for preview planning.
