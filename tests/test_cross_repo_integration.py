from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.core.artifact import BaseArtifact
from cosheaf.gates.gatekeeper import (
    GatekeeperReport,
    run_gatekeeper,
    validate_repository,
)
from cosheaf.gates.schema_gate import ValidationFailure
from cosheaf.storage.loader import load_artifacts
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "cross-repo-fixture"',
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


def _write_pr_template(repo_root: Path) -> None:
    _write_text(
        repo_root / ".github" / "pull_request_template.md",
        "\n".join(
            [
                "## Summary",
                "",
                "- Cross-repo fixture.",
                "",
                "## Changed Files",
                "",
                "- Cross-repo fixture.",
                "",
                "## Tests Run",
                "",
                "- [ ] `cosheaf validate`",
                "",
                "## Risks",
                "",
                "- Fixture only.",
                "",
                "## Interface Changes",
                "",
                "- None.",
                "",
                "## Documentation Changes",
                "",
                "- None.",
                "",
                "## Artifact/Schema Changes",
                "",
                "- None.",
                "",
                "## Gatekeeper Result",
                "",
                "- Pending.",
                "",
            ]
        ),
    )


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    status: str = "draft",
    depends_on: list[str] | None = None,
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": artifact_type,
        "title": f"Fixture {artifact_id}",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-04T00:00:00Z",
        "updated_at": "2026-06-04T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": ["cross-repo"],
        "statement": "A cross-repository integration fixture.",
        "evidence": [
            {
                "kind": "external",
                "path": "external:cross-repo-fixture",
                "summary": "Local deterministic fixture.",
            }
        ],
        "sources": sources or [],
        "review": {"state": "human_reviewed", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _source_fixture() -> dict[str, Any]:
    return {
        "kind": "paper",
        "title": "Cross Repo Source",
        "authors": ["A. Maintainer"],
        "year": 2026,
        "doi": "10.1145/cross-repo",
        "arxiv": "",
        "url": "",
        "theorem_number": "Definition 1",
        "page": "1",
        "notes": "Fixture source metadata.",
    }


def _write_valid_cross_repo_workspace(repo_root: Path) -> None:
    _write_workspace_config(repo_root)
    _write_pr_template(repo_root)
    _write_yaml(
        repo_root,
        "kb/public/accepted/definitions/definition.public.yaml",
        _artifact_data(
            "definition.public",
            artifact_type="definition",
            status="accepted",
            sources=[_source_fixture()],
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/claim.private.yaml",
        _artifact_data("claim.private", depends_on=["definition.public"]),
    )


def _failure_messages(failures: tuple[ValidationFailure, ...]) -> list[str]:
    return [failure.message for failure in failures]


def _gate_fingerprint(report: GatekeeperReport) -> tuple[object, ...]:
    return (
        report.verdict,
        tuple((gate.gate_id, gate.status, gate.summary) for gate in report.gates),
        tuple(
            (issue.gate_id, issue.artifact_id, issue.message)
            for issue in report.blocking_issues
        ),
        tuple(
            (issue.gate_id, issue.artifact_id, issue.message)
            for issue in report.nonblocking_issues
        ),
    )


def _write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8", newline="\n")


def test_private_artifact_can_depend_on_public_accepted_artifact(
    tmp_path: Path,
) -> None:
    _write_valid_cross_repo_workspace(tmp_path)
    context = RepoContext(tmp_path)

    report = validate_repository(context)
    records = {record.id: record for record in load_artifacts(context)}

    assert report.ok
    public_definition = records["definition.public"]
    private_claim = records["claim.private"]
    assert isinstance(public_definition.record, BaseArtifact)
    assert isinstance(private_claim.record, BaseArtifact)
    assert public_definition.kb_root_name == "public"
    assert public_definition.kb_root_readonly is True
    assert public_definition.record.status.value == "accepted"
    assert private_claim.kb_root_name == "private"
    assert private_claim.kb_root_readonly is False
    assert private_claim.record.depends_on == ["definition.public"]


def test_public_artifact_cannot_depend_on_private_artifact(tmp_path: Path) -> None:
    _write_valid_cross_repo_workspace(tmp_path)
    _write_yaml(
        tmp_path,
        "kb/public/draft/claims/claim.public-leak.yaml",
        _artifact_data("claim.public-leak", depends_on=["claim.private"]),
    )

    report = validate_repository(RepoContext(tmp_path))

    assert not report.ok
    assert any(
        "public artifact depends on private artifact: claim.private"
        in message
        for message in _failure_messages(report.failures)
    )


def test_accepted_artifact_cannot_depend_on_draft_artifact(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.draft-dependency.yaml",
        _artifact_data("claim.draft-dependency"),
    )
    _write_yaml(
        tmp_path,
        "kb/private/accepted/claims/claim.accepted-bad.yaml",
        _artifact_data(
            "claim.accepted-bad",
            status="accepted",
            depends_on=["claim.draft-dependency"],
        ),
    )

    report = validate_repository(RepoContext(tmp_path))

    assert not report.ok
    assert any(
        "accepted artifact depends on draft artifact: claim.draft-dependency"
        in message
        for message in _failure_messages(report.failures)
    )


def test_workspace_operations_refuse_to_write_readonly_public_root(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    source = _write_yaml(
        tmp_path,
        "kb/public/draft/claims/claim.public-draft.yaml",
        _artifact_data(
            "claim.public-draft",
            status="locally_tested",
            sources=[_source_fixture()],
        ),
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.public-draft",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "readonly KB root cannot be modified: public" in result.output
    assert source.is_file()
    assert not (
        tmp_path
        / "kb"
        / "public"
        / "accepted"
        / "claims"
        / "claim.public-draft.yaml"
    ).exists()


def test_validation_and_gate_fingerprints_are_stable_across_workspace_roots(
    tmp_path: Path,
) -> None:
    _write_valid_cross_repo_workspace(tmp_path)
    context = RepoContext(tmp_path)

    first_validation = validate_repository(context)
    second_validation = validate_repository(context)
    first_gate = run_gatekeeper(
        context,
        pr_checklist_path=Path(".github/pull_request_template.md"),
        timestamp="20260604T000000000000Z",
    ).report
    second_gate = run_gatekeeper(
        context,
        pr_checklist_path=Path(".github/pull_request_template.md"),
        timestamp="20260604T000000000001Z",
    ).report

    assert first_validation.ok
    assert second_validation.ok
    assert [record.id for record in first_validation.records] == [
        record.id for record in second_validation.records
    ]
    assert _gate_fingerprint(first_gate) == _gate_fingerprint(second_gate)
