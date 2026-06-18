from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.app import CosheafApp, open_app
from cosheaf.services.models import ErrorResult
from cosheaf.storage.repo import RepoContext


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _artifact_data() -> dict[str, Any]:
    return {
        "id": "claim.fixture.server-readiness",
        "type": "claim",
        "title": "Server readiness fixture claim",
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["server-readiness"],
        "statement": "A future server can call app services directly.",
        "evidence": [],
        "review": {
            "state": "requested",
            "notes": "No human review has been performed.",
        },
        "risk": {"level": "low", "notes": "Server-readiness test fixture."},
    }


def test_app_entrypoints_cover_server_readiness_without_cli_subprocess(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/server-readiness.yaml",
        _artifact_data(),
    )
    app = CosheafApp(RepoContext(tmp_path))

    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("server-readiness app calls must not shell out to CLI")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    assert open_app(tmp_path).workspace_info().repo_root == tmp_path

    issue = app.create_issue(
        issue_id="issue.fixture.server-readiness",
        title="Server readiness fixture issue",
        summary="Exercise app and forge entrypoints without CLI subprocesses.",
        authors=["tester"],
        labels=["server-readiness"],
        related_artifacts=["claim.fixture.server-readiness"],
    )
    assert issue.relative_path.as_posix() == (
        "issues/open/issue.fixture.server-readiness.yaml"
    )
    assert issue.github_issue_created is False
    assert issue.artifact_status_changed is False

    workspace = app.workspace_info()
    assert workspace.mode == "legacy"
    assert workspace.kb_roots[0].name == "default"

    validation = app.validate_repository()
    assert validation.ok is True
    assert validation.checked_count == 2

    gate = app.run_gate(timestamp="20260619T010000000000Z")
    assert gate.report.verdict == "pass"

    context_pack = app.build_context(
        "issue.fixture.server-readiness",
        max_full_artifacts=0,
    )
    assert context_pack.issue_id == "issue.fixture.server-readiness"
    assert context_pack.task_dir.name == "issue.fixture.server-readiness"
    assert app.show_context(
        "issue.fixture.server-readiness",
        max_full_artifacts=0,
    ).startswith("# Context Pack")

    issue_preview = app.forge_issue_preview(issue.relative_path)
    assert issue_preview.kind == "github_issue"
    assert issue_preview.network_calls_performed is False
    assert issue_preview.github_issue_plan is not None
    assert issue_preview.github_issue_plan.issue_id == issue.issue.id
    assert issue_preview.github_issue_plan.github_issue_created is False

    pr_preview = app.forge_pr_preview(base="main", head="arch-server-readiness-tests")
    assert pr_preview.kind == "github_pr"
    assert pr_preview.network_calls_performed is False
    assert pr_preview.github_writes_performed is False
    assert pr_preview.github_pr_plan is not None
    assert pr_preview.github_pr_plan.github_pr_created is False


def test_error_result_serializes_for_server_boundaries() -> None:
    error = ErrorResult(
        code="server_readiness_fixture",
        message="Server-readiness fixture error.",
        remediation="Return this DTO to the caller without raising raw exceptions.",
        blocking=True,
        related_path="issues/open/issue.fixture.server-readiness.yaml",
        related_artifact="claim.fixture.server-readiness",
        details={"surface": "app"},
    )

    payload = error.to_dict()
    assert payload["schema_version"] == 1
    assert payload["code"] == "server_readiness_fixture"
    assert payload["blocking"] is True
    assert ErrorResult.model_validate(payload) == error
    assert json.loads(error.to_json()) == payload


def test_server_readiness_doc_lists_future_server_functions() -> None:
    text = Path("docs/SERVER_READINESS.md").read_text(encoding="utf-8")
    expected_functions = [
        "open_app",
        "CosheafApp.workspace_info",
        "CosheafApp.validate_repository",
        "CosheafApp.validate_artifact_file",
        "CosheafApp.run_gate",
        "CosheafApp.build_context",
        "CosheafApp.show_context",
        "CosheafApp.create_issue",
        "CosheafApp.forge_status",
        "CosheafApp.forge_issue_preview",
        "CosheafApp.forge_pr_preview",
        "ErrorResult",
    ]

    for function_name in expected_functions:
        assert f"`{function_name}`" in text
