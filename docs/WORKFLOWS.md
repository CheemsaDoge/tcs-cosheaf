# Reviewable Workflows

`v0.9.0` starts the reviewable-workflow line. The goal is to make Cosheaf build
human-review-ready research packets from an issue while keeping generated
material in draft or review-context state.

The intended end-to-end workflow is:

```text
issue -> librarian context -> FSM plan -> bounded local loop -> evidence/failure
summary -> draft proposal -> review handoff -> benchmark report
```

## Current Surface

The current framework exposes the persistent workflow core from V14 B.1:

```bash
cosheaf workflow start --issue <issue-id> --query <query> --json
cosheaf workflow show <workflow-id> --json
cosheaf workflow step <workflow-id> --json
cosheaf workflow run <workflow-id> --max-steps <n> --execute-local-actions --json
cosheaf workflow readiness <workflow-id> --json
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

The current implementation lives under:

```text
cosheaf/workflow/engine.py
cosheaf/workflow/cli.py
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
```

These files are runtime review context. They are not YAML source-of-truth
artifacts and must not be treated as accepted knowledge.

## Not Implemented Yet

The following V14 targets are not complete in the current `v0.9.0` release:

- draft proposal generation from workflow output;
- workflow handoff build/show/scan/export commands;
- workflow scanner integration for private leakage, accepted-write attempts,
  hidden reasoning markers, provider payloads, source fabrication, and
  authority overclaims;
- `cosheaf eval reviewable-workflow --json`;
- workspace-template `make reviewable-workflow-demo`;
- public-KB policy guard for workflow packets as non-source metadata.

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
