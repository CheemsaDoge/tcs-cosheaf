from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_artifact(
    repo_root: Path,
    relative_path: str,
    *,
    artifact_id: str,
    status: str = "draft",
    depends_on: list[str] | None = None,
    sources: list[dict[str, Any]] | None = None,
) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": "claim",
        "title": f"Claim {artifact_id}",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": [],
        "statement": "Test statement.",
        "evidence": [],
        "sources": sources or [],
        "review": {"state": "requested", "notes": "Test review."},
        "risk": {"level": "low", "notes": "Test risk."},
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _load_single_report(repo_root: Path) -> dict[str, Any]:
    json_reports = sorted(
        (repo_root / ".cosheaf" / "reports").glob("*-gate-report.json")
    )
    assert len(json_reports) == 1
    return cast(
        dict[str, Any],
        json.loads(json_reports[0].read_text(encoding="utf-8")),
    )


def _write_pr_checklist(
    repo_root: Path,
    *,
    missing_sections: set[str] | None = None,
) -> Path:
    missing = missing_sections or set()
    sections = [
        ("Summary", "Implements the requested gate behavior."),
        ("Changed Files", "- `cosheaf/gates/gatekeeper.py`"),
        ("Tests Run", "- [x] `make test`"),
        ("Risks", "None."),
        ("Interface Changes", "`cosheaf gate run --pr-checklist <path>`."),
        ("Documentation Changes", "`docs/GATES.md` updated."),
        ("Artifact/Schema Changes", "None."),
        (
            "Gatekeeper Result",
            "Gate verdict: pass\nJSON report: .cosheaf/reports/example.json",
        ),
    ]
    content = ["# Pull Request", ""]
    for title, body in sections:
        if title in missing:
            continue
        content.extend([f"## {title}", "", body, ""])

    path = repo_root / "PR_BODY.md"
    path.write_text("\n".join(content), encoding="utf-8")
    return path


def _write_workspace_config(
    repo_root: Path,
    *,
    accepted_requires_source: bool = True,
) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "source-policy-workspace"',
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
                f"accepted_requires_source = {str(accepted_requires_source).lower()}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _source_fixture() -> dict[str, Any]:
    return {
        "kind": "paper",
        "title": "A Source-Backed Theorem",
        "authors": ["A. Author", "B. Author"],
        "year": 2024,
        "doi": "10.1145/example",
        "arxiv": "2401.00001",
        "url": "https://example.org/source",
        "theorem_number": "Theorem 1.2",
        "page": "12",
        "notes": "Fixture source metadata.",
    }


def test_passing_repo_produces_pass_report(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Gate verdict: pass" in result.output
    report = _load_single_report(tmp_path)
    assert report["verdict"] == "pass"
    assert report["blocking_issues"] == []
    assert {"verdict", "blocking_issues", "nonblocking_issues", "summary"} <= set(
        report
    )
    assert {"started_at", "ended_at"} <= set(report)
    gate_statuses = {gate["id"]: gate["status"] for gate in report["gates"]}
    gate_summaries = {gate["id"]: gate["summary"] for gate in report["gates"]}
    assert gate_statuses["G6"] == "skipped"
    assert gate_statuses["G7"] == "not_applicable"
    assert gate_statuses["G8"] == "skipped"
    assert "No PR checklist source was provided" in gate_summaries["G8"]
    assert "pass" not in {gate_statuses["G6"], gate_statuses["G7"], gate_statuses["G8"]}
    assert not (tmp_path / "reviews" / "gatekeeper").exists()


def test_failing_repo_produces_fail_report_and_nonzero_exit(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
        depends_on=["claim.fixture.missing"],
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "Gate verdict: fail" in result.output
    assert "missing dependency" in result.output
    report = _load_single_report(tmp_path)
    assert report["verdict"] == "fail"
    assert report["blocking_issues"]
    assert report["blocking_issues"][0]["gate_id"] == "G4"


def test_markdown_report_exists(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0
    markdown_reports = sorted(
        (tmp_path / ".cosheaf" / "reports").glob("*-gate-report.md")
    )
    assert len(markdown_reports) == 1
    assert "# Gatekeeper Report" in markdown_reports[0].read_text(encoding="utf-8")


def test_persist_review_writes_reviews_gatekeeper(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
    )

    result = runner.invoke(
        app,
        ["gate", "run", "--repo-root", str(tmp_path), "--persist-review"],
    )

    assert result.exit_code == 0
    review_reports = sorted(
        (tmp_path / "reviews" / "gatekeeper").glob("*-gate-report.json")
    )
    assert len(review_reports) == 1
    review_report = json.loads(review_reports[0].read_text(encoding="utf-8"))
    assert review_report["verdict"] == "pass"


def test_pr_checklist_gate_passes_with_required_sections(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
    )
    checklist = _write_pr_checklist(tmp_path)

    result = runner.invoke(
        app,
        [
            "gate",
            "run",
            "--repo-root",
            str(tmp_path),
            "--pr-checklist",
            str(checklist),
        ],
    )

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    g8 = next(gate for gate in report["gates"] if gate["id"] == "G8")
    assert g8["status"] == "pass"
    assert "PR checklist includes all 8 required section(s)." == g8["summary"]
    assert g8["details"] == [
        {
            "source_path": "PR_BODY.md",
            "required_sections": [
                "summary",
                "changed files",
                "tests run",
                "risks",
                "interface changes",
                "documentation changes",
                "artifact/schema changes",
                "gatekeeper result",
            ],
            "missing_sections": [],
        }
    ]


def test_pr_checklist_gate_fails_when_required_sections_missing(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
    )
    checklist = _write_pr_checklist(
        tmp_path,
        missing_sections={"Risks", "Gatekeeper Result"},
    )

    result = runner.invoke(
        app,
        [
            "gate",
            "run",
            "--repo-root",
            str(tmp_path),
            "--pr-checklist",
            str(checklist),
        ],
    )

    assert result.exit_code != 0
    assert "Gate verdict: fail" in result.output
    assert "missing PR checklist section: risks" in result.output
    assert "missing PR checklist section: gatekeeper result" in result.output
    report = _load_single_report(tmp_path)
    g8 = next(gate for gate in report["gates"] if gate["id"] == "G8")
    assert g8["status"] == "fail"
    assert g8["summary"] == "2 required PR checklist section(s) missing."
    assert [issue["gate_id"] for issue in g8["blocking_issues"]] == ["G8", "G8"]
    assert [issue["message"] for issue in g8["blocking_issues"]] == [
        "missing PR checklist section: risks",
        "missing PR checklist section: gatekeeper result",
    ]


def test_source_metadata_gate_passes_for_accepted_public_artifact_with_source(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/claims/claim.fixture.public.yaml",
        artifact_id="claim.fixture.public",
        status="accepted",
        sources=[_source_fixture()],
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    g9 = next(gate for gate in report["gates"] if gate["id"] == "G9")
    assert g9["status"] == "pass"
    assert g9["details"] == [
        {
            "artifact_id": "claim.fixture.public",
            "source_path": "kb/public/accepted/claims/claim.fixture.public.yaml",
            "kb_root": "public",
            "status": "pass",
            "source_count": 1,
            "missing_metadata": [],
        }
    ]


def test_source_metadata_gate_fails_for_accepted_public_artifact_without_source(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/claims/claim.fixture.public.yaml",
        artifact_id="claim.fixture.public",
        status="accepted",
        depends_on=["external:doi/10.1145/not-a-source"],
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    report = _load_single_report(tmp_path)
    g9 = next(gate for gate in report["gates"] if gate["id"] == "G9")
    assert g9["status"] == "fail"
    assert g9["blocking_issues"] == [
        {
            "gate_id": "G9",
            "gate_name": "source metadata gate",
            "source_path": "kb/public/accepted/claims/claim.fixture.public.yaml",
            "artifact_id": "claim.fixture.public",
            "message": "accepted public artifact requires source metadata",
            "severity": "blocking",
        }
    ]


def test_source_metadata_gate_fails_for_incomplete_accepted_public_source(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    source = _source_fixture()
    source["title"] = ""
    _write_artifact(
        tmp_path,
        "kb/public/accepted/claims/claim.fixture.public.yaml",
        artifact_id="claim.fixture.public",
        status="accepted",
        sources=[source],
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    report = _load_single_report(tmp_path)
    g9 = next(gate for gate in report["gates"] if gate["id"] == "G9")
    assert g9["blocking_issues"][0]["message"] == (
        "incomplete source metadata: source[0].title"
    )


def test_source_metadata_gate_ignores_draft_public_artifact_without_source(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/draft/claims/claim.fixture.public.yaml",
        artifact_id="claim.fixture.public",
        status="draft",
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    g9 = next(gate for gate in report["gates"] if gate["id"] == "G9")
    assert g9["status"] == "not_applicable"
    assert g9["summary"] == "No accepted public artifacts require source metadata."


def test_source_metadata_gate_allows_private_accepted_artifact_without_source(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/private/accepted/claims/claim.fixture.private.yaml",
        artifact_id="claim.fixture.private",
        status="accepted",
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    g9 = next(gate for gate in report["gates"] if gate["id"] == "G9")
    assert g9["status"] == "not_applicable"


def test_source_metadata_gate_preserves_legacy_single_root_behavior(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/claim.fixture.legacy.yaml",
        artifact_id="claim.fixture.legacy",
        status="accepted",
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    g9 = next(gate for gate in report["gates"] if gate["id"] == "G9")
    assert g9["status"] == "not_applicable"
    assert (
        "Legacy single-root mode has no public KB root; "
        "source metadata policy is not enforced."
    ) == g9["summary"]


def test_source_metadata_gate_output_is_deterministic(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/claims/b.yaml",
        artifact_id="claim.fixture.b",
        status="accepted",
    )
    _write_artifact(
        tmp_path,
        "kb/public/accepted/claims/a.yaml",
        artifact_id="claim.fixture.a",
        status="accepted",
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    report = _load_single_report(tmp_path)
    g9 = next(gate for gate in report["gates"] if gate["id"] == "G9")
    assert [detail["artifact_id"] for detail in g9["details"]] == [
        "claim.fixture.a",
        "claim.fixture.b",
    ]
    assert [issue["artifact_id"] for issue in g9["blocking_issues"]] == [
        "claim.fixture.a",
        "claim.fixture.b",
    ]

