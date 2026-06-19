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
        "id": "claim.fixture.review-packet",
        "type": "claim",
        "title": "Review packet draft claim",
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "depends_on": ["definition.graph"],
        "supersedes": [],
        "tags": ["review-packet"],
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
                "notes": "Used for packet source summary.",
            }
        ],
        "failure_log": [
            {
                "failure_id": "failure.fixture.review-packet.0001",
                "attempted_at": "2026-06-19T00:00:00Z",
                "recorded_by": "tester",
                "origin": "human",
                "attempt_kind": "proof_attempt",
                "target": "claim.fixture.review-packet",
                "direction": "prove",
                "summary": "Failed proof attempt",
                "failed_because": "Missing invariant.",
                "evidence_paths": ["docs/evidence.md"],
                "related_verifier_results": [],
                "related_counterexample_candidates": [],
                "next_possible_directions": ["Check smaller cases."],
                "status": "open",
                "limitations": "Fixture only.",
            }
        ],
    }


def _issue_data() -> dict[str, Any]:
    return {
        "id": "issue.fixture.review-packet",
        "type": "issue",
        "title": "Review packet fixture",
        "status": "open",
        "summary": "Generate a review packet from this issue.",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "labels": ["review-packet"],
        "related_artifacts": ["claim.fixture.review-packet"],
        "related_sources": [],
        "scope": "private",
    }


def _fixture_workspace(repo_root: Path) -> None:
    _write_yaml(
        repo_root,
        "kb/draft/claims/claim.fixture.review-packet.yaml",
        _artifact_data(),
    )
    _write_yaml(
        repo_root,
        "issues/open/issue.fixture.review-packet.yaml",
        _issue_data(),
    )
    evidence_path = repo_root / "docs" / "evidence.md"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("Fixture evidence.\n", encoding="utf-8")


def test_web_review_packet_preview_includes_review_context_without_writes(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path))

    preview = api.handle(
        "POST",
        "/api/reviews/packets/preview",
        json.dumps(
            {
                "issue_id": "issue.fixture.review-packet",
                "artifact_id": "claim.fixture.review-packet",
            }
        ),
    )

    assert preview.status == 200
    assert preview.payload["kind"] == "review_packet_preview"
    assert preview.payload["dry_run_only"] is True
    assert preview.payload["repo_writes_performed"] is False
    planned_file = preview.payload["planned_files"][0]
    assert planned_file.startswith("reviews/requests/review.packet.")
    assert not (tmp_path / planned_file).exists()

    packet = preview.payload["review_packet"]
    assert packet["decision"] == "informational"
    assert packet["status"] == "draft"
    sections = packet["sections"]
    assert sections["artifact_statement"] == "Triangle graph $K_3$ should stay draft."
    assert "definition.graph" in sections["dependencies"]
    assert any("Fixture Source" in source for source in sections["sources"])
    assert any("docs/evidence.md" in evidence for evidence in sections["evidence"])
    assert any("Failed proof attempt" in item for item in sections["known_failures"])
    assert any(
        "not human review" in item.lower()
        for item in sections["authority_checklist"]
    )

    entries = _audit_entries(tmp_path)
    assert entries[-1]["action"] == "review.packet_create"
    assert entries[-1]["preview_only"] is True


def test_web_review_packet_create_writes_draft_informational_request_only(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path))
    artifact_path = tmp_path / "kb/draft/claims/claim.fixture.review-packet.yaml"
    before_artifact = _read_yaml(artifact_path)
    payload = {
        "issue_id": "issue.fixture.review-packet",
        "artifact_id": "claim.fixture.review-packet",
    }

    blocked = api.handle(
        "POST",
        "/api/reviews/packets/create",
        json.dumps(payload),
    )
    assert blocked.status == 400
    assert blocked.payload["code"] == "confirm_required"
    assert not (tmp_path / "reviews" / "requests").exists()

    created = api.handle(
        "POST",
        "/api/reviews/packets/create",
        json.dumps({**payload, "confirm": True}),
    )

    assert created.status == 200
    assert created.payload["kind"] == "review_packet_create"
    assert created.payload["repo_writes_performed"] is True
    review_path = tmp_path / created.payload["path"]
    review = _read_yaml(review_path)
    assert review["status"] == "draft"
    assert review["decision"] == "informational"
    assert review["target"] == "claim.fixture.review-packet"
    assert "not human review" in " ".join(review["findings"]).lower()
    assert _read_yaml(artifact_path)["review"] == before_artifact["review"]
    assert _read_yaml(artifact_path)["status"] == "draft"

    entries = _audit_entries(tmp_path)
    assert entries[-1]["action"] == "review.packet_create"
    assert entries[-1]["repo_writes_performed"] is True
