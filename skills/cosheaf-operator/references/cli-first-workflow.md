# CLI-First Workflow

This reference expands the operator checklist from `SKILL.md`. Repository
files, schemas, services, CLI behavior, gates, review policy, and issue scope
remain authoritative.

## Baseline

Run these commands before relying on repository state:

```bash
cosheaf workspace info --json
cosheaf validate --json
cosheaf gate run --json
```

Use issue-scoped retrieval and context instead of loading the whole repository:

```bash
cosheaf memory search "<query>" --issue <issue-id> --json
cosheaf context build <issue-id> --json
```

If the task is public-facing or provider-preview work, prefer public-only
context unless the issue and policy explicitly allow private context:

```bash
cosheaf context build <issue-id> --json --public-only
```

## Controlled Draft And Review Staging

Controlled write commands accept explicit JSON request files and produce
structured JSON results:

```bash
cosheaf draft write-artifact --input-json <path> --json --dry-run
cosheaf draft write-source-note --input-json <path> --json --dry-run
cosheaf bundle submit --input-json <path> --json --dry-run
cosheaf review request --input-json <path> --json --dry-run
```

These commands do not run promotion, do not create human review, do not call
hosted providers, and do not change gate or verifier results. They must refuse
accepted paths, accepted artifact status, readonly public KB roots, and
`human_reviewed` review spoofing.

## WorkerBundle Discipline

WorkerBundle output should preserve review context:

- `used_artifacts` and `used_sources` should be explicit.
- `claims` should be proposals or findings, not accepted knowledge.
- `proposed_artifacts` should target draft/proposal paths.
- `verification_requests` should say what still needs checking.
- `failures_or_counterexamples` must preserve negative evidence.
- `risk_flags`, `next_steps`, and `confidence` should remain honest.

Do not remove risk or uncertainty fields to make output look cleaner.

## Provider And MCP Boundaries

MCP is optional. It is useful only for assistants that need resource or tool
surfaces rather than shell access. It must not expose arbitrary shell, arbitrary
filesystem access, direct accepted promotion, accepted-path writes, secrets, or
private KB context outside the selected scope.

Hosted providers are separate from this skill. Real calls require explicit
configuration, policy scope, operator consent, and fake or mocked tests. A
provider result can become a worker bundle, draft proposal, or review context;
it cannot become accepted knowledge by itself.

## Verification Closeout

For normal framework changes, run:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

For downstream workspace-template work, run the repository-specific Makefile or
`cosheaf` commands required by that issue. If a command cannot run, report the
exact command, exit state, and reason. Skipped is not pass.

## PR Summary Template

```text
Repository:
Branch:
Issue:
Summary:
Changed files:
Commands run:
Results:
Runtime outputs:
Public/private scope handling:
Known limitations:
Risk:
Docs updated:
Tests updated:
Public interfaces changed:
ADR required:
Artifact/schema changed:
Gate result:
```
