# Public And Private KB Policy

TCS-Cosheaf separates reusable public knowledge from user-private research
overlays.

## Recommended User Entry Point

Use
[`tcs-cosheaf-workspace-template`](https://github.com/CheemsaDoge/tcs-cosheaf-workspace-template)
for ordinary user workspaces. The template installs or references the
`tcs-cosheaf` framework, mounts
[`tcs-kb-public`](https://github.com/CheemsaDoge/tcs-kb-public) as readonly
public knowledge, and keeps user-owned work under a writable `kb/private`
overlay.

Do not manually merge the framework repository, public KB repository, and
private workspace into one mixed repository. Keeping the three roles separate
preserves review boundaries: framework changes happen in `tcs-cosheaf`, public
knowledge maintenance happens in `tcs-kb-public`, and private research drafts
stay in the user workspace.

## Public KB

Public KB roots are normally readonly in a user workspace. Public KB content
should contain only public, citable theoretical computer science knowledge such
as definitions, known theorems, constructions, reductions, counterexamples, and
source-backed examples.

Public KB rules:

- No private conjectures.
- No unpublished research ideas.
- No LLM-generated accepted artifacts without human review.
- Accepted public artifacts require structured source metadata when workspace
  policy has `accepted_requires_source = true`.
- Draft public artifacts must be clearly marked draft.
- Do not mass-import papers or large artifact batches without focused review.

Accepted public artifacts must record at least one source in `sources`. Each
source must have `kind`, non-empty `title`, at least one `authors` value,
`year`, and at least one locator from `doi`, `arxiv`, `url`,
`theorem_number`, or `page`. External dependency references such as
`external:doi/...` are not source metadata.

Draft public artifacts are allowed to omit formal source metadata while they
remain draft. This keeps exploratory staging possible without weakening the
accepted public KB policy.

## Private KB

Private KB roots are writable user overlays. They may contain conjectures,
proof attempts, failures, experiments, research notes, private ideas, and draft
claims.

Private KB rules:

- Private artifacts may depend on public artifacts.
- Private accepted artifacts may omit formal source metadata unless a later
  workspace policy requires it.
- Private knowledge must not leak into public KB unless explicitly promoted and
  reviewed.
- Do not promote private claims to accepted knowledge without review and gates.

## Workflow And Handoff Review Context

Reviewable workflow outputs, draft proposals, workflow handoff JSON, workflow
handoff scan reports, and exported `reviews/workflow/` YAML are review context.
They are useful for human review, but they are not public KB source metadata,
human review records, verifier passes, gate passes, accepted status, accepted
refutations, or promotion authority.

Workflow handoff scanners may block private path leakage and source metadata
fabrication, but a clean scan is still only a guard result. It does not make a
candidate public, accepted, source-reviewed, or human-reviewed.

Do not copy workflow handoff output into `kb/public/accepted/`. Public accepted
artifacts still require complete source metadata, passing validation and gates,
and explicit human review through the normal artifact lifecycle.

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
and documentation, but it must not vendor the full public KB. The intended user
model is:

```text
framework package + readonly public KB + writable private KB overlay
```
