# Post-v0.9.0 State Audit

Date: 2026-06-18

This audit closes the V14 reviewable-workflow line and records the evidence
needed before starting V15. It is documentation only. It does not implement the
checker registry, add schemas, bump the package version, or change promotion,
human-review, verifier, gate, or accepted-write authority.

## Release State

- Package metadata records `0.9.0` in `pyproject.toml`.
- `cosheaf.__version__` records `0.9.0`.
- `python -m cosheaf.cli version --json` reports `0.9.0`.
- The public `v0.9.0` tag exists.
- GitHub release `v0.9.0 - Reviewable Research Workflow MVP` is published:
  <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.9.0>.
- `docs/releases/v0.9.0.md` records the release as published and explicitly
  keeps workflow output non-authoritative.

The `v0.9.0` tag contains the initial reviewable-workflow surface. Later V14
follow-ups on `main` added persistent workflow runtime storage, draft proposal
generation, workflow handoffs, scanner coverage, and deterministic evals. Those
follow-ups are current `main` state, not a retroactive claim about the tag
contents.

## V14 Completion Evidence

Framework current `main` includes:

- `cosheaf workflow start/show/step/run/readiness`;
- `cosheaf workflow draft-proposal`;
- `cosheaf workflow handoff build/show/scan/export`;
- `cosheaf eval reviewable-workflow --json`;
- ecosystem smoke row `framework.reviewable-workflow-eval`;
- workflow handoff scanner guards for accepted-write, source-metadata,
  human-review, verifier/gate, private-leak, provider-payload, hidden-reasoning,
  and accepted theorem/refutation overclaims.

Workspace-template downstream is aligned:

- active install pins use `v0.9.0`;
- PR #83 added `make reviewable-workflow-demo`;
- the demo writes only ignored runtime outputs and dry-run review context;
- the demo does not write public KB content, accepted artifacts, human review,
  source metadata, verifier results, gate results, or promotion.

Public KB downstream is aligned:

- CI installs `tcs-cosheaf` from `v0.9.0`;
- PR #97 extends the local public KB policy guard so reviewable-workflow
  packets cannot be claimed as source metadata, accepted proof, or human
  review;
- no KB artifacts, review records, schemas, workflow files, formalization
  metadata, or accepted statuses were changed by the downstream policy guard.

At audit time, open PR lists for all three repositories were empty. Existing
older framework issues remain outside this V15 landing scope and should be
triaged separately before any release freeze that requires stale issue cleanup.

## Authority Boundary

V14 does not make workflow, proposal, handoff, scanner, eval, operator, MCP,
provider, loop, task, or campaign-like output into:

- proof;
- source metadata;
- human review;
- verifier pass;
- gate pass;
- accepted status;
- accepted theorem/refutation;
- promotion authority.

Skipped verifier, provider, workflow, or smoke rows remain skipped and must not
be counted as passes.

## V15 Entry Decision

V14 is complete enough to start V15 Phase A. The next line is the
Cross-Check Evidence and Checker Registry work. V15 must start with design,
typed registry boundaries, and review-only cross-check reports. It must not
turn checker output into human review or accepted knowledge.
