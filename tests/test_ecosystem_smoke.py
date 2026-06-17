from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast

from typer.testing import CliRunner

from cosheaf.cli import app
from scripts.ecosystem_smoke import (
    ISSUE_ID,
    PUBLIC_ARTIFACT_ID,
    _public_kb_operator_handoff_policy_command,
    _public_kb_research_loop_policy_command,
    _public_kb_strategy_plan_policy_command,
    _run_operator_handoff_dry_run_smoke,
    _run_operator_session_cli_smoke,
    _run_research_loop_workflow_smoke,
    _run_verifier_evidence_eval_smoke,
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
        "framework.verifier-evidence-eval",
        "framework.checked-evidence-run-loop-eval",
        "framework.research-run-loop-eval",
        "framework.research-loop-eval",
        "framework.research-loop-workflow-smoke",
        "framework.strategy-planner-eval",
        "framework.operator-session-cli-smoke",
        "framework.operator-handoff-dry-run-smoke",
        "framework.optional-verifier-availability",
        "framework.git-tag",
        "workspace-template.demo",
        "workspace-template.cli-agent-demo",
        "workspace-template.research-run-demo",
        "workspace-template.strategy-demo",
        "workspace-template.research-loop-demo",
        "workspace-template.operator-session-demo",
        "workspace-template.provider-fake-smoke",
        "workspace-template.verifier-evidence-demo",
        "public-kb.policy-guard",
        "public-kb.checked-evidence-policy-docs",
        "public-kb.strategy-plan-policy-docs",
        "public-kb.operator-handoff-policy-docs",
        "public-kb.research-loop-policy-docs",
        "public-kb.verifier-policy-self-test",
    }
    assert cases["framework.local-checkout"].repo == "tcs-cosheaf"
    assert cases["framework.verifier-evidence-eval"].repo == "tcs-cosheaf"
    assert cases["framework.checked-evidence-run-loop-eval"].argv[-2:] == (
        "checked-evidence-run-loop",
        "--json",
    )
    assert cases["framework.research-run-loop-eval"].argv[-2:] == (
        "research-run-loop",
        "--json",
    )
    assert cases["framework.research-loop-eval"].argv[-2:] == (
        "research-loop",
        "--json",
    )
    assert cases["framework.research-loop-workflow-smoke"].repo == "tcs-cosheaf"
    assert cases["framework.strategy-planner-eval"].argv[-2:] == (
        "strategy-planner",
        "--json",
    )
    assert cases["framework.operator-session-cli-smoke"].repo == "tcs-cosheaf"
    assert cases["framework.operator-handoff-dry-run-smoke"].repo == "tcs-cosheaf"
    assert cases["framework.optional-verifier-availability"].repo == "tcs-cosheaf"
    assert cases["framework.git-tag"].requires_network is True
    assert cases["framework.git-tag"].skip_reason == (
        "requires --include-network because it installs a framework git tag"
    )
    assert cases["workspace-template.research-run-demo"].argv[-1] == (
        "research-run-demo"
    )
    assert cases["workspace-template.strategy-demo"].argv[-1] == "strategy-demo"
    assert cases["workspace-template.research-loop-demo"].argv[-1] == (
        "research-loop-demo"
    )
    assert cases["workspace-template.operator-session-demo"].argv[-1] == (
        "operator-session-demo"
    )
    assert cases["workspace-template.provider-fake-smoke"].argv[-1] == (
        "provider-fake-smoke"
    )
    assert cases["workspace-template.verifier-evidence-demo"].argv[-1] == (
        "verifier-evidence-demo"
    )
    assert cases["public-kb.policy-guard"].repo == "tcs-kb-public"
    assert cases["public-kb.checked-evidence-policy-docs"].repo == "tcs-kb-public"
    assert cases["public-kb.strategy-plan-policy-docs"].repo == "tcs-kb-public"
    assert cases["public-kb.operator-handoff-policy-docs"].repo == "tcs-kb-public"
    assert cases["public-kb.research-loop-policy-docs"].repo == "tcs-kb-public"
    assert cases["public-kb.verifier-policy-self-test"].repo == "tcs-kb-public"


def test_ecosystem_smoke_matrix_defaults_to_current_release_tag(
    tmp_path: Path,
) -> None:
    matrix = build_ecosystem_smoke_matrix(
        framework_root=tmp_path / "tcs-cosheaf",
        workspace_template_root=tmp_path / "tcs-cosheaf-workspace-template",
        public_kb_root=tmp_path / "tcs-kb-public",
    )

    assert matrix.framework_tag == "v0.6.0"


def test_operator_session_cli_smoke_uses_temp_workspace() -> None:
    assert _run_operator_session_cli_smoke(Path.cwd()) == 0


def test_operator_handoff_dry_run_smoke_uses_temp_workspace() -> None:
    assert _run_operator_handoff_dry_run_smoke(Path.cwd()) == 0


def test_research_loop_workflow_smoke_uses_temp_workspace() -> None:
    assert _run_research_loop_workflow_smoke(Path.cwd()) == 0


def test_public_kb_strategy_plan_policy_docs_smoke_normalizes_wrapped_text(
    tmp_path: Path,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "STRATEGY_PLAN_POLICY.md").write_text(
        "\n".join(
            [
                "# Strategy Plan Policy",
                "",
                "Strategy plans are public review context only.",
                "Accepted public artifacts still require complete source metadata.",
                "Do not copy private strategy plans.",
                "`candidate_counterexample` remains proposed evidence only.",
                "Checked evidence can support maintainer review.",
                "Promotion",
                "still requires the ordinary accepted-artifact workflow.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        _public_kb_strategy_plan_policy_command(),
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_public_kb_operator_handoff_policy_docs_smoke(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    scripts = tmp_path / "scripts"
    docs.mkdir()
    scripts.mkdir()
    (docs / "OPERATOR_HANDOFF_POLICY.md").write_text(
        "\n".join(
            [
                "# Operator Handoff Policy",
                "",
                "Operator handoff bundles and `reviews/operator/` exports are",
                "public review context only.",
                "Operator handoff material is not:",
                "- source metadata;",
                "Accepted public artifacts still require complete artifact-local",
                "source metadata.",
                "Public KB handoff records must not contain private workspace paths.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (docs / "PUBLIC_KB_POLICY_GUARD.md").write_text(
        "The guard scans reviews/operator and review_context_only fields.\n",
        encoding="utf-8",
    )
    (scripts / "check_public_kb_policy.py").write_text(
        "raise SystemExit('operator handoff is claimed as source metadata')\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        _public_kb_operator_handoff_policy_command(),
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_public_kb_research_loop_policy_docs_smoke(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "RESEARCH_LOOP_POLICY.md").write_text(
        "\n".join(
            [
                "# Research Loop Policy",
                "",
                "Research loop outputs are public review context only.",
                "They are not source metadata and not accepted proof.",
                "Accepted public artifacts still require complete source metadata.",
                "Validation and gate success are not human review.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        _public_kb_research_loop_policy_command(),
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout


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
        command = " ".join(argv)
        if "--optional-verifier-availability" in command:
            return 77
        if (
            cwd.name == "tcs-kb-public"
            and any(part.endswith("check_public_kb_policy.py") for part in argv)
            and "--self-test" not in argv
        ):
            return 2
        return 0

    report = run_ecosystem_smoke_matrix(matrix, command_runner=fake_runner)

    assert report.passed is False
    assert report.case_count == 25
    assert report.pass_count == 21
    assert report.fail_count == 1
    assert report.skip_count == 3
    skipped = [result for result in report.results if result.status == "skipped"]
    assert {result.id for result in skipped} == {
        "framework.optional-verifier-availability",
        "framework.git-tag",
        "workspace-template.demo",
    }
    failure = [result for result in report.results if result.status == "fail"][0]
    assert failure.repo == "tcs-kb-public"
    assert "check_public_kb_policy.py" in failure.command
    assert "repo=tcs-kb-public command=" in failure.message
    optional_skip = [
        result
        for result in report.results
        if result.id == "framework.optional-verifier-availability"
    ][0]
    assert optional_skip.returncode == 77
    assert "repo=tcs-cosheaf command=" in optional_skip.message
    assert report.to_dict()["skip_count"] == 3


def test_verifier_evidence_eval_smoke_uses_clean_eval_context(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "framework"
    cases_path = repo_root / "evals" / "verifier_evidence" / "cases.yaml"
    cases_path.parent.mkdir(parents=True)
    cases_path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "cases:",
                "  - id: case.verifier.pass-policy",
                "    kind: pass_evidence_policy_allowed",
                "    expect_ready: true",
                "    expect_evidence_result: pass",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (repo_root / "kb" / "accepted").mkdir(parents=True)

    assert _run_verifier_evidence_eval_smoke(repo_root) == 0


def _latest_gate_report(repo_root: Path) -> dict[str, Any]:
    json_reports = sorted(
        (repo_root / ".cosheaf" / "reports").glob("*-gate-report.json")
    )
    assert json_reports
    return cast(
        dict[str, Any],
        json.loads(json_reports[-1].read_text(encoding="utf-8")),
    )
