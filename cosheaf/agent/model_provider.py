"""Provider-neutral model interface with a deterministic fake provider.

This module defines data contracts only. It does not import hosted provider
SDKs, open network connections, or execute tools.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ReasoningEffort(StrEnum):
    """Provider-neutral reasoning effort hint."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProviderName(StrEnum):
    """Provider-neutral model provider identifiers."""

    FAKE = "fake"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"


class ToolPolicy(StrEnum):
    """Provider-neutral tool-use policy."""

    NONE = "none"
    READ_ONLY = "read_only"
    LOCAL_TOOLS = "local_tools"
    VERIFIER_TOOLS = "verifier_tools"


class NetworkPolicy(StrEnum):
    """Provider-neutral network access policy."""

    DISABLED = "disabled"
    EXPLICIT_ALLOW = "explicit_allow"


class FinishReason(StrEnum):
    """Normalized provider response finish reason."""

    STOP = "stop"
    LENGTH = "length"
    ERROR = "error"


class ModelProviderModel(BaseModel):
    """Shared strict base for provider-neutral DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic machine-readable mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON for this model."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class ModelRequest(ModelProviderModel):
    """Provider-neutral request configuration for a model call."""

    provider: ProviderName = ProviderName.FAKE
    model: str = "fake-deterministic"
    prompt: str
    temperature: float | None = None
    top_p: float | None = None
    reasoning_effort: ReasoningEffort | None = None
    max_output_tokens: int | None = None
    tool_policy: ToolPolicy = ToolPolicy.NONE
    network_policy: NetworkPolicy = NetworkPolicy.DISABLED
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("model", "prompt")
    @classmethod
    def _validate_non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("model request text fields must be non-empty")
        return normalized

    @field_validator("temperature")
    @classmethod
    def _validate_temperature(cls, value: float | None) -> float | None:
        if value is not None and not 0 <= value <= 2:
            raise ValueError("temperature must be between 0 and 2")
        return value

    @field_validator("top_p")
    @classmethod
    def _validate_top_p(cls, value: float | None) -> float | None:
        if value is not None and not 0 < value <= 1:
            raise ValueError("top_p must be greater than 0 and at most 1")
        return value

    @field_validator("max_output_tokens")
    @classmethod
    def _validate_max_output_tokens(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("max_output_tokens must be positive when provided")
        return value

    @field_validator("metadata")
    @classmethod
    def _normalize_metadata(cls, values: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key, value in values.items():
            key_text = key.strip()
            value_text = value.strip()
            if not key_text or not value_text:
                raise ValueError("metadata keys and values must be non-empty")
            normalized[key_text] = value_text
        return normalized


class ProviderCapability(ModelProviderModel):
    """Capability negotiation result for one provider/request pair."""

    provider: ProviderName
    model: str
    supported_parameters: list[str] = Field(default_factory=list)
    unsupported_parameters: list[str] = Field(default_factory=list)
    hosted_provider: bool = False
    network_access: bool = False
    notes: str = ""

    @field_validator("model")
    @classmethod
    def _validate_non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("provider capability text fields must be non-empty")
        return normalized

    @field_validator("supported_parameters", "unsupported_parameters")
    @classmethod
    def _normalize_parameter_names(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            _validate_parameter_name(value) for value in values
        )

    @field_validator("notes")
    @classmethod
    def _strip_notes(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def _reject_overlap(self) -> ProviderCapability:
        overlap = set(self.supported_parameters).intersection(
            self.unsupported_parameters
        )
        if overlap:
            names = ", ".join(sorted(overlap))
            raise ValueError(
                "parameters cannot be both supported and unsupported: "
                f"{names}"
            )
        return self


class ModelResponse(ModelProviderModel):
    """Provider-neutral model response."""

    provider: ProviderName
    model: str
    content: str
    finish_reason: FinishReason = FinishReason.STOP
    capability: ProviderCapability
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("model", "content")
    @classmethod
    def _validate_non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("model response text fields must be non-empty")
        return normalized

    @field_validator("warnings")
    @classmethod
    def _normalize_warnings(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            _validate_non_empty_text(value) for value in values
        )

    @field_validator("metadata")
    @classmethod
    def _normalize_metadata(cls, values: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key, value in values.items():
            key_text = key.strip()
            value_text = value.strip()
            if not key_text or not value_text:
                raise ValueError("metadata keys and values must be non-empty")
            normalized[key_text] = value_text
        return normalized


class ModelProvider(Protocol):
    """Protocol implemented by provider-neutral model adapters."""

    provider_name: ProviderName

    def negotiate_capability(self, request: ModelRequest) -> ProviderCapability:
        """Return provider capability metadata for a request."""

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Return a provider-neutral response for a request."""


class FakeModelProvider:
    """Deterministic local fake provider for tests and disabled hosted runtime."""

    provider_name = ProviderName.FAKE

    supported_parameters = (
        "prompt",
        "max_output_tokens",
    )

    def negotiate_capability(self, request: ModelRequest) -> ProviderCapability:
        """Record which request parameters the fake provider will ignore."""
        unsupported = [
            name
            for name in (
                "provider",
                "model",
                "temperature",
                "top_p",
                "reasoning_effort",
                "max_output_tokens",
                "tool_policy",
                "network_policy",
            )
            if _is_unsupported_request_parameter(request, name)
        ]
        return ProviderCapability(
            provider=self.provider_name,
            model=request.model,
            supported_parameters=list(self.supported_parameters),
            unsupported_parameters=unsupported,
            hosted_provider=False,
            network_access=False,
            notes="Deterministic fake provider only; no hosted model call.",
        )

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Return a deterministic echo-style response without external calls."""
        capability = self.negotiate_capability(request)
        content = f"[fake:{request.model}] {request.prompt}"
        finish_reason = FinishReason.STOP
        if (
            request.max_output_tokens is not None
            and len(content.split()) > request.max_output_tokens
        ):
            content = _truncate_by_token_budget(content, request.max_output_tokens)
            finish_reason = FinishReason.LENGTH

        warnings = []
        if capability.unsupported_parameters:
            warnings.append(
                "fake provider ignored unsupported parameters: "
                + ", ".join(capability.unsupported_parameters)
            )

        return ModelResponse(
            provider=self.provider_name,
            model=request.model,
            content=content,
            finish_reason=finish_reason,
            capability=capability,
            warnings=warnings,
            metadata={
                "hosted_llm": "not_used",
                "network": "not_used",
            },
        )


def _is_unsupported_request_parameter(request: ModelRequest, name: str) -> bool:
    if name == "provider":
        return request.provider is not ProviderName.FAKE
    if name == "model":
        return request.model != "fake-deterministic"
    if name == "temperature":
        return request.temperature is not None
    if name == "top_p":
        return request.top_p is not None
    if name == "reasoning_effort":
        return request.reasoning_effort is not None
    if name == "max_output_tokens":
        return False
    if name == "tool_policy":
        return request.tool_policy is not ToolPolicy.NONE
    if name == "network_policy":
        return request.network_policy is not NetworkPolicy.DISABLED
    return False


def _truncate_by_token_budget(content: str, max_output_tokens: int) -> str:
    tokens = content.split()
    if len(tokens) <= max_output_tokens:
        return content
    return " ".join(tokens[:max_output_tokens])


def _validate_parameter_name(value: str) -> str:
    return _validate_non_empty_text(value).strip()


def _validate_non_empty_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("text values must be non-empty")
    return normalized


def _dedupe_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
