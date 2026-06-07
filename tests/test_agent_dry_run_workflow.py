from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.agent.orchestrator_runner import (
    OrchestratorLocalRunConfig,
    OrchestratorLocalRunner,
)
from cosheaf.cli import app
from cosheaf.storage.repo import RepoContext

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_demo_repo(repo_root: Path) -> None:
    _write_yaml(
        repo_root,
        "issues/open/issue.agent-dry-run.demo.yaml",
        {
            "id": "issue.agent-dry-run.demo",
            "type": "issue",
            "title": "Demonstrate agent dry-run workflow",
            "status": "open",
            "created_at": "2026-06-07T00:00:00Z",
            "updated_at": "2026-06-07T00:00:00Z",
            "authors": ["tester"],
            "severity": "medium",
            "description": (
                "Show that fake local reasoner and verifier workers produce "
                "reviewable bundles without writing accepted knowledge."
            ),
            "related_artifacts": ["claim.agent-dry-run.demo"],
            "tags": ["agent-dry-run", "local-only"],
        },
    )
    _write_yaml(
        repo_root,
        "kb/draft/claims/claim.agent-dry-run.demo.yaml",
        {
            "id": "claim.agent-dry-run.demo",
            "type": "claim",
            "title": "Agent dry-run demo claim",
            "domain": ["testing"],
            "status": "draft",
            "created_at": "2026-06-07T00:00:00Z",
            "updated_at": "2026-06-07T00:00:00Z",
            "authors": ["tester"],
            "depends_on": [],
            "supersedes": [],
            "tags": ["agent-dry-run"],
            "statement": "A local dry-run can produce proposal bundles only.",
            "evidence": [],
            "review": {
                "state": "requested",
                "notes": "Fixture remains draft and unreviewed.",
            },
            "risk": {"level": "low", "notes": "Fixture risk only."},
        },
    )


def test_agent_dry_run_demo_issue_example_is_present_and_draft_only() -> None:
    issue = yaml.safe_load(
        (ROOT / "examples/issues/issue.agent-dry-run.demo.yaml").read_text(
            encoding="utf-8"
        )
    )

    assert issue["id"] == "issue.agent-dry-run.demo"
    assert issue["status"] == "open"
    assert "claim.agent-dry-run.demo" in issue["related_artifacts"]
    claim = yaml.safe_load(
        (ROOT / "examples/claims/claim.agent-dry-run.demo.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert claim["id"] == "claim.agent-dry-run.demo"
    assert claim["status"] == "draft"
    assert claim["review"]["state"] == "requested"
    assert not (ROOT / "examples" / "kb" / "accepted").exists()


def test_agent_dry_run_workflow_uses_fake_reasoner_and_verifier_only(
    tmp_path: Path,
) -> None:
    _write_demo_repo(tmp_path)

    result = OrchestratorLocalRunner(RepoContext(tmp_path)).run_issue(
        OrchestratorLocalRunConfig(
            issue_id="issue.agent-dry-run.demo",
            run_id="run.issue.agent-dry-run.demo.0001",
        )
    )

    assert result.run.state.value == "completed"
    assert not (tmp_path / "kb" / "accepted").exists()
    assert not list(tmp_path.glob("reviews/human/**/*.yaml"))
    assert not list(tmp_path.glob("reviews/gatekeeper/**/*.yaml"))

    bundle_records = [
        yaml.safe_load((tmp_path / call.bundle_path).read_text(encoding="utf-8"))
        for call in result.run.worker_calls
        if call.bundle_path is not None
    ]
    by_role = {record["worker_role"]: record for record in bundle_records}

    assert by_role["reasoner"]["bundle_id"].endswith(".reasoner-draft")
    assert by_role["reasoner"]["confidence"] == "low"
    assert "needs_human_review" in by_role["reasoner"]["risk_flags"]
    assert any(
        artifact["path"].startswith(
            ".cosheaf/orchestrator/issue.agent-dry-run.demo/"
        )
        for artifact in by_role["reasoner"]["proposed_artifacts"]
    )

    assert by_role["verifier"]["bundle_id"].endswith(".verifier-check")
    assert "not_machine_checked" in by_role["verifier"]["risk_flags"]
    assert any(
        "No gate, Lean, SAT, SMT, or promotion result was produced." == failure
        for failure in by_role["verifier"]["failures_or_counterexamples"]
    )

    for record in bundle_records:
        assert record["worker_role"] in {"orchestrator", "reasoner", "verifier"}
        assert record["confidence"] == "low"
        assert "dry_run_only" in record["risk_flags"]
        assert "accepted" not in yaml.safe_dump(record).lower()
        for artifact in record["proposed_artifacts"]:
            assert artifact["path"].startswith(".cosheaf/orchestrator/")
            assert "/proposals/" in artifact["path"]
            assert "kb/accepted" not in artifact["path"]

    for call in result.run.worker_calls:
        assert call.command[1].endswith("dry_run_workers.py")
        assert "--worker-role" in call.command


def test_agent_dry_run_cli_smoke_uses_demo_issue(tmp_path: Path) -> None:
    _write_demo_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "orchestrator",
            "run",
            "--issue",
            "issue.agent-dry-run.demo",
            "--dry-run",
            "--local-only",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "state: completed" in result.output
    assert "hosted_llm: not used" in result.output
    assert "accepted_writes: not performed" in result.output
