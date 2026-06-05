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
    formalizations: list[dict[str, Any]] | None = None,
    alignment: dict[str, Any] | None = None,
    verification_policy: dict[str, Any] | None = None,
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
    if formalizations is not None:
        data["formalizations"] = formalizations
    if alignment is not None:
        data["alignment"] = alignment
    if verification_policy is not None:
        data["verification_policy"] = verification_policy
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


def _write_issue_record(repo_root: Path, relative_path: str, issue_id: str) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "id": issue_id,
        "type": "issue",
        "title": f"Issue {issue_id}",
        "status": "open",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Test issue.",
        "related_artifacts": [],
        "tags": ["testing"],
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


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


def _formalization_fixture(
    *,
    formalization_id: str = "cslib.fixture.link",
    status: str = "planned",
    check_mode: str = "external_library_ref",
) -> dict[str, Any]:
    return {
        "id": formalization_id,
        "system": "lean4",
        "library": "CSLib",
        "library_ref": "cslib-main",
        "import_path": "CSLib.Graph.Basic",
        "symbol": "CSLib.Graph.Basic.fixture_symbol",
        "declaration_kind": "theorem",
        "status": status,
        "check_mode": check_mode,
        "expected_type": "Fixture Lean type.",
        "notes": "Static gate test fixture.",
    }


def _formal_link_policy(
    *,
    level: str = "source_reviewed_with_formal_link",
    require_formal_link: bool = True,
    require_lean_check: bool = False,
    require_alignment_review: bool = False,
) -> dict[str, Any]:
    return {
        "level": level,
        "require_formal_link": require_formal_link,
        "require_lean_check": require_lean_check,
        "require_alignment_review": require_alignment_review,
    }


def _human_reviewed_alignment() -> dict[str, Any]:
    return {
        "status": "human_reviewed",
        "reviewer": "reviewer@example.org",
        "reviewed_at": "2026-06-01T00:00:00Z",
        "convention_notes": ["Fixture conventions match."],
        "limitations": "",
    }


def _gate_by_id(report: dict[str, Any], gate_id: str) -> dict[str, Any]:
    return next(gate for gate in report["gates"] if gate["id"] == gate_id)


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


def test_formal_link_gate_default_artifact_is_not_applicable(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.default-formal-policy",
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    g10 = _gate_by_id(report, "G10")
    assert g10["status"] == "not_applicable"
    assert g10["blocking_issues"] == []
    assert g10["nonblocking_issues"] == []


def test_formal_link_gate_ignores_non_artifact_records(tmp_path: Path) -> None:
    _write_issue_record(
        tmp_path,
        "issues/open/issue.fixture.yaml",
        "issue.fixture.formal-link",
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    g10 = _gate_by_id(report, "G10")
    assert g10["status"] == "not_applicable"
    assert g10["details"] == []


def test_formal_link_gate_passes_required_planned_link(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.formal-link",
        formalizations=[_formalization_fixture()],
        verification_policy=_formal_link_policy(),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    g10 = _gate_by_id(report, "G10")
    assert g10["status"] == "pass"
    assert g10["blocking_issues"] == []
    assert g10["nonblocking_issues"] == []
    assert g10["details"][0]["artifact_id"] == "claim.fixture.formal-link"
    assert g10["details"][0]["formalization_count"] == 1


def test_formal_link_gate_passes_required_alignment_review(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.reviewed-alignment",
        formalizations=[_formalization_fixture()],
        alignment=_human_reviewed_alignment(),
        verification_policy=_formal_link_policy(require_alignment_review=True),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    g10 = _gate_by_id(_load_single_report(tmp_path), "G10")
    assert g10["status"] == "pass"
    assert g10["blocking_issues"] == []


def test_formal_link_gate_passes_required_checked_formalization(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.checked-formalization",
        formalizations=[
            _formalization_fixture(
                status="checked",
                check_mode="local_file",
            )
        ],
        verification_policy=_formal_link_policy(
            level="machine_checked",
            require_lean_check=True,
        ),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    g10 = _gate_by_id(_load_single_report(tmp_path), "G10")
    assert g10["status"] == "pass"
    assert g10["blocking_issues"] == []


def test_formal_link_gate_fails_required_link_without_formalizations(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.missing-formal-link",
        verification_policy=_formal_link_policy(),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "Gate verdict: fail" in result.output
    assert "requires a" in result.output
    assert "formal link but has no formalizations" in result.output
    report = _load_single_report(tmp_path)
    g10 = _gate_by_id(report, "G10")
    assert g10["status"] == "fail"
    assert g10["blocking_issues"] == [
        {
            "gate_id": "G10",
            "gate_name": "formal link gate",
            "source_path": "examples/claims/a.yaml",
            "artifact_id": "claim.fixture.missing-formal-link",
            "message": (
                "verification_policy requires a formal link but has no "
                "formalizations"
            ),
            "severity": "blocking",
        }
    ]


def test_formal_link_gate_fails_required_alignment_without_human_review(
    tmp_path: Path,
) -> None:
    for alignment_status in ("none", "requested", "rejected"):
        repo_root = tmp_path / alignment_status
        alignment: dict[str, Any] = {
            "status": alignment_status,
            "reviewer": (
                "reviewer@example.org"
                if alignment_status == "rejected"
                else ""
            ),
            "reviewed_at": None,
            "convention_notes": [],
            "limitations": "",
        }
        _write_artifact(
            repo_root,
            "examples/claims/a.yaml",
            artifact_id=f"claim.fixture.alignment-{alignment_status}",
            formalizations=[_formalization_fixture()],
            alignment=alignment,
            verification_policy=_formal_link_policy(
                require_alignment_review=True,
            ),
        )

        result = runner.invoke(
            app,
            ["gate", "run", "--repo-root", str(repo_root)],
        )

        assert result.exit_code != 0
        report = _load_single_report(repo_root)
        g10 = _gate_by_id(report, "G10")
        assert g10["status"] == "fail"
        assert g10["blocking_issues"][0]["message"] == (
            "verification_policy requires alignment review but "
            f"alignment.status is {alignment_status}"
        )


def test_formal_link_gate_fails_required_lean_check_without_checked_link(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.no-checked-formalization",
        formalizations=[_formalization_fixture(status="linked")],
        verification_policy=_formal_link_policy(
            level="machine_checked",
            require_lean_check=True,
        ),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    report = _load_single_report(tmp_path)
    g10 = _gate_by_id(report, "G10")
    assert g10["status"] == "fail"
    assert g10["blocking_issues"][0]["message"] == (
        "verification_policy requires a Lean check but no formalization is checked"
    )


def test_formal_link_gate_fails_accepted_rejected_alignment(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/claim.fixture.accepted.yaml",
        artifact_id="claim.fixture.accepted-rejected-alignment",
        status="accepted",
        formalizations=[_formalization_fixture()],
        alignment={
            "status": "rejected",
            "reviewer": "reviewer@example.org",
            "reviewed_at": "2026-06-01T00:00:00Z",
            "convention_notes": [],
            "limitations": "Conventions do not match.",
        },
        verification_policy=_formal_link_policy(),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    g10 = _gate_by_id(_load_single_report(tmp_path), "G10")
    assert g10["status"] == "fail"
    assert g10["blocking_issues"][0]["message"] == (
        "accepted artifact has rejected formal alignment"
    )


def test_formal_link_gate_fails_accepted_lean_required_without_checked_link(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/claim.fixture.accepted.yaml",
        artifact_id="claim.fixture.accepted-lean-required",
        status="accepted",
        formalizations=[_formalization_fixture(status="linked")],
        verification_policy=_formal_link_policy(
            level="lean_required",
            require_lean_check=True,
        ),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    g10 = _gate_by_id(_load_single_report(tmp_path), "G10")
    assert g10["blocking_issues"][0]["message"] == (
        "verification_policy requires a Lean check but no formalization is checked"
    )


def test_formal_link_gate_warns_for_planned_formalization_on_accepted_artifact(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/claim.fixture.accepted.yaml",
        artifact_id="claim.fixture.accepted-planned-link",
        status="accepted",
        formalizations=[_formalization_fixture(status="planned")],
        verification_policy=_formal_link_policy(),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    g10 = _gate_by_id(report, "G10")
    assert g10["status"] == "pass"
    assert report["verdict"] == "pass"
    assert g10["nonblocking_issues"][0]["message"] == (
        "accepted artifact has a planned formalization"
    )


def test_formal_link_gate_fails_when_required_link_is_only_broken(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.only-broken-formal-link",
        formalizations=[_formalization_fixture(status="broken")],
        verification_policy=_formal_link_policy(),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    g10 = _gate_by_id(_load_single_report(tmp_path), "G10")
    assert g10["status"] == "fail"
    assert g10["blocking_issues"][0]["message"] == (
        "formalization cslib.fixture.link has status broken"
    )


def test_formal_link_gate_warns_for_broken_link_when_valid_link_exists(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.broken-with-valid-link",
        formalizations=[
            _formalization_fixture(
                formalization_id="cslib.fixture.broken",
                status="broken",
            ),
            _formalization_fixture(
                formalization_id="cslib.fixture.planned",
                status="planned",
            ),
        ],
        verification_policy=_formal_link_policy(),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    g10 = _gate_by_id(_load_single_report(tmp_path), "G10")
    assert g10["status"] == "pass"
    assert g10["nonblocking_issues"][0]["message"] == (
        "formalization cslib.fixture.broken has status broken"
    )


def test_formal_link_gate_warns_for_checked_external_library_reference(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.checked-external-link",
        formalizations=[_formalization_fixture(status="checked")],
        verification_policy=_formal_link_policy(
            level="machine_checked",
            require_lean_check=True,
        ),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    g10 = _gate_by_id(_load_single_report(tmp_path), "G10")
    assert g10["status"] == "pass"
    assert g10["nonblocking_issues"][0]["message"] == (
        "formalization cslib.fixture.link is checked through "
        "external_library_ref without verifier evidence linkage"
    )


def test_formal_link_gate_warns_when_link_present_but_policy_not_required(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.unrequired-formal-link",
        formalizations=[_formalization_fixture()],
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    g10 = _gate_by_id(report, "G10")
    assert g10["status"] == "pass"
    assert report["verdict"] == "pass"
    assert g10["nonblocking_issues"][0]["message"] == (
        "formalizations are present but verification_policy does not "
        "require a formal link"
    )


def test_formal_link_gate_reports_are_written_to_json_and_markdown(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.reported-formal-link",
        formalizations=[_formalization_fixture()],
        verification_policy=_formal_link_policy(),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _load_single_report(tmp_path)
    assert _gate_by_id(report, "G10")["name"] == "formal link gate"
    markdown_report = next((tmp_path / ".cosheaf" / "reports").glob("*.md"))
    assert "G10 formal link gate: pass" in markdown_report.read_text(
        encoding="utf-8"
    )

