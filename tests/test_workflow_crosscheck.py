from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from typer.testing import CliRunner

from cosheaf.checkers.builtins import default_checker_registry
from cosheaf.checkers.models import CheckerInput, CheckerResult, CheckerStatus
from cosheaf.checkers.registry import CheckerExecution
from cosheaf.checkers.storage import store_checker_execution
from cosheaf.cli import app
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.crosscheck import (
    CROSSCHECK_AUTHORITY_NOTICE,
    build_crosscheck_report,
    build_gap_report,
    scan_crosscheck_report_text,
    workflow_crosscheck_markdown_path,
    workflow_crosscheck_path,
    workflow_gap_path,
)
from cosheaf.workflow.engine import (
    WorkflowStep,
    append_step,
    load_workflow,
    start_workflow,
    step_workflow,
    write_workflow,
)
from cosheaf.workflow.handoff import (
    build_workflow_handoff,
    workflow_handoff_id,
    workflow_handoff_path,
)

runner = CliRunner()


def _json(output: str) -> dict[str, Any]:
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _workflow_fixture(tmp_path: Path) -> str:
    context = RepoContext(tmp_path)
    workflow_id = "workflow.crosscheck.fixture"
    start_workflow(
        context,
        issue_id="issue.crosscheck.fixture",
        query="review candidate graph claim",
        workflow_id=workflow_id,
    )
    step_workflow(
        context,
        workflow_id,
        action_id="workspace.info",
        execute_local_action=False,
    )
    workflow = load_workflow(context, workflow_id)
    workflow = append_step(
        workflow,
        WorkflowStep(
            step_number=2,
            action="formal.check",
            status="skipped",
            output_refs={"action_status": "skipped"},
        ),
    )
    write_workflow(context, workflow)
    return workflow_id


def _store_checker(
    tmp_path: Path,
    *,
    workflow_id: str,
    checker_id: str,
    status: CheckerStatus,
) -> None:
    context = RepoContext(tmp_path)
    registry = default_checker_registry()
    spec = registry.get(checker_id)
    assert spec is not None
    now = datetime(2026, 6, 18, 0, 0, tzinfo=UTC)
    result = CheckerResult(
        checker_id=checker_id,
        checker_type=spec.checker_type,
        status=status,
        started_at=now,
        ended_at=now,
        message=f"{checker_id} fixture {status.value}",
        command=("python", "-m", "fixture"),
        cwd=str(tmp_path),
        input_paths=(f".cosheaf/workflows/{workflow_id}/workflow.json",),
        limitations=("fixture checker result",),
    )
    store_checker_execution(
        context,
        spec,
        CheckerInput(
            paths=(f".cosheaf/workflows/{workflow_id}/workflow.json",),
            text=workflow_id,
            payload={"workflow_id": workflow_id},
        ),
        CheckerExecution(result=result),
    )


def test_crosscheck_report_renders_matrix_and_never_accepts_checked_evidence(
    tmp_path: Path,
) -> None:
    workflow_id = _workflow_fixture(tmp_path)
    _store_checker(
        tmp_path,
        workflow_id=workflow_id,
        checker_id="schema_check",
        status=CheckerStatus.PASS,
    )
    _store_checker(
        tmp_path,
        workflow_id=workflow_id,
        checker_id="source_metadata_check",
        status=CheckerStatus.FAIL,
    )
    _store_checker(
        tmp_path,
        workflow_id=workflow_id,
        checker_id="lean_optional_check",
        status=CheckerStatus.SKIPPED,
    )
    _store_checker(
        tmp_path,
        workflow_id=workflow_id,
        checker_id="smt_optional_check",
        status=CheckerStatus.INCONCLUSIVE,
    )

    report = build_crosscheck_report(RepoContext(tmp_path), workflow_id)

    assert report.workflow_id == workflow_id
    assert report.authority_notice == CROSSCHECK_AUTHORITY_NOTICE
    assert report.checked_pass_is_accepted is False
    assert report.human_review_created is False
    assert report.accepted_status_created is False
    assert report.matrix.status_counts["checked-pass"] >= 1
    assert report.matrix.status_counts["checked-fail"] >= 1
    assert report.matrix.status_counts["inconclusive"] >= 2
    assert report.matrix.status_counts["unchecked"] >= 1
    assert (tmp_path / workflow_crosscheck_path(workflow_id)).is_file()
    assert (tmp_path / workflow_crosscheck_markdown_path(workflow_id)).is_file()
    markdown = (tmp_path / workflow_crosscheck_markdown_path(workflow_id)).read_text(
        encoding="utf-8"
    )
    assert "checked-pass is not accepted" in markdown
    assert "source_metadata_check" in markdown


def test_gap_report_detects_source_formalization_review_and_proof_gaps(
    tmp_path: Path,
) -> None:
    workflow_id = _workflow_fixture(tmp_path)
    _store_checker(
        tmp_path,
        workflow_id=workflow_id,
        checker_id="source_metadata_check",
        status=CheckerStatus.FAIL,
    )
    _store_checker(
        tmp_path,
        workflow_id=workflow_id,
        checker_id="lean_optional_check",
        status=CheckerStatus.SKIPPED,
    )

    gap_report = build_gap_report(RepoContext(tmp_path), workflow_id)

    gap_kinds = {gap.kind.value for gap in gap_report.gaps}
    assert "proof_gap" in gap_kinds
    assert "source_gap" in gap_kinds
    assert "formalization_gap" in gap_kinds
    assert "review_gap" in gap_kinds
    assert gap_report.gaps_are_defects is False
    assert (tmp_path / workflow_gap_path(workflow_id)).is_file()


def test_workflow_crosscheck_and_gap_cli_exports_review_context(
    tmp_path: Path,
) -> None:
    workflow_id = _workflow_fixture(tmp_path)

    crosscheck = runner.invoke(
        app,
        [
            "workflow",
            "cross-check",
            workflow_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert crosscheck.exit_code == 0, crosscheck.output
    crosscheck_payload = _json(crosscheck.output)
    assert crosscheck_payload["kind"] == "workflow_crosscheck_report"
    assert crosscheck_payload["accepted_status_created"] is False

    evidence = runner.invoke(
        app,
        [
            "workflow",
            "evidence-report",
            workflow_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert evidence.exit_code == 0, evidence.output
    evidence_payload = _json(evidence.output)
    assert evidence_payload["kind"] == "workflow_evidence_report"
    assert evidence_payload["crosscheck_report"]["workflow_id"] == workflow_id

    export_crosscheck = runner.invoke(
        app,
        [
            "workflow",
            "export-crosscheck",
            workflow_id,
            "--out",
            "reviews/workflow/crosscheck.fixture.md",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert export_crosscheck.exit_code == 0, export_crosscheck.output
    export_payload = _json(export_crosscheck.output)
    assert export_payload["target_path"] == "reviews/workflow/crosscheck.fixture.md"
    assert export_payload["written"] is True
    assert (tmp_path / "reviews/workflow/crosscheck.fixture.md").is_file()

    gap_list = runner.invoke(
        app,
        [
            "gap",
            "list",
            workflow_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert gap_list.exit_code == 0, gap_list.output
    gap_payload = _json(gap_list.output)
    assert gap_payload["kind"] == "workflow_gap_report"

    gap_export = runner.invoke(
        app,
        [
            "gap",
            "export",
            workflow_id,
            "--out",
            "reviews/workflow/gaps.fixture.json",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert gap_export.exit_code == 0, gap_export.output
    assert (tmp_path / "reviews/workflow/gaps.fixture.json").is_file()


def test_crosscheck_authority_scanner_catches_overclaim_in_report_text() -> None:
    findings = scan_crosscheck_report_text(
        "This report proves an accepted theorem and creates human review."
    )

    codes = {finding["code"] for finding in findings}
    assert "accepted_theorem_or_refutation" in codes
    assert "human_review_overclaim" in codes


def test_workflow_handoff_includes_gap_summary(tmp_path: Path) -> None:
    workflow_id = _workflow_fixture(tmp_path)
    result = build_workflow_handoff(RepoContext(tmp_path), workflow_id)
    handoff_id = workflow_handoff_id(workflow_id)

    assert result.relative_path == workflow_handoff_path(handoff_id)
    assert result.handoff.review_gaps
    gap_kinds = {gap["kind"] for gap in result.handoff.review_gaps}
    assert "source_gap" in gap_kinds
    assert "formalization_gap" in gap_kinds
