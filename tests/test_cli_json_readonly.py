from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

import cosheaf
from cosheaf.cli import app

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    title: str,
    status: str = "accepted",
    domain: list[str] | None = None,
    tags: list[str] | None = None,
    statement: str = "Public fixture statement.",
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": artifact_type,
        "title": title,
        "domain": domain or ["testing"],
        "status": status,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": tags or [],
        "statement": statement,
        "evidence": [],
        "review": {
            "state": "human_reviewed",
            "notes": "Fixture review.",
        },
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _issue_data(
    *,
    issue_id: str,
    related_artifacts: list[str],
) -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "CLI JSON issue",
        "status": "open",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Issue for read-only CLI JSON smoke tests.",
        "related_artifacts": related_artifacts,
        "tags": ["cli-json"],
    }


def _write_repo(repo_root: Path) -> None:
    (repo_root / "context").mkdir(parents=True, exist_ok=True)
    (repo_root / "context" / "PROJECT_STATE.md").write_text(
        "# Project State\n\nFixture project state.\n",
        encoding="utf-8",
    )
    (repo_root / "context" / "INTERFACE_REGISTRY.md").write_text(
        "# Interface Registry\n\nFixture interface registry.\n",
        encoding="utf-8",
    )
    _write_yaml(
        repo_root,
        "kb/accepted/claims/public.yaml",
        _artifact_data(
            "claim.fixture.cli-json",
            title="CLI JSON public claim",
            tags=["cli-json"],
        ),
    )
    _write_yaml(
        repo_root,
        "issues/open/issue.fixture.cli-json.yaml",
        _issue_data(
            issue_id="issue.fixture.cli-json",
            related_artifacts=["claim.fixture.cli-json"],
        ),
    )


def _assert_json_output(output: str) -> Any:
    assert "\x1b[" not in output
    return json.loads(output)


def test_version_json_is_deterministic() -> None:
    result = runner.invoke(app, ["version", "--json"])

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload == {
        "schema_version": 1,
        "package": "tcs-cosheaf",
        "version": cosheaf.__version__,
    }


def test_interface_list_json_documents_stable_surface() -> None:
    result = runner.invoke(app, ["interface", "list", "--json"])

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["schema_version"] == 1
    assert payload["package"] == "tcs-cosheaf"
    assert payload["version"] == cosheaf.__version__
    assert payload["target_release"] == "v1.0.0"
    assert "does not grant proof" in payload["authority_notice"]

    preferred = {
        item["command"]: item["preferred_invocation"]
        for item in payload["stable_cli_surface"]
    }
    assert preferred["gate"] == "cosheaf gate run"
    assert preferred["research-run"] == "cosheaf research-run ..."
    assert preferred["mcp"] == "cosheaf mcp ..."
    assert preferred["server"] == (
        "cosheaf server serve --readonly --port 8765 --local-actor <name>"
    )

    aliases = {
        item["alias"]: item["preferred"] for item in payload["compatibility_aliases"]
    }
    assert aliases["cosheaf gate"] == "cosheaf gate run"
    assert aliases["cosheaf run"] == "cosheaf research-run"


def test_research_run_preferred_alias_help() -> None:
    preferred = runner.invoke(app, ["research-run", "--help"])
    compatibility = runner.invoke(app, ["run", "--help"])

    assert preferred.exit_code == 0, preferred.output
    assert compatibility.exit_code == 0, compatibility.output
    assert "Research-run provenance commands" in preferred.output
    assert "Research-run provenance commands" in compatibility.output


def test_workspace_info_json(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    result = runner.invoke(
        app,
        ["workspace", "info", "--repo-root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["schema_version"] == 1
    assert payload["workspace_name"] == tmp_path.name
    assert payload["mode"] == "legacy"
    assert payload["kb_roots"][0]["scope"] == "workspace"
    assert payload["kb_roots"][0]["readonly"] is False
    assert payload["policy"]["public_can_depend_on_private"] is False


def test_validate_json_success_and_failure(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    ok = runner.invoke(app, ["validate", "--repo-root", str(tmp_path), "--json"])

    assert ok.exit_code == 0, ok.output
    ok_payload = _assert_json_output(ok.output)
    assert ok_payload["schema_version"] == 1
    assert ok_payload["ok"] is True
    assert ok_payload["checked_count"] == 2
    assert ok_payload["failures"] == []

    _write_yaml(
        tmp_path,
        "kb/draft/claims/missing.yaml",
        _artifact_data(
            "claim.fixture.cli-json-missing",
            title="Missing dependency",
            status="draft",
        )
        | {"depends_on": ["claim.fixture.not-found"]},
    )

    failed = runner.invoke(app, ["validate", "--repo-root", str(tmp_path), "--json"])

    assert failed.exit_code == 1
    failed_payload = _assert_json_output(failed.output)
    assert failed_payload["ok"] is False
    assert failed_payload["failures"][0]["code"] == "validation_failed"
    assert failed_payload["failures"][0]["related_path"].endswith("missing.yaml")
    assert failed_payload["failures"][0]["related_artifact"] == (
        "claim.fixture.cli-json-missing"
    )


def test_gate_run_json(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["schema_version"] == 1
    assert payload["verdict"] == "pass"
    assert payload["report_json_path"].startswith(".cosheaf/reports/")
    assert payload["report_markdown_path"].startswith(".cosheaf/reports/")
    assert payload["blocking_issues"] == []


def test_memory_json_commands_remain_parseable(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    cards = runner.invoke(
        app,
        ["memory", "cards", "--repo-root", str(tmp_path), "--json"],
    )
    search = runner.invoke(
        app,
        ["memory", "search", "cli json", "--repo-root", str(tmp_path), "--json"],
    )

    assert cards.exit_code == 0, cards.output
    assert search.exit_code == 0, search.output
    cards_payload = _assert_json_output(cards.output)
    search_payload = _assert_json_output(search.output)
    assert cards_payload[0]["root_scope"] == "workspace"
    assert search_payload["schema_version"] == 1
    assert search_payload["cards"][0]["card"]["root_scope"] == "workspace"


def test_context_json_commands(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    built = runner.invoke(
        app,
        [
            "context",
            "build",
            "issue.fixture.cli-json",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    shown = runner.invoke(
        app,
        [
            "context",
            "show",
            "issue.fixture.cli-json",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert built.exit_code == 0, built.output
    assert shown.exit_code == 0, shown.output
    built_payload = _assert_json_output(built.output)
    shown_payload = _assert_json_output(shown.output)
    assert built_payload["schema_version"] == 1
    assert built_payload["issue_id"] == "issue.fixture.cli-json"
    assert built_payload["private_context_included"] is False
    assert built_payload["card_count"] == 1
    assert built_payload["full_artifact_count"] == 0
    assert built_payload["content_mode"] == "cards_only"
    assert "context/TASKS/issue.fixture.cli-json/CONTEXT.md" in built_payload["files"]
    assert shown_payload["schema_version"] == 1
    assert shown_payload["issue_id"] == "issue.fixture.cli-json"
    assert "# Context Pack: issue.fixture.cli-json" in shown_payload["content"]
    assert shown_payload["private_context_included"] is False


def test_orchestrator_plan_json_remains_parseable(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "orchestrator",
            "plan",
            "--issue",
            "issue.fixture.cli-json",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["schema_version"] == 1
    assert payload["issue_id"] == "issue.fixture.cli-json"


def test_artifact_failures_json_empty_for_artifact_without_failure_log(
    tmp_path: Path,
) -> None:
    _write_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "artifact",
            "failures",
            "claim.fixture.cli-json",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload == {
        "schema_version": 1,
        "kind": "artifact_failure_log",
        "artifact_id": "claim.fixture.cli-json",
        "artifact_path": "kb/accepted/claims/public.yaml",
        "root_name": "default",
        "root_scope": "workspace",
        "root_readonly": False,
        "failure_count": 0,
        "failure_log": [],
        "authority_notice": (
            "failure_log is research memory only; it is not proof, verifier "
            "success, checked counterexample evidence, human review, gate "
            "success, accepted status, or promotion evidence"
        ),
    }


def test_artifact_failures_json_returns_failure_log_entries(tmp_path: Path) -> None:
    data = _artifact_data(
        "claim.fixture.failure-log",
        title="Failure log fixture",
        status="draft",
    )
    data["failure_log"] = [
        {
            "failure_id": "failure.fixture.0001",
            "attempted_at": "2026-06-14T00:00:00Z",
            "recorded_by": "tester",
            "origin": "human",
            "attempt_kind": "proof_attempt",
            "target": "claim.fixture.failure-log",
            "direction": "Try direct induction.",
            "summary": "Checked the direct induction setup.",
            "failed_because": "The invariant is not preserved.",
            "evidence_paths": [".cosheaf/logs/failure-fixture.log"],
            "related_verifier_results": [],
            "related_counterexample_candidates": [],
            "next_possible_directions": ["Try a stronger invariant."],
            "status": "open",
            "limitations": "This failed direction does not refute the claim.",
        }
    ]
    _write_yaml(tmp_path, "kb/draft/claims/failure-log.yaml", data)

    result = runner.invoke(
        app,
        [
            "artifact",
            "failures",
            "claim.fixture.failure-log",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["artifact_path"] == "kb/draft/claims/failure-log.yaml"
    assert payload["root_scope"] == "workspace"
    assert payload["failure_count"] == 1
    assert payload["failure_log"][0]["failure_id"] == "failure.fixture.0001"
    assert payload["failure_log"][0]["origin"] == "human"
    assert payload["failure_log"][0]["status"] == "open"
    assert "not proof" in payload["authority_notice"]


def test_artifact_failures_json_missing_artifact_error(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "artifact",
            "failures",
            "claim.fixture.missing",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json_output(result.output)
    assert payload == {
        "schema_version": 1,
        "code": "artifact_not_found",
        "message": "artifact not found: claim.fixture.missing",
        "remediation": "Check the artifact ID and rerun the command.",
        "blocking": True,
        "related_path": None,
        "related_artifact": "claim.fixture.missing",
        "details": {},
    }


def test_readonly_json_errors_are_structured(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "context",
            "build",
            "issue.fixture.missing",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json_output(result.output)
    assert payload["schema_version"] == 1
    assert payload["code"] == "context_build_failed"
    assert payload["blocking"] is True
    assert "issue.fixture.missing" in payload["message"]
