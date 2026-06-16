from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from cosheaf.operator_session import (
    OPERATOR_SESSION_AUTHORITY_NOTICE,
    OPERATOR_SESSION_RUNTIME_ROOT,
    OperatorPolicyMode,
    OperatorSessionStatus,
    OperatorToolCallRecord,
    OperatorToolCallStatus,
    append_operator_session_event,
    load_operator_session,
    load_operator_session_events,
    operator_session_path,
    start_operator_session,
)
from cosheaf.storage.repo import RepoContext

STARTED_AT = datetime(2026, 6, 16, 2, 0, tzinfo=UTC)


def test_operator_session_storage_writes_session_json_and_events_jsonl(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)

    result = start_operator_session(
        context,
        issue_id="issue.fixture",
        policy_mode=OperatorPolicyMode.PUBLIC_ONLY,
        operator_label="external operator",
        now=STARTED_AT,
    )

    assert result.relative_path == Path(
        ".cosheaf/operator-sessions/"
        "session.issue.fixture.s20260616t020000z/session.json"
    )
    assert result.events_path == Path(
        ".cosheaf/operator-sessions/"
        "session.issue.fixture.s20260616t020000z/events.jsonl"
    )
    assert result.session.authority_notice == OPERATOR_SESSION_AUTHORITY_NOTICE
    assert result.session.accepted_write_performed is False
    assert (tmp_path / result.relative_path).is_file()
    assert (tmp_path / result.events_path).is_file()

    stored = json.loads((tmp_path / result.relative_path).read_text(encoding="utf-8"))
    assert stored["session_id"] == result.session.session_id
    assert stored["policy_mode"] == "public_only"
    assert stored["accepted_write_performed"] is False

    event = OperatorToolCallRecord(
        event_id="event.validate.0001",
        tool_name="validate",
        status=OperatorToolCallStatus.COMPLETED,
        recorded_at=STARTED_AT,
        result_summary="validation metadata only",
    )
    event_result = append_operator_session_event(
        context,
        session_id=result.session.session_id,
        event=event,
    )

    assert event_result.events_path == result.events_path
    lines = (tmp_path / result.events_path).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["event"]["tool_name"] == "validate"

    loaded = load_operator_session(context, result.session.session_id)
    assert loaded.session.session_id == result.session.session_id
    assert loaded.session.status is OperatorSessionStatus.IN_PROGRESS
    events = load_operator_session_events(context, result.session.session_id)
    assert len(events) == 1
    assert events[0].event["tool_name"] == "validate"


def test_operator_session_default_id_adds_suffix_on_collision(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)

    first = start_operator_session(
        context,
        issue_id="issue.fixture",
        policy_mode=OperatorPolicyMode.PRIVATE_RESEARCH,
        operator_label="external operator",
        now=STARTED_AT,
    )
    second = start_operator_session(
        context,
        issue_id="issue.fixture",
        policy_mode=OperatorPolicyMode.PRIVATE_RESEARCH,
        operator_label="external operator",
        now=STARTED_AT,
    )

    assert first.session.session_id == "session.issue.fixture.s20260616t020000z"
    assert second.session.session_id == "session.issue.fixture.s20260616t020000z.2"
    assert (tmp_path / first.relative_path).is_file()
    assert (tmp_path / second.relative_path).is_file()


def test_operator_session_path_rejects_unsafe_ids() -> None:
    assert operator_session_path("session.issue.fixture.s20260616t020000z") == (
        OPERATOR_SESSION_RUNTIME_ROOT
        / "session.issue.fixture.s20260616t020000z"
        / "session.json"
    )
