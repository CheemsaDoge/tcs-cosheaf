from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

ISSUE_ID = "issue.ecosystem-smoke.private-context"
PUBLIC_ARTIFACT_ID = "definition.ecosystem.graph"
PRIVATE_ARTIFACT_ID = "claim.ecosystem.private"
DEFAULT_FRAMEWORK_TAG = "v0.4.0"


@dataclass(frozen=True)
class CommandStep:
    """One command in the local three-repository smoke plan."""

    name: str
    argv: tuple[str, ...]
    expected_returncode: int = 0

    @property
    def display(self) -> str:
        return " ".join(self.argv)


@dataclass(frozen=True)
class EcosystemSmokePlan:
    """A deterministic local smoke plan for the three-repository model."""

    workspace: Path
    public_private_violation_workspace: Path
    accepted_draft_violation_workspace: Path
    steps: tuple[CommandStep, ...]


class MatrixCaseStatus(StrEnum):
    """Structured release matrix case status."""

    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class MatrixCommand:
    """One command belonging to a release matrix case."""

    argv: tuple[str, ...]
    skip_returncodes: tuple[int, ...] = ()

    @property
    def display(self) -> str:
        return " ".join(self.argv)


@dataclass(frozen=True)
class EcosystemSmokeMatrixCase:
    """One row in the three-repository compatibility smoke matrix."""

    id: str
    repo: str
    cwd: Path
    commands: tuple[MatrixCommand, ...]
    requires_network: bool = False
    env: dict[str, str] | None = None
    skip_reason: str | None = None

    @property
    def argv(self) -> tuple[str, ...]:
        """Return the first command argv for simple single-command callers."""
        if not self.commands:
            return ()
        return self.commands[0].argv


@dataclass(frozen=True)
class EcosystemSmokeMatrix:
    """A structured compatibility smoke matrix across the three repositories."""

    framework_root: Path
    workspace_template_root: Path
    public_kb_root: Path
    framework_tag: str
    include_network: bool
    cases: tuple[EcosystemSmokeMatrixCase, ...]


@dataclass(frozen=True)
class EcosystemSmokeMatrixCaseResult:
    """One executed compatibility smoke matrix result."""

    id: str
    repo: str
    status: MatrixCaseStatus
    command: str
    returncode: int | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible case result data."""
        return {
            "id": self.id,
            "repo": self.repo,
            "status": self.status.value,
            "command": self.command,
            "returncode": self.returncode,
            "message": self.message,
        }


@dataclass(frozen=True)
class EcosystemSmokeMatrixReport:
    """Structured compatibility smoke matrix report."""

    schema_version: int
    framework_tag: str
    include_network: bool
    results: tuple[EcosystemSmokeMatrixCaseResult, ...]

    @property
    def case_count(self) -> int:
        """Return the number of matrix rows."""
        return len(self.results)

    @property
    def pass_count(self) -> int:
        """Return the number of passed matrix rows."""
        return sum(
            1 for result in self.results if result.status is MatrixCaseStatus.PASS
        )

    @property
    def fail_count(self) -> int:
        """Return the number of failed matrix rows."""
        return sum(
            1 for result in self.results if result.status is MatrixCaseStatus.FAIL
        )

    @property
    def skip_count(self) -> int:
        """Return the number of skipped matrix rows."""
        return sum(
            1 for result in self.results if result.status is MatrixCaseStatus.SKIPPED
        )

    @property
    def passed(self) -> bool:
        """Return whether no executed matrix row failed."""
        return self.fail_count == 0

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible report data."""
        return {
            "schema_version": self.schema_version,
            "framework_tag": self.framework_tag,
            "include_network": self.include_network,
            "case_count": self.case_count,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "skip_count": self.skip_count,
            "passed": self.passed,
            "results": [result.to_dict() for result in self.results],
        }

    def to_json(self) -> str:
        """Return deterministic JSON report text."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


def build_ecosystem_smoke_plan(
    *,
    workspace: Path,
    public_private_violation_workspace: Path,
    accepted_draft_violation_workspace: Path,
    cosheaf_executable: str | Path = "cosheaf",
) -> EcosystemSmokePlan:
    """Build commands for a local, network-free three-repository smoke run."""
    cosheaf = tuple(shlex.split(str(cosheaf_executable))) or ("cosheaf",)
    steps = (
        CommandStep(
            name="inspect workspace",
            argv=(*cosheaf, "workspace", "info", "--repo-root", str(workspace)),
        ),
        CommandStep(
            name="validate workspace",
            argv=(*cosheaf, "validate", "--repo-root", str(workspace)),
        ),
        CommandStep(
            name="run gatekeeper",
            argv=(*cosheaf, "gate", "run", "--repo-root", str(workspace)),
        ),
        CommandStep(
            name="rebuild index",
            argv=(*cosheaf, "index", "rebuild", "--repo-root", str(workspace)),
        ),
        CommandStep(
            name="build private issue context",
            argv=(
                *cosheaf,
                "context",
                "build",
                ISSUE_ID,
                "--repo-root",
                str(workspace),
            ),
        ),
        CommandStep(
            name="verify readonly public root write refusal",
            argv=(
                *cosheaf,
                "artifact",
                "move-status",
                PUBLIC_ARTIFACT_ID,
                "locally_tested",
                "--repo-root",
                str(workspace),
            ),
            expected_returncode=1,
        ),
        CommandStep(
            name="verify public-to-private dependency rejection",
            argv=(
                *cosheaf,
                "validate",
                "--repo-root",
                str(public_private_violation_workspace),
            ),
            expected_returncode=1,
        ),
        CommandStep(
            name="verify accepted-to-draft dependency rejection",
            argv=(
                *cosheaf,
                "validate",
                "--repo-root",
                str(accepted_draft_violation_workspace),
            ),
            expected_returncode=1,
        ),
    )
    return EcosystemSmokePlan(
        workspace=workspace,
        public_private_violation_workspace=public_private_violation_workspace,
        accepted_draft_violation_workspace=accepted_draft_violation_workspace,
        steps=steps,
    )


def build_ecosystem_smoke_matrix(
    *,
    framework_root: Path,
    workspace_template_root: Path,
    public_kb_root: Path,
    cosheaf_executable: str | Path = "python -m cosheaf.cli",
    framework_tag: str = DEFAULT_FRAMEWORK_TAG,
    include_network: bool = False,
    bash_executable: str | None = None,
    make_executable: str = "make",
) -> EcosystemSmokeMatrix:
    """Build the structured release matrix across the three repositories."""
    cosheaf = str(cosheaf_executable)
    framework_root = framework_root.resolve()
    workspace_template_root = workspace_template_root.resolve()
    public_kb_root = public_kb_root.resolve()
    pythonpath = str(framework_root)
    local_env = {
        "COSHEAF_CMD": cosheaf,
        "COSHEAF_SKIP_INSTALL": "1",
        "PYTHONPATH": pythonpath,
    }
    workspace_demo_env: dict[str, str] = {}
    if bash_executable is not None:
        local_env["BASH"] = bash_executable
        workspace_demo_env["BASH"] = bash_executable
    public_kb_env = {"PYTHONPATH": pythonpath}
    tag_source = (
        "git+https://github.com/CheemsaDoge/tcs-cosheaf.git@"
        f"{framework_tag}"
    )
    cases = (
        EcosystemSmokeMatrixCase(
            id="framework.local-checkout",
            repo="tcs-cosheaf",
            cwd=framework_root,
            commands=(
                MatrixCommand(
                    (
                        sys.executable,
                        "scripts/ecosystem_smoke.py",
                        "--cosheaf",
                        cosheaf,
                    )
                ),
            ),
        ),
        EcosystemSmokeMatrixCase(
            id="framework.verifier-evidence-eval",
            repo="tcs-cosheaf",
            cwd=framework_root,
            commands=(
                MatrixCommand(
                    (
                        sys.executable,
                        "scripts/ecosystem_smoke.py",
                        "--verifier-evidence-eval",
                    )
                ),
            ),
        ),
        EcosystemSmokeMatrixCase(
            id="framework.checked-evidence-run-loop-eval",
            repo="tcs-cosheaf",
            cwd=framework_root,
            commands=(
                MatrixCommand(
                    (
                        *shlex.split(cosheaf),
                        "eval",
                        "checked-evidence-run-loop",
                        "--json",
                    )
                ),
            ),
        ),
        EcosystemSmokeMatrixCase(
            id="framework.research-run-loop-eval",
            repo="tcs-cosheaf",
            cwd=framework_root,
            commands=(
                MatrixCommand(
                    (
                        *shlex.split(cosheaf),
                        "eval",
                        "research-run-loop",
                        "--json",
                    )
                ),
            ),
        ),
        EcosystemSmokeMatrixCase(
            id="framework.strategy-planner-eval",
            repo="tcs-cosheaf",
            cwd=framework_root,
            commands=(
                MatrixCommand(
                    (
                        *shlex.split(cosheaf),
                        "eval",
                        "strategy-planner",
                        "--json",
                    )
                ),
            ),
        ),
        EcosystemSmokeMatrixCase(
            id="framework.optional-verifier-availability",
            repo="tcs-cosheaf",
            cwd=framework_root,
            commands=(
                MatrixCommand(
                    (
                        sys.executable,
                        "scripts/ecosystem_smoke.py",
                        "--optional-verifier-availability",
                    ),
                    skip_returncodes=(77,),
                ),
            ),
        ),
        EcosystemSmokeMatrixCase(
            id="framework.git-tag",
            repo="tcs-cosheaf",
            cwd=framework_root,
            commands=(
                MatrixCommand(
                    (
                        sys.executable,
                        "scripts/release_smoke.py",
                        "--source",
                        tag_source,
                    )
                ),
            ),
            requires_network=True,
            env=workspace_demo_env,
            skip_reason=_network_skip_reason(
                include_network,
                "requires --include-network because it installs a framework git tag",
            ),
        ),
        EcosystemSmokeMatrixCase(
            id="workspace-template.demo",
            repo="tcs-cosheaf-workspace-template",
            cwd=workspace_template_root,
            commands=(MatrixCommand((make_executable, "demo")),),
            requires_network=True,
            skip_reason=_network_skip_reason(
                include_network,
                "requires --include-network because the demo installs a framework tag",
            ),
        ),
        EcosystemSmokeMatrixCase(
            id="workspace-template.cli-agent-demo",
            repo="tcs-cosheaf-workspace-template",
            cwd=workspace_template_root,
            commands=(MatrixCommand((make_executable, "cli-agent-demo")),),
            env=local_env,
        ),
        EcosystemSmokeMatrixCase(
            id="workspace-template.research-run-demo",
            repo="tcs-cosheaf-workspace-template",
            cwd=workspace_template_root,
            commands=(MatrixCommand((make_executable, "research-run-demo")),),
            env=local_env,
        ),
        EcosystemSmokeMatrixCase(
            id="workspace-template.strategy-demo",
            repo="tcs-cosheaf-workspace-template",
            cwd=workspace_template_root,
            commands=(MatrixCommand((make_executable, "strategy-demo")),),
            env=local_env,
        ),
        EcosystemSmokeMatrixCase(
            id="workspace-template.provider-fake-smoke",
            repo="tcs-cosheaf-workspace-template",
            cwd=workspace_template_root,
            commands=(MatrixCommand((make_executable, "provider-fake-smoke")),),
            env=local_env,
        ),
        EcosystemSmokeMatrixCase(
            id="workspace-template.verifier-evidence-demo",
            repo="tcs-cosheaf-workspace-template",
            cwd=workspace_template_root,
            commands=(MatrixCommand((make_executable, "verifier-evidence-demo")),),
            env=local_env,
        ),
        EcosystemSmokeMatrixCase(
            id="public-kb.policy-guard",
            repo="tcs-kb-public",
            cwd=public_kb_root,
            commands=(
                MatrixCommand((sys.executable, "scripts/check_public_kb_policy.py")),
                MatrixCommand((*shlex.split(cosheaf), "workspace", "info")),
                MatrixCommand((*shlex.split(cosheaf), "validate")),
                MatrixCommand((*shlex.split(cosheaf), "gate", "run")),
                MatrixCommand(
                    (
                        *shlex.split(cosheaf),
                        "gate",
                        "run",
                        "--pr-checklist",
                        ".github/pull_request_template.md",
                    )
                ),
            ),
            env=public_kb_env,
        ),
        EcosystemSmokeMatrixCase(
            id="public-kb.checked-evidence-policy-docs",
            repo="tcs-kb-public",
            cwd=public_kb_root,
            commands=(
                MatrixCommand(_public_kb_checked_evidence_policy_command()),
            ),
            env=public_kb_env,
        ),
        EcosystemSmokeMatrixCase(
            id="public-kb.strategy-plan-policy-docs",
            repo="tcs-kb-public",
            cwd=public_kb_root,
            commands=(
                MatrixCommand(_public_kb_strategy_plan_policy_command()),
            ),
            env=public_kb_env,
        ),
        EcosystemSmokeMatrixCase(
            id="public-kb.verifier-policy-self-test",
            repo="tcs-kb-public",
            cwd=public_kb_root,
            commands=(
                MatrixCommand(
                    (
                        sys.executable,
                        "scripts/check_public_kb_policy.py",
                        "--self-test",
                    )
                ),
            ),
            env=public_kb_env,
        ),
    )
    return EcosystemSmokeMatrix(
        framework_root=framework_root,
        workspace_template_root=workspace_template_root,
        public_kb_root=public_kb_root,
        framework_tag=framework_tag,
        include_network=include_network,
        cases=cases,
    )


def _public_kb_checked_evidence_policy_command() -> tuple[str, ...]:
    code = "\n".join(
        [
            "from pathlib import Path",
            "path = Path('docs/CHECKED_EVIDENCE_POLICY.md')",
            "text = path.read_text(encoding='utf-8').lower()",
            "required = (",
            "    'checked evidence and research-run records are not:',",
            "    'human review;',",
            "    'accepted public artifacts still require complete source metadata',",
            "    'research-run records must not contain private workspace material',",
            "    'candidate evidence is not mislabeled as checked evidence',",
            ")",
            "missing = [phrase for phrase in required if phrase not in text]",
            "raise SystemExit(",
            "    'missing checked-evidence policy text: ' + ', '.join(missing)",
            "    if missing else 0",
            ")",
        ]
    )
    return (sys.executable, "-c", code)


def _public_kb_strategy_plan_policy_command() -> tuple[str, ...]:
    code = "\n".join(
        [
            "from pathlib import Path",
            "path = Path('docs/STRATEGY_PLAN_POLICY.md')",
            "text = path.read_text(encoding='utf-8').lower()",
            "normalized = ' '.join(text.split())",
            "required = (",
            "    'strategy plans are public review context only',",
            "    'accepted public artifacts still require complete source metadata',",
            "    'do not copy private strategy plans',",
            "    'candidate_counterexample',",
            "    'checked evidence can support maintainer review',",
            "    'promotion still requires the ordinary accepted-artifact workflow',",
            ")",
            "missing = [phrase for phrase in required if phrase not in normalized]",
            "raise SystemExit(",
            "    'missing strategy-plan policy text: ' + ', '.join(missing)",
            "    if missing else 0",
            ")",
        ]
    )
    return (sys.executable, "-c", code)


def run_ecosystem_smoke_matrix(
    matrix: EcosystemSmokeMatrix,
    *,
    command_runner: Callable[[tuple[str, ...], Path], int] | None = None,
) -> EcosystemSmokeMatrixReport:
    """Run the structured release matrix and return a deterministic report."""
    results: list[EcosystemSmokeMatrixCaseResult] = []
    for case in matrix.cases:
        if case.skip_reason is not None:
            skipped_argv = case.argv
            results.append(
                EcosystemSmokeMatrixCaseResult(
                    id=case.id,
                    repo=case.repo,
                    status=MatrixCaseStatus.SKIPPED,
                    command=" ".join(skipped_argv),
                    returncode=None,
                    message=case.skip_reason,
                )
            )
            continue

        failed_result: EcosystemSmokeMatrixCaseResult | None = None
        skipped_result: EcosystemSmokeMatrixCaseResult | None = None
        for command in case.commands:
            if command_runner is None:
                returncode = _run_matrix_command(command.argv, case.cwd, case.env)
            else:
                returncode = command_runner(command.argv, case.cwd)
            if returncode in command.skip_returncodes:
                message = (
                    f"repo={case.repo} command={command.display} "
                    f"returncode={returncode} skipped"
                )
                skipped_result = EcosystemSmokeMatrixCaseResult(
                    id=case.id,
                    repo=case.repo,
                    status=MatrixCaseStatus.SKIPPED,
                    command=command.display,
                    returncode=returncode,
                    message=message,
                )
                break
            if returncode != 0:
                message = (
                    f"repo={case.repo} command={command.display} "
                    f"returncode={returncode}"
                )
                failed_result = EcosystemSmokeMatrixCaseResult(
                    id=case.id,
                    repo=case.repo,
                    status=MatrixCaseStatus.FAIL,
                    command=command.display,
                    returncode=returncode,
                    message=message,
                )
                break
        if skipped_result is not None:
            results.append(skipped_result)
            continue
        if failed_result is not None:
            results.append(failed_result)
            continue
        results.append(
            EcosystemSmokeMatrixCaseResult(
                id=case.id,
                repo=case.repo,
                status=MatrixCaseStatus.PASS,
                command=" && ".join(command.display for command in case.commands),
                returncode=0,
                message=f"repo={case.repo} passed",
            )
        )
    return EcosystemSmokeMatrixReport(
        schema_version=1,
        framework_tag=matrix.framework_tag,
        include_network=matrix.include_network,
        results=tuple(results),
    )


def write_ecosystem_smoke_workspace(workspace: Path) -> None:
    """Write the positive local fixture for the three-repository workflow."""
    workspace.mkdir(parents=True, exist_ok=True)
    _write_workspace_config(workspace)
    _write_project_context(workspace)
    _write_issue(workspace)
    _write_artifact(
        workspace,
        "kb/public/accepted/definitions/definition.ecosystem.graph.yaml",
        artifact_id=PUBLIC_ARTIFACT_ID,
        artifact_type="definition",
        title="Ecosystem smoke graph definition",
        status="accepted",
        domain=("graph-theory", "ecosystem-smoke"),
        depends_on=(),
        tags=("public", "ecosystem-smoke"),
        statement=(
            "A graph is represented in this local smoke fixture as a finite "
            "vertex set together with an edge relation."
        ),
        evidence_path="external:ecosystem-smoke-public-source",
        evidence_summary="Local smoke fixture source reference.",
        review_state="human_reviewed",
        review_notes=(
            "Human-reviewed fixture metadata for exercising accepted public "
            "source policy."
        ),
        risk_notes="Tiny accepted public fixture used only by smoke tests.",
        sources=(
            {
                "kind": "book",
                "title": "Graph Theory Smoke Fixture",
                "authors": ["TCS-Cosheaf maintainers"],
                "year": 2026,
                "doi": "",
                "arxiv": "",
                "url": "https://github.com/CheemsaDoge/tcs-cosheaf",
                "theorem_number": "",
                "page": "1",
                "notes": "Durable local source metadata for smoke coverage.",
            },
        ),
    )
    _write_artifact(
        workspace,
        "kb/private/draft/claims/claim.ecosystem.private.yaml",
        artifact_id=PRIVATE_ARTIFACT_ID,
        artifact_type="claim",
        title="Ecosystem smoke private draft",
        status="draft",
        domain=("graph-theory", "ecosystem-smoke"),
        depends_on=(PUBLIC_ARTIFACT_ID,),
        tags=("private", "ecosystem-smoke"),
        statement=(
            "This private draft depends on the readonly public graph "
            "definition and remains private draft knowledge."
        ),
        evidence_path="external:ecosystem-smoke-private-draft",
        evidence_summary="Local smoke fixture private draft evidence.",
        review_state="requested",
        review_notes="Private draft fixture; not accepted knowledge.",
        risk_notes="Draft-only local fixture with no theorem claim.",
    )


def write_public_to_private_violation_workspace(workspace: Path) -> None:
    """Write a negative fixture where public knowledge depends on private work."""
    write_ecosystem_smoke_workspace(workspace)
    _write_artifact(
        workspace,
        "kb/public/draft/claims/claim.ecosystem.public-leak.yaml",
        artifact_id="claim.ecosystem.public-leak",
        artifact_type="claim",
        title="Invalid public dependency on private draft",
        status="draft",
        domain=("graph-theory", "ecosystem-smoke"),
        depends_on=(PRIVATE_ARTIFACT_ID,),
        tags=("public", "negative-fixture"),
        statement=(
            "This public draft intentionally depends on private draft work so "
            "validation can reject the invalid dependency direction."
        ),
        evidence_path="external:ecosystem-smoke-negative-fixture",
        evidence_summary="Negative local smoke fixture.",
        review_state="requested",
        review_notes="Negative fixture expected to fail validation.",
        risk_notes="Intentional invalid dependency direction.",
    )


def write_accepted_to_draft_violation_workspace(workspace: Path) -> None:
    """Write a negative fixture where accepted knowledge depends on a draft."""
    write_ecosystem_smoke_workspace(workspace)
    _write_artifact(
        workspace,
        "kb/private/accepted/claims/claim.ecosystem.accepted-bad.yaml",
        artifact_id="claim.ecosystem.accepted-bad",
        artifact_type="claim",
        title="Invalid accepted dependency on private draft",
        status="accepted",
        domain=("graph-theory", "ecosystem-smoke"),
        depends_on=(PRIVATE_ARTIFACT_ID,),
        tags=("private", "negative-fixture"),
        statement=(
            "This accepted private fixture intentionally depends on a draft "
            "artifact so validation can reject accepted-to-draft dependencies."
        ),
        evidence_path="external:ecosystem-smoke-accepted-draft-fixture",
        evidence_summary="Negative local smoke fixture.",
        review_state="human_reviewed",
        review_notes="Negative fixture expected to fail validation.",
        risk_notes="Intentional accepted-to-draft dependency.",
    )


def run_ecosystem_smoke(plan: EcosystemSmokePlan) -> int:
    """Run a local smoke plan and return nonzero when any expectation fails."""
    write_ecosystem_smoke_workspace(plan.workspace)
    write_public_to_private_violation_workspace(
        plan.public_private_violation_workspace
    )
    write_accepted_to_draft_violation_workspace(
        plan.accepted_draft_violation_workspace
    )

    for step in plan.steps:
        expectation = (
            ""
            if step.expected_returncode == 0
            else f"  # expected exit {step.expected_returncode}"
        )
        print(f"$ {step.display}{expectation}", flush=True)
        completed = subprocess.run(step.argv, check=False)
        if completed.returncode != step.expected_returncode:
            print(
                "Unexpected exit code for "
                f"{step.name}: got {completed.returncode}, "
                f"expected {step.expected_returncode}",
                file=sys.stderr,
            )
            return completed.returncode or 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a local, network-free TCS-Cosheaf ecosystem smoke test."
        ),
    )
    parser.add_argument(
        "--cosheaf",
        default="cosheaf",
        help=(
            "Cosheaf command to run. Defaults to the active PATH entry. "
            "For a source checkout, use: --cosheaf \"python -m cosheaf.cli\"."
        ),
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help=(
            "Optional working directory to overwrite and reuse instead of a "
            "temporary directory."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write fixtures and print the command plan without running it.",
    )
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="Run the structured three-repository compatibility smoke matrix.",
    )
    parser.add_argument(
        "--framework-root",
        type=Path,
        default=Path.cwd(),
        help="Framework checkout root used by --matrix.",
    )
    parser.add_argument(
        "--workspace-template-root",
        type=Path,
        default=Path.cwd().parent / "tcs-cosheaf-workspace-template",
        help="Workspace-template checkout root used by --matrix.",
    )
    parser.add_argument(
        "--public-kb-root",
        type=Path,
        default=Path.cwd().parent / "tcs-kb-public",
        help="Public KB checkout root used by --matrix.",
    )
    parser.add_argument(
        "--framework-tag",
        default=DEFAULT_FRAMEWORK_TAG,
        help="Framework tag used by the network-enabled release-smoke matrix row.",
    )
    parser.add_argument(
        "--include-network",
        action="store_true",
        help=(
            "Allow matrix rows that install framework git tags. "
            "Real provider calls are still never part of this smoke."
        ),
    )
    parser.add_argument(
        "--bash",
        default=None,
        help=(
            "Optional Bash executable override used by workspace-template "
            "Makefile targets in --matrix."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the --matrix report as deterministic JSON.",
    )
    parser.add_argument(
        "--verifier-evidence-eval",
        action="store_true",
        help="Run the local verifier-evidence eval smoke used by --matrix.",
    )
    parser.add_argument(
        "--optional-verifier-availability",
        action="store_true",
        help=(
            "Probe optional SAT/SMT/Lean tool availability. Exit 77 means "
            "skipped, not pass."
        ),
    )
    args = parser.parse_args(argv)

    if args.verifier_evidence_eval:
        return _run_verifier_evidence_eval_smoke(Path.cwd())

    if args.optional_verifier_availability:
        return _run_optional_verifier_availability_probe()

    if args.matrix:
        matrix = build_ecosystem_smoke_matrix(
            framework_root=args.framework_root,
            workspace_template_root=args.workspace_template_root,
            public_kb_root=args.public_kb_root,
            cosheaf_executable=args.cosheaf,
            framework_tag=args.framework_tag,
            include_network=args.include_network,
            bash_executable=args.bash,
        )
        if args.dry_run:
            _print_matrix_plan(matrix)
            return 0
        report = run_ecosystem_smoke_matrix(matrix)
        if args.json:
            print(report.to_json(), end="")
        else:
            _print_matrix_report(report)
        return 0 if report.passed else 1

    if args.workdir is not None:
        return _run_with_workdir(
            cosheaf_executable=args.cosheaf,
            workdir=args.workdir,
            dry_run=args.dry_run,
        )

    with tempfile.TemporaryDirectory(prefix="cosheaf-ecosystem-smoke-") as temp_dir:
        return _run_with_workdir(
            cosheaf_executable=args.cosheaf,
            workdir=Path(temp_dir),
            dry_run=args.dry_run,
        )


def _run_with_workdir(
    *,
    cosheaf_executable: str | Path,
    workdir: Path,
    dry_run: bool,
) -> int:
    if workdir.exists() and not dry_run:
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    plan = build_ecosystem_smoke_plan(
        workspace=workdir / "workspace",
        public_private_violation_workspace=(
            workdir / "public-private-violation-workspace"
        ),
        accepted_draft_violation_workspace=(
            workdir / "accepted-draft-violation-workspace"
        ),
        cosheaf_executable=cosheaf_executable,
    )
    write_ecosystem_smoke_workspace(plan.workspace)
    write_public_to_private_violation_workspace(
        plan.public_private_violation_workspace
    )
    write_accepted_to_draft_violation_workspace(
        plan.accepted_draft_violation_workspace
    )
    if dry_run:
        for step in plan.steps:
            print(step.display)
        return 0
    return run_ecosystem_smoke(plan)


def _network_skip_reason(include_network: bool, reason: str) -> str | None:
    return None if include_network else reason


def _run_verifier_evidence_eval_smoke(repo_root: Path) -> int:
    repo_root = repo_root.resolve()
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)

    from cosheaf.evals.verifier_evidence import (
        DEFAULT_VERIFIER_EVIDENCE_EVAL_CASES,
        load_verifier_evidence_eval_suite,
        run_verifier_evidence_eval_suite,
    )
    from cosheaf.storage.repo import RepoContext

    suite = load_verifier_evidence_eval_suite(
        repo_root / DEFAULT_VERIFIER_EVIDENCE_EVAL_CASES
    )
    with tempfile.TemporaryDirectory(prefix="cosheaf-verifier-eval-") as temp_dir:
        report = run_verifier_evidence_eval_suite(RepoContext(Path(temp_dir)), suite)
    print(report.to_json(), end="")
    return 0 if report.passed else 1


def _run_optional_verifier_availability_probe() -> int:
    optional_tools = ("kissat", "z3", "lean", "lake")
    available = tuple(tool for tool in optional_tools if shutil.which(tool))
    if available:
        print(
            "optional verifier tools available: "
            + ", ".join(available),
            file=sys.stderr,
        )
        return 0
    print(
        "optional verifier tools unavailable: kissat, z3, lean, lake; "
        "matrix row is skipped, not pass",
        file=sys.stderr,
    )
    return 77


def _run_matrix_command(
    argv: tuple[str, ...],
    cwd: Path,
    extra_env: dict[str, str] | None,
) -> int:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    print(f"[{cwd.name}] $ {' '.join(argv)}", file=sys.stderr, flush=True)
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        stdout=sys.stderr,
        stderr=sys.stderr,
        check=False,
    )
    return completed.returncode


def _print_matrix_plan(matrix: EcosystemSmokeMatrix) -> None:
    for case in matrix.cases:
        if case.skip_reason:
            print(f"[{case.repo}] {case.id}: skipped - {case.skip_reason}")
            continue
        for command in case.commands:
            print(f"[{case.repo}] {case.id}: {command.display}")


def _print_matrix_report(report: EcosystemSmokeMatrixReport) -> None:
    print(
        "Ecosystem smoke matrix: "
        f"pass={report.pass_count} fail={report.fail_count} "
        f"skipped={report.skip_count}"
    )
    for result in report.results:
        detail = result.message if result.message else result.command
        print(f"- {result.status.value}: {result.repo} {result.id}: {detail}")


def _write_workspace_config(workspace: Path) -> None:
    _write_text(
        workspace / "cosheaf.toml",
        "\n".join(
            [
                "[workspace]",
                'name = "ecosystem-smoke-workspace"',
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
    )


def _write_project_context(workspace: Path) -> None:
    _write_text(
        workspace / "context" / "PROJECT_STATE.md",
        "# Project State\n\n"
        "Local ecosystem smoke fixture. The public root is readonly, the "
        "private root is writable, and formal links are not proof checks.\n",
    )
    _write_text(
        workspace / "context" / "INTERFACE_REGISTRY.md",
        "# Interface Registry\n\n"
        "- `cosheaf workspace info`\n"
        "- `cosheaf validate`\n"
        "- `cosheaf gate run`\n"
        "- `cosheaf index rebuild`\n"
        "- `cosheaf context build <issue-id>`\n",
    )


def _write_issue(workspace: Path) -> None:
    _write_text(
        workspace / "issues" / "open" / f"{ISSUE_ID}.yaml",
        "\n".join(
            [
                f"id: {ISSUE_ID}",
                "type: issue",
                "title: Build context for a private ecosystem smoke claim",
                "status: open",
                'created_at: "2026-06-06T00:00:00Z"',
                'updated_at: "2026-06-06T00:00:00Z"',
                "authors:",
                "- release-engineering",
                "severity: low",
                "description: |",
                "  Exercise a private draft depending on readonly public",
                "  accepted knowledge in a local three-repository fixture.",
                "related_artifacts:",
                f"- {PRIVATE_ARTIFACT_ID}",
                "tags:",
                "- ecosystem-smoke",
                "- graph-theory",
                "",
            ]
        ),
    )


def _write_artifact(
    workspace: Path,
    relative_path: str,
    *,
    artifact_id: str,
    artifact_type: str,
    title: str,
    status: str,
    domain: tuple[str, ...],
    depends_on: tuple[str, ...],
    tags: tuple[str, ...],
    statement: str,
    evidence_path: str,
    evidence_summary: str,
    review_state: str,
    review_notes: str,
    risk_notes: str,
    sources: tuple[dict[str, object], ...] = (),
) -> None:
    lines = [
        f"id: {artifact_id}",
        f"type: {artifact_type}",
        f"title: {title}",
        "domain:",
        *(f"- {item}" for item in domain),
        f"status: {status}",
        'created_at: "2026-06-06T00:00:00Z"',
        'updated_at: "2026-06-06T00:00:00Z"',
        "authors:",
        "- release-engineering",
    ]
    lines.extend(
        ["depends_on:", *(f"- {dependency}" for dependency in depends_on)]
        if depends_on
        else ["depends_on: []"]
    )
    lines.extend(
        [
            "supersedes: []",
            "tags:",
            *(f"- {tag}" for tag in tags),
            f"statement: {statement}",
            "evidence:",
            "- kind: external",
            f"  path: {evidence_path}",
            f"  summary: {evidence_summary}",
        ]
    )
    if sources:
        lines.append("sources:")
        for source in sources:
            lines.extend(_source_lines(source))
    lines.extend(
        [
            "review:",
            f"  state: {review_state}",
            f"  notes: {review_notes}",
            "risk:",
            "  level: low",
            f"  notes: {risk_notes}",
            "",
        ]
    )
    _write_text(workspace / relative_path, "\n".join(lines))


def _source_lines(source: dict[str, object]) -> list[str]:
    authors = source.get("authors", [])
    if not isinstance(authors, list):
        raise TypeError("source authors must be a list")
    lines = [
        f"- kind: {_yaml_string(str(source['kind']))}",
        f"  title: {_yaml_string(str(source['title']))}",
        "  authors:",
        *(f"  - {_yaml_string(str(author))}" for author in authors),
        f"  year: {source['year']}",
    ]
    for key in ("doi", "arxiv", "url", "theorem_number", "page", "notes"):
        value = str(source.get(key, ""))
        lines.append(f"  {key}: {_yaml_string(value)}")
    return lines


def _yaml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
