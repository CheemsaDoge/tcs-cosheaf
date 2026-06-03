# AGENTS.md

## 1. Project Operating Model

TCS-Cosheaf is a Git-backed research knowledge base and agent harness for
theoretical computer science. It manages typed research artifacts such as
definitions, claims, proofs, constructions, algorithms, reductions,
counterexamples, experiments, reviews, verifier evidence, issues, and agent
task context.

The repository is project memory. Codex conversations are not project memory.
Durable project decisions, current state, workflow rules, architecture changes,
public interfaces, research artifacts, review evidence, and known limitations
must be recorded in repository files.

All nontrivial work should be issue-driven. One task should normally correspond
to one issue, one focused branch, one pull request, and one reviewable
increment. Avoid combining unrelated roadmap items in a single branch or PR.

User handoff messages should be written in Chinese. Project-facing repository
content should be written in English unless the task explicitly requires another
language.

## 2. Repository Architecture

The intended long-term architecture has three public repositories plus private
user overlays:

- `tcs-cosheaf`: framework repository. It contains the CLI, schema, artifact
  models, validation, gatekeeper, verifier adapters, context-pack machinery,
  workspace configuration support, and repository workflow rules.
- `tcs-kb-public`: public reusable TCS knowledge base. It contains public,
  citable definitions, known theorems, constructions, reductions,
  counterexamples, and source metadata.
- `tcs-cosheaf-workspace-template`: user-facing workspace template. It combines
  the framework package, readonly public KB, and writable private KB overlay
  into one usable local environment.
- User private KB: writable research overlay, usually under `kb/private/` in a
  workspace or in a private repository.

Do not vendor the full public KB into the framework repository. The framework
repository may contain only tiny seed examples needed for tests, examples, and
documentation. Users should not manually merge framework and KB repositories;
the intended model is framework package plus readonly public KB plus writable
private KB overlay.

## 3. Workspace Model

Workspaces use `cosheaf.toml`. A workspace may define multiple KB roots. Each KB
root should have a name, filesystem path, readonly flag, and priority.

Expected layering rules:

- Public KB roots are normally readonly.
- Private KB roots are writable.
- Private artifacts may depend on public artifacts.
- Public artifacts must not depend on private artifacts.
- Accepted artifacts must not depend on draft or pre-accepted artifacts, even
  across KB roots.
- Artifact IDs must be globally unique across all loaded KB roots.
- Readonly KB roots must not be modified by write commands.
- When no `cosheaf.toml` exists, preserve the old single-repository behavior.

Commands such as `validate`, `gate`, `context`, `index`, and `graph` should use
`cosheaf.toml` by default once workspace support exists. Future workspace
interfaces must be recorded in `context/INTERFACE_REGISTRY.md`.

## 4. Core Invariants

- `kb/accepted/` contains only accepted artifacts in the single-repo framework
  layout.
- `kb/draft/` contains only draft or pre-accepted artifacts in the single-repo
  framework layout.
- Accepted artifacts must not depend on draft or otherwise pre-accepted
  artifacts.
- Artifact IDs must be globally unique.
- Every artifact must pass schema validation.
- Every public behavior change must include tests.
- Every public interface change must update `context/INTERFACE_REGISTRY.md`.
- Every architectural decision must be recorded in `docs/ADR/`.
- Do not hide verification failures.
- External tool absence should produce a skipped verifier result, not crash the
  core system.
- Generated outputs must be deterministic.

## 5. Issue-Driven Workflow

Future Codex tasks should:

1. Inspect existing GitHub issues when relevant.
2. Create a GitHub issue for nontrivial new work if one does not already exist.
3. Create a focused branch named `codex/<task-id-or-short-name>`.
4. Keep each PR small and reviewable.
5. Include a PR summary, tests run, known limitations, and changed files.
6. Avoid combining unrelated roadmap items into one PR.

If GitHub issue creation is unavailable because `gh` is missing,
unauthenticated, or unauthorized, create a local markdown issue draft under
`issues/open/`, clearly report that remote issue creation was skipped, and do
not pretend a GitHub issue was created.

Use context packs when issue-specific context exists. Do not stuff the whole
repository into context. Prefer accepted artifacts over draft artifacts, clearly
label draft artifacts, and surface known failures or refuted artifacts when they
are relevant to the task.

## 6. Branch And PR Policy

Do not push directly to `main`. Every implementation should go through a pull
request targeting `main`.

Use branches named `codex/<task-id-or-short-name>`. One branch should normally
serve one issue and one PR.

PR requirements:

- PRs that change public interfaces must update
  `context/INTERFACE_REGISTRY.md`.
- PRs that change architecture must add or update ADRs under `docs/ADR/`.
- PRs that change schema must update schema docs, examples, and tests.
- PRs that change behavior must update tests.
- PRs that change workflow must update docs.
- PRs must record summary, changed files, commands run, known limitations, and
  any failed or skipped checks.

## 7. Required Commands

For normal code changes, run:

- `make lint`
- `make typecheck`
- `make test`
- `make validate`
- `make gate`

If a command is unavailable or fails due to environment limitations, report it
exactly. Do not hide it and do not claim success. Skipped is not pass.

## 8. Coding Style

- Use Python 3.11+.
- Use Pydantic v2 for typed data modeling and validation.
- Use Typer for CLI surfaces.
- Use pytest for tests.
- Use ruff for linting.
- Keep optional external tools optional.
- Tests must not depend on network access.
- Avoid global mutable state unless the design explicitly justifies it.

## 9. Testing Requirements

Every new behavior must include tests. CLI behavior must include smoke tests.
Gatekeeper behavior must include both pass and fail tests. Do not weaken tests
to make them pass, and do not mark placeholder behavior as complete.

For normal code changes, run the required commands in Section 7 before opening
or updating a PR. Documentation-only changes may still run the full command set
when feasible because repository workflow changes can affect validation and
gate expectations.

## 10. Documentation Requirements

Update documentation when behavior, public commands, artifact schema, workspace
layout, repository workflow, knowledge policy, or gate behavior changes.

Durable updates belong in repository files such as:

- `AGENTS.md`
- `README.md`
- `docs/`
- `docs/ADR/`
- `context/PROJECT_STATE.md`
- `context/INTERFACE_REGISTRY.md`
- issue records under `issues/`
- review records under `reviews/`

## 11. Knowledge Policy

Public KB policy:

- Only public, citable TCS knowledge belongs in public KB repositories.
- No private conjectures.
- No unpublished research ideas.
- No LLM-generated accepted artifacts without human review.
- Accepted public artifacts require source metadata.
- Draft artifacts must be clearly marked draft.
- Do not mass-import papers or large artifact batches without focused review.

Private KB policy:

- Private KB may contain conjectures, proof attempts, failures, research notes,
  experiments, and private ideas.
- Private artifacts may depend on public artifacts.
- Private knowledge must not leak into public KB unless explicitly promoted and
  reviewed.
- Do not promote private claims to accepted knowledge without review and gates.

## 12. Validation And Gate Policy

- Skipped is not pass.
- Optional external tool absence should produce a skipped verifier result, not
  crash core workflows.
- Expected validation failures should be cleanly reported.
- Unexpected errors should not be swallowed.
- Deterministic output is required.
- Validation failures must not be hidden or downgraded without justification.
- Placeholder gates must be reported as skipped or not implemented, never pass.
- Do not mark incomplete behavior as complete.

## 13. Repository Creation Policy

When asked to create repositories:

1. Check `gh --version`.
2. Check `gh auth status`.
3. Create the repository only if authenticated and authorized.
4. Verify the remote repository exists.
5. Open a PR where possible.
6. If any step fails, report the exact blocker.

Never fake repository creation, branch creation, issue creation, PR creation,
remote pushes, or passing checks. Do not claim repositories, issues, branches,
PRs, or checks exist unless they actually exist.

## 14. Review Guidelines

Reviews should focus on broken invariants, missing tests, nondeterminism,
swallowed errors, unlogged external commands, schema incompatibility, accepted
artifacts depending on draft artifacts, public artifacts depending on private
artifacts, private knowledge leaking into public KB, readonly KB writes, public
interface changes without registry updates, and architecture changes without
ADR updates.
