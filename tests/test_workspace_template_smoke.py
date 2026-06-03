from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.config.workspace import load_workspace_config
from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.loader import load_artifacts
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_workspace_template_fixture(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "my-tcs-workspace"',
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
        encoding="utf-8",
    )
    _write_pr_template(repo_root)
    _write_artifact(
        repo_root,
        "kb/public/definitions/definition.graph.yaml",
        artifact_id="definition.graph",
        artifact_type="definition",
        title="Graph",
        authors=["TCS-Cosheaf contributors"],
        depends_on=[],
        tags=["seed", "bootstrap"],
        statement="A graph is a mathematical object with vertices and edges.",
        evidence_path="external:standard-graph-theory-textbook",
        evidence_summary="Standard public graph theory terminology.",
        review_notes="Tiny public bootstrap seed for workspace template validation.",
        risk_notes="Informal seed definition; not accepted knowledge.",
    )
    _write_artifact(
        repo_root,
        "kb/private/claims/claim.example-private.yaml",
        artifact_id="claim.example-private",
        artifact_type="claim",
        title="Example private draft",
        authors=["workspace-user"],
        depends_on=["definition.graph"],
        tags=["private", "example"],
        statement=(
            "This private draft example depends on the public graph definition "
            "seed and does not claim novelty."
        ),
        evidence_path="external:workspace-template-example",
        evidence_summary=(
            "Template-only private draft example; not an accepted research claim."
        ),
        review_notes="Example private draft artifact for workspace onboarding.",
        risk_notes="Draft-only template example; no novelty is claimed.",
    )


def _write_pr_template(repo_root: Path) -> Path:
    path = repo_root / ".github" / "pull_request_template.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "## Summary",
                "",
                "- TODO",
                "",
                "## Changed Files",
                "",
                "- TODO",
                "",
                "## Tests Run",
                "",
                "- [ ] `cosheaf workspace info`",
                "- [ ] `cosheaf validate`",
                "- [ ] `cosheaf gate run`",
                "- [ ] `cosheaf gate run --pr-checklist "
                ".github/pull_request_template.md`",
                "",
                "## Risks",
                "",
                "- TODO",
                "",
                "## Interface Changes",
                "",
                "- TODO",
                "",
                "## Documentation Changes",
                "",
                "- TODO",
                "",
                "## Artifact/Schema Changes",
                "",
                "- TODO",
                "",
                "## Gatekeeper Result",
                "",
                "- TODO",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_artifact(
    repo_root: Path,
    relative_path: str,
    *,
    artifact_id: str,
    artifact_type: str,
    title: str,
    authors: list[str],
    depends_on: list[str],
    tags: list[str],
    statement: str,
    evidence_path: str,
    evidence_summary: str,
    review_notes: str,
    risk_notes: str,
) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"id: {artifact_id}",
        f"type: {artifact_type}",
        f"title: {title}",
        "domain:",
        "- graph-theory",
        "status: draft",
        "created_at: 2026-06-03T00:00:00Z",
        "updated_at: 2026-06-03T00:00:00Z",
        "authors:",
        *(f"- {author}" for author in authors),
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
            "review:",
            "  state: requested",
            f"  notes: {review_notes}",
            "risk:",
            "  level: low",
            f"  notes: {risk_notes}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _latest_gate_report(repo_root: Path) -> dict[str, Any]:
    json_reports = sorted(
        (repo_root / ".cosheaf" / "reports").glob("*-gate-report.json")
    )
    assert json_reports
    return cast(
        dict[str, Any],
        json.loads(json_reports[-1].read_text(encoding="utf-8")),
    )


def test_workspace_template_fixture_exercises_core_cli_flow(
    tmp_path: Path,
) -> None:
    _write_workspace_template_fixture(tmp_path)

    config = load_workspace_config(tmp_path)
    records = {record.id: record for record in load_artifacts(RepoContext(tmp_path))}

    assert config.configured is True
    assert config.name == "my-tcs-workspace"
    assert [
        (root.name, root.path, root.readonly, root.priority)
        for root in config.ordered_kb
    ] == [
        ("public", "kb/public", True, 10),
        ("private", "kb/private", False, 20),
    ]
    assert config.policy.private_can_depend_on_public is True
    assert config.policy.public_can_depend_on_private is False
    assert config.policy.accepted_requires_source is True

    public_seed = records["definition.graph"]
    private_claim = records["claim.example-private"]
    assert isinstance(public_seed.record, BaseArtifact)
    assert isinstance(private_claim.record, BaseArtifact)
    assert public_seed.kb_root_name == "public"
    assert public_seed.kb_root_readonly is True
    assert public_seed.source_path.as_posix() == (
        "kb/public/definitions/definition.graph.yaml"
    )
    assert private_claim.kb_root_name == "private"
    assert private_claim.kb_root_readonly is False
    assert private_claim.record.depends_on == ["definition.graph"]
    assert private_claim.record.status.value == "draft"

    workspace_info = runner.invoke(
        app, ["workspace", "info", "--repo-root", str(tmp_path)]
    )
    assert workspace_info.exit_code == 0, workspace_info.output
    assert "Workspace: my-tcs-workspace" in workspace_info.output
    assert "public | kb/public | readonly=true | priority=10" in workspace_info.output
    assert (
        "private | kb/private | readonly=false | priority=20"
        in workspace_info.output
    )

    validate = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])
    assert validate.exit_code == 0, validate.output
    assert "Validation passed: checked 2 YAML record(s)." in validate.output

    gate = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])
    assert gate.exit_code == 0, gate.output
    report = _latest_gate_report(tmp_path)
    gate_statuses = {gate["id"]: gate["status"] for gate in report["gates"]}
    assert report["verdict"] == "pass"
    assert gate_statuses["G6"] == "skipped"
    assert gate_statuses["G7"] == "not_applicable"
    assert gate_statuses["G8"] == "skipped"
    assert gate_statuses["G9"] == "not_applicable"

    checklist_gate = runner.invoke(
        app,
        [
            "gate",
            "run",
            "--repo-root",
            str(tmp_path),
            "--pr-checklist",
            ".github/pull_request_template.md",
        ],
    )
    assert checklist_gate.exit_code == 0, checklist_gate.output
    checklist_report = _latest_gate_report(tmp_path)
    checklist_statuses = {
        gate["id"]: gate["status"] for gate in checklist_report["gates"]
    }
    assert checklist_report["verdict"] == "pass"
    assert checklist_statuses["G8"] == "pass"


def test_workspace_template_fixture_rejects_public_dependency_on_private(
    tmp_path: Path,
) -> None:
    _write_workspace_template_fixture(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/claims/claim.public-leak.yaml",
        artifact_id="claim.public-leak",
        artifact_type="claim",
        title="Public leak",
        authors=["tester"],
        depends_on=["claim.example-private"],
        tags=["public"],
        statement="A public draft that incorrectly depends on private work.",
        evidence_path="external:workspace-template-negative-fixture",
        evidence_summary="Negative fixture for dependency direction.",
        review_notes="Negative fixture.",
        risk_notes="Negative fixture.",
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "public artifact depends on private" in result.output
    assert "artifact: claim.example-private" in result.output
    assert "claim.public-leak" in result.output
    assert "claim.example-private" in result.output
