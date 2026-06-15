from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.evals.strategy_planner import (
    DEFAULT_STRATEGY_PLANNER_EVAL_CASES,
    StrategyPlannerEvalCase,
    StrategyPlannerEvalKind,
    StrategyPlannerEvalSuite,
    load_strategy_planner_eval_suite,
    run_strategy_planner_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()


def test_strategy_planner_eval_scores_required_cases(tmp_path: Path) -> None:
    suite = StrategyPlannerEvalSuite(
        cases=[
            StrategyPlannerEvalCase(
                id="case.strategy.problem-decomposition",
                kind=StrategyPlannerEvalKind.PROBLEM_DECOMPOSITION,
            ),
            StrategyPlannerEvalCase(
                id="case.strategy.failed-directions-not-repeated",
                kind=StrategyPlannerEvalKind.FAILED_DIRECTIONS_NOT_REPEATED,
            ),
            StrategyPlannerEvalCase(
                id="case.strategy.evidence-label-separation",
                kind=StrategyPlannerEvalKind.EVIDENCE_LABEL_SEPARATION,
            ),
            StrategyPlannerEvalCase(
                id="case.strategy.skipped-not-pass",
                kind=StrategyPlannerEvalKind.SKIPPED_NOT_PASS,
            ),
            StrategyPlannerEvalCase(
                id="case.strategy.public-only-private-leakage",
                kind=StrategyPlannerEvalKind.PUBLIC_ONLY_PRIVATE_LEAKAGE,
            ),
            StrategyPlannerEvalCase(
                id="case.strategy.no-authority-escalation",
                kind=StrategyPlannerEvalKind.NO_AUTHORITY_ESCALATION,
            ),
        ]
    )

    report = run_strategy_planner_eval_suite(RepoContext(tmp_path), suite)

    assert report.passed is True
    assert report.case_count == 6
    assert report.metrics.problem_decomposition_count == 1
    assert report.metrics.failed_direction_repeat_count == 0
    assert report.metrics.evidence_label_separation_count == 1
    assert report.metrics.skipped_not_pass_count == 1
    assert report.metrics.private_leak_count == 0
    assert report.metrics.authority_escalation_count == 0
    assert not (tmp_path / "kb" / "accepted").exists()


def test_default_strategy_planner_eval_suite_lists_required_cases() -> None:
    suite = load_strategy_planner_eval_suite(ROOT / DEFAULT_STRATEGY_PLANNER_EVAL_CASES)
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.strategy.problem-decomposition",
        "case.strategy.failed-directions-not-repeated",
        "case.strategy.evidence-label-separation",
        "case.strategy.skipped-not-pass",
        "case.strategy.public-only-private-leakage",
        "case.strategy.no-authority-escalation",
    }
    assert {case.kind for case in suite.cases} == set(StrategyPlannerEvalKind)


def test_strategy_planner_eval_cli_json() -> None:
    result = runner.invoke(
        app,
        [
            "eval",
            "strategy-planner",
            "--repo-root",
            str(ROOT),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"passed": true' in result.output
    assert '"authority_escalation_count": 0' in result.output
