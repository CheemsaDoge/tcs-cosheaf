# Forge Planning, Local Git, And GitHub Actions

`cosheaf.forge` is the boundary for local git and GitHub workflow planning.
Forge builds typed preview and action DTOs that can be used by the CLI, app
facade, and future server surfaces. Previews are dry-run only. Local git
branch/commit actions and GitHub issue/PR creation are available only behind
explicit `--confirm`.

## Commands

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
It refuses `main`/`master` targets and dirty working trees before changing refs.
Server/app callers may explicitly request `allow_dirty: true` to carry current
worktree changes onto a new non-protected branch; the CLI keeps the clean-tree
default.

`forge commit --message <message> --confirm` commits already staged changes
only in the CLI. It refuses current `main`/`master` branches, untracked files,
unstaged changes, and empty staged state to avoid ambiguous or protected-branch
commits. Server/app callers may explicitly request `stage_all: true` to stage
repository changes before validation, gate, and commit, but the protected-branch
guard still runs first. Before `git commit`, it runs repository validation and
gatekeeper through the in-process app services.

Local git actions report:

- `action_performed`
- `git_writes_performed`
- `network_calls_performed: false`
- `github_writes_performed: false`
- `push_performed: false`
- `github_pr_created: false`

These branch and commit commands never push, create a pull request, call GitHub,
read tokens, or store credentials.

`forge push --branch <branch> --confirm` pushes one non-protected branch with
`git push -u origin <branch>`. Without `--branch`, it uses the current branch.
It refuses `main`/`master`, requires explicit confirmation, reports
`push_performed: true`, and does not call the GitHub API or store credentials.

## Confirmed GitHub Actions

`forge issue create --from <path> --confirm` creates a GitHub issue from one
repository-local issue YAML record through the external `gh` command. It writes
the returned GitHub issue URL into the local issue record's `external_links`
when possible. It keeps the local issue `status` unchanged and never treats the
GitHub issue as artifact review, verifier evidence, gate evidence, accepted
status, refutation, or promotion evidence.

`forge pr create --base <base> --head <head> --draft --confirm` creates a
GitHub pull request through `gh pr create`. It does not push the branch and does
not close or accept any local issue or artifact. Because Cosheaf has no local PR
record, PR linking is limited to the returned URL in the action result.

`forge pr submit --base <base> --head <head> --draft --confirm` is the
reviewable branch-to-PR flow. It refuses `main`/`master` heads, runs repository
validation and gatekeeper in-process, stops on failure, pushes the head branch
with `git push -u origin <head>`, then creates the GitHub PR through
`gh pr create`. The result reports `validation_performed: true`,
`gate_performed: true`, `push_performed: true`, `github_pr_created: true`, and
the returned `github_pr_url`.

GitHub actions use credentials outside the repository, such as the user's
authenticated `gh` state or token environment variables supported by `gh`.
Forge does not read token values, write token files, or persist credentials in
the repository. The `ForgeCredentialProvider` protocol is reserved for future
server-provided credentials.

GitHub action results report:

- `action_performed: true`
- `network_calls_performed: true`
- `github_writes_performed: true`
- `github_issue_created` or `github_pr_created`
- `git_writes_performed` when a branch push was performed
- `push_performed` when a branch push was performed
- `local_issue_closed: false`

`forge sync --json` is read-only in A4.3. It returns a typed action result
without calling `git`, `gh`, the network, or mutating repository files. Future
sync behavior may reconcile local issue links and remote metadata, but it must
remain separate from accepted-artifact authority.

## Read-Only PR Status

The app/server Forge surface also exposes read-only GitHub PR status for the
web workbench through `CosheafApp.forge_github_pr_status` and
`GET /api/forge/pr-status`. This uses `gh pr view --json` when available and
returns a degraded payload when GitHub auth, `gh`, or network access is
missing. It writes no git state, GitHub state, local issue state, review
records, gate reports, verifier evidence, accepted artifacts, or promotion
records.

The status payload keeps `github_reviews` and `cosheaf_review` separate.
GitHub approvals, comments, CI checks, and gate checks are collaboration and
workflow context only. They are not Cosheaf human review unless a human later
uses an explicit review-record workflow.

## Authority Boundary

Forge output is planning context only. It does not grant human review, verifier
pass, gate pass, accepted knowledge, accepted refutation, source metadata, or
promotion authority. A closed local issue, a GitHub issue, a GitHub PR, or a
merged PR must not be treated as accepted artifact evidence.
