# Post-v0.10.0 State Audit

Date: 2026-06-18

This audit closes the V15 Cross-Check Evidence + Checker Registry line and
records the evidence needed before starting V16. It is documentation only. It
does not implement campaign runtime, add schemas, add dependencies, change CLI
behavior, bump the package version, write KB artifacts, create tags, or publish
releases.

## Release State

- Package metadata records `0.10.0` in `pyproject.toml`.
- `cosheaf.__version__` records `0.10.0`.
- `python -m cosheaf.cli version --json` reports `0.10.0`.
- The public `v0.10.0` tag exists and points through the annotated tag to the
  reviewed release-candidate commit.
- GitHub release `v0.10.0 - Cross-Check Evidence + Checker Registry` is
  published:
  <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.10.0>.
- Post-tag release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.10.0` passed and
  installed `tcs-cosheaf==0.10.0`.
- `docs/releases/v0.10.0.md` records the release as published and explicitly
  keeps checker/cross-check/gap output non-authoritative.

## V15 Completion Evidence

Framework current `main` includes:

- `cosheaf checker list/describe/run/run-suite`;
- checker-run sidecars under ignored `.cosheaf/checker-runs/` paths;
- `cosheaf workflow cross-check <workflow-id> --json`;
- `cosheaf workflow evidence-report <workflow-id> --json`;
- `cosheaf workflow export-crosscheck <workflow-id> --out reviews/workflow/<name>.json --json`;
- `cosheaf gap list <workflow-id> --json`;
- `cosheaf gap export <workflow-id> --out reviews/workflow/<name>.json --json`;
- proof/source/formalization gap taxonomy in `cosheaf.workflow.crosscheck`;
- workflow handoff `review_gaps` summaries derived from the gap report;
- `cosheaf eval checker-crosscheck --json`;
- tests for checker CLI/registry, workflow cross-check reports, and
  checker/cross-check eval; and
- ecosystem smoke row `framework.checker-crosscheck-eval`.

Workspace-template downstream is aligned:

- active install/demo pins use the published `v0.10.0` tag;
- PR #85 added the cross-check demo path;
- PR #87 aligned active framework pins to `@v0.10.0`;
- demos write runtime outputs under ignored `.cosheaf/` paths; and
- demos do not write public KB content, accepted artifacts, human review,
  source metadata, verifier results, gate results, or promotion.

Public KB downstream is aligned:

- CI installs `tcs-cosheaf` from the published `v0.10.0` tag;
- PR #99 extends the local public KB policy guard so cross-check reports,
  evidence reports, gap reports, checker sidecars, and checker/cross-check eval
  reports cannot be claimed as source metadata, accepted proof, human review,
  verifier pass, gate pass, accepted status, accepted theorem/refutation, or
  promotion authority;
- PR #101 aligned CI/docs pins to `@v0.10.0`; and
- no KB artifacts, review records, schemas, workflow files, formalization
  metadata, or accepted statuses were changed by the downstream policy guard.

At audit time, open PR lists for all three repositories were empty. Open issue
lists were empty before issue #446 was created to track this V16 kickoff.

## Authority Boundary

V15 does not make checker registry entries, checker sidecars, workflow records,
cross-check reports, evidence reports, gap reports, handoff summaries, eval
reports, or downstream policy checks into:

- proof;
- source metadata;
- human review;
- verifier pass unless a real checker result explicitly records pass;
- gate pass;
- accepted status;
- accepted theorem/refutation;
- promotion authority.

Skipped, unsupported, unavailable, and inconclusive checker or smoke results
remain non-pass evidence and must not be counted as passes.

## V16 Entry Decision

V15 is complete enough to start V16 Phase A. The next line is external AI
operator campaigns: bounded multi-run campaign records, external operator
task/result packets, deterministic budget control, campaign handoff, and
campaign eval. V16 must keep the operator external and keep Cosheaf as the
deterministic controller, recorder, scanner, budget enforcer, and review
handoff builder. It must not add internal hosted-provider autonomy, accepted
writes, human-review creation, promotion authority, arbitrary shell execution,
or default network/API-key requirements.
