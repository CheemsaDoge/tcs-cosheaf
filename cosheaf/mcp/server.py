"""Minimal read-only MCP JSON-RPC surface for TCS-Cosheaf.

This module intentionally avoids an MCP SDK dependency for the first stdio
surface. It implements the protocol-level request shapes needed by tests and
external agents while delegating repository behavior to the shared service
layer.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, TextIO

from cosheaf.agent.context_pack import ContextPackError
from cosheaf.agent.orchestrator_planner import OrchestratorPlannerError
from cosheaf.gates.gatekeeper import GatekeeperRunResult, ValidationReport
from cosheaf.memory import ArtifactCard, MemoryCardError, MemoryRootScope
from cosheaf.memory import MemorySearchError as MemorySearchServiceError
from cosheaf.services import (
    ContextPackService,
    GateService,
    MemorySearchService,
    OrchestratorPlanService,
    ValidationService,
    WorkspaceInfoResult,
    WorkspaceService,
)
from cosheaf.storage.loader import IssueRecord, LoadedRecord, LoadError, load_artifacts
from cosheaf.storage.repo import RepoContext

READ_ONLY_TOOL_NAMES = (
    "workspace_info",
    "validate",
    "gate_run",
    "memory_search",
    "context_build",
    "context_show",
    "orchestrator_plan",
)


class McpServerError(ValueError):
    """Expected JSON-RPC error for the read-only MCP surface."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        remediation: str,
        blocking: bool = True,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.remediation = remediation
        self.blocking = blocking
        self.details = dict(details or {})

    def to_error_data(self) -> dict[str, Any]:
        """Return deterministic machine-readable error details."""
        data: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "remediation": self.remediation,
            "blocking": self.blocking,
        }
        if self.details:
            data["details"] = self.details
        return data


class ReadOnlyMcpServer:
    """Protocol-level read-only MCP handler over Cosheaf services."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context
        self._tool_handlers: dict[
            str,
            Callable[[Mapping[str, Any]], dict[str, Any]],
        ] = {
            "workspace_info": self._tool_workspace_info,
            "validate": self._tool_validate,
            "gate_run": self._tool_gate_run,
            "memory_search": self._tool_memory_search,
            "context_build": self._tool_context_build,
            "context_show": self._tool_context_show,
            "orchestrator_plan": self._tool_orchestrator_plan,
        }

    def handle(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Handle one JSON-RPC request mapping and return one response mapping."""
        request_id = request.get("id")
        try:
            method = _required_string(request, "method")
            params = _optional_mapping(request.get("params", {}), field_name="params")
            result: dict[str, Any]
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "tcs-cosheaf-readonly",
                        "version": "0.2.0",
                    },
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                    },
                }
            elif method == "tools/list":
                result = {"tools": tool_definitions()}
            elif method == "resources/list":
                result = {"resources": resource_definitions()}
            elif method == "tools/call":
                result = self._handle_tool_call(params)
            elif method == "resources/read":
                result = self._handle_resource_read(params)
            else:
                raise McpServerError(
                    "method_not_found",
                    f"unsupported MCP method: {method}",
                    remediation=(
                        "Use tools/list, tools/call, resources/list, "
                        "or resources/read."
                    ),
                )
            return _success_response(request_id, result)
        except McpServerError as exc:
            return _error_response(request_id, exc)
        except Exception as exc:
            error = McpServerError(
                "internal_error",
                "read-only MCP request failed",
                remediation="Inspect the repository state and rerun the request.",
                details={"exception": exc.__class__.__name__},
            )
            return _error_response(request_id, error)

    def _handle_tool_call(self, params: Mapping[str, Any]) -> dict[str, Any]:
        name = _required_string(params, "name")
        arguments = _optional_mapping(
            params.get("arguments", {}),
            field_name="arguments",
        )
        handler = self._tool_handlers.get(name)
        if handler is None:
            raise McpServerError(
                "tool_not_found",
                f"tool is not exposed by the read-only MCP server: {name}",
                remediation=(
                    "Call tools/list and use one of the whitelisted tool names."
                ),
            )
        try:
            payload = handler(arguments)
            return _tool_result(payload)
        except McpServerError as exc:
            return _tool_error_result(exc)

    def _handle_resource_read(self, params: Mapping[str, Any]) -> dict[str, Any]:
        uri = _required_string(params, "uri")
        if uri == "cosheaf://workspace":
            return _resource_result(
                uri,
                _workspace_info_payload(WorkspaceService(self.context).info()),
            )
        if uri.startswith("cosheaf://issues/"):
            issue_id = uri.removeprefix("cosheaf://issues/")
            if "/" in issue_id or not issue_id:
                raise _resource_not_found(uri)
            return _resource_result(uri, self._issue_payload(issue_id))
        if uri.startswith("cosheaf://artifacts/") and uri.endswith("/card"):
            artifact_id = uri.removeprefix("cosheaf://artifacts/").removesuffix("/card")
            if "/" in artifact_id or not artifact_id:
                raise _resource_not_found(uri)
            return _resource_result(
                uri,
                self._public_artifact_card_payload(artifact_id),
            )
        if uri.startswith("cosheaf://context/"):
            issue_id = uri.removeprefix("cosheaf://context/")
            if "/" in issue_id or not issue_id:
                raise _resource_not_found(uri)
            rendered = ContextPackService(self.context).show(issue_id, public_only=True)
            return _text_resource_result(uri, rendered, mime_type="text/markdown")
        if uri == "cosheaf://gate/latest":
            return _resource_result(uri, self._latest_gate_payload())
        raise _resource_not_found(uri)

    def _tool_workspace_info(self, _arguments: Mapping[str, Any]) -> dict[str, Any]:
        return _workspace_info_payload(WorkspaceService(self.context).info())

    def _tool_validate(self, _arguments: Mapping[str, Any]) -> dict[str, Any]:
        report = ValidationService(self.context).validate_repository()
        return _validation_payload(report)

    def _tool_gate_run(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        pr_checklist = arguments.get("pr_checklist")
        if pr_checklist is not None and not isinstance(pr_checklist, str):
            raise McpServerError(
                "invalid_arguments",
                "pr_checklist must be a string path when provided",
                remediation="Pass a repository-local PR checklist path or omit it.",
            )
        result = GateService(self.context).run(pr_checklist_path=pr_checklist)
        return _gate_payload(self.context, result)

    def _tool_memory_search(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        query = _required_string(arguments, "query")
        issue_id = _optional_string(arguments.get("issue_id"), field_name="issue_id")
        max_cards = _optional_positive_int(
            arguments.get("max_cards"),
            field_name="max_cards",
            default=20,
        )
        try:
            result = MemorySearchService(self.context).search(
                query,
                max_cards=max_cards,
            )
        except MemorySearchServiceError as exc:
            raise McpServerError(
                "memory_search_failed",
                str(exc),
                remediation="Check the query, issue ID, and repository records.",
            ) from exc
        payload = result.to_dict()
        payload["public_only"] = True
        if issue_id is not None:
            payload["requested_issue_id"] = issue_id
            payload["issue_conditioning"] = "disabled_for_read_only_public_mcp"
        return payload

    def _tool_context_build(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        issue_id = _required_string(arguments, "issue_id")
        max_cards = _optional_positive_int(
            arguments.get("max_cards"),
            field_name="max_cards",
            default=20,
        )
        max_full_artifacts = _optional_non_negative_int(
            arguments.get("max_full_artifacts"),
            field_name="max_full_artifacts",
            default=0,
        )
        try:
            result = ContextPackService(self.context).build(
                issue_id,
                max_cards=max_cards,
                max_full_artifacts=max_full_artifacts,
                public_only=True,
            )
        except ContextPackError as exc:
            raise McpServerError(
                "context_build_failed",
                str(exc),
                remediation="Check the issue ID and repository records.",
            ) from exc
        return {
            "issue_id": result.issue_id,
            "task_dir": _repo_relative_or_string(self.context, result.task_dir),
            "files": [
                _repo_relative_or_string(self.context, path)
                for path in result.files
            ],
            "public_only": True,
            "accepted_writes": False,
        }

    def _tool_context_show(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        issue_id = _required_string(arguments, "issue_id")
        try:
            rendered = ContextPackService(self.context).show(issue_id, public_only=True)
        except ContextPackError as exc:
            raise McpServerError(
                "context_show_failed",
                str(exc),
                remediation="Check the issue ID and repository records.",
            ) from exc
        return {
            "issue_id": issue_id,
            "public_only": True,
            "content": rendered,
        }

    def _tool_orchestrator_plan(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        issue_id = _required_string(arguments, "issue_id")
        try:
            plan = OrchestratorPlanService(self.context).plan_for_issue(issue_id)
        except OrchestratorPlannerError as exc:
            raise McpServerError(
                "orchestrator_plan_failed",
                str(exc),
                remediation="Check the issue ID and repository records.",
            ) from exc
        return {
            **plan.to_dict(),
            "execution_performed": False,
            "hosted_provider_called": False,
            "accepted_writes": False,
        }

    def _issue_payload(self, issue_id: str) -> dict[str, Any]:
        issue = _find_issue(self.context, issue_id)
        public_card_ids = {
            card.id
            for card in MemorySearchService(self.context).cards(issue_id=issue_id)
            if card.root_scope is not MemoryRootScope.PRIVATE
        }
        related_artifacts = [
            artifact_id
            for artifact_id in issue.related_artifacts
            if artifact_id in public_card_ids
        ]
        return {
            "id": issue.id,
            "type": issue.type,
            "title": issue.title,
            "status": issue.status,
            "severity": issue.severity,
            "description": issue.description,
            "related_artifacts": related_artifacts,
            "tags": issue.tags,
            "public_only": True,
        }

    def _public_artifact_card_payload(self, artifact_id: str) -> dict[str, Any]:
        try:
            cards = MemorySearchService(self.context).cards()
        except MemoryCardError as exc:
            raise McpServerError(
                "artifact_card_failed",
                str(exc),
                remediation="Fix repository records and retry.",
            ) from exc
        matches = [card for card in cards if card.id == artifact_id]
        if matches:
            return _artifact_card_payload(matches[0])
        if _artifact_exists_with_private_scope(self.context, artifact_id):
            raise McpServerError(
                "private_resource_denied",
                "private artifact card is not available through read-only "
                "public MCP resources",
                remediation=(
                    "Use an explicit private research policy mode in a later "
                    "controlled MCP surface; M.2 exposes public resources only."
                ),
            )
        raise McpServerError(
            "resource_not_found",
            "artifact card resource was not found",
            remediation="Check the artifact ID and visible public KB scope.",
        )

    def _latest_gate_payload(self) -> dict[str, Any]:
        reports_dir = self.context.resolve(Path(".cosheaf") / "reports")
        candidates = sorted(reports_dir.glob("*-gate-report.json"))
        if not candidates:
            raise McpServerError(
                "gate_report_not_found",
                "no gate report exists under .cosheaf/reports",
                remediation="Run the gate_run tool or cosheaf gate run first.",
                blocking=False,
            )
        latest = candidates[-1]
        try:
            payload = json.loads(latest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise McpServerError(
                "gate_report_unreadable",
                "latest gate report could not be read",
                remediation="Rerun gate_run to regenerate the report.",
                details={"path": _repo_relative_or_string(self.context, latest)},
            ) from exc
        return {
            "path": _repo_relative_or_string(self.context, latest),
            "report": payload,
        }


def tool_definitions() -> list[dict[str, Any]]:
    """Return deterministic read-only MCP tool definitions."""
    descriptions = {
        "workspace_info": "Return configured workspace and KB root metadata.",
        "validate": "Run repository validation and return structured failures.",
        "gate_run": "Run gatekeeper and return report metadata.",
        "memory_search": (
            "Search public artifact cards with deterministic local scoring."
        ),
        "context_build": "Build a public-only issue context pack.",
        "context_show": "Build and return public-only issue context text.",
        "orchestrator_plan": "Create a deterministic plan without executing workers.",
    }
    schemas: dict[str, dict[str, Any]] = {
        "workspace_info": {"type": "object", "additionalProperties": False},
        "validate": {"type": "object", "additionalProperties": False},
        "gate_run": {
            "type": "object",
            "properties": {"pr_checklist": {"type": "string"}},
            "additionalProperties": False,
        },
        "memory_search": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "issue_id": {"type": "string"},
                "max_cards": {"type": "integer", "minimum": 1},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "context_build": {
            "type": "object",
            "properties": {
                "issue_id": {"type": "string"},
                "max_cards": {"type": "integer", "minimum": 1},
                "max_full_artifacts": {"type": "integer", "minimum": 0},
            },
            "required": ["issue_id"],
            "additionalProperties": False,
        },
        "context_show": {
            "type": "object",
            "properties": {"issue_id": {"type": "string"}},
            "required": ["issue_id"],
            "additionalProperties": False,
        },
        "orchestrator_plan": {
            "type": "object",
            "properties": {"issue_id": {"type": "string"}},
            "required": ["issue_id"],
            "additionalProperties": False,
        },
    }
    return [
        {
            "name": name,
            "description": descriptions[name],
            "inputSchema": schemas[name],
        }
        for name in READ_ONLY_TOOL_NAMES
    ]


def resource_definitions() -> list[dict[str, str]]:
    """Return deterministic read-only MCP resource examples."""
    return [
        {
            "uri": "cosheaf://workspace",
            "name": "workspace",
            "mimeType": "application/json",
        },
        {
            "uri": "cosheaf://issues/{issue_id}",
            "name": "issue",
            "mimeType": "application/json",
        },
        {
            "uri": "cosheaf://artifacts/{artifact_id}/card",
            "name": "artifact card",
            "mimeType": "application/json",
        },
        {
            "uri": "cosheaf://context/{issue_id}",
            "name": "public context pack",
            "mimeType": "text/markdown",
        },
        {
            "uri": "cosheaf://gate/latest",
            "name": "latest gate report",
            "mimeType": "application/json",
        },
    ]


def serve_stdio(
    context: RepoContext,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> None:
    """Serve line-delimited JSON-RPC requests over stdio streams."""
    server = ReadOnlyMcpServer(context)
    input_handle = input_stream or sys.stdin
    output_handle = output_stream or sys.stdout
    for line in input_handle:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            request = json.loads(stripped)
        except json.JSONDecodeError as exc:
            response = _error_response(
                None,
                McpServerError(
                    "invalid_json",
                    "request line is not valid JSON",
                    remediation="Send one JSON-RPC request object per line.",
                    details={"error": str(exc)},
                ),
            )
        else:
            if not isinstance(request, dict):
                response = _error_response(
                    None,
                    McpServerError(
                        "invalid_request",
                        "JSON-RPC request must be an object",
                        remediation="Send one JSON-RPC request object per line.",
                    ),
                )
            else:
                response = server.handle(request)
        output_handle.write(json.dumps(response, ensure_ascii=True) + "\n")
        output_handle.flush()


def _success_response(request_id: Any, result: Mapping[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": dict(result)}


def _error_response(request_id: Any, error: McpServerError) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32000,
            "message": error.message,
            "data": error.to_error_data(),
        },
    }


def _tool_result(payload: Mapping[str, Any]) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=True, indent=2)
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": dict(payload),
        "isError": False,
    }


def _tool_error_result(error: McpServerError) -> dict[str, Any]:
    payload = error.to_error_data()
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=True, indent=2),
            }
        ],
        "structuredContent": payload,
        "isError": True,
    }


def _resource_result(uri: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _text_resource_result(
        uri,
        json.dumps(payload, ensure_ascii=True, indent=2),
        mime_type="application/json",
    )


def _text_resource_result(
    uri: str,
    text: str,
    *,
    mime_type: str,
) -> dict[str, Any]:
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": mime_type,
                "text": text,
            }
        ]
    }


def _workspace_info_payload(info: WorkspaceInfoResult) -> dict[str, Any]:
    return {
        "name": info.name,
        "repo_root": str(info.repo_root),
        "mode": info.mode,
        "kb_roots": [
            {
                "name": root.name,
                "path": root.path,
                "readonly": root.readonly,
                "priority": root.priority,
            }
            for root in info.kb_roots
        ],
    }


def _validation_payload(report: ValidationReport) -> dict[str, Any]:
    return {
        "ok": report.ok,
        "checked_count": report.checked_count,
        "failures": [
            {
                "gate": failure.gate,
                "source_path": failure.source_path,
                "artifact_id": failure.artifact_id,
                "message": failure.message,
            }
            for failure in report.failures
        ],
    }


def _gate_payload(context: RepoContext, result: GatekeeperRunResult) -> dict[str, Any]:
    return {
        "verdict": result.report.verdict,
        "json_path": _repo_relative_or_string(context, result.json_path),
        "markdown_path": _repo_relative_or_string(context, result.markdown_path),
        "blocking_issues": [
            issue.to_dict() for issue in result.report.blocking_issues
        ],
        "nonblocking_issues": [
            issue.to_dict() for issue in result.report.nonblocking_issues
        ],
        "summary": result.report.summary,
    }


def _artifact_card_payload(card: ArtifactCard) -> dict[str, Any]:
    payload = card.to_dict()
    payload["artifact_id"] = card.id
    return payload


def _find_issue(context: RepoContext, issue_id: str) -> IssueRecord:
    try:
        records = tuple(load_artifacts(context))
    except LoadError as exc:
        raise McpServerError(
            "issue_load_failed",
            str(exc),
            remediation="Fix repository records and retry.",
        ) from exc
    matches = [
        record.record
        for record in records
        if isinstance(record.record, IssueRecord) and record.record.id == issue_id
    ]
    if not matches:
        raise McpServerError(
            "resource_not_found",
            "issue resource was not found",
            remediation="Check the issue ID.",
        )
    return sorted(matches, key=lambda issue: issue.id)[0]


def _artifact_exists_with_private_scope(context: RepoContext, artifact_id: str) -> bool:
    try:
        records = tuple(load_artifacts(context))
    except LoadError as exc:
        raise McpServerError(
            "artifact_load_failed",
            str(exc),
            remediation="Fix repository records and retry.",
        ) from exc
    return any(
        record.id == artifact_id
        and _loaded_record_scope(record) is MemoryRootScope.PRIVATE
        for record in records
    )


def _loaded_record_scope(record: LoadedRecord) -> MemoryRootScope:
    root_name = (record.kb_root_name or "").lower()
    if root_name == "public":
        return MemoryRootScope.PUBLIC
    if root_name == "private":
        return MemoryRootScope.PRIVATE
    if root_name == "framework":
        return MemoryRootScope.FRAMEWORK
    return MemoryRootScope.WORKSPACE


def _resource_not_found(uri: str) -> McpServerError:
    return McpServerError(
        "resource_not_found",
        "MCP resource was not found",
        remediation="Use resources/list and a supported cosheaf:// URI.",
        details={"uri": uri},
    )


def _repo_relative_or_string(context: RepoContext, path: Path) -> str:
    try:
        return path.resolve().relative_to(context.repo_root).as_posix()
    except ValueError:
        return str(path)


def _required_string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise McpServerError(
            "invalid_arguments",
            f"{key} must be a non-empty string",
            remediation="Pass the required string argument.",
        )
    return value.strip()


def _optional_string(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise McpServerError(
            "invalid_arguments",
            f"{field_name} must be a non-empty string when provided",
            remediation="Pass a string value or omit the argument.",
        )
    return value.strip()


def _optional_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise McpServerError(
            "invalid_arguments",
            f"{field_name} must be an object",
            remediation="Pass a JSON object for this field.",
        )
    return value


def _optional_positive_int(value: Any, *, field_name: str, default: int) -> int:
    if value is None:
        return default
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise McpServerError(
            "invalid_arguments",
            f"{field_name} must be a positive integer",
            remediation="Pass a positive integer value.",
        )
    return value


def _optional_non_negative_int(value: Any, *, field_name: str, default: int) -> int:
    if value is None:
        return default
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise McpServerError(
            "invalid_arguments",
            f"{field_name} must be a non-negative integer",
            remediation="Pass a non-negative integer value.",
        )
    return value
