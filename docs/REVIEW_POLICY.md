# Review Policy

## Purpose

TCS-Cosheaf treats Git as durable project memory. Review policy protects that
memory by ensuring that repository changes are issue-scoped, validated,
reviewed, and merged through an auditable process.

This policy applies to all changes, including human-authored changes and
Codex-assisted changes.

## Protected Main Branch

The `main` branch must be protected in GitHub.

Direct pushes to `main` are disallowed. Changes must enter `main` only through
pull requests that satisfy the required checks and review requirements below.

The branch protection or repository ruleset for `main` should require:

- pull requests before merging;
- required status checks before merging;
- branches to be up to date before merging;
- the baseline status checks named `lint`, `typecheck`, `test`, `validate`,
  and `gate`.

## Required Change Flow

All changes must follow this sequence:

1. Open or select an issue that states the goal, scope, allowed files, acceptance
   criteria, and required commands.
2. Create a task branch from the current `main` branch.
3. Implement the issue on that branch only.
4. Open a pull request targeting `main`.
5. Run CI and gatekeeper checks.
6. Review the PR.
7. Merge only after required checks pass and review requirements are satisfied.

One issue should map to one branch and one pull request unless the issue is
explicitly split into smaller follow-up issues.

## Baseline Checks

The baseline local and CI checks are:

- `make lint`
- `make typecheck`
- `make test`
- `make validate`
- `make gate`

CI must pass before merge. Local runs should be recorded in the pull request
body when feasible. Validation or gate failures must not be hidden, ignored, or
reported as successful.

Optional external formal tools such as Lean, SAT solvers, SMT solvers, or Sage
must remain optional. Their absence should produce skipped verifier results, not
core validation crashes.

## Required Documentation Updates

Public interface changes require an update to
`context/INTERFACE_REGISTRY.md`. Public interfaces include CLI commands, Python
APIs, artifact schemas, gate result formats, verifier adapter contracts, context
pack formats, and documented file layouts.

Architecture changes require a new or updated ADR under `docs/ADR/`.

Workflow, command, artifact schema, status, gatekeeper, verifier, or review
behavior changes must update the relevant documentation in the same pull
request.

## Human Review Required Areas

The following areas require human maintainer review before merge:

- artifact schema changes;
- artifact status lattice or status/path rule changes;
- gatekeeper checks, report schemas, or exit-code behavior;
- dependency graph behavior;
- repository index schema, manifest format, or rebuild behavior;
- accepted/draft/refuted/obsolete knowledge-base invariants;
- verifier result semantics, especially `pass`, `fail`, `error`, and `skipped`;
- public interface changes that require registry updates;
- architecture changes that require ADRs.

Codex review may assist by identifying risks, missing tests, nondeterminism, or
policy violations. It does not replace maintainer judgment. A maintainer remains
responsible for deciding whether a PR is correct, sufficiently tested, and safe
to merge.

## Merge Blocking Conditions

A pull request must not be merged when any of the following are true:

- required CI status checks are failing or missing;
- `make validate` or `make gate` fails;
- validation failures are hidden or downgraded without justification;
- generated outputs are nondeterministic when determinism is required;
- public interface changes are missing `context/INTERFACE_REGISTRY.md` updates;
- architecture changes are missing ADR updates;
- schema, status, gatekeeper, or index changes have not received human review;
- the branch is stale and branch protection requires it to be up to date.
