from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.strategy.models import (
    STRATEGY_AUTHORITY_NOTICE,
    StrategyTaskNode,
    StrategyTaskNodeKind,
    StrategyTaskScope,
    StrategyTaskStatus,
)

runner = CliRunner()


def _write_json(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n")
    return path


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _assert_json(output: str) -> dict[str, Any]:
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def _valid_plan_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": 1,
        "plan_id": "strategy.issue.security.strategy.plan",
        "issue_id": "issue.security.strategy",
        "created_at": "2026-06-15T00:00:00Z",
        "problem": {
            "issue_id": "issue.security.strategy",
            "title": "Security strategy fixture",
        },
        "graph": {
            "nodes": [
                {
                    "node_id": "task.context-build",
                    "kind": "retrieval_context",
                    "title": "Build context",
                    "status": "ready",
                    "scope": "workspace",
                }
            ],
            "edges": [],
        },
        "next_steps": [],
        "authority_notice": STRATEGY_AUTHORITY_NOTICE,
        "accepted_write_performed": False,
    }
    data.update(overrides)
    return data


def test_strategy_plan_load_rejects_authority_and_hidden_reasoning_fields(
    tmp_path: Path,
) -> None:
    plan_id = "strategy.issue.security.strategy.plan"
    for field, value in {
        "human_reviewed": True,
        "review_state": "human_reviewed",
        "accepted": True,
        "artifact_status": "accepted",
        "promote": True,
        "chain_of_thought": "hidden reasoning should not be stored",
    }.items():
        _write_json(
            tmp_path,
            f".cosheaf/strategy/{plan_id}/strategy.json",
            _valid_plan_data(**{field: value}),
        )

        result = runner.invoke(
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

        assert result.exit_code == 1
        payload = _assert_json(result.output)
        assert payload["code"] == "strategy_plan_validation_failed"
        assert field in payload["message"]
        assert not (tmp_path / "kb" / "accepted").exists()


def test_strategy_task_nodes_reject_unsafe_paths_and_secret_summaries() -> None:
    for path_value in (
        "../outside.txt",
        "kb/accepted/claims/unsafe.yaml",
        str(Path("C:/outside/unsafe.txt")),
    ):
        with pytest.raises(ValidationError):
            StrategyTaskNode(
                node_id="task.security",
                kind=StrategyTaskNodeKind.REVIEW_DECISION,
                title="Security node",
                status=StrategyTaskStatus.READY,
                scope=StrategyTaskScope.WORKSPACE,
                write_paths=(path_value,),
            )

    with pytest.raises(ValidationError):
        StrategyTaskNode(
            node_id="task.security",
            kind=StrategyTaskNodeKind.REVIEW_DECISION,
            title="Security node",
            status=StrategyTaskStatus.READY,
            scope=StrategyTaskScope.WORKSPACE,
            notes=("provider token sk-secret-value",),
        )


def test_strategy_plan_from_context_rejects_non_repo_local_paths(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "issues/open/security-strategy.yaml",
        {
            "id": "issue.security.strategy",
            "type": "issue",
            "title": "Security strategy issue",
            "status": "open",
            "created_at": "2026-06-15T00:00:00Z",
            "updated_at": "2026-06-15T00:00:00Z",
            "authors": ["security-test"],
            "severity": "high",
            "description": "Fixture issue.",
            "related_artifacts": [],
            "tags": ["security"],
        },
    )
    for context_path in (tmp_path.parent / "outside-context", Path("../outside")):
        result = runner.invoke(
            app,
            [
                "strategy",
                "plan",
                "--issue",
                "issue.security.strategy",
                "--from-context",
                str(context_path),
                "--repo-root",
                str(tmp_path),
                "--json",
            ],
        )

        assert result.exit_code == 1
        payload = _assert_json(result.output)
        assert payload["code"] in {
            "invalid_strategy_path",
            "strategy_validation_failed",
            "strategy_failed",
        }
        assert "repository-local" in payload["message"]
        assert not (tmp_path / "kb" / "accepted").exists()
