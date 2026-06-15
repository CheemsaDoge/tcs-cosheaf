"""Deterministic research-run loop boundary eval harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PureWindowsPath

import yaml  # type: ignore[import-untyped]
from pydantic import field_validator

from cosheaf.memory.models import MemoryModel
from cosheaf.research.run import (
    RESEARCH_RUN_AUTHORITY_NOTICE,
    SKIPPED_RESEARCH_RUN_LIMITATION,
    ResearchRunCommandRecord,
    ResearchRunCommandStatus,
    ResearchRunOutputKind,
    ResearchRunOutputRef,
    ResearchRunRecord,
)
from cosheaf.storage.repo import RepoContext

DEFAULT_RESEARCH_RUN_LOOP_EVAL_CASES = (
    Path("evals") / "research_run_loop" / "cases.yaml"
)


class ResearchRunLoopEvalError(ValueError):
    """Raised for expected research-run eval loading failures."""


class ResearchRunLoopEvalKind(StrEnum):
    """Supported research-run loop scenarios."""

    COMPLETE_COMMAND_COVERAGE = "complete_command_coverage"
    SKIPPED_NOT_PASS = "skipped_not_pass"
    EVIDENCE_SEPARATION = "evidence_separation"
    PRIVATE_LEAKAGE_PREVENTION = "private_leakage_prevention"
    NO_AUTHORITY_ESCALATION = "no_authority_escalation"


class ResearchRunLoopEvalCase(MemoryModel):
    """One deterministic research-run eval case."""

    id: str | None = None
    kind: ResearchRunLoopEvalKind

    @field_validator("id")
    @classmethod
    def _id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("case id must be non-empty")
        return normalized


class ResearchRunLoopEvalCaseResult(MemoryModel):
    """One research-run eval case result."""

    id: str
    kind: ResearchRunLoopEvalKind
    passed: bool
    command_coverage: bool = False
    skipped_not_pass: bool = False
    evidence_separated: bool = False
    private_leak_count: int = 0
    authority_escalation: bool = False
    accepted_write_performed: bool = False
    failures: list[str]


class ResearchRunLoopEvalMetrics(MemoryModel):
    """Aggregate research-run eval metrics."""

    command_coverage_accuracy: float
    skipped_not_pass_count: int
    evidence_separation_count: int
    private_leak_count: int
    authority_escalation_count: int
    accepted_write_violation_count: int


class ResearchRunLoopEvalReport(MemoryModel):
    """Research-run eval report."""

    schema_version: int = 1
    kind: str = "research_run_loop_eval"
    case_count: int
    passed: bool
    metrics: ResearchRunLoopEvalMetrics
    cases: list[ResearchRunLoopEvalCaseResult]
    authority_notice: str = RESEARCH_RUN_AUTHORITY_NOTICE

    def to_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
        ) + "\n"


@dataclass(frozen=True)
class ResearchRunLoopEvalSuite:
    """Loaded research-run eval cases."""

    cases: list[ResearchRunLoopEvalCase]


def resolve_research_run_loop_eval_case_path(
    context: RepoContext,
    cases_path: Path,
) -> Path:
    """Resolve explicit or default research-run eval case path."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ResearchRunLoopEvalError(
            "research-run eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(
        cases_path
    ).is_absolute():
        raise ResearchRunLoopEvalError(
            "research-run eval case file must be repository-local"
        )
    return resolved


def load_research_run_loop_eval_suite(path: Path) -> ResearchRunLoopEvalSuite:
    """Load research-run eval cases from YAML."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ResearchRunLoopEvalError(f"could not read eval cases: {path}") from exc
    if not isinstance(raw, dict):
        raise ResearchRunLoopEvalError("research-run eval cases must be a mapping")
    cases_raw = raw.get("cases")
    if not isinstance(cases_raw, list):
        raise ResearchRunLoopEvalError("research-run eval cases require a cases list")
    cases = [ResearchRunLoopEvalCase.model_validate(item) for item in cases_raw]
    return ResearchRunLoopEvalSuite(cases=cases)


def run_research_run_loop_eval_suite(
    context: RepoContext,
    suite: ResearchRunLoopEvalSuite,
) -> ResearchRunLoopEvalReport:
    """Run deterministic research-run loop boundary eval cases."""
    _ = context
    results = [_run_case(case) for case in suite.cases]
    case_count = len(results)
    command_cases = [
        result
        for result in results
        if result.kind is ResearchRunLoopEvalKind.COMPLETE_COMMAND_COVERAGE
    ]
    command_accuracy = (
        sum(1 for result in command_cases if result.command_coverage)
        / len(command_cases)
        if command_cases
        else 1.0
    )
    metrics = ResearchRunLoopEvalMetrics(
        command_coverage_accuracy=command_accuracy,
        skipped_not_pass_count=sum(
            1 for result in results if result.skipped_not_pass
        ),
        evidence_separation_count=sum(
            1 for result in results if result.evidence_separated
        ),
        private_leak_count=sum(result.private_leak_count for result in results),
        authority_escalation_count=sum(
            1 for result in results if result.authority_escalation
        ),
        accepted_write_violation_count=sum(
            1 for result in results if result.accepted_write_performed
        ),
    )
    return ResearchRunLoopEvalReport(
        case_count=case_count,
        passed=all(result.passed for result in results),
        metrics=metrics,
        cases=results,
    )


def _run_case(case: ResearchRunLoopEvalCase) -> ResearchRunLoopEvalCaseResult:
    record = _record()
    failures: list[str] = []
    command_coverage = False
    skipped_not_pass = False
    evidence_separated = False
    private_leak_count = 0
    authority_escalation = False
    accepted_write_performed = False

    if case.kind is ResearchRunLoopEvalKind.COMPLETE_COMMAND_COVERAGE:
        command_coverage = bool(record.commands)
        if not command_coverage:
            failures.append("expected at least one recorded command")
    elif case.kind is ResearchRunLoopEvalKind.SKIPPED_NOT_PASS:
        skipped = ResearchRunCommandRecord(
            argv=("lean", "missing.lean"),
            cwd=".",
            started_at=datetime(2026, 6, 15, 1, 0, tzinfo=UTC),
            status=ResearchRunCommandStatus.SKIPPED,
            skipped_reason=SKIPPED_RESEARCH_RUN_LIMITATION,
        )
        skipped_not_pass = skipped.status == "skipped" and skipped.exit_code is None
        if not skipped_not_pass:
            failures.append("expected skipped command to remain non-pass evidence")
    elif case.kind is ResearchRunLoopEvalKind.EVIDENCE_SEPARATION:
        evidence_separated = bool(record.checked_counterexample_evidence_paths)
        evidence_separated = evidence_separated and not record.accepted_write_performed
        if not evidence_separated:
            failures.append("expected checked evidence to remain review evidence")
    elif case.kind is ResearchRunLoopEvalKind.PRIVATE_LEAKAGE_PREVENTION:
        private_marker = "private-secret-research-run-marker"
        serialized = record.to_json()
        private_leak_count = 1 if private_marker in serialized else 0
        if private_leak_count:
            failures.append("private marker leaked into research-run record")
    elif case.kind is ResearchRunLoopEvalKind.NO_AUTHORITY_ESCALATION:
        authority_escalation = (
            record.accepted_write_performed
            or "human_reviewed" in record.to_json()
            or "promotion_authority" in record.to_json()
        )
        if authority_escalation:
            failures.append("research-run record escalated authority")
    else:  # pragma: no cover - StrEnum exhaustiveness guard
        failures.append(f"unsupported research-run eval case: {case.kind}")

    return ResearchRunLoopEvalCaseResult(
        id=case.id or f"case.research-run.{case.kind.value}",
        kind=case.kind,
        passed=not failures,
        command_coverage=command_coverage,
        skipped_not_pass=skipped_not_pass,
        evidence_separated=evidence_separated,
        private_leak_count=private_leak_count,
        authority_escalation=authority_escalation,
        accepted_write_performed=accepted_write_performed,
        failures=failures,
    )


def _record() -> ResearchRunRecord:
    started = datetime(2026, 6, 15, 1, 0, tzinfo=UTC)
    command = ResearchRunCommandRecord(
        argv=("cosheaf", "validate"),
        cwd=".",
        started_at=started,
        ended_at=datetime(2026, 6, 15, 1, 1, tzinfo=UTC),
        exit_code=0,
        status=ResearchRunCommandStatus.COMPLETED,
        stdout_path=".cosheaf/runs/run.issue.fixture.eval/stdout.txt",
        stderr_path=".cosheaf/runs/run.issue.fixture.eval/stderr.txt",
    )
    evidence = ResearchRunOutputRef(
        kind=ResearchRunOutputKind.CHECKED_COUNTEREXAMPLE_EVIDENCE,
        path=(
            "reviews/evidence/checked-counterexamples/"
            "checked-counterexample.claim.fixture.candidate.fixture.habc123.yaml"
        ),
        identifier="checked-counterexample.claim.fixture.candidate.fixture.habc123",
        status="completed",
        summary="checked evidence staged for review",
    )
    return ResearchRunRecord.start(
        run_id="run.issue.fixture.eval",
        issue_id="issue.fixture",
        operator_kind="external",
        operator_label="eval fixture",
        now=started,
    ).with_command(command).with_output(evidence)


__all__ = [
    "DEFAULT_RESEARCH_RUN_LOOP_EVAL_CASES",
    "ResearchRunLoopEvalCase",
    "ResearchRunLoopEvalCaseResult",
    "ResearchRunLoopEvalError",
    "ResearchRunLoopEvalKind",
    "ResearchRunLoopEvalMetrics",
    "ResearchRunLoopEvalReport",
    "ResearchRunLoopEvalSuite",
    "load_research_run_loop_eval_suite",
    "resolve_research_run_loop_eval_case_path",
    "run_research_run_loop_eval_suite",
]
