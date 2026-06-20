from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.app import open_app
from cosheaf.server import ReadOnlySiteApi
from cosheaf.server.auth import (
    HostedIdentity,
    HostedRole,
    hosted_action_allowed,
    hosted_required_role,
)
from cosheaf.web_actions import WebActionKind, WebActionMode


class _StaticHostedAuthProvider:
    def __init__(self, identity: HostedIdentity | None) -> None:
        self.identity = identity

    def current_identity(self) -> HostedIdentity | None:
        return self.identity


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _audit_entries(repo_root: Path) -> list[dict[str, Any]]:
    audit_path = repo_root / ".cosheaf" / "audit" / "web-actions.jsonl"
    return [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _artifact_data(artifact_id: str) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "Hosted auth fixture claim",
        "domain": ["testing"],
        "status": "locally_tested",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["hosted-auth"],
        "statement": "Triangle graph $K_3$ should be reviewed before promotion.",
        "evidence": [],
        "sources": [],
        "review": {"state": "human_reviewed", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _promotion_payload() -> str:
    return json.dumps(
        {
            "target_state": "accepted",
            "typed_confirmation": "PROMOTE TO ACCEPTED",
            "promotion_justification": "Reviewed by hand before promotion.",
            "confirm": True,
        }
    )


def test_hosted_roles_map_to_minimal_action_permissions() -> None:
    contributor = HostedIdentity(
        subject="alice",
        roles=frozenset({HostedRole.CONTRIBUTOR}),
    )
    reviewer = HostedIdentity(
        subject="bob",
        roles=frozenset({HostedRole.REVIEWER}),
    )
    admin = HostedIdentity(subject="carol", roles=frozenset({HostedRole.ADMIN}))

    assert hosted_required_role(WebActionKind.ARTIFACT_CREATE) is HostedRole.CONTRIBUTOR
    assert hosted_required_role(WebActionKind.REVIEW_DECISION_CREATE) is (
        HostedRole.REVIEWER
    )
    assert hosted_required_role(WebActionKind.PROMOTION_CONFIRM) is (
        HostedRole.MAINTAINER
    )
    assert hosted_action_allowed(contributor, WebActionKind.ARTIFACT_CREATE) is True
    assert hosted_action_allowed(contributor, WebActionKind.REVIEW_DECISION_CREATE) is (
        False
    )
    assert hosted_action_allowed(reviewer, WebActionKind.PROMOTION_CONFIRM) is False
    assert hosted_action_allowed(admin, WebActionKind.PROMOTION_CONFIRM) is True


def test_hosted_promotion_requires_authenticated_identity(tmp_path: Path) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.hosted-no-auth.yaml",
        _artifact_data("claim.fixture.hosted-no-auth"),
    )
    api = ReadOnlySiteApi(
        open_app(tmp_path),
        web_action_mode=WebActionMode.HOSTED,
    )

    response = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.hosted-no-auth/promotion/confirm",
        _promotion_payload(),
    )

    assert response.status == 403
    assert response.payload["code"] == "hosted_auth_required"
    assert source.is_file()
    assert not (
        tmp_path / "kb/accepted/claims/claim.fixture.hosted-no-auth.yaml"
    ).exists()
    entries = _audit_entries(tmp_path)
    assert entries[-1]["action"] == "promotion.confirm"
    assert entries[-1]["mode"] == "hosted"
    assert entries[-1]["result_status"] == "hosted_auth_required"
    assert entries[-1]["repo_writes_performed"] is False


def test_hosted_promotion_refuses_reviewer_role(tmp_path: Path) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.hosted-reviewer.yaml",
        _artifact_data("claim.fixture.hosted-reviewer"),
    )
    identity = HostedIdentity(
        subject="reviewer@example.com",
        roles=frozenset({HostedRole.REVIEWER}),
    )
    api = ReadOnlySiteApi(
        open_app(tmp_path),
        web_action_mode=WebActionMode.HOSTED,
        hosted_auth_provider=_StaticHostedAuthProvider(identity),
    )

    response = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.hosted-reviewer/promotion/confirm",
        _promotion_payload(),
    )

    assert response.status == 403
    assert response.payload["code"] == "hosted_action_denied"
    assert source.is_file()
    entries = _audit_entries(tmp_path)
    assert entries[-1]["actor"] == "reviewer@example.com"
    assert entries[-1]["result_status"] == "hosted_action_denied"
    assert entries[-1]["repo_writes_performed"] is False


def test_hosted_maintainer_can_confirm_promotion_without_local_actor(
    tmp_path: Path,
) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.hosted-maintainer.yaml",
        _artifact_data("claim.fixture.hosted-maintainer"),
    )
    identity = HostedIdentity(
        subject="maintainer@example.com",
        roles=frozenset({HostedRole.MAINTAINER}),
    )
    api = ReadOnlySiteApi(
        open_app(tmp_path),
        web_action_mode=WebActionMode.HOSTED,
        hosted_auth_provider=_StaticHostedAuthProvider(identity),
    )

    response = api.handle(
        "POST",
        "/api/artifacts/claim.fixture.hosted-maintainer/promotion/confirm",
        _promotion_payload(),
    )

    assert response.status == 200, response.payload
    assert response.payload["promotion_performed"] is True
    target = tmp_path / "kb/accepted/claims/claim.fixture.hosted-maintainer.yaml"
    assert not source.exists()
    assert target.is_file()
    assert _read_yaml(target)["status"] == "accepted"
    entries = _audit_entries(tmp_path)
    assert entries[-1]["actor"] == "maintainer@example.com"
    assert entries[-1]["mode"] == "hosted"
    assert entries[-1]["repo_writes_performed"] is True
