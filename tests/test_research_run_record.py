from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from cosheaf.research.run import (
    RESEARCH_RUN_AUTHORITY_NOTICE,
    ResearchRunCommandRecord,
    ResearchRunCommandStatus,
    ResearchRunOperatorKind,
    ResearchRunOutputKind,
    ResearchRunOutputRef,
    ResearchRunRecord,
    ResearchRunStatus,
)

ROOT = Path(__file__).resolve().parents[1]
STARTED_AT = datetime(2026, 6, 15, 1, 0, tzinfo=UTC)
ENDED_AT = datetime(2026, 6, 15, 1, 1, tzinfo=UTC)


def test_research_run_serializes_deterministically_and_redacts_command() -> None:
    command = ResearchRunCommandRecord(
        argv=("python", "-m", "pytest", "--token", "ghp_secretValue"),
        cwd=".",
        started_at=STARTED_AT,
        ended_at=ENDED_AT,
        exit_code=0,
        status=ResearchRunCommandStatus.COMPLETED,
        stdout_path=".cosheaf/runs/run.issue.fixture.0001/stdout.txt",
        stderr_path=".cosheaf/runs/run.issue.fixture.0001/stderr.txt",
    )
    record = ResearchRunRecord.start(
        run_id="run.issue.fixture.0001",
        issue_id="issue.fixture",
        operator_kind=ResearchRunOperatorKind.EXTERNAL,
        operator_label="Codex CLI",
        now=STARTED_AT,
    ).with_command(command)

    payload = record.to_dict()

    assert list(payload) == [
        "schema_version",
        "run_id",
        "issue_id",
        "operator_kind",
        "operator_label",
        "status",
        "started_at",
        "ended_at",
        "stop_reason",
        "base_commit",
        "head_commit",
        "dirty_state_note",
        "workspace_info_summary",
        "context_packs",
        "commands",
        "artifacts_read",
        "artifacts_touched",
        "controlled_write_outputs",
        "worker_bundle_paths",
        "verifier_evidence_paths",
        "checked_counterexample_evidence_paths",
        "failure_log_entries_added",
        "validation_reports",
        "gate_reports",
        "pr_references",
        "issue_references",
        "limitations",
        "operator_notes",
        "authority_notice",
        "accepted_write_performed",
    ]
    assert record.status is ResearchRunStatus.IN_PROGRESS
    assert record.authority_notice == RESEARCH_RUN_AUTHORITY_NOTICE
    assert record.accepted_write_performed is False
    assert record.commands[0].argv == (
        "python",
        "-m",
        "pytest",
        "--token",
        "<redacted>",
    )
    assert "ghp_secretValue" not in record.to_json()


def test_research_run_finalize_requires_terminal_status_and_reason() -> None:
    record = ResearchRunRecord.start(
        run_id="run.issue.fixture.0001",
        issue_id="issue.fixture",
        operator_kind="external",
        operator_label="Codex CLI",
        now=STARTED_AT,
    )

    finalized = record.finalize(
        status=ResearchRunStatus.COMPLETED,
        stop_reason="all requested checks passed",
        now=ENDED_AT,
    )

    assert finalized.status is ResearchRunStatus.COMPLETED
    assert finalized.ended_at == ENDED_AT
    assert finalized.stop_reason == "all requested checks passed"
    with pytest.raises(ValueError, match="terminal"):
        finalized.with_artifact("claim.fixture", mode="read")


@pytest.mark.parametrize(
    "path",
    [
        "../outside.json",
        "C:/secret/run.json",
        "/tmp/run.json",
        "kb/accepted/claims/unsafe.yaml",
    ],
)
def test_research_run_output_paths_are_repo_local_and_nonaccepted(path: str) -> None:
    with pytest.raises(ValidationError):
        ResearchRunOutputRef(kind=ResearchRunOutputKind.CONTROLLED_WRITE, path=path)


def test_research_run_schema_file_defines_v1_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas" / "research_run.schema.json").read_text(encoding="utf-8")
    )

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "TCS-Cosheaf Research Run Record"
    assert schema["additionalProperties"] is False
    assert "run_id" in schema["required"]
    assert schema["properties"]["status"]["enum"] == [
        "in_progress",
        "completed",
        "failed",
        "blocked",
        "cancelled",
    ]
    assert schema["properties"]["authority_notice"]["const"] == (
        RESEARCH_RUN_AUTHORITY_NOTICE
    )
