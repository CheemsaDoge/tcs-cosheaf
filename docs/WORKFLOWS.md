# Reviewable Workflows

`v0.9.0` starts the reviewable-workflow line. The goal is to make Cosheaf build
human-review-ready research packets from an issue while keeping generated
material in draft or review-context state.

The intended end-to-end workflow is:

```text
issue -> librarian context -> FSM plan -> bounded local loop -> evidence/failure
summary -> draft proposal -> review handoff -> benchmark report
```

## Current v0.9.0 Surface

The published `v0.9.0` framework exposes an initial `cosheaf workflow` CLI:

```bash
cosheaf workflow start --issue <issue-id> --query <query> --json
cosheaf workflow step <workflow-id> --json
cosheaf workflow readiness <workflow-id> --json
```

Current behavior:

- `workflow start` emits a workflow JSON record with issue, query, timestamps,
  status, and an explicit authority notice.
- `workflow step` currently emits an ephemeral step status message; it does not
  yet persist the step to workflow storage.
- `workflow readiness` currently emits an ephemeral readiness message; it does
  not yet load a persisted workflow record or produce the full readiness
  classifier planned in the V14 plan.

The current implementation lives under:

```text
cosheaf/workflow/engine.py
cosheaf/workflow/cli.py
```

## Planned Runtime Layout

The intended persisted runtime layout remains:

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

- persistent workflow storage and replay under `.cosheaf/workflows/`;
- `workflow show`;
- bounded `workflow run --max-steps ... --execute-local-actions`;
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
