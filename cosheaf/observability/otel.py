"""Optional OpenTelemetry-style adapter for structured Cosheaf run logs.

This module intentionally does not import or require the OpenTelemetry SDK.
Callers may bridge ``OTelSpanExporter`` to a real SDK exporter in a separate
integration. Tests use fake exporters only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from cosheaf.agent.run_logging import StructuredRunLog

SPAN_NAME = "cosheaf.orchestrator.run"


class OTelExportError(ValueError):
    """Raised when strict telemetry export fails."""


class OTelSpanExporter(Protocol):
    """Minimal protocol for optional span exporters."""

    def export_span(self, name: str, attributes: dict[str, object]) -> None:
        """Export one span with already-sanitized attributes."""


@dataclass(frozen=True)
class OTelTelemetryConfig:
    """Configuration for optional telemetry export."""

    enabled: bool = False
    strict: bool = False


@dataclass(frozen=True)
class OTelExportResult:
    """Outcome for one optional telemetry export attempt."""

    enabled: bool
    exported: bool
    error: str | None = None


def emit_run_log_span(
    run_log: StructuredRunLog,
    *,
    exporter: OTelSpanExporter | None = None,
    config: OTelTelemetryConfig | None = None,
) -> OTelExportResult:
    """Optionally export one sanitized run-log span.

    Export is disabled by default. Non-strict export failures are reported in
    the returned result instead of failing the local research workflow.
    """
    resolved_config = config or OTelTelemetryConfig()
    if not resolved_config.enabled:
        return OTelExportResult(enabled=False, exported=False)
    if exporter is None:
        return OTelExportResult(
            enabled=True,
            exported=False,
            error="no exporter configured",
        )

    try:
        exporter.export_span(SPAN_NAME, run_log_span_attributes(run_log))
    except Exception as exc:
        message = str(exc)
        if resolved_config.strict:
            raise OTelExportError(message) from exc
        return OTelExportResult(enabled=True, exported=False, error=message)

    return OTelExportResult(enabled=True, exported=True)


def run_log_span_attributes(run_log: StructuredRunLog) -> dict[str, object]:
    """Return sanitized span attributes derived from a structured run log."""
    return {
        "cosheaf.run_id": run_log.run_id,
        "cosheaf.issue_id": run_log.issue_id,
        "cosheaf.plan_id": run_log.plan_id or "",
        "cosheaf.task_ids": _join(run_log.task_ids),
        "cosheaf.worker_roles": _join(run_log.worker_roles),
        "cosheaf.retrieved_artifacts": _join(run_log.retrieved_artifacts),
        "cosheaf.full_artifact_pulls": _join(run_log.full_artifact_pulls),
        "cosheaf.verifier_results": _join(run_log.verifier_results),
        "cosheaf.gate_results": _join(run_log.gate_results),
        "cosheaf.output_bundle_paths": _join(run_log.output_bundle_paths),
        "cosheaf.start_time": run_log.start_time.isoformat(),
        "cosheaf.end_time": run_log.end_time.isoformat(),
        "cosheaf.status": run_log.status,
        "cosheaf.stop_reason": run_log.stop_reason,
        "cosheaf.worker_call_count": len(run_log.worker_calls),
    }


def _join(values: list[str]) -> str:
    return ",".join(values)
