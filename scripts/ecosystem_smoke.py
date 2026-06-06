from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ISSUE_ID = "issue.ecosystem-smoke.private-context"
PUBLIC_ARTIFACT_ID = "definition.ecosystem.graph"
PRIVATE_ARTIFACT_ID = "claim.ecosystem.private"


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
    args = parser.parse_args(argv)

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
