from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from cosheaf.campaigns import (
    CAMPAIGN_AUTHORITY_NOTICE,
    CampaignAttempt,
    CampaignAttemptOutcome,
    CampaignBudget,
    CampaignComparison,
    CampaignError,
    CampaignOperatorPolicy,
    CampaignOperatorResult,
    CampaignRiskFinding,
    CampaignRiskSeverity,
    CampaignRunResult,
    CampaignScanResult,
    CampaignStatus,
    CampaignStopCondition,
    ResearchCampaign,
    append_campaign_attempt,
    build_campaign_scorecard,
    campaign_attempt_path,
    campaign_events_path,
    campaign_path,
    export_campaign_operator_task,
    finalize_campaign,
    import_campaign_operator_result,
    load_campaign,
    next_campaign_operator_task,
    pause_campaign,
    resume_campaign,
    run_campaign,
    scan_campaign,
    start_campaign,
)
from cosheaf.cli import app
from cosheaf.storage.repo import RepoContext

runner = CliRunner()

STARTED_AT = datetime(2026, 6, 18, 2, 0, tzinfo=UTC)
ENDED_AT = datetime(2026, 6, 18, 2, 5, tzinfo=UTC)


def _result_attempt(
    *,
    attempt_id: str = "campaign.issue.fixture.attempt.1",
    campaign_id: str = "campaign.issue.fixture.c20260618.t020000z",
    attempt_number: int = 1,
) -> CampaignAttempt:
    return CampaignAttempt(
        attempt_id=attempt_id,
        campaign_id=campaign_id,
        attempt_number=attempt_number,
        outcome=CampaignAttemptOutcome.RESULT,
        attempted_direction="Try a source-reviewed draft proposal",
        completed_at=ENDED_AT,
        result_summary="Draft proposal ready for human review only",
        workflow_refs=("workflow.issue.fixture",),
        check_report_refs=(".cosheaf/reports/validate.json",),
        proof_obligation_refs=("obligation.issue.fixture.1",),
        draft_proposal_refs=("kb/private/draft/claims/claim.fixture.yaml",),
        handoff_refs=(".cosheaf/operator-sessions/session.fixture/handoff.json",),
        benchmark_report_refs=(".cosheaf/evals/campaign.json",),
    )


def test_campaign_models_serialize_with_authority_boundary() -> None:
    budget = CampaignBudget(max_attempts=2, max_runtime_minutes=30)
    stop = CampaignStopCondition(
        condition_id="stop.max-attempts",
        kind="max_attempts",
        description="Stop when attempts are exhausted",
    )
    policy = CampaignOperatorPolicy(policy_mode="private_research")
    finding = CampaignRiskFinding(
        finding_id="finding.campaign.fixture.1",
        severity=CampaignRiskSeverity.WARNING,
        code="draft_only",
        message="Draft proposal needs human review",
        path="kb/private/draft/claims/claim.fixture.yaml",
    )
    comparison = CampaignComparison(
        comparison_id="comparison.campaign.fixture.1",
        attempt_ids=("campaign.issue.fixture.attempt.1",),
        summary="Single attempt baseline",
        preferred_attempt_id="campaign.issue.fixture.attempt.1",
        rationale="Only one reviewable attempt exists",
    )
    campaign = ResearchCampaign.start(
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        issue_id="issue.fixture",
        budget=budget,
        operator_policy=policy,
        now=STARTED_AT,
    ).with_stop_condition(stop)
    campaign = campaign.with_risk_finding(finding).with_comparison(comparison)
    campaign = campaign.add_attempt(_result_attempt())
    scorecard = build_campaign_scorecard(campaign)

    payloads = [
        budget.to_dict(),
        stop.to_dict(),
        policy.to_dict(),
        finding.to_dict(),
        comparison.to_dict(),
        campaign.to_dict(),
        scorecard.to_dict(),
    ]

    assert all(isinstance(payload, dict) for payload in payloads)
    assert campaign.status is CampaignStatus.RUNNING
    assert campaign.authority_notice == CAMPAIGN_AUTHORITY_NOTICE
    assert campaign.accepted_write_performed is False
    assert campaign.human_review_created is False
    assert campaign.promotion_performed is False
    assert campaign.verifier_result_mutated is False
    assert scorecard.attempt_count == 1
    assert scorecard.result_count == 1
    assert scorecard.accepted_write_performed is False
    assert "review context only" in scorecard.authority_notice


def test_campaign_rejects_invalid_status_transition_after_finalize() -> None:
    campaign = ResearchCampaign.start(
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        issue_id="issue.fixture",
        now=STARTED_AT,
    ).finalize(now=ENDED_AT, status=CampaignStatus.FINALIZED)

    with pytest.raises(CampaignError, match="terminal campaigns cannot be modified"):
        campaign.add_attempt(_result_attempt())


@pytest.mark.parametrize(
    ("outcome", "message"),
    [
        (CampaignAttemptOutcome.RESULT, "result attempts require result_summary"),
        (CampaignAttemptOutcome.FAILURE, "failure attempts require failure_summary"),
        (
            CampaignAttemptOutcome.INCONCLUSIVE,
            "inconclusive attempts require inconclusive_reason",
        ),
        (CampaignAttemptOutcome.BLOCKED, "blocked attempts require blocked_reason"),
    ],
)
def test_campaign_attempts_require_result_failure_or_blocker_details(
    outcome: CampaignAttemptOutcome,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        CampaignAttempt(
            attempt_id="campaign.issue.fixture.attempt.1",
            campaign_id="campaign.issue.fixture.c20260618.t020000z",
            attempt_number=1,
            outcome=outcome,
            attempted_direction="Try incomplete result",
            completed_at=ENDED_AT,
        )


def test_campaign_attempt_rejects_accepted_path_references() -> None:
    with pytest.raises(ValidationError, match="accepted KB paths"):
        CampaignAttempt(
            attempt_id="campaign.issue.fixture.attempt.1",
            campaign_id="campaign.issue.fixture.c20260618.t020000z",
            attempt_number=1,
            outcome=CampaignAttemptOutcome.RESULT,
            attempted_direction="Try unsafe accepted ref",
            completed_at=ENDED_AT,
            result_summary="Unsafe reference",
            draft_proposal_refs=("kb/accepted/claims/claim.fixture.yaml",),
        )


def test_campaign_public_mode_rejects_private_references() -> None:
    with pytest.raises(ValidationError, match="public_only"):
        CampaignAttempt(
            attempt_id="campaign.issue.fixture.attempt.1",
            campaign_id="campaign.issue.fixture.c20260618.t020000z",
            attempt_number=1,
            outcome=CampaignAttemptOutcome.RESULT,
            policy_mode="public_only",
            attempted_direction="Try public-only result",
            completed_at=ENDED_AT,
            result_summary="Unsafe private reference",
            draft_proposal_refs=("kb/private/draft/claims/claim.fixture.yaml",),
        )


def test_campaign_scorecard_output_is_deterministic() -> None:
    campaign = ResearchCampaign.start(
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        issue_id="issue.fixture",
        budget=CampaignBudget(max_attempts=3),
        now=STARTED_AT,
    ).add_attempt(_result_attempt())

    first = build_campaign_scorecard(campaign).to_dict()
    second = build_campaign_scorecard(campaign).to_dict()

    assert first == second
    assert first["attempt_count"] == 1
    assert first["draft_proposal_count"] == 1
    assert first["check_report_count"] == 1


def test_campaign_storage_writes_required_runtime_files(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    started = start_campaign(
        context,
        issue_id="issue.fixture",
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        budget=CampaignBudget(max_attempts=2),
        now=STARTED_AT,
    )
    appended = append_campaign_attempt(
        context,
        started.campaign.campaign_id,
        _result_attempt(),
    )
    finalized = finalize_campaign(
        context,
        started.campaign.campaign_id,
        status=CampaignStatus.FINALIZED,
        now=ENDED_AT,
    )
    scorecard = build_campaign_scorecard(finalized.campaign)
    loaded = load_campaign(context, started.campaign.campaign_id)

    assert started.relative_path == campaign_path(started.campaign.campaign_id)
    assert started.events_path == campaign_events_path(started.campaign.campaign_id)
    assert appended.attempt_path == campaign_attempt_path(
        started.campaign.campaign_id,
        "campaign.issue.fixture.attempt.1",
    )
    assert (tmp_path / started.relative_path).is_file()
    assert (tmp_path / appended.attempt_path).is_file()
    assert (tmp_path / started.scorecard_path).is_file()
    assert (tmp_path / started.events_path).is_file()
    assert scorecard.to_dict() == json.loads(
        (tmp_path / started.scorecard_path).read_text(encoding="utf-8")
    )
    assert finalized.campaign.status is CampaignStatus.FINALIZED
    assert loaded.campaign.attempts[0].attempt_id == "campaign.issue.fixture.attempt.1"


def test_campaign_export_task_includes_bounded_context_and_previous_failures(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)
    start_campaign(
        context,
        issue_id="issue.fixture",
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        budget=CampaignBudget(max_attempts=3),
        now=STARTED_AT,
    )
    append_campaign_attempt(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        CampaignAttempt(
            attempt_id="campaign.issue.fixture.c20260618.t020000z.attempt.1",
            campaign_id="campaign.issue.fixture.c20260618.t020000z",
            attempt_number=1,
            outcome=CampaignAttemptOutcome.FAILURE,
            attempted_direction="Try direct induction",
            completed_at=ENDED_AT,
            failure_summary="The induction hypothesis is too weak",
            proof_obligation_refs=("obligation.issue.fixture.weak-induction",),
            check_report_refs=(".cosheaf/reports/checker.json",),
        ),
    )

    relative_path = export_campaign_operator_task(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        ".cosheaf/campaigns/campaign.issue.fixture.c20260618.t020000z/operator_task_v2.json",
    )
    payload = json.loads((tmp_path / relative_path).read_text(encoding="utf-8"))
    next_result = next_campaign_operator_task(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
    )

    assert payload["kind"] == "operator_task_v2"
    assert payload["campaign_id"] == "campaign.issue.fixture.c20260618.t020000z"
    assert payload["attempt_id"] == (
        "campaign.issue.fixture.c20260618.t020000z.attempt.2"
    )
    assert payload["previous_failures_to_avoid"][0]["attempt_id"] == (
        "campaign.issue.fixture.c20260618.t020000z.attempt.1"
    )
    assert payload["proof_obligations"] == [
        "obligation.issue.fixture.weak-induction"
    ]
    assert "write kb/accepted" in payload["forbidden_actions"]
    assert payload["output_contract"]["authority_claims_must_be_false"] is True
    assert next_result.operator_task is not None
    assert next_result.operator_task.attempt_id == payload["attempt_id"]


def test_campaign_import_operator_result_writes_attempt(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_campaign(
        context,
        issue_id="issue.fixture",
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        now=STARTED_AT,
    )
    payload = CampaignOperatorResult.model_validate(
        {
            "attempted_direction": "Try separator-based draft",
            "actions_taken": ["cosheaf validate", "cosheaf gate run"],
            "artifacts_read": ["definition.graph"],
            "drafts_created": ["kb/private/draft/claims/claim.fixture.yaml"],
            "claims_made": ["A draft route may work after strengthening."],
            "checks_requested": ["cosheaf validate"],
            "evidence_refs": ["reviews/runs/campaign-result.json"],
            "authority_claims": {"accepted_status": False},
        }
    )

    imported = import_campaign_operator_result(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        payload,
    )
    loaded = load_campaign(context, "campaign.issue.fixture.c20260618.t020000z")

    assert imported.attempt.outcome is CampaignAttemptOutcome.RESULT
    assert imported.attempt.draft_proposal_refs == (
        "kb/private/draft/claims/claim.fixture.yaml",
    )
    assert imported.operator_result_path.endswith(
        "/operator-results/campaign.issue.fixture.c20260618.t020000z.attempt.1.json"
    )
    assert loaded.campaign.attempts[0].attempt_id == imported.attempt.attempt_id
    assert loaded.campaign.accepted_write_performed is False


def test_campaign_operator_result_rejects_authority_overclaims() -> None:
    with pytest.raises(ValidationError, match="cannot claim"):
        CampaignOperatorResult.model_validate(
            {
                "attempted_direction": "Try review spoof",
                "drafts_created": ["kb/private/draft/claims/claim.fixture.yaml"],
                "human_reviewed": True,
            }
        )
    with pytest.raises(ValidationError, match="authority_claims"):
        CampaignOperatorResult.model_validate(
            {
                "attempted_direction": "Try verifier spoof",
                "drafts_created": ["kb/private/draft/claims/claim.fixture.yaml"],
                "authority_claims": {"verifier_pass": True},
            }
        )


def test_campaign_operator_result_rejects_private_leak_in_public_mode(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)
    start_campaign(
        context,
        issue_id="issue.fixture",
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        operator_policy=CampaignOperatorPolicy(policy_mode="public_only"),
        now=STARTED_AT,
    )
    payload = CampaignOperatorResult.model_validate(
        {
            "attempted_direction": "Try public-only draft",
            "drafts_created": ["reviews/public/campaign-result.json"],
            "artifacts_read": ["kb/private/draft/claims/claim.fixture.yaml"],
        }
    )

    with pytest.raises(CampaignError, match="public_only"):
        import_campaign_operator_result(
            context,
            "campaign.issue.fixture.c20260618.t020000z",
            payload,
        )


def test_campaign_operator_result_requires_gap_or_failure_without_draft() -> None:
    with pytest.raises(
        ValidationError,
        match="drafts_created, failures, or remaining_gaps",
    ):
        CampaignOperatorResult.model_validate(
            {
                "attempted_direction": "Try empty result",
                "actions_taken": ["cosheaf validate"],
                "evidence_refs": ["reviews/runs/empty.json"],
            }
        )


def _json(output: str) -> dict[str, Any]:
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def test_campaign_cli_json_smoke(tmp_path: Path) -> None:
    campaign_id = "campaign.issue.fixture.c20260618.t020000z"

    start = runner.invoke(
        app,
        [
            "campaign",
            "start",
            "--issue",
            "issue.fixture",
            "--campaign-id",
            campaign_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert start.exit_code == 0, start.output
    start_payload = _json(start.output)
    assert start_payload["campaign_id"] == campaign_id
    assert start_payload["path"] == f".cosheaf/campaigns/{campaign_id}/campaign.json"
    assert start_payload["accepted_write_performed"] is False

    input_path = tmp_path / "attempt.json"
    input_path.write_text(json.dumps(_result_attempt().to_dict()), encoding="utf-8")
    append = runner.invoke(
        app,
        [
            "campaign",
            "append-attempt",
            campaign_id,
            "--input-json",
            str(input_path),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert append.exit_code == 0, append.output
    append_payload = _json(append.output)
    assert append_payload["attempt"]["outcome"] == "result"
    assert append_payload["campaign"]["attempts"][0]["attempt_id"] == (
        "campaign.issue.fixture.attempt.1"
    )

    show = runner.invoke(
        app,
        [
            "campaign",
            "show",
            campaign_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert show.exit_code == 0, show.output
    assert _json(show.output)["campaign"]["status"] == "running"

    scorecard = runner.invoke(
        app,
        [
            "campaign",
            "scorecard",
            campaign_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert scorecard.exit_code == 0, scorecard.output
    assert _json(scorecard.output)["scorecard"]["attempt_count"] == 1

    finalize = runner.invoke(
        app,
        [
            "campaign",
            "finalize",
            campaign_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert finalize.exit_code == 0, finalize.output
    assert _json(finalize.output)["campaign"]["status"] == "finalized"


def test_campaign_cli_c1_json_smoke(tmp_path: Path) -> None:
    campaign_id = "campaign.issue.fixture.c20260618.t020000z"
    start = runner.invoke(
        app,
        [
            "campaign",
            "start",
            "--issue",
            "issue.fixture",
            "--campaign-id",
            campaign_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert start.exit_code == 0, start.output

    next_result = runner.invoke(
        app,
        [
            "campaign",
            "next",
            campaign_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert next_result.exit_code == 0, next_result.output
    assert _json(next_result.output)["operator_task"]["kind"] == "operator_task_v2"

    export = runner.invoke(
        app,
        [
            "campaign",
            "export-task",
            campaign_id,
            "--out",
            ".cosheaf/campaigns/campaign.issue.fixture.c20260618.t020000z/operator_task_v2.json",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert export.exit_code == 0, export.output
    assert _json(export.output)["writes_performed"] is True

    input_path = tmp_path / "operator_result_v2.json"
    input_path.write_text(
        json.dumps(
            {
                "attempted_direction": "Try bounded draft",
                "actions_taken": ["cosheaf validate"],
                "artifacts_read": ["definition.graph"],
                "drafts_created": ["kb/private/draft/claims/claim.fixture.yaml"],
                "claims_made": ["Draft only; needs review."],
                "checks_requested": ["cosheaf validate"],
                "evidence_refs": ["reviews/runs/campaign-result.json"],
                "authority_claims": {"accepted_status": False},
            }
        ),
        encoding="utf-8",
    )
    imported = runner.invoke(
        app,
        [
            "campaign",
            "import-result",
            campaign_id,
            "--input-json",
            str(input_path),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert imported.exit_code == 0, imported.output
    imported_payload = _json(imported.output)
    assert imported_payload["attempt"]["outcome"] == "result"
    assert imported_payload["accepted_write_performed"] is False


def test_campaign_run_marks_attempt_budget_exhausted(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_campaign(
        context,
        issue_id="issue.fixture",
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        budget=CampaignBudget(max_attempts=1),
        now=STARTED_AT,
    )
    append_campaign_attempt(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        _result_attempt(campaign_id="campaign.issue.fixture.c20260618.t020000z"),
    )

    result = run_campaign(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        max_attempts=1,
    )

    assert isinstance(result, CampaignRunResult)
    assert result.campaign.status is CampaignStatus.BUDGET_EXHAUSTED
    assert result.stop_conditions["all_budget_exhausted"] is True
    assert result.writes_performed is True
    assert result.shell_commands_performed is False
    assert result.provider_calls_performed is False


def test_campaign_run_rejects_terminal_campaign(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_campaign(
        context,
        issue_id="issue.fixture",
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        now=STARTED_AT,
    )
    finalize_campaign(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        status=CampaignStatus.FINALIZED,
        now=ENDED_AT,
    )

    with pytest.raises(CampaignError, match="terminal campaigns cannot be modified"):
        run_campaign(
            context,
            "campaign.issue.fixture.c20260618.t020000z",
            max_attempts=1,
        )


def test_campaign_pause_and_resume_persist_status(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_campaign(
        context,
        issue_id="issue.fixture",
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        now=STARTED_AT,
    )

    paused = pause_campaign(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        reason="Human requested a pause",
    )
    paused_run = run_campaign(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        max_attempts=1,
    )
    resumed = resume_campaign(context, "campaign.issue.fixture.c20260618.t020000z")

    assert paused.campaign.status is CampaignStatus.PAUSED
    assert paused_run.stop_conditions["human_pause_requested"] is True
    assert resumed.campaign.status is CampaignStatus.RUNNING
    assert load_campaign(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
    ).campaign.status is CampaignStatus.RUNNING


def test_campaign_run_blocks_repeated_failures(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_campaign(
        context,
        issue_id="issue.fixture",
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        budget=CampaignBudget(max_attempts=5, max_failure_repeats=1),
        now=STARTED_AT,
    )
    for index in (1, 2):
        append_campaign_attempt(
            context,
            "campaign.issue.fixture.c20260618.t020000z",
            CampaignAttempt(
                attempt_id=f"campaign.issue.fixture.c20260618.t020000z.attempt.{index}",
                campaign_id="campaign.issue.fixture.c20260618.t020000z",
                attempt_number=index,
                outcome=CampaignAttemptOutcome.FAILURE,
                attempted_direction="Try direct induction",
                completed_at=ENDED_AT,
                failure_summary="The same route failed again",
            ),
        )

    result = run_campaign(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        max_attempts=5,
    )

    assert result.campaign.status is CampaignStatus.BLOCKED
    assert result.stop_conditions["repeated_failure_without_justification"] is True
    assert any(finding.code == "repeated_failure" for finding in result.scan.findings)


def test_campaign_run_stops_on_max_draft_outputs(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_campaign(
        context,
        issue_id="issue.fixture",
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        budget=CampaignBudget(max_attempts=5, max_draft_outputs=1),
        now=STARTED_AT,
    )
    append_campaign_attempt(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        _result_attempt(campaign_id="campaign.issue.fixture.c20260618.t020000z"),
    )

    result = run_campaign(
        context,
        "campaign.issue.fixture.c20260618.t020000z",
        max_attempts=5,
    )

    assert result.campaign.status is CampaignStatus.BUDGET_EXHAUSTED
    assert result.stop_conditions["reviewable_draft_created"] is True
    assert result.stop_conditions["all_budget_exhausted"] is True


def test_campaign_scan_blocks_unsafe_runtime_output(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    started = start_campaign(
        context,
        issue_id="issue.fixture",
        campaign_id="campaign.issue.fixture.c20260618.t020000z",
        now=STARTED_AT,
    )
    unsafe = (
        tmp_path
        / started.relative_path.parent
        / "operator-results"
        / "unsafe.json"
    )
    unsafe.parent.mkdir(parents=True, exist_ok=True)
    unsafe.write_text(
        json.dumps({"accepted_status": True, "path": "kb/accepted/claims/x.yaml"}),
        encoding="utf-8",
    )

    result = scan_campaign(context, "campaign.issue.fixture.c20260618.t020000z")

    assert isinstance(result, CampaignScanResult)
    assert result.blocking_finding_count >= 1
    assert result.run_blocked is True
    assert any(
        finding.code == "accepted_authority_overclaim"
        for finding in result.findings
    )


def test_campaign_cli_d1_json_smoke(tmp_path: Path) -> None:
    campaign_id = "campaign.issue.fixture.c20260618.t020000z"
    start = runner.invoke(
        app,
        [
            "campaign",
            "start",
            "--issue",
            "issue.fixture",
            "--campaign-id",
            campaign_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert start.exit_code == 0, start.output

    pause = runner.invoke(
        app,
        [
            "campaign",
            "pause",
            campaign_id,
            "--reason",
            "manual pause",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert pause.exit_code == 0, pause.output
    assert _json(pause.output)["campaign"]["status"] == "paused"

    resume = runner.invoke(
        app,
        [
            "campaign",
            "resume",
            campaign_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert resume.exit_code == 0, resume.output
    assert _json(resume.output)["campaign"]["status"] == "running"

    scan = runner.invoke(
        app,
        [
            "campaign",
            "scan",
            campaign_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert scan.exit_code == 0, scan.output
    assert _json(scan.output)["run_blocked"] is False

    run = runner.invoke(
        app,
        [
            "campaign",
            "run",
            campaign_id,
            "--max-attempts",
            "1",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert run.exit_code == 0, run.output
    run_payload = _json(run.output)
    assert run_payload["shell_commands_performed"] is False
    assert run_payload["provider_calls_performed"] is False
