from __future__ import annotations

import json
import subprocess
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


def _post(api: ReadOnlySiteApi, path: str, payload: dict[str, Any]) -> Any:
    return api.handle("POST", path, json.dumps(payload))


def _assert_refused(response: Any, code: str) -> None:
    assert response.status in {400, 401, 403}, response.payload
    assert response.payload["code"] == code
    assert isinstance(response.payload["message"], str)
    assert response.payload["message"].strip()


def _artifact_data(
    artifact_id: str,
    *,
    status: str = "locally_tested",
    review_state: str = "human_reviewed",
    sources: list[dict[str, Any]] | None = None,
    formalizations: list[dict[str, Any]] | None = None,
    verification_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": "claim",
        "title": "Authority negative fixture",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-20T00:00:00Z",
        "updated_at": "2026-06-20T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["authority-negative"],
        "statement": "Triangle graph $K_3$ is a negative authority fixture.",
        "evidence": [],
        "sources": sources or [],
        "review": {"state": review_state, "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }
    if formalizations is not None:
        data["formalizations"] = formalizations
    if verification_policy is not None:
        data["verification_policy"] = verification_policy
    return data


def _source_metadata() -> dict[str, Any]:
    return {
        "kind": "book",
        "title": "Graph Theory Fixture",
        "authors": ["Ada Author"],
        "year": 2026,
        "page": "1",
        "notes": "Fixture source.",
    }


def test_workbench_authority_negative_e2e_fail_closed_and_audited(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Ada Local")
    secret = "browser-token-should-not-be-used-or-logged"

    accepted_direct = _post(
        api,
        "/api/artifacts/create",
        {
            "artifact_id": "claim.fixture.accepted.direct",
            "artifact_type": "claim",
            "title": "Forbidden accepted artifact",
            "domain": ["testing"],
            "status": "accepted",
            "statement": "The browser must not create accepted artifacts.",
            "authors": ["Ada Local"],
            "tags": [],
            "depends_on": [],
            "supersedes": [],
            "confirm": True,
        },
    )
    _assert_refused(accepted_direct, "accepted_write_forbidden")
    assert not list((tmp_path / "kb" / "accepted").glob("**/*.yaml"))

    unreviewed_path = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.unreviewed.yaml",
        _artifact_data(
            "claim.fixture.unreviewed",
            review_state="requested",
            sources=[_source_metadata()],
        ),
    )
    promotion_without_review = _post(
        api,
        "/api/artifacts/claim.fixture.unreviewed/promotion/confirm",
        {
            "target_state": "accepted",
            "actor": "Ada Reviewer",
            "typed_confirmation": "PROMOTE TO ACCEPTED",
            "promotion_justification": "Negative test should refuse this.",
            "confirm": True,
        },
    )
    _assert_refused(promotion_without_review, "promotion_blocked")
    assert "missing_review" in promotion_without_review.payload["message"]
    assert unreviewed_path.is_file()
    assert not (
        tmp_path / "kb" / "accepted" / "claims" / "claim.fixture.unreviewed.yaml"
    ).exists()

    ai_reviewer = _post(
        api,
        "/api/reviews/decisions/preview",
        {
            "artifact_id": "claim.fixture.unreviewed",
            "reviewer": "Codex reviewer",
            "decision": "accept_for_private_use",
            "review_notes": "This identity must be refused.",
            "scope": "private",
            "limitations": "Negative test.",
            "dependencies_checked": True,
            "sources_checked": True,
            "evidence_checked": True,
            "gate_state_acknowledged": True,
            "explicit_human_confirmation": True,
        },
    )
    _assert_refused(ai_reviewer, "review_reviewer_forbidden")

    injected_token = _post(
        api,
        "/api/forge/prs/create",
        {
            "base": "main",
            "head": "feature",
            "github_token": secret,
            "confirm": True,
        },
    )
    _assert_refused(injected_token, "auth_required")

    no_credentials = _post(
        api,
        "/api/forge/prs/create",
        {"base": "main", "head": "feature", "confirm": True},
    )
    _assert_refused(no_credentials, "auth_required")

    (tmp_path / "README.md").write_text("direct main change\n", encoding="utf-8")
    direct_main_commit = _post(
        api,
        "/api/forge/commit/create",
        {
            "message": "Direct main write should fail",
            "stage_all": True,
            "confirm": True,
        },
    )
    _assert_refused(direct_main_commit, "forge_protected_branch")
    assert _git(tmp_path, "branch", "--show-current") == "main"
    assert _git(tmp_path, "log", "-1", "--pretty=%s") == "Initial commit"

    audit_text = (
        tmp_path / ".cosheaf" / "audit" / "web-actions.jsonl"
    ).read_text(encoding="utf-8")
    assert secret not in audit_text
    entries = _audit_entries(tmp_path)
    result_statuses = [entry["result_status"] for entry in entries]
    assert "accepted_write_forbidden" in result_statuses
    assert "promotion_blocked" in result_statuses
    assert "review_reviewer_forbidden" in result_statuses
    assert result_statuses.count("auth_required") >= 2
    assert "forge_protected_branch" in result_statuses
    assert all(not entry.get("repo_writes_performed", False) for entry in entries)


def test_required_skipped_verifier_cannot_be_treated_as_promotion_pass(
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
            formalizations=[
                {
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
            ],
            verification_policy={
                "level": "machine_checked",
                "require_formal_link": True,
                "require_lean_check": True,
                "require_alignment_review": False,
            },
        ),
    )
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Ada Local")

    preview = _post(
        api,
        "/api/artifacts/claim.fixture.required-skip/promotion/preview",
        {"target_state": "accepted"},
    )

    assert preview.status == 200
    assert preview.payload["promotion_blocked"] is True
    reasons = preview.payload["missing_requirements"]
    skipped = [reason for reason in reasons if reason["code"] == "skipped_verifier"]
    assert skipped and skipped[0]["severity"] == "blocking"

    confirmed = _post(
        api,
        "/api/artifacts/claim.fixture.required-skip/promotion/confirm",
        {
            "target_state": "accepted",
            "actor": "Ada Reviewer",
            "typed_confirmation": "PROMOTE TO ACCEPTED",
            "promotion_justification": "Skipped verifier must block promotion.",
            "confirm": True,
        },
    )
    _assert_refused(confirmed, "promotion_blocked")
    assert "no Lean verifier result passed" in confirmed.payload["message"]
    entries = _audit_entries(tmp_path)
    assert entries[-1]["result_status"] == "promotion_blocked"
    assert entries[-1]["repo_writes_performed"] is False


def test_public_promotion_missing_source_metadata_is_refused(
    tmp_path: Path,
) -> None:
    (tmp_path / "cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "authority-negative"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                "readonly = false",
                "priority = 10",
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
    public_artifact_path = _write_yaml(
        tmp_path,
        "kb/public/draft/claims/claim.fixture.public-missing-source.yaml",
        _artifact_data("claim.fixture.public-missing-source"),
    )
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Ada Local")

    preview = _post(
        api,
        "/api/artifacts/claim.fixture.public-missing-source/promotion/preview",
        {"target_state": "accepted"},
    )

    assert preview.status == 200
    assert preview.payload["promotion_blocked"] is True
    reasons = preview.payload["missing_requirements"]
    assert any(reason["code"] == "missing_source_metadata" for reason in reasons)

    confirmed = _post(
        api,
        "/api/artifacts/claim.fixture.public-missing-source/promotion/confirm",
        {
            "target_state": "accepted",
            "actor": "Ada Reviewer",
            "typed_confirmation": "PROMOTE TO ACCEPTED",
            "promotion_justification": "Public accepted artifacts need sources.",
            "confirm": True,
        },
    )
    _assert_refused(confirmed, "promotion_blocked")
    assert public_artifact_path.is_file()
    assert not (
        tmp_path
        / "kb/public/accepted/claims/claim.fixture.public-missing-source.yaml"
    ).exists()
    assert _read_yaml(public_artifact_path)["status"] == "locally_tested"
