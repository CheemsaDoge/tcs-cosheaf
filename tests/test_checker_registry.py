from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.checkers import (
    CheckerInput,
    CheckerResult,
    CheckerStatus,
    CheckerType,
    default_checker_registry,
)
from cosheaf.checkers.storage import run_checker_and_store
from cosheaf.storage.repo import RepoContext


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n")


def _artifact_data(
    artifact_id: str,
    *,
    status: str = "draft",
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "Checker fixture",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-18T00:00:00Z",
        "updated_at": "2026-06-18T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": [],
        "statement": "Checker fixture statement.",
        "evidence": [],
        "sources": sources or [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def test_default_checker_registry_allowlist() -> None:
    registry = default_checker_registry()

    assert registry.checker_ids == (
        "artifact_path_policy_check",
        "authority_overclaim_check",
        "gate_check",
        "lean_optional_check",
        "private_leak_check",
        "python_local_check",
        "sat_optional_check",
        "schema_check",
        "smt_optional_check",
        "source_metadata_check",
    )


def test_checker_result_status_serialization_and_skipped_not_pass() -> None:
    result = CheckerResult(
        checker_id="sat_optional_check",
        checker_type=CheckerType.SAT_OPTIONAL_CHECK,
        status=CheckerStatus.SKIPPED,
        started_at=datetime(2026, 6, 18, tzinfo=UTC),
        ended_at=datetime(2026, 6, 18, tzinfo=UTC),
        message="optional SAT tool unavailable",
    )

    payload = result.to_dict()

    assert payload["status"] == "skipped"
    assert not result.is_pass
    assert result.is_skipped
    assert not result.is_blocking
    assert payload["authority_notice"]["skipped_is_not_pass"] is True


def test_optional_tool_missing_returns_skipped(tmp_path: Path) -> None:
    registry = default_checker_registry()
    record = run_checker_and_store(
        registry,
        RepoContext(tmp_path),
        "sat_optional_check",
        CheckerInput(
            payload={"tool_command": "cosheaf-definitely-missing-sat-tool"}
        ),
    )

    assert record.result.status is CheckerStatus.SKIPPED
    assert not record.result.is_pass
    assert (tmp_path / record.result_path).is_file()
    assert (tmp_path / record.stdout_path).is_file()
    assert (tmp_path / record.stderr_path).is_file()


def test_authority_overclaim_rejected() -> None:
    registry = default_checker_registry()
    execution = registry.run(
        "authority_overclaim_check",
        RepoContext(Path(".")),
        CheckerInput(
            text="This draft is an accepted theorem after verifier passed.",
            payload={"human_reviewed": True},
        ),
    )

    assert execution.result.status is CheckerStatus.BLOCKED_BY_POLICY
    assert execution.result.is_blocking
    assert "human_reviewed" in execution.stderr


def test_public_private_leak_rejected() -> None:
    registry = default_checker_registry()
    execution = registry.run(
        "private_leak_check",
        RepoContext(Path(".")),
        CheckerInput(mode="public", paths=("kb/private/draft/claims/x.yaml",)),
    )

    assert execution.result.status is CheckerStatus.BLOCKED_BY_POLICY
    assert execution.result.is_blocking


def test_path_policy_rejects_accepted_kb_path(tmp_path: Path) -> None:
    registry = default_checker_registry()
    execution = registry.run(
        "artifact_path_policy_check",
        RepoContext(tmp_path),
        CheckerInput(paths=("kb/accepted/claims/claim.fixture.yaml",)),
    )

    assert execution.result.status is CheckerStatus.BLOCKED_BY_POLICY
    assert execution.result.is_blocking


def test_source_metadata_checker_fails_missing_source(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "kb" / "accepted" / "claims" / "claim.fixture.yaml",
        _artifact_data("claim.fixture.source", status="accepted"),
    )
    registry = default_checker_registry()
    execution = registry.run(
        "source_metadata_check",
        RepoContext(tmp_path),
        CheckerInput(artifact_id="claim.fixture.source"),
    )

    assert execution.result.status is CheckerStatus.FAIL
    assert "sources" in execution.result.message


def test_python_local_checker_runs_repo_local_script(tmp_path: Path) -> None:
    script = tmp_path / "checks" / "ok.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('checker ok')\n", encoding="utf-8")
    registry = default_checker_registry()
    record = run_checker_and_store(
        registry,
        RepoContext(tmp_path),
        "python_local_check",
        CheckerInput(payload={"script_path": "checks/ok.py"}),
    )

    assert record.result.status is CheckerStatus.PASS
    assert (tmp_path / record.stdout_path).read_text(encoding="utf-8") == (
        "checker ok\n"
    )


def test_schema_checker_passes_for_minimal_repo(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / "kb" / "draft" / "claims" / "claim.fixture.yaml",
        _artifact_data("claim.fixture.schema"),
    )
    registry = default_checker_registry()
    record = run_checker_and_store(
        registry,
        RepoContext(tmp_path),
        "schema_check",
        CheckerInput(),
    )

    assert record.result.status is CheckerStatus.PASS

