from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.verification.counterexample_evidence import (
    CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
)

runner = CliRunner()


def _write_json(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n")
    return path


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _assert_json(output: str) -> dict[str, Any]:
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def _workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "checked-evidence-security"',
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


def _artifact(artifact_id: str, *, status: str, statement: str) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": artifact_id,
        "domain": ["security"],
        "status": status,
        "created_at": "2026-06-15T00:00:00Z",
        "updated_at": "2026-06-15T00:00:00Z",
        "authors": ["security-test"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["security-regression"],
        "statement": statement,
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _issue() -> dict[str, Any]:
    return {
        "id": "issue.security.checked-evidence",
        "type": "issue",
        "title": "Checked evidence public-only regression",
        "status": "open",
        "created_at": "2026-06-15T00:00:00Z",
        "updated_at": "2026-06-15T00:00:00Z",
        "authors": ["security-test"],
        "severity": "high",
        "description": "Public-only context must not expose private checked evidence.",
        "related_artifacts": [
            "claim.security.public",
            "claim.security.private",
        ],
        "tags": ["security-regression"],
    }


def _record_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": 1,
        "evidence_id": (
            "checked-counterexample.claim.security.private."
            "candidate.security.private.habc123"
        ),
        "target_artifact_id": "claim.security.private",
        "candidate_id": "candidate.security.private",
        "candidate_source": "manual_note",
        "check_method": "executable_check",
        "checked_result": "checked_refutes",
        "verifier_evidence_ids": [],
        "review_record_paths": [],
        "evidence_paths": [".cosheaf/evidence/private-check.json"],
        "created_at": "2026-06-15T00:00:00Z",
        "checker": "private-security-checker",
        "limitations": [
            CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
            "private-secret-checked-evidence-marker",
        ],
    }
    data.update(overrides)
    return data


def _stage(repo_root: Path, record: dict[str, Any]) -> Any:
    request = _write_json(repo_root, "requests/checked-evidence.json", record)
    return runner.invoke(
        app,
        [
            "counterexample",
            "evidence",
            "stage",
            "--input-json",
            str(request),
            "--repo-root",
            str(repo_root),
            "--json",
        ],
    )


def test_checked_evidence_stage_rejects_authority_claim_fields(
    tmp_path: Path,
) -> None:
    for field, value in {
        "human_reviewed": True,
        "review_state": "human_reviewed",
        "accepted": True,
        "artifact_status": "accepted",
        "promote": True,
    }.items():
        result = _stage(tmp_path, _record_data(**{field: value}))

        assert result.exit_code == 1
        payload = _assert_json(result.output)
        assert payload["code"] == "authority_claim_forbidden"
        assert field in payload["details"]["forbidden_fields"].split(",")
        assert not (tmp_path / "reviews" / "evidence").exists()
        assert not (tmp_path / "kb" / "accepted").exists()


def test_checked_evidence_stage_rejects_accepted_evidence_path(
    tmp_path: Path,
) -> None:
    result = _stage(
        tmp_path,
        _record_data(evidence_paths=["kb/accepted/evidence/unsafe.yaml"]),
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "checked_evidence_validation_failed"
    assert "accepted KB paths" in payload["message"]
    assert not (tmp_path / "reviews" / "evidence").exists()
    assert not (tmp_path / "kb" / "accepted").exists()


def test_checked_evidence_stage_rejects_path_traversal(tmp_path: Path) -> None:
    result = _stage(tmp_path, _record_data(evidence_paths=["../secret.json"]))

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "checked_evidence_validation_failed"
    assert "repository-local" in payload["message"]
    assert not (tmp_path / "reviews" / "evidence").exists()


def test_public_only_context_excludes_private_checked_evidence_text(
    tmp_path: Path,
) -> None:
    _workspace_config(tmp_path)
    _write_yaml(
        tmp_path,
        "kb/public/accepted/claims/claim.security.public.yaml",
        _artifact(
            "claim.security.public",
            status="accepted",
            statement="Public fixture.",
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.security.private.yaml",
        _artifact(
            "claim.security.private",
            status="draft",
            statement="Private fixture with private-secret-checked-evidence-marker.",
        ),
    )
    _write_yaml(tmp_path, "issues/open/checked-evidence.yaml", _issue())
    private_stage = _stage(tmp_path, _record_data())
    assert private_stage.exit_code == 0, private_stage.output

    public_record = _record_data(
        evidence_id=(
            "checked-counterexample.claim.security.public."
            "candidate.security.public.habc123"
        ),
        target_artifact_id="claim.security.public",
        candidate_id="candidate.security.public",
        evidence_paths=[".cosheaf/evidence/public-check.json"],
        checker="public-security-checker",
        limitations=[
            CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
            "public checked evidence marker",
        ],
    )
    public_stage = _stage(tmp_path, public_record)
    assert public_stage.exit_code == 0, public_stage.output

    result = runner.invoke(
        app,
        [
            "context",
            "build",
            "issue.security.checked-evidence",
            "--repo-root",
            str(tmp_path),
            "--public-only",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    task_dir = tmp_path / "context" / "TASKS" / "issue.security.checked-evidence"
    rendered = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(task_dir.rglob("*"))
        if path.is_file()
    )
    assert "checked-counterexample.claim.security.public" in rendered
    assert "public checked evidence marker" in rendered
    assert "checked-counterexample.claim.security.private" not in rendered
    assert "private-secret-checked-evidence-marker" not in rendered
    assert "claim.security.private" not in rendered
