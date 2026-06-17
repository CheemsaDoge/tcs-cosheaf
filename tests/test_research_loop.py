"""Tests for research loop models and storage."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from cosheaf.research.loop import (
    AttemptFailureRecord,
    ResearchLoop,
    ResearchLoopAttempt,
    ResearchLoopAttemptStatus,
    ResearchLoopError,
    ResearchLoopFailureTag,
    ResearchLoopStatus,
    list_loops,
    load_loop,
    save_attempt,
    save_loop,
)
from cosheaf.storage.repo import RepoContext


def test_attempt_failure_record() -> None:
    """Test AttemptFailureRecord validation."""
    record = AttemptFailureRecord(
        failure_id="failure.test.1",
        attempt_id="attempt.test.1",
        tags=[ResearchLoopFailureTag.INSUFFICIENT_EVIDENCE],
        summary="Verifier rejected the proof",
        evidence=["artifact.example"],
        avoidance_guidance="Gather more evidence before retry",
        signature="insufficient_evidence:artifact.example",
    )

    assert record.tags == [ResearchLoopFailureTag.INSUFFICIENT_EVIDENCE]
    assert record.summary == "Verifier rejected the proof"
    assert record.evidence == ["artifact.example"]
    assert isinstance(record.occurred_at, datetime)


def test_attempt_failure_record_validation() -> None:
    """Test AttemptFailureRecord validation rules."""
    # Empty tags should fail
    with pytest.raises(ValueError, match="(?i)at least one"):
        AttemptFailureRecord(
            failure_id="f1",
            attempt_id="a1",
            tags=[],
            summary="test",
            avoidance_guidance="avoid",
            signature="sig",
        )

    # Empty summary should fail
    with pytest.raises(ValueError, match="non-empty"):
        AttemptFailureRecord(
            failure_id="f1",
            attempt_id="a1",
            tags=[ResearchLoopFailureTag.UNKNOWN],
            summary="",
            avoidance_guidance="avoid",
            signature="sig",
        )


def test_research_loop_attempt() -> None:
    """Test ResearchLoopAttempt creation and validation."""
    attempt = ResearchLoopAttempt(
        attempt_id="loop.test.attempt.1",
        loop_id="loop.test",
        attempt_number=1,
        planned_direction="Explore approach A",
    )

    assert attempt.attempt_id == "loop.test.attempt.1"
    assert attempt.loop_id == "loop.test"
    assert attempt.status == ResearchLoopAttemptStatus.PLANNED
    assert attempt.planned_direction == "Explore approach A"
    assert attempt.actions_taken == []
    assert attempt.failures == []


def test_research_loop_attempt_timing_validation() -> None:
    """Test ResearchLoopAttempt timing validation."""
    now = datetime.now(UTC)
    later = datetime(now.year + 1, 1, 1, tzinfo=UTC)

    # Valid: completed after started
    attempt = ResearchLoopAttempt(
        attempt_id="test",
        loop_id="loop.test",
        attempt_number=1,
        planned_direction="test",
        started_at=now,
        completed_at=later,
    )
    assert attempt.started_at == now
    assert attempt.completed_at == later

    # Invalid: completed before started
    with pytest.raises(ValueError, match="cannot be before"):
        ResearchLoopAttempt(
            attempt_id="test",
            loop_id="loop.test",
            attempt_number=1,
            planned_direction="test",
            started_at=later,
            completed_at=now,
        )


def test_research_loop() -> None:
    """Test ResearchLoop creation and validation."""
    loop = ResearchLoop(
        loop_id="loop.test.20260617",
        issue_id="issue.test",
        max_attempts=5,
    )

    assert loop.loop_id == "loop.test.20260617"
    assert loop.issue_id == "issue.test"
    assert loop.status == ResearchLoopStatus.ACTIVE
    assert loop.attempts == []
    assert loop.max_attempts == 5


def test_research_loop_add_attempt() -> None:
    """Test adding attempts to a loop."""
    loop = ResearchLoop(
        loop_id="loop.test",
        issue_id="issue.test",
        max_attempts=3,
    )

    attempt1 = ResearchLoopAttempt(
        attempt_id="loop.test.attempt.1",
        loop_id="loop.test",
        attempt_number=1,
        planned_direction="Try A",
    )

    loop.add_attempt(attempt1)
    assert len(loop.attempts) == 1
    assert loop.attempts[0] == attempt1


def test_research_loop_max_attempts_enforcement() -> None:
    """Test max_attempts enforcement."""
    loop = ResearchLoop(
        loop_id="loop.test",
        issue_id="issue.test",
        max_attempts=2,
    )

    attempt1 = ResearchLoopAttempt(
        attempt_id="loop.test.attempt.1",
        loop_id="loop.test",
        attempt_number=1,
        planned_direction="A",
    )
    attempt2 = ResearchLoopAttempt(
        attempt_id="loop.test.attempt.2",
        loop_id="loop.test",
        attempt_number=2,
        planned_direction="B",
    )
    attempt3 = ResearchLoopAttempt(
        attempt_id="loop.test.attempt.3",
        loop_id="loop.test",
        attempt_number=3,
        planned_direction="C",
    )

    loop.add_attempt(attempt1)
    loop.add_attempt(attempt2)

    # Third attempt should fail
    with pytest.raises(ResearchLoopError, match="max_attempts"):
        loop.add_attempt(attempt3)


def test_research_loop_finalize() -> None:
    """Test loop finalization."""
    loop = ResearchLoop(
        loop_id="loop.test",
        issue_id="issue.test",
    )

    assert loop.status == ResearchLoopStatus.ACTIVE
    assert loop.finalized_at is None

    loop.finalize(reason="All attempts exhausted")

    assert loop.status == ResearchLoopStatus.FINALIZED
    assert loop.finalized_at is not None
    assert "All attempts exhausted" in loop.notes


def test_research_loop_cannot_add_after_finalize() -> None:
    """Test that attempts cannot be added after finalization."""
    loop = ResearchLoop(
        loop_id="loop.test",
        issue_id="issue.test",
    )

    loop.finalize()

    attempt = ResearchLoopAttempt(
        attempt_id="loop.test.attempt.1",
        loop_id="loop.test",
        attempt_number=1,
        planned_direction="test",
    )

    with pytest.raises(ResearchLoopError, match="status"):
        loop.add_attempt(attempt)


def test_save_and_load_loop(tmp_path: Path) -> None:
    """Test saving and loading a research loop."""
    repo = RepoContext(repo_root=tmp_path)

    loop = ResearchLoop(
        loop_id="loop.test.20260617",
        issue_id="issue.test",
        max_attempts=10,
        notes="Test loop",
    )

    # Save
    saved_path = save_loop(repo, loop)
    assert saved_path.exists()
    assert saved_path.name == "loop.json"

    # Load
    loaded = load_loop(repo, "loop.test.20260617")
    assert loaded.loop_id == loop.loop_id
    assert loaded.issue_id == loop.issue_id
    assert loaded.max_attempts == loop.max_attempts
    assert loaded.notes == loop.notes


def test_load_nonexistent_loop(tmp_path: Path) -> None:
    """Test loading a loop that does not exist."""
    repo = RepoContext(repo_root=tmp_path)

    with pytest.raises(ResearchLoopError, match="Loop not found"):
        load_loop(repo, "nonexistent")


def test_save_and_load_attempt(tmp_path: Path) -> None:
    """Test saving and loading an attempt."""
    repo = RepoContext(repo_root=tmp_path)

    attempt = ResearchLoopAttempt(
        attempt_id="loop.test.attempt.1",
        loop_id="loop.test",
        attempt_number=1,
        planned_direction="Explore proof sketch",
        actions_taken=["validate", "gate"],
    )

    # Save
    saved_path = save_attempt(repo, attempt)
    assert saved_path.exists()
    assert saved_path.name == "loop.test.attempt.1.json"


def test_list_loops(tmp_path: Path) -> None:
    """Test listing all loops."""
    repo = RepoContext(repo_root=tmp_path)

    # Empty repository
    assert list_loops(repo) == []

    # Add loops
    loop1 = ResearchLoop(loop_id="loop.a", issue_id="issue.a")
    loop2 = ResearchLoop(loop_id="loop.b", issue_id="issue.b")

    save_loop(repo, loop1)
    save_loop(repo, loop2)

    loops = sorted(list_loops(repo))
    assert loops == ["loop.a", "loop.b"]


def test_research_loop_attempt_loop_id_mismatch() -> None:
    """Test that attempt loop_id must match loop loop_id."""
    loop = ResearchLoop(
        loop_id="loop.correct",
        issue_id="issue.test",
    )

    attempt = ResearchLoopAttempt(
        attempt_id="loop.wrong.attempt.1",
        loop_id="loop.wrong",
        attempt_number=1,
        planned_direction="test",
    )

    with pytest.raises(ResearchLoopError, match="mismatch"):
        loop.add_attempt(attempt)
