"""Tests for bounded research-loop models, storage, and CLI."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.research.loop import (
    AttemptEvidenceSummary,
    AttemptFailureRecord,
    AttemptNextAction,
    AttemptPolicyFinding,
    LoopReviewSummary,
    ResearchLoop,
    ResearchLoopAttempt,
    ResearchLoopAttemptStatus,
    ResearchLoopBudget,
    ResearchLoopDecision,
    ResearchLoopError,
    ResearchLoopFailureTag,
    ResearchLoopStatus,
    ResearchLoopStopCondition,
    append_attempt,
    list_loops,
    load_loop,
    research_loop_attempt_path,
    research_loop_events_path,
    research_loop_path,
    start_loop,
    write_loop,
)
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _completed_at() -> datetime:
    return datetime(2026, 6, 17, 12, 0, tzinfo=UTC)


def _failure(attempt_id: str = "loop.test.attempt.1") -> AttemptFailureRecord:
    return AttemptFailureRecord(
        failure_id=f"failure.{attempt_id}",
        attempt_id=attempt_id,
        attempted_direction="Try direct induction",
        why_it_failed="The induction hypothesis is too weak",
        evidence_for_failure=("reviews/runs/failure.json",),
        related_artifacts=("claim.example",),
        related_previous_attempts=(),
        counterexample_candidate_ids=(),
        checked_counterexample_ids=(),
        verifier_or_gate_errors=("gate G6 skipped is not pass",),
        should_retry=True,
        retry_conditions="Strengthen the invariant first",
        avoid_in_future="Do not retry direct induction without a stronger invariant",
        tags=(ResearchLoopFailureTag.INSUFFICIENT_EVIDENCE,),
        signature="direct-induction:weak-hypothesis",
        occurred_at=_completed_at(),
    )


def _failed_attempt() -> ResearchLoopAttempt:
    attempt_id = "loop.test.attempt.1"
    return ResearchLoopAttempt(
        attempt_id=attempt_id,
        loop_id="loop.test",
        attempt_number=1,
        status=ResearchLoopAttemptStatus.FAILED,
        planned_direction="Try direct induction",
        completed_at=_completed_at(),
        actions_taken=("cosheaf validate", "cosheaf gate run"),
        failures=(_failure(attempt_id),),
        evidence=AttemptEvidenceSummary(
            evidence_refs=("reviews/runs/failure.json",),
            related_artifacts=("claim.example",),
        ),
    )


def test_required_models_serialize() -> None:
    """All B.1 DTOs should serialize deterministically."""
    budget = ResearchLoopBudget(max_attempts=100, max_wallclock_minutes=60)
    stop = ResearchLoopStopCondition(
        condition_id="stop.max-attempts",
        kind="max_attempts",
        description="Stop when attempts are exhausted",
    )
    decision = ResearchLoopDecision(
        decision_id="decision.loop.test.1",
        loop_id="loop.test",
        decision="append failed attempt",
        rationale="Failure memory must be preserved",
        created_at=_completed_at(),
    )
    finding = AttemptPolicyFinding(
        finding_id="finding.loop.test.1",
        severity="blocking",
        finding_type="accepted_write",
        summary="accepted KB path was referenced",
        blocking=True,
    )
    next_action = AttemptNextAction(
        action_id="action.loop.test.1",
        kind="retry_with_justification",
        summary="Retry only with strengthened invariant",
        rationale="Previous direct induction failed",
        retry_requires_justification=True,
    )
    loop = ResearchLoop(
        loop_id="loop.test",
        issue_id="issue.test",
        budget=budget,
        decisions=(decision,),
        stop_conditions=(stop,),
    )
    summary = LoopReviewSummary(
        loop_id=loop.loop_id,
        issue_id=loop.issue_id,
        status=loop.status,
        attempt_count=0,
        failed_attempt_count=0,
        succeeded_attempt_count=0,
        blocking_policy_findings=0,
    )

    payloads = [
        budget.to_dict(),
        stop.to_dict(),
        decision.to_dict(),
        finding.to_dict(),
        next_action.to_dict(),
        loop.to_dict(),
        summary.to_dict(),
    ]
    assert all(isinstance(payload, dict) for payload in payloads)
    assert loop.status == ResearchLoopStatus.CREATED
    assert "accepted status" in loop.authority_notice


def test_failed_attempt_requires_failure_record() -> None:
    """Failed terminal attempts require structured failures."""
    with pytest.raises(ValueError, match="failed attempts require failures"):
        ResearchLoopAttempt(
            attempt_id="loop.test.attempt.1",
            loop_id="loop.test",
            attempt_number=1,
            status=ResearchLoopAttemptStatus.FAILED,
            planned_direction="Try direct induction",
            completed_at=_completed_at(),
        )


def test_succeeded_attempt_requires_result_or_evidence() -> None:
    """Succeeded terminal attempts require result summary or evidence refs."""
    with pytest.raises(ValueError, match="succeeded attempts require"):
        ResearchLoopAttempt(
            attempt_id="loop.test.attempt.1",
            loop_id="loop.test",
            attempt_number=1,
            status=ResearchLoopAttemptStatus.SUCCEEDED,
            planned_direction="Try construction",
            completed_at=_completed_at(),
        )


def test_terminal_attempt_requires_completed_at() -> None:
    """Terminal attempts must record completion time."""
    with pytest.raises(ValueError, match="terminal attempts require completed_at"):
        ResearchLoopAttempt(
            attempt_id="loop.test.attempt.1",
            loop_id="loop.test",
            attempt_number=1,
            status=ResearchLoopAttemptStatus.FAILED,
            planned_direction="Try direct induction",
            failures=(_failure(),),
        )


def test_accepted_path_rejected() -> None:
    """Loop attempts cannot reference accepted KB paths."""
    with pytest.raises(ValueError, match="accepted KB paths"):
        AttemptEvidenceSummary(evidence_refs=("kb/accepted/claims/claim.x.yaml",))


def test_public_mode_rejects_private_refs() -> None:
    """Public-mode attempts must not leak private references."""
    with pytest.raises(ValueError, match="public_only"):
        ResearchLoopAttempt(
            attempt_id="loop.test.attempt.1",
            loop_id="loop.test",
            attempt_number=1,
            status=ResearchLoopAttemptStatus.SUCCEEDED,
            planned_direction="Summarize public context",
            policy_mode="public_only",
            completed_at=_completed_at(),
            result_summary="Uses a private draft",
            evidence=AttemptEvidenceSummary(evidence_refs=("kb/private/draft.yaml",)),
        )


def test_authority_overclaim_rejected() -> None:
    """Attempts cannot claim human-review, verifier, gate, or promotion authority."""
    with pytest.raises(ValueError, match="cannot claim"):
        ResearchLoopAttempt.model_validate(
            {
                "attempt_id": "loop.test.attempt.1",
                "loop_id": "loop.test",
                "attempt_number": 1,
                "status": "succeeded",
                "planned_direction": "Try construction",
                "completed_at": _completed_at().isoformat(),
                "result_summary": "Looks plausible",
                "human_reviewed": True,
            }
        )


def test_storage_paths_are_deterministic(tmp_path: Path) -> None:
    """Loop, attempt, and event paths are deterministic under .cosheaf."""
    context = RepoContext(tmp_path)
    loop = ResearchLoop(
        loop_id="loop.test",
        issue_id="issue.test",
        budget=ResearchLoopBudget(max_attempts=2),
    )
    result = write_loop(context, loop)

    assert result.relative_path == research_loop_path("loop.test")
    assert result.events_path == research_loop_events_path("loop.test")
    assert research_loop_attempt_path(
        "loop.test", "loop.test.attempt.1"
    ) == Path(".cosheaf/research-loops/loop.test/attempts/loop.test.attempt.1.json")
    assert (tmp_path / result.relative_path).exists()
    assert (tmp_path / result.events_path).exists()


def test_start_append_load_and_finalize_loop(tmp_path: Path) -> None:
    """A loop can be created, appended, shown, and finalized."""
    context = RepoContext(tmp_path)
    started = start_loop(
        context,
        issue_id="issue.test",
        loop_id="loop.test",
        budget=ResearchLoopBudget(max_attempts=2),
    )
    attempt = _failed_attempt()
    appended = append_attempt(context, "loop.test", attempt)
    loaded = load_loop(context, "loop.test")
    finalized = loaded.finalize(reason="Operator stopped after first failure")
    written = write_loop(context, finalized)

    assert started.loop.status == ResearchLoopStatus.CREATED
    assert appended.loop.status == ResearchLoopStatus.RUNNING
    assert len(loaded.attempts) == 1
    assert loaded.attempts[0].failures[0].avoid_in_future.startswith("Do not retry")
    assert written.loop.status == ResearchLoopStatus.FINALIZED
    assert "review context only" in written.loop.authority_notice
    assert (tmp_path / ".cosheaf/research-loops/loop.test/events.jsonl").exists()


def test_invalid_status_transition_after_finalize() -> None:
    """Terminal loops cannot accept more attempts."""
    loop = ResearchLoop(loop_id="loop.test", issue_id="issue.test").finalize()

    with pytest.raises(ResearchLoopError, match="status=finalized") as exc_info:
        loop.add_attempt(_failed_attempt())
    assert exc_info.value.code == "loop_terminal"


def test_attempt_number_must_be_ordered() -> None:
    """Append attempts in deterministic sequence order."""
    loop = ResearchLoop(loop_id="loop.test", issue_id="issue.test")
    attempt = _failed_attempt().model_copy(update={"attempt_number": 2})

    with pytest.raises(ResearchLoopError, match="attempt_number"):
        loop.add_attempt(attempt)


def test_list_loops(tmp_path: Path) -> None:
    """List runtime loops in deterministic order."""
    context = RepoContext(tmp_path)
    start_loop(context, issue_id="issue.b", loop_id="loop.b")
    start_loop(context, issue_id="issue.a", loop_id="loop.a")

    assert list_loops(context) == ["loop.a", "loop.b"]


def test_json_schema_files_cover_research_loop_models() -> None:
    """Schema files for B.1 DTOs should exist and be valid JSON documents."""
    schema_names = [
        "research_loop.schema.json",
        "research_loop_attempt.schema.json",
        "attempt_failure_record.schema.json",
        "research_loop_budget.schema.json",
        "research_loop_stop_condition.schema.json",
        "research_loop_decision.schema.json",
        "attempt_evidence_summary.schema.json",
        "attempt_policy_finding.schema.json",
        "attempt_next_action.schema.json",
        "loop_review_summary.schema.json",
    ]
    root = Path(__file__).resolve().parents[1]

    for name in schema_names:
        payload = json.loads((root / "schemas" / name).read_text(encoding="utf-8"))
        assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert payload["title"]


def test_cli_json_smoke(tmp_path: Path) -> None:
    """CLI supports start/show/append-attempt/finalize with JSON output."""
    start = runner.invoke(
        app,
        [
            "research-loop",
            "start",
            "--issue",
            "issue.test",
            "--loop-id",
            "loop.test",
            "--max-attempts",
            "3",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert start.exit_code == 0, start.output
    start_payload = json.loads(start.output)
    assert start_payload["loop"]["loop_id"] == "loop.test"
    assert start_payload["relative_path"].endswith("loop.json")

    input_path = tmp_path / "attempt.json"
    input_path.write_text(json.dumps(_failed_attempt().to_dict()), encoding="utf-8")
    append = runner.invoke(
        app,
        [
            "research-loop",
            "append-attempt",
            "loop.test",
            "--input-json",
            str(input_path),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert append.exit_code == 0, append.output
    append_payload = json.loads(append.output)
    assert append_payload["attempt"]["status"] == "failed"

    show = runner.invoke(
        app,
        [
            "research-loop",
            "show",
            "loop.test",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert show.exit_code == 0, show.output
    assert json.loads(show.output)["attempts"][0]["attempt_id"] == "loop.test.attempt.1"

    finalize = runner.invoke(
        app,
        [
            "research-loop",
            "finalize",
            "loop.test",
            "--reason",
            "done",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert finalize.exit_code == 0, finalize.output
    assert json.loads(finalize.output)["loop"]["status"] == "finalized"
