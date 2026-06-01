"""Validation and gatekeeper report orchestration."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from cosheaf.gates.dependency_gate import (
    validate_dependencies,
    validate_id_uniqueness,
)
from cosheaf.gates.schema_gate import (
    ValidationFailure,
    load_schema_valid_record,
    load_schema_valid_records,
    sort_failures,
)
from cosheaf.gates.status_gate import (
    validate_evidence_paths,
    validate_status_paths,
)
from cosheaf.storage.loader import LoadedRecord
from cosheaf.storage.repo import RepoContext

GateStatus = Literal["pass", "fail", "skipped", "not_applicable"]
GateVerdict = Literal["pass", "fail"]


@dataclass(frozen=True)
class ValidationReport:
    """Validation result for a repository or a single artifact file."""

    records: tuple[LoadedRecord, ...]
    failures: tuple[ValidationFailure, ...]

    @property
    def ok(self) -> bool:
        return not self.failures

    @property
    def checked_count(self) -> int:
        return len(self.records)


def validate_repository(context: RepoContext) -> ValidationReport:
    """Validate a repository checkout using the implemented MVP gates."""
    schema_result = load_schema_valid_records(context)
    records = schema_result.records
    failures: list[ValidationFailure] = list(schema_result.failures)
    failures.extend(validate_id_uniqueness(records))
    failures.extend(validate_status_paths(records))
    failures.extend(validate_dependencies(records))
    failures.extend(validate_evidence_paths(context, records))

    return ValidationReport(records=records, failures=sort_failures(failures))


def validate_artifact_file(context: RepoContext, path: Path) -> ValidationReport:
    """Validate one YAML file with file-local checks."""
    schema_result = load_schema_valid_record(context, path)
    records = schema_result.records
    failures: list[ValidationFailure] = list(schema_result.failures)
    failures.extend(validate_status_paths(records))
    failures.extend(validate_evidence_paths(context, records))

    return ValidationReport(records=records, failures=sort_failures(failures))


@dataclass(frozen=True)
class GateIssue:
    """A blocking or nonblocking issue recorded in a gatekeeper report."""

    gate_id: str
    gate_name: str
    source_path: str
    artifact_id: str
    message: str
    severity: Literal["blocking", "nonblocking"]

    def to_dict(self) -> dict[str, str]:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "source_path": self.source_path,
            "artifact_id": self.artifact_id,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class GateResult:
    """One gate result in a gatekeeper run."""

    gate_id: str
    name: str
    status: GateStatus
    summary: str
    blocking_issues: tuple[GateIssue, ...] = ()
    nonblocking_issues: tuple[GateIssue, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.gate_id,
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
            "blocking_issues": [
                issue.to_dict() for issue in self.blocking_issues
            ],
            "nonblocking_issues": [
                issue.to_dict() for issue in self.nonblocking_issues
            ],
        }


@dataclass(frozen=True)
class GatekeeperReport:
    """Machine-readable gatekeeper report."""

    verdict: GateVerdict
    blocking_issues: tuple[GateIssue, ...]
    nonblocking_issues: tuple[GateIssue, ...]
    summary: dict[str, int | str]
    started_at: str
    ended_at: str
    gates: tuple[GateResult, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict,
            "blocking_issues": [
                issue.to_dict() for issue in self.blocking_issues
            ],
            "nonblocking_issues": [
                issue.to_dict() for issue in self.nonblocking_issues
            ],
            "summary": self.summary,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "gates": [gate.to_dict() for gate in self.gates],
        }


@dataclass(frozen=True)
class GatekeeperRunResult:
    """Report and written report paths for a gatekeeper run."""

    report: GatekeeperReport
    json_path: Path
    markdown_path: Path
    review_json_path: Path | None = None
    review_markdown_path: Path | None = None


def run_gatekeeper(
    context: RepoContext,
    *,
    persist_review: bool = False,
    timestamp: str | None = None,
) -> GatekeeperRunResult:
    """Run all current gates and write machine/human-readable reports."""
    started = datetime.now(UTC)
    started_at = _format_report_time(started)
    report_timestamp = timestamp or started.strftime("%Y%m%dT%H%M%S%fZ")

    schema_result = load_schema_valid_records(context)
    records = schema_result.records
    gates = (
        _gate_from_failures(
            gate_id="G1",
            name="schema gate",
            failures=schema_result.failures,
            pass_summary=(
                f"Schema/model parsing passed for {len(records)} loaded record(s)."
            ),
        ),
        _gate_from_failures(
            gate_id="G2",
            name="ID uniqueness gate",
            failures=validate_id_uniqueness(records),
            pass_summary="All loaded record IDs are globally unique.",
        ),
        _gate_from_failures(
            gate_id="G3",
            name="status/path gate",
            failures=validate_status_paths(records),
            pass_summary="All loaded artifact statuses match their paths.",
        ),
        _gate_from_failures(
            gate_id="G4",
            name="dependency gate",
            failures=validate_dependencies(records),
            pass_summary="All loaded artifact dependencies are valid.",
        ),
        _gate_from_failures(
            gate_id="G5",
            name="evidence path gate",
            failures=validate_evidence_paths(context, records),
            pass_summary="All local evidence paths exist.",
        ),
        _placeholder_gate("G6", "verifier gate placeholder"),
        _placeholder_gate("G7", "reproducibility metadata gate placeholder"),
        _placeholder_gate("G8", "PR checklist gate placeholder"),
    )

    blocking_issues = tuple(
        issue for gate in gates for issue in gate.blocking_issues
    )
    nonblocking_issues = tuple(
        issue for gate in gates for issue in gate.nonblocking_issues
    )
    ended_at = _format_report_time(datetime.now(UTC))
    report = GatekeeperReport(
        verdict="fail" if blocking_issues else "pass",
        blocking_issues=blocking_issues,
        nonblocking_issues=nonblocking_issues,
        summary={
            "records_checked": len(records),
            "gates_total": len(gates),
            "gates_passed": sum(1 for gate in gates if gate.status == "pass"),
            "gates_failed": sum(1 for gate in gates if gate.status == "fail"),
            "gates_skipped": sum(1 for gate in gates if gate.status == "skipped"),
            "gates_not_applicable": sum(
                1 for gate in gates if gate.status == "not_applicable"
            ),
            "blocking_issue_count": len(blocking_issues),
            "nonblocking_issue_count": len(nonblocking_issues),
        },
        started_at=started_at,
        ended_at=ended_at,
        gates=gates,
    )

    report_dir = context.resolve(".cosheaf/reports")
    json_path, markdown_path = _write_report_files(
        report_dir=report_dir,
        timestamp=report_timestamp,
        report=report,
    )

    review_json_path: Path | None = None
    review_markdown_path: Path | None = None
    if persist_review:
        review_dir = context.resolve("reviews/gatekeeper")
        review_json_path, review_markdown_path = _copy_report_files(
            json_path=json_path,
            markdown_path=markdown_path,
            review_dir=review_dir,
        )

    return GatekeeperRunResult(
        report=report,
        json_path=json_path,
        markdown_path=markdown_path,
        review_json_path=review_json_path,
        review_markdown_path=review_markdown_path,
    )


def _gate_from_failures(
    *,
    gate_id: str,
    name: str,
    failures: tuple[ValidationFailure, ...] | list[ValidationFailure],
    pass_summary: str,
) -> GateResult:
    issues = tuple(_issue_from_failure(gate_id, name, failure) for failure in failures)
    if issues:
        return GateResult(
            gate_id=gate_id,
            name=name,
            status="fail",
            summary=f"{len(issues)} blocking issue(s).",
            blocking_issues=issues,
        )
    return GateResult(
        gate_id=gate_id,
        name=name,
        status="pass",
        summary=pass_summary,
    )


def _placeholder_gate(gate_id: str, name: str) -> GateResult:
    issue = GateIssue(
        gate_id=gate_id,
        gate_name=name,
        source_path="",
        artifact_id="",
        message="Gate is specified but not implemented yet.",
        severity="nonblocking",
    )
    return GateResult(
        gate_id=gate_id,
        name=name,
        status="skipped",
        summary="Skipped: gate is specified but not implemented yet.",
        nonblocking_issues=(issue,),
    )


def _issue_from_failure(
    gate_id: str,
    gate_name: str,
    failure: ValidationFailure,
) -> GateIssue:
    return GateIssue(
        gate_id=gate_id,
        gate_name=gate_name,
        source_path=failure.source_path,
        artifact_id=failure.artifact_id,
        message=failure.message,
        severity="blocking",
    )


def _write_report_files(
    *,
    report_dir: Path,
    timestamp: str,
    report: GatekeeperReport,
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{timestamp}-gate-report.json"
    markdown_path = report_dir / f"{timestamp}-gate-report.md"
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown_report(report), encoding="utf-8")
    return json_path, markdown_path


def _copy_report_files(
    *,
    json_path: Path,
    markdown_path: Path,
    review_dir: Path,
) -> tuple[Path, Path]:
    review_dir.mkdir(parents=True, exist_ok=True)
    review_json_path = review_dir / json_path.name
    review_markdown_path = review_dir / markdown_path.name
    shutil.copyfile(json_path, review_json_path)
    shutil.copyfile(markdown_path, review_markdown_path)
    return review_json_path, review_markdown_path


def _render_markdown_report(report: GatekeeperReport) -> str:
    lines = [
        "# Gatekeeper Report",
        "",
        f"- Verdict: {report.verdict}",
        f"- Started at: {report.started_at}",
        f"- Ended at: {report.ended_at}",
        "",
        "## Summary",
        "",
    ]
    for key, value in report.summary.items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Gates", ""])
    for gate in report.gates:
        lines.append(f"- {gate.gate_id} {gate.name}: {gate.status}")
        lines.append(f"  - {gate.summary}")

    lines.extend(["", "## Blocking Issues", ""])
    if report.blocking_issues:
        for issue in report.blocking_issues:
            lines.append(_format_markdown_issue(issue))
    else:
        lines.append("- None")

    lines.extend(["", "## Nonblocking Issues", ""])
    if report.nonblocking_issues:
        for issue in report.nonblocking_issues:
            lines.append(_format_markdown_issue(issue))
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


def _format_markdown_issue(issue: GateIssue) -> str:
    location = issue.source_path or "-"
    artifact_id = issue.artifact_id or "-"
    return (
        f"- {issue.gate_id} {issue.gate_name} | {location} | "
        f"{artifact_id} | {issue.message}"
    )


def _format_report_time(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")

