from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.operator_session import (
    OPERATOR_SESSION_AUTHORITY_NOTICE,
    SKIPPED_OPERATOR_SESSION_LIMITATION,
    OperatorArtifactRef,
    OperatorArtifactRefKind,
    OperatorCheckKind,
    OperatorCheckResult,
    OperatorCheckStatus,
    OperatorPolicyMode,
    OperatorToolCallRecord,
    OperatorToolCallStatus,
    append_operator_session_event,
    build_operator_handoff,
    operator_handoff_path,
    operator_session_events_path,
    start_operator_session,
    write_operator_session,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[1]
STARTED_AT = datetime(2026, 6, 16, 10, 0, tzinfo=UTC)
ENDED_AT = datetime(2026, 6, 16, 10, 10, tzinfo=UTC)
runner = CliRunner()


def _assert_json(output: str) -> dict[str, Any]:
    assert "\x1b[" not in output
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "operator-handoff-fixture"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                "readonly = true",
                "priority = 10",
                "",
                "[[kb]]",
                'name = "private"',
                'path = "kb/private"',
                "readonly = false",
                "priority = 20",
                "",
                "[policy]",
                "private_can_depend_on_public = true",
                "public_can_depend_on_private = false",
                "accepted_requires_source = true",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _fixture_context(repo_root: Path) -> RepoContext:
    _write_workspace_config(repo_root)
    return RepoContext(repo_root)


def _finalized_session(
    context: RepoContext,
    *,
    session_id: str = "session.issue.fixture.handoff.0001",
) -> str:
    started = start_operator_session(
        context,
        issue_id="issue.fixture.handoff",
        policy_mode=OperatorPolicyMode.PRIVATE_RESEARCH,
        operator_label="handoff test operator",
        session_id=session_id,
        now=STARTED_AT,
    ).session
    session = (
        started.with_artifact_ref(
            OperatorArtifactRef(
                kind=OperatorArtifactRefKind.DRAFT,
                path="kb/private/draft/claims/claim.fixture.yaml",
                artifact_id="claim.fixture",
                summary="private draft proposed by operator",
                scope="private",
            )
        )
        .with_artifact_ref(
            OperatorArtifactRef(
                kind=OperatorArtifactRefKind.SOURCE_NOTE,
                path="sources/notes/source.fixture.yaml",
                summary="durable source-note candidate",
                scope="workspace",
            )
        )
        .with_artifact_ref(
            OperatorArtifactRef(
                kind=OperatorArtifactRefKind.REVIEW_CONTEXT,
                path="reviews/requests/review.fixture.yaml",
                summary="review-context request only",
                scope="workspace",
            )
        )
        .with_check_result(
            OperatorCheckResult(
                kind=OperatorCheckKind.VALIDATE,
                status=OperatorCheckStatus.PASS,
                summary="validate completed outside the handoff builder",
                report_path=".cosheaf/reports/validate.json",
                recorded_at=STARTED_AT,
            )
        )
        .with_check_result(
            OperatorCheckResult(
                kind=OperatorCheckKind.GATE,
                status=OperatorCheckStatus.PASS,
                summary="gate completed outside the handoff builder",
                report_path=".cosheaf/reports/gate.json",
                recorded_at=STARTED_AT,
            )
        )
        .with_check_result(
            OperatorCheckResult(
                kind=OperatorCheckKind.EVAL,
                status=OperatorCheckStatus.SKIPPED,
                summary=SKIPPED_OPERATOR_SESSION_LIMITATION,
                recorded_at=STARTED_AT,
            )
        )
        .finalize(now=ENDED_AT)
    )
    write_operator_session(context, session)
    append_operator_session_event(
        context,
        session_id=session_id,
        event=OperatorToolCallRecord(
            event_id="event.workspace-info.0001",
            tool_name="workspace_info",
            status=OperatorToolCallStatus.COMPLETED,
            recorded_at=STARTED_AT,
            input_metadata={
                "argument_count": "0",
                "argument_names": "none",
                "session_mode": "private_research",
            },
            result_summary="completed tool call: workspace_info",
        ),
    )
    return session_id


def test_operator_handoff_builds_review_context_bundle(tmp_path: Path) -> None:
    context = _fixture_context(tmp_path)
    session_id = _finalized_session(context)

    result = build_operator_handoff(context, session_id=session_id)

    payload = result.handoff.to_dict()
    assert payload["kind"] == "operator_handoff_bundle"
    assert payload["handoff_id"] == f"handoff.{session_id}"
    assert payload["session_id"] == session_id
    assert payload["issue_id"] == "issue.fixture.handoff"
    assert payload["policy_mode"] == "private_research"
    assert payload["session_status"] == "finalized"
    assert payload["accepted_write_performed"] is False
    assert payload["human_review_created"] is False
    assert payload["promotion_performed"] is False
    assert payload["verifier_result_mutated"] is False
    assert payload["authority_notice"] == OPERATOR_SESSION_AUTHORITY_NOTICE
    assert payload["scanner"]["handoff_blocked"] is False
    assert payload["scanner"]["blocking_finding_count"] == 0
    assert payload["check_summary"]["skipped"] == ["eval"]
    assert payload["check_summary"]["all_required_recorded"] is False
    assert payload["skipped_checks_are_pass"] is False
    assert "Skipped checks are not pass evidence." in payload["known_limitations"]
    assert payload["referenced_files"] == [
        "kb/private/draft/claims/claim.fixture.yaml",
        "sources/notes/source.fixture.yaml",
        "reviews/requests/review.fixture.yaml",
    ]
    assert payload["draft_artifacts"] == ["claim.fixture"]
    assert payload["source_notes"] == ["sources/notes/source.fixture.yaml"]
    assert payload["review_context_records"] == ["reviews/requests/review.fixture.yaml"]
    assert payload["tool_summary"] == {
        "workspace_info": {"completed": 1, "denied": 0, "error": 0, "failed": 0}
    }
    assert payload["human_review_checklist"] == [
        "Confirm source metadata separately from this handoff.",
        "Confirm human review separately from this handoff.",
        "Run or inspect validation, gate, tests, and evals independently.",
        "Confirm skipped checks are not treated as pass evidence.",
        "Confirm no accepted write, promotion, or verifier mutation occurred.",
    ]
    assert payload["follow_up_recommendations"]
    assert (tmp_path / result.relative_path).is_file()
    persisted_payload = json.loads(
        (tmp_path / result.relative_path).read_text(encoding="utf-8")
    )
    assert persisted_payload == payload


def test_operator_handoff_cli_build_and_show(tmp_path: Path) -> None:
    context = _fixture_context(tmp_path)
    session_id = _finalized_session(context)

    build = runner.invoke(
        app,
        [
            "operator",
            "handoff",
            "build",
            "--session",
            session_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert build.exit_code == 0, build.output
    build_payload = _assert_json(build.output)
    handoff_id = build_payload["handoff_id"]
    assert build_payload["kind"] == "operator_handoff_bundle"
    assert build_payload["path"] == operator_handoff_path(handoff_id).as_posix()
    assert build_payload["accepted_write_performed"] is False

    show = runner.invoke(
        app,
        [
            "operator",
            "handoff",
            "show",
            handoff_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert show.exit_code == 0, show.output
    show_payload = _assert_json(show.output)
    assert show_payload == build_payload


def test_operator_handoff_requires_finalized_session(tmp_path: Path) -> None:
    context = _fixture_context(tmp_path)
    session_id = "session.issue.fixture.handoff.open"
    start_operator_session(
        context,
        issue_id="issue.fixture.handoff",
        policy_mode=OperatorPolicyMode.PRIVATE_RESEARCH,
        operator_label="handoff test operator",
        session_id=session_id,
        now=STARTED_AT,
    )

    result = runner.invoke(
        app,
        [
            "operator",
            "handoff",
            "build",
            "--session",
            session_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "operator_handoff_session_not_finalized"


def test_operator_handoff_fails_closed_when_scan_has_blockers(tmp_path: Path) -> None:
    context = _fixture_context(tmp_path)
    session_id = _finalized_session(
        context,
        session_id="session.issue.fixture.block.0001",
    )
    events_path = tmp_path / operator_session_events_path(session_id)
    events_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "session_id": session_id,
                "sequence": 1,
                "event_kind": "tool_call",
                "recorded_at": "2026-06-16T10:01:00Z",
                "event": {
                    "event_id": "event.provider.0001",
                    "tool_name": "provider_call",
                    "status": "completed",
                    "recorded_at": "2026-06-16T10:01:00Z",
                    "provider_payload": {"messages": []},
                    "result_summary": "raw provider payload leaked",
                    "warning_codes": [],
                },
                "authority_notice": OPERATOR_SESSION_AUTHORITY_NOTICE,
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "operator",
            "handoff",
            "build",
            "--session",
            session_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "operator_handoff_blocked_by_scan"
    assert "blocking leak scanner findings" in payload["message"]


def test_operator_handoff_schema_file_defines_v1_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas" / "operator_handoff.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "TCS-Cosheaf Operator Handoff Bundle"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == 1
    assert schema["properties"]["kind"]["const"] == "operator_handoff_bundle"
    assert schema["properties"]["authority_notice"]["const"] == (
        OPERATOR_SESSION_AUTHORITY_NOTICE
    )
    assert schema["properties"]["accepted_write_performed"]["const"] is False
    assert schema["properties"]["human_review_created"]["const"] is False
    assert schema["properties"]["promotion_performed"]["const"] is False
    assert schema["properties"]["verifier_result_mutated"]["const"] is False
