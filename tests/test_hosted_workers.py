from __future__ import annotations

import json
from pathlib import Path

from cosheaf.agent.hosted_workers import (
    HostedWorkerInput,
    HostedWorkerOutput,
    HostedWorkerService,
    HostedWorkerStatus,
)
from cosheaf.agent.model_provider import ProviderName
from cosheaf.agent.providers import (
    OpenAICompatibleProvider,
    ProviderConfig,
    ProviderMode,
    ProviderTransportResult,
    ProviderTransportStatus,
)
from cosheaf.agent.roles import RoleName
from cosheaf.agent.worker_bundle_v2 import WorkerBundleV2
from cosheaf.services.models import ContextPolicyMode, ProviderConsent
from cosheaf.storage.repo import RepoContext


class StaticTransport:
    def __init__(self, content: str) -> None:
        self.content = content

    def complete(self, request, config):  # type: ignore[no-untyped-def]
        return ProviderTransportResult(
            content=self.content,
            status=ProviderTransportStatus.COMPLETED,
        )


def _public_consent() -> ProviderConsent:
    return ProviderConsent(
        consent_required=False,
        consent_granted=False,
        allow_private_context=False,
        policy_scope=ContextPolicyMode.PUBLIC,
    )


def _request(role: RoleName = RoleName.REASONER) -> HostedWorkerInput:
    return HostedWorkerInput(
        issue_id="issue.hosted.worker.0001",
        role=role,
        prompt="Prepare review-only worker output.",
        context_artifact_ids=["definition.graph"],
        root_scopes=["public"],
        consent=_public_consent(),
    )


def _bundle_json(
    *,
    role: str = "reasoner",
    proposed_path: str = "kb/draft/claims/hosted-worker.yaml",
    summary: str = "Hosted worker produced review-only output.",
) -> str:
    return json.dumps(
        {
            "bundle_id": f"bundle.issue.hosted.worker.0001.{role}.0001",
            "task_id": f"task.issue.hosted.worker.0001.{role}",
            "worker_role": role,
            "created_at": "2026-06-10T00:00:00Z",
            "summary": summary,
            "used_artifacts": ["definition.graph"],
            "used_sources": [],
            "claims": ["This is review context, not accepted knowledge."],
            "proposed_artifacts": [
                {
                    "path": proposed_path,
                    "summary": "Draft-only hosted worker proposal.",
                }
            ],
            "assumptions": ["Hosted worker output is review-only."],
            "uncertainty": ["No human review was performed."],
            "verification_requests": ["Run validate and gate before review."],
            "failed_attempts": [],
            "counterexamples": [],
            "failures_or_counterexamples": ["No external verifier was run."],
            "dependency_questions": [],
            "risk_flags": ["needs_human_review"],
            "next_steps": ["Request explicit human review."],
            "confidence": "low",
        }
    )


def test_fake_hosted_worker_produces_valid_worker_bundle(tmp_path: Path) -> None:
    service = HostedWorkerService(RepoContext(tmp_path))

    result = service.run(_request())

    assert isinstance(result, HostedWorkerOutput)
    assert result.status is HostedWorkerStatus.COMPLETED
    assert result.role is RoleName.REASONER
    assert result.accepted_write_performed is False
    assert result.provider_run is not None
    assert result.provider_run.private_context_sent is False
    assert result.bundle is not None
    assert isinstance(result.bundle, WorkerBundleV2)
    assert result.bundle.worker_role.value == "reasoner"
    assert result.bundle.assumptions == ["Hosted worker output is review-only."]
    assert result.bundle.uncertainty == [
        "No human review or semantic alignment review was run."
    ]
    assert result.bundle.proposed_artifacts[0].path.startswith("kb/draft/")
    assert result.typed_result is None
    assert result.provider_log_path == ".cosheaf/providers/run.provider.0001.json"


def test_fake_hosted_worker_can_return_typed_subresult(tmp_path: Path) -> None:
    service = HostedWorkerService(RepoContext(tmp_path))

    result = service.run(_request(RoleName.EXPLORER))

    assert result.status is HostedWorkerStatus.COMPLETED
    assert result.role is RoleName.EXPLORER
    assert result.accepted_write_performed is False
    assert result.bundle is None
    assert result.typed_result is not None
    assert result.typed_result.role is RoleName.EXPLORER
    assert result.typed_result.selected_artifacts == ["definition.graph"]
    assert result.provider_log_path == ".cosheaf/providers/run.provider.0001.json"


def test_fake_verifier_keeps_skipped_and_review_boundaries(tmp_path: Path) -> None:
    service = HostedWorkerService(RepoContext(tmp_path))

    result = service.run(_request(RoleName.VERIFIER))

    assert result.status is HostedWorkerStatus.COMPLETED
    assert result.bundle is not None
    assert result.bundle.worker_role.value == "verifier"
    assert "No external verifier was run." in result.bundle.failures_or_counterexamples
    assert result.accepted_write_performed is False


def test_hosted_worker_rejects_invalid_provider_output(tmp_path: Path) -> None:
    service = HostedWorkerService(RepoContext(tmp_path))

    result = service.run(
        _request(),
        config=ProviderConfig(
            provider=ProviderName.OPENAI,
            mode=ProviderMode.OPENAI_COMPATIBLE,
            model="gpt-test",
            enabled=True,
            api_key_env=None,
        ),
        provider=OpenAICompatibleProvider(transport=StaticTransport("not json")),
    )

    assert isinstance(result, HostedWorkerOutput)
    assert result.status is HostedWorkerStatus.REJECTED
    assert result.bundle is None
    assert result.error is not None
    assert result.error.code == "provider_output_validation_failed"
    assert result.accepted_write_performed is False


def test_hosted_worker_rejects_unsafe_verifier_bundle(tmp_path: Path) -> None:
    service = HostedWorkerService(RepoContext(tmp_path))
    unsafe = _bundle_json(
        role="verifier",
        summary="Verifier says review.state human_reviewed and accepted.",
    )

    result = service.run(
        _request(RoleName.VERIFIER),
        config=ProviderConfig(
            provider=ProviderName.OPENAI,
            mode=ProviderMode.OPENAI_COMPATIBLE,
            model="gpt-test",
            enabled=True,
            api_key_env=None,
        ),
        provider=OpenAICompatibleProvider(transport=StaticTransport(unsafe)),
    )

    assert result.status is HostedWorkerStatus.REJECTED
    assert result.error is not None
    assert result.error.code == "hosted_worker_policy_violation"
    assert "human_reviewed" in result.error.message


def test_hosted_worker_rejects_reasoner_theorem_claim(tmp_path: Path) -> None:
    service = HostedWorkerService(RepoContext(tmp_path))
    unsafe = _bundle_json(
        role="reasoner",
        summary="This conjecture is now a theorem.",
    )

    result = service.run(
        _request(RoleName.REASONER),
        config=ProviderConfig(
            provider=ProviderName.OPENAI,
            mode=ProviderMode.OPENAI_COMPATIBLE,
            model="gpt-test",
            enabled=True,
            api_key_env=None,
        ),
        provider=OpenAICompatibleProvider(transport=StaticTransport(unsafe)),
    )

    assert result.status is HostedWorkerStatus.REJECTED
    assert result.error is not None
    assert result.error.code == "hosted_worker_policy_violation"
    assert "theorem" in result.error.message


def test_hosted_worker_rejects_formalizer_alignment_claim(tmp_path: Path) -> None:
    service = HostedWorkerService(RepoContext(tmp_path))
    unsafe = _bundle_json(
        role="formalizer",
        summary="Lean checked semantic alignment with the informal statement.",
    )

    result = service.run(
        _request(RoleName.FORMALIZER),
        config=ProviderConfig(
            provider=ProviderName.OPENAI,
            mode=ProviderMode.OPENAI_COMPATIBLE,
            model="gpt-test",
            enabled=True,
            api_key_env=None,
        ),
        provider=OpenAICompatibleProvider(transport=StaticTransport(unsafe)),
    )

    assert result.status is HostedWorkerStatus.REJECTED
    assert result.error is not None
    assert result.error.code == "hosted_worker_policy_violation"
    assert "semantic alignment" in result.error.message
