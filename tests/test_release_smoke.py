from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from cosheaf.cli import app
from scripts.release_smoke import (
    build_release_smoke_plan,
    write_release_smoke_workspace,
)

runner = CliRunner()


def test_release_smoke_plan_covers_clean_install_and_required_commands(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    venv_dir = tmp_path / "venv"

    plan = build_release_smoke_plan(
        source="git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.1.0",
        venv_dir=venv_dir,
        workspace=workspace,
    )

    commands = [step.display for step in plan.steps]

    assert commands == [
        f"{plan.python_executable} -m venv {venv_dir}",
        f"{plan.venv_python} -m pip install --upgrade pip",
        (
            f"{plan.venv_python} -m pip install "
            "git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.1.0"
        ),
        f"{plan.cosheaf_executable} --help",
        f"{plan.cosheaf_executable} version",
        f"{plan.cosheaf_executable} validate --repo-root {workspace}",
        f"{plan.cosheaf_executable} gate run --repo-root {workspace}",
        f"{plan.cosheaf_executable} index rebuild --repo-root {workspace}",
        (
            f"{plan.cosheaf_executable} context build issue.release-smoke "
            f"--repo-root {workspace}"
        ),
    ]


def test_release_smoke_workspace_exercises_required_cli_flow(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    write_release_smoke_workspace(workspace)

    validate = runner.invoke(app, ["validate", "--repo-root", str(workspace)])
    assert validate.exit_code == 0, validate.output
    assert "Validation passed" in validate.output

    gate = runner.invoke(app, ["gate", "run", "--repo-root", str(workspace)])
    assert gate.exit_code == 0, gate.output
    assert "Gate verdict: pass" in gate.output

    index = runner.invoke(app, ["index", "rebuild", "--repo-root", str(workspace)])
    assert index.exit_code == 0, index.output
    assert "Index rebuilt" in index.output

    context = runner.invoke(
        app,
        ["context", "build", "issue.release-smoke", "--repo-root", str(workspace)],
    )
    assert context.exit_code == 0, context.output
    assert "Context pack built" in context.output
