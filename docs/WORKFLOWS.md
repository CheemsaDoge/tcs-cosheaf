# Reviewable Workflows

`v0.9.0` starts the reviewable-workflow line. The goal is to make Cosheaf build
human-review-ready research packets from an issue while keeping generated
material in draft or review-context state.

The intended end-to-end workflow is:

```text
issue -> librarian context -> FSM plan -> bounded local loop -> evidence/failure
summary -> draft proposal -> cross-check/gap report -> review handoff ->
benchmark report
```

## Current Surface

The current framework exposes the persistent workflow core from V14 B.1:

```bash
cosheaf workflow start --issue <issue-id> --query <query> --json
cosheaf workflow show <workflow-id> --json
cosheaf workflow step <workflow-id> --json
cosheaf workflow run <workflow-id> --max-steps <n> --execute-local-actions --json
cosheaf workflow readiness <workflow-id> --json
cosheaf workflow draft-proposal <workflow-id> --dry-run --json
cosheaf workflow draft-proposal <workflow-id> --out <path> --json
cosheaf workflow draft-proposal <workflow-id> --private-root <path> --artifact-id <artifact-id> --json
cosheaf workflow handoff build <workflow-id> --json
cosheaf workflow handoff show <handoff-id> --json
cosheaf workflow handoff scan <handoff-id> --json
cosheaf workflow handoff export <handoff-id> --dry-run --json
cosheaf workflow cross-check <workflow-id> --json
cosheaf workflow evidence-report <workflow-id> --json
cosheaf workflow export-crosscheck <workflow-id> --out reviews/workflow/<name>.md --json
cosheaf gap list <workflow-id> --json
cosheaf gap export <workflow-id> --out reviews/workflow/<name>.json --json
cosheaf eval reviewable-workflow --json
```

Current behavior:

- `workflow start` persists `.cosheaf/workflows/<workflow-id>/workflow.json`,
  initializes `events.jsonl`, writes placeholder component files for
  librarian/FSM/loop review context, and records an explicit authority notice.
- `workflow show` reads one persisted workflow record.
- `workflow step` appends one deterministic step and records a bounded event.
  By default it records a planned step; `--execute-local-action` runs only an
  action from the whitelisted local action registry.
- `workflow run` executes a bounded number of workflow steps. With
  `--execute-local-actions`, it still uses only the whitelisted local action
  registry and forbids accepted writes, network, hosted providers, and arbitrary
  shell.
- `workflow readiness` loads persisted workflow state and classifies it as
  `ready_for_draft_proposal`, a specific blocker class, or `inconclusive`.
- `workflow draft-proposal` converts persisted workflow output into a
  review-only draft proposal. `--dry-run` writes nothing, `--out` writes
  review-context JSON under a safe repository-local non-public path, and
  `--private-root ... --artifact-id ...` writes a draft claim YAML under a
  writable private draft root. It refuses accepted and public KB targets.
- `workflow handoff build` converts persisted workflow and draft-proposal
  output into a compact runtime human-review handoff. It scans workflow inputs
  first, fails closed on blocking scanner findings, writes
  `.cosheaf/workflows/<workflow-id>/handoff.json`, and records scanner status
  in `.cosheaf/workflows/<workflow-id>/handoff-scan.json`.
- `workflow handoff show` reads one persisted workflow handoff. The
  deterministic handoff ID is `handoff.<workflow-id>`.
- `workflow handoff scan` scans workflow runtime and handoff JSON for
  accepted-write attempts, private leakage, hidden reasoning, provider payload
  dumps, secrets/env dumps, human-review overclaims, verifier/gate pass
  overclaims, source metadata fabrication, and accepted theorem/refutation
  claims without promotion. Blocking findings make the command exit nonzero
  after emitting JSON.
- `workflow handoff export --dry-run` reports the deterministic
  review-context target `reviews/workflow/<handoff-id>.yaml` without writing
  files. Non-dry-run export writes only under `reviews/workflow/` after a clean
  scan and still does not create human review.
- `workflow cross-check` builds a deterministic review-context matrix from
  workflow steps, relevant checker-run sidecars, and draft proposal candidate
  claims. It writes `.cosheaf/workflows/<workflow-id>/crosscheck.json` and
  `crosscheck.md`. Checked-pass items remain non-authoritative; skipped,
  inconclusive, and unsupported outputs are not passes.
- `workflow evidence-report` wraps the cross-check report together with
  generated gap counts for quick reviewer inspection.
- `workflow export-crosscheck` writes explicit review-context `.json` or `.md`
  output only under `reviews/workflow/` after the authority scanner passes.
  It rejects accepted KB targets and does not create human review.
- `gap list` and `gap export` build review-guidance gap reports from the
  workflow cross-check report. Gap kinds include proof, source,
  formalization, semantic alignment, review, and reproducibility gaps. Gaps are
  triage guidance, not proof or defects by themselves.
- `eval reviewable-workflow` runs deterministic temporary fixtures for
  accepted dependency plus draft target, repeated failure memory, unchecked
  counterexample, private leakage risk, scanner blocker, and
  draft-proposal-ready cases. It reports benchmark metrics only and writes no
  accepted knowledge in the caller repository.

The current implementation lives under:

```text
cosheaf/workflow/engine.py
cosheaf/workflow/cli.py
cosheaf/workflow/proposal.py
cosheaf/workflow/handoff.py
cosheaf/workflow/crosscheck.py
cosheaf/gap_cli.py
cosheaf/evals/reviewable_workflow.py
```

## Runtime Layout

Workflow runtime records are written under ignored `.cosheaf/` paths:

```text
.cosheaf/workflows/<workflow-id>/workflow.json
.cosheaf/workflows/<workflow-id>/events.jsonl
.cosheaf/workflows/<workflow-id>/librarian.json
.cosheaf/workflows/<workflow-id>/fsm.json
.cosheaf/workflows/<workflow-id>/loop.json
.cosheaf/workflows/<workflow-id>/readiness.json
.cosheaf/workflows/<workflow-id>/proposal.json
.cosheaf/workflows/<workflow-id>/handoff.json
.cosheaf/workflows/<workflow-id>/handoff-scan.json
.cosheaf/workflows/<workflow-id>/crosscheck.json
.cosheaf/workflows/<workflow-id>/crosscheck.md
.cosheaf/workflows/<workflow-id>/gaps.json
```

These files are runtime review context. They are not YAML source-of-truth
artifacts and must not be treated as accepted knowledge.

Private draft artifact proposals may also be written under a writable private
root, for example:

```text
kb/private/draft/claims/<artifact-id>.yaml
```

Those files are still draft artifacts. They are not source reviewed, human
reviewed, accepted, or promoted by the proposal command.

Cross-check and gap reports may also be exported under `reviews/workflow/`.
Those exports are explicit review context only. They are not public KB source
metadata, verifier evidence, human review records, accepted proof, accepted
refutation, gate pass, or promotion authority.

## Downstream Status

The V14 downstream workflow closeout has landed:

- workspace-template PR #83 adds `make reviewable-workflow-demo`;
- public KB PR #97 guards against using workflow packets as source metadata,
  accepted proof, or human review.

Those downstream changes do not change the framework authority boundary and do
not make workflow packets accepted knowledge.

## Authority Boundary

Workflow output is review context only. It is not:

- proof;
- source metadata;
- human review;
- verifier pass;
- gate pass;
- accepted status;
- accepted refutation;
- promotion authority.

Skipped verifier output remains skipped, not pass. Any accepted artifact still
requires the ordinary validation, gate, human-review, source-metadata, and
promotion workflow.

Checker sidecars and cross-check reports can make a review packet easier to
inspect, but they do not close semantic-alignment gaps. A successful local
checker result records only that the checker criterion passed; it does not make
an informal statement true or aligned with a formal reference.
