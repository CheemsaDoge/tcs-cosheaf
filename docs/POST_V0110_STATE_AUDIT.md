# Post-v0.11.0 State Audit

Date: 2026-06-18

This audit closes the V16 External Operator Campaigns line and records the
evidence needed before starting V17. It is documentation only. It does not
implement memory update runtime, add schemas, add dependencies, change CLI
behavior, bump the package version, write KB artifacts, create tags, or publish
releases.

## Release State

- Package metadata records `0.11.0` in `pyproject.toml`.
- `cosheaf.__version__` records `0.11.0`.
- `python -m cosheaf.cli version --json` reports `0.11.0`.
- The annotated `v0.11.0` tag exists as tag object
  `640b503b9421555c277dd722f125a389ceb9efc5`.
- The tag peels to main commit
  `b04a34bf1a1b27310e64625a3d9be3a84998e622`.
- GitHub release `v0.11.0 External Operator Campaigns` is published:
  <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.11.0>.
- Post-tag release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.11.0` passed and
  installed `tcs-cosheaf==0.11.0`.
- `docs/releases/v0.11.0.md` records the release as published and explicitly
  keeps campaign outputs non-authoritative.

## V16 Completion Evidence

Framework current `main` includes:

- `cosheaf campaign start/show/append-attempt/scorecard/finalize`;
- `cosheaf campaign next/export-task/import-result`;
- `cosheaf campaign pause/resume/scan/run`;
- `cosheaf campaign handoff <campaign-id> --out <dir> --json`;
- `cosheaf eval campaign --json`;
- runtime campaign sidecars under ignored `.cosheaf/campaigns/` paths;
- tests for campaign models, storage, CLI, budget controller, scanner,
  handoff, and eval; and
- ecosystem smoke row `framework.campaign-eval`.

`python -m cosheaf.cli eval campaign --json` reports four passing campaign
eval cases with `accepted_write_violation_count: 0`.

Workspace-template downstream is aligned:

- active install/demo pins use the published `v0.11.0` tag;
- PR #89 added `make campaign-demo`;
- PR #91 aligned active framework pins to `@v0.11.0`;
- demos write runtime outputs under ignored `.cosheaf/` paths; and
- demos do not write public KB content, accepted artifacts, human review,
  source metadata, verifier results, gate results, or promotion.

Public KB downstream is aligned:

- CI installs `tcs-cosheaf` from the published `v0.11.0` tag;
- PR #103 added campaign-output policy guard coverage;
- PR #105 aligned CI/docs pins to `@v0.11.0`; and
- no KB artifacts, review records, schemas, workflow files, formalization
  metadata, or accepted statuses were changed by the downstream pin closeout.

At audit time, open PR and issue lists for all three repositories were empty
before issue #460 was created to track this V17 kickoff.

## Authority Boundary

V16 does not make campaign records, attempts, scorecards, scans, operator
packets, handoffs, campaign eval reports, downstream demos, or public KB policy
guards into:

- proof;
- source metadata;
- human review;
- verifier pass unless a real checker result explicitly records pass;
- gate pass;
- accepted status;
- accepted theorem/refutation; or
- promotion authority.

Skipped, unsupported, unavailable, and inconclusive results remain non-pass
evidence and must not be counted as passes.

## V17 Entry Decision

V16 is complete enough to start V17 Phase A. The next line is deterministic
research memory learning and benchmark suite v1: sidecar memory updates,
stable benchmark suites, comparative reports, and static review reports.
V17 must not train a model, mutate YAML artifact truth, create accepted status,
create human review, grant promotion authority, or make benchmark success a
truth claim.
