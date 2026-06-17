from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import (
    WorkflowStep,
    append_step,
    load_workflow,
    start_workflow,
    step_workflow,
    write_workflow,
)
from cosheaf.workflow.handoff import (
    WORKFLOW_HANDOFF_AUTHORITY_NOTICE,
    workflow_handoff_export_path,
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
    workflow_id = "workflow.fixture.handoff"
    start_workflow(
        context,
        issue_id="issue.workflow.handoff",
        query="review a graph claim candidate",
        workflow_id=workflow_id,
    )
    step_workflow(
        context,
        workflow_id,
        action_id="workspace.info",
        execute_local_action=False,
    )
    step_workflow(
        context,
        workflow_id,
        action_id="context.build",
        execute_local_action=False,
    )
    return workflow_id


def _build_handoff(tmp_path: Path) -> tuple[str, dict[str, Any]]:
    workflow_id = _workflow_fixture(tmp_path)
    result = runner.invoke(
        app,
        [
            "workflow",
            "handoff",
            "build",
            workflow_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    return workflow_id, _json(result.output)


def _mutate_handoff(
    tmp_path: Path,
    handoff_id: str,
    mutator: Callable[[dict[str, Any]], None],
) -> None:
    handoff_path = tmp_path / workflow_handoff_path(handoff_id)
    payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    mutator(payload)
    handoff_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _scan_codes(
    tmp_path: Path,
    handoff_id: str,
) -> tuple[int, set[str], dict[str, Any]]:
    result = runner.invoke(
        app,
        [
            "workflow",
            "handoff",
            "scan",
            handoff_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    payload = _json(result.output)
    codes = {finding["code"] for finding in payload["findings"]}
    return result.exit_code, codes, payload


def test_workflow_handoff_build_show_scan_and_export_dry_run(
    tmp_path: Path,
) -> None:
    workflow_id, build_payload = _build_handoff(tmp_path)
    handoff_id = workflow_handoff_id(workflow_id)

    assert build_payload["kind"] == "workflow_handoff_bundle"
    assert build_payload["handoff_id"] == handoff_id
    assert build_payload["workflow_id"] == workflow_id
    assert build_payload["issue_id"] == "issue.workflow.handoff"
    assert build_payload["query_objective"] == "review a graph claim candidate"
    assert build_payload["scanner"]["handoff_blocked"] is False
    assert build_payload["accepted_write_performed"] is False
    assert build_payload["human_review_created"] is False
    assert build_payload["source_metadata_created"] is False
    assert build_payload["promotion_performed"] is False
    assert build_payload["verifier_result_mutated"] is False
    assert build_payload["gate_result_mutated"] is False
    assert build_payload["review_context_only"] is True
    assert build_payload["authority_notice"] == WORKFLOW_HANDOFF_AUTHORITY_NOTICE
    assert build_payload["path"] == workflow_handoff_path(handoff_id).as_posix()
    assert (tmp_path / workflow_handoff_path(handoff_id)).is_file()

    show = runner.invoke(
        app,
        [
            "workflow",
            "handoff",
            "show",
            handoff_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert show.exit_code == 0, show.output
    assert _json(show.output) == build_payload

    scan = runner.invoke(
        app,
        [
            "workflow",
            "handoff",
            "scan",
            handoff_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert scan.exit_code == 0, scan.output
    scan_payload = _json(scan.output)
    assert scan_payload["kind"] == "workflow_handoff_scan"
    assert scan_payload["handoff_blocked"] is False
    assert scan_payload["blocking_finding_count"] == 0

    export = runner.invoke(
        app,
        [
            "workflow",
            "handoff",
            "export",
            handoff_id,
            "--dry-run",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert export.exit_code == 0, export.output
    export_payload = _json(export.output)
    assert export_payload["kind"] == "workflow_handoff_export"
    assert export_payload["dry_run"] is True
    assert export_payload["written_paths"] == []
    assert export_payload["target_path"] == workflow_handoff_export_path(
        handoff_id
    ).as_posix()
    assert not (tmp_path / workflow_handoff_export_path(handoff_id)).exists()

    write_export = runner.invoke(
        app,
        [
            "workflow",
            "handoff",
            "export",
            handoff_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert write_export.exit_code == 0, write_export.output
    write_payload = _json(write_export.output)
    export_path = tmp_path / workflow_handoff_export_path(handoff_id)
    assert write_payload["dry_run"] is False
    assert write_payload["written_paths"] == [
        workflow_handoff_export_path(handoff_id).as_posix()
    ]
    assert export_path.is_file()
    exported = yaml.safe_load(export_path.read_text(encoding="utf-8"))
    assert exported == write_payload
    assert exported["review_context_only"] is True
    assert exported["accepted_write_performed"] is False


def test_workflow_handoff_scan_blocks_private_leakage(tmp_path: Path) -> None:
    _workflow_id, build_payload = _build_handoff(tmp_path)
    handoff_id = build_payload["handoff_id"]

    def _leak_private(payload: dict[str, Any]) -> None:
        payload["candidate_claims"][0]["statement"] = (
            "Leaked private path kb/private/draft/claims/claim.secret.yaml"
        )

    _mutate_handoff(tmp_path, handoff_id, _leak_private)

    exit_code, codes, payload = _scan_codes(tmp_path, handoff_id)

    assert exit_code == 1
    assert "private_path_reference" in codes
    assert payload["handoff_blocked"] is True


def test_workflow_handoff_scan_blocks_accepted_write_attempt(
    tmp_path: Path,
) -> None:
    _workflow_id, build_payload = _build_handoff(tmp_path)
    handoff_id = build_payload["handoff_id"]

    def _accepted_write(payload: dict[str, Any]) -> None:
        payload["target_path"] = "kb/accepted/claims/claim.bad.yaml"

    _mutate_handoff(tmp_path, handoff_id, _accepted_write)

    exit_code, codes, _payload = _scan_codes(tmp_path, handoff_id)

    assert exit_code == 1
    assert "accepted_write_attempt" in codes


def test_workflow_handoff_scan_blocks_human_review_overclaim(
    tmp_path: Path,
) -> None:
    _workflow_id, build_payload = _build_handoff(tmp_path)
    handoff_id = build_payload["handoff_id"]

    def _human_reviewed(payload: dict[str, Any]) -> None:
        payload["human_review_created"] = True

    _mutate_handoff(tmp_path, handoff_id, _human_reviewed)

    exit_code, codes, _payload = _scan_codes(tmp_path, handoff_id)

    assert exit_code == 1
    assert "human_review_overclaim" in codes


def test_workflow_handoff_scan_blocks_source_metadata_fabrication(
    tmp_path: Path,
) -> None:
    _workflow_id, build_payload = _build_handoff(tmp_path)
    handoff_id = build_payload["handoff_id"]

    def _fabricate_sources(payload: dict[str, Any]) -> None:
        payload["candidate_claims"][0]["sources"] = [
            {"title": "Fabricated locator", "page": "guessed"}
        ]

    _mutate_handoff(tmp_path, handoff_id, _fabricate_sources)

    exit_code, codes, _payload = _scan_codes(tmp_path, handoff_id)

    assert exit_code == 1
    assert "source_metadata_fabrication" in codes


def test_workflow_handoff_preserves_skipped_not_pass_warning(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)
    workflow_id = "workflow.fixture.skipped"
    start_workflow(
        context,
        issue_id="issue.workflow.skipped",
        query="handle skipped evidence honestly",
        workflow_id=workflow_id,
    )
    workflow = load_workflow(context, workflow_id)
    skipped = append_step(
        workflow,
        WorkflowStep(
            step_number=1,
            action="formal.check",
            status="skipped",
            output_refs={"action_status": "skipped", "scanner_status": "skipped"},
        ),
    )
    write_workflow(context, skipped)

    build = runner.invoke(
        app,
        [
            "workflow",
            "handoff",
            "build",
            workflow_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert build.exit_code == 0, build.output
    payload = _json(build.output)
    assert "Skipped workflow steps are not pass evidence." in (
        payload["evidence_and_limitations"]
    )
    assert payload["scanner"]["handoff_blocked"] is False
    assert payload["scanner"]["blocking_finding_count"] == 0
    codes = {finding["code"] for finding in payload["scanner"]["findings"]}
    assert "skipped_not_pass" in codes
