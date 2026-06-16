from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.operator_session import (
    OPERATOR_SESSION_AUTHORITY_NOTICE,
    SKIPPED_OPERATOR_SESSION_LIMITATION,
)

runner = CliRunner()


def _assert_json(output: str) -> dict[str, Any]:
    assert "\x1b[" not in output
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def test_operator_session_cli_lifecycle_records_metadata_only(
    tmp_path: Path,
) -> None:
    session_id = "session.issue.fixture.cli.0001"

    start = runner.invoke(
        app,
        [
            "operator",
            "session",
            "start",
            "--issue",
            "issue.fixture",
            "--policy",
            "private_research",
            "--operator-label",
            "external operator",
            "--session-id",
            session_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert start.exit_code == 0, start.output
    start_payload = _assert_json(start.output)
    assert start_payload["kind"] == "operator_session"
    assert start_payload["session_id"] == session_id
    assert start_payload["status"] == "in_progress"
    assert start_payload["path"] == (
        f".cosheaf/operator-sessions/{session_id}/session.json"
    )
    assert start_payload["accepted_write_performed"] is False
    assert start_payload["authority_notice"] == OPERATOR_SESSION_AUTHORITY_NOTICE
    assert start_payload["session"]["human_review_created"] is False
    assert start_payload["session"]["promotion_performed"] is False
    assert start_payload["session"]["verifier_result_mutated"] is False

    append_check = runner.invoke(
        app,
        [
            "operator",
            "session",
            "append-check",
            session_id,
            "--kind",
            "validate",
            "--status",
            "pass",
            "--summary",
            "validation command completed outside this metadata recorder",
            "--report-path",
            ".cosheaf/reports/validate.json",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert append_check.exit_code == 0, append_check.output
    check_payload = _assert_json(append_check.output)
    assert check_payload["session"]["check_results"][0]["kind"] == "validate"
    assert check_payload["session"]["check_results"][0]["status"] == "pass"

    append_skipped = runner.invoke(
        app,
        [
            "operator",
            "session",
            "append-check",
            session_id,
            "--kind",
            "eval",
            "--status",
            "skipped",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert append_skipped.exit_code == 0, append_skipped.output
    skipped_payload = _assert_json(append_skipped.output)
    skipped_result = skipped_payload["session"]["check_results"][1]
    assert skipped_result["status"] == "skipped"
    assert skipped_result["summary"] == SKIPPED_OPERATOR_SESSION_LIMITATION

    append_ref = runner.invoke(
        app,
        [
            "operator",
            "session",
            "append-ref",
            session_id,
            "--kind",
            "draft",
            "--path",
            "kb/private/draft/claims/claim.fixture.yaml",
            "--artifact",
            "claim.fixture",
            "--scope",
            "private",
            "--summary",
            "private draft reference only",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert append_ref.exit_code == 0, append_ref.output
    ref_payload = _assert_json(append_ref.output)
    assert ref_payload["session"]["artifact_refs"][0]["kind"] == "draft"
    assert ref_payload["session"]["artifact_refs"][0]["scope"] == "private"

    show = runner.invoke(
        app,
        [
            "operator",
            "session",
            "show",
            session_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert show.exit_code == 0, show.output
    show_payload = _assert_json(show.output)
    assert show_payload["session"]["status"] == "in_progress"
    assert len(show_payload["session"]["check_results"]) == 2
    assert len(show_payload["session"]["artifact_refs"]) == 1

    events_path = tmp_path / f".cosheaf/operator-sessions/{session_id}/events.jsonl"
    events = events_path.read_text(encoding="utf-8").splitlines()
    assert len(events) == 3
    assert [json.loads(line)["event_kind"] for line in events] == [
        "check_result",
        "check_result",
        "artifact_ref",
    ]

    finalize = runner.invoke(
        app,
        [
            "operator",
            "session",
            "finalize",
            session_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert finalize.exit_code == 0, finalize.output
    finalize_payload = _assert_json(finalize.output)
    assert finalize_payload["session"]["status"] == "finalized"
    assert finalize_payload["session"]["accepted_write_performed"] is False

    append_after_finalize = runner.invoke(
        app,
        [
            "operator",
            "session",
            "append-check",
            session_id,
            "--kind",
            "gate",
            "--status",
            "pass",
            "--summary",
            "late check should be rejected",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert append_after_finalize.exit_code == 1
    error_payload = _assert_json(append_after_finalize.output)
    assert error_payload["blocking"] is True
    assert "terminal operator sessions cannot be modified" in error_payload["message"]


def test_operator_session_cli_rejects_private_refs_in_public_only_session(
    tmp_path: Path,
) -> None:
    session_id = "session.issue.fixture.public.0001"
    start = runner.invoke(
        app,
        [
            "operator",
            "session",
            "start",
            "--issue",
            "issue.fixture",
            "--session-id",
            session_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert start.exit_code == 0, start.output

    private_ref = runner.invoke(
        app,
        [
            "operator",
            "session",
            "append-ref",
            session_id,
            "--kind",
            "draft",
            "--path",
            "kb/private/draft/claims/claim.fixture.yaml",
            "--scope",
            "private",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert private_ref.exit_code == 1
    payload = _assert_json(private_ref.output)
    assert payload["code"] == "private_context_requires_policy"
    assert "public-only operator sessions cannot reference private paths" in (
        payload["message"]
    )


def test_operator_session_cli_rejects_accepted_kb_references(
    tmp_path: Path,
) -> None:
    session_id = "session.issue.fixture.accepted.0001"
    start = runner.invoke(
        app,
        [
            "operator",
            "session",
            "start",
            "--issue",
            "issue.fixture",
            "--policy",
            "private_research",
            "--session-id",
            session_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert start.exit_code == 0, start.output

    accepted_ref = runner.invoke(
        app,
        [
            "operator",
            "session",
            "append-ref",
            session_id,
            "--kind",
            "review_context",
            "--path",
            "kb/accepted/claims/claim.fixture.yaml",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert accepted_ref.exit_code == 1
    payload = _assert_json(accepted_ref.output)
    assert payload["code"] == "accepted_write_forbidden"
    assert "accepted KB paths" in payload["message"]

