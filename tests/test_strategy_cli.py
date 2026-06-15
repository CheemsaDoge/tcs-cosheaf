from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.strategy.models import STRATEGY_AUTHORITY_NOTICE

runner = CliRunner()


def _assert_json(output: str) -> dict[str, Any]:
    assert "\x1b[" not in output
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _artifact_data(artifact_id: str, *, status: str = "draft") -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "CLI strategy target",
        "domain": ["graph-theory"],
        "status": status,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["strategy"],
        "statement": "Fixture statement.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _write_fixture(repo_root: Path) -> None:
    _write_yaml(
        repo_root,
        "issues/open/strategy-cli.yaml",
        {
            "id": "issue.fixture.strategy-cli",
            "type": "issue",
            "title": "CLI strategy issue",
            "status": "open",
            "created_at": "2026-06-01T00:00:00Z",
            "updated_at": "2026-06-15T12:00:00Z",
            "authors": ["tester"],
            "severity": "medium",
            "description": "Need CLI strategy plan.",
            "related_artifacts": ["claim.fixture.strategy-cli"],
            "tags": ["strategy"],
        },
    )
    _write_yaml(
        repo_root,
        "kb/draft/claims/strategy-cli.yaml",
        _artifact_data("claim.fixture.strategy-cli"),
    )


def _write_research_run(repo_root: Path, run_id: str) -> None:
    _write_json(
        repo_root,
        f".cosheaf/runs/{run_id}/run.json",
        {
            "schema_version": 1,
            "run_id": run_id,
            "issue_id": "issue.fixture.strategy-cli",
            "operator_kind": "external",
            "operator_label": "Codex CLI",
            "status": "completed",
            "started_at": "2026-06-15T12:01:00Z",
            "ended_at": "2026-06-15T12:05:00Z",
            "stop_reason": "fixture run completed",
            "context_packs": [
                {
                    "kind": "context_pack",
                    "path": "context/TASKS/issue.fixture.strategy-cli/CONTEXT.md",
                    "status": "completed",
                    "summary": "context pack built",
                }
            ],
            "commands": [
                {
                    "argv": ["cosheaf", "validate"],
                    "cwd": ".",
                    "started_at": "2026-06-15T12:02:00Z",
                    "ended_at": "2026-06-15T12:03:00Z",
                    "exit_code": 0,
                    "status": "completed",
                },
                {
                    "argv": ["cosheaf", "gate", "run"],
                    "cwd": ".",
                    "started_at": "2026-06-15T12:03:00Z",
                    "status": "skipped",
                    "skipped_reason": (
                        "Skipped research-run steps are not pass evidence."
                    ),
                },
            ],
            "artifacts_read": ["claim.fixture.strategy-cli"],
            "artifacts_touched": ["claim.fixture.strategy-cli"],
            "checked_counterexample_evidence_paths": [
                {
                    "kind": "checked_counterexample_evidence",
                    "path": "reviews/evidence/checked-counterexamples/fixture.yaml",
                    "identifier": "checked-counterexample.fixture",
                    "status": "completed",
                    "summary": "checked evidence staged for review",
                }
            ],
            "validation_reports": [
                {
                    "kind": "validation_report",
                    "path": ".cosheaf/reports/validation.json",
                    "status": "completed",
                    "summary": "validation report",
                }
            ],
            "gate_reports": [
                {
                    "kind": "gate_report",
                    "path": ".cosheaf/reports/gate.json",
                    "status": "skipped",
                    "summary": "Skipped research-run steps are not pass evidence.",
                }
            ],
        },
    )


def _write_json(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n")


def test_strategy_cli_plan_show_graph_next_json(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    plan_id = "strategy.issue.fixture.strategy-cli.plan"

    plan = runner.invoke(
        app,
        [
            "strategy",
            "plan",
            "--issue",
            "issue.fixture.strategy-cli",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert plan.exit_code == 0, plan.output
    plan_payload = _assert_json(plan.output)
    assert plan_payload["kind"] == "strategy_plan"
    assert plan_payload["plan_id"] == plan_id
    assert plan_payload["path"] == f".cosheaf/strategy/{plan_id}/strategy.json"
    assert plan_payload["accepted_write_performed"] is False
    assert plan_payload["authority_notice"] == STRATEGY_AUTHORITY_NOTICE
    assert (tmp_path / ".cosheaf" / "strategy" / plan_id / "strategy.json").is_file()

    show = runner.invoke(
        app,
        [
            "strategy",
            "show",
            plan_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert show.exit_code == 0, show.output
    show_payload = _assert_json(show.output)
    assert show_payload["plan"]["plan_id"] == plan_id
    assert show_payload["plan"]["authority_notice"] == STRATEGY_AUTHORITY_NOTICE

    graph = runner.invoke(
        app,
        [
            "strategy",
            "graph",
            plan_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert graph.exit_code == 0, graph.output
    graph_payload = _assert_json(graph.output)
    assert graph_payload["kind"] == "strategy_task_graph"
    assert any(
        node["node_id"] == "task.context-build"
        for node in graph_payload["graph"]["nodes"]
    )

    next_step = runner.invoke(
        app,
        [
            "strategy",
            "next",
            plan_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert next_step.exit_code == 0, next_step.output
    next_payload = _assert_json(next_step.output)
    assert next_payload["kind"] == "strategy_next_steps"
    assert [step["node_id"] for step in next_payload["next_steps"][:3]] == [
        "task.context-build",
        "task.validate",
        "task.gate",
    ]

    second_plan = runner.invoke(
        app,
        [
            "strategy",
            "plan",
            "--issue",
            "issue.fixture.strategy-cli",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert second_plan.exit_code == 0, second_plan.output
    assert second_plan.output == plan.output
    assert not (tmp_path / "kb" / "accepted").exists()


def test_strategy_cli_reports_missing_plan_as_json_error(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "strategy",
            "show",
            "strategy.issue.missing.plan",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "strategy_plan_not_found"


def test_strategy_cli_plan_from_context_records_context_reference(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    context_result = runner.invoke(
        app,
        [
            "context",
            "build",
            "issue.fixture.strategy-cli",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert context_result.exit_code == 0, context_result.output
    context_dir = tmp_path / "context" / "TASKS" / "issue.fixture.strategy-cli"

    result = runner.invoke(
        app,
        [
            "strategy",
            "plan",
            "--issue",
            "issue.fixture.strategy-cli",
            "--from-context",
            str(context_dir),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    context_node = next(
        node
        for node in payload["plan"]["graph"]["nodes"]
        if node["node_id"] == "task.context-build"
    )
    assert context_node["references"] == [
        {
            "kind": "context_pack",
            "identifier": "issue.fixture.strategy-cli",
            "path": "context/TASKS/issue.fixture.strategy-cli",
            "status": "completed",
            "summary": "strategy plan was generated from this context pack",
        }
    ]


def test_strategy_cli_update_from_run_preserves_skipped_as_non_pass(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    plan_id = "strategy.issue.fixture.strategy-cli.plan"
    plan = runner.invoke(
        app,
        [
            "strategy",
            "plan",
            "--issue",
            "issue.fixture.strategy-cli",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert plan.exit_code == 0, plan.output
    run_id = "run.issue.fixture.strategy-cli.0001"
    _write_research_run(tmp_path, run_id)

    result = runner.invoke(
        app,
        [
            "strategy",
            "update-from-run",
            "--plan",
            plan_id,
            "--run",
            run_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    assert payload["kind"] == "strategy_plan_update"
    nodes = {node["node_id"]: node for node in payload["plan"]["graph"]["nodes"]}
    assert nodes["task.validate"]["status"] == "completed"
    assert nodes["task.gate"]["status"] == "skipped"
    assert nodes["task.gate"]["references"][0]["status"] == "skipped"
    assert "not pass evidence" in nodes["task.gate"]["references"][0]["summary"]
    assert nodes["artifact.claim.fixture.strategy-cli"]["status"] == "completed"
    assert run_id in nodes["task.review-runs"]["related_research_run_ids"]
    assert not (tmp_path / "kb" / "accepted").exists()


def test_strategy_cli_export_review_dry_run_and_write(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    plan_id = "strategy.issue.fixture.strategy-cli.plan"
    plan = runner.invoke(
        app,
        [
            "strategy",
            "plan",
            "--issue",
            "issue.fixture.strategy-cli",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert plan.exit_code == 0, plan.output

    dry_run = runner.invoke(
        app,
        [
            "strategy",
            "export-review",
            "--plan",
            plan_id,
            "--dry-run",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert dry_run.exit_code == 0, dry_run.output
    dry_payload = _assert_json(dry_run.output)
    assert dry_payload["dry_run"] is True
    assert dry_payload["written_paths"] == []
    assert not (tmp_path / "reviews" / "strategy" / f"{plan_id}.yaml").exists()

    export = runner.invoke(
        app,
        [
            "strategy",
            "export-review",
            "--plan",
            plan_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert export.exit_code == 0, export.output
    export_payload = _assert_json(export.output)
    assert export_payload["kind"] == "strategy_review_export"
    assert export_payload["written_paths"] == [f"reviews/strategy/{plan_id}.yaml"]
    exported = yaml.safe_load(
        (tmp_path / "reviews" / "strategy" / f"{plan_id}.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert exported["authority_notice"] == STRATEGY_AUTHORITY_NOTICE
    assert exported["accepted_write_performed"] is False
    assert not (tmp_path / "kb" / "accepted").exists()
