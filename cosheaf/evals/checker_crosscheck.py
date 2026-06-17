"""Deterministic checker/cross-check eval harness."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import field_validator

from cosheaf.checkers.builtins import default_checker_registry
from cosheaf.checkers.models import CheckerInput, CheckerResult, CheckerStatus
from cosheaf.checkers.registry import CheckerExecution
from cosheaf.checkers.storage import store_checker_execution
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.crosscheck import (
    CrossCheckClassification,
    build_crosscheck_report,
    build_gap_report,
    scan_crosscheck_report_text,
)
from cosheaf.workflow.engine import (
    WorkflowStep,
    append_step,
    load_workflow,
    start_workflow,
    workflow_root,
    write_workflow,
)

DEFAULT_CHECKER_CROSSCHECK_EVAL_CASES = (
    Path("evals") / "checker_crosscheck" / "cases.yaml"
)

ISSUE_ID = "issue.eval.checker-crosscheck"


class CheckerCrossCheckEvalError(ValueError):
    """Raised for expected checker/cross-check eval loading failures."""


class CheckerCrossCheckEvalKind(StrEnum):
    """Supported checker/cross-check eval scenarios."""

    VALID_CHECKED_LOCAL_CLAIM = "valid_checked_local_claim"
    FAILED_CHECKER_CLAIM = "failed_checker_claim"
    SKIPPED_OPTIONAL_CHECKER = "skipped_optional_checker"
    OVERCLAIMED_ACCEPTED_PROOF = "overclaimed_accepted_proof"
    PRIVATE_LEAKAGE_IN_CROSSCHECK = "private_leakage_in_crosscheck"
    SOURCE_GAP = "source_gap"
    FORMALIZATION_GAP = "formalization_gap"
    INCONCLUSIVE_EVIDENCE = "inconclusive_evidence"


class CheckerCrossCheckEvalCase(MemoryModel):
    """One deterministic checker/cross-check eval case."""

    id: str | None = None
    kind: CheckerCrossCheckEvalKind

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("case id must be non-empty")
        return normalized


class CheckerCrossCheckEvalSuite(MemoryModel):
    """A small collection of checker/cross-check eval cases."""

    schema_version: Literal[1] = 1
    cases: list[CheckerCrossCheckEvalCase]

    @field_validator("cases")
    @classmethod
    def _validate_cases(
        cls,
        values: list[CheckerCrossCheckEvalCase],
    ) -> list[CheckerCrossCheckEvalCase]:
        if not values:
            raise ValueError("cases must not be empty")
        return values


class CheckerCrossCheckEvalCaseResult(MemoryModel):
    """One checker/cross-check eval case result."""

    id: str
    kind: CheckerCrossCheckEvalKind
    passed: bool
    checked_pass_seen: bool = False
    checked_fail_seen: bool = False
    inconclusive_seen: bool = False
    skipped_not_pass: bool = False
    inconclusive_not_pass: bool = False
    authority_overclaim_rejected: bool = False
    private_leak_rejected: bool = False
    source_gap_detected: bool = False
    formalization_gap_detected: bool = False
    semantic_alignment_gap_detected: bool = False
    checked_pass_not_accepted: bool = False
    human_review_created: bool = False
    source_metadata_created: bool = False
    accepted_write_performed: bool = False
    failures: list[str]


class CheckerCrossCheckEvalMetrics(MemoryModel):
    """Aggregate checker/cross-check eval metrics."""

    case_pass_rate: float
    checked_pass_boundary_rate: float
    failed_checker_detection_rate: float
    authority_overclaim_rejection_rate: float
    private_leak_rejection_rate: float
    source_gap_detection_rate: float
    formalization_gap_detection_rate: float
    skipped_not_pass_count: int
    inconclusive_not_pass_count: int
    accepted_write_violation_count: int


class CheckerCrossCheckEvalReport(MemoryModel):
    """Checker/cross-check eval report."""

    schema_version: Literal[1] = 1
    kind: Literal["checker_crosscheck_eval"] = "checker_crosscheck_eval"
    case_count: int
    passed: bool
    metrics: CheckerCrossCheckEvalMetrics
    cases: list[CheckerCrossCheckEvalCaseResult]

    def to_json(self) -> str:
        """Return deterministic JSON for the report."""

        return json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
        ) + "\n"


@dataclass(frozen=True)
class _Observation:
    checked_pass_seen: bool
    checked_fail_seen: bool
    inconclusive_seen: bool
    skipped_not_pass: bool
    inconclusive_not_pass: bool
    authority_overclaim_rejected: bool
    private_leak_rejected: bool
    source_gap_detected: bool
    formalization_gap_detected: bool
    semantic_alignment_gap_detected: bool
    checked_pass_not_accepted: bool
    human_review_created: bool
    source_metadata_created: bool
    accepted_write_performed: bool


def load_checker_crosscheck_eval_suite(path: Path) -> CheckerCrossCheckEvalSuite:
    """Load checker/cross-check eval cases from YAML."""

    if not path.exists():
        raise CheckerCrossCheckEvalError(
            f"checker/cross-check eval case file not found: {path}"
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise CheckerCrossCheckEvalError(
            f"cannot read checker/cross-check eval case file: {exc}"
        ) from exc
    if data is None:
        raise CheckerCrossCheckEvalError("checker/cross-check eval case file is empty")
    try:
        return CheckerCrossCheckEvalSuite.model_validate(data)
    except ValueError as exc:
        raise CheckerCrossCheckEvalError(
            f"invalid checker/cross-check eval case file: {exc}"
        ) from exc


def resolve_checker_crosscheck_eval_case_path(
    context: RepoContext,
    cases_path: Path,
) -> Path:
    """Resolve and constrain the case file path to the repository root."""

    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise CheckerCrossCheckEvalError(
            "checker/cross-check eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(
        cases_path
    ).is_absolute():
        raise CheckerCrossCheckEvalError(
            "checker/cross-check eval case file must be repository-local"
        )
    return resolved


def run_checker_crosscheck_eval_suite(
    context: RepoContext,
    suite: CheckerCrossCheckEvalSuite,
) -> CheckerCrossCheckEvalReport:
    """Run every checker/cross-check eval case."""

    _ = context
    results = [
        run_checker_crosscheck_eval_case(case, case_index=index)
        for index, case in enumerate(suite.cases, start=1)
    ]
    metrics = CheckerCrossCheckEvalMetrics(
        case_pass_rate=_rate_all(results, "passed"),
        checked_pass_boundary_rate=_rate_selected(
            results,
            {CheckerCrossCheckEvalKind.VALID_CHECKED_LOCAL_CLAIM},
            "checked_pass_not_accepted",
        ),
        failed_checker_detection_rate=_rate_selected(
            results,
            {CheckerCrossCheckEvalKind.FAILED_CHECKER_CLAIM},
            "checked_fail_seen",
        ),
        authority_overclaim_rejection_rate=_rate_selected(
            results,
            {CheckerCrossCheckEvalKind.OVERCLAIMED_ACCEPTED_PROOF},
            "authority_overclaim_rejected",
        ),
        private_leak_rejection_rate=_rate_selected(
            results,
            {CheckerCrossCheckEvalKind.PRIVATE_LEAKAGE_IN_CROSSCHECK},
            "private_leak_rejected",
        ),
        source_gap_detection_rate=_rate_selected(
            results,
            {CheckerCrossCheckEvalKind.SOURCE_GAP},
            "source_gap_detected",
        ),
        formalization_gap_detection_rate=_rate_selected(
            results,
            {CheckerCrossCheckEvalKind.FORMALIZATION_GAP},
            "formalization_gap_detected",
        ),
        skipped_not_pass_count=sum(1 for result in results if result.skipped_not_pass),
        inconclusive_not_pass_count=sum(
            1 for result in results if result.inconclusive_not_pass
        ),
        accepted_write_violation_count=sum(
            1 for result in results if result.accepted_write_performed
        ),
    )
    return CheckerCrossCheckEvalReport(
        case_count=len(results),
        passed=all(result.passed for result in results),
        metrics=metrics,
        cases=results,
    )


def run_checker_crosscheck_eval_case(
    case: CheckerCrossCheckEvalCase,
    *,
    case_index: int = 1,
) -> CheckerCrossCheckEvalCaseResult:
    """Run and score one checker/cross-check eval case."""

    with tempfile.TemporaryDirectory(prefix="cosheaf-checker-crosscheck-eval-") as tmp:
        context = RepoContext(Path(tmp))
        _write_fixture(context.repo_root)
        workflow_id = _workflow_id(case.kind)
        start_workflow(
            context,
            issue_id=ISSUE_ID,
            query=_query_for_case(case.kind),
            workflow_id=workflow_id,
        )
        _append_workflow_step(context, workflow_id, case.kind)
        _attach_case_checkers(context, workflow_id, case.kind)
        observation = _observe_case(context, workflow_id, case.kind)

    failures = _case_failures(case.kind, observation)
    return CheckerCrossCheckEvalCaseResult(
        id=case.id or f"case.checker-crosscheck.{case_index:04d}",
        kind=case.kind,
        passed=not failures,
        checked_pass_seen=observation.checked_pass_seen,
        checked_fail_seen=observation.checked_fail_seen,
        inconclusive_seen=observation.inconclusive_seen,
        skipped_not_pass=observation.skipped_not_pass,
        inconclusive_not_pass=observation.inconclusive_not_pass,
        authority_overclaim_rejected=observation.authority_overclaim_rejected,
        private_leak_rejected=observation.private_leak_rejected,
        source_gap_detected=observation.source_gap_detected,
        formalization_gap_detected=observation.formalization_gap_detected,
        semantic_alignment_gap_detected=(
            observation.semantic_alignment_gap_detected
        ),
        checked_pass_not_accepted=observation.checked_pass_not_accepted,
        human_review_created=observation.human_review_created,
        source_metadata_created=observation.source_metadata_created,
        accepted_write_performed=observation.accepted_write_performed,
        failures=failures,
    )


def _attach_case_checkers(
    context: RepoContext,
    workflow_id: str,
    kind: CheckerCrossCheckEvalKind,
) -> None:
    if kind is CheckerCrossCheckEvalKind.VALID_CHECKED_LOCAL_CLAIM:
        _store_checker_status(
            context,
            workflow_id,
            "python_local_check",
            CheckerStatus.PASS,
            "local fixture checker passed",
        )
        _store_checker_status(
            context,
            workflow_id,
            "source_metadata_check",
            CheckerStatus.PASS,
            "source metadata present in fixture",
        )
    elif kind is CheckerCrossCheckEvalKind.FAILED_CHECKER_CLAIM:
        _store_checker_status(
            context,
            workflow_id,
            "python_local_check",
            CheckerStatus.FAIL,
            "local fixture checker failed",
        )
    elif kind is CheckerCrossCheckEvalKind.SKIPPED_OPTIONAL_CHECKER:
        _store_checker_status(
            context,
            workflow_id,
            "lean_optional_check",
            CheckerStatus.SKIPPED,
            "optional Lean tool unavailable in fixture",
        )
    elif kind is CheckerCrossCheckEvalKind.OVERCLAIMED_ACCEPTED_PROOF:
        _store_checker_status(
            context,
            workflow_id,
            "authority_overclaim_check",
            CheckerStatus.BLOCKED_BY_POLICY,
            "authority overclaim blocked by policy fixture",
        )
    elif kind is CheckerCrossCheckEvalKind.PRIVATE_LEAKAGE_IN_CROSSCHECK:
        _store_checker_status(
            context,
            workflow_id,
            "private_leak_check",
            CheckerStatus.BLOCKED_BY_POLICY,
            "private leak blocked by policy fixture",
        )
    elif kind is CheckerCrossCheckEvalKind.SOURCE_GAP:
        _store_checker_status(
            context,
            workflow_id,
            "source_metadata_check",
            CheckerStatus.FAIL,
            "source metadata missing in fixture",
        )
    elif kind is CheckerCrossCheckEvalKind.FORMALIZATION_GAP:
        _store_checker_status(
            context,
            workflow_id,
            "lean_optional_check",
            CheckerStatus.FAIL,
            "optional formal checker failed in fixture",
        )
    elif kind is CheckerCrossCheckEvalKind.INCONCLUSIVE_EVIDENCE:
        _store_checker_status(
            context,
            workflow_id,
            "smt_optional_check",
            CheckerStatus.INCONCLUSIVE,
            "optional SMT availability is inconclusive in fixture",
        )
    else:  # pragma: no cover - StrEnum exhaustiveness guard
        raise CheckerCrossCheckEvalError(f"unsupported checker eval kind: {kind}")


def _observe_case(
    context: RepoContext,
    workflow_id: str,
    kind: CheckerCrossCheckEvalKind,
) -> _Observation:
    report = build_crosscheck_report(context, workflow_id)
    gaps = build_gap_report(context, workflow_id, crosscheck_report=report)
    checker_items = [
        item for item in report.matrix.items if item.item_kind == "checker_run"
    ]
    checked_pass_seen = report.matrix.status_counts.get(
        CrossCheckClassification.CHECKED_PASS.value,
        0,
    ) > 0
    checked_fail_seen = report.matrix.status_counts.get(
        CrossCheckClassification.CHECKED_FAIL.value,
        0,
    ) > 0
    inconclusive_seen = report.matrix.status_counts.get(
        CrossCheckClassification.INCONCLUSIVE.value,
        0,
    ) > 0
    skipped_not_pass = any(
        item.checker_status == CheckerStatus.SKIPPED.value
        and item.classification is CrossCheckClassification.INCONCLUSIVE
        for item in checker_items
    )
    inconclusive_not_pass = any(
        item.checker_status
        in {CheckerStatus.INCONCLUSIVE.value, CheckerStatus.UNSUPPORTED.value}
        and item.classification is CrossCheckClassification.INCONCLUSIVE
        for item in checker_items
    )
    checker_statuses = {
        item.checker_id: item.checker_status for item in checker_items
    }
    gap_kinds = {gap.kind.value for gap in gaps.gaps}
    overclaim_codes = {
        finding["code"]
        for finding in scan_crosscheck_report_text(
            "This report proves an accepted theorem, creates human review, "
            "claims gate_pass=true, and says source metadata confirmed."
        )
    }
    return _Observation(
        checked_pass_seen=checked_pass_seen,
        checked_fail_seen=checked_fail_seen,
        inconclusive_seen=inconclusive_seen,
        skipped_not_pass=skipped_not_pass,
        inconclusive_not_pass=inconclusive_not_pass,
        authority_overclaim_rejected=(
            kind is CheckerCrossCheckEvalKind.OVERCLAIMED_ACCEPTED_PROOF
            and checker_statuses.get("authority_overclaim_check")
            == CheckerStatus.BLOCKED_BY_POLICY.value
            and {
                "accepted_theorem_or_refutation",
                "human_review_overclaim",
                "verifier_gate_overclaim",
                "source_metadata_fabrication",
            }
            <= overclaim_codes
        ),
        private_leak_rejected=(
            checker_statuses.get("private_leak_check")
            == CheckerStatus.BLOCKED_BY_POLICY.value
        ),
        source_gap_detected="source_gap" in gap_kinds,
        formalization_gap_detected="formalization_gap" in gap_kinds,
        semantic_alignment_gap_detected="semantic_alignment_gap" in gap_kinds,
        checked_pass_not_accepted=(
            checked_pass_seen
            and report.checked_pass_is_accepted is False
            and report.human_review_created is False
            and report.source_metadata_created is False
            and report.accepted_status_created is False
            and report.promotion_performed is False
        ),
        human_review_created=report.human_review_created,
        source_metadata_created=report.source_metadata_created,
        accepted_write_performed=(
            report.accepted_status_created
            or report.promotion_performed
            or (context.repo_root / "kb" / "accepted").exists()
        ),
    )


def _case_failures(
    kind: CheckerCrossCheckEvalKind,
    observation: _Observation,
) -> list[str]:
    failures: list[str] = []
    if kind is CheckerCrossCheckEvalKind.VALID_CHECKED_LOCAL_CLAIM:
        if not observation.checked_pass_seen:
            failures.append("expected at least one checked-pass evidence row")
        if not observation.checked_pass_not_accepted:
            failures.append("expected checked pass to remain non-accepted")
    elif kind is CheckerCrossCheckEvalKind.FAILED_CHECKER_CLAIM:
        if not observation.checked_fail_seen:
            failures.append("expected failed checker row")
    elif kind is CheckerCrossCheckEvalKind.SKIPPED_OPTIONAL_CHECKER:
        if not observation.skipped_not_pass:
            failures.append("expected skipped checker to be inconclusive, not pass")
    elif kind is CheckerCrossCheckEvalKind.OVERCLAIMED_ACCEPTED_PROOF:
        if not observation.authority_overclaim_rejected:
            failures.append("expected authority overclaim rejection")
    elif kind is CheckerCrossCheckEvalKind.PRIVATE_LEAKAGE_IN_CROSSCHECK:
        if not observation.private_leak_rejected:
            failures.append("expected private leak rejection")
    elif kind is CheckerCrossCheckEvalKind.SOURCE_GAP:
        if not observation.source_gap_detected:
            failures.append("expected source gap detection")
    elif kind is CheckerCrossCheckEvalKind.FORMALIZATION_GAP:
        if not observation.formalization_gap_detected:
            failures.append("expected formalization gap detection")
        if not observation.semantic_alignment_gap_detected:
            failures.append("expected semantic-alignment gap detection")
    elif kind is CheckerCrossCheckEvalKind.INCONCLUSIVE_EVIDENCE:
        if not observation.inconclusive_not_pass:
            failures.append("expected inconclusive checker to remain non-pass")
    else:  # pragma: no cover - StrEnum exhaustiveness guard
        failures.append(f"unsupported checker eval kind: {kind}")

    if observation.human_review_created:
        failures.append("eval must not create human review")
    if observation.source_metadata_created:
        failures.append("eval must not create source metadata")
    if observation.accepted_write_performed:
        failures.append("eval must not write or claim accepted knowledge")
    return failures


def _store_checker_status(
    context: RepoContext,
    workflow_id: str,
    checker_id: str,
    status: CheckerStatus,
    message: str,
) -> None:
    registry = default_checker_registry()
    spec = registry.get(checker_id)
    if spec is None:
        raise CheckerCrossCheckEvalError(f"unknown checker fixture: {checker_id}")
    now = datetime(2026, 6, 18, 0, 0, tzinfo=UTC)
    workflow_path = workflow_root(workflow_id) / "workflow.json"
    result = CheckerResult(
        checker_id=checker_id,
        checker_type=spec.checker_type,
        status=status,
        started_at=now,
        ended_at=now,
        message=message,
        command=("python", "-m", "fixture"),
        cwd=str(context.repo_root),
        input_paths=(workflow_path.as_posix(),),
        limitations=("fixture checker result; review context only",),
    )
    store_checker_execution(
        context,
        spec,
        CheckerInput(
            paths=(workflow_path.as_posix(),),
            text=workflow_id,
            payload={"workflow_id": workflow_id},
        ),
        CheckerExecution(result=result),
    )


def _append_workflow_step(
    context: RepoContext,
    workflow_id: str,
    kind: CheckerCrossCheckEvalKind,
) -> None:
    workflow = load_workflow(context, workflow_id)
    status = "success"
    if kind in {
        CheckerCrossCheckEvalKind.SKIPPED_OPTIONAL_CHECKER,
        CheckerCrossCheckEvalKind.INCONCLUSIVE_EVIDENCE,
    }:
        status = "skipped"
    workflow = append_step(
        workflow,
        WorkflowStep(
            step_number=1,
            action=f"eval.{kind.value}",
            status=status,
            output_refs={
                "workflow": (
                    workflow_root(workflow_id) / "workflow.json"
                ).as_posix()
            },
        ),
    )
    write_workflow(context, workflow)


def _write_fixture(root: Path) -> None:
    (root / "issues" / "open").mkdir(parents=True)
    (root / "kb" / "private" / "draft" / "claims").mkdir(parents=True)
    (root / "cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "checker-crosscheck-eval"',
                "",
                "[[kb]]",
                'name = "private"',
                'path = "kb/private"',
                "readonly = false",
                "priority = 20",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    _write_yaml(
        root / "issues" / "open" / f"{ISSUE_ID}.yaml",
        {
            "id": ISSUE_ID,
            "type": "issue",
            "title": "Checker cross-check eval fixture",
            "status": "open",
            "created_at": "2026-06-18T00:00:00Z",
            "updated_at": "2026-06-18T00:00:00Z",
            "authors": ["eval-fixture"],
            "severity": "low",
            "description": "Checker/cross-check eval fixture.",
            "related_artifacts": ["claim.eval.checker-crosscheck"],
            "tags": ["checker-crosscheck"],
        },
    )
    _write_yaml(
        root
        / "kb"
        / "private"
        / "draft"
        / "claims"
        / "claim.eval.checker-crosscheck.yaml",
        {
            "id": "claim.eval.checker-crosscheck",
            "type": "claim",
            "title": "Checker cross-check eval fixture claim",
            "domain": ["testing"],
            "status": "draft",
            "created_at": "2026-06-18T00:00:00Z",
            "updated_at": "2026-06-18T00:00:00Z",
            "authors": ["eval-fixture"],
            "depends_on": [],
            "supersedes": [],
            "tags": ["checker-crosscheck"],
            "statement": "Fixture claim for checker/cross-check eval.",
            "evidence": [
                {
                    "kind": "external",
                    "path": "external:checker-crosscheck-eval",
                    "summary": "Deterministic local eval fixture.",
                }
            ],
            "review": {"state": "requested", "notes": "Eval fixture only."},
            "risk": {"level": "low", "notes": "Fixture risk."},
        },
    )


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
        newline="\n",
    )


def _workflow_id(kind: CheckerCrossCheckEvalKind) -> str:
    return f"workflow.eval.checker-crosscheck.{kind.value.replace('_', '-')}"


def _query_for_case(kind: CheckerCrossCheckEvalKind) -> str:
    return {
        CheckerCrossCheckEvalKind.VALID_CHECKED_LOCAL_CLAIM: (
            "review local checked evidence without accepting it"
        ),
        CheckerCrossCheckEvalKind.FAILED_CHECKER_CLAIM: (
            "surface failed checker evidence in cross-check report"
        ),
        CheckerCrossCheckEvalKind.SKIPPED_OPTIONAL_CHECKER: (
            "preserve skipped optional checker as non-pass evidence"
        ),
        CheckerCrossCheckEvalKind.OVERCLAIMED_ACCEPTED_PROOF: (
            "reject accepted proof overclaims from checker input"
        ),
        CheckerCrossCheckEvalKind.PRIVATE_LEAKAGE_IN_CROSSCHECK: (
            "reject private leakage in public cross-check material"
        ),
        CheckerCrossCheckEvalKind.SOURCE_GAP: (
            "detect missing source metadata as a review gap"
        ),
        CheckerCrossCheckEvalKind.FORMALIZATION_GAP: (
            "detect missing formalization and semantic alignment gaps"
        ),
        CheckerCrossCheckEvalKind.INCONCLUSIVE_EVIDENCE: (
            "preserve inconclusive checker evidence as non-pass"
        ),
    }[kind]


def _rate_all(results: list[CheckerCrossCheckEvalCaseResult], field_name: str) -> float:
    if not results:
        return 1.0
    return sum(1 for result in results if bool(getattr(result, field_name))) / len(
        results
    )


def _rate_selected(
    results: list[CheckerCrossCheckEvalCaseResult],
    kinds: set[CheckerCrossCheckEvalKind],
    field_name: str,
) -> float:
    selected = [result for result in results if result.kind in kinds]
    if not selected:
        return 1.0
    return sum(1 for result in selected if bool(getattr(result, field_name))) / len(
        selected
    )


__all__ = [
    "DEFAULT_CHECKER_CROSSCHECK_EVAL_CASES",
    "CheckerCrossCheckEvalCase",
    "CheckerCrossCheckEvalCaseResult",
    "CheckerCrossCheckEvalError",
    "CheckerCrossCheckEvalKind",
    "CheckerCrossCheckEvalMetrics",
    "CheckerCrossCheckEvalReport",
    "CheckerCrossCheckEvalSuite",
    "load_checker_crosscheck_eval_suite",
    "resolve_checker_crosscheck_eval_case_path",
    "run_checker_crosscheck_eval_case",
    "run_checker_crosscheck_eval_suite",
]
