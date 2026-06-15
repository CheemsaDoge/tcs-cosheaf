from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from cosheaf.strategy.models import (
    STRATEGY_AUTHORITY_NOTICE,
    StrategyPlan,
    StrategyProblem,
    StrategyTaskGraph,
    StrategyTaskNode,
    StrategyTaskNodeKind,
    StrategyTaskScope,
    StrategyTaskStatus,
)

ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)


def _node(node_id: str, *, command: tuple[str, ...] = ()) -> StrategyTaskNode:
    return StrategyTaskNode(
        node_id=node_id,
        kind=StrategyTaskNodeKind.VALIDATION,
        title=f"Run {node_id}",
        status=StrategyTaskStatus.READY,
        scope=StrategyTaskScope.WORKSPACE,
        expected_evidence_kinds=("command_result",),
        command=command,
        write_paths=(),
    )


def test_strategy_plan_serializes_deterministically_with_authority_notice() -> None:
    graph = StrategyTaskGraph(
        nodes=(
            _node(
                "task.context",
                command=("cosheaf", "context", "build", "issue.fixture"),
            ),
            _node("task.validate", command=("cosheaf", "validate")),
        ),
        edges=(),
    )
    plan = StrategyPlan(
        plan_id="strategy.issue.fixture.plan",
        issue_id="issue.fixture",
        created_at=CREATED_AT,
        problem=StrategyProblem(
            issue_id="issue.fixture",
            title="Fixture problem",
            domains=("graph-theory",),
            tags=("strategy",),
            target_artifacts=("claim.fixture.target",),
            known_constraints=("Do not write accepted knowledge.",),
        ),
        graph=graph,
        next_steps=(),
    )

    payload = plan.to_dict()

    assert list(payload) == [
        "schema_version",
        "plan_id",
        "issue_id",
        "created_at",
        "problem",
        "graph",
        "next_steps",
        "authority_notice",
        "accepted_write_performed",
    ]
    assert payload["authority_notice"] == STRATEGY_AUTHORITY_NOTICE
    assert payload["accepted_write_performed"] is False
    assert plan.created_at.tzinfo is not None
    assert plan.to_json() == plan.to_json()


def test_strategy_graph_rejects_duplicate_node_ids() -> None:
    with pytest.raises(ValidationError, match="duplicate task node id"):
        StrategyTaskGraph(nodes=(_node("task.same"), _node("task.same")), edges=())


@pytest.mark.parametrize(
    "path",
    [
        "../outside.json",
        "C:/secret/plan.json",
        "/tmp/plan.json",
    ],
)
def test_strategy_node_rejects_non_repository_paths(path: str) -> None:
    with pytest.raises(ValidationError, match="repository-local"):
        StrategyTaskNode(
            node_id="task.path",
            kind=StrategyTaskNodeKind.REVIEW,
            title="Bad path",
            status=StrategyTaskStatus.READY,
            scope=StrategyTaskScope.PRIVATE,
            expected_evidence_kinds=("review_context",),
            input_paths=(path,),
        )


def test_strategy_node_rejects_accepted_write_authority() -> None:
    with pytest.raises(ValidationError, match="accepted KB"):
        StrategyTaskNode(
            node_id="task.write",
            kind=StrategyTaskNodeKind.REVIEW,
            title="Unsafe write",
            status=StrategyTaskStatus.READY,
            scope=StrategyTaskScope.PRIVATE,
            expected_evidence_kinds=("review_context",),
            write_paths=("kb/accepted/claims/unsafe.yaml",),
        )


def test_strategy_schema_files_define_v1_contract() -> None:
    strategy_schema = json.loads(
        (ROOT / "schemas" / "research_strategy.schema.json").read_text(
            encoding="utf-8"
        )
    )
    graph_schema = json.loads(
        (ROOT / "schemas" / "research_task_graph.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert strategy_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert strategy_schema["title"] == "TCS-Cosheaf Research Strategy Plan"
    assert strategy_schema["additionalProperties"] is False
    assert strategy_schema["properties"]["schema_version"]["const"] == 1
    assert strategy_schema["properties"]["authority_notice"]["const"] == (
        STRATEGY_AUTHORITY_NOTICE
    )
    assert "problem" in strategy_schema["required"]
    assert graph_schema["title"] == "TCS-Cosheaf Research Task Graph"
    assert graph_schema["properties"]["nodes"]["items"]["required"][:4] == [
        "node_id",
        "kind",
        "title",
        "status",
    ]
