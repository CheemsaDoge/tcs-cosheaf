from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

import cosheaf.gates.gatekeeper as gatekeeper_module
from cosheaf.cli import app
from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.registry import VerifierRegistry
from cosheaf.verification.result import VerificationResult, VerificationStatus

runner = CliRunner()


class _SkippedLeanLibraryRefAdapter:
    name = "lean_library_ref"

    def can_verify(self, artifact: BaseArtifact, repo: RepoContext) -> bool:
        return artifact.id == "claim.fixture.required-skip"

    def verify(self, artifact: BaseArtifact, repo: RepoContext) -> VerificationResult:
        now = datetime.now(UTC)
        return VerificationResult(
            verifier=self.name,
            artifact_id=artifact.id,
            status=VerificationStatus.SKIPPED,
            started_at=now,
            ended_at=now,
            tool_name="fake-lean",
            message="fake Lean backend unavailable",
        )


def _skipped_lean_registry() -> VerifierRegistry:
    registry = VerifierRegistry()
    registry.register(_SkippedLeanLibraryRefAdapter())
    return registry


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _write_workspace_config(repo_root: Path, *, public_readonly: bool = True) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "promotion-readiness-fixture"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                f"readonly = {str(public_readonly).lower()}",
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
    artifact_type: str = "claim",
    status: str = "locally_tested",
    review_state: str = "human_reviewed",
    depends_on: list[str] | None = None,
    sources: list[dict[str, Any]] | None = None,
    formalizations: list[dict[str, Any]] | None = None,
    verification_policy: dict[str, Any] | None = None,
    failure_log: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": artifact_type,
        "title": "Promotion readiness fixture",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-14T00:00:00Z",
        "updated_at": "2026-06-14T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": ["promotion-readiness"],
        "statement": "Fixture statement.",
        "evidence": [],
        "sources": sources or [],
        "review": {"state": review_state, "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }
    if formalizations is not None:
        data["formalizations"] = formalizations
    if verification_policy is not None:
        data["verification_policy"] = verification_policy
    if failure_log is not None:
        data["failure_log"] = failure_log
    return data


def _failure_log_entry(
    *,
    status: str = "open",
) -> dict[str, Any]:
    return {
        "failure_id": "failure.fixture.readiness.0001",
        "attempted_at": "2026-06-14T00:00:00Z",
        "recorded_by": "tester",
        "origin": "human",
        "attempt_kind": "proof_attempt",
        "target": "",
        "direction": "Try a separator induction",
        "summary": "A failed proof attempt fixture.",
        "failed_because": "The induction hypothesis was too weak.",
        "evidence_paths": [],
        "related_verifier_results": [],
        "related_counterexample_candidates": [],
        "next_possible_directions": ["Try a decomposition lemma first."],
        "status": status,
        "limitations": "Failure memory only; not proof or refutation.",
    }


def _issue_data(issue_id: str, related_artifacts: list[str]) -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Promotion readiness issue",
        "status": "open",
        "created_at": "2026-06-14T00:00:00Z",
        "updated_at": "2026-06-14T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Issue fixture for promotion readiness.",
        "related_artifacts": related_artifacts,
        "tags": ["promotion-readiness"],
    }


def _source_fixture() -> dict[str, Any]:
    return {
        "kind": "paper",
        "title": "Promotion Readiness Source",
        "authors": ["A. Reviewer"],
        "year": 2026,
        "doi": "10.1145/readiness",
        "arxiv": "",
        "url": "",
        "theorem_number": "Claim 1",
        "page": "7",
        "notes": "Source metadata fixture.",
    }


def _formalization_fixture() -> dict[str, Any]:
    return {
        "id": "formalization.fixture.required-skip",
        "system": "lean4",
        "library": "mathlib",
        "library_ref": "mathlib",
        "import_path": "Mathlib.Data.Nat.Basic",
        "symbol": "Nat",
        "declaration_kind": "definition",
        "status": "checked",
        "check_mode": "external_library_ref",
        "expected_type": "",
        "notes": "Fixture only.",
    }


def _assert_json_output(output: str) -> dict[str, Any]:
    assert "\x1b[" not in output
    data = json.loads(output)
    assert isinstance(data, dict)
    return data


def _reason_codes(payload: dict[str, Any]) -> set[str]:
    reasons = payload["artifacts"][0]["reasons"]
    return {reason["code"] for reason in reasons}


def test_promotion_readiness_artifact_json_is_readonly(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    source = _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.fixture.ready.yaml",
        _artifact_data("claim.fixture.ready"),
    )

    result = runner.invoke(
        app,
        [
            "promotion",
            "readiness",
            "--artifact",
            "claim.fixture.ready",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["schema_version"] == 1
    assert payload["target"] == {
        "mode": "artifact",
        "artifact_id": "claim.fixture.ready",
        "issue_id": "",
    }
    assert payload["ready"] is True
    assert payload["accepted_write_performed"] is False
    assert payload["artifacts"][0]["ready"] is True
    assert payload["artifacts"][0]["artifact_id"] == "claim.fixture.ready"
    assert payload["artifacts"][0]["reasons"] == []
    assert source.is_file()
    assert _read_yaml(source)["status"] == "locally_tested"
    assert not (
        tmp_path / "kb/private/accepted/claims/claim.fixture.ready.yaml"
    ).exists()


def test_promotion_readiness_reports_unresolved_failure_memory_as_warning(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.fixture.failure-memory.yaml",
        _artifact_data(
            "claim.fixture.failure-memory",
            failure_log=[_failure_log_entry()],
        ),
    )

    result = runner.invoke(
        app,
        [
            "promotion",
            "readiness",
            "--artifact",
            "claim.fixture.failure-memory",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["ready"] is True
    assert payload["accepted_write_performed"] is False
    artifact_report = payload["artifacts"][0]
    assert artifact_report["ready"] is True
    reasons = artifact_report["reasons"]
    assert [reason["code"] for reason in reasons] == [
        "unresolved_failure_memory"
    ]
    warning = reasons[0]
    assert warning["severity"] == "warning"
    assert warning["status"] == "open"
    assert "Try a separator induction" in warning["message"]
    assert "The induction hypothesis was too weak" in warning["message"]
    assert "failure memory only" in warning["message"]
    assert "not verifier evidence" in warning["message"]
    assert "not a promotion blocker by itself" in warning["message"]
    assert "failed_verifier" not in {reason["code"] for reason in reasons}


def test_promotion_readiness_ignores_resolved_failure_memory(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.fixture.resolved-failure.yaml",
        _artifact_data(
            "claim.fixture.resolved-failure",
            failure_log=[_failure_log_entry(status="resolved")],
        ),
    )

    result = runner.invoke(
        app,
        [
            "promotion",
            "readiness",
            "--artifact",
            "claim.fixture.resolved-failure",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["ready"] is True
    assert payload["artifacts"][0]["reasons"] == []


def test_promotion_readiness_issue_json_uses_related_artifacts(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.fixture.issue-ready.yaml",
        _artifact_data("claim.fixture.issue-ready"),
    )
    _write_yaml(
        tmp_path,
        "issues/open/issue.fixture.readiness.yaml",
        _issue_data(
            "issue.fixture.readiness",
            related_artifacts=["claim.fixture.issue-ready"],
        ),
    )

    result = runner.invoke(
        app,
        [
            "promotion",
            "readiness",
            "--issue",
            "issue.fixture.readiness",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json_output(result.output)
    assert payload["target"] == {
        "mode": "issue",
        "artifact_id": "",
        "issue_id": "issue.fixture.readiness",
    }
    assert payload["ready"] is True
    assert [item["artifact_id"] for item in payload["artifacts"]] == [
        "claim.fixture.issue-ready"
    ]


def test_promotion_readiness_negative_reasons_are_distinguished(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.fixture.private-dep.yaml",
        _artifact_data(
            "claim.fixture.private-dep",
            status="draft",
            review_state="requested",
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/public/draft/claims/claim.fixture.not-ready.yaml",
        _artifact_data(
            "claim.fixture.not-ready",
            status="draft",
            review_state="requested",
            depends_on=["claim.fixture.private-dep"],
        ),
    )

    result = runner.invoke(
        app,
        [
            "promotion",
            "readiness",
            "--artifact",
            "claim.fixture.not-ready",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json_output(result.output)
    assert payload["ready"] is False
    assert payload["accepted_write_performed"] is False
    assert _reason_codes(payload) >= {
        "draft_status",
        "missing_review",
        "missing_source_metadata",
        "dependency_risk",
        "private_dependency",
        "readonly_kb_root",
    }


def test_promotion_readiness_blocks_unrelated_repository_gate_blocker(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.fixture.ready.yaml",
        _artifact_data("claim.fixture.ready"),
    )
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.fixture.bad.yaml",
        _artifact_data(
            "claim.fixture.bad",
            depends_on=["claim.fixture.missing-dependency"],
        ),
    )

    result = runner.invoke(
        app,
        [
            "promotion",
            "readiness",
            "--artifact",
            "claim.fixture.ready",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json_output(result.output)
    assert payload["ready"] is False
    assert payload["artifacts"][0]["artifact_id"] == "claim.fixture.ready"
    assert "repository_gate_blocker" in _reason_codes(payload)


def test_promotion_readiness_required_skipped_verifier_blocks(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        gatekeeper_module,
        "default_verifier_registry",
        _skipped_lean_registry,
    )
    _write_workspace_config(tmp_path)
    _write_yaml(
        tmp_path,
        "formal-libs/lean-libraries.yaml",
        {
            "libraries": [
                {
                    "id": "mathlib",
                    "name": "mathlib",
                    "system": "lean4",
                    "repo_url": "https://github.com/leanprover-community/mathlib4",
                    "revision": "fixture",
                    "lean_version": "4.0.0",
                    "notes": "Fixture manifest.",
                }
            ]
        },
    )
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.fixture.required-skip.yaml",
        _artifact_data(
            "claim.fixture.required-skip",
            formalizations=[_formalization_fixture()],
            verification_policy={
                "level": "machine_checked",
                "require_formal_link": True,
                "require_lean_check": True,
                "require_alignment_review": False,
            },
        ),
    )

    result = runner.invoke(
        app,
        [
            "promotion",
            "readiness",
            "--artifact",
            "claim.fixture.required-skip",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json_output(result.output)
    assert payload["ready"] is False
    artifact_report = payload["artifacts"][0]
    assert artifact_report["checker_required"] is True
    assert artifact_report["ready"] is False
    reasons = {
        reason["code"]: reason["severity"]
        for reason in artifact_report["reasons"]
    }
    assert reasons["skipped_verifier"] == "blocking"
    assert any(
        reason["code"] == "skipped_verifier"
        and "not a pass" in reason["message"]
        for reason in artifact_report["reasons"]
    )
