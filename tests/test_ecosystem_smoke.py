from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from typer.testing import CliRunner

from cosheaf.cli import app
from scripts.ecosystem_smoke import (
    ISSUE_ID,
    PUBLIC_ARTIFACT_ID,
    MatrixCaseStatus,
    build_ecosystem_smoke_matrix,
    build_ecosystem_smoke_plan,
    run_ecosystem_smoke_matrix,
    write_accepted_to_draft_violation_workspace,
    write_ecosystem_smoke_workspace,
    write_public_to_private_violation_workspace,
)

runner = CliRunner()


def test_ecosystem_smoke_plan_covers_three_repo_commands(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    public_private_violation_workspace = tmp_path / "public-leak-workspace"
    accepted_draft_violation_workspace = tmp_path / "accepted-draft-workspace"

    plan = build_ecosystem_smoke_plan(
        workspace=workspace,
        public_private_violation_workspace=public_private_violation_workspace,
        accepted_draft_violation_workspace=accepted_draft_violation_workspace,
        cosheaf_executable="cosheaf",
    )

    assert [(step.display, step.expected_returncode) for step in plan.steps] == [
        (f"cosheaf workspace info --repo-root {workspace}", 0),
        (f"cosheaf validate --repo-root {workspace}", 0),
        (f"cosheaf gate run --repo-root {workspace}", 0),
        (f"cosheaf index rebuild --repo-root {workspace}", 0),
        (f"cosheaf context build {ISSUE_ID} --repo-root {workspace}", 0),
        (
            (
                f"cosheaf artifact move-status {PUBLIC_ARTIFACT_ID} "
                f"locally_tested --repo-root {workspace}"
            ),
            1,
        ),
        (f"cosheaf validate --repo-root {public_private_violation_workspace}", 1),
        (f"cosheaf validate --repo-root {accepted_draft_violation_workspace}", 1),
    ]


def test_ecosystem_smoke_workspace_exercises_required_cli_flow(
    tmp_path: Path,
) -> None:
    write_ecosystem_smoke_workspace(tmp_path)

    workspace = runner.invoke(app, ["workspace", "info", "--repo-root", str(tmp_path)])
    assert workspace.exit_code == 0, workspace.output
    assert "Workspace: ecosystem-smoke-workspace" in workspace.output
    assert "public | kb/public | readonly=true | priority=10" in workspace.output
    assert "private | kb/private | readonly=false | priority=20" in workspace.output

    validate = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])
    assert validate.exit_code == 0, validate.output
    assert "Validation passed" in validate.output

    gate = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])
    assert gate.exit_code == 0, gate.output
    assert "Gate verdict: pass" in gate.output
    gate_report = _latest_gate_report(tmp_path)
    gate_statuses = {gate["id"]: gate["status"] for gate in gate_report["gates"]}
    assert gate_statuses["G6"] == "skipped"
    assert gate_statuses["G6"] != "pass"

    index = runner.invoke(app, ["index", "rebuild", "--repo-root", str(tmp_path)])
    assert index.exit_code == 0, index.output
    assert "Index rebuilt" in index.output

    context = runner.invoke(
        app,
        ["context", "build", ISSUE_ID, "--repo-root", str(tmp_path)],
    )
    assert context.exit_code == 0, context.output
    assert "Context pack built" in context.output

    manifest = cast(
        dict[str, Any],
        json.loads(
            (tmp_path / ".cosheaf" / "artifact_manifest.json").read_text(
                encoding="utf-8"
            )
        ),
    )
    artifacts = {artifact["id"]: artifact for artifact in manifest["artifacts"]}
    assert artifacts[PUBLIC_ARTIFACT_ID]["kb_root"] == "public"
    assert artifacts["claim.ecosystem.private"]["kb_root"] == "private"
    assert manifest["dependencies"] == [
        {
            "source_id": "claim.ecosystem.private",
            "target_id": PUBLIC_ARTIFACT_ID,
        }
    ]
    assert (
        tmp_path / "context" / "TASKS" / ISSUE_ID / "CONTEXT.md"
    ).is_file()


def test_ecosystem_smoke_refuses_readonly_public_root_write(
    tmp_path: Path,
) -> None:
    write_ecosystem_smoke_workspace(tmp_path)

    result = runner.invoke(
        app,
        [
            "artifact",
            "move-status",
            PUBLIC_ARTIFACT_ID,
            "locally_tested",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "readonly KB root cannot be modified: public" in result.output
    assert (
        tmp_path
        / "kb"
        / "public"
        / "accepted"
        / "definitions"
        / f"{PUBLIC_ARTIFACT_ID}.yaml"
    ).is_file()
    assert not (
        tmp_path
        / "kb"
        / "public"
        / "locally_tested"
        / "definitions"
        / f"{PUBLIC_ARTIFACT_ID}.yaml"
    ).exists()


def test_ecosystem_smoke_rejects_public_dependency_on_private(
    tmp_path: Path,
) -> None:
    write_public_to_private_violation_workspace(tmp_path)

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    normalized_output = " ".join(result.output.split())
    assert "public artifact depends on private artifact" in normalized_output
    assert "claim.ecosystem.private" in result.output


def test_ecosystem_smoke_rejects_accepted_dependency_on_draft(
    tmp_path: Path,
) -> None:
    write_accepted_to_draft_violation_workspace(tmp_path)

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    normalized_output = " ".join(result.output.split())
    assert "accepted artifact depends on draft artifact" in normalized_output
    assert "claim.ecosystem.private" in result.output


def test_ecosystem_smoke_matrix_lists_required_three_repo_cases(
    tmp_path: Path,
) -> None:
    matrix = build_ecosystem_smoke_matrix(
        framework_root=tmp_path / "tcs-cosheaf",
        workspace_template_root=tmp_path / "tcs-cosheaf-workspace-template",
        public_kb_root=tmp_path / "tcs-kb-public",
        cosheaf_executable="python -m cosheaf.cli",
        framework_tag="v0.2.1",
        include_network=False,
    )

    cases = {case.id: case for case in matrix.cases}

    assert set(cases) == {
        "framework.local-checkout",
        "framework.git-tag",
        "workspace-template.demo",
        "workspace-template.cli-agent-demo",
        "workspace-template.provider-fake-smoke",
        "public-kb.policy-guard",
    }
    assert cases["framework.local-checkout"].repo == "tcs-cosheaf"
    assert cases["framework.git-tag"].requires_network is True
    assert cases["framework.git-tag"].skip_reason == (
        "requires --include-network because it installs a framework git tag"
    )
    assert cases["workspace-template.provider-fake-smoke"].argv[-1] == (
        "provider-fake-smoke"
    )
    assert cases["public-kb.policy-guard"].repo == "tcs-kb-public"


def test_ecosystem_smoke_matrix_report_is_structured_and_identifies_failures(
    tmp_path: Path,
) -> None:
    matrix = build_ecosystem_smoke_matrix(
        framework_root=tmp_path / "tcs-cosheaf",
        workspace_template_root=tmp_path / "tcs-cosheaf-workspace-template",
        public_kb_root=tmp_path / "tcs-kb-public",
        cosheaf_executable="python -m cosheaf.cli",
        framework_tag="v0.2.1",
        include_network=False,
    )

    def fake_runner(argv: tuple[str, ...], cwd: Path) -> int:
        if cwd.name == "tcs-kb-public":
            return 2
        return 0

    report = run_ecosystem_smoke_matrix(matrix, command_runner=fake_runner)

    assert report.passed is False
    assert report.case_count == 6
    assert report.pass_count == 3
    assert report.fail_count == 1
    assert report.skip_count == 2
    assert report.results[1].status is MatrixCaseStatus.SKIPPED
    failure = [result for result in report.results if result.status == "fail"][0]
    assert failure.repo == "tcs-kb-public"
    assert "check_public_kb_policy.py" in failure.command
    assert "repo=tcs-kb-public command=" in failure.message
    assert report.to_dict()["results"][1]["status"] == "skipped"


def _latest_gate_report(repo_root: Path) -> dict[str, Any]:
    json_reports = sorted(
        (repo_root / ".cosheaf" / "reports").glob("*-gate-report.json")
    )
    assert json_reports
    return cast(
        dict[str, Any],
        json.loads(json_reports[-1].read_text(encoding="utf-8")),
    )
