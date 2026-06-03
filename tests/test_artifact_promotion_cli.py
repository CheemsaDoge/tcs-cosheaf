from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _write_workspace_config(
    repo_root: Path,
    *,
    public_readonly: bool = True,
) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "promotion-workspace"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                f"readonly = {str(public_readonly).lower()}",
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


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    status: str = "draft",
    review_state: str = "human_reviewed",
    depends_on: list[str] | None = None,
    evidence: list[dict[str, str]] | None = None,
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": artifact_type,
        "title": "Promotion fixture",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-03T00:00:00Z",
        "updated_at": "2026-06-03T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": ["promotion"],
        "statement": "A fixture for accepted promotion.",
        "evidence": evidence or [],
        "sources": sources or [],
        "review": {"state": review_state, "notes": "Promotion review evidence."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _source_fixture() -> dict[str, Any]:
    return {
        "kind": "paper",
        "title": "Promotion Source",
        "authors": ["A. Reviewer"],
        "year": 2026,
        "doi": "10.1145/promotion",
        "arxiv": "",
        "url": "",
        "theorem_number": "Claim 1",
        "page": "3",
        "notes": "Promotion source fixture.",
    }


def _issue_data(issue_id: str = "issue.fixture.promotion") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Promotion issue fixture",
        "status": "open",
        "created_at": "2026-06-03T00:00:00Z",
        "updated_at": "2026-06-03T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Issue records are not lifecycle artifacts.",
        "related_artifacts": [],
        "tags": ["promotion"],
    }


def _review_data(review_id: str = "review.fixture.promotion") -> dict[str, Any]:
    return {
        "id": review_id,
        "type": "review",
        "title": "Promotion review fixture",
        "status": "human_reviewed",
        "created_at": "2026-06-03T00:00:00Z",
        "updated_at": "2026-06-03T00:00:00Z",
        "authors": ["tester"],
        "target": "claim.fixture.target",
        "summary": "Review records are not lifecycle artifacts.",
        "findings": [],
        "decision": "approve",
    }


def _task_data(
    task_id: str = "task.issue.fixture.promotion.reasoner",
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "issue_id": "issue.fixture.promotion",
        "worker_type": "reasoner",
        "status": "open",
        "input_context": ["issues/open/issue.yaml"],
        "budget": {},
        "expected_outputs": [],
        "created_at": "2026-06-03T00:00:00Z",
        "updated_at": "2026-06-03T00:00:00Z",
    }


def _write_checker(repo_root: Path, body: str) -> None:
    path = repo_root / "experiments" / "evaluators" / "check_fixture.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_artifact_promote_moves_reviewed_artifact_to_accepted(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/accepted-dep.yaml",
        _artifact_data(
            "claim.fixture.accepted-dep",
            status="accepted",
            review_state="accepted",
        ),
    )
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.promote.yaml",
        _artifact_data(
            "claim.fixture.promote",
            status="locally_tested",
            depends_on=["claim.fixture.accepted-dep", "external:doi/10.0000/test"],
        ),
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.fixture.promote",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    target = tmp_path / "kb" / "accepted" / "claims" / "claim.fixture.promote.yaml"
    assert not source.exists()
    assert target.is_file()
    assert "Artifact promoted: claim.fixture.promote" in result.output
    assert "kb/accepted/claims/claim.fixture.promote.yaml" in result.output

    promoted = _read_yaml(target)
    assert list(promoted) == [
        "id",
        "type",
        "title",
        "domain",
        "status",
        "created_at",
        "updated_at",
        "authors",
        "depends_on",
        "supersedes",
        "tags",
        "statement",
        "evidence",
        "sources",
        "review",
        "risk",
    ]
    assert promoted["status"] == "accepted"
    assert promoted["review"]["state"] == "human_reviewed"
    assert datetime.fromisoformat(
        promoted["updated_at"].replace("Z", "+00:00")
    ) > datetime.fromisoformat("2026-06-03T00:00:00+00:00")


def test_artifact_promote_uses_current_writable_kb_root_in_workspace(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    source = _write_yaml(
        tmp_path,
        "kb/private/draft/claims/claim.fixture.promote.yaml",
        _artifact_data("claim.fixture.promote", status="locally_tested"),
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.fixture.promote",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    target = (
        tmp_path
        / "kb"
        / "private"
        / "accepted"
        / "claims"
        / "claim.fixture.promote.yaml"
    )
    assert not source.exists()
    assert target.is_file()
    assert "kb/private/accepted/claims/claim.fixture.promote.yaml" in result.output


def test_artifact_promote_refuses_readonly_kb_root_in_workspace(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    source = _write_yaml(
        tmp_path,
        "kb/public/draft/claims/claim.fixture.public.yaml",
        _artifact_data("claim.fixture.public", status="locally_tested"),
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.fixture.public",
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
        / "claim.fixture.public.yaml"
    ).exists()


def test_artifact_promote_refuses_public_artifact_without_source_metadata(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path, public_readonly=False)
    source = _write_yaml(
        tmp_path,
        "kb/public/draft/claims/claim.fixture.public.yaml",
        _artifact_data("claim.fixture.public", status="locally_tested"),
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.fixture.public",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "accepted public artifact requires source metadata" in result.output
    assert source.is_file()
    assert not (
        tmp_path
        / "kb"
        / "public"
        / "accepted"
        / "claims"
        / "claim.fixture.public.yaml"
    ).exists()


def test_artifact_promote_allows_public_artifact_with_source_metadata(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path, public_readonly=False)
    source = _write_yaml(
        tmp_path,
        "kb/public/draft/claims/claim.fixture.public.yaml",
        _artifact_data(
            "claim.fixture.public",
            status="locally_tested",
            sources=[_source_fixture()],
        ),
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.fixture.public",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    target = (
        tmp_path
        / "kb"
        / "public"
        / "accepted"
        / "claims"
        / "claim.fixture.public.yaml"
    )
    assert not source.exists()
    assert target.is_file()
    promoted = _read_yaml(target)
    assert promoted["sources"] == [_source_fixture()]


def test_artifact_promote_refuses_when_repository_validation_fails(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/target.yaml",
        _artifact_data("claim.fixture.target"),
    )
    _write_yaml(
        tmp_path,
        "kb/draft/claims/bad.yaml",
        _artifact_data("claim.fixture.bad", depends_on=["claim.fixture.missing"]),
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.fixture.target",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "repository validation failed before promotion" in result.output
    assert "missing dependency: claim.fixture.missing" in result.output
    assert not (tmp_path / "kb" / "accepted" / "claims" / "target.yaml").exists()


def test_artifact_promote_refuses_when_gatekeeper_has_blocking_issue(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/target.yaml",
        _artifact_data("claim.fixture.target"),
    )
    _write_yaml(
        tmp_path,
        "kb/draft/claims/other.yaml",
        _artifact_data(
            "claim.fixture.other",
            evidence=[
                {
                    "kind": "python_checker",
                    "path": "experiments/evaluators/check_fixture.py",
                    "summary": "Fails for another artifact.",
                }
            ],
        ),
    )
    _write_checker(tmp_path, "import sys\nsys.exit(7)\n")

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.fixture.target",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "gatekeeper blocking issues prevent promotion" in result.output
    assert "claim.fixture.other" in result.output


def test_artifact_promote_refuses_target_verifier_failures(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/target.yaml",
        _artifact_data(
            "claim.fixture.target",
            evidence=[
                {
                    "kind": "python_checker",
                    "path": "experiments/evaluators/check_fixture.py",
                    "summary": "Fails for target artifact.",
                }
            ],
        ),
    )
    _write_checker(tmp_path, "import sys\nsys.exit(3)\n")

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.fixture.target",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "target verifier result blocks promotion" in result.output
    assert "python_checker fail" in result.output


def test_artifact_promote_requires_reviewed_state(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/target.yaml",
        _artifact_data("claim.fixture.target", review_state="requested"),
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.fixture.target",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "review.state must be human_reviewed or accepted" in result.output


def test_artifact_promote_requires_accepted_or_external_dependencies(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/dependency.yaml",
        _artifact_data("claim.fixture.draft-dependency", status="draft"),
    )
    _write_yaml(
        tmp_path,
        "kb/draft/claims/target.yaml",
        _artifact_data(
            "claim.fixture.target",
            depends_on=["claim.fixture.draft-dependency"],
        ),
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.fixture.target",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "dependency is not accepted" in result.output
    assert "claim.fixture.draft-dependency" in result.output


@pytest.mark.parametrize(
    ("relative_path", "record_id", "data"),
    [
        ("issues/open/issue.yaml", "issue.fixture.promotion", _issue_data()),
        ("examples/reviews/review.yaml", "review.fixture.promotion", _review_data()),
        (
            "examples/tasks/task.yaml",
            "task.issue.fixture.promotion.reasoner",
            _task_data(),
        ),
    ],
)
def test_artifact_promote_refuses_non_lifecycle_records(
    tmp_path: Path,
    relative_path: str,
    record_id: str,
    data: dict[str, Any],
) -> None:
    _write_yaml(tmp_path, relative_path, data)

    result = runner.invoke(
        app,
        ["artifact", "promote", record_id, "--repo-root", str(tmp_path)],
    )

    assert result.exit_code != 0
    assert "record is not a promotable lifecycle artifact" in result.output
