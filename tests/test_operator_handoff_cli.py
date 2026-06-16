from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.operator_session import (
    OPERATOR_SESSION_AUTHORITY_NOTICE,
    OperatorCheckKind,
    OperatorCheckResult,
    OperatorCheckStatus,
    OperatorPolicyMode,
    OperatorSessionError,
    build_operator_handoff,
    export_operator_handoff,
    operator_handoff_export_path,
    operator_handoff_path,
    start_operator_session,
    write_operator_session,
)
from cosheaf.storage.repo import RepoContext

STARTED_AT = datetime(2026, 6, 16, 11, 0, tzinfo=UTC)
ENDED_AT = datetime(2026, 6, 16, 11, 10, tzinfo=UTC)
runner = CliRunner()


def _assert_json(output: str) -> dict[str, Any]:
    assert "\x1b[" not in output
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def _build_handoff_fixture(tmp_path: Path) -> tuple[RepoContext, str]:
    context = RepoContext(tmp_path)
    session_id = "session.issue.fixture.export.0001"
    started = start_operator_session(
        context,
        issue_id="issue.fixture.export",
        policy_mode=OperatorPolicyMode.PRIVATE_RESEARCH,
        operator_label="handoff export test operator",
        session_id=session_id,
        now=STARTED_AT,
    ).session
    session = (
        started.with_check_result(
            OperatorCheckResult(
                kind=OperatorCheckKind.VALIDATE,
                status=OperatorCheckStatus.PASS,
                summary="validate completed outside the handoff export",
                recorded_at=STARTED_AT,
            )
        )
        .with_check_result(
            OperatorCheckResult(
                kind=OperatorCheckKind.GATE,
                status=OperatorCheckStatus.PASS,
                summary="gate completed outside the handoff export",
                recorded_at=STARTED_AT,
            )
        )
        .with_check_result(
            OperatorCheckResult(
                kind=OperatorCheckKind.TEST,
                status=OperatorCheckStatus.PASS,
                summary="tests completed outside the handoff export",
                recorded_at=STARTED_AT,
            )
        )
        .with_check_result(
            OperatorCheckResult(
                kind=OperatorCheckKind.EVAL,
                status=OperatorCheckStatus.PASS,
                summary="eval completed outside the handoff export",
                recorded_at=STARTED_AT,
            )
        )
        .finalize(now=ENDED_AT)
    )
    write_operator_session(context, session)
    handoff = build_operator_handoff(context, session_id=session_id).handoff
    return context, handoff.handoff_id


def test_operator_handoff_export_dry_run_reports_target_without_writing(
    tmp_path: Path,
) -> None:
    _context, handoff_id = _build_handoff_fixture(tmp_path)

    result = runner.invoke(
        app,
        [
            "operator",
            "handoff",
            "export",
            "--handoff",
            handoff_id,
            "--dry-run",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    target_path = operator_handoff_export_path(handoff_id)
    assert payload["kind"] == "operator_handoff_export"
    assert payload["handoff_id"] == handoff_id
    assert payload["target_path"] == target_path.as_posix()
    assert payload["dry_run"] is True
    assert payload["written_paths"] == []
    assert payload["accepted_write_performed"] is False
    assert payload["human_review_created"] is False
    assert payload["promotion_performed"] is False
    assert payload["verifier_result_mutated"] is False
    assert payload["authority_notice"] == OPERATOR_SESSION_AUTHORITY_NOTICE
    assert not (tmp_path / target_path).exists()


def test_operator_handoff_export_writes_review_context_yaml(tmp_path: Path) -> None:
    _context, handoff_id = _build_handoff_fixture(tmp_path)

    result = runner.invoke(
        app,
        [
            "operator",
            "handoff",
            "export",
            "--handoff",
            handoff_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    target_path = tmp_path / operator_handoff_export_path(handoff_id)
    assert payload["dry_run"] is False
    export_path = operator_handoff_export_path(handoff_id).as_posix()
    assert payload["written_paths"] == [export_path]
    assert payload["target_path"] == export_path
    assert target_path.is_file()
    exported = yaml.safe_load(target_path.read_text(encoding="utf-8"))
    assert exported == payload
    assert exported["handoff"]["scanner"]["handoff_blocked"] is False
    assert exported["handoff"]["authority_notice"] == OPERATOR_SESSION_AUTHORITY_NOTICE
    assert exported["review_context_only"] is True


def test_operator_handoff_export_rejects_accepted_write_target(
    tmp_path: Path,
) -> None:
    context, handoff_id = _build_handoff_fixture(tmp_path)

    with pytest.raises(OperatorSessionError) as exc_info:
        export_operator_handoff(
            context,
            handoff_id=handoff_id,
            target_path=Path("kb/accepted/operator/bad.yaml"),
        )

    assert exc_info.value.code == "accepted_write_forbidden"


def test_operator_handoff_export_fails_closed_when_handoff_scanner_blocked(
    tmp_path: Path,
) -> None:
    _context, handoff_id = _build_handoff_fixture(tmp_path)
    handoff_path = tmp_path / operator_handoff_path(handoff_id)
    handoff_payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    handoff_payload["scanner"]["handoff_blocked"] = True
    handoff_payload["scanner"]["blocking_finding_count"] = 1
    handoff_payload["scanner"]["findings"] = [
        {
            "code": "provider_payload",
            "severity": "blocker",
            "message": "operator session stores raw provider payload",
            "source_path": ".cosheaf/operator-sessions/session/events.jsonl",
        }
    ]
    handoff_path.write_text(
        json.dumps(handoff_payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "operator",
            "handoff",
            "export",
            "--handoff",
            handoff_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "operator_handoff_blocked_by_scan"
