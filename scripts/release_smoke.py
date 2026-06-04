from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ISSUE_ID = "issue.release-smoke"


@dataclass(frozen=True)
class CommandStep:
    """One subprocess step in the release smoke plan."""

    name: str
    argv: tuple[str, ...]

    @property
    def display(self) -> str:
        return " ".join(self.argv)


@dataclass(frozen=True)
class ReleaseSmokePlan:
    """Fully expanded clean-environment release smoke plan."""

    source: str
    python_executable: Path
    venv_dir: Path
    venv_python: Path
    cosheaf_executable: Path
    workspace: Path
    steps: tuple[CommandStep, ...]


def build_release_smoke_plan(
    *,
    source: str,
    venv_dir: Path,
    workspace: Path,
    python_executable: Path | None = None,
) -> ReleaseSmokePlan:
    """Build the deterministic command sequence for release smoke testing."""
    base_python = (
        Path(sys.executable) if python_executable is None else python_executable
    )
    venv_python = _venv_python(venv_dir)
    cosheaf_executable = _venv_script(venv_dir, "cosheaf")
    steps = (
        CommandStep(
            name="create virtual environment",
            argv=(str(base_python), "-m", "venv", str(venv_dir)),
        ),
        CommandStep(
            name="upgrade pip",
            argv=(str(venv_python), "-m", "pip", "install", "--upgrade", "pip"),
        ),
        CommandStep(
            name="install tcs-cosheaf",
            argv=(str(venv_python), "-m", "pip", "install", source),
        ),
        CommandStep(name="show help", argv=(str(cosheaf_executable), "--help")),
        CommandStep(name="show version", argv=(str(cosheaf_executable), "version")),
        CommandStep(
            name="validate fixture",
            argv=(str(cosheaf_executable), "validate", "--repo-root", str(workspace)),
        ),
        CommandStep(
            name="run gatekeeper",
            argv=(
                str(cosheaf_executable),
                "gate",
                "run",
                "--repo-root",
                str(workspace),
            ),
        ),
        CommandStep(
            name="rebuild index",
            argv=(
                str(cosheaf_executable),
                "index",
                "rebuild",
                "--repo-root",
                str(workspace),
            ),
        ),
        CommandStep(
            name="build context pack",
            argv=(
                str(cosheaf_executable),
                "context",
                "build",
                ISSUE_ID,
                "--repo-root",
                str(workspace),
            ),
        ),
    )
    return ReleaseSmokePlan(
        source=source,
        python_executable=base_python,
        venv_dir=venv_dir,
        venv_python=venv_python,
        cosheaf_executable=cosheaf_executable,
        workspace=workspace,
        steps=steps,
    )


def write_release_smoke_workspace(workspace: Path) -> None:
    """Write a tiny deterministic repository fixture for release smoke commands."""
    workspace.mkdir(parents=True, exist_ok=True)
    _write_text(
        workspace / "context" / "PROJECT_STATE.md",
        "# Project State\n\nRelease smoke fixture for v0.1.0.\n",
    )
    _write_text(
        workspace / "context" / "INTERFACE_REGISTRY.md",
        "# Interface Registry\n\n- `cosheaf context build <issue-id>`\n",
    )
    _write_text(
        workspace / ".github" / "pull_request_template.md",
        "\n".join(
            [
                "## Summary",
                "",
                "- Release smoke fixture.",
                "",
                "## Tests Run",
                "",
                "- [ ] `cosheaf validate`",
                "- [ ] `cosheaf gate run`",
                "",
            ]
        )
        + "\n",
    )
    _write_text(
        workspace / "issues" / "open" / f"{ISSUE_ID}.yaml",
        "\n".join(
            [
                f"id: {ISSUE_ID}",
                "type: issue",
                "title: Run the release smoke fixture",
                "status: open",
                'created_at: "2026-06-04T00:00:00Z"',
                'updated_at: "2026-06-04T00:00:00Z"',
                "authors:",
                "- release-engineering",
                "severity: low",
                "description: |",
                "  Exercise the release smoke command set against a tiny local",
                "  fixture without requiring external repositories.",
                "related_artifacts:",
                "- claim.release-smoke",
                "tags:",
                "- release-smoke",
                "",
            ]
        ),
    )
    _write_text(
        workspace / "kb" / "draft" / "claims" / "claim.release-smoke.yaml",
        "\n".join(
            [
                "id: claim.release-smoke",
                "type: claim",
                "title: Release smoke fixture claim",
                "domain:",
                "- release-engineering",
                "status: draft",
                'created_at: "2026-06-04T00:00:00Z"',
                'updated_at: "2026-06-04T00:00:00Z"',
                "authors:",
                "- release-engineering",
                "depends_on: []",
                "supersedes: []",
                "tags:",
                "- release-smoke",
                "statement: The release smoke fixture exercises CLI commands.",
                "evidence:",
                "- kind: external",
                "  path: external:release-smoke-fixture",
                "  summary: Local deterministic smoke fixture.",
                "review:",
                "  state: requested",
                "  notes: Release smoke fixture, not accepted knowledge.",
                "risk:",
                "  level: low",
                "  notes: Draft-only local smoke fixture.",
                "",
            ]
        ),
    )


def run_release_smoke(plan: ReleaseSmokePlan) -> int:
    """Run a release smoke plan and return the first failing exit code."""
    write_release_smoke_workspace(plan.workspace)
    for step in plan.steps:
        print(f"$ {step.display}", flush=True)
        completed = subprocess.run(step.argv, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a clean-environment TCS-Cosheaf release smoke test.",
    )
    parser.add_argument(
        "--source",
        default=".",
        help=(
            "Package source passed to pip install. Use "
            "git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.1.0 "
            "to test the release tag."
        ),
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help="Optional working directory to reuse instead of a temporary directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command plan without running it.",
    )
    args = parser.parse_args(argv)

    if args.workdir is not None:
        return _run_with_workdir(args.source, args.workdir, dry_run=args.dry_run)

    with tempfile.TemporaryDirectory(prefix="cosheaf-release-smoke-") as temp_dir:
        return _run_with_workdir(args.source, Path(temp_dir), dry_run=args.dry_run)


def _run_with_workdir(source: str, workdir: Path, *, dry_run: bool) -> int:
    if workdir.exists() and not dry_run:
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    plan = build_release_smoke_plan(
        source=source,
        venv_dir=workdir / "venv",
        workspace=workdir / "workspace",
    )
    if dry_run:
        write_release_smoke_workspace(plan.workspace)
        for step in plan.steps:
            print(step.display)
        return 0
    return run_release_smoke(plan)


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_script(venv_dir: Path, name: str) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


def _write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
