from __future__ import annotations

import json
from collections.abc import Mapping
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from cosheaf.agent.model_provider import NetworkPolicy, ProviderName
from cosheaf.agent.providers import (
    OpenAICompatibleHttpTransport,
    OpenAICompatibleProvider,
    ProviderConfig,
    ProviderGateway,
    ProviderGatewayRequest,
    ProviderMode,
    ProviderTransportResult,
    ProviderTransportStatus,
)
from cosheaf.agent.task import WorkerType
from cosheaf.services.models import (
    ContextPolicyMode,
    ModelCallResult,
    ProviderConsent,
)
from cosheaf.storage.repo import RepoContext


def _synthetic_secret(label: str) -> str:
    return "sk-" + "cosheaf-fixture-" + label


class FakeHttpResponse:
    def __init__(
        self,
        payload: bytes,
        *,
        status: int = 200,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.payload = payload
        self.status = status
        self.headers = dict(headers or {})

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload

    def getcode(self) -> int:
        return self.status


class FakeUrlopen:
    def __init__(
        self,
        response: FakeHttpResponse | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[Request, float]] = []

    def __call__(self, request: Request, *, timeout: float) -> FakeHttpResponse:
        self.calls.append((request, timeout))
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise AssertionError("fake urlopen has no response")
        return self.response


def _public_consent(*, granted: bool = True) -> ProviderConsent:
    return ProviderConsent(
        consent_required=True,
        consent_granted=granted,
        allow_private_context=False,
        policy_scope=ContextPolicyMode.PUBLIC,
    )


def _request(
    *,
    prompt: str = "Return a review-only response.",
    network_policy: NetworkPolicy = NetworkPolicy.EXPLICIT_ALLOW,
    consent_granted: bool = True,
) -> ProviderGatewayRequest:
    return ProviderGatewayRequest(
        provider=ProviderName.OPENAI,
        model="gpt-test",
        worker_role=WorkerType.REASONER,
        prompt=prompt,
        consent=_public_consent(granted=consent_granted),
        context_artifact_ids=["definition.graph"],
        root_scopes=["public"],
        output_kind="text",
        network_policy=network_policy,
        max_output_tokens=64,
    )


def _config(*, api_key_env: str | None = "COSHEAF_TEST_API_KEY") -> ProviderConfig:
    return ProviderConfig(
        provider=ProviderName.OPENAI,
        mode=ProviderMode.OPENAI_COMPATIBLE,
        model="gpt-test",
        enabled=True,
        api_key_env=api_key_env,
        timeout_seconds=7,
        max_retries=0,
        base_url="https://provider.test/v1/chat/completions",
        supported_parameters=("prompt", "model", "max_output_tokens"),
    )


def _openai_payload(content: str = "Review-only transport response.") -> bytes:
    return json.dumps(
        {
            "id": "chatcmpl-test",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": content},
                }
            ],
            "usage": {
                "prompt_tokens": 11,
                "completion_tokens": 5,
            },
        }
    ).encode("utf-8")


def _empty_headers() -> Message:
    return Message()


def test_http_transport_posts_openai_compatible_request_and_parses_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_key = _synthetic_secret("request")
    monkeypatch.setenv("COSHEAF_TEST_API_KEY", api_key)
    urlopen = FakeUrlopen(FakeHttpResponse(_openai_payload()))
    transport = OpenAICompatibleHttpTransport(urlopen=urlopen)

    result = transport.complete(_request(), _config())

    assert isinstance(result, ProviderTransportResult)
    assert result.status is ProviderTransportStatus.COMPLETED
    assert result.content == "Review-only transport response."
    assert result.input_tokens == 11
    assert result.output_tokens == 5
    assert result.raw_metadata["http_status"] == "200"
    assert result.raw_metadata["response_id"] == "chatcmpl-test"
    assert len(urlopen.calls) == 1

    request, timeout = urlopen.calls[0]
    assert timeout == 7
    assert request.full_url == "https://provider.test/v1/chat/completions"
    assert request.get_method() == "POST"
    assert request.headers["Authorization"] == f"Bearer {api_key}"
    assert isinstance(request.data, bytes)
    body = json.loads(request.data.decode("utf-8"))
    assert body["model"] == "gpt-test"
    assert body["messages"] == [
        {"role": "user", "content": "Return a review-only response."}
    ]
    assert body["max_tokens"] == 64


def test_http_transport_fails_closed_without_explicit_config_or_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("COSHEAF_TEST_API_KEY", raising=False)
    urlopen = FakeUrlopen(FakeHttpResponse(_openai_payload()))
    transport = OpenAICompatibleHttpTransport(urlopen=urlopen)

    no_network = transport.complete(
        _request(network_policy=NetworkPolicy.DISABLED),
        _config(),
    )
    missing_consent = transport.complete(
        _request(consent_granted=False),
        _config(),
    )
    missing_key_source = transport.complete(_request(), _config(api_key_env=None))
    missing_key_value = transport.complete(_request(), _config())

    assert missing_consent.status is ProviderTransportStatus.ERROR
    assert missing_consent.error_code == "provider_confirm_send_required"
    assert no_network.status is ProviderTransportStatus.ERROR
    assert no_network.error_code == "provider_network_not_allowed"
    assert missing_key_source.status is ProviderTransportStatus.ERROR
    assert missing_key_source.error_code == "provider_config_missing"
    assert missing_key_value.status is ProviderTransportStatus.ERROR
    assert missing_key_value.error_code == "provider_api_key_missing"
    assert urlopen.calls == []


def test_http_transport_maps_timeout_rate_limit_and_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COSHEAF_TEST_API_KEY", _synthetic_secret("errors"))

    timeout = OpenAICompatibleHttpTransport(
        urlopen=FakeUrlopen(error=TimeoutError("slow provider"))
    ).complete(_request(), _config())
    wrapped_timeout = OpenAICompatibleHttpTransport(
        urlopen=FakeUrlopen(error=URLError(TimeoutError("wrapped timeout")))
    ).complete(_request(), _config())
    rate_limited = OpenAICompatibleHttpTransport(
        urlopen=FakeUrlopen(
            error=HTTPError(
                "https://provider.test/v1/chat/completions",
                429,
                "Too Many Requests",
                _empty_headers(),
                None,
            )
        )
    ).complete(_request(), _config())
    http_error = OpenAICompatibleHttpTransport(
        urlopen=FakeUrlopen(
            error=HTTPError(
                "https://provider.test/v1/chat/completions",
                500,
                "Internal Server Error",
                _empty_headers(),
                None,
            )
        )
    ).complete(_request(), _config())

    assert timeout.status is ProviderTransportStatus.TIMEOUT
    assert timeout.error_code == "provider_timeout"
    assert wrapped_timeout.status is ProviderTransportStatus.TIMEOUT
    assert wrapped_timeout.error_code == "provider_timeout"
    assert rate_limited.status is ProviderTransportStatus.RATE_LIMITED
    assert rate_limited.error_code == "provider_rate_limited"
    assert http_error.status is ProviderTransportStatus.FAILED
    assert http_error.error_code == "provider_http_error"
    assert http_error.raw_metadata["http_status"] == "500"


def test_http_transport_maps_network_invalid_json_and_malformed_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COSHEAF_TEST_API_KEY", _synthetic_secret("malformed"))

    network = OpenAICompatibleHttpTransport(
        urlopen=FakeUrlopen(error=URLError("dns unavailable"))
    ).complete(_request(), _config())
    invalid_json = OpenAICompatibleHttpTransport(
        urlopen=FakeUrlopen(FakeHttpResponse(b"not json"))
    ).complete(_request(), _config())
    malformed = OpenAICompatibleHttpTransport(
        urlopen=FakeUrlopen(FakeHttpResponse(b'{"choices": []}'))
    ).complete(_request(), _config())

    assert network.status is ProviderTransportStatus.ERROR
    assert network.error_code == "provider_network_error"
    assert invalid_json.status is ProviderTransportStatus.ERROR
    assert invalid_json.error_code == "provider_invalid_json"
    assert malformed.status is ProviderTransportStatus.FAILED
    assert malformed.error_code == "provider_malformed_response"


def test_http_transport_result_is_redacted_by_gateway_logs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_secret = _synthetic_secret("request-log")
    response_secret = _synthetic_secret("response-log")
    monkeypatch.setenv("COSHEAF_TEST_API_KEY", request_secret)
    urlopen = FakeUrlopen(
        FakeHttpResponse(_openai_payload(f"Provider leaked {response_secret}."))
    )
    gateway = ProviderGateway(RepoContext(tmp_path))

    result = gateway.call(
        _request(prompt=f"Never log {request_secret}."),
        config=_config(),
        provider=OpenAICompatibleProvider(
            transport=OpenAICompatibleHttpTransport(urlopen=urlopen)
        ),
    )

    assert isinstance(result, ModelCallResult)
    assert response_secret not in result.content
    assert "<redacted>" in result.content
    assert result.provider_run.log_path is not None
    log_text = (tmp_path / result.provider_run.log_path).read_text(encoding="utf-8")
    log = json.loads(log_text)
    assert request_secret not in log_text
    assert response_secret not in log_text
    assert log["redaction_applied"] is True
    assert log["metadata"]["http_status"] == "200"
