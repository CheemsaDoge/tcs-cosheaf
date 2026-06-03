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

## GitHub Workflow

Pull requests are the review unit for Codex tasks. Each PR should use the
repository pull request template and explicitly record the summary, changed
files, tests run, risks, interface changes, documentation changes,
artifact/schema changes, and gatekeeper result.

Branch protection and review requirements are documented in
[`docs/REVIEW_POLICY.md`](REVIEW_POLICY.md). Direct pushes to `main` are
disallowed. All changes should follow the issue -> branch -> PR -> CI/gate ->
review -> merge workflow.

GitHub issue forms are provided for feature tasks, bug tasks, and research
issues. Feature task issues should constrain Codex work with a goal, allowed
files, acceptance criteria, required commands, and a context pack path. Research
issues should record the problem statement, domain, known baselines, relevant
artifacts, expected evidence, and required gates. Bug task issues should record
observed behavior, expected behavior, reproduction steps, logs, and the
suspected module.

GitHub Actions CI runs on pull requests and pushes to `main` using Python 3.11.
CI installs the package with development dependencies and then runs:

- `make lint`
- `make typecheck`
- `make test`
- `make validate`
- `make gate`

CI must not require optional external formal tools such as Lean, Sage, Z3, cvc5,
or SAT solvers. Tests must not make network calls.

## Interface and Architecture Changes

Public interface changes require INTERFACE_REGISTRY update in `context/INTERFACE_REGISTRY.md`.

Architecture changes require ADR.

## Workspace Configuration

Use `cosheaf workspace info` to inspect the active workspace before assuming a
single KB tree. If `cosheaf.toml` is absent, the repository runs in legacy mode
with one writable KB root at `kb/`.

When `cosheaf.toml` is present, the `[workspace]` table names the workspace and
each `[[kb]]` table declares one KB root with `name`, repository-relative
`path`, `readonly`, and `priority` fields. Storage discovery reads configured
KB roots plus repository-local `issues/` and `examples/`.

Private artifacts may depend on public artifacts. Public artifacts must not
depend on private artifacts. Accepted artifacts must not depend on draft or
pre-accepted artifacts, even across KB roots. Do not manually merge framework
and KB repositories.

Lifecycle write commands respect readonly roots. `cosheaf artifact create`
writes into the writable private root by default in configured workspaces, and
`cosheaf artifact move-status` refuses records loaded from readonly roots.

## Verification

Do not hide verification failures. If an intended command does not exist yet, the task must either implement it or clearly state why it is not available yet.

## Artifact Lifecycle Commands

Use `cosheaf artifact create` for new artifact records instead of hand-writing
YAML when the artifact is meant to enter the lifecycle tree. The command derives
the repository path from artifact type, status, and ID, refuses duplicate IDs,
and validates the new file before reporting success.

Use `cosheaf artifact move-status <artifact-id> <new-status>` for lifecycle
status movement instead of manual file shuffling. The command checks that the
current artifact path already matches its current status, validates the
repository before moving, writes deterministic YAML, and refuses direct moves to
`accepted`.

Accepted promotion requires a future dedicated review/gate workflow. Until that
exists, do not move artifacts into `kb/accepted/` manually.

## Context Packs

Use `cosheaf context build <issue-id>` to generate a bounded task context pack
under `context/TASKS/<issue-id>/`.

Each context pack contains:

- `CONTEXT.md`
- `ACCEPTANCE.md`
- `RELEVANT_ARTIFACTS.md`
- `KNOWN_FAILURES.md`
- `COMMANDS.md`

Context packs are deterministic, issue-scoped, and intentionally short. They do
not include every repository artifact by default. Relevant artifacts are ranked
with explainable local reasons:

- direct references from the issue;
- one-hop dependency neighbors of directly referenced artifacts;
- artifact domains matching issue title, description, or tags;
- artifact tags matching issue tags.

Within the same relevance class, accepted artifacts are preferred over draft
artifacts. Draft artifacts are visibly marked as `[DRAFT]`. Refuted, obsolete,
and superseded artifacts are shown only when they match the issue and are marked
with their terminal status, not presented as current truth.

Use `cosheaf context show <issue-id>` to build the pack and print the main
context document for quick handoff into a new Codex conversation.

## Handoff

User handoff messages should be written in Chinese. Project-facing documentation should remain in English unless a task explicitly requests otherwise.
