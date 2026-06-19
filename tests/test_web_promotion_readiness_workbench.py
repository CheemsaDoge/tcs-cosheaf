from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

import cosheaf.gates.gatekeeper as gatekeeper_module
from cosheaf.app import open_app
from cosheaf.core.artifact import BaseArtifact
from cosheaf.server import ReadOnlySiteApi
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.registry import VerifierRegistry
from cosheaf.verification.result import VerificationResult, VerificationStatus


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


def _audit_entries(repo_root: Path) -> list[dict[str, Any]]:
    audit_path = repo_root / ".cosheaf" / "audit" / "web-actions.jsonl"
    return [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _artifact_data(
    artifact_id: str,
    *,
    status: str = "locally_tested",
    review_state: str = "human_reviewed",
    depends_on: list[str] | None = None,
    formalizations: list[dict[str, Any]] | None = None,
    verification_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": "claim",
        "title": "Promotion readiness web fixture",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": ["promotion-readiness"],
        "statement": "Triangle graph $K_3$ should be reviewed before promotion.",
        "evidence": [],
        "sources": [],
        "review": {"state": review_state, "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }
    if formalizations is not None:
        data["formalizations"] = formalizations
    if verification_policy is not None:
        data["verification_policy"] = verification_policy
    return data


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


def test_web_promotion_readiness_get_reports_ready_artifact(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.ready.yaml",
        _artifact_data("claim.fixture.ready"),
    )
    api = ReadOnlySiteApi(open_app(tmp_path))

    response = api.handle(
        "GET",
        "/api/artifacts/claim.fixture.ready/promotion-readiness",
    )

    assert response.status == 200
    assert response.payload["kind"] == "promotion_readiness"
    assert response.payload["source_of_truth"] == "repository"
    assert response.payload["promotion_performed"] is False
    assert response.payload["accepted_write_performed"] is False
    readiness = response.payload["promotion_readiness"]
    assert readiness["ready"] is True
    assert readiness["artifacts"][0]["artifact_id"] == "claim.fixture.ready"
    assert readiness["artifacts"][0]["ready"] is True


def test_web_promotion_preview_reports_blockers_and_audits(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.not-ready.yaml",
        _artifact_data(
            "claim.fixture.not-ready",
            status="draft",
            review_state="requested",
            depends_on=["claim.fixture.missing-dependency"],
        ),
    )
    api = ReadOnlySiteApi(open_app(tmp_path))

    response = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.not-ready/promotion/preview",
        json.dumps({"target_state": "accepted"}),
    )

    assert response.status == 200
    assert response.payload["kind"] == "promotion_preview"
    assert response.payload["dry_run_only"] is True
    assert response.payload["promotion_performed"] is False
    assert response.payload["accepted_write_performed"] is False
    assert response.payload["promotion_blocked"] is True
    assert response.payload["promotion_plan"]["target_state"] == "accepted"
    assert response.payload["promotion_plan"]["promotion_performed"] is False
    reasons = response.payload["missing_requirements"]
    assert {reason["code"] for reason in reasons} >= {
        "draft_status",
        "missing_review",
        "dependency_risk",
    }

    entries = _audit_entries(tmp_path)
    assert entries[-1]["action"] == "promotion.preview"
    assert entries[-1]["preview_only"] is True


def test_web_promotion_readiness_displays_required_skipped_verifier_as_blocking(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        gatekeeper_module,
        "default_verifier_registry",
        _skipped_lean_registry,
    )
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
        "kb/draft/claims/claim.fixture.required-skip.yaml",
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
    api = ReadOnlySiteApi(open_app(tmp_path))

    response = api.handle(
        "GET",
        "/api/artifacts/claim.fixture.required-skip/promotion-readiness",
    )

    assert response.status == 200
    readiness = response.payload["promotion_readiness"]
    assert readiness["ready"] is False
    reasons = readiness["artifacts"][0]["reasons"]
    skipped = [reason for reason in reasons if reason["code"] == "skipped_verifier"]
    assert len(skipped) == 1
    assert skipped[0]["status"] == "skipped"
    assert skipped[0]["severity"] == "blocking"
    assert "not a pass" in skipped[0]["message"]


def test_web_promotion_preview_includes_target_diff_review_and_confirmation(
    tmp_path: Path,
) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.web-promote.yaml",
        _artifact_data("claim.fixture.web-promote"),
    )
    before = source.read_text(encoding="utf-8")
    api = ReadOnlySiteApi(open_app(tmp_path))

    response = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.web-promote/promotion/preview",
        json.dumps(
            {
                "target_state": "accepted",
                "actor": "Ada Reviewer",
            }
        ),
    )

    assert response.status == 200
    assert response.payload["kind"] == "promotion_preview"
    assert response.payload["dry_run_only"] is True
    assert response.payload["promotion_blocked"] is False
    assert response.payload["promotion_plan"]["target_state"] == "accepted"
    assert (
        response.payload["promotion_plan"]["required_confirmation"]
        == "PROMOTE TO ACCEPTED"
    )
    assert response.payload["review_record_preview"] == {
        "actor": "Ada Reviewer",
        "artifact_id": "claim.fixture.web-promote",
        "target_state": "accepted",
        "existing_review_state": "human_reviewed",
    }
    assert response.payload["validation_summary"] == "validation passed"
    assert response.payload["gate_summary"] == "gate passed"
    assert "kb/draft/claims/claim.fixture.web-promote.yaml" in response.payload[
        "planned_files"
    ]
    assert "kb/accepted/claims/claim.fixture.web-promote.yaml" in response.payload[
        "planned_files"
    ]
    assert "status: accepted" in response.payload["yaml_diff"]
    assert source.read_text(encoding="utf-8") == before
    assert not (
        tmp_path / "kb" / "accepted" / "claims" / "claim.fixture.web-promote.yaml"
    ).exists()


def test_web_promotion_confirm_requires_typed_confirmation_then_promotes(
    tmp_path: Path,
) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.web-promote.yaml",
        _artifact_data("claim.fixture.web-promote"),
    )
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Ada Local")

    blocked = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.web-promote/promotion/confirm",
        json.dumps(
            {
                "target_state": "accepted",
                "actor": "Payload Reviewer",
                "typed_confirmation": "MARK REFUTED",
                "promotion_justification": "Reviewed by hand before promotion.",
                "confirm": True,
            }
        ),
    )

    assert blocked.status == 400
    assert blocked.payload["code"] == "typed_confirmation_required"
    assert source.is_file()

    confirmed = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.web-promote/promotion/confirm",
        json.dumps(
            {
                "target_state": "accepted",
                "actor": "Payload Reviewer",
                "typed_confirmation": "PROMOTE TO ACCEPTED",
                "promotion_justification": "Reviewed by hand before promotion.",
                "confirm": True,
            }
        ),
    )

    assert confirmed.status == 200
    assert confirmed.payload["kind"] == "promotion_confirm"
    assert confirmed.payload["repo_writes_performed"] is True
    assert confirmed.payload["accepted_write_performed"] is True
    assert confirmed.payload["promotion_performed"] is True
    target = tmp_path / "kb" / "accepted" / "claims" / "claim.fixture.web-promote.yaml"
    assert not source.exists()
    assert target.is_file()
    assert _read_yaml(target)["status"] == "accepted"

    entries = _audit_entries(tmp_path)
    assert entries[-1]["action"] == "promotion.confirm"
    assert entries[-1]["actor"] == "Ada Local"
    assert entries[-1]["operator_notes"] == "Reviewed by hand before promotion."
    assert entries[-1]["repo_writes_performed"] is True
    assert "kb/accepted/claims/claim.fixture.web-promote.yaml" in entries[-1][
        "written_files"
    ]


def test_web_promotion_confirm_requires_configured_local_actor(
    tmp_path: Path,
) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.missing-local-actor.yaml",
        _artifact_data("claim.fixture.missing-local-actor"),
    )
    api = ReadOnlySiteApi(open_app(tmp_path))

    response = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.missing-local-actor/promotion/confirm",
        json.dumps(
            {
                "target_state": "accepted",
                "actor": "Payload Reviewer",
                "typed_confirmation": "PROMOTE TO ACCEPTED",
                "promotion_justification": "Reviewed by hand before promotion.",
                "confirm": True,
            }
        ),
    )

    assert response.status == 400
    assert response.payload["code"] == "local_actor_required"
    assert source.is_file()
    entries = _audit_entries(tmp_path)
    assert entries[-1]["action"] == "promotion.confirm"
    assert entries[-1]["result_status"] == "local_actor_required"
    assert entries[-1]["repo_writes_performed"] is False


def test_web_promotion_confirm_requires_justification(
    tmp_path: Path,
) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.web-promote-notes.yaml",
        _artifact_data("claim.fixture.web-promote-notes"),
    )
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Ada Local")

    response = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.web-promote-notes/promotion/confirm",
        json.dumps(
            {
                "target_state": "accepted",
                "actor": "Ada Reviewer",
                "typed_confirmation": "PROMOTE TO ACCEPTED",
                "promotion_justification": " ",
                "confirm": True,
            }
        ),
    )

    assert response.status == 400
    assert response.payload["code"] == "promotion_justification_required"
    assert source.is_file()
    assert not (
        tmp_path
        / "kb"
        / "accepted"
        / "claims"
        / "claim.fixture.web-promote-notes.yaml"
    ).exists()


def test_web_promotion_confirm_blocks_missing_review(
    tmp_path: Path,
) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.unreviewed.yaml",
        _artifact_data("claim.fixture.unreviewed", review_state="requested"),
    )
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Ada Local")

    response = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.unreviewed/promotion/confirm",
        json.dumps(
            {
                "target_state": "accepted",
                "actor": "Ada Reviewer",
                "typed_confirmation": "PROMOTE TO ACCEPTED",
                "promotion_justification": "Reviewed by hand before promotion.",
                "confirm": True,
            }
        ),
    )

    assert response.status == 400
    assert response.payload["code"] == "promotion_blocked"
    assert "missing_review" in response.payload["message"]
    assert source.is_file()
    assert not (
        tmp_path / "kb" / "accepted" / "claims" / "claim.fixture.unreviewed.yaml"
    ).exists()


def test_web_promotion_confirm_moves_refuted_through_lifecycle(
    tmp_path: Path,
) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.refute.yaml",
        _artifact_data("claim.fixture.refute"),
    )
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Ada Local")

    response = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.refute/promotion/confirm",
        json.dumps(
            {
                "target_state": "refuted",
                "actor": "Ada Reviewer",
                "typed_confirmation": "MARK REFUTED",
                "promotion_justification": "Reviewed by hand before refutation.",
                "confirm": True,
            }
        ),
    )

    assert response.status == 200
    assert response.payload["accepted_write_performed"] is False
    assert response.payload["promotion_performed"] is True
    target = tmp_path / "kb" / "refuted" / "claim.fixture.refute.yaml"
    assert not source.exists()
    assert target.is_file()
    assert _read_yaml(target)["status"] == "refuted"


def test_web_promotion_confirm_refuses_ai_actor(
    tmp_path: Path,
) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.ai-actor.yaml",
        _artifact_data("claim.fixture.ai-actor"),
    )
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Codex reviewer")

    response = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.ai-actor/promotion/confirm",
        json.dumps(
            {
                "target_state": "accepted",
                "actor": "Payload Reviewer",
                "typed_confirmation": "PROMOTE TO ACCEPTED",
                "promotion_justification": "Reviewed by hand before promotion.",
                "confirm": True,
            }
        ),
    )

    assert response.status == 400
    assert response.payload["code"] == "promotion_actor_forbidden"
    assert source.is_file()
