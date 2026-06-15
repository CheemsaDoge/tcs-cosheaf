from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.storage.repo import RepoContext
from cosheaf.strategy.models import STRATEGY_AUTHORITY_NOTICE
from cosheaf.strategy.planner import build_strategy_plan


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    status: str = "draft",
    title: str = "Fixture artifact",
    domain: list[str] | None = None,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
    failure_log: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": artifact_type,
        "title": title,
        "domain": domain or ["graph-theory"],
        "status": status,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": tags or [],
        "statement": "Fixture statement.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }
    if failure_log is not None:
        data["failure_log"] = failure_log
    return data


def _failure_log_entry() -> dict[str, Any]:
    return {
        "failure_id": "failure.fixture.separator-proof",
        "attempted_at": "2026-06-02T00:00:00Z",
        "recorded_by": "tester",
        "origin": "human",
        "attempt_kind": "proof_attempt",
        "target": "claim.fixture.target",
        "direction": "Try separator induction on the bad component",
        "summary": "Separator induction failed.",
        "failed_because": "The separator premise is unavailable.",
        "evidence_paths": [],
        "related_verifier_results": [],
        "related_counterexample_candidates": ["candidate.fixture.gadget"],
        "next_possible_directions": ["Try a bounded-width decomposition first."],
        "status": "open",
        "limitations": "Failure memory only; not proof or refutation.",
    }


def _write_issue(repo_root: Path) -> None:
    _write_yaml(
        repo_root,
        "issues/open/strategy.yaml",
        {
            "id": "issue.fixture.strategy",
            "type": "issue",
            "title": "Plan graph strategy",
            "status": "open",
            "created_at": "2026-06-01T00:00:00Z",
            "updated_at": "2026-06-15T12:00:00Z",
            "authors": ["tester"],
            "severity": "medium",
            "description": "Need graph strategy next steps.",
            "related_artifacts": ["claim.fixture.target"],
            "tags": ["strategy", "graph"],
        },
    )


def _write_checked_evidence(repo_root: Path) -> None:
    _write_yaml(
        repo_root,
        "reviews/evidence/checked-counterexamples/"
        "checked-counterexample.claim.fixture.target.candidate.fixture.gadget.yaml",
        {
            "schema_version": 1,
            "evidence_id": (
                "checked-counterexample.claim.fixture.target."
                "candidate.fixture.gadget"
            ),
            "target_artifact_id": "claim.fixture.target",
            "candidate_id": "candidate.fixture.gadget",
            "candidate_source": "failure_log",
            "check_method": "executable_check",
            "checked_result": "checked_does_not_refute",
            "verifier_evidence_ids": [],
            "review_record_paths": [],
            "evidence_paths": [".cosheaf/evidence/gadget-check.json"],
            "created_at": "2026-06-14T00:00:00Z",
            "checker": "fixture-checker",
            "limitations": [
                "Checked counterexample evidence is evidence for review only; "
                "it is not human review, accepted refutation, accepted status, "
                "or promotion authority."
            ],
        },
    )


def _write_research_run(repo_root: Path) -> None:
    run_id = "run.issue.fixture.strategy.r20260615.t120000z"
    run_path = repo_root / ".cosheaf" / "runs" / run_id / "run.json"
    run_path.parent.mkdir(parents=True, exist_ok=True)
    run_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": run_id,
                "issue_id": "issue.fixture.strategy",
                "operator_kind": "external",
                "operator_label": "tester",
                "status": "completed",
                "started_at": "2026-06-15T12:00:00Z",
                "ended_at": "2026-06-15T12:01:00Z",
                "stop_reason": "fixture completed",
                "base_commit": None,
                "head_commit": None,
                "dirty_state_note": None,
                "workspace_info_summary": None,
                "context_packs": [],
                "commands": [],
                "artifacts_read": ["claim.fixture.target"],
                "artifacts_touched": [],
                "controlled_write_outputs": [],
                "worker_bundle_paths": [],
                "verifier_evidence_paths": [],
                "checked_counterexample_evidence_paths": [],
                "failure_log_entries_added": [],
                "validation_reports": [],
                "gate_reports": [],
                "pr_references": [],
                "issue_references": [],
                "limitations": [
                    "Research run records are provenance for review only; they "
                    "are not proof, verifier pass, gate pass, human review, "
                    "accepted status, or promotion authority."
                ],
                "operator_notes": [],
                "authority_notice": (
                    "Research run records are provenance for review only; they "
                    "are not proof, verifier pass, gate pass, human review, "
                    "accepted status, or promotion authority."
                ),
                "accepted_write_performed": False,
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_strategy_fixture(repo_root: Path) -> None:
    _write_issue(repo_root)
    _write_yaml(
        repo_root,
        "kb/draft/claims/target.yaml",
        _artifact_data(
            "claim.fixture.target",
            title="Target graph claim",
            depends_on=["definition.fixture.graph"],
            failure_log=[_failure_log_entry()],
        ),
    )
    _write_yaml(
        repo_root,
        "kb/accepted/definitions/graph.yaml",
        _artifact_data(
            "definition.fixture.graph",
            artifact_type="definition",
            status="accepted",
            title="Graph",
        ),
    )
    _write_checked_evidence(repo_root)
    _write_research_run(repo_root)


def test_strategy_planner_builds_issue_task_graph_with_boundaries(
    tmp_path: Path,
) -> None:
    _write_strategy_fixture(tmp_path)

    result = build_strategy_plan(RepoContext(tmp_path), "issue.fixture.strategy")
    plan = result.plan

    assert plan.plan_id == "strategy.issue.fixture.strategy.plan"
    assert plan.authority_notice == STRATEGY_AUTHORITY_NOTICE
    assert plan.accepted_write_performed is False
    assert plan.problem.target_artifacts == ("claim.fixture.target",)
    assert plan.problem.domains == ("graph-theory",)
    assert plan.problem.tags == ("graph", "strategy")
    artifact_nodes = {
        node.node_id: node
        for node in plan.graph.nodes
        if node.node_id.startswith("artifact.")
    }
    assert "artifact.claim.fixture.target" in artifact_nodes
    assert "artifact.definition.fixture.graph" in artifact_nodes
    assert artifact_nodes["artifact.claim.fixture.target"].scope == "workspace"
    assert artifact_nodes["artifact.definition.fixture.graph"].scope == "workspace"

    all_nodes = {node.node_id: node for node in plan.graph.nodes}
    assert all_nodes["task.context-build"].command == (
        "cosheaf",
        "context",
        "build",
        "issue.fixture.strategy",
    )
    assert all_nodes["task.validate"].command == ("cosheaf", "validate")
    assert all_nodes["task.gate"].command == ("cosheaf", "gate", "run")
    assert "failure.fixture.separator-proof" in (
        all_nodes["task.review-failures"].related_failure_log_entries
    )
    assert "candidate.fixture.gadget" in (
        all_nodes["task.counterexample-review"].related_candidate_counterexamples
    )
    assert "checked-counterexample.claim.fixture.target.candidate.fixture.gadget" in (
        all_nodes[
            "task.counterexample-review"
        ].related_checked_counterexample_evidence
    )
    assert "run.issue.fixture.strategy.r20260615.t120000z" in (
        all_nodes["task.review-runs"].related_research_run_ids
    )
    assert plan.to_json() == plan.to_json()


def test_failed_directions_influence_next_step_ranking(tmp_path: Path) -> None:
    _write_strategy_fixture(tmp_path)

    plan = build_strategy_plan(RepoContext(tmp_path), "issue.fixture.strategy").plan

    ranked_ids = [step.node_id for step in plan.next_steps]
    assert ranked_ids[:3] == ["task.context-build", "task.validate", "task.gate"]
    assert ranked_ids.index("task.review-failures") < ranked_ids.index(
        "task.proof-attempt"
    )
    failed_step = next(
        step for step in plan.next_steps if step.node_id == "task.proof-attempt"
    )
    assert any("known failed direction" in reason for reason in failed_step.reasons)


def test_candidate_and_checked_evidence_labels_are_preserved(tmp_path: Path) -> None:
    _write_strategy_fixture(tmp_path)

    plan = build_strategy_plan(RepoContext(tmp_path), "issue.fixture.strategy").plan
    node = next(
        node
        for node in plan.graph.nodes
        if node.node_id == "task.counterexample-review"
    )

    assert node.related_candidate_counterexamples == ("candidate.fixture.gadget",)
    assert node.related_checked_counterexample_evidence == (
        "checked-counterexample.claim.fixture.target.candidate.fixture.gadget",
    )
    assert "candidate only" in " ".join(node.notes)
    assert "checked evidence only" in " ".join(node.notes)
