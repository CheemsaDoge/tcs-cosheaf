from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.evals.context import (
    DEFAULT_CONTEXT_EVAL_CASES,
    ContextEvalCase,
    ContextEvalSuite,
    load_context_eval_suite,
    run_context_eval_suite,
)
from cosheaf.memory import RetrievalRole
from cosheaf.storage.repo import RepoContext

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "context-eval-workspace"',
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


def _write_context_docs(repo_root: Path) -> None:
    context_dir = repo_root / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    (context_dir / "PROJECT_STATE.md").write_text(
        "# Project State\n\nContext eval fixture state.\n",
        encoding="utf-8",
    )
    (context_dir / "INTERFACE_REGISTRY.md").write_text(
        "# Interface Registry\n\n- `cosheaf eval context`\n",
        encoding="utf-8",
    )


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    title: str,
    status: str,
    domain: list[str] | None = None,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
    statement: str = "Context eval fixture statement.",
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


def _issue_data(
    issue_id: str,
    *,
    related_artifacts: list[str],
    tags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Build context eval fixture",
        "status": "open",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Need bounded graph context for a public-only task.",
        "related_artifacts": related_artifacts,
        "tags": tags or ["graph"],
    }


def _write_context_eval_fixture(repo_root: Path) -> None:
    _write_workspace_config(repo_root)
    _write_context_docs(repo_root)
    _write_yaml(
        repo_root,
        "issues/open/issue.fixture.context-eval.yaml",
        _issue_data(
            "issue.fixture.context-eval",
            related_artifacts=[
                "definition.fixture.public-graph",
                "claim.fixture.private-graph",
            ],
        ),
    )
    _write_yaml(
        repo_root,
        "kb/public/accepted/definitions/public-graph.yaml",
        _artifact_data(
            "definition.fixture.public-graph",
            artifact_type="definition",
            title="Public graph definition",
            status="accepted",
            domain=["graph-theory"],
            tags=["graph"],
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/private-graph.yaml",
        _artifact_data(
            "claim.fixture.private-graph",
            title="Private graph attempt",
            status="draft",
            domain=["graph-theory"],
            tags=["graph", "private"],
            depends_on=["definition.fixture.public-graph"],
            statement="PRIVATE STATEMENT SHOULD NOT LEAK",
        ),
    )


def test_context_eval_metrics_cover_bounded_public_only_context(
    tmp_path: Path,
) -> None:
    _write_context_eval_fixture(tmp_path)
    suite = ContextEvalSuite(
        cases=[
            ContextEvalCase(
                id="case.context.public-only",
                issue_id="issue.fixture.context-eval",
                required_artifacts=["definition.fixture.public-graph"],
                public_only=True,
                max_cards=3,
                max_full_artifacts=0,
                max_token_estimate=1500,
            )
        ]
    )

    report = run_context_eval_suite(RepoContext(tmp_path), suite)

    assert report.passed is True
    assert report.metrics.max_cards == 1
    assert report.metrics.max_full_artifacts == 0
    assert report.metrics.private_leakage_count == 0
    assert report.metrics.required_artifact_hit == 1.0
    assert report.metrics.accepted_ratio == 1.0
    assert report.metrics.draft_ratio == 0.0
    assert report.cases[0].returned_artifacts == ["definition.fixture.public-graph"]
    assert report.cases[0].failures == []


def test_context_eval_reports_full_artifact_budget_failure(
    tmp_path: Path,
) -> None:
    _write_context_eval_fixture(tmp_path)
    suite = ContextEvalSuite(
        cases=[
            ContextEvalCase(
                id="case.context.full-artifact-over-budget",
                issue_id="issue.fixture.context-eval",
                required_artifacts=["definition.fixture.public-graph"],
                role=RetrievalRole.VERIFIER,
                max_cards=3,
                max_full_artifacts=1,
                max_allowed_full_artifacts=0,
                max_token_estimate=2500,
            )
        ]
    )

    report = run_context_eval_suite(RepoContext(tmp_path), suite)

    assert report.passed is False
    assert report.metrics.max_full_artifacts == 1
    assert report.cases[0].metrics.max_full_artifacts == 1
    assert report.cases[0].failures == [
        "max_full_artifacts 1 exceeds allowed 0",
        "private_leakage_count 1 exceeds allowed 0",
    ]


def test_context_eval_reports_known_failures_unless_allowed(
    tmp_path: Path,
) -> None:
    _write_context_eval_fixture(tmp_path)
    _write_yaml(
        tmp_path,
        "kb/public/refuted/claims/refuted-graph.yaml",
        _artifact_data(
            "claim.fixture.refuted-graph",
            title="Refuted graph approach",
            status="refuted",
            domain=["graph-theory"],
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "issues/open/issue.fixture.known-failure.yaml",
        _issue_data(
            "issue.fixture.known-failure",
            related_artifacts=[
                "definition.fixture.public-graph",
                "claim.fixture.refuted-graph",
            ],
        ),
    )
    suite = ContextEvalSuite(
        cases=[
            ContextEvalCase(
                id="case.context.known-failure",
                issue_id="issue.fixture.known-failure",
                required_artifacts=["definition.fixture.public-graph"],
                public_only=True,
                max_cards=3,
                max_full_artifacts=0,
                max_token_estimate=2000,
            )
        ]
    )

    report = run_context_eval_suite(RepoContext(tmp_path), suite)

    assert report.passed is False
    assert report.cases[0].failures == [
        "known_failure_count 1 exceeds allowed 0"
    ]


def test_default_context_eval_suite_covers_graph_and_sat_pilots() -> None:
    suite = load_context_eval_suite(ROOT / DEFAULT_CONTEXT_EVAL_CASES)
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.context.graph-toy",
        "case.context.sat-smt-gadget",
    }
    assert cases_by_id["case.context.graph-toy"].required_artifacts == [
        "construction.graph-toy.0001"
    ]
    assert cases_by_id["case.context.sat-smt-gadget"].required_artifacts == [
        "construction.sat-smt-gadget.0001"
    ]
    assert all(case.role is RetrievalRole.ORCHESTRATOR for case in cases_by_id.values())
    assert all(case.max_full_artifacts == 0 for case in cases_by_id.values())


def test_context_eval_cli_runs_deterministic_fixture(tmp_path: Path) -> None:
    _write_context_eval_fixture(tmp_path)
    cases_path = tmp_path / "evals" / "context" / "cases.yaml"
    cases_path.parent.mkdir(parents=True, exist_ok=True)
    cases_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "id": "case.context.public-only",
                        "issue_id": "issue.fixture.context-eval",
                        "required_artifacts": ["definition.fixture.public-graph"],
                            "public_only": True,
                            "max_cards": 3,
                            "max_full_artifacts": 0,
                            "max_token_estimate": 1500,
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    args = [
        "eval",
        "context",
        "--repo-root",
        str(tmp_path),
        "--cases",
        str(cases_path),
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
    assert payload["passed"] is True
    assert payload["metrics"]["max_cards"] == 1
    assert payload["metrics"]["max_full_artifacts"] == 0
    assert payload["metrics"]["private_leakage_count"] == 0
    assert payload["metrics"]["required_artifact_hit"] == 1.0
