"""Provider gateway core with fake and mocked OpenAI-compatible transports.

The gateway is a service boundary. It does not make real network calls by
itself; OpenAI-compatible behavior is provided through an injected transport so
tests can remain fake or mocked.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cosheaf.agent.model_provider import (
    FakeModelProvider,
    FinishReason,
    ModelRequest,
    NetworkPolicy,
    ProviderCapability,
    ProviderName,
    ReasoningEffort,
    ToolPolicy,
)
from cosheaf.agent.task import WorkerType
from cosheaf.agent.worker_bundle_v2 import WorkerBundleV2
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.services.models import (
    ContextPolicyMode,
    ModelCallResult,
    ProviderConsent,
    ProviderRunRecord,
    ProviderRunStatus,
)
from cosheaf.storage.repo import RepoContext

SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(sk-[A-Za-z0-9_-]+|gh[pousr]_[A-Za-z0-9_]+|xox[baprs]-[A-Za-z0-9-]+)"
)
REDACTED = "<redacted>"


class ProviderMode(StrEnum):
    """Supported provider gateway modes."""

    FAKE = "fake"
    OPENAI_COMPATIBLE = "openai_compatible"


class ProviderTransportStatus(StrEnum):
    """Normalized transport status values."""

    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


_RETRYABLE_STATUSES = frozenset(
    {ProviderTransportStatus.RATE_LIMITED, ProviderTransportStatus.ERROR}
)


class ProviderConfig(BaseModel):
    """Explicit provider runtime configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    provider: ProviderName = ProviderName.FAKE
    mode: ProviderMode = ProviderMode.FAKE
    model: str = "fake-deterministic"
    enabled: bool = False
    api_key_env: str | None = None
    timeout_seconds: int = 30
    max_retries: int = 0
    base_url: str | None = None
    supported_parameters: tuple[str, ...] = ("prompt", "max_output_tokens")

    @field_validator("mode", mode="before")
    @classmethod
    def _mode(cls, value: ProviderMode | str) -> ProviderMode:
        return value if isinstance(value, ProviderMode) else ProviderMode(value)

    @field_validator("model")
    @classmethod
    def _model(cls, value: str) -> str:
        return _non_empty(value)

    @field_validator("api_key_env", "base_url")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _non_empty(value)

    @field_validator("timeout_seconds")
    @classmethod
    def _timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("timeout_seconds must be positive")
        return value

    @field_validator("max_retries")
    @classmethod
    def _max_retries(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_retries must be non-negative")
        return value

    @field_validator("supported_parameters")
    @classmethod
    def _supported_parameters(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_dedupe(_non_empty(value) for value in values))


class ProviderGatewayRequest(BaseModel):
    """Provider gateway request with context and output policy metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    provider: ProviderName = ProviderName.FAKE
    model: str
    worker_role: WorkerType
    prompt: str
    consent: ProviderConsent
    context_artifact_ids: list[str] = Field(default_factory=list)
    root_scopes: list[str] = Field(default_factory=list)
    output_kind: Literal["text", "worker_bundle", "draft", "proposal"] = "text"
    expected_output_paths: list[str] = Field(default_factory=list)
    temperature: float | None = None
    top_p: float | None = None
    reasoning_effort: ReasoningEffort | None = None
    max_output_tokens: int | None = None
    tool_policy: ToolPolicy = ToolPolicy.NONE
    network_policy: NetworkPolicy = NetworkPolicy.DISABLED

    @field_validator("model", "prompt")
    @classmethod
    def _text(cls, value: str) -> str:
        return _non_empty(value)

    @field_validator("context_artifact_ids")
    @classmethod
    def _artifact_ids(cls, values: list[str]) -> list[str]:
        return [validate_artifact_id(value.strip()) for value in values]

    @field_validator("root_scopes")
    @classmethod
    def _root_scopes(cls, values: list[str]) -> list[str]:
        return _dedupe(_non_empty(value) for value in values)

    @field_validator("expected_output_paths")
    @classmethod
    def _output_paths(cls, values: list[str]) -> list[str]:
        return [_repo_local_path(value) for value in values]

    @field_validator("temperature")
    @classmethod
    def _temperature(cls, value: float | None) -> float | None:
        if value is not None and not 0 <= value <= 2:
            raise ValueError("temperature must be between 0 and 2")
        return value

    @field_validator("top_p")
    @classmethod
    def _top_p(cls, value: float | None) -> float | None:
        if value is not None and not 0 < value <= 1:
            raise ValueError("top_p must be greater than 0 and at most 1")
        return value

    @field_validator("max_output_tokens")
    @classmethod
    def _max_output_tokens(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("max_output_tokens must be positive")
        return value

    @model_validator(mode="after")
    def _private_context_requires_consent(self) -> ProviderGatewayRequest:
        has_private_scope = "private" in self.root_scopes
        if has_private_scope and (
            self.consent.policy_scope is not ContextPolicyMode.PRIVATE_RESEARCH
            or not self.consent.allow_private_context
            or not self.consent.consent_granted
        ):
            raise ValueError("private provider context requires policy and consent")
        return self


class ProviderTransportResult(BaseModel):
    """Result returned by an injected provider transport."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    content: str
    status: ProviderTransportStatus = ProviderTransportStatus.COMPLETED
    finish_reason: FinishReason = FinishReason.STOP
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    raw_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("status", mode="before")
    @classmethod
    def _status(
        cls,
        value: ProviderTransportStatus | str,
    ) -> ProviderTransportStatus:
        return (
            value
            if isinstance(value, ProviderTransportStatus)
            else ProviderTransportStatus(value)
        )

    @field_validator("finish_reason", mode="before")
    @classmethod
    def _finish_reason(cls, value: FinishReason | str) -> FinishReason:
        return value if isinstance(value, FinishReason) else FinishReason(value)

    @field_validator("latency_ms", "input_tokens", "output_tokens")
    @classmethod
    def _non_negative_int(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("provider transport counts must be non-negative")
        return value

    @field_validator("cost_usd", "error_code", "error_message")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _non_empty(value)

    @field_validator("raw_metadata")
    @classmethod
    def _metadata(cls, values: dict[str, str]) -> dict[str, str]:
        return {_non_empty(key): str(value) for key, value in values.items()}


class ProviderError(BaseModel):
    """Expected provider gateway failure."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    remediation: str
    blocking: bool = True
    details: dict[str, str] = Field(default_factory=dict)

    @field_validator("code", "message", "remediation")
    @classmethod
    def _text(cls, value: str) -> str:
        return _non_empty(value)


class ProviderTransport(Protocol):
    """Injected transport for hosted provider calls."""

    def complete(
        self,
        request: ProviderGatewayRequest,
        config: ProviderConfig,
    ) -> ProviderTransportResult:
        """Return a mocked or real transport result."""


class OpenAICompatibleProvider:
    """OpenAI-compatible provider adapter over an injected transport."""

    provider_name = ProviderName.OPENAI

    def __init__(self, transport: ProviderTransport) -> None:
        self.transport = transport

    def complete(
        self,
        request: ProviderGatewayRequest,
        config: ProviderConfig,
    ) -> ProviderTransportResult:
        """Dispatch through the injected transport."""
        return self.transport.complete(request, config)


class ProviderGateway:
    """Provider gateway service with fake and injected OpenAI-compatible modes."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def call(
        self,
        request: ProviderGatewayRequest,
        *,
        config: ProviderConfig | None = None,
        provider: OpenAICompatibleProvider | None = None,
    ) -> ModelCallResult | ProviderError:
        """Call a provider through the configured gateway boundary."""
        normalized_config = config or ProviderConfig(
            provider=request.provider,
            mode=ProviderMode.FAKE,
            model=request.model,
            enabled=True,
        )
        run_id = "run.provider.0001"
        started_at = _now()
        if normalized_config.mode is ProviderMode.FAKE:
            return self._call_fake(
                request,
                config=normalized_config,
                run_id=run_id,
                started_at=started_at,
            )
        return self._call_openai_compatible(
            request,
            config=normalized_config,
            provider=provider,
            run_id=run_id,
            started_at=started_at,
        )

    def _call_fake(
        self,
        request: ProviderGatewayRequest,
        *,
        config: ProviderConfig,
        run_id: str,
        started_at: datetime,
    ) -> ModelCallResult:
        fake = FakeModelProvider()
        response = fake.generate(_model_request_from_gateway_request(request))
        content, redaction_applied = redact_text(response.content)
        return self._completed_result(
            request,
            config=config,
            run_id=run_id,
            started_at=started_at,
            content=content,
            finish_reason=response.finish_reason,
            warnings=response.warnings,
            redaction_applied=redaction_applied,
            metadata={"hosted_network": "not_used"},
        )

    def _call_openai_compatible(
        self,
        request: ProviderGatewayRequest,
        *,
        config: ProviderConfig,
        provider: OpenAICompatibleProvider | None,
        run_id: str,
        started_at: datetime,
    ) -> ModelCallResult | ProviderError:
        if not config.enabled:
            return ProviderError(
                code="provider_disabled",
                message="provider is disabled",
                remediation="Enable the provider explicitly before real calls.",
                blocking=True,
            )
        if config.api_key_env is not None and not os.environ.get(config.api_key_env):
            return ProviderError(
                code="provider_api_key_missing",
                message="provider API key environment variable is missing",
                remediation="Set the configured API key environment variable.",
                blocking=True,
                details={"api_key_env": config.api_key_env},
            )
        if provider is None:
            return ProviderError(
                code="provider_transport_missing",
                message="OpenAI-compatible provider transport is not configured",
                remediation="Inject a mocked or configured provider transport.",
                blocking=True,
            )
        capability = _negotiate_openai_compatible_capability(request, config)
        transport_result, attempt_count, retry_statuses = _complete_with_retries(
            provider,
            request,
            config,
        )
        retry_metadata = {
            "attempt_count": str(attempt_count),
            "retry_statuses": ",".join(status.value for status in retry_statuses),
            "unsupported_parameters": ",".join(capability.unsupported_parameters),
        }
        if transport_result.status is ProviderTransportStatus.CANCELLED:
            return self._provider_error_result(
                request,
                config=config,
                run_id=run_id,
                started_at=started_at,
                code="provider_cancelled",
                message=transport_result.error_message or "provider call cancelled",
                remediation="Retry only if the operator intended to continue.",
                metadata={**transport_result.raw_metadata, **retry_metadata},
            )
        if transport_result.status is ProviderTransportStatus.TIMEOUT:
            return self._provider_error_result(
                request,
                config=config,
                run_id=run_id,
                started_at=started_at,
                code="provider_timeout",
                message=transport_result.error_message or "provider timed out",
                remediation="Retry with a larger timeout or inspect provider status.",
                metadata={**transport_result.raw_metadata, **retry_metadata},
            )
        if transport_result.status is ProviderTransportStatus.RATE_LIMITED:
            return self._provider_error_result(
                request,
                config=config,
                run_id=run_id,
                started_at=started_at,
                code="provider_rate_limited",
                message=transport_result.error_message or "provider rate limited",
                remediation="Retry later or lower provider request volume.",
                metadata={**transport_result.raw_metadata, **retry_metadata},
            )
        if transport_result.status is not ProviderTransportStatus.COMPLETED:
            return self._provider_error_result(
                request,
                config=config,
                run_id=run_id,
                started_at=started_at,
                code=transport_result.error_code or "provider_call_failed",
                message=transport_result.error_message or "provider call failed",
                remediation="Inspect provider configuration and mocked transport.",
                metadata={**transport_result.raw_metadata, **retry_metadata},
            )
        validation_error = _validate_output_payload(request, transport_result.content)
        if validation_error is not None:
            return self._provider_error_result(
                request,
                config=config,
                run_id=run_id,
                started_at=started_at,
                code=validation_error.code,
                message=validation_error.message,
                remediation=validation_error.remediation,
                metadata=retry_metadata,
            )

        content, content_redacted = redact_text(transport_result.content)
        metadata, metadata_redacted = redact_mapping(transport_result.raw_metadata)
        warnings = []
        if capability.unsupported_parameters:
            warnings.append(
                "unsupported provider parameters reported by capability "
                "negotiation: "
                + ", ".join(capability.unsupported_parameters)
            )
        return self._completed_result(
            request,
            config=config,
            run_id=run_id,
            started_at=started_at,
            content=content,
            finish_reason=transport_result.finish_reason,
            warnings=warnings,
            redaction_applied=content_redacted or metadata_redacted,
            metadata={
                **metadata,
                **retry_metadata,
                "latency_ms": _optional_int(transport_result.latency_ms),
                "input_tokens": _optional_int(transport_result.input_tokens),
                "output_tokens": _optional_int(transport_result.output_tokens),
                "cost_usd": transport_result.cost_usd or "unavailable",
                "timeout_seconds": str(config.timeout_seconds),
                "max_retries": str(config.max_retries),
            },
        )

    def _provider_error_result(
        self,
        request: ProviderGatewayRequest,
        *,
        config: ProviderConfig,
        run_id: str,
        started_at: datetime,
        code: str,
        message: str,
        remediation: str,
        metadata: Mapping[str, str],
    ) -> ProviderError:
        log_path = Path(".cosheaf") / "providers" / f"{run_id}.json"
        clean_message, message_redacted = redact_text(message)
        clean_metadata, metadata_redacted = redact_mapping(metadata)
        provider_run = ProviderRunRecord(
            run_id=run_id,
            provider=request.provider,
            model=request.model,
            policy_scope=request.consent.policy_scope,
            consent=request.consent,
            private_context_sent=_private_context_sent(request),
            status=ProviderRunStatus.FAILED,
            started_at=started_at,
            ended_at=_now(),
            request_fingerprint=_request_fingerprint(request),
            log_path=normalize_repo_path(log_path),
        )
        _write_provider_error_log(
            self.context,
            log_path,
            request=request,
            config=config,
            provider_run=provider_run,
            error_code=code,
            error_message=clean_message,
            remediation=remediation,
            redaction_applied=message_redacted or metadata_redacted,
            metadata=clean_metadata,
        )
        details_log_path = provider_run.log_path or normalize_repo_path(log_path)
        return ProviderError(
            code=code,
            message=clean_message,
            remediation=remediation,
            blocking=True,
            details={"log_path": details_log_path},
        )

    def _completed_result(
        self,
        request: ProviderGatewayRequest,
        *,
        config: ProviderConfig,
        run_id: str,
        started_at: datetime,
        content: str,
        finish_reason: FinishReason,
        warnings: list[str],
        redaction_applied: bool,
        metadata: Mapping[str, str],
    ) -> ModelCallResult:
        ended_at = _now()
        log_path = Path(".cosheaf") / "providers" / f"{run_id}.json"
        provider_run = ProviderRunRecord(
            run_id=run_id,
            provider=request.provider,
            model=request.model,
            policy_scope=request.consent.policy_scope,
            consent=request.consent,
            private_context_sent=_private_context_sent(request),
            status=ProviderRunStatus.COMPLETED,
            started_at=started_at,
            ended_at=ended_at,
            request_fingerprint=_request_fingerprint(request),
            log_path=normalize_repo_path(log_path),
        )
        result = ModelCallResult(
            request_id="request.provider.0001",
            provider=request.provider,
            model=request.model,
            status=ProviderRunStatus.COMPLETED,
            content=content,
            finish_reason=finish_reason,
            provider_run=provider_run,
            warnings=warnings,
        )
        _write_provider_log(
            self.context,
            log_path,
            request=request,
            config=config,
            provider_run=provider_run,
            result=result,
            redaction_applied=redaction_applied,
            metadata=metadata,
        )
        return result


def _model_request_from_gateway_request(
    request: ProviderGatewayRequest,
) -> ModelRequest:
    return ModelRequest(
        provider=request.provider,
        model=request.model,
        prompt=request.prompt,
        temperature=request.temperature,
        top_p=request.top_p,
        reasoning_effort=request.reasoning_effort,
        max_output_tokens=request.max_output_tokens,
        tool_policy=request.tool_policy,
        network_policy=request.network_policy,
    )


def _validate_output_payload(
    request: ProviderGatewayRequest,
    content: str,
) -> ProviderError | None:
    if request.output_kind != "worker_bundle":
        return None
    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        return ProviderError(
            code="provider_output_validation_failed",
            message=f"provider output is not valid JSON: {exc.msg}",
            remediation="Ask the provider for a valid WorkerBundle JSON object.",
            blocking=True,
        )
    if not isinstance(raw, dict):
        return ProviderError(
            code="provider_output_validation_failed",
            message="provider WorkerBundle output must be a JSON object",
            remediation="Ask the provider for a valid WorkerBundle JSON object.",
            blocking=True,
        )
    try:
        WorkerBundleV2.model_validate(raw)
    except ValueError as exc:
        return ProviderError(
            code="provider_output_validation_failed",
            message=f"provider WorkerBundle output is invalid: {exc}",
            remediation="Ask the provider for a valid WorkerBundle v2 payload.",
            blocking=True,
        )
    return None


def _negotiate_openai_compatible_capability(
    request: ProviderGatewayRequest,
    config: ProviderConfig,
) -> ProviderCapability:
    supported = list(config.supported_parameters)
    unsupported = [
        name
        for name in (
            "model",
            "temperature",
            "top_p",
            "reasoning_effort",
            "tool_policy",
        )
        if _is_unsupported_gateway_parameter(request, config, name)
    ]
    return ProviderCapability(
        provider=config.provider,
        model=request.model,
        supported_parameters=supported,
        unsupported_parameters=unsupported,
        hosted_provider=True,
        network_access=request.network_policy is NetworkPolicy.EXPLICIT_ALLOW,
        notes="OpenAI-compatible provider boundary; transport may be mocked.",
    )


def _is_unsupported_gateway_parameter(
    request: ProviderGatewayRequest,
    config: ProviderConfig,
    name: str,
) -> bool:
    if name == "model":
        return request.model != config.model and name not in config.supported_parameters
    if name == "temperature":
        return (
            request.temperature is not None
            and name not in config.supported_parameters
        )
    if name == "top_p":
        return request.top_p is not None and name not in config.supported_parameters
    if name == "reasoning_effort":
        return (
            request.reasoning_effort is not None
            and name not in config.supported_parameters
        )
    if name == "tool_policy":
        return (
            request.tool_policy is not ToolPolicy.NONE
            and name not in config.supported_parameters
        )
    return False


def _complete_with_retries(
    provider: OpenAICompatibleProvider,
    request: ProviderGatewayRequest,
    config: ProviderConfig,
) -> tuple[ProviderTransportResult, int, list[ProviderTransportStatus]]:
    retry_statuses: list[ProviderTransportStatus] = []
    max_attempts = config.max_retries + 1
    for attempt_index in range(max_attempts):
        result = provider.complete(request, config)
        if (
            result.status not in _RETRYABLE_STATUSES
            or attempt_index == max_attempts - 1
        ):
            return result, attempt_index + 1, retry_statuses
        retry_statuses.append(result.status)
    raise RuntimeError("provider retry loop exhausted unexpectedly")


def _write_provider_log(
    context: RepoContext,
    relative_path: Path,
    *,
    request: ProviderGatewayRequest,
    config: ProviderConfig,
    provider_run: ProviderRunRecord,
    result: ModelCallResult,
    redaction_applied: bool,
    metadata: Mapping[str, str],
) -> None:
    path = context.resolve(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    log = {
        "schema_version": 1,
        "run_id": provider_run.run_id,
        "provider": request.provider.value,
        "mode": config.mode.value,
        "model": request.model,
        "status": result.status.value,
        "policy_scope": request.consent.policy_scope.value,
        "consent_granted": request.consent.consent_granted,
        "private_context_sent": provider_run.private_context_sent,
        "request_fingerprint": provider_run.request_fingerprint,
        "output_kind": request.output_kind,
        "output_paths": request.expected_output_paths,
        "redaction_applied": redaction_applied,
        "metadata": dict(sorted(metadata.items())),
    }
    attempt_count = metadata.get("attempt_count")
    if attempt_count is not None and attempt_count != "unavailable":
        log["attempt_count"] = int(attempt_count)
    retry_statuses = metadata.get("retry_statuses")
    if retry_statuses:
        log["retry_statuses"] = retry_statuses.split(",")
    else:
        log["retry_statuses"] = []
    unsupported_parameters = metadata.get("unsupported_parameters")
    if unsupported_parameters:
        log["unsupported_parameters"] = unsupported_parameters.split(",")
    else:
        log["unsupported_parameters"] = []
    _copy_optional_int_log_field(log, metadata, "latency_ms")
    _copy_optional_int_log_field(log, metadata, "input_tokens")
    _copy_optional_int_log_field(log, metadata, "output_tokens")
    cost_usd = metadata.get("cost_usd")
    if cost_usd is not None and cost_usd != "unavailable":
        log["cost_usd"] = cost_usd
    path.write_text(
        json.dumps(log, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_provider_error_log(
    context: RepoContext,
    relative_path: Path,
    *,
    request: ProviderGatewayRequest,
    config: ProviderConfig,
    provider_run: ProviderRunRecord,
    error_code: str,
    error_message: str,
    remediation: str,
    redaction_applied: bool,
    metadata: Mapping[str, str],
) -> None:
    path = context.resolve(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    log = {
        "schema_version": 1,
        "run_id": provider_run.run_id,
        "provider": request.provider.value,
        "mode": config.mode.value,
        "model": request.model,
        "status": provider_run.status.value,
        "policy_scope": request.consent.policy_scope.value,
        "consent_granted": request.consent.consent_granted,
        "private_context_sent": provider_run.private_context_sent,
        "request_fingerprint": provider_run.request_fingerprint,
        "output_kind": request.output_kind,
        "output_paths": request.expected_output_paths,
        "error_code": error_code,
        "error_message": error_message,
        "remediation": remediation,
        "redaction_applied": redaction_applied,
        "metadata": dict(sorted(metadata.items())),
    }
    attempt_count = metadata.get("attempt_count")
    if attempt_count is not None and attempt_count != "unavailable":
        log["attempt_count"] = int(attempt_count)
    retry_statuses = metadata.get("retry_statuses")
    if retry_statuses:
        log["retry_statuses"] = retry_statuses.split(",")
    else:
        log["retry_statuses"] = []
    unsupported_parameters = metadata.get("unsupported_parameters")
    if unsupported_parameters:
        log["unsupported_parameters"] = unsupported_parameters.split(",")
    else:
        log["unsupported_parameters"] = []
    path.write_text(
        json.dumps(log, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def redact_text(value: str) -> tuple[str, bool]:
    """Redact common secret value shapes from text."""
    redacted = SECRET_VALUE_PATTERN.sub(REDACTED, value)
    return redacted, redacted != value


def redact_mapping(values: Mapping[str, str]) -> tuple[dict[str, str], bool]:
    """Redact secret-looking keys and values from provider metadata."""
    redacted: dict[str, str] = {}
    changed = False
    for key, value in values.items():
        if _secret_key(key):
            redacted[key] = REDACTED
            changed = True
            continue
        clean_value, value_changed = redact_text(str(value))
        redacted[key] = clean_value
        changed = changed or value_changed
    return redacted, changed


def _secret_key(key: str) -> bool:
    normalized = key.strip().lower().replace("_", "-")
    return any(
        marker in normalized
        for marker in ("authorization", "api-key", "apikey", "token", "secret")
    )


def _request_fingerprint(request: ProviderGatewayRequest) -> str:
    payload = {
        "provider": request.provider.value,
        "model": request.model,
        "worker_role": request.worker_role.value,
        "prompt": request.prompt,
        "context_artifact_ids": request.context_artifact_ids,
        "root_scopes": request.root_scopes,
        "output_kind": request.output_kind,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _private_context_sent(request: ProviderGatewayRequest) -> bool:
    return "private" in request.root_scopes and request.consent.allow_private_context


def _non_empty(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("text value must be non-empty")
    return stripped


def _repo_local_path(value: str) -> str:
    normalized = normalize_repo_path(value)
    if (
        not normalized
        or normalized == ".."
        or normalized.startswith("../")
        or Path(value).is_absolute()
    ):
        raise ValueError("path must be repository-local")
    if "accepted" in Path(normalized).parts:
        raise ValueError("provider output paths must not target accepted knowledge")
    return normalized


def _dedupe(values: Sequence[str] | Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _optional_int(value: int | None) -> str:
    return str(value) if value is not None else "unavailable"


def _copy_optional_int_log_field(
    log: dict[str, object],
    metadata: Mapping[str, str],
    key: str,
) -> None:
    value = metadata.get(key)
    if value is None or value == "unavailable":
        return
    log[key] = int(value)


def _now() -> datetime:
    return datetime.now(tz=UTC).replace(microsecond=0)


__all__ = [
    "OpenAICompatibleProvider",
    "ProviderConfig",
    "ProviderError",
    "ProviderGateway",
    "ProviderGatewayRequest",
    "ProviderMode",
    "ProviderTransport",
    "ProviderTransportResult",
    "ProviderTransportStatus",
    "redact_mapping",
    "redact_text",
]
