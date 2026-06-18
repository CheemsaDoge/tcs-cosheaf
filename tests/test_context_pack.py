from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

import cosheaf.context_cli as context_cli
from cosheaf.agent.context_pack import ContextPackError, build_context_pack
from cosheaf.cli import app
from cosheaf.memory import RetrievalRole
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_context_docs(repo_root: Path) -> None:
    context_dir = repo_root / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    (context_dir / "PROJECT_STATE.md").write_text(
        "# Project State\n\nCurrent state for tests.\n",
        encoding="utf-8",
    )
    (context_dir / "INTERFACE_REGISTRY.md").write_text(
        "# Interface Registry\n\n- `cosheaf context build <issue-id>`\n",
        encoding="utf-8",
    )


def _artifact_data(
    artifact_id: str,
    *,
    status: str,
    title: str | None = None,
    domain: list[str] | None = None,
    depends_on: list[str] | None = None,
    tags: list[str] | None = None,
    statement: str = "A bounded context-pack fixture.",
    formalizations: list[dict[str, Any]] | None = None,
    alignment: dict[str, Any] | None = None,
    verification_policy: dict[str, Any] | None = None,
    failure_log: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": "claim",
        "title": title or f"Claim {artifact_id}",
        "domain": domain or ["testing"],
        "status": status,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": tags or [],
        "statement": statement,
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }
    if formalizations is not None:
        data["formalizations"] = formalizations
    if alignment is not None:
        data["alignment"] = alignment
    if verification_policy is not None:
        data["verification_policy"] = verification_policy
    if failure_log is not None:
        data["failure_log"] = failure_log
    return data


def _failure_log_entry(
    *,
    failure_id: str = "failure.fixture.0001",
    direction: str = "Try a separator induction on the bad component",
    failed_because: str = "The separator premise is unavailable for the draft.",
    next_possible_directions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "failure_id": failure_id,
        "attempted_at": "2026-06-02T00:00:00Z",
        "recorded_by": "tester",
        "origin": "human",
        "attempt_kind": "proof_attempt",
        "target": "",
        "direction": direction,
        "summary": "Fixture failed attempt memory.",
        "failed_because": failed_because,
        "evidence_paths": [],
        "related_verifier_results": [],
        "related_counterexample_candidates": [],
        "next_possible_directions": next_possible_directions or [],
        "status": "open",
        "limitations": "Failure memory only; not proof or refutation.",
    }


def _formalization_fixture(
    *,
    formalization_id: str = "cslib.fixture.link",
    library: str = "CSLib",
    library_ref: str = "cslib-main",
    import_path: str = "CSLib.Graph.Basic",
    symbol: str = "CSLib.Graph.Basic.fixture_symbol",
    status: str = "planned",
) -> dict[str, Any]:
    return {
        "id": formalization_id,
        "system": "lean4",
        "library": library,
        "library_ref": library_ref,
        "import_path": import_path,
        "symbol": symbol,
        "declaration_kind": "theorem",
        "status": status,
        "check_mode": "external_library_ref",
        "expected_type": "Fixture Lean type.",
        "notes": "Fixture formalization link.",
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


def _issue_data(
    issue_id: str = "issue.fixture.context",
    related_artifacts: list[str] | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Build a bounded context pack",
        "status": "open",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": description
        or (
            "The task needs a short, deterministic handoff.\n"
            "- Include accepted background before draft material.\n"
            "- Mark draft artifacts visibly.\n"
        ),
        "related_artifacts": related_artifacts or [
            "claim.fixture.accepted",
            "claim.fixture.draft",
            "claim.fixture.refuted",
        ],
        "tags": tags or ["context-pack"],
    }


def _write_repo(repo_root: Path) -> None:
    _write_context_docs(repo_root)
    _write_yaml(repo_root, "issues/open/issue.yaml", _issue_data())
    _write_yaml(
        repo_root,
        "kb/accepted/claims/accepted.yaml",
        _artifact_data(
            "claim.fixture.accepted",
            status="accepted",
            title="Accepted claim",
        ),
    )
    _write_yaml(
        repo_root,
        "kb/draft/claims/draft.yaml",
        _artifact_data("claim.fixture.draft", status="draft", title="Draft claim"),
    )
    _write_yaml(
        repo_root,
        "kb/refuted/refuted.yaml",
        _artifact_data(
            "claim.fixture.refuted",
            status="refuted",
            title="Refuted claim",
        ),
    )
    _write_yaml(
        repo_root,
        "kb/draft/claims/unrelated.yaml",
        _artifact_data(
            "claim.fixture.unrelated",
            status="draft",
            title="Unrelated claim",
        ),
    )


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "context-pack-workspace"',
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


def test_context_pack_files_created(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    result = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    assert result.issue_id == "issue.fixture.context"
    assert result.task_dir == tmp_path / "context" / "TASKS" / "issue.fixture.context"
    expected_names = {
        "CONTEXT.md",
        "ACCEPTANCE.md",
        "RELEVANT_ARTIFACTS.md",
        "KNOWN_FAILURES.md",
        "COMMANDS.md",
        "RETRIEVAL_AUDIT.json",
        "FULL_ARTIFACTS.md",
    }
    assert {path.name for path in result.files} == expected_names
    for path in result.files:
        assert path.exists()


def test_context_pack_output_is_deterministic(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    first = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")
    first_contents = {
        path.name: path.read_text(encoding="utf-8") for path in first.files
    }
    second = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")
    second_contents = {
        path.name: path.read_text(encoding="utf-8") for path in second.files
    }

    assert second_contents == first_contents


def test_context_pack_v2_uses_cards_and_audit_by_default(tmp_path: Path) -> None:
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/card-audit.yaml",
        _issue_data(
            related_artifacts=["claim.fixture.accepted"],
            description="Need graph card context.",
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/accepted.yaml",
        _artifact_data(
            "claim.fixture.accepted",
            status="accepted",
            title="Accepted card source",
            domain=["graph-theory"],
            tags=["graph"],
            statement="SECRET FULL STATEMENT SHOULD NOT APPEAR BY DEFAULT",
        ),
    )

    result = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    context_md = (result.task_dir / "CONTEXT.md").read_text(encoding="utf-8")
    audit = json.loads((result.task_dir / "RETRIEVAL_AUDIT.json").read_text())
    full_artifacts = (result.task_dir / "FULL_ARTIFACTS.md").read_text(
        encoding="utf-8"
    )

    assert "## Relevant Artifact Cards" in context_md
    assert "claim.fixture.accepted | Accepted card source | accepted" in context_md
    assert "score:" in context_md
    assert "root_scope=workspace" in context_md
    assert "SECRET FULL STATEMENT" not in context_md
    assert "SECRET FULL STATEMENT" not in full_artifacts
    assert audit["request"]["role"] == "orchestrator"
    assert audit["request"]["max_full_artifacts"] == 0
    assert audit["context_payload"] == {
        "card_count": 1,
        "full_artifact_count": 0,
        "failure_entry_count": 0,
        "checked_counterexample_evidence_count": 0,
        "content_mode": "cards_only",
    }
    assert audit["full_artifact_pulls"] == []


def test_context_pack_worker_role_can_pull_bounded_full_artifacts(
    tmp_path: Path,
) -> None:
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/full-artifact.yaml",
        _issue_data(
            related_artifacts=["claim.fixture.full-a", "claim.fixture.full-b"],
            description="Need graph verifier context.",
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/full-a.yaml",
        _artifact_data(
            "claim.fixture.full-a",
            status="accepted",
            title="First full artifact",
            domain=["graph-theory"],
            tags=["graph"],
            statement="SECRET FULL STATEMENT A",
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/full-b.yaml",
        _artifact_data(
            "claim.fixture.full-b",
            status="accepted",
            title="Second full artifact",
            domain=["graph-theory"],
            tags=["graph"],
            statement="SECRET FULL STATEMENT B",
        ),
    )

    result = build_context_pack(
        RepoContext(tmp_path),
        "issue.fixture.context",
        role=RetrievalRole.VERIFIER,
        max_full_artifacts=1,
    )

    full_artifacts = (result.task_dir / "FULL_ARTIFACTS.md").read_text(
        encoding="utf-8"
    )
    audit = json.loads((result.task_dir / "RETRIEVAL_AUDIT.json").read_text())

    assert "SECRET FULL STATEMENT A" in full_artifacts
    assert "SECRET FULL STATEMENT B" not in full_artifacts
    assert [pull["artifact_id"] for pull in audit["full_artifact_pulls"]] == [
        "claim.fixture.full-a"
    ]
    assert audit["context_payload"] == {
        "card_count": 2,
        "full_artifact_count": 1,
        "failure_entry_count": 0,
        "checked_counterexample_evidence_count": 0,
        "content_mode": "cards_with_full_artifacts",
    }
    assert "role=verifier" in audit["full_artifact_pulls"][0]["reason"]
    assert "policy_scope=workspace" in audit["full_artifact_pulls"][0]["reason"]
    assert audit["request"]["role"] == "verifier"
    assert audit["request"]["max_full_artifacts"] == 1


def test_context_pack_public_only_does_not_leak_private_cards(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/private.yaml",
        _issue_data(
            related_artifacts=[
                "definition.fixture.public-graph",
                "claim.fixture.private-graph",
            ],
            description="Need graph context.",
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/public/accepted/definitions/public-graph.yaml",
        _artifact_data(
            "definition.fixture.public-graph",
            status="accepted",
            title="Public graph definition",
            domain=["graph-theory"],
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/private-graph.yaml",
        _artifact_data(
            "claim.fixture.private-graph",
            status="draft",
            title="Private graph conjecture",
            domain=["graph-theory"],
            tags=["graph", "private"],
            depends_on=["definition.fixture.public-graph"],
            statement="PRIVATE FULL STATEMENT SHOULD NOT LEAK",
        ),
    )

    result = build_context_pack(
        RepoContext(tmp_path),
        "issue.fixture.context",
        public_only=True,
    )

    context_md = (result.task_dir / "CONTEXT.md").read_text(encoding="utf-8")
    audit_text = (result.task_dir / "RETRIEVAL_AUDIT.json").read_text(
        encoding="utf-8"
    )

    assert "definition.fixture.public-graph" in context_md
    assert "claim.fixture.private-graph" not in context_md
    assert "Private graph conjecture" not in context_md
    assert "PRIVATE FULL STATEMENT" not in context_md
    assert "claim.fixture.private-graph" not in audit_text
    assert "private scope exclusions" in audit_text


def test_context_pack_surfaces_compact_strategy_plan_summary(
    tmp_path: Path,
) -> None:
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/strategy-summary.yaml",
        _issue_data(
            issue_id="issue.fixture.strategy-summary",
            related_artifacts=["claim.fixture.strategy-summary"],
            description="Need strategy-aware context.",
            tags=["strategy"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/draft/claims/strategy-summary.yaml",
        _artifact_data(
            "claim.fixture.strategy-summary",
            status="draft",
            title="Strategy summary draft",
            domain=["graph-theory"],
            tags=["strategy"],
        ),
    )
    plan = runner.invoke(
        app,
        [
            "strategy",
            "plan",
            "--issue",
            "issue.fixture.strategy-summary",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert plan.exit_code == 0, plan.output

    result = build_context_pack(RepoContext(tmp_path), "issue.fixture.strategy-summary")

    context_md = (result.task_dir / "CONTEXT.md").read_text(encoding="utf-8")
    audit = json.loads((result.task_dir / "RETRIEVAL_AUDIT.json").read_text())

    assert "## Strategy Plan Summary" in context_md
    assert "strategy.issue.fixture.strategy-summary.plan" in context_md
    assert "Strategy plans are guidance for review only" in context_md
    assert audit["context_payload"]["strategy_plan_count"] == 1
    assert audit["strategy_plans"][0]["plan_id"] == (
        "strategy.issue.fixture.strategy-summary.plan"
    )


def test_context_pack_public_only_does_not_leak_private_strategy_text(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/private-strategy.yaml",
        _issue_data(
            issue_id="issue.fixture.private-strategy",
            related_artifacts=[
                "definition.fixture.public-graph",
                "claim.fixture.private-strategy",
            ],
            description="Need public-only strategy context.",
            tags=["graph", "strategy"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/public/accepted/definitions/public-graph.yaml",
        _artifact_data(
            "definition.fixture.public-graph",
            status="accepted",
            title="Public graph definition",
            domain=["graph-theory"],
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/private-strategy.yaml",
        _artifact_data(
            "claim.fixture.private-strategy",
            status="draft",
            title="PRIVATE STRATEGY MARKER should not leak",
            domain=["graph-theory"],
            tags=["graph", "strategy"],
            depends_on=["definition.fixture.public-graph"],
        ),
    )
    plan = runner.invoke(
        app,
        [
            "strategy",
            "plan",
            "--issue",
            "issue.fixture.private-strategy",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert plan.exit_code == 0, plan.output

    result = build_context_pack(
        RepoContext(tmp_path),
        "issue.fixture.private-strategy",
        public_only=True,
    )

    rendered = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(result.task_dir.iterdir())
        if path.is_file()
    )
    assert "definition.fixture.public-graph" in rendered
    assert "strategy.issue.fixture.private-strategy.plan" in rendered
    assert "PRIVATE STRATEGY MARKER" not in rendered
    assert "claim.fixture.private-strategy" not in rendered
    assert "private strategy content excluded" in rendered


def test_context_pack_includes_failure_memory_card_summary(
    tmp_path: Path,
) -> None:
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/failure-memory.yaml",
        _issue_data(
            related_artifacts=["claim.fixture.failure-memory"],
            description="Need graph failure memory context.",
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/draft/claims/failure-memory.yaml",
        _artifact_data(
            "claim.fixture.failure-memory",
            status="draft",
            title="Draft claim with failure memory",
            domain=["graph-theory"],
            tags=["graph"],
            failure_log=[
                _failure_log_entry(
                    direction="Search for a triangle-free gadget counterexample",
                    failed_because="The candidate gadget still contains a triangle.",
                )
            ],
        ),
    )

    result = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    context_md = (result.task_dir / "CONTEXT.md").read_text(encoding="utf-8")
    audit = json.loads((result.task_dir / "RETRIEVAL_AUDIT.json").read_text())

    assert "[DRAFT] claim.fixture.failure-memory" in context_md
    assert "failures: 1" in context_md
    assert "Search for a triangle-free gadget counterexample" in context_md
    assert audit["retrieval"]["cards"][0]["failure_count"] == 1
    assert audit["retrieval"]["cards"][0]["recent_failure_directions"] == [
        "Search for a triangle-free gadget counterexample"
    ]


def test_context_pack_writes_known_failed_directions_section(
    tmp_path: Path,
) -> None:
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/failure-section.yaml",
        _issue_data(
            related_artifacts=["claim.fixture.failure-section"],
            description="Need graph failure section context.",
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/draft/claims/failure-section.yaml",
        _artifact_data(
            "claim.fixture.failure-section",
            status="draft",
            title="Draft claim with failed directions",
            domain=["graph-theory"],
            tags=["graph"],
            failure_log=[
                _failure_log_entry(
                    direction="Try a separator induction on the bad component",
                    failed_because="The separator premise is unavailable.",
                    next_possible_directions=[
                        "Try a bounded-width decomposition first."
                    ],
                )
            ],
        ),
    )

    result = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    context_md = (result.task_dir / "CONTEXT.md").read_text(encoding="utf-8")
    known_failures = (result.task_dir / "KNOWN_FAILURES.md").read_text(
        encoding="utf-8"
    )
    audit = json.loads((result.task_dir / "RETRIEVAL_AUDIT.json").read_text())

    for rendered in (context_md, known_failures):
        assert "## Known Failed Directions" in rendered
        assert "claim.fixture.failure-section" in rendered
        assert "Try a separator induction on the bad component" in rendered
        assert "failed_because: The separator premise is unavailable." in rendered
        assert "status: open" in rendered
        assert "next: Try a bounded-width decomposition first." in rendered
        assert "origin: human" in rendered
        assert "not proof, refutation, verifier pass, or human review" in rendered

    assert audit["context_payload"]["failure_entry_count"] == 1
    assert audit["failure_memory"] == [
        {
            "artifact_id": "claim.fixture.failure-section",
            "artifact_path": "kb/draft/claims/failure-section.yaml",
            "root_scope": "workspace",
            "failure_id": "failure.fixture.0001",
            "direction": "Try a separator induction on the bad component",
            "failed_because": "The separator premise is unavailable.",
            "status": "open",
            "next_possible_directions": [
                "Try a bounded-width decomposition first."
            ],
            "origin": "human",
            "attempt_kind": "proof_attempt",
            "source_label": "workspace:human",
        }
    ]


def test_context_pack_omits_failed_directions_section_when_empty(
    tmp_path: Path,
) -> None:
    _write_repo(tmp_path)

    result = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    context_md = (result.task_dir / "CONTEXT.md").read_text(encoding="utf-8")
    known_failures = (result.task_dir / "KNOWN_FAILURES.md").read_text(
        encoding="utf-8"
    )
    audit = json.loads((result.task_dir / "RETRIEVAL_AUDIT.json").read_text())

    assert "## Known Failed Directions" not in context_md
    assert "## Known Failed Directions" not in known_failures
    assert audit["context_payload"]["failure_entry_count"] == 0
    assert audit["failure_memory"] == []


def test_context_pack_public_only_excludes_private_failure_log_text(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/private-failure.yaml",
        _issue_data(
            related_artifacts=[
                "definition.fixture.public-graph",
                "claim.fixture.private-failure-memory",
            ],
            description="Need graph context.",
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/public/accepted/definitions/public-graph.yaml",
        _artifact_data(
            "definition.fixture.public-graph",
            status="accepted",
            title="Public graph definition",
            domain=["graph-theory"],
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/private/draft/claims/private-failure-memory.yaml",
        _artifact_data(
            "claim.fixture.private-failure-memory",
            status="draft",
            title="Private graph conjecture",
            domain=["graph-theory"],
            tags=["graph"],
            depends_on=["definition.fixture.public-graph"],
            failure_log=[
                _failure_log_entry(
                    direction="PRIVATE SECRET separator failure direction",
                    failed_because="PRIVATE SECRET failed reason",
                )
            ],
        ),
    )

    result = build_context_pack(
        RepoContext(tmp_path),
        "issue.fixture.context",
        public_only=True,
    )

    context_md = (result.task_dir / "CONTEXT.md").read_text(encoding="utf-8")
    known_failures = (result.task_dir / "KNOWN_FAILURES.md").read_text(
        encoding="utf-8"
    )
    audit_text = (result.task_dir / "RETRIEVAL_AUDIT.json").read_text(
        encoding="utf-8"
    )

    assert "definition.fixture.public-graph" in context_md
    assert "claim.fixture.private-failure-memory" not in context_md
    assert "PRIVATE SECRET" not in context_md
    assert "PRIVATE SECRET" not in known_failures
    assert "PRIVATE SECRET" not in audit_text
    assert "Known Failed Directions" not in context_md
    assert "Known Failed Directions" not in known_failures
    assert "private scope exclusions" in audit_text


def test_relevant_artifacts_are_ranked_by_explainable_reasons(
    tmp_path: Path,
) -> None:
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/ranking.yaml",
        _issue_data(
            related_artifacts=["claim.fixture.direct"],
            description="Need context for graph-theory ranking.",
            tags=["ranked-context", "search"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/draft/claims/direct.yaml",
        _artifact_data(
            "claim.fixture.direct",
            status="draft",
            title="Direct draft",
            depends_on=["claim.fixture.dependency"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/dependency.yaml",
        _artifact_data(
            "claim.fixture.dependency",
            status="accepted",
            title="Accepted dependency",
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/domain.yaml",
        _artifact_data(
            "claim.fixture.domain",
            status="accepted",
            title="Domain match",
            domain=["graph-theory"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/tag.yaml",
        _artifact_data(
            "claim.fixture.tag",
            status="accepted",
            title="Tag match",
            tags=["search"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/unrelated.yaml",
        _artifact_data(
            "claim.fixture.unrelated",
            status="accepted",
            title="Unrelated accepted",
            domain=["number-theory"],
            tags=["unrelated"],
        ),
    )

    build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    relevant_md = (
        tmp_path
        / "context"
        / "TASKS"
        / "issue.fixture.context"
        / "RELEVANT_ARTIFACTS.md"
    ).read_text(encoding="utf-8")
    ordered_ids = [
        "claim.fixture.direct",
        "claim.fixture.dependency",
        "claim.fixture.domain",
        "claim.fixture.tag",
    ]
    positions = [relevant_md.index(artifact_id) for artifact_id in ordered_ids]

    assert positions == sorted(positions)
    assert "claim.fixture.direct" in relevant_md
    assert "reasons: direct reference" in relevant_md
    assert "claim.fixture.dependency" in relevant_md
    assert "reasons: dependency neighbor" in relevant_md
    assert "claim.fixture.domain" in relevant_md
    assert "reasons: domain match" in relevant_md
    assert "claim.fixture.tag" in relevant_md
    assert "reasons: tag match" in relevant_md
    assert "claim.fixture.unrelated" not in relevant_md


def test_related_known_failures_are_marked_not_current_truth(
    tmp_path: Path,
) -> None:
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/known-failure.yaml",
        _issue_data(related_artifacts=[], tags=["failed-approach"]),
    )
    _write_yaml(
        tmp_path,
        "kb/refuted/refuted.yaml",
        _artifact_data(
            "claim.fixture.refuted-tag",
            status="refuted",
            title="Refuted tagged claim",
            tags=["failed-approach"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/obsolete/obsolete.yaml",
        _artifact_data(
            "claim.fixture.obsolete-tag",
            status="obsolete",
            title="Obsolete tagged claim",
            tags=["failed-approach"],
        ),
    )

    build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    context_md = (
        tmp_path
        / "context"
        / "TASKS"
        / "issue.fixture.context"
        / "CONTEXT.md"
    ).read_text(encoding="utf-8")
    known_failures = (
        tmp_path
        / "context"
        / "TASKS"
        / "issue.fixture.context"
        / "KNOWN_FAILURES.md"
    ).read_text(encoding="utf-8")

    assert "## Relevant Known Failures" in context_md
    assert "[REFUTED] claim.fixture.refuted-tag" in context_md
    assert "[OBSOLETE] claim.fixture.obsolete-tag" in context_md
    assert "[REFUTED] claim.fixture.refuted-tag" in known_failures
    assert "[OBSOLETE] claim.fixture.obsolete-tag" in known_failures


def test_missing_issue_fails_with_clear_error(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    with pytest.raises(
        ContextPackError,
        match="issue not found: issue.fixture.missing",
    ):
        build_context_pack(RepoContext(tmp_path), "issue.fixture.missing")

    result = runner.invoke(
        app,
        ["context", "build", "issue.fixture.missing", "--repo-root", str(tmp_path)],
    )

    assert result.exit_code != 0
    assert "issue not found: issue.fixture.missing" in result.output
    assert "Traceback" not in result.output


def test_accepted_and_draft_labels_are_clear(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    context_md = (
        tmp_path
        / "context"
        / "TASKS"
        / "issue.fixture.context"
        / "CONTEXT.md"
    ).read_text(encoding="utf-8")
    relevant_md = (
        tmp_path
        / "context"
        / "TASKS"
        / "issue.fixture.context"
        / "RELEVANT_ARTIFACTS.md"
    ).read_text(encoding="utf-8")

    assert "## Relevant Accepted Artifacts" in context_md
    assert "- claim.fixture.accepted | Accepted claim" in context_md
    assert "## Relevant Draft Artifacts" in context_md
    assert "[DRAFT] claim.fixture.draft | Draft claim" in context_md
    assert "claim.fixture.accepted | Accepted claim | accepted" in relevant_md
    assert "[DRAFT] claim.fixture.draft | Draft claim | draft" in relevant_md
    assert "claim.fixture.unrelated" not in context_md
    assert "claim.fixture.unrelated" not in relevant_md
    assert "Formal links:" not in context_md
    assert "G10-relevant:" not in context_md


def test_context_pack_displays_formal_link_metadata_without_lean_claims(
    tmp_path: Path,
) -> None:
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/formal-link.yaml",
        _issue_data(
            related_artifacts=["claim.fixture.formal-link"],
            tags=["formal-link"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/draft/claims/formal-link.yaml",
        _artifact_data(
            "claim.fixture.formal-link",
            status="draft",
            title="Draft formal-link claim",
            formalizations=[
                _formalization_fixture(
                    formalization_id="cslib.fixture.z-link",
                    symbol="CSLib.Graph.Basic.z_symbol",
                ),
                _formalization_fixture(
                    formalization_id="cslib.fixture.a-link",
                    symbol="CSLib.Graph.Basic.a_symbol",
                ),
            ],
            alignment={
                "status": "requested",
                "reviewer": "",
                "reviewed_at": None,
                "convention_notes": ["Check graph conventions."],
                "limitations": "Fixture alignment is not reviewed.",
            },
            verification_policy=_formal_link_policy(),
        ),
    )

    first = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")
    second = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")
    first_context = (first.task_dir / "CONTEXT.md").read_text(encoding="utf-8")
    second_context = (second.task_dir / "CONTEXT.md").read_text(encoding="utf-8")

    assert first_context == second_context
    assert (
        "[DRAFT] claim.fixture.formal-link | Draft formal-link claim"
        in first_context
    )
    assert "Formal links:" in first_context
    assert (
        "CSLib@cslib-main:CSLib.Graph.Basic#CSLib.Graph.Basic.a_symbol "
        "[theorem, planned, external_library_ref]"
    ) in first_context
    assert (
        "CSLib@cslib-main:CSLib.Graph.Basic#CSLib.Graph.Basic.z_symbol "
        "[theorem, planned, external_library_ref]"
    ) in first_context
    assert first_context.index("CSLib.Graph.Basic.a_symbol") < first_context.index(
        "CSLib.Graph.Basic.z_symbol"
    )
    assert "Alignment: requested; reviewer=-" in first_context
    assert (
        "Verification policy: source_reviewed_with_formal_link; "
        "formal_link=true; lean_check=false; alignment_review=false"
    ) in first_context
    assert "G10-relevant: yes; requires formal link; planned formalization" in (
        first_context
    )
    assert "Lean verified" not in first_context
    assert "G10 formal link gate: pass" not in first_context


def test_known_failures_and_commands_are_written(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    task_dir = tmp_path / "context" / "TASKS" / "issue.fixture.context"
    known_failures = (task_dir / "KNOWN_FAILURES.md").read_text(encoding="utf-8")
    commands = (task_dir / "COMMANDS.md").read_text(encoding="utf-8")

    assert "claim.fixture.refuted | Refuted claim | refuted" in known_failures
    for command in (
        "make lint",
        "make typecheck",
        "make test",
        "make validate",
        "make gate",
    ):
        assert f"- `{command}`" in commands


def test_context_show_prints_context_pack(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    result = runner.invoke(
        app,
        ["context", "show", "issue.fixture.context", "--repo-root", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert "# Context Pack: issue.fixture.context" in result.output
    assert "claim.fixture.accepted" in result.output
    assert "[DRAFT] claim.fixture.draft" in result.output


def test_context_cli_routes_through_app_facade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, bool]] = []

    class FakeContextResult:
        def __init__(self, issue_id: str, repo_root: Path) -> None:
            self.issue_id = issue_id
            self.task_dir = repo_root / "context" / "TASKS" / issue_id
            self.files = [self.task_dir / "CONTEXT.md"]

    class FakeApp:
        def __init__(self, repo_root: str | Path) -> None:
            self.context = RepoContext(Path(repo_root))

        def build_context(
            self,
            issue_id: str,
            *,
            role: RetrievalRole | str = RetrievalRole.ORCHESTRATOR,
            max_cards: int = 20,
            max_full_artifacts: int | None = None,
            public_only: bool = False,
        ) -> FakeContextResult:
            calls.append(("build", issue_id, public_only))
            return FakeContextResult(issue_id, self.context.repo_root)

        def show_context(
            self,
            issue_id: str,
            *,
            role: RetrievalRole | str = RetrievalRole.ORCHESTRATOR,
            max_cards: int = 20,
            max_full_artifacts: int | None = None,
            public_only: bool = False,
        ) -> str:
            calls.append(("show", issue_id, public_only))
            return f"# Context Pack: {issue_id}\n"

    def fake_open_app(repo_root: str | Path = ".") -> FakeApp:
        return FakeApp(repo_root)

    monkeypatch.setattr(context_cli, "open_app", fake_open_app)

    build = runner.invoke(
        app,
        [
            "context",
            "build",
            "issue.fixture.context",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    show = runner.invoke(
        app,
        [
            "context",
            "show",
            "issue.fixture.context",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert build.exit_code == 0, build.output
    assert json.loads(build.output)["issue_id"] == "issue.fixture.context"
    assert show.exit_code == 0, show.output
    assert json.loads(show.output)["content"] == (
        "# Context Pack: issue.fixture.context\n"
    )
    assert calls == [
        ("build", "issue.fixture.context", False),
        ("show", "issue.fixture.context", False),
    ]


def test_context_build_cli_accepts_role_and_full_artifact_budget(
    tmp_path: Path,
) -> None:
    _write_context_docs(tmp_path)
    _write_yaml(
        tmp_path,
        "issues/open/cli-full-artifact.yaml",
        _issue_data(
            related_artifacts=["claim.fixture.cli-full"],
            description="Need graph verifier context.",
            tags=["graph"],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/cli-full.yaml",
        _artifact_data(
            "claim.fixture.cli-full",
            status="accepted",
            title="CLI full artifact",
            domain=["graph-theory"],
            tags=["graph"],
            statement="SECRET CLI FULL STATEMENT",
        ),
    )

    result = runner.invoke(
        app,
        [
            "context",
            "build",
            "issue.fixture.context",
            "--repo-root",
            str(tmp_path),
            "--role",
            "verifier",
            "--max-full-artifacts",
            "1",
        ],
    )

    task_dir = tmp_path / "context" / "TASKS" / "issue.fixture.context"
    full_artifacts = (task_dir / "FULL_ARTIFACTS.md").read_text(encoding="utf-8")
    audit = json.loads((task_dir / "RETRIEVAL_AUDIT.json").read_text())

    assert result.exit_code == 0, result.output
    assert "SECRET CLI FULL STATEMENT" in full_artifacts
    assert audit["request"]["role"] == "verifier"
    assert audit["request"]["max_full_artifacts"] == 1
