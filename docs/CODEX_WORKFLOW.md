# Codex Workflow

## Repository Memory

Codex conversations are not project memory. The repository is project memory.

Durable project decisions, current state, public interfaces, milestones, and workflow rules must be recorded in repository files. Future tasks should not rely on assumptions preserved only in a chat transcript.

## Operating Scope

TCS-Cosheaf is moving toward a three-repository architecture:

- `tcs-cosheaf` is the framework repository for the CLI, schema, artifact
  models, validation, gatekeeper, verifier adapters, context-pack machinery,
  workspace configuration support, and workflow rules.
- `tcs-kb-public` is the public reusable TCS knowledge base for public,
  citable definitions, known theorems, constructions, reductions,
  counterexamples, and source metadata.
- `tcs-cosheaf-workspace-template` is the user-facing workspace template that
  combines the framework package, readonly public KB, and writable private KB
  overlay.

Users should not manually merge framework and KB repositories. Workspaces should
use `cosheaf.toml` to make the framework package, readonly public KB, and
writable private KB overlay feel like one usable environment. Private artifacts
may depend on public artifacts; public artifacts must not depend on private
artifacts. Accepted artifacts must not depend on draft artifacts, even across KB
roots.

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

Before nontrivial new work, inspect existing issues. If no relevant issue
exists and GitHub issue creation is available, create a focused issue for the
work. If GitHub issue creation is unavailable because `gh` is missing,
unauthenticated, or unauthorized, create a local markdown issue draft under
`issues/open/`, clearly report that remote issue creation was skipped, and do
not pretend a GitHub issue was created.

Branches should use short human-readable names such as
`<phase-task>-short-description`. Do not add `codex/`, `codex-`, or other
agent-specific prefixes to issue titles, branch names, or PR titles unless the
maintainer explicitly asks for that prefix. If an issue, maintainer, or release
workflow specifies an exact branch name, preserve that exact branch name. Do
not push directly to `main`. Keep each PR small and reviewable, and do not
combine unrelated roadmap items into one PR.

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

Skipped is not pass. Optional external tool absence should produce a skipped
verifier result, not a core workflow crash. Expected validation failures should
be cleanly reported; unexpected errors should not be swallowed. Do not weaken
tests to make them pass, and do not mark placeholder behavior as complete.

## Repository Creation

When a task asks Codex to create repositories, first run `gh --version` and
`gh auth status`. Create a repository only when GitHub CLI is present,
authenticated, and authorized. Verify that the remote exists after creation and
open a PR where possible.

Never fake repository creation, branch creation, issue creation, PR creation,
remote pushes, or passing checks. If any GitHub step fails, report the exact
blocker and the closest honest next step.

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

Use `cosheaf artifact promote <artifact-id>` to promote eligible artifacts into
accepted knowledge. Promotion validates the repository, runs the gatekeeper,
refuses blocking gatekeeper issues, refuses target verifier `fail` or `error`
results, requires `review.state` to be `human_reviewed` or `accepted`, requires
dependencies to be accepted local artifacts or explicit external references, and
writes deterministic YAML under `kb/accepted/<type-dir>/<artifact-id>.yaml`.

Do not move artifacts into `kb/accepted/` manually. Direct accepted creation and
direct `cosheaf artifact move-status <artifact-id> accepted` remain refused.
Issue, task, and review records are not lifecycle artifacts and must not be
promoted with `artifact promote`.

## Controlled Agent Writes

Use controlled write commands only when a task explicitly permits draft or
review-staging writes:

- `cosheaf draft write-artifact --input-json <path> --json`
- `cosheaf draft write-source-note --input-json <path> --json`
- `cosheaf bundle submit --input-json <path> --json`
- `cosheaf review request --input-json <path> --json`
- `cosheaf review request-from-bundle --bundle <path> --json`

Prefer `--dry-run` before a real write when an agent is proposing changes.
These commands validate the JSON request, report exact target paths, and refuse
accepted paths, readonly KB roots, accepted artifact status, and
`human_reviewed` review spoofing. `bundle submit` validates worker bundle v2
manifests for review only; it does not complete tasks, merge outputs, promote
artifacts, or write accepted knowledge. `review request` writes draft
informational review-request records only; it does not create human review.
`review request-from-bundle` generates the same draft informational review
request from WorkerBundle assumptions, uncertainty, failed attempts,
verification requests, counterexample candidates, risk flags, next steps, and
limitations. It does not approve, reject, mark human review, create verifier
results, or write accepted knowledge.

After any controlled write, run validation and gate commands required by the
task. Validation and gate success remain evidence for review, not a substitute
for human review or promotion.

## CLI Agent Operator Contract

For Codex-style execution, use the CLI as the first machine interface and the
human/CI oracle. MCP is optional and is not required for ordinary repository
work. The detailed v0.3.0 runbook is
[`docs/EXTERNAL_OPERATOR_RUN_LOOP.md`](EXTERNAL_OPERATOR_RUN_LOOP.md).

Follow this sequence for nontrivial issue work:

1. Read `AGENTS.md`, `context/CURRENT_MILESTONE.md`, this workflow document,
   and the GitHub issue.
2. Start a research run with `cosheaf run start --issue <issue-id>
   --operator external --json` when auditable operator provenance is expected.
3. Inspect workspace state:
   `cosheaf workspace info --json`.
4. Establish the pre-change baseline:
   `cosheaf validate --json` and `cosheaf gate run --json`.
5. Search issue-scoped memory:
   `cosheaf memory search "<query>" --issue <issue-id> --json`.
6. Build bounded context:
   `cosheaf context build <issue-id> --json`.
   For `v0.4.0` planning work, also generate or inspect a strategy plan with
   `cosheaf strategy plan --issue <issue-id> --json`,
   `cosheaf strategy show <plan-id> --json`, and
   `cosheaf strategy next <plan-id> --json`. If a context pack already exists,
   use `cosheaf strategy plan --issue <issue-id> --from-context
   context/TASKS/<issue-id> --json`.
7. Read `context/TASKS/<issue-id>/CONTEXT.md`,
   `RELEVANT_ARTIFACTS.md`, `KNOWN_FAILURES.md`, `COMMANDS.md`, and
   `ACCEPTANCE.md` when present.
8. Make only issue-scoped changes. If the task permits generated research
   outputs, write only draft/proposal/source-note/bundle/review-staging
   records through the controlled commands above.
9. Record relevant commands, artifacts, and controlled outputs with
   `cosheaf run append-command`, `cosheaf run append-artifact`, and
   `cosheaf run append-output`. Do not store secrets, hidden reasoning, full
   environment dumps, or accepted-write claims.
10. Re-run task-required checks, including `make lint`, `make typecheck`,
    `make test`, `make validate`, `make gate`, and `git diff --check` unless
    the issue narrows the required command set.
11. Finalize and export the run with `cosheaf run finalize` and
    `cosheaf run export-review --dry-run` first, then `export-review` only when
    a review record is intended. For strategy-planner work, update and stage
    strategy review context with `cosheaf strategy update-from-run --plan
    <plan-id> --run <run-id> --json` and `cosheaf strategy export-review --plan
    <plan-id> --dry-run --json` before any real strategy review export.
12. Open one PR with a summary that records changed files, exact commands,
    results, runtime outputs, limitations, interface/docs/schema changes, and
    gate verdict. When counterexamples or checked evidence are relevant,
    distinguish candidate counterexamples from checked evidence.

Allowed agent-facing command families are:

- read/check: `version`, `workspace info`, `validate`, `gate run`,
  `memory cards`, `memory search`, `context build`, `context show`, and
  `strategy plan/show/graph/next/update-from-run`, and `orchestrator plan`,
  preferably with `--json` for machine consumers;
- controlled write: `draft write-artifact`, `draft write-source-note`,
  `bundle submit`, `review request`, `run export-review`, and
  `strategy export-review`, preferably with `--dry-run --json` before real
  writes;
- provenance: `run start`, `run append-command`, `run append-artifact`,
  `run append-output`, `run finalize`, `run show`, `run evidence-report`, and
  `run replay-plan`;
- ordinary repository verification: `make lint`, `make typecheck`,
  `make test`, `make validate`, `make gate`, and `git diff --check`.

Forbidden agent actions are:

- direct writes to `kb/accepted/`;
- direct accepted promotion unless the issue explicitly asks for the existing
  promotion workflow and all review/gate requirements are satisfied;
- marking AI output or agent review as `human_reviewed`;
- treating validation, gate, verifier, Lean, SAT, SMT, provider, MCP, memory,
  context, or strategy output as human review;
- treating strategy plans as proof, evidence, verifier pass, gate pass,
  accepted status, accepted refutation, or promotion authority;
- treating skipped verifier/provider/tool results as passes;
- writing into readonly public KB roots;
- copying private artifacts into public KB or readonly roots;
- requiring MCP for CLI-first work;
- sending private KB context to hosted providers without explicit policy,
  configuration, preview, and operator consent.

If private-root scope appears in workspace, memory, or context output, preserve
that scope label in the PR summary and avoid quoting private artifact text in
public GitHub surfaces unless the task explicitly permits it.

## Local Task Runner

Use `cosheaf task run <task-id> -- <command> [args...]` only for explicit local
commands against existing task records. The local runner is not an LLM runtime,
does not call hosted model providers, and does not add network service calls.
It executes the argv list with `shell=False`, enforces a timeout, runs from the
repository root by default, allows only repository-local `--cwd` values, and
rejects bundle paths outside the repository before command execution. It logs
stdout, stderr, return code, command metadata, and optional bundle validation
status under `.cosheaf/tasks/<task-id>/runs/<run-id>/`.

Use `--bundle <path>` to validate a worker output bundle after a successful
command without completing the task. Use `--complete-with-bundle <path>` only
when the command succeeded and the task should be completed through the existing
orchestrator stub. Bundle paths must be repository-local YAML manifests or
repository-local directories containing `bundle.yaml`. Neither mode merges
outputs into accepted knowledge or promotes artifacts. Accepted knowledge still
enters only through review, gates, and `cosheaf artifact promote`.

## Local Orchestrator Dry-Run

Use `cosheaf orchestrator run --issue <issue-id> --dry-run --local-only` to
exercise the deterministic issue plan with local fake workers. The default
dry-run worker writes worker bundle v2 manifests for the reasoner, verifier, and
orchestrator steps under `.cosheaf/orchestrator/<issue-id>/runs/<run-id>/`.
Those bundles are review context only. They may name proposal paths under
`.cosheaf/orchestrator/.../proposals/`, but the dry-run does not write those
proposal artifacts, does not write `kb/accepted/`, does not create human review
records, does not run gates, and does not promote artifacts.

Treat the generated verifier bundle as a checklist reminder, not as a verifier
pass. Real validation, gatekeeper runs, verifier adapters, human review, and
promotion remain explicit follow-up steps outside the dry-run workflow.

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

## Agent-Facing JSON

For external coding agents, prefer deterministic JSON output on core read-only
commands when the result will be parsed by a program:

- `cosheaf version --json`
- `cosheaf workspace info --json`
- `cosheaf validate --json`
- `cosheaf gate run --json`
- `cosheaf memory cards --json`
- `cosheaf memory search "<query>" --json`
- `cosheaf context build <issue-id> --json`
- `cosheaf context show <issue-id> --json`
- `cosheaf strategy plan --issue <issue-id> --json`
- `cosheaf strategy show <plan-id> --json`
- `cosheaf strategy graph <plan-id> --json`
- `cosheaf strategy next <plan-id> --json`
- `cosheaf strategy update-from-run --plan <plan-id> --run <run-id> --json`
- `cosheaf strategy export-review --plan <plan-id> --dry-run --json`
- `cosheaf orchestrator plan --issue <issue-id> --json`
- `cosheaf draft write-artifact --input-json <path> --json --dry-run`
- `cosheaf draft write-source-note --input-json <path> --json --dry-run`
- `cosheaf bundle submit --input-json <path> --json --dry-run`
- `cosheaf review request --input-json <path> --json --dry-run`
- `cosheaf review request-from-bundle --bundle <path> --json --dry-run`
- `cosheaf run start --issue <issue-id> --operator external --json`
- `cosheaf run append-command --run <run-id> --input-json <path> --json`
- `cosheaf run append-artifact --run <run-id> --artifact <artifact-id> --json`
- `cosheaf run append-output --run <run-id> --input-json <path> --json`
- `cosheaf run finalize --run <run-id> --status completed --stop-reason <text> --json`
- `cosheaf run evidence-report --run <run-id> --json`
- `cosheaf run export-review --run <run-id> --dry-run --json`
- `cosheaf run replay-plan --run <run-id> --json`

JSON mode keeps human text rendering out of stdout and uses structured
`ErrorResult` payloads for expected command failures. Human output remains the
default. JSON output does not grant accepted-write authority, does not run
hosted providers, does not write accepted knowledge, and does not make skipped
verifier/provider results into passes.

Research-run JSON output is provenance only. It does not execute replay plans,
does not create human review, does not mark verifier or gate pass, does not
write accepted knowledge, and does not authorize promotion.

Strategy-plan JSON output is planning guidance only. It does not execute the
ranked tasks, create evidence, mark verifier or gate pass, create human review,
write accepted knowledge, or authorize promotion. Runtime plans write under
`.cosheaf/strategy/<plan-id>/strategy.json`; explicit strategy review export
writes only non-authoritative context under `reviews/strategy/`.

## Handoff

User handoff messages should be written in Chinese. Project-facing documentation should remain in English unless a task explicitly requests otherwise.
