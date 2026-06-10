from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_json(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n")
    return path


def _write_json_with_bom(
    repo_root: Path,
    relative_path: str,
    data: dict[str, Any],
) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=True, indent=2) + "\n"
    path.write_bytes(payload.encode("utf-8-sig"))
    return path


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "provider-cli-fixture"',
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
    tags: list[str],
    statement: str,
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": title,
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-10T00:00:00Z",
        "updated_at": "2026-06-10T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": tags,
        "statement": statement,
        "evidence": [],
        "review": {"state": "requested", "notes": "Provider CLI fixture review."},
        "risk": {"level": "low", "notes": "Provider CLI fixture risk."},
    }


def _issue_data(issue_id: str, *, related_artifacts: list[str]) -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Provider CLI preview test",
        "status": "open",
        "created_at": "2026-06-10T00:00:00Z",
        "updated_at": "2026-06-10T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": (
            "The private artifact mentions supersecret-token but public preview "
            "must not include it."
        ),
        "related_artifacts": related_artifacts,
        "tags": ["supersecret-token"],
    }


def _fixture_repo(repo_root: Path) -> None:
    _write_workspace_config(repo_root)
    _write_yaml(
        repo_root,
        "kb/public/accepted/claims/public.yaml",
        _artifact_data(
            "claim.fixture.provider-cli-public",
            title="Public provider CLI claim",
            status="accepted",
            tags=["provider-cli"],
            statement="Public provider CLI context.",
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/private.yaml",
        _artifact_data(
            "claim.fixture.provider-cli-private",
            title="supersecret-token private provider CLI draft",
            status="draft",
            tags=["supersecret-token"],
            statement="Private context with API-like value sk-private-fixture.",
            depends_on=["claim.fixture.provider-cli-public"],
        ),
    )
    _write_yaml(
        repo_root,
        "issues/open/provider-cli.yaml",
        _issue_data(
            "issue.fixture.provider-cli",
            related_artifacts=[
                "claim.fixture.provider-cli-public",
                "claim.fixture.provider-cli-private",
            ],
        ),
    )


def _assert_json_output(output: str) -> dict[str, Any]:
    assert "\x1b[" not in output
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def test_provider_list_json_is_agent_parseable() -> None:
    result = runner.invoke(app, ["provider", "list", "--json"])

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["schema_version"] == 1
    assert [provider["provider"] for provider in payload["providers"]] == [
        "fake",
        "openai",
    ]
    assert payload["providers"][0]["mode"] == "fake"
    assert payload["providers"][0]["network"] == "not_used"
    assert payload["providers"][1]["mode"] == "openai_compatible"
    assert payload["providers"][1]["real_run_cli"] is False


def test_provider_config_check_redacts_secret_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COSHEAF_TEST_API_KEY", "sk-test-secret")

    result = runner.invoke(
        app,
        [
            "provider",
            "config-check",
            "--repo-root",
            str(tmp_path),
            "--provider",
            "openai",
            "--api-key-env",
            "COSHEAF_TEST_API_KEY",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "sk-test-secret" not in result.output
    payload = _assert_json_output(result.output)
    assert payload["provider"] == "openai"
    assert payload["mode"] == "openai_compatible"
    assert payload["enabled"] is False
    assert payload["api_key_env"] == "COSHEAF_TEST_API_KEY"
    assert payload["api_key_present"] is True
    assert payload["api_key_value"] == "<redacted>"
    assert payload["real_run_cli"] is False


def test_provider_config_check_rejects_unimplemented_provider(
    tmp_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "provider",
            "config-check",
            "--repo-root",
            str(tmp_path),
            "--provider",
            "anthropic",
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json_output(result.output)
    assert payload["code"] == "provider_unsupported"
    assert payload["details"]["supported_providers"] == "fake,openai"


def test_provider_preview_send_defaults_to_public_only(tmp_path: Path) -> None:
    _fixture_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "provider",
            "preview-send",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.fixture.provider-cli",
            "--provider",
            "fake",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["provider"] == "fake"
    assert payload["preview"]["public_only"] is True
    assert payload["preview"]["private_context_included"] is False
    assert payload["preview"]["root_scopes"] == ["public"]
    assert payload["payload_shape"]["artifact_count"] == 1
    assert payload["payload_shape"]["estimated_tokens"] > 0
    assert "claim.fixture.provider-cli-public" in result.output
    assert "claim.fixture.provider-cli-private" not in result.output
    assert "supersecret-token" not in result.output
    assert "sk-private-fixture" not in result.output


def test_provider_preview_send_requires_private_policy_and_consent(
    tmp_path: Path,
) -> None:
    _fixture_repo(tmp_path)

    denied = runner.invoke(
        app,
        [
            "provider",
            "preview-send",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.fixture.provider-cli",
            "--provider",
            "openai",
            "--include-private",
            "--json",
        ],
    )
    allowed = runner.invoke(
        app,
        [
            "provider",
            "preview-send",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.fixture.provider-cli",
            "--provider",
            "openai",
            "--include-private",
            "--policy-mode",
            "private_research",
            "--allow-private-context",
            "--json",
        ],
    )

    assert denied.exit_code == 1
    denied_payload = _assert_json_output(denied.output)
    assert denied_payload["code"] == "private_context_requires_policy"
    assert denied_payload["blocking"] is True

    assert allowed.exit_code == 0, allowed.output
    allowed_payload = _assert_json_output(allowed.output)
    assert allowed_payload["preview"]["private_context_included"] is True
    assert set(allowed_payload["preview"]["root_scopes"]) == {"public", "private"}
    assert allowed_payload["payload_shape"]["artifact_count"] == 2


def test_provider_fake_run_json_uses_fake_provider_without_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("COSHEAF_TEST_API_KEY", raising=False)
    request_path = _write_json(
        tmp_path,
        "requests/fake-run.json",
        {
            "model": "fake-deterministic",
            "worker_role": "reasoner",
            "prompt": "Return a draft-only provider CLI smoke response.",
            "context_artifact_ids": ["claim.fixture.provider-cli-public"],
            "root_scopes": ["public"],
            "output_kind": "text",
            "expected_output_paths": ["kb/private/draft/claims/provider-cli.yaml"],
        },
    )

    result = runner.invoke(
        app,
        [
            "provider",
            "fake-run",
            "--repo-root",
            str(tmp_path),
            "--input-json",
            str(request_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["schema_version"] == 1
    assert payload["provider"] == "fake"
    assert payload["status"] == "completed"
    assert payload["provider_run"]["private_context_sent"] is False
    assert payload["provider_run"]["log_path"].startswith(".cosheaf/providers/")
    assert "hosted_network" in payload["provider_log"]["metadata"]
    assert "accepted" not in payload["provider_log"]["output_paths"][0]
    assert "sk-" not in result.output


def test_provider_fake_run_accepts_utf8_bom_input_json(tmp_path: Path) -> None:
    request_path = _write_json_with_bom(
        tmp_path,
        "requests/fake-run-bom.json",
        {
            "model": "fake-deterministic",
            "worker_role": "reasoner",
            "prompt": "Return a draft-only provider CLI smoke response.",
            "context_artifact_ids": ["claim.fixture.provider-cli-public"],
            "root_scopes": ["public"],
            "output_kind": "text",
            "expected_output_paths": ["kb/private/draft/claims/provider-cli.yaml"],
        },
    )

    result = runner.invoke(
        app,
        [
            "provider",
            "fake-run",
            "--repo-root",
            str(tmp_path),
            "--input-json",
            str(request_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["provider"] == "fake"
    assert payload["status"] == "completed"
