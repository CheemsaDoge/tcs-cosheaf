"""Deterministic benchmark suite aggregator for existing eval harnesses."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

from pydantic import Field, ValidationError, field_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.evals import (
    DEFAULT_CAMPAIGN_EVAL_CASES,
    DEFAULT_CHECKED_EVIDENCE_RUN_LOOP_EVAL_CASES,
    DEFAULT_CHECKER_CROSSCHECK_EVAL_CASES,
    DEFAULT_CONTEXT_EVAL_CASES,
    DEFAULT_RESEARCH_LOOP_EVAL_CASES,
    DEFAULT_RESEARCH_RUN_LOOP_EVAL_CASES,
    DEFAULT_RETRIEVAL_EVAL_CASES,
    DEFAULT_REVIEWABLE_WORKFLOW_EVAL_CASES,
    DEFAULT_STRATEGY_PLANNER_EVAL_CASES,
    load_campaign_eval_suite,
    load_checked_evidence_run_loop_eval_suite,
    load_checker_crosscheck_eval_suite,
    load_context_eval_suite,
    load_research_loop_eval_suite,
    load_research_run_loop_eval_suite,
    load_retrieval_eval_suite,
    load_reviewable_workflow_eval_suite,
    load_strategy_planner_eval_suite,
    resolve_campaign_eval_case_path,
    resolve_checked_evidence_run_loop_eval_case_path,
    resolve_checker_crosscheck_eval_case_path,
    resolve_context_eval_case_path,
    resolve_research_loop_eval_case_path,
    resolve_research_run_loop_eval_case_path,
    resolve_retrieval_eval_case_path,
    resolve_reviewable_workflow_eval_case_path,
    resolve_strategy_planner_eval_case_path,
    run_campaign_eval_suite,
    run_checked_evidence_run_loop_eval_suite,
    run_checker_crosscheck_eval_suite,
    run_context_eval_suite,
    run_research_loop_eval_suite,
    run_research_run_loop_eval_suite,
    run_retrieval_eval_suite,
    run_reviewable_workflow_eval_suite,
    run_strategy_planner_eval_suite,
)
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext

BENCHMARK_AUTHORITY_NOTICE = (
    "Benchmark runs are deterministic regression evidence only; they are not "
    "proof, source metadata, human review, verifier pass, gate pass, accepted "
    "status, accepted theorem/refutation, or promotion authority."
)
BENCHMARK_RUNTIME_ROOT = Path(".cosheaf") / "benchmark-runs"
DETERMINISTIC_GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)


class BenchmarkError(ValueError):
    """Expected benchmark loading, running, or reporting failure."""


class BenchmarkSuiteName(StrEnum):
    """Supported benchmark suite names."""

    SMOKE = "smoke"
    REGRESSION = "regression"
    AUTHORITY_NEGATIVE = "authority_negative"
    PRIVATE_BOUNDARY = "private_boundary"
    RESEARCH_LOOP = "research_loop"
    CAMPAIGN = "campaign"
    REVIEW_WORKFLOW = "review_workflow"


class BenchmarkComponentName(StrEnum):
    """Existing eval components used by benchmark suites."""

    RETRIEVAL = "retrieval"
    CONTEXT = "context"
    CHECKER_CROSSCHECK = "checker_crosscheck"
    CHECKED_EVIDENCE_RUN_LOOP = "checked_evidence_run_loop"
    RESEARCH_RUN_LOOP = "research_run_loop"
    RESEARCH_LOOP = "research_loop"
    REVIEWABLE_WORKFLOW = "reviewable_workflow"
    CAMPAIGN = "campaign"
    STRATEGY_PLANNER = "strategy_planner"


BENCHMARK_CATEGORIES = (
    "retrieval_quality",
    "context_relevance",
    "workflow_completion",
    "checker_accuracy",
    "failure_memory_use",
    "campaign_budget_control",
    "authority_boundary",
    "public_private_boundary",
    "review_handoff_quality",
)


SUITE_COMPONENTS: dict[BenchmarkSuiteName, tuple[BenchmarkComponentName, ...]] = {
    BenchmarkSuiteName.SMOKE: (
        BenchmarkComponentName.RETRIEVAL,
        BenchmarkComponentName.CONTEXT,
        BenchmarkComponentName.CHECKER_CROSSCHECK,
    ),
    BenchmarkSuiteName.REGRESSION: (
        BenchmarkComponentName.RETRIEVAL,
        BenchmarkComponentName.CONTEXT,
        BenchmarkComponentName.CHECKER_CROSSCHECK,
        BenchmarkComponentName.REVIEWABLE_WORKFLOW,
        BenchmarkComponentName.RESEARCH_LOOP,
        BenchmarkComponentName.CAMPAIGN,
    ),
    BenchmarkSuiteName.AUTHORITY_NEGATIVE: (
        BenchmarkComponentName.CHECKER_CROSSCHECK,
        BenchmarkComponentName.REVIEWABLE_WORKFLOW,
        BenchmarkComponentName.CAMPAIGN,
    ),
    BenchmarkSuiteName.PRIVATE_BOUNDARY: (
        BenchmarkComponentName.CONTEXT,
        BenchmarkComponentName.CHECKER_CROSSCHECK,
        BenchmarkComponentName.REVIEWABLE_WORKFLOW,
    ),
    BenchmarkSuiteName.RESEARCH_LOOP: (
        BenchmarkComponentName.RESEARCH_LOOP,
        BenchmarkComponentName.RESEARCH_RUN_LOOP,
        BenchmarkComponentName.CHECKED_EVIDENCE_RUN_LOOP,
        BenchmarkComponentName.STRATEGY_PLANNER,
    ),
    BenchmarkSuiteName.CAMPAIGN: (BenchmarkComponentName.CAMPAIGN,),
    BenchmarkSuiteName.REVIEW_WORKFLOW: (
        BenchmarkComponentName.REVIEWABLE_WORKFLOW,
        BenchmarkComponentName.CHECKER_CROSSCHECK,
    ),
}


class BenchmarkMetrics(MemoryModel):
    """Stable v1 benchmark metrics."""

    pass_count: int = 0
    fail_count: int = 0
    skipped_count: int = 0
    retrieval_precision_at_k: float = 0.0
    context_relevance_score: float = 0.0
    workflow_completion_rate: float = 0.0
    checker_matrix_accuracy: float = 0.0
    failure_reuse_rate: float = 0.0
    budget_stop_accuracy: float = 0.0
    authority_violation_count: int = 0
    private_leak_count: int = 0
    review_handoff_validity: float = 0.0


class BenchmarkComponentResult(MemoryModel):
    """One eval component result inside a benchmark run."""

    name: BenchmarkComponentName
    passed: bool
    case_count: int
    pass_count: int
    fail_count: int
    skipped_count: int
    metrics: dict[str, Any] = Field(default_factory=dict)
    report: dict[str, Any] = Field(default_factory=dict)


class BenchmarkRun(MemoryModel):
    """Persisted benchmark run sidecar."""

    schema_version: Literal[1] = 1
    kind: Literal["benchmark_run"] = "benchmark_run"
    run_id: str
    suite: BenchmarkSuiteName
    generated_at: datetime = DETERMINISTIC_GENERATED_AT
    categories: tuple[str, ...] = BENCHMARK_CATEGORIES
    passed: bool
    metrics: BenchmarkMetrics
    components: tuple[BenchmarkComponentResult, ...]
    skipped_rows_are_passes: Literal[False] = False
    accepted_write_performed: Literal[False] = False
    yaml_artifacts_mutated: Literal[False] = False
    authority_notice: str = BENCHMARK_AUTHORITY_NOTICE

    @field_validator("run_id")
    @classmethod
    def _run_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())


class BenchmarkSuiteInfo(MemoryModel):
    """List entry for one benchmark suite."""

    name: BenchmarkSuiteName
    components: tuple[BenchmarkComponentName, ...]
    categories: tuple[str, ...] = BENCHMARK_CATEGORIES
    authority_notice: str = BENCHMARK_AUTHORITY_NOTICE


class BenchmarkListResult(MemoryModel):
    """Benchmark suite list result."""

    schema_version: Literal[1] = 1
    suites: tuple[BenchmarkSuiteInfo, ...]
    authority_notice: str = BENCHMARK_AUTHORITY_NOTICE


class BenchmarkReportResult(MemoryModel):
    """Benchmark report write result."""

    schema_version: Literal[1] = 1
    run_id: str
    out_path: str
    report_format: Literal["json", "markdown"]
    accepted_write_performed: Literal[False] = False
    authority_notice: str = BENCHMARK_AUTHORITY_NOTICE


def list_benchmark_suites() -> BenchmarkListResult:
    """Return all supported benchmark suites."""
    return BenchmarkListResult(
        suites=tuple(
            BenchmarkSuiteInfo(name=suite, components=components)
            for suite, components in sorted(
                SUITE_COMPONENTS.items(),
                key=lambda item: item[0].value,
            )
        )
    )


def run_benchmark_suite(
    context: RepoContext,
    suite: BenchmarkSuiteName | str,
    *,
    persist: bool = True,
) -> BenchmarkRun:
    """Run a deterministic benchmark suite and optionally persist it."""
    suite_name = _suite_name(suite)
    components = tuple(
        _run_component(context, component)
        for component in SUITE_COMPONENTS[suite_name]
    )
    metrics = _aggregate_metrics(components)
    run = BenchmarkRun(
        run_id=_benchmark_run_id(suite_name),
        suite=suite_name,
        passed=all(component.passed for component in components)
        and metrics.authority_violation_count == 0
        and metrics.private_leak_count == 0,
        metrics=metrics,
        components=components,
    )
    if persist:
        write_benchmark_run(context, run)
    return run


def load_benchmark_run(context: RepoContext, run_id: str) -> BenchmarkRun:
    """Load one persisted benchmark run."""
    resolved = validate_artifact_id(run_id.strip())
    target = context.resolve(benchmark_run_path(resolved))
    _ensure_repo_local(context, target)
    if not target.is_file():
        raise BenchmarkError(
            f"benchmark run not found: {resolved}; run "
            "`cosheaf benchmark run --suite <suite> --json` first"
        )
    try:
        return BenchmarkRun.model_validate_json(target.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as exc:
        raise BenchmarkError(f"invalid benchmark run sidecar: {exc}") from exc


def write_benchmark_run(context: RepoContext, run: BenchmarkRun) -> Path:
    """Persist one benchmark run under ignored runtime storage."""
    relative_path = benchmark_run_path(run.run_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(run.to_json(), encoding="utf-8", newline="\n")
    return relative_path


def write_benchmark_report(
    context: RepoContext,
    run_id: str,
    out: Path,
) -> BenchmarkReportResult:
    """Write a static JSON or Markdown report for one benchmark run."""
    run = load_benchmark_run(context, run_id)
    relative_out = _validate_output_path(context, out)
    target = context.resolve(relative_out)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if relative_out.suffix.lower() == ".json":
        target.write_text(run.to_json(), encoding="utf-8", newline="\n")
        report_format: Literal["json", "markdown"] = "json"
    else:
        target.write_text(
            render_benchmark_markdown(run),
            encoding="utf-8",
            newline="\n",
        )
        report_format = "markdown"
    return BenchmarkReportResult(
        run_id=run.run_id,
        out_path=relative_out.as_posix(),
        report_format=report_format,
    )


def render_benchmark_markdown(run: BenchmarkRun) -> str:
    """Render a short static benchmark report."""
    lines = [
        f"# Benchmark Run {run.run_id}",
        "",
        f"- suite: `{run.suite.value}`",
        f"- passed: `{str(run.passed).lower()}`",
        f"- pass_count: `{run.metrics.pass_count}`",
        f"- fail_count: `{run.metrics.fail_count}`",
        f"- skipped_count: `{run.metrics.skipped_count}`",
        f"- authority_violation_count: `{run.metrics.authority_violation_count}`",
        f"- private_leak_count: `{run.metrics.private_leak_count}`",
        "",
        run.authority_notice,
        "",
        "## Components",
        "",
        "| component | passed | cases | skipped |",
        "| --- | --- | ---: | ---: |",
    ]
    for component in run.components:
        lines.append(
            f"| `{component.name.value}` | `{str(component.passed).lower()}` | "
            f"{component.case_count} | {component.skipped_count} |"
        )
    return "\n".join(lines) + "\n"


def benchmark_run_path(run_id: str) -> Path:
    """Return the deterministic runtime path for one benchmark run."""
    resolved = validate_artifact_id(run_id.strip())
    return BENCHMARK_RUNTIME_ROOT / resolved / "run.json"


def _run_component(
    context: RepoContext,
    component: BenchmarkComponentName,
) -> BenchmarkComponentResult:
    runner = _COMPONENT_RUNNERS[component]
    report = runner(context)
    report_dict = _report_to_dict(report)
    case_count = int(report_dict.get("case_count", 0))
    passed = bool(report_dict.get("passed", False))
    pass_count = int(passed)
    fail_count = int(not passed)
    metrics = dict(report_dict.get("metrics") or {})
    skipped_count = _sum_matching_ints(metrics, ("skipped",))
    return BenchmarkComponentResult(
        name=component,
        passed=passed,
        case_count=case_count,
        pass_count=pass_count,
        fail_count=fail_count,
        skipped_count=skipped_count,
        metrics=metrics,
        report=report_dict,
    )


def _aggregate_metrics(
    components: tuple[BenchmarkComponentResult, ...],
) -> BenchmarkMetrics:
    metric_sets = {component.name: component.metrics for component in components}
    pass_count = sum(component.pass_count for component in components)
    fail_count = sum(component.fail_count for component in components)
    skipped_count = sum(component.skipped_count for component in components)
    return BenchmarkMetrics(
        pass_count=pass_count,
        fail_count=fail_count,
        skipped_count=skipped_count,
        retrieval_precision_at_k=_metric(
            metric_sets,
            BenchmarkComponentName.RETRIEVAL,
            "hit@5",
        ),
        context_relevance_score=_metric(
            metric_sets,
            BenchmarkComponentName.CONTEXT,
            "required_artifact_hit",
        ),
        workflow_completion_rate=_metric(
            metric_sets,
            BenchmarkComponentName.REVIEWABLE_WORKFLOW,
            "workflow_validity_rate",
        ),
        checker_matrix_accuracy=_average(
            _metric(
                metric_sets,
                BenchmarkComponentName.CHECKER_CROSSCHECK,
                "checked_pass_boundary_rate",
            ),
            _metric(
                metric_sets,
                BenchmarkComponentName.CHECKER_CROSSCHECK,
                "failed_checker_detection_rate",
            ),
        ),
        failure_reuse_rate=max(
            _metric(
                metric_sets,
                BenchmarkComponentName.RESEARCH_LOOP,
                "repeat_failure_detection_rate",
            ),
            _metric(
                metric_sets,
                BenchmarkComponentName.REVIEWABLE_WORKFLOW,
                "review_readiness_classification_rate",
            ),
        ),
        budget_stop_accuracy=max(
            _metric(
                metric_sets,
                BenchmarkComponentName.CAMPAIGN,
                "budget_stop_accuracy",
            ),
            _metric(
                metric_sets,
                BenchmarkComponentName.RESEARCH_LOOP,
                "budget_stop_accuracy",
            ),
        ),
        authority_violation_count=sum(
            _sum_matching_ints(component.metrics, ("accepted_write", "authority"))
            for component in components
        ),
        private_leak_count=sum(
            _sum_matching_ints(component.metrics, ("private_leak", "private_leakage"))
            for component in components
        ),
        review_handoff_validity=max(
            _metric(
                metric_sets,
                BenchmarkComponentName.CAMPAIGN,
                "operator_contract_validity",
            ),
            _metric(
                metric_sets,
                BenchmarkComponentName.RESEARCH_LOOP,
                "handoff_review_context_validity_rate",
            ),
            _metric(
                metric_sets,
                BenchmarkComponentName.REVIEWABLE_WORKFLOW,
                "draft_proposal_validity_rate",
            ),
        ),
    )


def _report_to_dict(report: object) -> dict[str, Any]:
    if hasattr(report, "to_dict"):
        value = report.to_dict()
    elif hasattr(report, "model_dump"):
        value = report.model_dump(mode="json")  # type: ignore[attr-defined]
    else:
        raise BenchmarkError(f"unsupported eval report type: {type(report)!r}")
    if not isinstance(value, dict):
        raise BenchmarkError("eval report did not produce a mapping")
    return value


def _sum_matching_ints(metrics: dict[str, Any], needles: tuple[str, ...]) -> int:
    total = 0
    for key, value in metrics.items():
        if not any(needle in key for needle in needles):
            continue
        if isinstance(value, bool):
            total += int(value)
        elif isinstance(value, int):
            total += value
    return total


def _metric(
    metric_sets: dict[BenchmarkComponentName, dict[str, Any]],
    component: BenchmarkComponentName,
    key: str,
) -> float:
    value = metric_sets.get(component, {}).get(key, 0.0)
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return round(float(value), 6)
    return 0.0


def _average(*values: float) -> float:
    present = [value for value in values if value > 0.0]
    if not present:
        return 0.0
    return round(sum(present) / len(present), 6)


def _suite_name(value: BenchmarkSuiteName | str) -> BenchmarkSuiteName:
    try:
        return BenchmarkSuiteName(str(value))
    except ValueError as exc:
        allowed = ", ".join(suite.value for suite in BenchmarkSuiteName)
        raise BenchmarkError(
            f"unknown benchmark suite: {value}; allowed: {allowed}"
        ) from exc


def _benchmark_run_id(suite: BenchmarkSuiteName) -> str:
    return f"benchmark.{suite.value.replace('_', '-')}.r19700101.t000000z".replace(
        "-",
        ".",
    )


def _validate_output_path(context: RepoContext, out: Path) -> Path:
    normalized = normalize_repo_path(str(out))
    if not normalized or normalized == ".":
        raise BenchmarkError("benchmark report path must be repository-local")
    relative = Path(normalized)
    if (
        Path(out).is_absolute()
        or PureWindowsPath(str(out)).is_absolute()
        or normalized.startswith("../")
        or normalized == ".."
        or ".." in relative.parts
    ):
        raise BenchmarkError("benchmark report path must be repository-local")
    if normalized.startswith("kb/accepted/") or "/accepted/" in normalized:
        raise BenchmarkError("benchmark reports must not be written to accepted KB")
    target = context.resolve(relative)
    _ensure_repo_local(context, target)
    return relative


def _ensure_repo_local(context: RepoContext, target: Path) -> None:
    root = context.repo_root.resolve()
    resolved = target.resolve()
    if resolved != root and root not in resolved.parents:
        raise BenchmarkError(f"benchmark path escapes repository: {target}")


def _run_retrieval(context: RepoContext) -> object:
    path = resolve_retrieval_eval_case_path(context, DEFAULT_RETRIEVAL_EVAL_CASES)
    return run_retrieval_eval_suite(
        context,
        load_retrieval_eval_suite(path),
        k=5,
    )


def _run_context(context: RepoContext) -> object:
    path = resolve_context_eval_case_path(context, DEFAULT_CONTEXT_EVAL_CASES)
    return run_context_eval_suite(context, load_context_eval_suite(path))


def _run_checker_crosscheck(context: RepoContext) -> object:
    path = resolve_checker_crosscheck_eval_case_path(
        context,
        DEFAULT_CHECKER_CROSSCHECK_EVAL_CASES,
    )
    return run_checker_crosscheck_eval_suite(
        context,
        load_checker_crosscheck_eval_suite(path),
    )


def _run_checked_evidence_run_loop(context: RepoContext) -> object:
    path = resolve_checked_evidence_run_loop_eval_case_path(
        context,
        DEFAULT_CHECKED_EVIDENCE_RUN_LOOP_EVAL_CASES,
    )
    return run_checked_evidence_run_loop_eval_suite(
        context,
        load_checked_evidence_run_loop_eval_suite(path),
    )


def _run_research_run_loop(context: RepoContext) -> object:
    path = resolve_research_run_loop_eval_case_path(
        context,
        DEFAULT_RESEARCH_RUN_LOOP_EVAL_CASES,
    )
    return run_research_run_loop_eval_suite(
        context,
        load_research_run_loop_eval_suite(path),
    )


def _run_research_loop(context: RepoContext) -> object:
    path = resolve_research_loop_eval_case_path(
        context,
        DEFAULT_RESEARCH_LOOP_EVAL_CASES,
    )
    return run_research_loop_eval_suite(context, load_research_loop_eval_suite(path))


def _run_reviewable_workflow(context: RepoContext) -> object:
    path = resolve_reviewable_workflow_eval_case_path(
        context,
        DEFAULT_REVIEWABLE_WORKFLOW_EVAL_CASES,
    )
    return run_reviewable_workflow_eval_suite(
        context,
        load_reviewable_workflow_eval_suite(path),
    )


def _run_campaign(context: RepoContext) -> object:
    path = resolve_campaign_eval_case_path(context, DEFAULT_CAMPAIGN_EVAL_CASES)
    return run_campaign_eval_suite(context, load_campaign_eval_suite(path))


def _run_strategy_planner(context: RepoContext) -> object:
    path = resolve_strategy_planner_eval_case_path(
        context,
        DEFAULT_STRATEGY_PLANNER_EVAL_CASES,
    )
    return run_strategy_planner_eval_suite(
        context,
        load_strategy_planner_eval_suite(path),
    )


_COMPONENT_RUNNERS: dict[BenchmarkComponentName, Callable[[RepoContext], object]] = {
    BenchmarkComponentName.RETRIEVAL: _run_retrieval,
    BenchmarkComponentName.CONTEXT: _run_context,
    BenchmarkComponentName.CHECKER_CROSSCHECK: _run_checker_crosscheck,
    BenchmarkComponentName.CHECKED_EVIDENCE_RUN_LOOP: _run_checked_evidence_run_loop,
    BenchmarkComponentName.RESEARCH_RUN_LOOP: _run_research_run_loop,
    BenchmarkComponentName.RESEARCH_LOOP: _run_research_loop,
    BenchmarkComponentName.REVIEWABLE_WORKFLOW: _run_reviewable_workflow,
    BenchmarkComponentName.CAMPAIGN: _run_campaign,
    BenchmarkComponentName.STRATEGY_PLANNER: _run_strategy_planner,
}


__all__ = [
    "BENCHMARK_AUTHORITY_NOTICE",
    "BENCHMARK_CATEGORIES",
    "BENCHMARK_RUNTIME_ROOT",
    "BenchmarkComponentName",
    "BenchmarkComponentResult",
    "BenchmarkError",
    "BenchmarkListResult",
    "BenchmarkMetrics",
    "BenchmarkReportResult",
    "BenchmarkRun",
    "BenchmarkSuiteInfo",
    "BenchmarkSuiteName",
    "benchmark_run_path",
    "list_benchmark_suites",
    "load_benchmark_run",
    "render_benchmark_markdown",
    "run_benchmark_suite",
    "write_benchmark_report",
    "write_benchmark_run",
]
