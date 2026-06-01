from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.graph.claim_graph import DependencyGraph, build_dependency_graph
from cosheaf.storage.loader import load_artifacts
from cosheaf.storage.repo import RepoContext


def _write_artifact(
    repo_root: Path,
    relative_path: str,
    *,
    artifact_id: str,
    status: str = "draft",
    depends_on: list[str] | None = None,
) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": "claim",
        "title": f"Claim {artifact_id}",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": [],
        "statement": "Test statement.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Test review."},
        "risk": {"level": "low", "notes": "Test risk."},
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _build_graph(repo_root: Path) -> DependencyGraph:
    records = tuple(load_artifacts(RepoContext(repo_root)))
    return build_dependency_graph(records)


def test_simple_dependency_graph_uses_claim_to_dependency_direction(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
        depends_on=["claim.fixture.b"],
    )
    _write_artifact(tmp_path, "examples/claims/b.yaml", artifact_id="claim.fixture.b")

    graph = _build_graph(tmp_path)

    assert [node.artifact_id for node in graph.nodes] == [
        "claim.fixture.a",
        "claim.fixture.b",
    ]
    assert [(edge.source_id, edge.target_id) for edge in graph.edges] == [
        ("claim.fixture.a", "claim.fixture.b")
    ]


def test_missing_dependency_is_reported(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
        depends_on=["claim.fixture.missing"],
    )

    graph = _build_graph(tmp_path)

    assert [issue.message for issue in graph.missing_dependencies] == [
        "missing dependency: claim.fixture.missing"
    ]


def test_cycle_detection_is_deterministic(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
        depends_on=["claim.fixture.b"],
    )
    _write_artifact(
        tmp_path,
        "examples/claims/b.yaml",
        artifact_id="claim.fixture.b",
        depends_on=["claim.fixture.a"],
    )

    graph = _build_graph(tmp_path)

    assert graph.cycles == (("claim.fixture.a", "claim.fixture.b", "claim.fixture.a"),)


def test_accepted_depends_on_draft_is_reported(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/a.yaml",
        artifact_id="claim.fixture.accepted",
        status="accepted",
        depends_on=["claim.fixture.draft"],
    )
    _write_artifact(
        tmp_path,
        "kb/draft/claims/b.yaml",
        artifact_id="claim.fixture.draft",
        status="draft",
    )

    graph = _build_graph(tmp_path)

    assert [issue.message for issue in graph.accepted_draft_violations] == [
        "accepted artifact depends on draft artifact: claim.fixture.draft"
    ]
