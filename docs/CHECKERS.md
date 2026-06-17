# Checker Registry

V15 adds a typed local checker registry for review-context evidence. A checker
run records what was checked, which checker ran, the normalized result status,
stdout/stderr log paths, and the authority boundary attached to the result.

Checker output is not accepted knowledge. A checker pass is not proof, human
review, source metadata, gate pass, verifier pass, accepted status, accepted
theorem/refutation, or promotion authority. A skipped checker is not a pass.

## CLI

```bash
cosheaf checker list --json
cosheaf checker describe schema_check --json
cosheaf checker run schema_check --input-json checker-input.json --json
cosheaf checker run-suite --input-json checker-input.json --json
```

Checker runs are written under:

```text
.cosheaf/checker-runs/<run-id>/result.json
.cosheaf/checker-runs/<run-id>/stdout.txt
.cosheaf/checker-runs/<run-id>/stderr.txt
```

These are runtime sidecars and should remain ignored unless a later workflow
explicitly exports them as review context.

## Input

The shared input packet is intentionally small:

```json
{
  "schema_version": 1,
  "artifact_id": "claim.example",
  "artifact_path": "kb/draft/claims/claim.example.yaml",
  "paths": ["kb/draft/claims/claim.example.yaml"],
  "text": "review-context text to scan",
  "mode": "workspace",
  "payload": {}
}
```

Individual checkers may use only a subset of those fields. Unsupported input
returns `unsupported` rather than pretending to pass.

## Statuses

- `pass`: the checker completed and its local criterion passed.
- `fail`: the checker completed and found a substantive failure.
- `error`: the checker could not complete because of a runtime or tool error.
- `skipped`: an optional checker did not run, usually because a tool is absent.
- `inconclusive`: the checker ran but cannot decide the requested property.
- `unsupported`: the input does not match the checker surface.
- `blocked_by_policy`: the checker refused unsafe or overclaiming input.

Only `fail`, `error`, and `blocked_by_policy` are blocking for the checker CLI.
`skipped`, `inconclusive`, and `unsupported` are not passes.

## Built-In Checkers

- `schema_check`
- `artifact_path_policy_check`
- `gate_check`
- `python_local_check`
- `sat_optional_check`
- `smt_optional_check`
- `lean_optional_check`
- `source_metadata_check`
- `private_leak_check`
- `authority_overclaim_check`

The optional SAT, SMT, and Lean checkers do not make those tools mandatory in
CI. Missing tools are reported as `skipped`. Availability alone is
`inconclusive`; it does not prove a claim or informal/formal alignment.

`python_local_check` runs only an explicit repository-local Python script from
`payload.script_path`. It is not an arbitrary shell surface.

