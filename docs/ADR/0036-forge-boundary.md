# ADR 0036: Forge Dry-Run Boundary

Status: accepted

Date: 2026-06-19

## Context

Cosheaf development currently uses external git and GitHub commands for
issue-driven repository workflow. The framework also has local issue YAML
records and an application facade that future CLI, MCP, server, and dashboard
surfaces should share.

Before adding controlled git commits or GitHub issue/PR creation, Cosheaf needs
a typed planning boundary that can describe intended actions without mutating a
repository, calling the network, or storing credentials.

## Decision

Introduce `cosheaf.forge` as the Git/GitHub planning boundary. The first
implementation is dry-run only and exposes:

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
```

The app facade exposes corresponding `forge_status`,
`forge_issue_preview`, and `forge_pr_preview` methods.

## Authority Boundary

Forge previews are planning output only. They do not perform git commits, git
pushes, GitHub issue creation, GitHub PR creation, token storage, network
calls, human review, verifier passes, gate passes, artifact acceptance,
refutation, or promotion.

Every preview result must serialize the dry-run and no-write flags and include
authority-boundary warning text.

## Consequences

- CLI and future server surfaces can share the same typed forge service.
- Git/GitHub write behavior remains out of scope until a later task adds
  explicit confirmation and negative tests.
- Tests can prove the initial forge path does not shell out or mutate files.
- Operators still use external git/GitHub tools for real commits, pushes,
  issues, PRs, and merges until controlled forge actions are implemented.

## Rejected Options

- Add `gh` or `git` subprocess calls in the initial forge task.
- Read or persist GitHub tokens during dry-run previews.
- Treat GitHub issue/PR state as artifact review, verifier, gate, or accepted
  knowledge authority.
- Let future server code shell out to CLI for preview planning.
