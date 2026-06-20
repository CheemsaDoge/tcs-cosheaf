from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.app import open_app
from cosheaf.server import ReadOnlySiteApi


class _FakeCredentialProvider:
    def __init__(self) -> None:
        self.calls = 0

    def provider_name(self) -> str:
        return "fake-provider"

    def has_github_token(self) -> bool:
        self.calls += 1
        return True


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Tester")
    _git(repo, "config", "user.email", "tester@example.invalid")
    (repo / ".gitignore").write_text(".cosheaf/\n", encoding="utf-8")
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Initial commit")


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _audit_entries(repo_root: Path) -> list[dict[str, Any]]:
    audit_path = repo_root / ".cosheaf" / "audit" / "web-actions.jsonl"
    return [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _post(api: ReadOnlySiteApi, path: str, payload: dict[str, Any]) -> Any:
    return api.handle("POST", path, json.dumps(payload))


def _record(
    report: list[dict[str, str]],
    step: str,
    operation: str,
    response: Any,
    *,
    note: str = "",
) -> None:
    assert response.status == 200, response.payload
    report.append(
        {
            "step": step,
            "operation": operation,
            "status": "completed",
            "kind": str(response.payload.get("kind", "")),
            "note": note,
        }
    )


def test_local_workbench_e2e_happy_path_documents_all_steps(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _init_repo(tmp_path)
    evidence_path = tmp_path / "docs" / "workbench-e2e-evidence.md"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("Reviewed fixture evidence.\n", encoding="utf-8")

    original_run = subprocess.run
    gh_calls: list[list[str]] = []

    def fake_subprocess_run(
        args: list[str],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        if args[:3] == ["gh", "pr", "create"]:
            gh_calls.append(args)
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout="https://github.com/CheemsaDoge/tcs-cosheaf/pull/582\n",
                stderr="",
            )
        return original_run(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    credentials = _FakeCredentialProvider()
    api = ReadOnlySiteApi(
        open_app(tmp_path),
        local_actor="Ada Local",
        credential_provider=credentials,
    )
    scenario_report: list[dict[str, str]] = []
    issue_id = "issue.fixture.workbench.e2e"
    artifact_id = "claim.fixture.workbench.e2e"
    branch = "workbench-e2e-fixture"

    health = api.handle("GET", "/api/health")
    assert health.payload["local_actor_configured"] is True
    _record(
        scenario_report,
        "start server in local write-enabled mode",
        "real",
        health,
        note="in-process ReadOnlySiteApi harness with local actor",
    )

    dashboard = api.handle("GET", "/api/workspace/live")
    _record(scenario_report, "open dashboard", "real", dashboard)

    issue_payload = {
        "issue_id": issue_id,
        "title": "Workbench E2E fixture",
        "summary": "Exercise the local Workbench happy path without manual CLI.",
        "authors": ["Ada Local"],
        "labels": ["workbench", "e2e"],
        "related_artifacts": [artifact_id],
        "related_sources": [],
        "scope": "private",
    }
    issue_preview = _post(api, "/api/issues/preview-create", issue_payload)
    assert issue_preview.payload["repo_writes_performed"] is False
    issue_created = _post(api, "/api/issues/create", {**issue_payload, "confirm": True})
    _record(scenario_report, "create local issue", "real", issue_created)

    artifact_payload = {
        "artifact_id": artifact_id,
        "artifact_type": "claim",
        "title": "Workbench E2E claim",
        "domain": ["testing"],
        "status": "locally_tested",
        "statement": "Triangle graph $K_3$ is used as a fixture.",
        "authors": ["Ada Local"],
        "tags": ["workbench", "e2e"],
        "depends_on": [],
        "supersedes": [],
    }
    artifact_preview = _post(api, "/api/artifacts/preview-create", artifact_payload)
    assert artifact_preview.payload["repo_writes_performed"] is False
    artifact_created = _post(
        api,
        "/api/artifacts/create",
        {**artifact_payload, "confirm": True},
    )
    source_written = _post(
        api,
        f"/api/artifacts/{artifact_id}/source",
        {
            "kind": "book",
            "title": "Graph Theory Fixture",
            "authors": ["Ada Author"],
            "year": 2026,
            "page": "1",
            "notes": "Fixture source metadata for the E2E path.",
            "confirm": True,
        },
    )
    evidence_written = _post(
        api,
        f"/api/artifacts/{artifact_id}/evidence",
        {
            "kind": "note",
            "path": "docs/workbench-e2e-evidence.md",
            "summary": "Fixture evidence reviewed by the local operator.",
            "confirm": True,
        },
    )
    assert source_written.status == 200
    assert evidence_written.status == 200
    _record(
        scenario_report,
        "create draft artifact",
        "real",
        artifact_created,
        note="pre-accepted artifact plus source/evidence metadata",
    )

    context_preview = _post(
        api,
        f"/api/context/{issue_id}/preview-build",
        {"role": "orchestrator", "public_only": False, "max_cards": 5},
    )
    assert context_preview.payload["repo_writes_performed"] is False
    context_built = _post(
        api,
        f"/api/context/{issue_id}/build",
        {
            "role": "orchestrator",
            "public_only": False,
            "max_cards": 5,
            "confirm": True,
        },
    )
    _record(scenario_report, "build context", "real", context_built)

    validate_run = _post(api, "/api/validate/run", {})
    assert validate_run.payload["validation"]["ok"] is True
    _record(scenario_report, "run validate", "real", validate_run)

    gate_run = _post(api, "/api/gate/run", {})
    assert gate_run.payload["gate"]["verdict"] == "pass"
    _record(scenario_report, "run gate", "real", gate_run)

    packet_payload = {"issue_id": issue_id, "artifact_id": artifact_id}
    packet_preview = _post(api, "/api/reviews/packets/preview", packet_payload)
    assert packet_preview.payload["repo_writes_performed"] is False
    packet_created = _post(
        api,
        "/api/reviews/packets/create",
        {**packet_payload, "confirm": True},
    )
    _record(scenario_report, "generate review packet", "real", packet_created)

    decision_payload = {
        "artifact_id": artifact_id,
        "reviewer": "Ada Reviewer",
        "decision": "accept_for_private_use",
        "review_notes": "Checked source, evidence, dependencies, and gate context.",
        "scope": "private",
        "limitations": "Fixture review only.",
        "dependencies_checked": True,
        "sources_checked": True,
        "evidence_checked": True,
        "gate_state_acknowledged": True,
        "explicit_human_confirmation": True,
    }
    decision_preview = _post(api, "/api/reviews/decisions/preview", decision_payload)
    assert decision_preview.payload["repo_writes_performed"] is False
    decision_created = _post(
        api,
        "/api/reviews/decisions/create",
        {**decision_payload, "confirm": True},
    )
    _record(scenario_report, "record human review decision", "real", decision_created)

    promotion_payload = {
        "target_state": "accepted",
        "actor": "Ada Reviewer",
    }
    promotion_preview = _post(
        api,
        f"/api/artifacts/{artifact_id}/promotion/preview",
        promotion_payload,
    )
    assert promotion_preview.payload["promotion_blocked"] is False
    _record(scenario_report, "preview promotion", "real", promotion_preview)

    promotion_confirmed = _post(
        api,
        f"/api/artifacts/{artifact_id}/promotion/confirm",
        {
            **promotion_payload,
            "typed_confirmation": "PROMOTE TO ACCEPTED",
            "promotion_justification": "Human-reviewed fixture promotion.",
            "confirm": True,
        },
    )
    _record(
        scenario_report,
        "promote to permitted target state in fixture repo",
        "real",
        promotion_confirmed,
    )

    branch_preview = _post(
        api,
        "/api/forge/branch/preview",
        {"branch": branch, "allow_dirty": True},
    )
    assert branch_preview.payload["repo_writes_performed"] is False
    branch_created = _post(
        api,
        "/api/forge/branch/create",
        {"branch": branch, "allow_dirty": True, "confirm": True},
    )
    commit_preview = _post(
        api,
        "/api/forge/commit/preview",
        {"message": "Add Workbench E2E fixture", "stage_all": True},
    )
    assert commit_preview.payload["repo_writes_performed"] is False
    commit_created = _post(
        api,
        "/api/forge/commit/create",
        {
            "message": "Add Workbench E2E fixture",
            "stage_all": True,
            "confirm": True,
        },
    )
    assert branch_created.payload["forge_action"]["branch"] == branch
    assert commit_created.payload["forge_action"]["commit_hash"]
    _record(scenario_report, "create branch/commit", "real", commit_created)

    pr_preview = _post(
        api,
        "/api/forge/prs/preview",
        {"base": "main", "head": branch},
    )
    assert pr_preview.payload["github_pr_plan"]["head"] == branch
    _record(scenario_report, "preview PR", "real", pr_preview)

    pr_created = _post(
        api,
        "/api/forge/prs/create",
        {"base": "main", "head": branch, "draft": True, "confirm": True},
    )
    assert pr_created.payload["forge_action"]["github_pr_created"] is True
    assert gh_calls == [
        [
            "gh",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            branch,
            "--title",
            f"Merge {branch} into main",
            "--body",
            f"Forge-created PR for {branch} into main.",
            "--draft",
        ]
    ]
    _record(
        scenario_report,
        "confirm PR creation with mocked GitHub/gh",
        "mocked",
        pr_created,
    )

    audit = api.handle("GET", "/api/audit/recent")
    accepted_path = (
        tmp_path / "kb" / "accepted" / "claims" / "claim.fixture.workbench.e2e.yaml"
    )
    assert accepted_path.is_file()
    assert _read_yaml(accepted_path)["status"] == "accepted"
    assert _git(tmp_path, "branch", "--show-current") == branch
    assert _git(tmp_path, "log", "-1", "--pretty=%s") == "Add Workbench E2E fixture"
    assert any(
        entry["action"] == "promotion.confirm"
        for entry in _audit_entries(tmp_path)
    )
    _record(scenario_report, "verify audit log and repo files", "real", audit)

    assert [item["step"] for item in scenario_report] == [
        "start server in local write-enabled mode",
        "open dashboard",
        "create local issue",
        "create draft artifact",
        "build context",
        "run validate",
        "run gate",
        "generate review packet",
        "record human review decision",
        "preview promotion",
        "promote to permitted target state in fixture repo",
        "create branch/commit",
        "preview PR",
        "confirm PR creation with mocked GitHub/gh",
        "verify audit log and repo files",
    ]
    assert {item["operation"] for item in scenario_report} == {"real", "mocked"}
    assert not [
        item
        for item in scenario_report
        if item["operation"] in {"skipped", "deferred"}
    ]
    assert credentials.calls == 1
