"""Built-in local action implementations for the deterministic action registry.

Each action is a function that receives (request, policy, repo_root) and returns
a LocalActionResult. Actions must not write accepted KB, call hosted providers,
require network, or execute arbitrary shell by default.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from cosheaf.actions.registry import (
    ActionFunc,
    LocalActionError,
    LocalActionInputRefKind,
    LocalActionPolicy,
    LocalActionRegistry,
    LocalActionResult,
    LocalActionRunRequest,
    LocalActionSpec,
    LocalActionStatus,
)


def _cosheaf_cli(argv: list[str], repo_root: Path) -> LocalActionResult:
    """Run cosheaf CLI via subprocess in the repo root and return structured result."""
    started_at = datetime.now(UTC)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "cosheaf.cli"] + argv,
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )
        finished_at = datetime.now(UTC)
        status = (
            LocalActionStatus.SUCCESS
            if proc.returncode == 0
            else LocalActionStatus.FAILED
        )
        error = None
        if status == LocalActionStatus.FAILED and proc.stderr.strip():
            error = LocalActionError(
                error_code="NONZERO_EXIT",
                message=proc.stderr.strip()[:500],
            )
        return LocalActionResult(
            action_id="",
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=(finished_at - started_at).total_seconds(),
            stdout_snippet=proc.stdout.strip()[-500:] if proc.stdout else "",
            stderr_snippet=proc.stderr.strip()[-500:] if proc.stderr else "",
            error=error,
            scanner_status="not_applicable",
        )
    except subprocess.TimeoutExpired:
        finished_at = datetime.now(UTC)
        return LocalActionResult(
            action_id="",
            status=LocalActionStatus.ERROR,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=(finished_at - started_at).total_seconds(),
            error=LocalActionError(error_code="TIMEOUT", message="Action timed out"),
            scanner_status="not_applicable",
        )
    except Exception as exc:
        finished_at = datetime.now(UTC)
        return LocalActionResult(
            action_id="",
            status=LocalActionStatus.ERROR,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=(finished_at - started_at).total_seconds(),
            error=LocalActionError(error_code="EXECUTION_EXCEPTION", message=str(exc)),
            scanner_status="not_applicable",
        )


def _action_workspace_info(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    result = _cosheaf_cli(["workspace", "info"], repo_root)
    return result.model_copy(update={"action_id": "workspace.info"})


def _action_validate(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    result = _cosheaf_cli(["validate"], repo_root)
    return result.model_copy(update={"action_id": "validate.run"})


def _action_gate(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    result = _cosheaf_cli(["gate", "run"], repo_root)
    return result.model_copy(update={"action_id": "gate.run"})


def _action_index_rebuild(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    result = _cosheaf_cli(["index", "rebuild"], repo_root)
    return result.model_copy(update={"action_id": "index.rebuild"})


def _action_memory_search(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    query = request.input_refs.get("query", "")
    result = _cosheaf_cli(["memory", "search", query, "--json"], repo_root)
    return result.model_copy(update={"action_id": "memory.search"})


def _action_context_build(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    issue_id = request.input_refs.get("issue_id", "")
    result = _cosheaf_cli(["context", "build", issue_id], repo_root)
    return result.model_copy(update={"action_id": "context.build"})


def _action_strategy_next(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    issue_id = request.input_refs.get("issue_id", "")
    result = _cosheaf_cli(["strategy", "next", issue_id, "--json"], repo_root)
    return result.model_copy(update={"action_id": "strategy.next"})


def _action_research_loop_scan(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    loop_id = request.input_refs.get("loop_id", "")
    result = _cosheaf_cli(["research-loop", "scan", loop_id, "--json"], repo_root)
    return result.model_copy(update={"action_id": "research_loop.scan"})


def _action_operator_session_scan(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    session_id = request.input_refs.get("session_id", "")
    result = _cosheaf_cli(
        ["operator", "session", "scan", session_id, "--json"], repo_root
    )
    return result.model_copy(update={"action_id": "operator_session.scan"})


def _action_operator_handoff_preview(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    handoff_id = request.input_refs.get("handoff_id", "")
    result = _cosheaf_cli(
        [
            "operator",
            "handoff",
            "export",
            "--handoff",
            handoff_id,
            "--dry-run",
            "--json",
        ],
        repo_root,
    )
    return result.model_copy(update={"action_id": "operator_handoff.preview"})


def _action_research_run_summary(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    run_id = request.input_refs.get("run_id", "")
    result = _cosheaf_cli(["research-run", "show", run_id, "--json"], repo_root)
    return result.model_copy(update={"action_id": "research_run.summary"})


def _action_checked_evidence_summary(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    artifact_id = request.input_refs.get("artifact_id", "")
    result = _cosheaf_cli(
        ["checked-evidence", "show", artifact_id, "--json"], repo_root
    )
    return result.model_copy(update={"action_id": "checked_evidence.summary"})


def _action_failure_memory_summary(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    issue_id = request.input_refs.get("issue_id", "")
    result = _cosheaf_cli(["failure-memory", "show", issue_id, "--json"], repo_root)
    return result.model_copy(update={"action_id": "failure_memory.summary"})


def _action_eval_research_loop(
    request: LocalActionRunRequest,
    policy: LocalActionPolicy,
    repo_root: Path,
) -> LocalActionResult:
    result = _cosheaf_cli(["eval", "research-loop", "--json"], repo_root)
    return result.model_copy(update={"action_id": "eval.research_loop"})


# Action spec definitions for the registry
_BUILTIN_SPECS: list[LocalActionSpec] = [
    LocalActionSpec(
        action_id="workspace.info",
        description="Inspect the configured workspace and KB roots",
        allowed_input_refs=[],
        max_timeout_seconds=30,
    ),
    LocalActionSpec(
        action_id="validate.run",
        description="Run artifact validation against loaded KB roots",
        allowed_input_refs=[],
        max_timeout_seconds=60,
    ),
    LocalActionSpec(
        action_id="gate.run",
        description="Run the gatekeeper check",
        allowed_input_refs=[],
        max_timeout_seconds=60,
    ),
    LocalActionSpec(
        action_id="index.rebuild",
        description="Rebuild the deterministic SQLite/manifest index",
        allowed_input_refs=[],
        max_timeout_seconds=120,
    ),
    LocalActionSpec(
        action_id="memory.search",
        description="Search the memory graph for related artifacts",
        allowed_input_refs=[LocalActionInputRefKind.ISSUE_ID],
        max_timeout_seconds=60,
    ),
    LocalActionSpec(
        action_id="context.build",
        description="Build a ranked context pack for an issue",
        allowed_input_refs=[LocalActionInputRefKind.ISSUE_ID],
        max_timeout_seconds=120,
    ),
    LocalActionSpec(
        action_id="strategy.next",
        description="Get the next strategy action for an issue",
        allowed_input_refs=[LocalActionInputRefKind.ISSUE_ID],
        max_timeout_seconds=60,
    ),
    LocalActionSpec(
        action_id="research_loop.scan",
        description="Scan a research loop for leaks and authority violations",
        allowed_input_refs=[LocalActionInputRefKind.LOOP_ID],
        max_timeout_seconds=60,
    ),
    LocalActionSpec(
        action_id="operator_session.scan",
        description="Scan an operator session for leaks and authority violations",
        allowed_input_refs=[LocalActionInputRefKind.SESSION_ID],
        max_timeout_seconds=60,
    ),
    LocalActionSpec(
        action_id="operator_handoff.preview",
        description="Preview an operator handoff export (dry run)",
        allowed_input_refs=[LocalActionInputRefKind.HANDOFF_ID],
        max_timeout_seconds=60,
    ),
    LocalActionSpec(
        action_id="research_run.summary",
        description="Show a research run summary",
        allowed_input_refs=[LocalActionInputRefKind.RUN_ID],
        max_timeout_seconds=30,
    ),
    LocalActionSpec(
        action_id="checked_evidence.summary",
        description="Show checked evidence summary for an artifact",
        allowed_input_refs=[LocalActionInputRefKind.ARTIFACT_ID],
        max_timeout_seconds=30,
    ),
    LocalActionSpec(
        action_id="failure_memory.summary",
        description="Show failure memory summary for an issue",
        allowed_input_refs=[LocalActionInputRefKind.ISSUE_ID],
        max_timeout_seconds=30,
    ),
    LocalActionSpec(
        action_id="eval.research_loop",
        description="Run the deterministic research-loop eval",
        allowed_input_refs=[],
        max_timeout_seconds=120,
    ),
]


_BUILTIN_FUNCS: dict[str, ActionFunc] = {
    "workspace.info": _action_workspace_info,
    "validate.run": _action_validate,
    "gate.run": _action_gate,
    "index.rebuild": _action_index_rebuild,
    "memory.search": _action_memory_search,
    "context.build": _action_context_build,
    "strategy.next": _action_strategy_next,
    "research_loop.scan": _action_research_loop_scan,
    "operator_session.scan": _action_operator_session_scan,
    "operator_handoff.preview": _action_operator_handoff_preview,
    "research_run.summary": _action_research_run_summary,
    "checked_evidence.summary": _action_checked_evidence_summary,
    "failure_memory.summary": _action_failure_memory_summary,
    "eval.research_loop": _action_eval_research_loop,
}


def build_default_registry() -> LocalActionRegistry:
    """Build a LocalActionRegistry with all built-in actions registered."""
    registry = LocalActionRegistry()
    for spec in _BUILTIN_SPECS:
        func = _BUILTIN_FUNCS.get(spec.action_id)
        if func is None:
            raise KeyError(
                f"No function registered for built-in action {spec.action_id!r}"
            )
        registry.register(spec, func)
    return registry
