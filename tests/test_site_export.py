from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.site import REQUIRED_SITE_EXPORT_FILES, export_site_data
from cosheaf.storage.repo import RepoContext

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _artifact_data(
    artifact_id: str,
    *,
    title: str,
    status: str = "draft",
    depends_on: list[str] | None = None,
    tags: list[str] | None = None,
    statement: str = "Full statement must not be exported.",
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": title,
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": tags or ["site-export"],
        "statement": statement,
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _issue_data(
    issue_id: str = "issue.fixture.site-export",
    *,
    scope: str = "public",
    labels: list[str] | None = None,
    related_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Site export fixture issue",
        "status": "open",
        "summary": "Exercise the deterministic website export.",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "labels": labels or ["site-export"],
        "related_artifacts": related_artifacts or [],
        "related_sources": [],
        "scope": scope,
    }


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "site-export-workspace"',
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


def _fixture_workspace(repo_root: Path) -> None:
    _write_workspace_config(repo_root)
    _write_yaml(
        repo_root,
        "kb/public/draft/claims/public.yaml",
        _artifact_data(
            "claim.fixture.site-public",
            title="Public site export claim",
            status="draft",
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/private.yaml",
        _artifact_data(
            "claim.fixture.site-private",
            title="PRIVATE SECRET SITE CLAIM",
            status="draft",
            depends_on=["claim.fixture.site-public"],
            statement="PRIVATE SECRET STATEMENT",
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/demo-private.yaml",
        _artifact_data(
            "claim.fixture.site-demo-private",
            title="Demo private site export claim",
            status="draft",
            depends_on=["claim.fixture.site-public"],
            tags=["workspace-demo"],
            statement="DEMO PRIVATE STATEMENT SHOULD NOT APPEAR",
        ),
    )
    _write_yaml(
        repo_root,
        "issues/open/site-export.yaml",
        _issue_data(
            related_artifacts=[
                "claim.fixture.site-public",
                "claim.fixture.site-private",
            ],
        ),
    )
    _write_yaml(
        repo_root,
        "issues/open/site-demo.yaml",
        _issue_data(
            "issue.fixture.site-demo",
            scope="private",
            labels=["workspace-demo"],
            related_artifacts=[
                "claim.fixture.site-public",
                "claim.fixture.site-demo-private",
                "claim.fixture.site-private",
            ],
        ),
    )


def _read_outputs(out: Path) -> dict[str, Any]:
    return {
        relative_path: json.loads((out / relative_path).read_text(encoding="utf-8"))
        for relative_path in REQUIRED_SITE_EXPORT_FILES
    }


def _assert_matches_site_export_schema(payload: dict[str, Any]) -> None:
    schema = json.loads(
        (ROOT / "schemas/site_export.schema.json").read_text(encoding="utf-8")
    )
    for key in schema["required"]:
        assert key in payload
    assert payload["schema_version"] == schema["properties"]["schema_version"]["const"]
    assert payload["kind"] in schema["properties"]["kind"]["enum"]
    assert isinstance(payload["authority_notice"], str)
    assert payload["authority_notice"]


def test_site_export_writes_required_files_and_schema_fields(tmp_path: Path) -> None:
    _fixture_workspace(tmp_path)

    result = export_site_data(RepoContext(tmp_path), tmp_path / ".cosheaf/site-data")

    assert result.files == REQUIRED_SITE_EXPORT_FILES
    exported = _read_outputs(tmp_path / ".cosheaf/site-data")
    assert set(exported) == set(REQUIRED_SITE_EXPORT_FILES)
    for filename, payload in exported.items():
        _assert_matches_site_export_schema(payload)
        assert payload["schema_version"] == 1
        assert payload["kind"] == filename.removesuffix(".json")
        assert "authority_notice" in payload
    artifacts = {
        artifact["id"]: artifact for artifact in exported["artifacts.json"]["artifacts"]
    }
    assert "claim.fixture.site-public" in artifacts
    assert "statement" not in artifacts["claim.fixture.site-public"]


def test_site_export_public_only_excludes_private_content(tmp_path: Path) -> None:
    _fixture_workspace(tmp_path)

    export_site_data(
        RepoContext(tmp_path),
        tmp_path / ".cosheaf/site-data",
        public_only=True,
    )

    combined = "\n".join(
        (tmp_path / ".cosheaf/site-data" / name).read_text(encoding="utf-8")
        for name in REQUIRED_SITE_EXPORT_FILES
    )
    assert "PRIVATE SECRET" not in combined
    assert "claim.fixture.site-private" not in combined
    assert "claim.fixture.site-demo-private" not in combined
    assert "claim.fixture.site-public" in combined


def test_site_export_demo_includes_marked_private_fixtures(tmp_path: Path) -> None:
    _fixture_workspace(tmp_path)

    export_site_data(
        RepoContext(tmp_path),
        tmp_path / ".cosheaf/site-data",
        demo=True,
    )

    exported = _read_outputs(tmp_path / ".cosheaf/site-data")
    artifact_ids = {
        artifact["id"] for artifact in exported["artifacts.json"]["artifacts"]
    }
    issues = {
        issue["id"]: issue for issue in exported["issues.json"]["issues"]
    }
    combined = "\n".join(
        (tmp_path / ".cosheaf/site-data" / name).read_text(encoding="utf-8")
        for name in REQUIRED_SITE_EXPORT_FILES
    )

    assert "claim.fixture.site-demo-private" in artifact_ids
    assert "claim.fixture.site-private" not in artifact_ids
    assert "PRIVATE SECRET" not in combined
    assert "DEMO PRIVATE STATEMENT SHOULD NOT APPEAR" not in combined
    assert issues["issue.fixture.site-demo"]["demo_fixture"] is True
    assert issues["issue.fixture.site-demo"]["related_artifacts"] == [
        "claim.fixture.site-public",
        "claim.fixture.site-demo-private",
    ]


def test_site_export_is_deterministic(tmp_path: Path) -> None:
    _fixture_workspace(tmp_path)

    export_site_data(RepoContext(tmp_path), tmp_path / "first")
    export_site_data(RepoContext(tmp_path), tmp_path / "second")

    for filename in REQUIRED_SITE_EXPORT_FILES:
        assert (tmp_path / "first" / filename).read_bytes() == (
            tmp_path / "second" / filename
        ).read_bytes()


def test_site_export_empty_workspace(tmp_path: Path) -> None:
    result = export_site_data(RepoContext(tmp_path), tmp_path / "site-data")

    exported = _read_outputs(tmp_path / "site-data")
    assert result.file_count == len(REQUIRED_SITE_EXPORT_FILES)
    assert exported["artifacts.json"]["artifacts"] == []
    assert exported["issues.json"]["issues"] == []
    assert exported["graph.json"]["nodes"] == []
    assert exported["gates.json"]["blocking_issues"] == []


def test_site_export_demo_flag_and_cli(tmp_path: Path) -> None:
    _fixture_workspace(tmp_path)
    out = tmp_path / ".cosheaf/site-data"

    result = runner.invoke(
        app,
        [
            "site",
            "export",
            "--demo",
            "--public-only",
            "--out",
            str(out),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    assert payload["out"] == str(out)
    assert payload["demo"] is True
    assert payload["public_only"] is True
    assert payload["file_count"] == len(REQUIRED_SITE_EXPORT_FILES)
    assert json.loads((out / "site.json").read_text(encoding="utf-8"))["demo"] is True
