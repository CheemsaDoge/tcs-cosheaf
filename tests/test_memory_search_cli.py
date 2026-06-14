from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pytest import MonkeyPatch
from typer.testing import CliRunner

import cosheaf.memory.search as memory_search_module
from cosheaf.cli import app
from cosheaf.memory import RetrievalScoreWeights, search_artifact_cards
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    title: str,
    status: str = "draft",
    domain: list[str] | None = None,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
    statement: str = "Fixture statement.",
    failure_log: list[dict[str, Any]] | None = None,
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
        "tags": tags or [],
        "statement": statement,
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }
    if failure_log is not None:
        data["failure_log"] = failure_log
    return data


def _write_artifact(
    repo_root: Path,
    relative_path: str,
    *,
    artifact_id: str,
    artifact_type: str = "claim",
    title: str,
    status: str = "draft",
    domain: list[str] | None = None,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
    statement: str = "Fixture statement.",
    failure_log: list[dict[str, Any]] | None = None,
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
                tags=tags,
                depends_on=depends_on,
                statement=statement,
                failure_log=failure_log,
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _failure_log_entry(
    *,
    failure_id: str = "failure.fixture.0001",
    direction: str = "Try a separator induction on the bad component",
    failed_because: str = "The separator premise is unavailable for the draft.",
) -> dict[str, Any]:
    return {
        "failure_id": failure_id,
        "attempted_at": "2026-06-02T00:00:00Z",
        "recorded_by": "tester",
        "origin": "human",
        "attempt_kind": "proof_attempt",
        "target": "",
        "direction": direction,
        "summary": "Fixture failed attempt memory.",
        "failed_because": failed_because,
        "evidence_paths": [],
        "related_verifier_results": [],
        "related_counterexample_candidates": [],
        "next_possible_directions": [],
        "status": "open",
        "limitations": "Failure memory only; not proof or refutation.",
    }


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
                "title": "Memory search issue",
                "status": "open",
                "created_at": "2026-06-01T00:00:00Z",
                "updated_at": "2026-06-01T00:00:00Z",
                "authors": ["tester"],
                "severity": "medium",
                "description": "Issue for memory search filtering.",
                "related_artifacts": related_artifacts,
                "tags": ["memory-search"],
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


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "memory-search-workspace"',
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


def test_memory_search_json_returns_ranked_cards_with_audit(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/planar.yaml",
        artifact_id="definition.fixture.planar-separator",
        artifact_type="definition",
        title="Planar separator theorem",
        status="accepted",
        domain=["graph-theory"],
        tags=["planar", "separator"],
        statement="SECRET FULL STATEMENT SHOULD NOT APPEAR",
    )
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/tree.yaml",
        artifact_id="definition.fixture.tree",
        artifact_type="definition",
        title="Tree",
        status="accepted",
        domain=["graph-theory"],
        tags=["tree"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "planar separator",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    assert payload["request_id"].startswith("retrieval.memory.search.")
    assert payload["index_fingerprint"].startswith("sha256:")
    assert payload["audit"]["filters_applied"][:2] == [
        "scope:public,workspace,framework",
        "status:accepted,human_reviewed,machine_checked,locally_tested",
    ]
    assert payload["cards"][0]["card"]["id"] == (
        "definition.fixture.planar-separator"
    )
    assert payload["cards"][0]["score_breakdown"]["retrieval_hybrid"] > 0
    assert payload["cards"][0]["score_breakdown"]["total"] > 0
    assert "lexical" in " ".join(payload["cards"][0]["why_relevant"]).lower() or (
        "fts" in " ".join(payload["cards"][0]["why_relevant"]).lower()
    )
    assert "SECRET FULL STATEMENT" not in result.output
    assert not (tmp_path / ".cosheaf" / "memory").exists()


def test_memory_search_status_filter_excludes_draft(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph foundation",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
    )
    _write_artifact(
        tmp_path,
        "kb/draft/claims/draft.yaml",
        artifact_id="claim.fixture.graph-draft",
        title="Graph draft",
        status="draft",
        domain=["graph-theory"],
        tags=["graph"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "graph",
            "--repo-root",
            str(tmp_path),
            "--status",
            "accepted",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert [hit["card"]["id"] for hit in payload["cards"]] == [
        "definition.fixture.graph"
    ]
    assert "claim.fixture.graph-draft" not in [
        hit["card"]["id"] for hit in payload["cards"]
    ]
    assert payload["audit"]["excluded"] == [
        {
            "artifact_id": "claim.fixture.graph-draft",
            "reason": "status excluded: draft not in accepted",
        }
    ]


def test_memory_search_text_output_is_compact(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
        statement="SECRET FULL STATEMENT SHOULD NOT APPEAR",
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "graph",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "definition.fixture.graph | score=" in result.output
    assert "Graph | accepted | workspace | kb/accepted/definitions/graph.yaml" in (
        result.output
    )
    assert "SECRET FULL STATEMENT" not in result.output


def test_memory_search_issue_ranking_and_private_default_scope(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Public graph",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
    )
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/walk.yaml",
        artifact_id="definition.fixture.walk",
        artifact_type="definition",
        title="Walk",
        status="accepted",
        domain=["graph-theory"],
        tags=["walk"],
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private.yaml",
        artifact_id="claim.fixture.private",
        title="Private graph conjecture",
        status="draft",
        domain=["graph-theory"],
        tags=["graph"],
        depends_on=["definition.fixture.graph"],
    )
    _write_issue(
        tmp_path,
        issue_id="issue.fixture.search",
        related_artifacts=["definition.fixture.graph", "claim.fixture.private"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "graph",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.fixture.search",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    ids = [hit["card"]["id"] for hit in payload["cards"]]
    assert ids[0] == "definition.fixture.graph"
    assert "definition.fixture.walk" in ids
    assert "claim.fixture.private" not in result.output
    assert payload["audit"]["excluded"] == []
    assert any(
        "private scope exclusions" in warning
        for warning in payload["audit"]["warnings"]
    )


def test_memory_search_json_output_is_deterministic(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
    )

    args = [
        "memory",
        "search",
        "graph",
        "--repo-root",
        str(tmp_path),
        "--json",
    ]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert first.output == second.output


def test_memory_search_falls_back_when_sqlite_fts_is_unavailable(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
    )

    class _BrokenFtsConnection:
        def execute(self, *_args: object, **_kwargs: object) -> None:
            raise sqlite3.DatabaseError("no fts5")

        def close(self) -> None:
            return None

    def _broken_connect(_database: str) -> _BrokenFtsConnection:
        return _BrokenFtsConnection()

    monkeypatch.setattr(memory_search_module.sqlite3, "connect", _broken_connect)

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "graph",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert [hit["card"]["id"] for hit in payload["cards"]] == [
        "definition.fixture.graph"
    ]
    assert any(
        "lexical fallback used" in warning
        for warning in payload["audit"]["warnings"]
    )


def test_memory_search_issue_conditioned_pagerank_uses_seed_artifacts(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/target.yaml",
        artifact_id="definition.fixture.seed-target",
        artifact_type="definition",
        title="Target foundation",
        status="accepted",
        domain=["graph-theory"],
        tags=["target"],
    )
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/seed.yaml",
        artifact_id="claim.fixture.seed",
        title="Seed claim",
        status="accepted",
        domain=["graph-theory"],
        tags=["seed"],
        depends_on=["definition.fixture.seed-target"],
    )
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/unrelated.yaml",
        artifact_id="definition.fixture.unrelated",
        artifact_type="definition",
        title="Target unrelated",
        status="accepted",
        domain=["logic"],
        tags=["target"],
    )
    _write_issue(
        tmp_path,
        issue_id="issue.fixture.personalized",
        related_artifacts=["claim.fixture.seed"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "target",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.fixture.personalized",
            "--seed-artifact",
            "claim.fixture.seed",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    ids = [hit["card"]["id"] for hit in payload["cards"]]
    assert ids.index("definition.fixture.seed-target") < ids.index(
        "definition.fixture.unrelated"
    )
    target = next(
        hit
        for hit in payload["cards"]
        if hit["card"]["id"] == "definition.fixture.seed-target"
    )
    unrelated = next(
        hit
        for hit in payload["cards"]
        if hit["card"]["id"] == "definition.fixture.unrelated"
    )
    assert target["score_breakdown"]["personalized_pagerank"] > (
        unrelated["score_breakdown"]["personalized_pagerank"]
    )
    assert target["score_breakdown"]["global_pagerank"] > 0
    assert any(
        "personalized pagerank" in reason.lower()
        for reason in target["why_relevant"]
    )


def test_memory_search_pinned_artifact_and_successful_run_influence_ranking(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/pinned.yaml",
        artifact_id="definition.fixture.pinned",
        artifact_type="definition",
        title="Pinned target",
        status="accepted",
        domain=["graph-theory"],
        tags=["target"],
    )
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/recent.yaml",
        artifact_id="definition.fixture.recent-success",
        artifact_type="definition",
        title="Recent target",
        status="accepted",
        domain=["graph-theory"],
        tags=["target"],
    )
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/plain.yaml",
        artifact_id="definition.fixture.plain",
        artifact_type="definition",
        title="Plain target",
        status="accepted",
        domain=["logic"],
        tags=["target"],
    )
    issue_id = "issue.fixture.personalized-runs"
    _write_issue(
        tmp_path,
        issue_id=issue_id,
        related_artifacts=["definition.fixture.recent-success"],
    )
    task_id = "task.issue.fixture.personalized-runs.reasoner"
    _write_task(tmp_path, task_id=task_id, issue_id=issue_id)
    _write_task_run(
        tmp_path,
        task_id=task_id,
        run_id="run.r20260601.t000000z",
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "target",
            "--repo-root",
            str(tmp_path),
            "--issue",
            issue_id,
            "--pin-artifact",
            "definition.fixture.pinned",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    by_id = {hit["card"]["id"]: hit for hit in payload["cards"]}
    assert by_id["definition.fixture.pinned"]["score_breakdown"][
        "personalized_pagerank"
    ] > by_id["definition.fixture.plain"]["score_breakdown"][
        "personalized_pagerank"
    ]
    assert by_id["definition.fixture.recent-success"]["score_breakdown"][
        "freshness"
    ] > by_id["definition.fixture.plain"]["score_breakdown"]["freshness"]
    assert by_id["definition.fixture.recent-success"]["score_breakdown"][
        "personalized_pagerank"
    ] > 0


def test_memory_search_issue_ranking_keeps_accepted_priority(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/accepted.yaml",
        artifact_id="definition.fixture.accepted-priority",
        artifact_type="definition",
        title="Priority graph",
        status="accepted",
        domain=["graph-theory"],
        tags=["priority"],
    )
    _write_artifact(
        tmp_path,
        "kb/draft/claims/draft.yaml",
        artifact_id="claim.fixture.draft-priority",
        title="Priority graph",
        status="draft",
        domain=["graph-theory"],
        tags=["priority"],
    )
    _write_issue(
        tmp_path,
        issue_id="issue.fixture.accepted-priority",
        related_artifacts=[
            "definition.fixture.accepted-priority",
            "claim.fixture.draft-priority",
        ],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "priority graph",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.fixture.accepted-priority",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["cards"][0]["card"]["id"] == (
        "definition.fixture.accepted-priority"
    )
    assert payload["cards"][0]["score_breakdown"]["quality_prior"] > (
        payload["cards"][1]["score_breakdown"]["quality_prior"]
    )


def test_memory_search_finds_failure_log_directions_by_keyword(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/draft/claims/failure-memory.yaml",
        artifact_id="claim.fixture.failure-memory-search",
        title="Failure memory draft",
        status="draft",
        domain=["graph-theory"],
        tags=["failure-memory"],
        failure_log=[
            _failure_log_entry(
                direction="Search for a triangle-free gadget counterexample",
                failed_because="The candidate gadget still contains a triangle.",
            )
        ],
    )
    _write_issue(
        tmp_path,
        issue_id="issue.fixture.failure-memory-search",
        related_artifacts=["claim.fixture.failure-memory-search"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "triangle-free gadget",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.fixture.failure-memory-search",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert [hit["card"]["id"] for hit in payload["cards"]] == [
        "claim.fixture.failure-memory-search"
    ]
    hit = payload["cards"][0]
    assert hit["card"]["failure_count"] == 1
    assert hit["card"]["recent_failure_directions"] == [
        "Search for a triangle-free gadget counterexample"
    ]
    assert hit["card"]["trust_score"] == 0.1
    assert hit["score_breakdown"]["quality_prior"] == 0.1
    assert any("failure memory match" in reason for reason in hit["why_relevant"])
    assert any(
        "failure memory is not proof" in warning
        for warning in payload["audit"]["warnings"]
    )


def test_memory_search_failure_log_does_not_change_accepted_quality_prior(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/failure-memory.yaml",
        artifact_id="claim.fixture.accepted-failure-memory",
        title="Accepted claim with failed attempts",
        status="accepted",
        domain=["graph-theory"],
        tags=["accepted"],
        failure_log=[
            _failure_log_entry(
                direction="Try a separator induction on the bad component",
                failed_because="The induction hypothesis was too weak.",
            )
        ],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "separator induction",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    hit = payload["cards"][0]
    assert hit["card"]["id"] == "claim.fixture.accepted-failure-memory"
    assert hit["card"]["failure_count"] == 1
    assert hit["card"]["trust_score"] == 1.0
    assert hit["score_breakdown"]["quality_prior"] == 1.0
    assert any("failure memory match" in reason for reason in hit["why_relevant"])


def test_memory_search_refuted_artifacts_require_explicit_inclusion(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/refuted.yaml",
        artifact_id="claim.fixture.refuted-target",
        title="Refuted target",
        status="refuted",
        domain=["graph-theory"],
        tags=["target"],
    )

    default_result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "refuted target",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    include_result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "refuted target",
            "--repo-root",
            str(tmp_path),
            "--include-refuted",
            "--json",
        ],
    )

    assert default_result.exit_code == 0, default_result.output
    default_payload = json.loads(default_result.output)
    assert default_payload["cards"] == []
    assert default_payload["audit"]["excluded"] == [
        {
            "artifact_id": "claim.fixture.refuted-target",
            "reason": (
                "status excluded: refuted not in "
                "accepted,human_reviewed,machine_checked,locally_tested"
            ),
        }
    ]

    assert include_result.exit_code == 0, include_result.output
    include_payload = json.loads(include_result.output)
    assert [hit["card"]["id"] for hit in include_payload["cards"]] == [
        "claim.fixture.refuted-target"
    ]
    assert include_payload["cards"][0]["score_breakdown"]["penalty"] > 0


def test_memory_search_private_seed_cannot_influence_public_default_ranking(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/alpha.yaml",
        artifact_id="definition.fixture.public-alpha",
        artifact_type="definition",
        title="Target policy alpha",
        status="accepted",
        domain=["graph-theory"],
        tags=["target", "policy"],
    )
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/beta.yaml",
        artifact_id="definition.fixture.public-beta",
        artifact_type="definition",
        title="Target policy beta",
        status="accepted",
        domain=["graph-theory"],
        tags=["target", "policy"],
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private-seed.yaml",
        artifact_id="claim.fixture.private-seed",
        title="Private seed",
        status="draft",
        domain=["graph-theory"],
        tags=["private"],
        depends_on=["definition.fixture.public-beta"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "target policy",
            "--repo-root",
            str(tmp_path),
            "--seed-artifact",
            "claim.fixture.private-seed",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert [hit["card"]["id"] for hit in payload["cards"]] == [
        "definition.fixture.public-alpha",
        "definition.fixture.public-beta",
    ]
    assert "claim.fixture.private-seed" not in {
        hit["card"]["id"] for hit in payload["cards"]
    }
    by_id = {hit["card"]["id"]: hit for hit in payload["cards"]}
    assert by_id["definition.fixture.public-beta"]["score_breakdown"][
        "personalized_pagerank"
    ] == 0
    assert any(
        "explicit seed artifact ignored because artifact is outside current "
        "scope/status filters: claim.fixture.private-seed"
        == warning
        for warning in payload["audit"]["warnings"]
    )
    assert any(
        "private scope exclusions" in warning
        for warning in payload["audit"]["warnings"]
    )


def test_memory_search_default_ranking_ignores_unrequested_issue_context(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/alpha.yaml",
        artifact_id="definition.fixture.unrequested-alpha",
        artifact_type="definition",
        title="Target policy alpha",
        status="accepted",
        domain=["graph-theory"],
        tags=["target", "policy"],
    )
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/beta.yaml",
        artifact_id="definition.fixture.unrequested-beta",
        artifact_type="definition",
        title="Target policy beta",
        status="accepted",
        domain=["graph-theory"],
        tags=["target", "policy"],
    )
    issue_id = "issue.fixture.unrequested-context"
    _write_issue(
        tmp_path,
        issue_id=issue_id,
        related_artifacts=["definition.fixture.unrequested-beta"],
    )
    task_id = "task.issue.fixture.unrequested-context.reasoner"
    _write_task(tmp_path, task_id=task_id, issue_id=issue_id)
    _write_task_run(
        tmp_path,
        task_id=task_id,
        run_id="run.r20260601.t000000z",
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "target policy",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert [hit["card"]["id"] for hit in payload["cards"]] == [
        "definition.fixture.unrequested-alpha",
        "definition.fixture.unrequested-beta",
    ]
    by_id = {hit["card"]["id"]: hit for hit in payload["cards"]}
    assert by_id["definition.fixture.unrequested-alpha"]["score_breakdown"][
        "global_pagerank"
    ] == by_id["definition.fixture.unrequested-beta"]["score_breakdown"][
        "global_pagerank"
    ]
    assert by_id["definition.fixture.unrequested-beta"]["score_breakdown"][
        "freshness"
    ] == 0


def test_memory_search_explain_prints_full_score_breakdown(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "graph",
            "--repo-root",
            str(tmp_path),
            "--explain",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "retrieval_hybrid=" in result.output
    assert "personalized_pagerank=" in result.output
    assert "global_pagerank=" in result.output
    assert "quality_prior=" in result.output
    assert "freshness=" in result.output
    assert "penalty=" in result.output


def test_memory_search_score_formula_is_configurable(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/lexical.yaml",
        artifact_id="definition.fixture.lexical",
        artifact_type="definition",
        title="Target lexical",
        status="accepted",
        domain=["logic"],
        tags=["target"],
    )
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/pinned.yaml",
        artifact_id="definition.fixture.configurable-pinned",
        artifact_type="definition",
        title="Pinned seed",
        status="accepted",
        domain=["graph-theory"],
        tags=["seed"],
    )

    result = search_artifact_cards(
        RepoContext(tmp_path),
        query="target",
        pinned_artifacts=("definition.fixture.configurable-pinned",),
        score_weights=RetrievalScoreWeights(
            retrieval_hybrid=0.0,
            personalized_pagerank=1.0,
            global_pagerank=0.0,
            quality_prior=0.0,
            freshness=0.0,
        ),
    )

    assert [hit.card.id for hit in result.cards][:2] == [
        "definition.fixture.configurable-pinned",
        "definition.fixture.lexical",
    ]
    assert result.cards[0].score_breakdown.personalized_pagerank > 0
