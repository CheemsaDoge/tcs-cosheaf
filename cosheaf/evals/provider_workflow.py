"""Deterministic provider workflow evaluation harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import Field, field_validator

from cosheaf.agent.hosted_workers import (
    HostedWorkerInput,
    HostedWorkerOutput,
    HostedWorkerService,
    HostedWorkerStatus,
)
from cosheaf.agent.model_provider import NetworkPolicy, ProviderName
from cosheaf.agent.providers import (
    OpenAICompatibleHttpTransport,
    OpenAICompatibleProvider,
    ProviderConfig,
    ProviderError,
    ProviderGateway,
    ProviderGatewayRequest,
    ProviderMode,
    ProviderTransportResult,
    ProviderTransportStatus,
)
from cosheaf.agent.roles import RoleName
from cosheaf.agent.task import WorkerType
from cosheaf.core.ids import validate_artifact_id
from cosheaf.memory.models import MemoryModel
from cosheaf.security.provider_logs import (
    scan_provider_log_file,
    scan_provider_log_text,
)
from cosheaf.services import ContextSendPolicyService
from cosheaf.services.models import (
    ContextBuildRequest,
    ContextPolicyMode,
    ErrorResult,
    ModelCallResult,
    ProviderConsent,
)
from cosheaf.storage.repo import RepoContext

DEFAULT_PROVIDER_WORKFLOW_EVAL_CASES = (
    Path("evals") / "provider_workflow" / "cases.yaml"
)


class ProviderWorkflowEvalError(ValueError):
    """Raised for expected provider workflow eval loading failures."""


class ProviderWorkflowEvalKind(StrEnum):
    """Supported provider workflow eval scenarios."""

    FAKE_PROVIDER_SUCCESS = "fake_provider_success"
    MOCKED_OPENAI_SUCCESS = "mocked_openai_success"
    MISSING_CONFIG = "missing_config"
    MISSING_CONSENT = "missing_consent"
    PRIVATE_CONTEXT_DENIED = "private_context_denied"
    MALFORMED_OUTPUT = "malformed_output"
    POLICY_VIOLATING_VERIFIER_OUTPUT = "policy_violating_verifier_output"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CANCELLATION = "cancellation"


class ProviderWorkflowEvalCase(MemoryModel):
    """One deterministic provider workflow eval case."""

    id: str | None = None
    kind: ProviderWorkflowEvalKind
    expected_error_code: str | None = None
    expect_policy_denial: bool = False
    expect_validation_rejection: bool = False
    expect_malformed_rejection: bool = False
    expect_context_scope_violation: bool = False
    expect_bundle_valid: bool = False
    forbidden_substrings: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("kind", mode="before")
    @classmethod
    def _validate_kind(
        cls,
        value: ProviderWorkflowEvalKind | str,
    ) -> ProviderWorkflowEvalKind:
        return (
            value
            if isinstance(value, ProviderWorkflowEvalKind)
            else ProviderWorkflowEvalKind(value)
        )

    @field_validator("expected_error_code")
    @classmethod
    def _validate_error_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _non_empty(value)

    @field_validator("forbidden_substrings")
    @classmethod
    def _validate_forbidden_substrings(cls, values: list[str]) -> list[str]:
        return [_non_empty(value) for value in values]


class ProviderWorkflowEvalSuite(MemoryModel):
    """A small collection of provider workflow eval cases."""

    schema_version: Literal[1] = 1
    cases: list[ProviderWorkflowEvalCase]

    @field_validator("cases")
    @classmethod
    def _validate_cases(
        cls,
        values: list[ProviderWorkflowEvalCase],
    ) -> list[ProviderWorkflowEvalCase]:
        if not values:
            raise ValueError("cases must not be empty")
        return values


@dataclass(frozen=True)
class ProviderWorkflowEvalMetrics:
    """Aggregate provider workflow safety and quality metrics."""

    policy_denial_accuracy: float
    validation_rejection_accuracy: float
    secret_leak_count: int
    malformed_output_reject_count: int
    bundle_validity_rate: float
    context_scope_violation_count: int

    def to_dict(self) -> dict[str, int | float]:
        """Return deterministic machine-readable metrics."""
        return {
            "policy_denial_accuracy": self.policy_denial_accuracy,
            "validation_rejection_accuracy": self.validation_rejection_accuracy,
            "secret_leak_count": self.secret_leak_count,
            "malformed_output_reject_count": self.malformed_output_reject_count,
            "bundle_validity_rate": self.bundle_validity_rate,
            "context_scope_violation_count": self.context_scope_violation_count,
        }


@dataclass(frozen=True)
class ProviderWorkflowEvalCaseResult:
    """One executed provider workflow eval case."""

    id: str
    kind: ProviderWorkflowEvalKind
    provider: str | None
    role: str | None
    status: str
    error_code: str | None
    bundle_valid: bool
    accepted_write_performed: bool
    policy_denial_expected: bool
    policy_denial_matched: bool
    validation_rejection_expected: bool
    validation_rejection_matched: bool
    malformed_output_rejected: bool
    context_scope_violation_expected: bool
    context_scope_violation: bool
    secret_leak_count: int
    secret_findings: list[str]
    runtime_paths: tuple[Path, ...]
    failures: list[str]

    @property
    def passed(self) -> bool:
        """Return whether this case satisfied every configured expectation."""
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable case output."""
        return {
            "id": self.id,
            "kind": self.kind.value,
            "provider": self.provider,
            "role": self.role,
            "status": self.status,
            "error_code": self.error_code,
            "bundle_valid": self.bundle_valid,
            "accepted_write_performed": self.accepted_write_performed,
            "policy_denial_expected": self.policy_denial_expected,
            "policy_denial_matched": self.policy_denial_matched,
            "validation_rejection_expected": self.validation_rejection_expected,
            "validation_rejection_matched": self.validation_rejection_matched,
            "malformed_output_rejected": self.malformed_output_rejected,
            "context_scope_violation_expected": self.context_scope_violation_expected,
            "context_scope_violation": self.context_scope_violation,
            "secret_leak_count": self.secret_leak_count,
            "secret_findings": self.secret_findings,
            "runtime_paths": [path.as_posix() for path in self.runtime_paths],
            "failures": self.failures,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class ProviderWorkflowEvalReport:
    """Scored provider workflow eval suite output."""

    schema_version: Literal[1]
    case_count: int
    passed: bool
    metrics: ProviderWorkflowEvalMetrics
    runtime_paths: tuple[Path, ...]
    cases: list[ProviderWorkflowEvalCaseResult]

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable report output."""
        return {
            "schema_version": self.schema_version,
            "case_count": self.case_count,
            "passed": self.passed,
            "metrics": self.metrics.to_dict(),
            "runtime_paths": [path.as_posix() for path in self.runtime_paths],
            "cases": [case.to_dict() for case in self.cases],
        }

    def to_json(self) -> str:
        """Return deterministic JSON for the report."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


@dataclass(frozen=True)
class _ProviderWorkflowObservation:
    provider: str | None
    role: str | None
    status: str
    error_code: str | None
    bundle_valid: bool
    accepted_write_performed: bool
    runtime_paths: tuple[Path, ...]
    output_text: str


class _StaticTransport:
    def __init__(self, result: ProviderTransportResult) -> None:
        self.result = result

    def complete(
        self,
        request: ProviderGatewayRequest,
        config: ProviderConfig,
    ) -> ProviderTransportResult:
        return self.result


def load_provider_workflow_eval_suite(path: Path) -> ProviderWorkflowEvalSuite:
    """Load a provider workflow eval suite from a YAML file."""
    if not path.exists():
        raise ProviderWorkflowEvalError(
            f"provider workflow eval case file not found: {path}"
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProviderWorkflowEvalError(
            f"cannot read provider workflow eval case file: {exc}"
        ) from exc
    if data is None:
        raise ProviderWorkflowEvalError("provider workflow eval case file is empty")
    try:
        return ProviderWorkflowEvalSuite.model_validate(data)
    except ValueError as exc:
        raise ProviderWorkflowEvalError(
            f"invalid provider workflow eval case file: {exc}"
        ) from exc


def resolve_provider_workflow_eval_case_path(
    context: RepoContext,
    cases_path: Path,
) -> Path:
    """Resolve and constrain the case file path to the repository root."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ProviderWorkflowEvalError(
            "provider workflow eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(cases_path).is_absolute():
        raise ProviderWorkflowEvalError(
            "provider workflow eval case file must be repository-local"
        )
    return resolved


def run_provider_workflow_eval_suite(
    context: RepoContext,
    suite: ProviderWorkflowEvalSuite,
) -> ProviderWorkflowEvalReport:
    """Run every provider workflow eval case against local deterministic services."""
    case_results = [
        run_provider_workflow_eval_case(context, case, case_index=index)
        for index, case in enumerate(suite.cases, start=1)
    ]
    metrics = _aggregate_metrics(case_results)
    runtime_paths = _unique_runtime_paths(case_results)
    return ProviderWorkflowEvalReport(
        schema_version=1,
        case_count=len(case_results),
        passed=all(case.passed for case in case_results),
        metrics=metrics,
        runtime_paths=runtime_paths,
        cases=case_results,
    )


def run_provider_workflow_eval_case(
    context: RepoContext,
    case: ProviderWorkflowEvalCase,
    *,
    case_index: int = 1,
) -> ProviderWorkflowEvalCaseResult:
    """Run and score one provider workflow eval case."""
    observation = _run_case_observation(context, case)
    secret_findings = _secret_findings(context, case, observation)
    policy_denial_matched = (
        case.expect_policy_denial
        and case.expected_error_code is not None
        and observation.error_code == case.expected_error_code
    )
    validation_rejection_matched = (
        case.expect_validation_rejection
        and case.expected_error_code is not None
        and observation.error_code == case.expected_error_code
    )
    malformed_output_rejected = (
        case.expect_malformed_rejection
        and observation.error_code == "provider_output_validation_failed"
    )
    context_scope_violation = (
        observation.error_code in {"private_context_requires_policy"}
        or observation.error_code == "private_context_requires_consent"
        or observation.error_code == "provider_context_scope_violation"
    )
    failures = _case_failures(
        case,
        observation=observation,
        secret_findings=secret_findings,
        policy_denial_matched=policy_denial_matched,
        validation_rejection_matched=validation_rejection_matched,
        context_scope_violation=context_scope_violation,
    )
    return ProviderWorkflowEvalCaseResult(
        id=_case_id(case, case_index),
        kind=case.kind,
        provider=observation.provider,
        role=observation.role,
        status=observation.status,
        error_code=observation.error_code,
        bundle_valid=observation.bundle_valid,
        accepted_write_performed=observation.accepted_write_performed,
        policy_denial_expected=case.expect_policy_denial,
        policy_denial_matched=policy_denial_matched,
        validation_rejection_expected=case.expect_validation_rejection,
        validation_rejection_matched=validation_rejection_matched,
        malformed_output_rejected=malformed_output_rejected,
        context_scope_violation_expected=case.expect_context_scope_violation,
        context_scope_violation=context_scope_violation,
        secret_leak_count=len(secret_findings),
        secret_findings=secret_findings,
        runtime_paths=observation.runtime_paths,
        failures=failures,
    )


def _run_case_observation(
    context: RepoContext,
    case: ProviderWorkflowEvalCase,
) -> _ProviderWorkflowObservation:
    if case.kind is ProviderWorkflowEvalKind.FAKE_PROVIDER_SUCCESS:
        return _observe_hosted_worker(context, _fake_hosted_worker_output(context))
    if case.kind is ProviderWorkflowEvalKind.MOCKED_OPENAI_SUCCESS:
        return _observe_hosted_worker(context, _mocked_openai_worker_output(context))
    if case.kind is ProviderWorkflowEvalKind.MISSING_CONFIG:
        return _observe_provider_result(
            context,
            _http_preflight_result(context, missing_config=True),
        )
    if case.kind is ProviderWorkflowEvalKind.MISSING_CONSENT:
        return _observe_provider_result(
            context,
            _http_preflight_result(context, missing_consent=True),
        )
    if case.kind is ProviderWorkflowEvalKind.PRIVATE_CONTEXT_DENIED:
        return _observe_context_policy_denial(context)
    if case.kind is ProviderWorkflowEvalKind.MALFORMED_OUTPUT:
        return _observe_hosted_worker(context, _malformed_worker_output(context))
    if case.kind is ProviderWorkflowEvalKind.POLICY_VIOLATING_VERIFIER_OUTPUT:
        return _observe_hosted_worker(context, _unsafe_verifier_output(context))
    if case.kind is ProviderWorkflowEvalKind.RATE_LIMIT:
        return _observe_provider_result(
            context,
            _transport_failure_result(
                context,
                ProviderTransportStatus.RATE_LIMITED,
                "rate_limited",
                "rate limited",
            ),
        )
    if case.kind is ProviderWorkflowEvalKind.TIMEOUT:
        return _observe_provider_result(
            context,
            _transport_failure_result(
                context,
                ProviderTransportStatus.TIMEOUT,
                "timeout",
                "request timed out",
            ),
        )
    if case.kind is ProviderWorkflowEvalKind.CANCELLATION:
        return _observe_provider_result(
            context,
            _transport_failure_result(
                context,
                ProviderTransportStatus.CANCELLED,
                "cancelled",
                "operator cancelled sk-provider-workflow-cancel-secret",
            ),
        )
    raise ProviderWorkflowEvalError(f"unsupported provider workflow eval: {case.kind}")


def _fake_hosted_worker_output(context: RepoContext) -> HostedWorkerOutput:
    return HostedWorkerService(context).run(
        _hosted_input(
            RoleName.REASONER,
            prompt=(
                "Return review-only fake provider output. "
                "Use sk-provider-workflow-fake-secret only as a redaction fixture."
            ),
        )
    )


def _mocked_openai_worker_output(context: RepoContext) -> HostedWorkerOutput:
    return HostedWorkerService(context).run(
        _hosted_input(RoleName.REASONER),
        config=_openai_mock_config(),
        provider=OpenAICompatibleProvider(
            transport=_StaticTransport(
                ProviderTransportResult(
                    content=_worker_bundle_json(role="reasoner"),
                    status=ProviderTransportStatus.COMPLETED,
                    raw_metadata={
                        "Authorization": "Bearer sk-provider-workflow-mock-secret"
                    },
                )
            )
        ),
    )


def _malformed_worker_output(context: RepoContext) -> HostedWorkerOutput:
    return HostedWorkerService(context).run(
        _hosted_input(RoleName.REASONER),
        config=_openai_mock_config(),
        provider=OpenAICompatibleProvider(
            transport=_StaticTransport(
                ProviderTransportResult(
                    content="not json",
                    status=ProviderTransportStatus.COMPLETED,
                )
            )
        ),
    )


def _unsafe_verifier_output(context: RepoContext) -> HostedWorkerOutput:
    return HostedWorkerService(context).run(
        _hosted_input(RoleName.VERIFIER),
        config=_openai_mock_config(),
        provider=OpenAICompatibleProvider(
            transport=_StaticTransport(
                ProviderTransportResult(
                    content=_worker_bundle_json(
                        role="verifier",
                        summary=(
                            "Verifier says review.state human_reviewed and accepted."
                        ),
                    ),
                    status=ProviderTransportStatus.COMPLETED,
                )
            )
        ),
    )


def _http_preflight_result(
    context: RepoContext,
    *,
    missing_config: bool = False,
    missing_consent: bool = False,
) -> ModelCallResult | ProviderError:
    consent = _public_consent(consent_required=not missing_consent, granted=True)
    if missing_consent:
        consent = _public_consent(consent_required=True, granted=False)
    config = _openai_mock_config(base_url=None if missing_config else "https://unused")
    return ProviderGateway(context).call(
        _gateway_request(consent=consent, network_policy=NetworkPolicy.EXPLICIT_ALLOW),
        config=config,
        provider=OpenAICompatibleProvider(
            transport=OpenAICompatibleHttpTransport(urlopen=_forbid_urlopen)
        ),
    )


def _transport_failure_result(
    context: RepoContext,
    status: ProviderTransportStatus,
    error_code: str,
    error_message: str,
) -> ModelCallResult | ProviderError:
    return ProviderGateway(context).call(
        _gateway_request(),
        config=_openai_mock_config(),
        provider=OpenAICompatibleProvider(
            transport=_StaticTransport(
                ProviderTransportResult(
                    content="",
                    status=status,
                    error_code=error_code,
                    error_message=error_message,
                    raw_metadata={
                        "Authorization": "Bearer sk-provider-workflow-failure-secret"
                    },
                )
            )
        ),
    )


def _observe_context_policy_denial(
    context: RepoContext,
) -> _ProviderWorkflowObservation:
    result = ContextSendPolicyService(context).provider_preview(
        ContextBuildRequest(
            issue_id="issue.fixture.provider-workflow",
            policy_mode=ContextPolicyMode.PUBLIC,
            public_only=False,
            allow_private_context=False,
        )
    )
    if not isinstance(result, ErrorResult):
        return _ProviderWorkflowObservation(
            provider=None,
            role=None,
            status="completed",
            error_code=None,
            bundle_valid=False,
            accepted_write_performed=False,
            runtime_paths=(),
            output_text=result.to_json(),
        )
    return _ProviderWorkflowObservation(
        provider=None,
        role=None,
        status="rejected",
        error_code=result.code,
        bundle_valid=False,
        accepted_write_performed=False,
        runtime_paths=(),
        output_text=result.to_json(),
    )


def _observe_hosted_worker(
    context: RepoContext,
    result: HostedWorkerOutput,
) -> _ProviderWorkflowObservation:
    runtime_paths = _runtime_paths(result.provider_log_path)
    return _ProviderWorkflowObservation(
        provider=(
            result.provider_run.provider.value
            if result.provider_run is not None
            else None
        ),
        role=result.role.value,
        status=result.status.value,
        error_code=result.error.code if result.error is not None else None,
        bundle_valid=result.bundle is not None
        and result.status is HostedWorkerStatus.COMPLETED,
        accepted_write_performed=result.accepted_write_performed,
        runtime_paths=runtime_paths,
        output_text=_observation_text(
            context,
            result.model_dump(mode="json"),
            runtime_paths,
        ),
    )


def _observe_provider_result(
    context: RepoContext,
    result: ModelCallResult | ProviderError,
) -> _ProviderWorkflowObservation:
    if isinstance(result, ProviderError):
        runtime_paths = _runtime_paths(result.details.get("log_path"))
        return _ProviderWorkflowObservation(
            provider="openai",
            role="reasoner",
            status="rejected",
            error_code=result.code,
            bundle_valid=False,
            accepted_write_performed=False,
            runtime_paths=runtime_paths,
            output_text=_observation_text(
                context,
                result.model_dump(mode="json"),
                runtime_paths,
            ),
        )
    runtime_paths = _runtime_paths(result.provider_run.log_path)
    return _ProviderWorkflowObservation(
        provider=result.provider.value,
        role="reasoner",
        status=result.status.value,
        error_code=None,
        bundle_valid=True,
        accepted_write_performed=False,
        runtime_paths=runtime_paths,
        output_text=_observation_text(context, result.to_dict(), runtime_paths),
    )


def _case_failures(
    case: ProviderWorkflowEvalCase,
    *,
    observation: _ProviderWorkflowObservation,
    secret_findings: list[str],
    policy_denial_matched: bool,
    validation_rejection_matched: bool,
    context_scope_violation: bool,
) -> list[str]:
    failures: list[str] = []
    if case.expected_error_code is None and observation.error_code is not None:
        failures.append(f"unexpected error_code {observation.error_code}")
    if (
        case.expected_error_code is not None
        and observation.error_code != case.expected_error_code
    ):
        failures.append(
            f"expected error_code {case.expected_error_code}, "
            f"got {observation.error_code}"
        )
    if case.expect_policy_denial and not policy_denial_matched:
        failures.append("policy denial did not match expected error code")
    if case.expect_validation_rejection and not validation_rejection_matched:
        failures.append("validation rejection did not match expected error code")
    if case.expect_malformed_rejection and not (
        observation.error_code == "provider_output_validation_failed"
    ):
        failures.append("malformed output was not rejected with validation failure")
    if case.expect_context_scope_violation and not context_scope_violation:
        failures.append("context scope violation was not recorded")
    if case.expect_bundle_valid and not observation.bundle_valid:
        failures.append("expected a valid WorkerBundle output")
    if observation.accepted_write_performed:
        failures.append("accepted_write_performed must remain false")
    for forbidden in case.forbidden_substrings:
        if forbidden in observation.output_text:
            failures.append(f"forbidden substring leaked: {forbidden}")
    if secret_findings:
        failures.append("provider workflow output/log contained secret findings")
    return failures


def _aggregate_metrics(
    cases: list[ProviderWorkflowEvalCaseResult],
) -> ProviderWorkflowEvalMetrics:
    if not cases:
        raise ProviderWorkflowEvalError("cannot aggregate empty provider workflow eval")
    return ProviderWorkflowEvalMetrics(
        policy_denial_accuracy=_accuracy(
            case.policy_denial_matched
            for case in cases
            if case.policy_denial_expected
        ),
        validation_rejection_accuracy=_accuracy(
            case.validation_rejection_matched
            for case in cases
            if case.validation_rejection_expected
        ),
        secret_leak_count=sum(case.secret_leak_count for case in cases),
        malformed_output_reject_count=sum(
            1 for case in cases if case.malformed_output_rejected
        ),
        bundle_validity_rate=_accuracy(
            case.bundle_valid for case in cases if case.bundle_valid
        ),
        context_scope_violation_count=sum(
            1 for case in cases if case.context_scope_violation
        ),
    )


def _secret_findings(
    context: RepoContext,
    case: ProviderWorkflowEvalCase,
    observation: _ProviderWorkflowObservation,
) -> list[str]:
    findings = [
        f"{finding.kind}:{finding.path or case.id or case.kind.value}"
        for finding in scan_provider_log_text(
            observation.output_text,
            path=case.id or case.kind.value,
        )
    ]
    for relative_path in observation.runtime_paths:
        path = context.resolve(relative_path)
        if path.is_file():
            findings.extend(
                f"{finding.kind}:{finding.path or relative_path.as_posix()}"
                for finding in scan_provider_log_file(path)
            )
    return sorted(dict.fromkeys(findings))


def _observation_text(
    context: RepoContext,
    payload: dict[str, Any],
    runtime_paths: tuple[Path, ...],
) -> str:
    text = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    for relative_path in runtime_paths:
        path = context.resolve(relative_path)
        if path.is_file():
            text += "\n" + path.read_text(encoding="utf-8")
    return text


def _hosted_input(role: RoleName, *, prompt: str | None = None) -> HostedWorkerInput:
    return HostedWorkerInput(
        issue_id="issue.fixture.provider-workflow",
        role=role,
        prompt=prompt or "Return review-only provider workflow output.",
        context_artifact_ids=["claim.fixture.provider-workflow-public"],
        root_scopes=["public"],
        consent=_public_consent(),
    )


def _gateway_request(
    *,
    consent: ProviderConsent | None = None,
    network_policy: NetworkPolicy = NetworkPolicy.DISABLED,
) -> ProviderGatewayRequest:
    return ProviderGatewayRequest(
        provider=ProviderName.OPENAI,
        model="gpt-test",
        worker_role=WorkerType.REASONER,
        prompt="Return review-only provider workflow output.",
        consent=consent or _public_consent(),
        context_artifact_ids=["claim.fixture.provider-workflow-public"],
        root_scopes=["public"],
        output_kind="worker_bundle",
        expected_output_paths=["kb/draft/claims/provider-workflow.yaml"],
        network_policy=network_policy,
    )


def _public_consent(
    *,
    consent_required: bool = False,
    granted: bool = False,
) -> ProviderConsent:
    return ProviderConsent(
        consent_required=consent_required,
        consent_granted=granted,
        allow_private_context=False,
        policy_scope=ContextPolicyMode.PUBLIC,
    )


def _openai_mock_config(*, base_url: str | None = None) -> ProviderConfig:
    return ProviderConfig(
        provider=ProviderName.OPENAI,
        mode=ProviderMode.OPENAI_COMPATIBLE,
        model="gpt-test",
        enabled=True,
        api_key_env=None,
        base_url=base_url,
    )


def _worker_bundle_json(
    *,
    role: str,
    summary: str = "Provider workflow returned review-only output.",
) -> str:
    return json.dumps(
        {
            "bundle_id": f"bundle.issue.fixture.provider-workflow.{role}.0001",
            "task_id": f"task.issue.fixture.provider-workflow.{role}",
            "worker_role": role,
            "created_at": "2026-06-10T00:00:00Z",
            "summary": summary,
            "used_artifacts": ["claim.fixture.provider-workflow-public"],
            "used_sources": [],
            "claims": ["This output remains review context."],
            "proposed_artifacts": [
                {
                    "path": "kb/draft/claims/provider-workflow.yaml",
                    "summary": "Draft-only provider workflow proposal.",
                }
            ],
            "assumptions": ["Provider workflow output is review-only."],
            "uncertainty": ["No human review or semantic alignment review was run."],
            "verification_requests": ["Run validate and gate before review."],
            "failed_attempts": [],
            "counterexamples": [],
            "failures_or_counterexamples": ["No external verifier was run."],
            "dependency_questions": [],
            "risk_flags": ["needs_human_review"],
            "next_steps": ["Request explicit human review."],
            "confidence": "low",
        },
        ensure_ascii=True,
        sort_keys=True,
    )


def _runtime_paths(path: str | None) -> tuple[Path, ...]:
    if path is None:
        return ()
    normalized = Path(path)
    if not normalized.as_posix().startswith(".cosheaf/"):
        return ()
    return (normalized,)


def _unique_runtime_paths(
    cases: list[ProviderWorkflowEvalCaseResult],
) -> tuple[Path, ...]:
    paths = {
        path.as_posix(): path
        for case in cases
        for path in case.runtime_paths
        if path.as_posix().startswith(".cosheaf/")
    }
    return tuple(paths[key] for key in sorted(paths))


def _accuracy(values: Any) -> float:
    items = list(values)
    if not items:
        return 1.0
    return round(sum(1 for value in items if value) / len(items), 6)


def _case_id(case: ProviderWorkflowEvalCase, index: int) -> str:
    if case.id:
        return case.id
    return f"case.provider.{index:04d}"


def _forbid_urlopen(*_args: Any, **_kwargs: Any) -> Any:
    raise AssertionError("provider workflow eval must not perform network I/O")


def _non_empty(value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("text value must be non-empty")
    return normalized


__all__ = [
    "DEFAULT_PROVIDER_WORKFLOW_EVAL_CASES",
    "ProviderWorkflowEvalCase",
    "ProviderWorkflowEvalCaseResult",
    "ProviderWorkflowEvalError",
    "ProviderWorkflowEvalKind",
    "ProviderWorkflowEvalMetrics",
    "ProviderWorkflowEvalReport",
    "ProviderWorkflowEvalSuite",
    "load_provider_workflow_eval_suite",
    "resolve_provider_workflow_eval_case_path",
    "run_provider_workflow_eval_case",
    "run_provider_workflow_eval_suite",
]
