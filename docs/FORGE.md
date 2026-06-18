# Forge Planning And Local Git Actions

`cosheaf.forge` is the boundary for local git and GitHub workflow planning.
Forge builds typed preview and action DTOs that can be used by the CLI, app
facade, and future server surfaces. GitHub-facing surfaces are still dry-run
only. Local git branch and commit actions are available only behind explicit
`--confirm`.

## Commands

```bash
cosheaf forge status --json
cosheaf forge issue preview --from issues/open/<issue-id>.yaml --json
cosheaf forge pr preview --base main --head <branch> --json
cosheaf forge branch create <branch> --confirm --json
cosheaf forge commit --message <message> --confirm --json
```

All commands also accept `--repo-root <path>` for tests and explicit operator
workflows.

## Dry-Run Contract

Forge previews must report:

- `dry_run_only: true`
- `network_calls_performed: false`
- `git_writes_performed: false`
- `github_writes_performed: false`
- an `authority_warning` explaining that the preview is not proof, review,
  validation, gate success, accepted status, refutation, or promotion evidence.

`forge issue preview` reads one repository-local issue YAML file and returns a
`GitHubIssuePlan`. It does not create a GitHub issue and does not store or read
a token.

`forge pr preview` returns a `LocalGitPlan` and `GitHubPrPlan`. It does not run
`git`, `gh`, or any subprocess, and it does not inspect remote state.

## Confirmed Local Git Actions

`forge branch create <branch> --confirm` creates and switches to a local branch.
It refuses dirty working trees before changing refs.

`forge commit --message <message> --confirm` commits already staged changes
only. It refuses untracked files, unstaged changes, and empty staged state to
avoid ambiguous commits. Before `git commit`, it runs repository validation and
gatekeeper through the in-process app services.

Local git actions report:

- `action_performed`
- `git_writes_performed`
- `network_calls_performed: false`
- `github_writes_performed: false`
- `push_performed: false`
- `github_pr_created: false`

These commands never push, create a pull request, call GitHub, read tokens, or
store credentials.

## Authority Boundary

Forge output is planning context only. It does not grant human review, verifier
pass, gate pass, accepted knowledge, accepted refutation, source metadata, or
promotion authority. A closed local issue, a GitHub issue, a GitHub PR, or a
merged PR must not be treated as accepted artifact evidence.

Future GitHub-write forge actions must be separate tasks, require explicit
confirmation, avoid token persistence, and preserve the existing accepted
promotion protocol.
