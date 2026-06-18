from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from typer.testing import CliRunner

from cosheaf.campaigns import (
    CampaignAttempt,
    CampaignAttemptOutcome,
    append_campaign_attempt,
    start_campaign,
)
from cosheaf.cli import app
from cosheaf.memory.updates import (
    MEMORY_UPDATES_AUTHORITY_NOTICE,
    explain_memory_weight,
    rebuild_memory_weights,
    update_memory_from_campaign,
    update_memory_from_workflow,
)
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import start_workflow, step_workflow

runner = CliRunner()
COMPLETED_AT = datetime(2026, 6, 18, tzinfo=UTC)


def _json(output: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(output))


def test_workflow_memory_update_is_sidecar_only_and_rebuildable(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)
    start_workflow(
        context,
        issue_id="issue.memory.fixture",
        workflow_id="workflow.memory.fixture",
    )
    step_workflow(
        context,
        "workflow.memory.fixture",
        action_id="memory.search",
        execute_local_action=False,
    )

    result = update_memory_from_workflow(context, "workflow.memory.fixture")
    rebuilt = rebuild_memory_weights(context)
    explained = explain_memory_weight(context, "issue.memory.fixture")

    assert result.run.run_id == "memory.update.workflow.workflow.memory.fixture"
    assert result.accepted_write_performed is False
    assert result.yaml_artifacts_mutated is False
    run_path = (
        tmp_path / ".cosheaf/memory/update-runs" / f"{result.run.run_id}.json"
    )
    assert run_path.is_file()
    assert (tmp_path / ".cosheaf/memory/weights.json").is_file()
    assert not (tmp_path / "kb/accepted").exists()
    assert rebuilt.to_dict() == result.weights.to_dict()
    assert explained.edges
    assert explained.authority_notice == MEMORY_UPDATES_AUTHORITY_NOTICE


def test_campaign_memory_update_records_success_and_failure_signals(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)
    campaign_id = "campaign.issue.memory.fixture.c20260618.t000000z"
    start_campaign(
        context,
        issue_id="issue.memory.fixture",
        campaign_id=campaign_id,
    )
    append_campaign_attempt(
        context,
        campaign_id,
        CampaignAttempt(
            attempt_id=f"{campaign_id}.attempt.1",
            campaign_id=campaign_id,
            attempt_number=1,
            outcome=CampaignAttemptOutcome.RESULT,
            attempted_direction="Try a draft",
            completed_at=COMPLETED_AT,
            result_summary="Draft proposal for review only",
            workflow_refs=("workflow.memory.fixture",),
            check_report_refs=(".cosheaf/reports/checker.json",),
            draft_proposal_refs=("kb/private/draft/claims/claim.memory.fixture.yaml",),
        ),
    )
    append_campaign_attempt(
        context,
        campaign_id,
        CampaignAttempt(
            attempt_id=f"{campaign_id}.attempt.2",
            campaign_id=campaign_id,
            attempt_number=2,
            outcome=CampaignAttemptOutcome.FAILURE,
            attempted_direction="Try the failed route",
            completed_at=COMPLETED_AT,
            failure_summary="The route failed",
        ),
    )

    result = update_memory_from_campaign(context, campaign_id)

    signals = {update.signal.value for update in result.run.updates}
    assert {"used_in_successful_draft", "repeat_failure"} <= signals
    assert result.weights.weight_count >= 3
    assert result.accepted_write_performed is False
    assert result.yaml_artifacts_mutated is False

    cli_result = runner.invoke(
        app,
        [
            "memory",
            "update-from-campaign",
            campaign_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert cli_result.exit_code == 0, cli_result.output
    assert _json(cli_result.output)["run"]["source_kind"] == "campaign"


def test_memory_update_cli_smoke(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_workflow(
        context,
        issue_id="issue.memory.fixture",
        workflow_id="workflow.memory.fixture",
    )

    update = runner.invoke(
        app,
        [
            "memory",
            "update-from-workflow",
            "workflow.memory.fixture",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert update.exit_code == 0, update.output
    update_payload = _json(update.output)
    assert update_payload["run"]["source_kind"] == "workflow"
    assert update_payload["accepted_write_performed"] is False

    rebuild = runner.invoke(
        app,
        ["memory", "rebuild", "--repo-root", str(tmp_path), "--json"],
    )
    assert rebuild.exit_code == 0, rebuild.output
    assert _json(rebuild.output)["weight_count"] >= 1

    explain = runner.invoke(
        app,
        [
            "memory",
            "explain",
            "issue.memory.fixture",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert explain.exit_code == 0, explain.output
    explain_payload = _json(explain.output)
    assert explain_payload["artifact_id"] == "issue.memory.fixture"
    assert "sidecar guidance only" in explain_payload["authority_notice"]


def test_memory_explain_requires_weights_sidecar(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "memory",
            "explain",
            "issue.memory.fixture",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    assert "cosheaf memory rebuild" in result.output
