from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.evals.campaign import (
    CampaignEvalCase,
    CampaignEvalKind,
    CampaignEvalSuite,
    load_campaign_eval_suite,
    resolve_campaign_eval_case_path,
    run_campaign_eval_suite,
)
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def test_campaign_eval_suite_reports_required_metrics(tmp_path: Path) -> None:
    suite = CampaignEvalSuite(
        cases=[
            CampaignEvalCase(
                id="case.campaign.reviewable-handoff",
                kind=CampaignEvalKind.REVIEWABLE_HANDOFF,
            ),
            CampaignEvalCase(
                id="case.campaign.unsafe-output-blocked",
                kind=CampaignEvalKind.UNSAFE_OUTPUT_BLOCKED,
            ),
            CampaignEvalCase(
                id="case.campaign.budget-stop-accuracy",
                kind=CampaignEvalKind.BUDGET_STOP_ACCURACY,
            ),
            CampaignEvalCase(
                id="case.campaign.operator-contract-boundary",
                kind=CampaignEvalKind.OPERATOR_CONTRACT_BOUNDARY,
            ),
        ]
    )

    report = run_campaign_eval_suite(RepoContext(tmp_path), suite)

    assert report.passed is True
    assert report.case_count == 4
    assert report.metrics.attempt_count >= 4
    assert report.metrics.unique_direction_count >= 3
    assert report.metrics.repeat_failure_count >= 1
    assert report.metrics.reviewable_draft_count >= 1
    assert report.metrics.checked_evidence_count >= 1
    assert report.metrics.gap_count >= 1
    assert report.metrics.unsafe_output_count >= 1
    assert report.metrics.budget_stop_accuracy == 1.0
    assert report.metrics.operator_contract_validity == 1.0
    assert report.metrics.accepted_write_violation_count == 0
    assert "review context only" in report.authority_notice


def test_campaign_eval_loads_default_case_file() -> None:
    context = RepoContext(Path("."))
    path = resolve_campaign_eval_case_path(
        context,
        Path("evals/campaign/cases.yaml"),
    )
    suite = load_campaign_eval_suite(path)

    assert [case.kind for case in suite.cases] == [
        CampaignEvalKind.REVIEWABLE_HANDOFF,
        CampaignEvalKind.UNSAFE_OUTPUT_BLOCKED,
        CampaignEvalKind.BUDGET_STOP_ACCURACY,
        CampaignEvalKind.OPERATOR_CONTRACT_BOUNDARY,
    ]


def test_campaign_eval_rejects_nonlocal_case_path(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)

    with pytest.raises(ValueError, match="repository-local"):
        resolve_campaign_eval_case_path(context, tmp_path.parent / "cases.yaml")


def test_campaign_eval_cli_json_smoke(tmp_path: Path) -> None:
    _ = tmp_path
    result = runner.invoke(
        app,
        [
            "eval",
            "campaign",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "campaign_eval"
    assert payload["passed"] is True
    assert payload["metrics"]["budget_stop_accuracy"] == 1.0
    assert payload["metrics"]["operator_contract_validity"] == 1.0
    assert payload["metrics"]["accepted_write_violation_count"] == 0
