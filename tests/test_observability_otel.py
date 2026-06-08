from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from cosheaf.agent.run_logging import RunLogWorkerCall, StructuredRunLog
from cosheaf.observability.otel import (
    OTelExportError,
    OTelSpanExporter,
    OTelTelemetryConfig,
    emit_run_log_span,
)


@dataclass(frozen=True)
class FakeSpan:
    name: str
    attributes: dict[str, object]


class FakeExporter(OTelSpanExporter):
    def __init__(self) -> None:
        self.spans: list[FakeSpan] = []

    def export_span(self, name: str, attributes: dict[str, object]) -> None:
        self.spans.append(FakeSpan(name=name, attributes=attributes))


class FailingExporter(OTelSpanExporter):
    def export_span(self, name: str, attributes: dict[str, object]) -> None:
        raise RuntimeError(f"export failed for {name}")


def _run_log() -> StructuredRunLog:
    timestamp = datetime(2026, 6, 8, tzinfo=UTC)
    return StructuredRunLog(
        run_id="run.issue.fixture.otel",
        issue_id="issue.fixture.otel",
        plan_id="plan.issue.fixture.otel",
        task_ids=["task.node.issue.fixture.otel.reasoner"],
        worker_roles=["reasoner"],
        retrieved_artifacts=["claim.fixture.otel"],
        full_artifact_pulls=[],
        verifier_results=[".cosheaf/reports/verifier.json"],
        gate_results=[".cosheaf/reports/gate.json"],
        output_bundle_paths=[".cosheaf/orchestrator/issue.fixture.otel/bundle.yaml"],
        start_time=timestamp,
        end_time=timestamp,
        status="completed",
        stop_reason="completed",
        worker_calls=[
            RunLogWorkerCall(
                call_id="call.node.issue.fixture.otel.reasoner",
                task_node_id="node.issue.fixture.otel.reasoner",
                worker_role="reasoner",
                status="completed",
                command=["worker", "--api-key", "<redacted>"],
                cwd=".",
                exit_code=0,
                bundle_path=".cosheaf/orchestrator/issue.fixture.otel/bundle.yaml",
            )
        ],
    )


def test_otel_adapter_disabled_by_default_does_not_export() -> None:
    exporter = FakeExporter()

    result = emit_run_log_span(_run_log(), exporter=exporter)

    assert result.enabled is False
    assert result.exported is False
    assert result.error is None
    assert exporter.spans == []


def test_otel_adapter_exports_run_ids_with_fake_exporter() -> None:
    exporter = FakeExporter()

    result = emit_run_log_span(
        _run_log(),
        exporter=exporter,
        config=OTelTelemetryConfig(enabled=True),
    )

    assert result.enabled is True
    assert result.exported is True
    assert result.error is None
    assert len(exporter.spans) == 1
    span = exporter.spans[0]
    assert span.name == "cosheaf.orchestrator.run"
    attributes = span.attributes
    assert attributes["cosheaf.run_id"] == "run.issue.fixture.otel"
    assert attributes["cosheaf.issue_id"] == "issue.fixture.otel"
    assert attributes["cosheaf.plan_id"] == "plan.issue.fixture.otel"
    assert attributes["cosheaf.task_ids"] == "task.node.issue.fixture.otel.reasoner"
    assert attributes["cosheaf.worker_roles"] == "reasoner"
    assert attributes["cosheaf.retrieved_artifacts"] == "claim.fixture.otel"
    assert attributes["cosheaf.verifier_results"] == ".cosheaf/reports/verifier.json"
    assert attributes["cosheaf.gate_results"] == ".cosheaf/reports/gate.json"
    assert attributes["cosheaf.status"] == "completed"
    assert attributes["cosheaf.stop_reason"] == "completed"
    assert "<redacted>" not in str(attributes)
    assert "api-key" not in str(attributes).lower()


def test_otel_export_failure_is_nonfatal_unless_strict() -> None:
    result = emit_run_log_span(
        _run_log(),
        exporter=FailingExporter(),
        config=OTelTelemetryConfig(enabled=True, strict=False),
    )

    assert result.enabled is True
    assert result.exported is False
    assert result.error == "export failed for cosheaf.orchestrator.run"

    with pytest.raises(OTelExportError, match="export failed"):
        emit_run_log_span(
            _run_log(),
            exporter=FailingExporter(),
            config=OTelTelemetryConfig(enabled=True, strict=True),
        )
