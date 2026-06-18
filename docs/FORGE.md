# Forge Dry-Run Planning

`cosheaf.forge` is the boundary for local git and GitHub workflow planning.
The first forge implementation is dry-run only. It builds typed preview DTOs
that can be used by the CLI, app facade, and future server surfaces without
performing git writes, GitHub writes, token storage, or network calls.

## Commands

```bash
cosheaf forge status --json
cosheaf forge issue preview --from issues/open/<issue-id>.yaml --json
cosheaf forge pr preview --base main --head <branch> --json
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

## Authority Boundary

Forge output is planning context only. It does not grant human review, verifier
pass, gate pass, accepted knowledge, accepted refutation, source metadata, or
promotion authority. A closed local issue, a GitHub issue, a GitHub PR, or a
merged PR must not be treated as accepted artifact evidence.

Future non-dry-run forge actions must be separate tasks, require explicit
confirmation, avoid token persistence, and preserve the existing accepted
promotion protocol.
