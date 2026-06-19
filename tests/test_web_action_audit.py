from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from cosheaf.storage.repo import RepoContext
from cosheaf.web_actions import (
    WEB_ACTION_AUDIT_PATH,
    WebActionAuditEntry,
    WebActionError,
    WebActionKind,
    WebActionMode,
    append_web_action_audit,
)


def test_web_action_audit_logger_appends_redacted_entries(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    secret = "secret-token-value"
    entry = WebActionAuditEntry(
        timestamp=datetime(2026, 6, 19, tzinfo=UTC),
        actor="local.web",
        action=WebActionKind.FORGE_PR_CREATE,
        mode=WebActionMode.LOCAL,
        repo_root=str(tmp_path),
        preview_only=False,
        confirmed=True,
        performed=False,
        planned_files=[],
        authority_warnings=["Skipped is not pass."],
        error_code="forge_github_failed",
        errors=[
            WebActionError(
                code="forge_github_failed",
                message=f"gh failed with token {secret}",
                remediation="Check backend credentials.",
                blocking=True,
                details={"token": secret, "safe": "kept"},
            )
        ],
    )

    first_path = append_web_action_audit(context, entry)
    second_path = append_web_action_audit(context, entry)

    assert first_path == WEB_ACTION_AUDIT_PATH
    assert second_path == WEB_ACTION_AUDIT_PATH
    audit_path = tmp_path / WEB_ACTION_AUDIT_PATH
    audit_text = audit_path.read_text(encoding="utf-8")
    assert secret not in audit_text
    assert "[REDACTED]" in audit_text

    lines = [json.loads(line) for line in audit_text.splitlines()]
    assert len(lines) == 2
    assert lines[0]["action"] == "forge.pr_create"
    assert lines[0]["errors"][0]["details"]["token"] == "[REDACTED]"
    assert lines[0]["errors"][0]["details"]["safe"] == "kept"
