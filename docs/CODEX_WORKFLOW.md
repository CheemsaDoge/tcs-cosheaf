# Codex Workflow

## Repository Memory

Codex conversations are not project memory. The repository is project memory.

Durable project decisions, current state, public interfaces, milestones, and workflow rules must be recorded in repository files. Future tasks should not rely on assumptions preserved only in a chat transcript.

## Required Reading

Every task must read:

- `AGENTS.md`.
- Relevant files under `docs/`.
- Relevant files under `context/`.

Tasks that change architecture must read existing ADRs. Tasks that change public interfaces must read `context/INTERFACE_REGISTRY.md`.

## Task Shape

One task = one branch = one PR. Tasks should be small enough to review, verify, and describe precisely.

Do not run large tasks. Split broad work into sequenced branches with clear handoff notes and follow-up tasks.

## Interface and Architecture Changes

Public interface changes require INTERFACE_REGISTRY update in `context/INTERFACE_REGISTRY.md`.

Architecture changes require ADR.

## Verification

Do not hide verification failures. If an intended command does not exist yet, the task must either implement it or clearly state why it is not available yet.

## Context Packs

Use `cosheaf context build <issue-id>` to generate a bounded task context pack
under `context/TASKS/<issue-id>/`.

Each context pack contains:

- `CONTEXT.md`
- `ACCEPTANCE.md`
- `RELEVANT_ARTIFACTS.md`
- `KNOWN_FAILURES.md`
- `COMMANDS.md`

Context packs are deterministic, issue-scoped, and intentionally short. They
must prefer accepted artifacts over draft artifacts, visibly mark draft
artifacts, and avoid including every repository artifact by default.

Use `cosheaf context show <issue-id>` to build the pack and print the main
context document for quick handoff into a new Codex conversation.

## Handoff

User handoff messages should be written in Chinese. Project-facing documentation should remain in English unless a task explicitly requests otherwise.
