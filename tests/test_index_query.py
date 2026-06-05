from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.storage.index import rebuild_index
from cosheaf.storage.query import (
    ArtifactIndexQuery,
    ArtifactQueryRow,
    DependencyQueryRow,
    FormalizationQueryRow,
    FormalPolicyQueryRow,
    IndexQueryError,
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
    formalizations: list[dict[str, Any]] | None = None,
    alignment: dict[str, Any] | None = None,
    verification_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
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
    if formalizations is not None:
        data["formalizations"] = formalizations
    if alignment is not None:
        data["alignment"] = alignment
    if verification_policy is not None:
        data["verification_policy"] = verification_policy
    return data


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
    formalizations: list[dict[str, Any]] | None = None,
    alignment: dict[str, Any] | None = None,
    verification_policy: dict[str, Any] | None = None,
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
                formalizations=formalizations,
                alignment=alignment,
                verification_policy=verification_policy,
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _formalization_fixture(
    *,
    formalization_id: str = "cslib.fixture.link",
    library: str = "CSLib",
    library_ref: str = "cslib-main",
    import_path: str = "CSLib.Graph.Basic",
    symbol: str = "CSLib.Graph.Basic.fixture_symbol",
    status: str = "planned",
) -> dict[str, Any]:
    return {
        "id": formalization_id,
        "system": "lean4",
        "library": library,
        "library_ref": library_ref,
        "import_path": import_path,
        "symbol": symbol,
        "declaration_kind": "theorem",
        "status": status,
        "check_mode": "external_library_ref",
        "expected_type": "Fixture Lean type.",
        "notes": "Fixture formalization link.",
    }


def _formal_link_policy(
    *,
    level: str = "source_reviewed_with_formal_link",
    require_formal_link: bool = True,
    require_lean_check: bool = False,
    require_alignment_review: bool = False,
) -> dict[str, Any]:
    return {
        "level": level,
        "require_formal_link": require_formal_link,
        "require_lean_check": require_lean_check,
        "require_alignment_review": require_alignment_review,
    }


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


def test_query_api_reads_formalizations_deterministically(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/formal-b.yaml",
        artifact_id="claim.fixture.formal-b",
        title="B",
        formalizations=[
            _formalization_fixture(
                formalization_id="mathlib.fixture.b",
                library="mathlib",
                library_ref="mathlib-main",
                import_path="Mathlib.Combinatorics.Graph.Basic",
                symbol="Mathlib.Combinatorics.Graph.Basic.b_symbol",
                status="linked",
            ),
        ],
        verification_policy=_formal_link_policy(),
    )
    _write_artifact(
        tmp_path,
        "examples/claims/formal-a.yaml",
        artifact_id="claim.fixture.formal-a",
        title="A",
        formalizations=[
            _formalization_fixture(
                formalization_id="cslib.fixture.z-link",
                symbol="CSLib.Graph.Basic.z_symbol",
                status="checked",
            ),
            _formalization_fixture(
                formalization_id="cslib.fixture.a-link",
                symbol="CSLib.Graph.Basic.a_symbol",
                status="planned",
            ),
        ],
        alignment={
            "status": "human_reviewed",
            "reviewer": "reviewer@example.org",
            "reviewed_at": "2026-06-01T00:00:00Z",
            "convention_notes": [],
            "limitations": "",
        },
        verification_policy=_formal_link_policy(
            level="machine_checked",
            require_lean_check=True,
            require_alignment_review=True,
        ),
    )
    _write_artifact(
        tmp_path,
        "examples/claims/plain.yaml",
        artifact_id="claim.fixture.plain",
        title="Plain",
    )
    context = RepoContext(tmp_path)
    rebuild_index(context)

    query = ArtifactIndexQuery.from_context(context)

    assert query.list_formalizations() == (
        FormalizationQueryRow(
            artifact_id="claim.fixture.formal-a",
            formalization_id="cslib.fixture.a-link",
            system="lean4",
            library="CSLib",
            library_ref="cslib-main",
            import_path="CSLib.Graph.Basic",
            symbol="CSLib.Graph.Basic.a_symbol",
            declaration_kind="theorem",
            status="planned",
            check_mode="external_library_ref",
            expected_type="Fixture Lean type.",
            notes="Fixture formalization link.",
        ),
        FormalizationQueryRow(
            artifact_id="claim.fixture.formal-a",
            formalization_id="cslib.fixture.z-link",
            system="lean4",
            library="CSLib",
            library_ref="cslib-main",
            import_path="CSLib.Graph.Basic",
            symbol="CSLib.Graph.Basic.z_symbol",
            declaration_kind="theorem",
            status="checked",
            check_mode="external_library_ref",
            expected_type="Fixture Lean type.",
            notes="Fixture formalization link.",
        ),
        FormalizationQueryRow(
            artifact_id="claim.fixture.formal-b",
            formalization_id="mathlib.fixture.b",
            system="lean4",
            library="mathlib",
            library_ref="mathlib-main",
            import_path="Mathlib.Combinatorics.Graph.Basic",
            symbol="Mathlib.Combinatorics.Graph.Basic.b_symbol",
            declaration_kind="theorem",
            status="linked",
            check_mode="external_library_ref",
            expected_type="Fixture Lean type.",
            notes="Fixture formalization link.",
        ),
    )
    assert [
        row.formalization_id
        for row in query.list_formalizations_for_artifact("claim.fixture.formal-a")
    ] == ["cslib.fixture.a-link", "cslib.fixture.z-link"]
    assert query.list_formalizations_for_artifact("claim.fixture.missing") == ()
    assert [
        row.formalization_id
        for row in query.list_formalizations_by_library("CSLib")
    ] == ["cslib.fixture.a-link", "cslib.fixture.z-link"]
    assert [
        row.artifact_id
        for row in query.list_formalizations_by_symbol(
            "CSLib.Graph.Basic.a_symbol"
        )
    ] == ["claim.fixture.formal-a"]
    assert [
        row.formalization_id
        for row in query.list_formalizations_by_status("planned")
    ] == ["cslib.fixture.a-link"]
    assert [
        row.formalization_id
        for row in query.list_formalizations_by_import("CSLib.Graph.Basic")
    ] == ["cslib.fixture.a-link", "cslib.fixture.z-link"]

    assert query.get_formal_policy("claim.fixture.formal-a") == FormalPolicyQueryRow(
        artifact_id="claim.fixture.formal-a",
        alignment_status="human_reviewed",
        alignment_reviewer="reviewer@example.org",
        verification_level="machine_checked",
        require_formal_link=True,
        require_lean_check=True,
        require_alignment_review=True,
    )
    assert query.get_formal_policy("claim.fixture.missing") is None
    requiring_formal_link = query.list_artifacts_requiring_formal_link()
    assert [row.artifact_id for row in requiring_formal_link] == [
        "claim.fixture.formal-a",
        "claim.fixture.formal-b",
    ]
    assert [row.artifact_id for row in query.list_artifacts_requiring_lean_check()] == [
        "claim.fixture.formal-a",
    ]
    assert [
        row.artifact_id
        for row in query.list_artifacts_requiring_alignment_review()
    ] == ["claim.fixture.formal-a"]


def test_query_api_does_not_rebuild_or_modify_index_outputs(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/formal.yaml",
        artifact_id="claim.fixture.formal",
        title="Formal",
        formalizations=[_formalization_fixture()],
        verification_policy=_formal_link_policy(),
    )
    context = RepoContext(tmp_path)
    result = rebuild_index(context)
    before_sqlite_mtime = result.sqlite_path.stat().st_mtime_ns
    before_manifest_mtime = result.manifest_path.stat().st_mtime_ns

    query = ArtifactIndexQuery.from_context(context)
    assert len(query.list_formalizations()) == 1
    assert query.list_artifacts_requiring_formal_link()[0].artifact_id == (
        "claim.fixture.formal"
    )

    assert result.sqlite_path.stat().st_mtime_ns == before_sqlite_mtime
    assert result.manifest_path.stat().st_mtime_ns == before_manifest_mtime


def test_query_api_missing_index_still_raises_index_query_error(
    tmp_path: Path,
) -> None:
    try:
        ArtifactIndexQuery.from_context(RepoContext(tmp_path))
    except IndexQueryError as exc:
        assert "index sqlite file does not exist" in str(exc)
    else:
        raise AssertionError("missing index should raise IndexQueryError")
