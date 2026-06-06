from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.memory.graph import build_memory_graph, compute_global_pagerank
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    title: str = "Test artifact",
    status: str = "draft",
    domain: list[str] | None = None,
    depends_on: list[str] | None = None,
    supersedes: list[str] | None = None,
    sources: list[dict[str, Any]] | None = None,
    formalizations: list[dict[str, Any]] | None = None,
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
        "supersedes": supersedes or [],
        "tags": [],
        "statement": "Fixture statement.",
        "evidence": [],
        "sources": sources or [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }
    if formalizations is not None:
        data["formalizations"] = formalizations
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
    supersedes: list[str] | None = None,
    sources: list[dict[str, Any]] | None = None,
    formalizations: list[dict[str, Any]] | None = None,
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
                supersedes=supersedes,
                sources=sources,
                formalizations=formalizations,
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_issue(
    repo_root: Path,
    *,
    issue_id: str,
    related_artifacts: list[str],
) -> None:
    path = repo_root / "issues" / "open" / f"{issue_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "id": issue_id,
                "type": "issue",
                "title": "Memory graph issue",
                "status": "open",
                "created_at": "2026-06-01T00:00:00Z",
                "updated_at": "2026-06-01T00:00:00Z",
                "authors": ["tester"],
                "severity": "medium",
                "description": "Issue for memory graph fixtures.",
                "related_artifacts": related_artifacts,
                "tags": ["memory-graph"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_review(
    repo_root: Path,
    *,
    review_id: str,
    target: str,
    status: str = "human_reviewed",
    decision: str = "approve",
) -> None:
    path = repo_root / "reviews" / "human" / f"{review_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "id": review_id,
                "type": "review",
                "title": "Memory graph review",
                "status": status,
                "created_at": "2026-06-01T00:00:00Z",
                "updated_at": "2026-06-01T00:00:00Z",
                "authors": ["tester"],
                "target": target,
                "summary": "Fixture review.",
                "findings": ["Fixture finding."],
                "decision": decision,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_task(
    repo_root: Path,
    *,
    task_id: str,
    issue_id: str,
) -> None:
    path = repo_root / "examples" / "tasks" / f"{task_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "task_id": task_id,
                "issue_id": issue_id,
                "worker_type": "reasoner",
                "status": "completed",
                "input_context": [f"context/TASKS/{issue_id}/CONTEXT.md"],
                "budget": {"max_iterations": 1},
                "expected_outputs": ["worker_notes"],
                "created_at": "2026-06-01T00:00:00Z",
                "updated_at": "2026-06-01T00:00:00Z",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_task_run(
    repo_root: Path,
    *,
    task_id: str,
    run_id: str,
    status: str = "completed",
) -> None:
    run_dir = repo_root / ".cosheaf" / "tasks" / task_id / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "task_id": task_id,
                "worker_type": "reasoner",
                "command": ["python", "-c", "print('ok')"],
                "cwd": ".",
                "started_at": "2026-06-01T00:00:00Z",
                "finished_at": "2026-06-01T00:00:00Z",
                "timeout_seconds": 60,
                "returncode": 0 if status == "completed" else 1,
                "stdout_path": "stdout.txt",
                "stderr_path": "stderr.txt",
                "bundle_path": None,
                "bundle_valid": None,
                "status": status,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_gate_report_with_verifier_failure(
    repo_root: Path,
    *,
    artifact_id: str,
) -> None:
    report_dir = repo_root / ".cosheaf" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "20260601T000000000000Z-gate-report.json").write_text(
        json.dumps(
            {
                "verdict": "fail",
                "gates": [
                    {
                        "id": "G6",
                        "details": [
                            {
                                "verifier": "python_checker",
                                "artifact_id": artifact_id,
                                "status": "fail",
                                "message": "Fixture verifier failure.",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _source_fixture() -> dict[str, Any]:
    return {
        "kind": "paper",
        "title": "A graph source",
        "authors": ["A. Author"],
        "year": 2026,
        "doi": "10.1145/fixture",
        "url": "https://example.org/fixture",
        "theorem_number": "Definition 1",
        "page": "7",
        "notes": "Fixture source metadata.",
    }


def _formalization_fixture() -> dict[str, Any]:
    return {
        "id": "cslib.fixture.graph",
        "system": "lean4",
        "library": "CSLib",
        "library_ref": "cslib-main",
        "import_path": "CSLib.Graph.Basic",
        "symbol": "CSLib.Graph.Basic.fixture_graph",
        "declaration_kind": "definition",
        "status": "planned",
        "check_mode": "external_library_ref",
        "expected_type": "Fixture Lean type.",
        "notes": "Metadata-only fixture.",
    }


def _write_graph_fixture(repo_root: Path) -> None:
    _write_artifact(
        repo_root,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
        domain=["graph-theory"],
        sources=[_source_fixture()],
        formalizations=[_formalization_fixture()],
    )
    _write_artifact(
        repo_root,
        "kb/accepted/definitions/vertex.yaml",
        artifact_id="definition.fixture.vertex",
        artifact_type="definition",
        title="Vertex",
        status="accepted",
        domain=["graph-theory"],
    )
    _write_artifact(
        repo_root,
        "kb/draft/claims/old.yaml",
        artifact_id="claim.fixture.old",
        title="Old draft",
        status="draft",
        domain=["graph-theory"],
    )
    _write_artifact(
        repo_root,
        "kb/draft/claims/derived.yaml",
        artifact_id="claim.fixture.derived",
        title="Derived draft",
        status="draft",
        domain=["graph-theory"],
        depends_on=["definition.fixture.graph"],
        supersedes=["claim.fixture.old"],
    )
    _write_issue(
        repo_root,
        issue_id="issue.fixture.graph",
        related_artifacts=["claim.fixture.derived", "definition.fixture.graph"],
    )
    _write_review(
        repo_root,
        review_id="review.fixture.derived",
        target="claim.fixture.derived",
    )
    task_id = "task.issue.fixture.graph.reasoner"
    _write_task(repo_root, task_id=task_id, issue_id="issue.fixture.graph")
    _write_task_run(
        repo_root,
        task_id=task_id,
        run_id="run.r20260601.t000000z",
    )
    _write_gate_report_with_verifier_failure(
        repo_root,
        artifact_id="claim.fixture.derived",
    )


def test_memory_graph_builds_nodes_edges_and_rebuildable_sidecar(
    tmp_path: Path,
) -> None:
    _write_graph_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["memory", "graph", "build", "--repo-root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    assert payload["node_count"] >= 8
    assert payload["edge_count"] >= 9
    assert payload["sidecar_path"] == ".cosheaf/memory/graph_snapshot.json"

    sidecar = tmp_path / ".cosheaf" / "memory" / "graph_snapshot.json"
    assert sidecar.exists()
    snapshot = json.loads(sidecar.read_text(encoding="utf-8"))
    node_kinds = {node["kind"] for node in snapshot["nodes"]}
    assert {
        "artifact",
        "issue",
        "review",
        "source_note",
        "formalization",
        "verifier_result",
        "task_run",
    } <= node_kinds
    edge_kinds = {edge["kind"] for edge in snapshot["edges"]}
    assert {
        "depends_on",
        "supersedes",
        "cites_source",
        "reviews",
        "formalizes",
        "same_domain",
        "same_issue_context",
        "used_in_success",
        "rejected_by_verifier",
    } <= edge_kinds
    assert snapshot["warnings"] == [
        "memory graph is a rebuildable ranking sidecar, not source of truth",
        "formal links are metadata only unless a checker verifies them",
    ]
    repo_gitignore = Path(__file__).resolve().parents[1] / ".gitignore"
    assert ".cosheaf/" in repo_gitignore.read_text(encoding="utf-8")


def test_memory_graph_pagerank_is_deterministic(tmp_path: Path) -> None:
    _write_graph_fixture(tmp_path)
    graph = build_memory_graph(RepoContext(tmp_path), persist=True)

    first = compute_global_pagerank(graph)
    second = compute_global_pagerank(graph)

    assert first.to_dict() == second.to_dict()
    assert first.rows
    scores = [row.score for row in first.rows]
    assert scores == sorted(scores, reverse=True)
    assert first.rows[0].node_id
    assert first.rows[0].rank == 1


def test_memory_graph_pagerank_cli_reads_existing_sidecar(tmp_path: Path) -> None:
    _write_graph_fixture(tmp_path)
    build_result = runner.invoke(
        app,
        ["memory", "graph", "build", "--repo-root", str(tmp_path), "--json"],
    )
    assert build_result.exit_code == 0, build_result.output

    result = runner.invoke(
        app,
        [
            "memory",
            "graph",
            "pagerank",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    assert payload["algorithm"] == "weighted-pagerank"
    assert payload["graph_fingerprint"].startswith("sha256:")
    assert payload["rows"][0]["rank"] == 1
    assert payload["rows"][0]["score"] > 0


def test_memory_graph_pagerank_requires_built_sidecar(tmp_path: Path) -> None:
    _write_graph_fixture(tmp_path)

    result = runner.invoke(
        app,
        [
            "memory",
            "graph",
            "pagerank",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code != 0
    assert "run `cosheaf memory graph build` first" in result.output
