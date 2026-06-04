from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.storage.index import rebuild_index
from cosheaf.storage.query import (
    ArtifactIndexQuery,
    ArtifactQueryRow,
    DependencyQueryRow,
)
from cosheaf.storage.repo import RepoContext


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    title: str = "Test artifact",
    status: str = "draft",
    domain: list[str] | None = None,
    depends_on: list[str] | None = None,
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
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": [],
        "statement": "Test statement.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Test review."},
        "risk": {"level": "low", "notes": "Test risk."},
    }


def _write_artifact(
    repo_root: Path,
    relative_path: str,
    *,
    artifact_id: str,
    artifact_type: str = "claim",
    title: str = "Test artifact",
    status: str = "draft",
    domain: list[str] | None = None,
    depends_on: list[str] | None = None,
) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            _artifact_data(
                artifact_id,
                artifact_type=artifact_type,
                title=title,
                status=status,
                domain=domain,
                depends_on=depends_on,
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "query-workspace"',
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


def test_query_api_reads_legacy_index_deterministically(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/draft/claims/b.yaml",
        artifact_id="claim.fixture.b",
        title="B",
        domain=["testing", "shared"],
    )
    _write_artifact(
        tmp_path,
        "kb/draft/claims/a.yaml",
        artifact_id="claim.fixture.a",
        title="A",
        domain=["testing"],
        depends_on=["claim.fixture.b", "definition.fixture.c"],
    )
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/c.yaml",
        artifact_id="definition.fixture.c",
        artifact_type="definition",
        title="C",
        status="accepted",
        domain=["shared"],
    )
    context = RepoContext(tmp_path)
    rebuild_index(context)

    query = ArtifactIndexQuery.from_context(context)

    assert [artifact.id for artifact in query.list_artifacts()] == [
        "claim.fixture.a",
        "claim.fixture.b",
        "definition.fixture.c",
    ]
    assert query.get_artifact("claim.fixture.a") == ArtifactQueryRow(
        id="claim.fixture.a",
        type="claim",
        status="draft",
        path="kb/draft/claims/a.yaml",
        title="A",
        domain=("testing",),
        kb_root="default",
    )
    assert query.get_artifact("claim.fixture.missing") is None
    assert [artifact.id for artifact in query.list_artifacts_by_status("draft")] == [
        "claim.fixture.a",
        "claim.fixture.b",
    ]
    assert [artifact.id for artifact in query.list_artifacts_by_type("definition")] == [
        "definition.fixture.c"
    ]
    assert [artifact.id for artifact in query.list_artifacts_by_domain("shared")] == [
        "claim.fixture.b",
        "definition.fixture.c",
    ]
    assert query.list_dependencies("claim.fixture.a") == (
        DependencyQueryRow("claim.fixture.a", "claim.fixture.b"),
        DependencyQueryRow("claim.fixture.a", "definition.fixture.c"),
    )
    assert query.list_reverse_dependencies("definition.fixture.c") == (
        DependencyQueryRow("claim.fixture.a", "definition.fixture.c"),
    )


def test_query_api_preserves_workspace_kb_roots(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
        domain=["graph-theory"],
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private.yaml",
        artifact_id="claim.fixture.private",
        title="Private claim",
        domain=["graph-theory", "workspace"],
        depends_on=["definition.fixture.graph"],
    )
    context = RepoContext(tmp_path)
    rebuild_index(context)

    query = ArtifactIndexQuery.from_context(context)

    public = query.get_artifact("definition.fixture.graph")
    private = query.get_artifact("claim.fixture.private")
    assert public is not None
    assert private is not None
    assert public.kb_root == "public"
    assert public.path == "kb/public/accepted/definitions/graph.yaml"
    assert private.kb_root == "private"
    assert private.path == "kb/private/draft/claims/private.yaml"
    graph_artifact_ids = [
        artifact.id
        for artifact in query.list_artifacts_by_domain("graph-theory")
    ]
    assert graph_artifact_ids == ["claim.fixture.private", "definition.fixture.graph"]
    assert query.list_reverse_dependencies("definition.fixture.graph") == (
        DependencyQueryRow("claim.fixture.private", "definition.fixture.graph"),
    )
