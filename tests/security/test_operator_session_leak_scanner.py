from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.operator_session import (
    OPERATOR_SESSION_AUTHORITY_NOTICE,
    OperatorPolicyMode,
    OperatorToolCallRecord,
    OperatorToolCallStatus,
    append_operator_session_event,
    operator_session_events_path,
    operator_session_path,
    start_operator_session,
)
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "operator-session-scan-fixture"',
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


def _artifact_data(
    artifact_id: str,
    *,
    title: str,
    status: str,
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": title,
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-16T00:00:00Z",
        "updated_at": "2026-06-16T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["operator-session-scan"],
        "statement": f"{title}.",
        "evidence": [],
        "sources": sources or [],
        "review": {"state": "requested", "notes": "Operator scan fixture."},
        "risk": {"level": "low", "notes": "Operator scan fixture risk."},
    }


def _source_fixture() -> dict[str, Any]:
    return {
        "kind": "paper",
        "title": "Operator Session Scanner Fixture Source",
        "authors": ["A. Maintainer"],
        "year": 2026,
        "doi": "10.1145/operator-session-scan-fixture",
        "arxiv": "",
        "url": "",
        "theorem_number": "Definition 1",
        "page": "1",
        "notes": "Deterministic scanner fixture.",
    }


def _fixture_repo(repo_root: Path) -> RepoContext:
    _write_workspace_config(repo_root)
    _write_yaml(
        repo_root,
        "kb/public/accepted/claims/public.yaml",
        _artifact_data(
            "claim.fixture.scan-public",
            title="Scanner public claim",
            status="accepted",
            sources=[_source_fixture()],
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/private.yaml",
        _artifact_data(
            "claim.fixture.scan-private",
            title="Scanner private claim",
            status="draft",
        ),
    )
    return RepoContext(repo_root)


def _start_session(
    context: RepoContext,
    *,
    policy_mode: OperatorPolicyMode = OperatorPolicyMode.PUBLIC_ONLY,
    session_id: str = "session.issue.fixture.scan.0001",
) -> str:
    result = start_operator_session(
        context,
        issue_id="issue.fixture.scan",
        policy_mode=policy_mode,
        operator_label="scan test operator",
        session_id=session_id,
        now=datetime(2026, 6, 16, 9, 0, tzinfo=UTC),
    )
    return result.session.session_id


def _assert_json(output: str) -> dict[str, Any]:
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def test_operator_session_scan_clean_session_writes_runtime_report(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)
    session_id = _start_session(context)
    event = OperatorToolCallRecord(
        event_id="event.workspace-info.0001",
        tool_name="workspace_info",
        status=OperatorToolCallStatus.COMPLETED,
        recorded_at=datetime(2026, 6, 16, 9, 1, tzinfo=UTC),
        input_metadata={
            "argument_count": "0",
            "argument_names": "none",
            "mcp_mode": "public_adapter",
            "session_mode": "public_only",
        },
        result_summary="completed tool call: workspace_info",
    )
    append_operator_session_event(context, session_id=session_id, event=event)
    session_before = (tmp_path / operator_session_path(session_id)).read_text(
        encoding="utf-8"
    )

    result = runner.invoke(
        app,
        [
            "operator",
            "session",
            "scan",
            session_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    assert payload["kind"] == "operator_session_scan"
    assert payload["session_id"] == session_id
    assert payload["finding_count"] == 0
    assert payload["blocking_finding_count"] == 0
    assert payload["handoff_blocked"] is False
    assert payload["accepted_write_performed"] is False
    assert payload["authority_notice"] == OPERATOR_SESSION_AUTHORITY_NOTICE
    assert payload["findings"] == []
    report_path = tmp_path / payload["report_path"]
    assert report_path.is_file()
    assert json.loads(report_path.read_text(encoding="utf-8")) == payload
    assert (tmp_path / operator_session_path(session_id)).read_text(
        encoding="utf-8"
    ) == session_before


def test_operator_session_scan_detects_public_only_leaks_and_blocks_handoff(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)
    session_id = _start_session(context)
    session_path = tmp_path / operator_session_path(session_id)
    session_data = json.loads(session_path.read_text(encoding="utf-8"))
    session_data["operator_notes"] = [
        "BEGIN HIDDEN REASONING: chain of thought should not be stored.",
        "Authorization: Bearer leakedoperatorbearertoken123456",
        "Please mark human_reviewed and promote this artifact.",
    ]
    session_path.write_text(
        json.dumps(session_data, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    leaked_event = {
        "schema_version": 1,
        "session_id": session_id,
        "sequence": 1,
        "event_kind": "tool_call",
        "recorded_at": "2026-06-16T09:02:00Z",
        "event": {
            "event_id": "event.provider.0001",
            "tool_name": "provider_call",
            "status": "completed",
            "recorded_at": "2026-06-16T09:02:00Z",
            "input_metadata": {
                "artifact_id": "claim.fixture.scan-private",
                "query": "private-secret",
                "path": "kb/private/draft/claims/private.yaml",
                "write_path": "kb/accepted/claims/claim.bad.yaml",
                "absolute_path": (
                    "C:\\Users\\ywjhn\\research\\kb\\private\\claim.yaml"
                ),
                "env_dump": (
                    "PATH=C:\\Tools\n"
                    "HOME=C:\\Users\\ywjhn\n"
                    "OPENAI_API_KEY=sk-proj-leakedoperatorsecret123456"
                ),
            },
            "provider_payload": {"messages": [{"role": "user", "content": "..."}]},
            "result_summary": "raw provider response included private-secret",
            "warning_codes": [],
        },
        "authority_notice": OPERATOR_SESSION_AUTHORITY_NOTICE,
    }
    events_path = tmp_path / operator_session_events_path(session_id)
    events_path.write_text(json.dumps(leaked_event, ensure_ascii=True) + "\n")

    result = runner.invoke(
        app,
        [
            "operator",
            "session",
            "scan",
            session_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["kind"] == "operator_session_scan"
    assert payload["session_id"] == session_id
    assert payload["handoff_blocked"] is True
    assert payload["blocking_finding_count"] >= 1
    codes = {finding["code"] for finding in payload["findings"]}
    assert codes >= {
        "api_key",
        "bearer_token",
        "environment_dump",
        "secret_env_value",
        "hidden_reasoning",
        "private_artifact_id",
        "private_path_reference",
        "absolute_private_path",
        "accepted_write_attempt",
        "provider_payload",
        "authority_claim",
    }
    report_path = tmp_path / payload["report_path"]
    assert report_path.is_file()
    assert json.loads(report_path.read_text(encoding="utf-8")) == payload


def test_operator_session_scan_missing_session_returns_structured_error(
    tmp_path: Path,
) -> None:
    _fixture_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "operator",
            "session",
            "scan",
            "session.issue.missing.0001",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "operator_session_not_found"
