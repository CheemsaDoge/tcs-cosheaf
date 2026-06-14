from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _write_json(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n")
    return path


def _assert_json(output: str) -> dict[str, Any]:
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def _workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "failure-log-security"',
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


def _artifact(
    artifact_id: str,
    *,
    status: str,
    statement: str = "Security regression fixture.",
    depends_on: list[str] | None = None,
    review_state: str = "requested",
    failure_log: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": "claim",
        "title": artifact_id,
        "domain": ["security"],
        "status": status,
        "created_at": "2026-06-15T00:00:00Z",
        "updated_at": "2026-06-15T00:00:00Z",
        "authors": ["security-test"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": ["security-regression"],
        "statement": statement,
        "evidence": [],
        "review": {
            "state": review_state,
            "notes": "Security regression fixture.",
        },
        "risk": {"level": "low", "notes": "Fixture only."},
    }
    if failure_log is not None:
        data["failure_log"] = failure_log
    return data


def _issue() -> dict[str, Any]:
    return {
        "id": "issue.security.failure-log",
        "type": "issue",
        "title": "Failure-log private leak regression",
        "status": "open",
        "created_at": "2026-06-15T00:00:00Z",
        "updated_at": "2026-06-15T00:00:00Z",
        "authors": ["security-test"],
        "severity": "high",
        "description": "Public-only context must not expose private failure memory.",
        "related_artifacts": [
            "claim.security.public",
            "claim.security.private",
        ],
        "tags": ["security-regression"],
    }


def _failure_log_entry(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "failure_id": "failure.security.regression.0001",
        "attempted_at": "2026-06-15T00:00:00Z",
        "recorded_by": "security-test",
        "origin": "agent",
        "attempt_kind": "proof_attempt",
        "target": "claim.security.draft",
        "direction": "Try a direct proof direction.",
        "summary": "A failed-attempt memory fixture.",
        "failed_because": "The attempted direction was not sufficient.",
        "evidence_paths": [],
        "related_verifier_results": [],
        "related_counterexample_candidates": [],
        "next_possible_directions": ["Try a smaller lemma first."],
        "status": "open",
        "limitations": "Failure memory only; not proof or review evidence.",
    }
    data.update(overrides)
    return data


def _write_failure_target(repo_root: Path) -> Path:
    return _write_yaml(
        repo_root,
        "kb/private/draft/claims/claim.security.draft.yaml",
        _artifact(
            "claim.security.draft",
            status="draft",
            depends_on=["claim.security.public"],
        ),
    )


def _invoke_failure_add(
    repo_root: Path,
    request: dict[str, Any],
    *,
    artifact_id: str = "claim.security.draft",
) -> Any:
    request_path = _write_json(repo_root, "requests/failure-log.json", request)
    return runner.invoke(
        app,
        [
            "artifact",
            "failure",
            "add",
            "--artifact",
            artifact_id,
            "--input-json",
            str(request_path),
            "--repo-root",
            str(repo_root),
            "--json",
        ],
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("review_state", "human_reviewed"),
        ("human_review", True),
        ("verifier_status", "pass"),
        ("verifier_pass", True),
        ("counterexample_status", "checked"),
        ("checked_counterexample", True),
        ("artifact_status", "accepted"),
        ("status", "accepted"),
    ],
)
def test_failure_log_add_rejects_authority_claim_fields(
    tmp_path: Path,
    field: str,
    value: Any,
) -> None:
    _workspace_config(tmp_path)
    target_path = _write_failure_target(tmp_path)

    result = _invoke_failure_add(
        tmp_path,
        _failure_log_entry(**{field: value}),
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "authority_claim_forbidden"
    assert field in payload["details"]["forbidden_fields"].split(",")
    written = yaml.safe_load(target_path.read_text(encoding="utf-8"))
    assert "failure_log" not in written
    assert not (tmp_path / "kb" / "accepted").exists()


def test_failure_log_add_rejects_accepted_evidence_path(
    tmp_path: Path,
) -> None:
    _workspace_config(tmp_path)
    target_path = _write_failure_target(tmp_path)

    result = _invoke_failure_add(
        tmp_path,
        _failure_log_entry(evidence_paths=["kb/accepted/evidence/proof.md"]),
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "artifact_model_validation_failed"
    assert "accepted KB paths" in payload["message"]
    written = yaml.safe_load(target_path.read_text(encoding="utf-8"))
    assert "failure_log" not in written
    assert not (tmp_path / "kb" / "accepted").exists()


def test_provider_origin_failure_log_cannot_claim_accepted_status(
    tmp_path: Path,
) -> None:
    _workspace_config(tmp_path)
    target_path = _write_failure_target(tmp_path)

    result = _invoke_failure_add(
        tmp_path,
        _failure_log_entry(origin="provider", artifact_status="accepted"),
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "authority_claim_forbidden"
    assert payload["details"]["forbidden_fields"] == "artifact_status"
    written = yaml.safe_load(target_path.read_text(encoding="utf-8"))
    assert "failure_log" not in written
    assert not (tmp_path / "kb" / "accepted").exists()


def test_public_only_context_excludes_private_failure_log_text(
    tmp_path: Path,
) -> None:
    _workspace_config(tmp_path)
    private_marker = "private-failure-secret-do-not-leak"
    _write_yaml(
        tmp_path,
        "kb/public/accepted/claims/claim.security.public.yaml",
        _artifact(
            "claim.security.public",
            status="accepted",
            statement="Public context fixture.",
            review_state="accepted",
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.security.private.yaml",
        _artifact(
            "claim.security.private",
            status="draft",
            statement=f"Private context fixture with {private_marker}.",
            depends_on=["claim.security.public"],
            failure_log=[
                _failure_log_entry(
                    failure_id="failure.security.private.0001",
                    target="claim.security.private",
                    direction=f"Private failed direction {private_marker}.",
                    failed_because=f"Private reason {private_marker}.",
                    limitations=f"Private limitation {private_marker}.",
                )
            ],
        ),
    )
    _write_yaml(tmp_path, "issues/open/failure-log.yaml", _issue())

    result = runner.invoke(
        app,
        [
            "context",
            "build",
            "issue.security.failure-log",
            "--repo-root",
            str(tmp_path),
            "--public-only",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    assert payload["public_only"] is True
    assert "claim.security.private" not in json.dumps(payload, sort_keys=True)
    task_dir = tmp_path / "context" / "TASKS" / "issue.security.failure-log"
    rendered = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(task_dir.rglob("*"))
        if path.is_file()
    )
    assert private_marker not in rendered
    assert "claim.security.private" not in rendered
