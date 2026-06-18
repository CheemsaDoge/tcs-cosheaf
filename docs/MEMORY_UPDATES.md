# Memory Updates

V17 Phase B adds deterministic memory update sidecars. They turn persisted
workflow and campaign history into bounded edge weights for later retrieval and
planning.

Memory updates are operational guidance only. They are not proof, source
metadata, human review, verifier pass, gate pass, accepted status, accepted
theorem/refutation status, or promotion authority.

## Commands

```bash
cosheaf memory update-from-workflow <workflow-id> --json
cosheaf memory update-from-campaign <campaign-id> --json
cosheaf memory rebuild --json
cosheaf memory explain <artifact-id> --json
```

`update-from-workflow` and `update-from-campaign` write one deterministic update
run under:

```text
.cosheaf/memory/update-runs/<run-id>.json
```

They then rebuild aggregate weights under:

```text
.cosheaf/memory/weights.json
```

`rebuild` reads all update runs and recreates `weights.json`. `explain` reads
`weights.json` and shows edges touching the requested artifact ID.

## Signals

The v1 policy uses a small fixed vocabulary:

- `retrieved`
- `used_in_plan`
- `used_in_attempt`
- `used_in_successful_draft`
- `checker_pass`
- `checker_fail`
- `gate_blocked`
- `review_requested`
- `human_accept_reference`
- `repeat_failure`
- `unsafe_output`

Signals have deterministic bounded deltas. Aggregate weights are clamped to the
configured range and can be rebuilt from update-run sidecars.

## Boundaries

Memory updates do not mutate YAML artifacts. They write only ignored `.cosheaf/`
runtime sidecars. They do not write accepted KB content, create human review,
fabricate source metadata, mutate verifier results, mark gates as passing, call
hosted providers, execute shell commands, or promote artifacts.

Negative signals such as `checker_fail`, `gate_blocked`, `repeat_failure`, and
`unsafe_output` are not proof of refutation. They are routing hints for future
review and planning.
