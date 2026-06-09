# ADR 0018: CLI Agent Operator Contract

## Status

Accepted

## Context

ADR 0015 corrected the post-`v0.2.0` direction to CLI-first agent access,
ADR 0016 defined the agent-access authority model, and ADR 0017 reclassified
MCP as an optional adapter. The repository now has deterministic CLI JSON for
core read-only commands and narrow controlled-write CLI commands for draft and
review-staging surfaces.

External coding agents need one concrete operator contract that says which
commands to run, what they may write, and what they must never infer from CLI
output. Without that contract, agent runs can drift into broad filesystem
editing, accepted-path writes, overclaiming validation as review, or treating
MCP/provider paths as required.

## Decision

Adopt this CLI agent operator contract for external coding agents such as
Codex, Cursor, Claude Code, or similar repository operators:

1. Read repository policy first: `AGENTS.md`, `context/CURRENT_MILESTONE.md`,
   the relevant issue, and issue-specific context if present.
2. Inspect workspace state with `cosheaf workspace info`, using `--json` when
   the caller will parse the result.
3. Establish the baseline with `cosheaf validate` and `cosheaf gate run`
   before making changes when the task may affect artifacts, workflow, or
   agent-access behavior.
4. Build bounded task context with `cosheaf memory search ... --issue
   <issue-id>` and `cosheaf context build <issue-id>` rather than reading the
   whole repository by default.
5. Read the generated context pack before writing.
6. Write only files allowed by the issue. When writing agent-generated research
   outputs through Cosheaf, use controlled draft/staging commands:
   `cosheaf draft write-artifact`, `cosheaf draft write-source-note`,
   `cosheaf bundle submit`, and `cosheaf review request`.
7. Prefer `--dry-run --json` before any controlled write that is not already
   mechanically obvious.
8. Re-run task-required tests, validation, and gates after changes.
9. Report exact commands, pass/fail/skipped results, changed files, runtime
   outputs, limitations, and any policy-relevant non-goals in the PR summary.

## Allowed Commands

Agent-safe CLI reads and checks include:

- `cosheaf version --json`
- `cosheaf workspace info --json`
- `cosheaf validate --json`
- `cosheaf gate run --json`
- `cosheaf memory cards --json`
- `cosheaf memory search "<query>" --issue <issue-id> --json`
- `cosheaf context build <issue-id> --json`
- `cosheaf context show <issue-id> --json`
- `cosheaf orchestrator plan --issue <issue-id> --json`

Controlled write commands are allowed only when the task explicitly permits
draft/proposal/review-staging writes:

- `cosheaf draft write-artifact --input-json <path> --json`
- `cosheaf draft write-source-note --input-json <path> --json`
- `cosheaf bundle submit --input-json <path> --json`
- `cosheaf review request --input-json <path> --json`

Human-readable forms of the same commands remain useful for operator review,
but machine consumers should prefer deterministic JSON output.

## Forbidden Actions

External coding agents must not:

- write directly to `kb/accepted/`;
- run or simulate accepted promotion unless the issue explicitly asks for the
  existing promotion workflow and all review/gate requirements are satisfied;
- mark `review.state: human_reviewed` or create approval/rejection decisions
  as an AI agent;
- treat validation, gate, verifier, Lean, SAT, SMT, provider, MCP, memory, or
  context output as human review;
- treat skipped verifier/provider/tool results as passes;
- write into readonly public KB roots;
- copy private artifacts into public KB or readonly roots;
- send private KB context to hosted providers without explicit policy,
  configuration, preview, and operator consent;
- require MCP for ordinary CLI-first work;
- use broad ad hoc filesystem edits for lifecycle artifact creation when a
  controlled Cosheaf write command is the requested surface.

## Public And Private KB Boundary

The operator contract preserves the three-repository model:

- public KB roots are normally readonly;
- private KB roots are writable overlays;
- private artifacts may depend on accepted public artifacts;
- public artifacts must not depend on private artifacts;
- accepted artifacts must not depend on draft artifacts;
- generated context and PR summaries must not leak private artifact text unless
  the task and policy explicitly allow private research context.

`cosheaf workspace info --json`, memory search, and context-pack output should
be treated as scope evidence. If a result labels private root scope, the agent
must keep that scope visible in any follow-up summary.

## Consequences

Future CLI, provider, Skill, and optional MCP work should keep this operator
contract stable. If new agent-facing commands are added, they should define:

- whether the command is read-only or controlled-write;
- whether `--json` is deterministic and machine-readable;
- whether it may write runtime sidecars;
- which paths and root scopes it may touch;
- which stable error codes indicate blocking policy failures.

This ADR is documentation and workflow policy only. It does not add runtime
behavior, implement provider calls, implement MCP tools, change artifact
schema, change gates, change verifier adapters, or weaken accepted-promotion
policy.

## Non-Goals

This ADR does not:

- implement a hosted provider gateway;
- implement MCP controlled-write tools;
- package an operator Skill;
- add automatic theorem proving or autoformalization;
- allow direct accepted writes;
- make AI, CLI, MCP, provider, SAT, SMT, or Lean output count as human review.
