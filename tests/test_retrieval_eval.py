from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.evals.retrieval import (
    DEFAULT_RETRIEVAL_EVAL_CASES,
    RetrievalEvalCase,
    load_retrieval_eval_suite,
    score_retrieval_case,
)
from cosheaf.memory import (
    ArtifactCard,
    ArtifactCardStatus,
    ArtifactCardType,
    MemoryRootScope,
    RetrievalAudit,
    RetrievalResult,
    RetrievedArtifactCard,
    ScoreBreakdown,
)

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


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
        "tags": tags or [],
        "statement": statement,
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


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
                "title": "Retrieval eval issue",
                "status": "open",
                "created_at": "2026-06-01T00:00:00Z",
                "updated_at": "2026-06-01T00:00:00Z",
                "authors": ["tester"],
                "severity": "medium",
                "description": "Issue for retrieval eval fixtures.",
                "related_artifacts": related_artifacts,
                "tags": ["retrieval-eval"],
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
                'name = "retrieval-eval-workspace"',
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


def _retrieval_result_with_cards(
    cards: list[ArtifactCard],
) -> RetrievalResult:
    return RetrievalResult(
        request_id="retrieval.eval.fixture",
        generated_at=datetime(1970, 1, 1, tzinfo=UTC),
        index_fingerprint="sha256:fixture",
        cards=[
            RetrievedArtifactCard(
                card=card,
                score_breakdown=ScoreBreakdown(total=1.0),
                why_relevant=["fixture"],
            )
            for card in cards
        ],
        audit=RetrievalAudit(),
    )


def _card(
    artifact_id: str,
    *,
    status: ArtifactCardStatus,
    root_scope: MemoryRootScope,
) -> ArtifactCard:
    return ArtifactCard(
        id=artifact_id,
        path=f"fixtures/{artifact_id}.yaml",
        root_scope=root_scope,
        type=ArtifactCardType.CLAIM,
        status=status,
        title=artifact_id,
        summary=f"Fixture card for {artifact_id}.",
    )


def test_retrieval_eval_metrics_count_hits_forbidden_and_private_leakage() -> None:
    case = RetrievalEvalCase(
        id="case.fixture.metrics",
        query="graph separator",
        expected_relevant_artifacts=["claim.fixture.expected"],
        forbidden_artifacts=["claim.fixture.forbidden"],
        allowed_scope=[MemoryRootScope.PUBLIC],
    )
    result = _retrieval_result_with_cards(
        [
            _card(
                "claim.fixture.expected",
                status=ArtifactCardStatus.ACCEPTED,
                root_scope=MemoryRootScope.PUBLIC,
            ),
            _card(
                "claim.fixture.forbidden",
                status=ArtifactCardStatus.LOCALLY_TESTED,
                root_scope=MemoryRootScope.PRIVATE,
            ),
        ]
    )

    scored = score_retrieval_case(case, result, k=2)

    assert scored.hit_at_k == 1.0
    assert scored.forbidden_hit_count == 1
    assert scored.private_leakage_count == 1
    assert scored.accepted_priority_score == 1.0
    assert scored.returned_artifacts == [
        "claim.fixture.expected",
        "claim.fixture.forbidden",
    ]


def test_default_retrieval_eval_suite_covers_graph_and_sat_pilots() -> None:
    suite = load_retrieval_eval_suite(ROOT / DEFAULT_RETRIEVAL_EVAL_CASES)
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.retrieval.graph-toy",
        "case.retrieval.sat-smt-gadget",
    }
    assert cases_by_id[
        "case.retrieval.graph-toy"
    ].expected_relevant_artifacts == ["construction.graph-toy.0001"]
    assert cases_by_id["case.retrieval.graph-toy"].forbidden_artifacts == [
        "construction.sat-smt-gadget.0001"
    ]
    assert cases_by_id[
        "case.retrieval.sat-smt-gadget"
    ].expected_relevant_artifacts == ["construction.sat-smt-gadget.0001"]
    assert cases_by_id["case.retrieval.sat-smt-gadget"].forbidden_artifacts == [
        "construction.graph-toy.0001"
    ]


def test_retrieval_eval_cli_runs_small_deterministic_fixture(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph separator foundation",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph", "separator"],
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private.yaml",
        artifact_id="claim.fixture.private",
        title="Private graph separator attempt",
        status="locally_tested",
        domain=["graph-theory"],
        tags=["graph", "separator", "private"],
        depends_on=["definition.fixture.graph"],
    )
    _write_issue(
        tmp_path,
        issue_id="issue.fixture.retrieval-eval",
        related_artifacts=["definition.fixture.graph", "claim.fixture.private"],
    )
    cases_path = tmp_path / "evals" / "retrieval" / "cases.yaml"
    cases_path.parent.mkdir(parents=True, exist_ok=True)
    cases_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "id": "case.fixture.public-graph",
                        "query": "graph separator",
                        "issue_id": "issue.fixture.retrieval-eval",
                        "expected_relevant_artifacts": [
                            "definition.fixture.graph"
                        ],
                        "forbidden_artifacts": ["claim.fixture.private"],
                        "allowed_scope": ["public"],
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    args = [
        "eval",
        "retrieval",
        "--repo-root",
        str(tmp_path),
        "--cases",
        str(cases_path),
        "--k",
        "3",
        "--json",
    ]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert first.output == second.output

    payload = json.loads(first.output)
    assert payload["schema_version"] == 1
    assert payload["case_count"] == 1
    assert payload["metrics"] == {
        "hit@3": 1.0,
        "forbidden_hit_count": 0,
        "accepted_priority_score": 1.0,
        "private_leakage_count": 0,
    }
    assert payload["cases"][0]["id"] == "case.fixture.public-graph"
    assert payload["cases"][0]["hit@3"] == 1.0
    assert payload["cases"][0]["returned_artifacts"] == ["definition.fixture.graph"]
    assert "claim.fixture.private" not in payload["cases"][0]["returned_artifacts"]
    assert not (tmp_path / ".cosheaf" / "memory").exists()
