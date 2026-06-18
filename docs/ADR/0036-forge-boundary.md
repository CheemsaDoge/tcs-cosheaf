# ADR 0036: Forge Boundary

Status: accepted

Date: 2026-06-19

## Context

Cosheaf development currently uses external git and GitHub commands for
issue-driven repository workflow. The framework also has local issue YAML
records and an application facade that future CLI, MCP, server, and dashboard
surfaces should share.

Before adding controlled GitHub issue/PR creation, Cosheaf needs a typed
boundary that can describe intended actions and run limited local git actions
without pushing, calling the network, or storing credentials.

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
cosheaf forge pr preview --base main --head <branch> --json
cosheaf forge branch create <branch> --confirm --json
cosheaf forge commit --message <message> --confirm --json
```

The app facade exposes corresponding `forge_status`,
`forge_issue_preview`, `forge_pr_preview`, `forge_branch_create`, and
`forge_commit` methods.

GitHub-facing forge commands remain dry-run only. Local git branch creation and
commit are the only confirmed write actions in this ADR.

## Authority Boundary

Forge previews are planning output only. They do not perform git commits, git
pushes, GitHub issue creation, GitHub PR creation, token storage, network
calls, human review, verifier passes, gate passes, artifact acceptance,
refutation, or promotion.

Every preview result must serialize the dry-run and no-write flags and include
authority-boundary warning text.

Confirmed local git actions may create a local branch or local commit only
after `--confirm`. They must not push, create PRs, read or store tokens, or
change accepted/promotion rules. `forge commit` must refuse untracked or
unstaged ambiguity, require staged changes, run repository validation and
gatekeeper first, and stop on validation or gate failure.

## Consequences

- CLI and future server surfaces can share the same typed forge service.
- GitHub write behavior remains out of scope until a later task adds explicit
  confirmation, credentials, and negative tests.
- Tests prove preview paths do not shell out or mutate files, and local action
  paths only shell out to local `git`.
- Operators can use `cosheaf forge` for local branch and commit actions, but
  still use external tools for pushes, GitHub issues, PRs, and merges until
  controlled GitHub forge actions are implemented.

## Rejected Options

- Add `gh` subprocess calls before the GitHub-action task.
- Read or persist GitHub tokens during dry-run previews.
- Treat GitHub issue/PR state as artifact review, verifier, gate, or accepted
  knowledge authority.
- Let future server code shell out to CLI for preview planning.
