from __future__ import annotations

from cosheaf.agent.model_provider import (
    FakeModelProvider,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    NetworkPolicy,
    ProviderCapability,
    ProviderName,
    ReasoningEffort,
    ToolPolicy,
)


def _generate_with_protocol(
    provider: ModelProvider,
    request: ModelRequest,
) -> ModelResponse:
    return provider.generate(request)


def test_model_request_serializes_provider_neutral_config_fields() -> None:
    request = ModelRequest(
        provider=ProviderName.FAKE,
        model="fake-deterministic",
        prompt="Summarize the current issue context.",
        temperature=0.2,
        top_p=0.9,
        reasoning_effort=ReasoningEffort.MEDIUM,
        max_output_tokens=256,
        tool_policy=ToolPolicy.NONE,
        network_policy=NetworkPolicy.DISABLED,
    )

    serialized = request.to_dict()

    assert list(serialized) == [
        "provider",
        "model",
        "prompt",
        "temperature",
        "top_p",
        "reasoning_effort",
        "max_output_tokens",
        "tool_policy",
        "network_policy",
        "metadata",
    ]
    assert serialized["provider"] == "fake"
    assert serialized["model"] == "fake-deterministic"
    assert request.to_json() == request.to_json()


def test_fake_model_provider_generates_deterministic_response() -> None:
    provider = FakeModelProvider()
    request = ModelRequest(
        provider=ProviderName.FAKE,
        model="fake-deterministic",
        prompt="Draft reviewer-facing notes only.",
    )

    first = _generate_with_protocol(provider, request)
    second = provider.generate(request)

    assert first == second
    assert first.provider == "fake"
    assert first.model == "fake-deterministic"
    assert first.content == (
        "[fake:fake-deterministic] Draft reviewer-facing notes only."
    )
    assert first.finish_reason == "stop"
    assert first.capability.unsupported_parameters == []
    assert first.to_json() == second.to_json()


def test_unsupported_parameters_are_recorded_by_capability_negotiation() -> None:
    provider = FakeModelProvider()
    request = ModelRequest(
        provider=ProviderName.FAKE,
        model="fake-deterministic",
        prompt="Use advanced hosted-provider features.",
        temperature=0.7,
        top_p=0.8,
        reasoning_effort=ReasoningEffort.HIGH,
        tool_policy=ToolPolicy.READ_ONLY,
        network_policy=NetworkPolicy.EXPLICIT_ALLOW,
    )

    capability = provider.negotiate_capability(request)
    response = provider.generate(request)

    assert isinstance(capability, ProviderCapability)
    assert capability.unsupported_parameters == [
        "temperature",
        "top_p",
        "reasoning_effort",
        "tool_policy",
        "network_policy",
    ]
    assert response.capability == capability
    assert response.finish_reason == "stop"
    assert response.warnings == [
        "fake provider ignored unsupported parameters: "
        "temperature, top_p, reasoning_effort, tool_policy, network_policy"
    ]


def test_fake_provider_records_unsupported_provider_and_model_without_overlap() -> None:
    provider = FakeModelProvider()
    request = ModelRequest(
        provider=ProviderName.OPENAI,
        model="not-a-fake-model",
        prompt="Route through fake provider for tests.",
    )

    capability = provider.negotiate_capability(request)

    assert capability.supported_parameters == ["prompt", "max_output_tokens"]
    assert capability.unsupported_parameters == ["provider", "model"]
