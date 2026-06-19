from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.app import open_app
from cosheaf.server import ReadOnlySiteApi


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


def _artifact_data() -> dict[str, Any]:
    return {
        "id": "claim.fixture.review-decision",
        "type": "claim",
        "title": "Review decision draft claim",
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "depends_on": ["definition.graph"],
        "supersedes": [],
        "tags": ["review-decision"],
        "statement": "Triangle graph $K_3$ should stay draft.",
        "evidence": [
            {
                "kind": "python_checker",
                "path": "docs/evidence.md",
                "summary": "Checker output for reviewer context.",
            }
        ],
        "review": {"state": "requested", "notes": "Review still pending."},
        "risk": {"level": "medium", "notes": "Needs human review."},
        "sources": [
            {
                "kind": "paper",
                "title": "Fixture Source",
                "authors": ["Author"],
                "year": 2026,
                "doi": "",
                "arxiv": "",
                "url": "",
                "theorem_number": "Theorem 1",
                "page": "12",
                "notes": "Used for review decision source check.",
            }
        ],
    }


def _fixture_workspace(repo_root: Path) -> None:
    _write_yaml(
        repo_root,
        "kb/draft/claims/claim.fixture.review-decision.yaml",
        _artifact_data(),
    )
    evidence_path = repo_root / "docs" / "evidence.md"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("Fixture evidence.\n", encoding="utf-8")


def _valid_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_id": "claim.fixture.review-decision",
        "reviewer": "Ada Reviewer",
        "decision": "accept_for_private_use",
        "review_notes": "Checked the source, dependency, and evidence context.",
        "scope": "private",
        "limitations": "Fixture review only.",
        "dependencies_checked": True,
        "sources_checked": True,
        "evidence_checked": True,
        "gate_state_acknowledged": True,
        "explicit_human_confirmation": True,
    }
    payload.update(overrides)
    return payload


def test_web_review_decision_preview_plans_record_and_artifact_update_without_writes(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path))
    artifact_path = tmp_path / "kb/draft/claims/claim.fixture.review-decision.yaml"
    before_artifact = _read_yaml(artifact_path)

    preview = api.handle(
        "POST",
        "/api/reviews/decisions/preview",
        json.dumps(_valid_payload()),
    )

    assert preview.status == 200
    assert preview.payload["kind"] == "review_decision_preview"
    assert preview.payload["dry_run_only"] is True
    assert preview.payload["repo_writes_performed"] is False
    assert preview.payload["review_decision"]["decision"] == "accept_for_private_use"
    assert preview.payload["artifact_update"]["review"]["state"] == "human_reviewed"
    assert preview.payload["accepted_write_performed"] is False
    planned_files = preview.payload["planned_files"]
    review_path = planned_files[0]
    assert review_path.startswith("reviews/decisions/review.decision.")
    assert "kb/draft/claims/claim.fixture.review-decision.yaml" in planned_files
    assert not (tmp_path / review_path).exists()
    assert _read_yaml(artifact_path) == before_artifact

    entries = _audit_entries(tmp_path)
    assert entries[-1]["action"] == "review.decision_create"
    assert entries[-1]["preview_only"] is True


def test_web_review_decision_create_requires_confirm_and_then_records_human_review(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Ada Local")
    artifact_path = tmp_path / "kb/draft/claims/claim.fixture.review-decision.yaml"

    blocked = api.handle(
        "POST",
        "/api/reviews/decisions/create",
        json.dumps(_valid_payload()),
    )
    assert blocked.status == 400
    assert blocked.payload["code"] == "confirm_required"
    assert not (tmp_path / "reviews" / "decisions").exists()

    created = api.handle(
        "POST",
        "/api/reviews/decisions/create",
        json.dumps({**_valid_payload(), "confirm": True}),
    )

    assert created.status == 200
    assert created.payload["kind"] == "review_decision_create"
    assert created.payload["repo_writes_performed"] is True
    assert created.payload["accepted_write_performed"] is False
    assert created.payload["promotion_performed"] is False

    review = _read_yaml(tmp_path / created.payload["path"])
    assert review["status"] == "human_reviewed"
    assert review["decision"] == "accept_for_private_use"
    assert review["target"] == "claim.fixture.review-decision"
    assert review["authors"] == ["Ada Reviewer"]
    assert any("dependencies_checked=True" in item for item in review["findings"])

    artifact = _read_yaml(artifact_path)
    assert artifact["review"]["state"] == "human_reviewed"
    assert "Ada Reviewer" in artifact["review"]["notes"]
    assert artifact["status"] == "draft"

    entries = _audit_entries(tmp_path)
    assert entries[-1]["action"] == "review.decision_create"
    assert entries[-1]["actor"] == "Ada Local"
    assert entries[-1]["repo_writes_performed"] is True


def test_web_review_decision_confirm_requires_configured_local_actor(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path))

    blocked = api.handle(
        "POST",
        "/api/reviews/decisions/create",
        json.dumps({**_valid_payload(), "confirm": True}),
    )

    assert blocked.status == 400
    assert blocked.payload["code"] == "local_actor_required"
    assert not (tmp_path / "reviews" / "decisions").exists()
    entries = _audit_entries(tmp_path)
    assert entries[-1]["action"] == "review.decision_create"
    assert entries[-1]["result_status"] == "local_actor_required"
    assert entries[-1]["repo_writes_performed"] is False


def test_web_review_decision_refuses_missing_notes_and_ai_reviewer(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Ada Local")

    missing_notes = api.handle(
        "POST",
        "/api/reviews/decisions/preview",
        json.dumps(_valid_payload(review_notes=" ")),
    )
    assert missing_notes.status == 400
    assert missing_notes.payload["code"] == "review_notes_required"

    ai_reviewer = api.handle(
        "POST",
        "/api/reviews/decisions/preview",
        json.dumps(_valid_payload(reviewer="Codex reviewer")),
    )
    assert ai_reviewer.status == 400
    assert ai_reviewer.payload["code"] == "review_reviewer_forbidden"

    entries = _audit_entries(tmp_path)
    assert entries[-1]["action"] == "review.decision_create"
    assert entries[-1]["error_code"] == "review_reviewer_forbidden"


def test_web_review_decision_keep_draft_records_decision_without_review_state_change(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path), local_actor="Ada Local")
    artifact_path = tmp_path / "kb/draft/claims/claim.fixture.review-decision.yaml"

    created = api.handle(
        "POST",
        "/api/reviews/decisions/create",
        json.dumps(
            {
                **_valid_payload(decision="keep_draft"),
                "confirm": True,
            }
        ),
    )

    assert created.status == 200
    review = _read_yaml(tmp_path / created.payload["path"])
    assert review["decision"] == "keep_draft"
    artifact = _read_yaml(artifact_path)
    assert artifact["review"]["state"] == "requested"
    assert artifact["status"] == "draft"
