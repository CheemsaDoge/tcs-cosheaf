# Observability

Cosheaf observability is local and file-based by default. It is meant to make
dry-run workflows auditable without requiring OpenTelemetry, hosted services,
network access, or external collectors.

## Structured Run Logs

`cosheaf orchestrator run --issue <issue-id> --dry-run --local-only` writes two
run-level records under:

```text
.cosheaf/orchestrator/<issue-id>/runs/<run-id>/
```

The existing `run.yaml` remains the detailed orchestrator state-machine record.
The structured observability record is:

```text
run_log.json
```

`run_log.json` is deterministic JSON with these top-level fields:

- `schema_version`
- `run_id`
- `issue_id`
- `plan_id`
- `task_ids`
- `worker_roles`
- `retrieved_artifacts`
- `full_artifact_pulls`
- `verifier_results`
- `gate_results`
- `output_bundle_paths`
- `start_time`
- `end_time`
- `status`
- `stop_reason`
- `worker_calls`

The current local orchestrator dry-run does not execute gatekeeper or verifier
adapters, so `gate_results` and `verifier_results` are empty unless a future
explicit workflow records those paths. The default dry-run context is
cards-only, so `full_artifact_pulls` is empty unless a future run explicitly
records full-artifact pulls.

## Safety Boundaries

Structured run logs are audit metadata only. They are not proof, verifier
evidence, source review, human review, accepted-promotion evidence, or
authorization to merge worker outputs.

Logs must not include:

- secret values
- stdout or stderr contents
- hidden chain-of-thought or private reasoning
- accepted-knowledge writes

Worker command argv metadata is recorded after local redaction of common secret
flags and token-like values. Stdout and stderr contents remain in the existing
per-worker files referenced by the lower-level task runner; `run_log.json` does
not inline those contents.

## Local-Only Mode

Structured logging does not change local-only execution semantics. The
orchestrator runner still:

- uses explicit local argv commands with `shell=False`
- writes under `.cosheaf/`
- keeps hosted LLMs disabled
- avoids network services
- does not run gates implicitly
- does not request human review
- does not write accepted knowledge
- does not promote artifacts

## Optional OpenTelemetry Adapter

Cosheaf includes a small optional OpenTelemetry-style adapter in
`cosheaf.observability.otel`. It does not import or require the OpenTelemetry
SDK, does not configure a collector, and does not export anything unless a
caller explicitly enables telemetry and provides an exporter object.

The adapter exposes:

- `OTelTelemetryConfig(enabled=False, strict=False)`
- `OTelSpanExporter`
- `emit_run_log_span(run_log, exporter=..., config=...)`
- `run_log_span_attributes(run_log)`

Default behavior is disabled:

```python
result = emit_run_log_span(run_log, exporter=my_exporter)
assert result.exported is False
```

Enabled export maps safe run metadata to span attributes such as:

- `cosheaf.run_id`
- `cosheaf.issue_id`
- `cosheaf.plan_id`
- `cosheaf.task_ids`
- `cosheaf.worker_roles`
- `cosheaf.retrieved_artifacts`
- `cosheaf.full_artifact_pulls`
- `cosheaf.verifier_results`
- `cosheaf.gate_results`
- `cosheaf.output_bundle_paths`
- `cosheaf.status`
- `cosheaf.stop_reason`

The adapter intentionally does not export worker command argv, stdout, stderr,
hidden reasoning, or secret values. Export failures are nonfatal by default and
are returned as `OTelExportResult(error=...)`. Only
`OTelTelemetryConfig(strict=True)` turns exporter failure into
`OTelExportError`.

Tests use fake exporters only. No external collector is required.
