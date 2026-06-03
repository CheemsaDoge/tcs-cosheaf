# Public And Private KB Policy

TCS-Cosheaf separates reusable public knowledge from user-private research
overlays.

## Public KB

Public KB roots are normally readonly in a user workspace. Public KB content
should contain only public, citable theoretical computer science knowledge such
as definitions, known theorems, constructions, reductions, counterexamples, and
source-backed examples.

Public KB rules:

- No private conjectures.
- No unpublished research ideas.
- No LLM-generated accepted artifacts without human review.
- Accepted public artifacts require source metadata.
- Draft public artifacts must be clearly marked draft.
- Do not mass-import papers or large artifact batches without focused review.

## Private KB

Private KB roots are writable user overlays. They may contain conjectures,
proof attempts, failures, experiments, research notes, private ideas, and draft
claims.

Private KB rules:

- Private artifacts may depend on public artifacts.
- Private knowledge must not leak into public KB unless explicitly promoted and
  reviewed.
- Do not promote private claims to accepted knowledge without review and gates.

## Dependency Direction

The valid dependency direction is:

```text
private artifact -> public artifact
```

The invalid direction is:

```text
public artifact -> private artifact
```

This keeps reusable public knowledge independent of user-private research.

Accepted artifacts must not depend on draft or pre-accepted artifacts across
any KB roots.

## Framework Repository Boundary

The `tcs-cosheaf` framework repository may include tiny seed examples for tests
and documentation, but it must not vendor the full public KB. Users should not
manually merge the framework repository and KB repositories. The intended user
model is:

```text
framework package + readonly public KB + writable private KB overlay
```
