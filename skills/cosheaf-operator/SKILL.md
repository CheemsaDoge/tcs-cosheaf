---
name: cosheaf-operator
description: Use when operating TCS-Cosheaf repositories or workspaces as an external coding agent, especially issue-driven CLI-first tasks, context-pack handoff, draft or staging writes, worker-bundle review submissions, and PR summaries under public/private KB governance.
---

# Cosheaf Operator

Use this skill to operate TCS-Cosheaf through the CLI-first workflow. The
repository remains the source of truth; this skill is only an operator guide.

## Read First

Before changing files, read the current repository policy and task context:

- `AGENTS.md`
- `context/CURRENT_MILESTONE.md`
- the GitHub issue or local issue record
- relevant `docs/` pages, especially `docs/AGENT_ACCESS.md` and
  `docs/CODEX_WORKFLOW.md` when present
- generated context under `context/TASKS/<issue-id>/` when the issue references
  a context pack

## Default Path

For coding agents, prefer CLI commands with `--json` whenever output will be
parsed or used for decisions:

```bash
cosheaf workspace info --json
cosheaf validate --json
cosheaf gate run --json
cosheaf memory search "<query>" --issue <issue-id> --json
cosheaf context build <issue-id> --json
```

Use the human-readable commands as the operator-facing check and CI surface.
See [references/cli-first-workflow.md](references/cli-first-workflow.md) for
the full command sequence, controlled-write examples, and PR summary template.

## Controlled Writes

Only use controlled write commands when the issue explicitly permits draft or
review-staging output:

- `cosheaf draft write-artifact --input-json <path> --json --dry-run`
- `cosheaf draft write-source-note --input-json <path> --json --dry-run`
- `cosheaf bundle submit --input-json <path> --json --dry-run`
- `cosheaf review request --input-json <path> --json --dry-run`

Prefer `--dry-run` first. Real writes, if allowed, stay limited to draft,
proposal, source-note staging, bundle, or review-request records. WorkerBundle
output is review context only; it is not accepted knowledge.

## Optional Surfaces

MCP is optional and not required for normal coding-agent work. Hosted provider
workers are allowed only when the repository policy and issue explicitly permit
them; they must be default-off, fake or mocked in tests, policy-scoped, and
unable to write accepted knowledge.

## Forbidden

Never:

- write directly to `kb/accepted/` or accepted public KB paths
- mark AI output as `human_reviewed`
- treat validation, gates, memory, context, MCP, provider, verifier, Lean, SAT,
  or SMT output as human review
- treat skipped verifier or provider results as passes
- write into readonly public KB roots
- copy private artifacts into public KB
- send private KB context to hosted providers without explicit policy and
  operator consent
- require MCP for CLI-first work

## Closeout

Before opening or updating a PR, run the task-required checks and `git diff
--check`. The PR summary must list changed files, exact commands, pass/fail or
skipped results, runtime outputs, public/private scope handling, interface or
schema changes, known limitations, and any gate result.
