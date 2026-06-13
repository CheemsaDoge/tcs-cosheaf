from __future__ import annotations

import json
from pathlib import Path

from cosheaf.agent.model_provider import NetworkPolicy, ProviderName
from cosheaf.agent.providers import (
    OpenAICompatibleProvider,
    ProviderConfig,
    ProviderGateway,
    ProviderGatewayRequest,
    ProviderMode,
    ProviderTransportResult,
    ProviderTransportStatus,
)
from cosheaf.agent.task import WorkerType
from cosheaf.security.provider_logs import (
    scan_provider_log_file,
    scan_provider_log_text,
)
from cosheaf.services.models import ContextPolicyMode, ModelCallResult, ProviderConsent
from cosheaf.storage.repo import RepoContext


class StaticTransport:
    def __init__(self, content: str, metadata: dict[str, str] | None = None) -> None:
        self.content = content
        self.metadata = metadata or {}

    def complete(
        self,
        request: ProviderGatewayRequest,
        config: ProviderConfig,
    ) -> ProviderTransportResult:
        return ProviderTransportResult(
            content=self.content,
            status=ProviderTransportStatus.COMPLETED,
            raw_metadata=self.metadata,
        )


def _public_consent() -> ProviderConsent:
    return ProviderConsent(
        consent_required=False,
        consent_granted=False,
        allow_private_context=False,
        policy_scope=ContextPolicyMode.PUBLIC,
    )


def _worker_bundle_json() -> str:
    return json.dumps(
        {
            "bundle_id": "bundle.issue.security.reasoner.0001",
            "task_id": "task.issue.security.reasoner",
            "worker_role": "reasoner",
            "created_at": "2026-06-10T00:00:00Z",
            "summary": "Provider returned review-only output.",
            "used_artifacts": ["claim.security.public"],
            "used_sources": [],
            "claims": ["This is review context, not accepted knowledge."],
            "proposed_artifacts": [
                {
                    "path": "kb/draft/claims/security-provider.yaml",
                    "summary": "Draft-only provider proposal.",
                }
            ],
            "verification_requests": ["Run validate and gate before review."],
            "failures_or_counterexamples": ["No external verifier was run."],
            "risk_flags": ["needs_human_review"],
            "next_steps": ["Request human review."],
            "confidence": "low",
        }
    )


def test_synthetic_provider_log_leaks_are_detected() -> None:
    leaked = json.dumps(
        {
            "metadata": {
                "Authorization": "Bearer provider-token-1234567890",
                "OPENAI_API_KEY": "sk-proj-leakedproviderkey1234567890",
            },
            "stderr": "BEGIN HIDDEN REASONING: do not show chain of thought",
            "environment": "\n".join(
                [
                    "PATH=C:\\Users\\example\\bin",
                    "HOME=C:\\Users\\example",
                    "OPENAI_API_KEY=sk-envleakedproviderkey123456",
                    "HTTPS_PROXY=http://127.0.0.1:3067",
                ]
            ),
            "context": (
                "UNAPPROVED_PRIVATE_CONTEXT "
                "kb/private/draft/claims/private.yaml private-secret-value"
            ),
            "cwd": "C:\\Users\\example\\research\\kb\\private\\draft",
        },
        ensure_ascii=True,
        indent=2,
    )

    findings = scan_provider_log_text(leaked, path="synthetic-provider-log.json")

    assert {finding.kind for finding in findings} >= {
        "api_key",
        "bearer_token",
        "environment_dump",
        "secret_env_value",
        "hidden_reasoning",
        "unapproved_private_context",
        "absolute_private_path",
    }
    assert all(finding.path == "synthetic-provider-log.json" for finding in findings)
    assert all(finding.message for finding in findings)


def test_redacted_provider_log_shape_passes_scanner() -> None:
    redacted_log = {
        "schema_version": 1,
        "run_id": "run.provider.0001",
        "provider": "openai",
        "mode": "openai_compatible",
        "model": "gpt-test",
        "status": "completed",
        "policy_scope": "public",
        "consent_granted": False,
        "private_context_sent": False,
        "request_fingerprint": "sha256:" + "0" * 64,
        "output_kind": "worker_bundle",
        "output_paths": ["kb/draft/claims/security-provider.yaml"],
        "redaction_applied": True,
        "metadata": {
            "Authorization": "<redacted>",
            "api_key_env": "COSHEAF_TEST_API_KEY",
            "api_key_present": "true",
            "hosted_network": "not_used",
        },
    }
    text = json.dumps(redacted_log, ensure_ascii=True, indent=2)

    assert scan_provider_log_text(text, path=".cosheaf/providers/run.json") == []


def test_scanner_accepts_generated_redacted_provider_log(tmp_path: Path) -> None:
    transport = StaticTransport(
        _worker_bundle_json(),
        metadata={
            "Authorization": "Bearer sk-generated-provider-secret",
            "request_id": "req-sec",
        },
    )
    gateway = ProviderGateway(RepoContext(tmp_path))

    result = gateway.call(
        ProviderGatewayRequest(
            provider=ProviderName.OPENAI,
            model="mock-openai-compatible",
            worker_role=WorkerType.REASONER,
            prompt="Use sk-generated-provider-secret only as a redaction fixture.",
            consent=_public_consent(),
            context_artifact_ids=["claim.security.public"],
            root_scopes=["public"],
            output_kind="worker_bundle",
            expected_output_paths=["kb/draft/claims/security-provider.yaml"],
            network_policy=NetworkPolicy.EXPLICIT_ALLOW,
        ),
        config=ProviderConfig(
            provider=ProviderName.OPENAI,
            mode=ProviderMode.OPENAI_COMPATIBLE,
            model="mock-openai-compatible",
            enabled=True,
            api_key_env=None,
        ),
        provider=OpenAICompatibleProvider(transport=transport),
    )

    assert isinstance(result, ModelCallResult)
    assert result.provider_run.log_path is not None
    assert scan_provider_log_file(tmp_path / result.provider_run.log_path) == []
