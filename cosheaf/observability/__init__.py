"""Optional local observability adapters."""

from __future__ import annotations

from cosheaf.observability.otel import (
    OTelExportError,
    OTelExportResult,
    OTelSpanExporter,
    OTelTelemetryConfig,
    emit_run_log_span,
    run_log_span_attributes,
)

__all__ = [
    "OTelExportError",
    "OTelExportResult",
    "OTelSpanExporter",
    "OTelTelemetryConfig",
    "emit_run_log_span",
    "run_log_span_attributes",
]
