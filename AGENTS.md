# AGENTS.md

## 1. Project

TCS-Cosheaf is a Git-backed research knowledge base and agent harness for theoretical computer science. It manages typed research artifacts such as definitions, claims, proofs, constructions, algorithms, reductions, counterexamples, experiments, reviews, and issues.

## 2. Core invariants

- `kb/accepted/` contains only accepted artifacts.
- `kb/draft/` contains only draft or pre-accepted artifacts.
- Accepted artifacts must not depend on draft artifacts.
- Artifact IDs must be globally unique.
- Every artifact must pass schema validation.
- Every public behavior change must include tests.
- Every public interface change must update `context/INTERFACE_REGISTRY.md`.
- Every architectural decision must be recorded in `docs/ADR/`.
- Do not hide verification failures.
- External tool absence should produce a skipped verifier result, not crash the core system.
- Generated outputs must be deterministic.

## 3. Development commands

The intended project commands are:

- `make lint`
- `make typecheck`
- `make test`
- `make validate`
- `make gate`

If a command does not exist yet, the current task should either implement it or clearly state why it is not available yet.

## 4. Coding style

- Use Python 3.11+.
- Use Pydantic v2 for typed data modeling and validation.
- Use Typer for CLI surfaces.
- Use pytest for tests.
- Use ruff for linting.
- Keep optional external tools optional.
- Tests must not depend on network access.
- Avoid global mutable state unless the design explicitly justifies it.

## 5. Testing requirements

Every new behavior must include tests. CLI behavior must include smoke tests. Gatekeeper behavior must include both pass and fail tests.

## 6. Documentation requirements

Update documentation when behavior, public commands, artifact schema, or workflow changes.

User handoff messages should be written in Chinese. All other project-facing content should be written in English unless a task explicitly requires otherwise.

## 7. Review guidelines

Reviews should focus on broken invariants, missing tests, nondeterminism, swallowed errors, unlogged external commands, schema incompatibility, accepted artifacts depending on draft artifacts, and public interface changes without registry or ADR updates.
