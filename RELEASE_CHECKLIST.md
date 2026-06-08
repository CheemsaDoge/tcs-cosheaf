# Three-Repository Release Checklist

This checklist is for release-hardening the TCS-Cosheaf ecosystem after the
`v0.1.1` Formal Link Layer support baseline. It is an operator checklist for
the framework package, public KB, and workspace template together. It is not a
production-readiness claim.

`v0.1.1` is the current downstream tag baseline for formal-link metadata. The
current `main` branch also contains later hardening work, including the
optional external Lean library reference adapter. Do not assume a downstream
pin to `@v0.1.1` includes post-tag `main` features.

## Scope

- Framework repository: `tcs-cosheaf`.
- Public knowledge repository: `tcs-kb-public`.
- User entry point: `tcs-cosheaf-workspace-template`.
- Current framework package metadata version on `main`: `0.1.1` until the next
  release tag is cut.
- Current downstream dependency baseline for formal-link metadata:
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.1.1`.

## Framework Checklist

### Version And Tag

- [x] `pyproject.toml` records package version `0.1.1`.
- [x] Remote tag `v0.1.1` exists as the formal-link support baseline.
- [ ] For any later release tag, confirm the tag target is a reviewed merge
  commit on the protected default branch.
- [ ] Downstream repositories pin to an explicit release tag rather than
  tracking `main`.
- [ ] If downstream repositories need post-`v0.1.1` features such as the
  external Lean library reference adapter, cut and validate a later tag first.

### License

- [x] `LICENSE` contains Apache License 2.0.
- [x] README license text states Apache License 2.0.
- [x] `pyproject.toml` project metadata uses `Apache-2.0`.

### CI And Local Verification

Run these before release or showcase PRs:

- [ ] `make lint`
- [ ] `make typecheck`
- [ ] `make test`
- [ ] `make validate`
- [ ] `make gate`
- [ ] `git diff --check`
- [ ] GitHub Actions checks pass for the release or showcase PR.

Skipped verifier output is not a pass. Optional-tool skips must stay visible in
gate output and release notes.

### Validate/Gate Status

- [ ] `cosheaf validate` passes on the framework checkout.
- [ ] `cosheaf gate run` passes or reports only intentional nonblocking
  skipped/not-applicable gates.
- [ ] `cosheaf gate run --pr-checklist <local-pr-body.md>` passes before a PR
  is marked ready when a local PR body draft is available.
- [ ] Gate reports are generated under `.cosheaf/reports/` and are not
  committed unless explicitly persisted for review.

### Demo Status

- [ ] `python scripts/release_smoke.py --source
  git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.1.1` runs against a
  clean environment when network access is available.
- [ ] `python scripts/ecosystem_smoke.py --cosheaf cosheaf` runs without
  cloning remote repositories.
- [ ] The ecosystem smoke covers a readonly public KB root, writable private KB
  root, private draft depending on public accepted knowledge, validation,
  gatekeeper, index rebuild, and context-pack generation.
- [ ] Expected policy failures in smoke helpers are verified as failures, not
  described as passes.

## Workspace Template Checklist

- [ ] The template remains the recommended user entry point.
- [ ] The one-command demo runs from a clean clone.
- [ ] Makefile shortcuts remain thin wrappers around documented `cosheaf`
  commands.
- [ ] `kb/public` is documented as seed/demo content unless replaced or mounted
  from `tcs-kb-public`.
- [ ] `kb/private` is documented as the writable private research overlay.
- [ ] The docs warn users not to manually merge framework, public KB, and
  private workspace repositories into one mixed tree.
- [ ] Runtime output stays ignored under `.cosheaf/` or another ignored runtime
  directory.

## Public KB Checklist

- [ ] Public KB accepted artifacts have complete structured source metadata.
- [ ] Public KB accepted artifacts have human review records or explicit
  maintainer review evidence.
- [ ] Validation and gate success are recorded as checks, not as substitutes
  for human review.
- [ ] No accepted public artifact depends on private or draft artifacts.
- [ ] No private conjecture, unpublished idea, or unreviewed LLM output is
  committed under accepted public KB paths.
- [ ] Source-note conventions and foundation backlog stay updated before
  adding new accepted theorem/proof-sketch batches.

## Public/Private Policy Status

- Public KB roots are readonly from downstream workspaces.
- Private KB roots are writable overlays.
- Private artifacts may depend on public accepted artifacts.
- Public artifacts must not depend on private artifacts.
- Accepted artifacts must not depend on draft or otherwise pre-accepted
  artifacts, even across KB roots.
- Readonly KB roots must reject lifecycle write commands.

## Formal Link Status

Implemented framework surfaces on current `main`:

- Artifact metadata fields: `formalizations`, `alignment`, and
  `verification_policy`.
- Formal library manifest metadata and schema.
- G10 Formal Link Gate metadata and verifier-result consistency checks.
- Context-pack display of formal-link metadata.
- SQLite/index/query formal-link surfaces.
- Optional external Lean library reference checker for generated
  `import <module>` / `#check <symbol>` runs when Lean or lake is available.

The `v0.1.1` tag includes formal-link metadata, G10, context, index, and query
surfaces, but it does not include the later `LeanLibraryRefAdapter`. A future
tag is required before downstream pinned work can rely on that adapter.

Boundaries:

- Formal links are metadata unless a verifier actually runs and records a
  result.
- Planned formal links do not mean Lean has checked anything.
- A successful external Lean `#check` means the import and symbol resolved; it
  does not prove informal/formal semantic alignment.
- Alignment review remains human-reviewed metadata.
- Missing Lean/lake is `skipped`, not `pass`.
- Cosheaf does not fetch CSLib/mathlib or vendor Lean proof bodies.

## Hosted LLM Status

- Hosted LLM/model-provider worker execution is not implemented.
- The model provider surface is provider-neutral and currently uses a
  deterministic fake provider for tests and disabled hosted-runtime paths.
- The orchestrator dry-run is local-only and does not call network services,
  request human review, merge worker outputs, or promote accepted knowledge.

## Known Limitations

- Pre-MVP framework, not production software.
- No web UI.
- No automatic theorem-proving agent.
- No full Lean autoformalization.
- No automatic informal/formal semantic alignment checking.
- No multi-user permission system.
- External public KB integration is through local workspace roots, not a hosted
  registry service.
- SAT, SMT, plain Lean, and external Lean reference adapters are intentionally
  minimal optional invocation paths.
- MarkItDown, Headroom, CodeGraph, and Understand-Anything are optional or
  manual developer surfaces and are not source-of-truth dependencies.

## Non-Goals For This Release-Hardening Phase

- Do not add a web UI.
- Do not add a large agent runtime.
- Do not make hosted LLM calls part of default workflows.
- Do not mass-import public KB artifacts.
- Do not change accepted-promotion semantics.
- Do not treat validation, gatekeeper, formal links, or skipped verifier
  results as human review or proof.
