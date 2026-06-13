from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.evals.provider_workflow import (
    DEFAULT_PROVIDER_WORKFLOW_EVAL_CASES,
    ProviderWorkflowEvalCase,
    ProviderWorkflowEvalKind,
    ProviderWorkflowEvalSuite,
    load_provider_workflow_eval_suite,
    run_provider_workflow_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[2]


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "provider-workflow-eval-fixture"',
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


def _artifact_data(
    artifact_id: str,
    *,
    title: str,
    status: str,
    statement: str,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": title,
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-10T00:00:00Z",
        "updated_at": "2026-06-10T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": tags or ["provider-workflow-eval"],
        "statement": statement,
        "evidence": [],
        "review": {"state": "requested", "notes": "Eval fixture review."},
        "risk": {"level": "low", "notes": "Eval fixture risk."},
    }


def _issue_data() -> dict[str, Any]:
    return {
        "id": "issue.fixture.provider-workflow",
        "type": "issue",
        "title": "Evaluate provider workflow fixture",
        "status": "open",
        "created_at": "2026-06-10T00:00:00Z",
        "updated_at": "2026-06-10T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": (
            "Evaluate provider workflow safety without leaking "
            "sk-provider-workflow-private-secret."
        ),
        "related_artifacts": [
            "claim.fixture.provider-workflow-public",
            "claim.fixture.provider-workflow-private",
        ],
        "tags": ["provider-workflow-eval", "private-scope-marker"],
    }


def _write_fixture_repo(repo_root: Path) -> None:
    _write_workspace_config(repo_root)
    _write_yaml(
        repo_root,
        "kb/public/accepted/claims/public.yaml",
        _artifact_data(
            "claim.fixture.provider-workflow-public",
            title="Public provider workflow fixture",
            status="accepted",
            statement="Public context for provider workflow eval.",
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/private.yaml",
        _artifact_data(
            "claim.fixture.provider-workflow-private",
            title="private-scope-marker private fixture",
            status="draft",
            statement="Private context with sk-provider-workflow-private-secret.",
            tags=["provider-workflow-eval", "private-scope-marker"],
            depends_on=["claim.fixture.provider-workflow-public"],
        ),
    )
    _write_yaml(repo_root, "issues/open/provider-workflow.yaml", _issue_data())


def _required_suite() -> ProviderWorkflowEvalSuite:
    return ProviderWorkflowEvalSuite(
        cases=[
            ProviderWorkflowEvalCase(
                id="case.provider.fake-success",
                kind=ProviderWorkflowEvalKind.FAKE_PROVIDER_SUCCESS,
                expect_bundle_valid=True,
                forbidden_substrings=["sk-provider-workflow-"],
            ),
            ProviderWorkflowEvalCase(
                id="case.provider.mock-openai-success",
                kind=ProviderWorkflowEvalKind.MOCKED_OPENAI_SUCCESS,
                expect_bundle_valid=True,
                forbidden_substrings=["sk-provider-workflow-"],
            ),
            ProviderWorkflowEvalCase(
                id="case.provider.missing-config",
                kind=ProviderWorkflowEvalKind.MISSING_CONFIG,
                expected_error_code="provider_config_missing",
                expect_policy_denial=True,
                forbidden_substrings=["sk-provider-workflow-"],
            ),
            ProviderWorkflowEvalCase(
                id="case.provider.missing-consent",
                kind=ProviderWorkflowEvalKind.MISSING_CONSENT,
                expected_error_code="provider_confirm_send_required",
                expect_policy_denial=True,
                forbidden_substrings=["sk-provider-workflow-"],
            ),
            ProviderWorkflowEvalCase(
                id="case.provider.private-context-denied",
                kind=ProviderWorkflowEvalKind.PRIVATE_CONTEXT_DENIED,
                expected_error_code="private_context_requires_policy",
                expect_policy_denial=True,
                expect_context_scope_violation=True,
                forbidden_substrings=[
                    "claim.fixture.provider-workflow-private",
                    "private-scope-marker",
                    "sk-provider-workflow-private-secret",
                ],
            ),
            ProviderWorkflowEvalCase(
                id="case.provider.malformed-output",
                kind=ProviderWorkflowEvalKind.MALFORMED_OUTPUT,
                expected_error_code="provider_output_validation_failed",
                expect_validation_rejection=True,
                expect_malformed_rejection=True,
                forbidden_substrings=["sk-provider-workflow-"],
            ),
            ProviderWorkflowEvalCase(
                id="case.provider.verifier-policy-violation",
                kind=ProviderWorkflowEvalKind.POLICY_VIOLATING_VERIFIER_OUTPUT,
                expected_error_code="hosted_worker_policy_violation",
                expect_policy_denial=True,
                forbidden_substrings=["sk-provider-workflow-"],
            ),
            ProviderWorkflowEvalCase(
                id="case.provider.rate-limit",
                kind=ProviderWorkflowEvalKind.RATE_LIMIT,
                expected_error_code="provider_rate_limited",
                forbidden_substrings=["sk-provider-workflow-"],
            ),
            ProviderWorkflowEvalCase(
                id="case.provider.timeout",
                kind=ProviderWorkflowEvalKind.TIMEOUT,
                expected_error_code="provider_timeout",
                forbidden_substrings=["sk-provider-workflow-"],
            ),
            ProviderWorkflowEvalCase(
                id="case.provider.cancellation",
                kind=ProviderWorkflowEvalKind.CANCELLATION,
                expected_error_code="provider_cancelled",
                forbidden_substrings=["sk-provider-workflow-"],
            ),
        ]
    )


def test_provider_workflow_eval_scores_required_provider_cases(
    tmp_path: Path,
) -> None:
    _write_fixture_repo(tmp_path)

    report = run_provider_workflow_eval_suite(
        RepoContext(tmp_path),
        _required_suite(),
    )

    assert report.passed is True
    assert report.case_count == 10
    assert report.metrics.policy_denial_accuracy == 1.0
    assert report.metrics.validation_rejection_accuracy == 1.0
    assert report.metrics.secret_leak_count == 0
    assert report.metrics.malformed_output_reject_count == 1
    assert report.metrics.bundle_validity_rate == 1.0
    assert report.metrics.context_scope_violation_count == 1
    assert {case.kind for case in report.cases} == set(ProviderWorkflowEvalKind)

    cases = {case.id: case for case in report.cases}
    assert cases["case.provider.fake-success"].status == "completed"
    assert cases["case.provider.mock-openai-success"].provider == "openai"
    assert cases["case.provider.missing-config"].error_code == (
        "provider_config_missing"
    )
    assert cases["case.provider.missing-consent"].error_code == (
        "provider_confirm_send_required"
    )
    assert cases["case.provider.private-context-denied"].error_code == (
        "private_context_requires_policy"
    )
    assert cases["case.provider.malformed-output"].error_code == (
        "provider_output_validation_failed"
    )
    assert cases["case.provider.verifier-policy-violation"].error_code == (
        "hosted_worker_policy_violation"
    )
    assert cases["case.provider.rate-limit"].error_code == "provider_rate_limited"
    assert cases["case.provider.timeout"].error_code == "provider_timeout"
    assert cases["case.provider.cancellation"].error_code == "provider_cancelled"
    assert all(case.accepted_write_performed is False for case in report.cases)
    assert all(path.as_posix().startswith(".cosheaf/") for path in report.runtime_paths)
    assert not (tmp_path / "kb" / "accepted").exists()


def test_provider_workflow_eval_fails_when_error_reason_is_wrong(
    tmp_path: Path,
) -> None:
    _write_fixture_repo(tmp_path)

    report = run_provider_workflow_eval_suite(
        RepoContext(tmp_path),
        ProviderWorkflowEvalSuite(
            cases=[
                ProviderWorkflowEvalCase(
                    id="case.provider.wrong-reason",
                    kind=ProviderWorkflowEvalKind.MISSING_CONSENT,
                    expected_error_code="provider_config_missing",
                    expect_policy_denial=True,
                )
            ]
        ),
    )

    assert report.passed is False
    assert report.metrics.policy_denial_accuracy == 0.0
    assert report.cases[0].error_code == "provider_confirm_send_required"
    assert "expected error_code provider_config_missing" in report.cases[0].failures[0]


def test_default_provider_workflow_eval_suite_lists_required_cases() -> None:
    suite = load_provider_workflow_eval_suite(
        ROOT / DEFAULT_PROVIDER_WORKFLOW_EVAL_CASES
    )
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.provider.fake-success",
        "case.provider.mock-openai-success",
        "case.provider.missing-config",
        "case.provider.missing-consent",
        "case.provider.private-context-denied",
        "case.provider.malformed-output",
        "case.provider.verifier-policy-violation",
        "case.provider.rate-limit",
        "case.provider.timeout",
        "case.provider.cancellation",
    }
    assert {case.kind for case in suite.cases} == set(ProviderWorkflowEvalKind)
