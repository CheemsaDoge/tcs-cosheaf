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
