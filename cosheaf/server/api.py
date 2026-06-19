"""Read-only local HTTP API for website preview."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal, cast
from urllib.parse import unquote, urlparse

from cosheaf.app import CosheafApp
from cosheaf.core.artifact import BaseArtifact
from cosheaf.core.ids import validate_artifact_id
from cosheaf.forge import (
    FORGE_AUTHORITY_WARNING,
    FORGE_PREVIEW_AUTHORITY_WARNING,
    ForgeActionError,
    ForgeActionResult,
    ForgeCredentialProvider,
)
from cosheaf.issues import ISSUE_AUTHORITY_NOTICE, LocalIssueError
from cosheaf.site import REQUIRED_SITE_EXPORT_FILES, SITE_EXPORT_AUTHORITY_NOTICE
from cosheaf.storage.loader import LoadedRecord, LoadError, load_artifacts
from cosheaf.web_actions import (
    WEB_ACTION_AUDIT_PATH,
    WebActionAuditEntry,
    WebActionError,
    WebActionKind,
    WebActionMode,
    append_web_action_audit,
)

READONLY_SERVER_HOST = "127.0.0.1"
READONLY_SERVER_PORT = 8765
READONLY_SERVER_SCHEMA_VERSION = 1
_EXPORT_ENDPOINTS = {
    "/api/workspace": "workspace.json",
    "/api/artifacts": "artifacts.json",
    "/api/issues": "issues.json",
    "/api/graph": "graph.json",
    "/api/gates": "gates.json",
}
_PREVIEW_ENDPOINTS = {
    "/api/forge/local-issues/preview",
    "/api/forge/issues/preview",
    "/api/forge/prs/preview",
    "/api/forge/review-packets/preview",
}
_CREATE_ENDPOINTS = {
    "/api/forge/issues/create",
    "/api/forge/prs/create",
}


@dataclass(frozen=True)
class ApiResponse:
    """JSON response returned by the read-only local API router."""

    status: int
    payload: dict[str, Any]

    def body(self) -> bytes:
        """Serialize this response body deterministically."""
        return (
            json.dumps(self.payload, ensure_ascii=True, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")


class ReadOnlySiteApi:
    """Route read-only website API requests through the app facade."""

    def __init__(
        self,
        app: CosheafApp,
        *,
        host: str = READONLY_SERVER_HOST,
        credential_provider: ForgeCredentialProvider | None = None,
    ) -> None:
        self.app = app
        self.host = host
        self.credential_provider = credential_provider

    def handle(
        self,
        method: str,
        raw_path: str,
        body: str | bytes = b"",
    ) -> ApiResponse:
        """Return a JSON response for one HTTP-like request."""
        normalized_method = method.upper()
        path = _normalize_path(raw_path)
        if normalized_method == "GET":
            return self._handle_get(path)
        if normalized_method == "POST":
            return self._handle_post(path, body)
        return _error(
            405,
            "method_not_allowed",
            "The local website API is read-only and only accepts GET or "
            "preview-only POST requests.",
        )

    def _handle_get(self, path: str) -> ApiResponse:
        if path in _PREVIEW_ENDPOINTS:
            return _error(
                405,
                "method_not_allowed",
                "Preview endpoints only accept POST.",
            )
        if path == "/api/health":
            return ApiResponse(200, self._health_payload())
        if path == "/api/workspace/live":
            return self._live_workspace_payload()
        if path == "/api/status":
            return self._live_status_payload()
        if path == "/api/issues/live":
            return self._live_issues_payload()
        if path.startswith("/api/issues/"):
            return self._live_issue_payload(path.removeprefix("/api/issues/"))
        if path == "/api/artifacts/live":
            return self._live_artifacts_payload()
        if path.startswith("/api/artifacts/"):
            return self._live_artifact_payload(path.removeprefix("/api/artifacts/"))
        if path.startswith("/api/context/") and path.endswith("/latest"):
            issue_id = path.removeprefix("/api/context/").removesuffix("/latest")
            return self._live_context_latest_payload(issue_id)
        if path == "/api/gates/latest":
            return self._live_gate_latest_payload()
        if path == "/api/audit/recent":
            return self._live_audit_recent_payload()
        if path in _EXPORT_ENDPOINTS:
            return ApiResponse(200, self._payload_file(_EXPORT_ENDPOINTS[path]))
        if path.startswith("/api/context/"):
            issue_id = path.removeprefix("/api/context/")
            return self._context_payload(issue_id)
        return _error(404, "not_found", f"Unknown endpoint: {path}")

    def _handle_post(self, path: str, body: str | bytes) -> ApiResponse:
        if path not in _PREVIEW_ENDPOINTS and path not in _CREATE_ENDPOINTS:
            return _error(
                405,
                "method_not_allowed",
                "POST is only available for preview or authenticated create "
                "endpoints.",
            )
        payload = _json_body(body)
        if isinstance(payload, ApiResponse):
            return payload
        try:
            if path == "/api/forge/local-issues/preview":
                return self._preview_local_issue(payload)
            if path == "/api/forge/issues/preview":
                return self._preview_github_issue(payload)
            if path == "/api/forge/prs/preview":
                return self._preview_github_pr(payload)
            if path == "/api/forge/review-packets/preview":
                return self._preview_review_packet(payload)
            if path == "/api/forge/issues/create":
                return self._create_github_issue(payload)
            if path == "/api/forge/prs/create":
                return self._create_github_pr(payload)
        except ForgeActionError as exc:
            return _error(400, exc.code, "forge action failed; see backend audit")
        except ValueError as exc:
            return _error(400, "preview_invalid_input", str(exc))
        return _error(404, "not_found", f"Unknown endpoint: {path}")

    def _health_payload(self) -> dict[str, Any]:
        return {
            "schema_version": READONLY_SERVER_SCHEMA_VERSION,
            "status": "ok",
            "readonly": True,
            "host": self.host,
            "repo_root": str(self.app.context.repo_root),
            "authority_notice": SITE_EXPORT_AUTHORITY_NOTICE,
        }

    def _live_workspace_payload(self) -> ApiResponse:
        return _live_response(
            "workspace_live",
            workspace=_workspace_info_payload(self.app.workspace_info()),
        )

    def _live_status_payload(self) -> ApiResponse:
        validation = self.app.validate_repository()
        return _live_response(
            "repository_status",
            status="ok" if validation.ok else "validation_failed",
            workspace=_workspace_info_payload(self.app.workspace_info()),
            validation=_validation_payload(validation),
        )

    def _live_issues_payload(self) -> ApiResponse:
        result = self.app.list_issues()
        issues = [
            {
                **issue.model_dump(mode="json"),
                "path": path.as_posix(),
            }
            for issue, path in zip(result.issues, result.paths, strict=True)
        ]
        return _live_response(
            "issues_live",
            issues=issues,
            count=len(issues),
            authority_notice=ISSUE_AUTHORITY_NOTICE,
        )

    def _live_issue_payload(self, issue_id: str) -> ApiResponse:
        try:
            result = self.app.show_issue(issue_id)
        except (LocalIssueError, ValueError):
            return _error(
                404,
                "issue_not_found",
                f"No repository-local issue exists for: {issue_id}",
            )
        issue = result.issue.model_dump(mode="json")
        issue["path"] = result.relative_path.as_posix()
        return _live_response(
            "issue_live",
            issue=issue,
            authority_notice=result.authority_notice,
        )

    def _live_artifacts_payload(self) -> ApiResponse:
        loaded = self._live_artifact_records()
        if isinstance(loaded, ApiResponse):
            return loaded
        artifacts = [_artifact_payload(record) for record in loaded]
        return _live_response(
            "artifacts_live",
            artifacts=artifacts,
            count=len(artifacts),
        )

    def _live_artifact_payload(self, artifact_id: str) -> ApiResponse:
        try:
            normalized_id = validate_artifact_id(artifact_id)
        except ValueError:
            return _error(
                404,
                "artifact_not_found",
                f"No lifecycle artifact exists for: {artifact_id}",
            )
        loaded = self._live_artifact_records()
        if isinstance(loaded, ApiResponse):
            return loaded
        for record in loaded:
            if record.id == normalized_id:
                return _live_response(
                    "artifact_live",
                    artifact=_artifact_payload(record),
                )
        return _error(
            404,
            "artifact_not_found",
            f"No lifecycle artifact exists for: {normalized_id}",
        )

    def _live_context_latest_payload(self, issue_id: str) -> ApiResponse:
        if not issue_id:
            return _error(404, "issue_not_found", "No issue id was provided.")
        try:
            self.app.show_issue(issue_id)
        except (LocalIssueError, ValueError):
            return _error(
                404,
                "issue_not_found",
                f"No repository-local issue exists for: {issue_id}",
            )
        task_dir = self.app.context.resolve(Path("context") / "TASKS" / issue_id)
        files = _repo_files_under(self.app.context.repo_root, task_dir)
        audit = _read_json_file(task_dir / "RETRIEVAL_AUDIT.json")
        return _live_response(
            "context_pack_latest",
            issue_id=issue_id,
            context_pack={
                "exists": task_dir.is_dir(),
                "task_dir": _repo_relative_or_string(
                    self.app.context.repo_root,
                    task_dir,
                ),
                "files": files,
                "retrieval_audit": audit,
                "authority_notice": (
                    "Context packs are retrieval context only; they are not "
                    "proof, verifier pass, gate pass, human review, accepted "
                    "status, or promotion authority."
                ),
            },
        )

    def _live_gate_latest_payload(self) -> ApiResponse:
        reports_dir = self.app.context.resolve(Path(".cosheaf") / "reports")
        candidates = sorted(reports_dir.glob("*-gate-report.json"))
        if not candidates:
            return _live_response(
                "gate_latest",
                gate_report={
                    "exists": False,
                    "path": None,
                    "report": None,
                    "verdict": "not_run",
                    "note": "No gate report exists under .cosheaf/reports.",
                },
            )
        latest = candidates[-1]
        report = _read_json_file(latest)
        if report is None:
            return _error(
                500,
                "gate_report_unreadable",
                "Latest gate report could not be read as JSON.",
            )
        return _live_response(
            "gate_latest",
            gate_report={
                "exists": True,
                "path": _repo_relative_or_string(self.app.context.repo_root, latest),
                "report": report,
                "verdict": report.get("verdict"),
            },
        )

    def _live_audit_recent_payload(self) -> ApiResponse:
        audit_path = self.app.context.resolve(WEB_ACTION_AUDIT_PATH)
        entries = _read_jsonl_file(audit_path)
        if isinstance(entries, ApiResponse):
            return entries
        recent = entries[-50:]
        return _live_response(
            "web_action_audit_recent",
            audit={
                "exists": audit_path.is_file(),
                "path": WEB_ACTION_AUDIT_PATH.as_posix(),
            },
            entries=recent,
            count=len(recent),
        )

    def _live_artifact_records(self) -> tuple[LoadedRecord, ...] | ApiResponse:
        try:
            records = tuple(load_artifacts(self.app.context))
        except LoadError as exc:
            return _error(
                500,
                "repository_load_failed",
                f"Cannot load repository records: {exc}",
            )
        return tuple(
            record for record in records if isinstance(record.record, BaseArtifact)
        )

    def _context_payload(self, issue_id: str) -> ApiResponse:
        payload = self._payload_file("context_packs.json")
        for context_pack in payload["context_packs"]:
            if context_pack["issue_id"] == issue_id:
                return ApiResponse(
                    200,
                    {
                        "schema_version": READONLY_SERVER_SCHEMA_VERSION,
                        "kind": "context_pack",
                        "issue_id": issue_id,
                        "context_pack": context_pack,
                        "authority_notice": SITE_EXPORT_AUTHORITY_NOTICE,
                    },
                )
        return _error(
            404,
            "context_pack_not_found",
            f"No exported context pack summary for issue: {issue_id}",
        )

    def _preview_local_issue(self, payload: dict[str, Any]) -> ApiResponse:
        result = self.app.preview_issue(
            issue_id=_required_text(payload, "issue_id"),
            title=_required_text(payload, "title"),
            summary=_optional_text(payload, "summary"),
            authors=_text_list(payload, "authors"),
            labels=_text_list(payload, "labels"),
            related_artifacts=_text_list(payload, "related_artifacts"),
            related_sources=_text_list(payload, "related_sources"),
            scope=_scope(payload.get("scope", "private")),
        )
        planned_file = result.relative_path.as_posix()
        self._write_audit(
            action="local_issue_preview",
            result_status="preview",
            explicit_confirm=False,
            preview_only=True,
            planned_files=[planned_file],
        )
        return _preview_response(
            "local_issue_preview",
            planned_actions=["create repository-local issue YAML preview"],
            planned_files=[planned_file],
            issue=result.issue.model_dump(mode="json"),
        )

    def _preview_github_issue(self, payload: dict[str, Any]) -> ApiResponse:
        source_path = _required_text(payload, "source_path")
        result = self.app.forge_issue_preview(source_path)
        result_payload = result.model_dump(mode="json")
        self._write_audit(
            action="github_issue_preview",
            result_status="preview",
            explicit_confirm=False,
            preview_only=True,
            planned_files=[source_path],
        )
        return _preview_response(
            "github_issue_preview",
            planned_actions=["create GitHub issue preview"],
            planned_files=[source_path],
            forge_preview=result_payload,
            github_issue_plan=result_payload.get("github_issue_plan"),
        )

    def _preview_github_pr(self, payload: dict[str, Any]) -> ApiResponse:
        base = _required_text(payload, "base")
        head = _required_text(payload, "head")
        result = self.app.forge_pr_preview(
            base=base,
            head=head,
        )
        result_payload = result.model_dump(mode="json")
        self._write_audit(
            action="github_pr_preview",
            result_status="preview",
            explicit_confirm=False,
            preview_only=True,
            planned_files=[],
            base=base,
            head=head,
        )
        return _preview_response(
            "github_pr_preview",
            planned_actions=["create GitHub pull request preview"],
            planned_files=[],
            forge_preview=result_payload,
            github_pr_plan=result_payload.get("github_pr_plan"),
        )

    def _preview_review_packet(self, payload: dict[str, Any]) -> ApiResponse:
        issue_id = _required_text(payload, "issue_id")
        issue = self.app.show_issue(issue_id).issue
        planned_file = f"reviews/website/{issue_id}-review-packet.md"
        self._write_audit(
            action="review_packet_preview",
            result_status="preview",
            explicit_confirm=False,
            preview_only=True,
            planned_files=[planned_file],
        )
        return _preview_response(
            "review_packet_preview",
            planned_actions=["create review packet markdown preview"],
            planned_files=[planned_file],
            issue=issue.model_dump(mode="json"),
            review_packet={
                "issue_id": issue_id,
                "title": issue.title,
                "sections": [
                    "issue summary",
                    "related artifacts",
                    "context pack",
                    "authority-boundary checklist",
                ],
            },
        )

    def _create_github_issue(self, payload: dict[str, Any]) -> ApiResponse:
        action = "github_issue_create"
        source_path = _required_text(payload, "source_path")
        blocked = self._blocked_create(action, payload)
        if blocked is not None:
            return blocked
        try:
            result = self.app.forge_github_issue_create(
                source_path,
                confirm=True,
            )
        except ForgeActionError as exc:
            self._write_action_failure(
                action=action,
                result_status=exc.code,
                planned_files=[source_path],
            )
            raise
        return self._action_response(
            "github_issue_create",
            result,
            planned_files=[source_path],
            repo_writes_performed=True,
        )

    def _create_github_pr(self, payload: dict[str, Any]) -> ApiResponse:
        action = "github_pr_create"
        base = _required_text(payload, "base")
        head = _required_text(payload, "head")
        blocked = self._blocked_create(action, payload)
        if blocked is not None:
            return blocked
        try:
            result = self.app.forge_github_pr_create(
                base=base,
                head=head,
                draft=_bool(payload, "draft", default=False),
                confirm=True,
            )
        except ForgeActionError as exc:
            self._write_action_failure(
                action=action,
                result_status=exc.code,
                planned_files=[],
                base=base,
                head=head,
            )
            raise
        return self._action_response(
            "github_pr_create",
            result,
            planned_files=[],
            repo_writes_performed=False,
        )

    def _blocked_create(
        self,
        action: str,
        payload: dict[str, Any],
    ) -> ApiResponse | None:
        explicit_confirm = payload.get("confirm") is True
        if not explicit_confirm:
            self._write_audit(
                action=action,
                result_status="confirm_required",
                explicit_confirm=False,
                preview_only=False,
            )
            return _error(400, "confirm_required", "create requires confirm: true")
        provider = self.credential_provider
        if provider is None or not provider.has_github_token():
            self._write_audit(
                action=action,
                result_status="auth_required",
                explicit_confirm=True,
                preview_only=False,
                credential_provider=self._credential_provider_name(),
            )
            return _error(
                401,
                "auth_required",
                "authenticated forge create requires backend GitHub credentials",
            )
        return None

    def _action_response(
        self,
        kind: str,
        result: ForgeActionResult,
        *,
        planned_files: list[str],
        repo_writes_performed: bool,
    ) -> ApiResponse:
        payload = result.model_dump(mode="json")
        self._write_audit(
            action=result.action,
            result_status="success",
            explicit_confirm=True,
            preview_only=False,
            credential_provider=self._credential_provider_name(),
            planned_files=planned_files,
            repo_writes_performed=repo_writes_performed,
            result=payload,
        )
        return ApiResponse(
            200,
            {
                "schema_version": READONLY_SERVER_SCHEMA_VERSION,
                "kind": kind,
                "action_performed": result.action_performed,
                "repo_writes_performed": repo_writes_performed,
                "git_writes_performed": result.git_writes_performed,
                "github_writes_performed": result.github_writes_performed,
                "network_calls_performed": result.network_calls_performed,
                "audit_logged": True,
                "forge_action": payload,
                "authority_warning": FORGE_AUTHORITY_WARNING,
                "authority_notice": SITE_EXPORT_AUTHORITY_NOTICE,
            },
        )

    def _write_action_failure(
        self,
        *,
        action: str,
        result_status: str,
        planned_files: list[str],
        base: str | None = None,
        head: str | None = None,
    ) -> None:
        self._write_audit(
            action=action,
            result_status=result_status,
            explicit_confirm=True,
            preview_only=False,
            credential_provider=self._credential_provider_name(),
            planned_files=planned_files,
            base=base,
            head=head,
        )

    def _credential_provider_name(self) -> str | None:
        return (
            self.credential_provider.provider_name()
            if self.credential_provider
            else None
        )

    def _write_audit(
        self,
        *,
        action: str,
        result_status: str,
        explicit_confirm: bool,
        preview_only: bool,
        credential_provider: str | None = None,
        planned_files: list[str] | None = None,
        repo_writes_performed: bool = False,
        base: str | None = None,
        head: str | None = None,
        branch: str | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        result = result or {}
        github_url = result.get("github_issue_url") or result.get("github_pr_url")
        performed = result_status == "success" and bool(
            result.get("action_performed", False)
        )
        error_code = None if result_status in {"preview", "success"} else result_status
        errors = []
        if error_code is not None:
            errors.append(
                WebActionError(
                    code=error_code,
                    message="web action did not complete",
                    remediation="Inspect the API response and backend credentials.",
                    blocking=True,
                )
            )
        append_web_action_audit(
            self.app.context,
            WebActionAuditEntry(
                timestamp=datetime.now(UTC).replace(microsecond=0),
                actor="local.web",
                action=_web_action_kind(action),
                mode=WebActionMode.LOCAL,
                repo_root=str(self.app.context.repo_root),
                branch=branch or _optional_str(result.get("branch")),
                base=base or _optional_str(result.get("base")),
                head=head or _optional_str(result.get("head")),
                preview_only=preview_only,
                confirm_required=result_status == "confirm_required",
                confirmed=explicit_confirm,
                explicit_confirm=explicit_confirm,
                performed=performed,
                repo_writes_performed=repo_writes_performed,
                git_writes_performed=bool(result.get("git_writes_performed", False)),
                github_writes_performed=bool(
                    result.get("github_writes_performed", False)
                ),
                network_calls_performed=bool(
                    result.get("network_calls_performed", False)
                ),
                planned_files=planned_files or [],
                written_files=(planned_files or []) if repo_writes_performed else [],
                validation_summary=_performed_summary(result, "validation_performed"),
                gate_summary=_performed_summary(result, "gate_performed"),
                github_urls=[github_url] if isinstance(github_url, str) else [],
                credential_provider=credential_provider,
                result_status=result_status,
                authority_warnings=[FORGE_AUTHORITY_WARNING],
                error_code=error_code,
                errors=errors,
            ),
        )

    def _payload_file(self, filename: str) -> dict[str, Any]:
        payloads = self._site_payloads()
        return payloads[filename]

    def _site_payloads(self) -> dict[str, dict[str, Any]]:
        with TemporaryDirectory(prefix="cosheaf-site-api-") as temp_dir:
            out = Path(temp_dir)
            self.app.export_site_data(out)
            return {
                filename: json.loads((out / filename).read_text(encoding="utf-8"))
                for filename in REQUIRED_SITE_EXPORT_FILES
            }


def make_handler(api: ReadOnlySiteApi) -> type[BaseHTTPRequestHandler]:
    """Create an HTTP handler class bound to a read-only API router."""

    class ReadOnlySiteRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self._send(api.handle("GET", self.path))

        def do_POST(self) -> None:  # noqa: N802
            self._send(api.handle("POST", self.path, self._read_body()))

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self._send_cors_headers()
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_PUT(self) -> None:  # noqa: N802
            self._send(api.handle("PUT", self.path))

        def do_PATCH(self) -> None:  # noqa: N802
            self._send(api.handle("PATCH", self.path))

        def do_DELETE(self) -> None:  # noqa: N802
            self._send(api.handle("DELETE", self.path))

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send(self, response: ApiResponse) -> None:
            body = response.body()
            self.send_response(response.status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(body)

        def _read_body(self) -> bytes:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            return self.rfile.read(length)

        def _send_cors_headers(self) -> None:
            origin = self.headers.get("Origin")
            if origin is not None and _allowed_cors_origin(origin):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    return ReadOnlySiteRequestHandler


def serve_readonly_api(
    app: CosheafApp,
    *,
    host: str = READONLY_SERVER_HOST,
    port: int = READONLY_SERVER_PORT,
) -> None:
    """Serve the read-only local website API until interrupted."""
    api = ReadOnlySiteApi(app, host=host)
    server = HTTPServer((host, port), make_handler(api))
    try:
        server.serve_forever()
    finally:
        server.server_close()


def _normalize_path(raw_path: str) -> str:
    path = unquote(urlparse(raw_path).path)
    if path != "/":
        path = path.rstrip("/")
    return path or "/"


def _allowed_cors_origin(origin: str | None) -> bool:
    if not origin:
        return False
    parsed = urlparse(origin)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {
        "localhost",
        "127.0.0.1",
        "::1",
    }


def _json_body(body: str | bytes) -> dict[str, Any] | ApiResponse:
    try:
        text = body.decode("utf-8") if isinstance(body, bytes) else body
        payload = json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        return _error(400, "invalid_json", str(exc))
    if not isinstance(payload, dict):
        return _error(400, "invalid_json", "Expected a JSON object request body.")
    return cast(dict[str, Any], payload)


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_text(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string when provided")
    return value.strip()


def _bool(payload: dict[str, Any], key: str, *, default: bool) -> bool:
    value = payload.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _text_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list of strings")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{key} must be a list of non-empty strings")
        result.append(item.strip())
    return result


def _scope(value: object) -> Literal["private", "public"]:
    if not isinstance(value, str):
        raise ValueError("scope must be private or public")
    normalized = value.strip()
    if normalized not in {"private", "public"}:
        raise ValueError("scope must be private or public")
    return cast(Literal["private", "public"], normalized)


def _preview_response(
    kind: str,
    *,
    planned_actions: list[str],
    planned_files: list[str],
    **extra: Any,
) -> ApiResponse:
    return ApiResponse(
        200,
        {
            "schema_version": READONLY_SERVER_SCHEMA_VERSION,
            "kind": kind,
            "dry_run_only": True,
            "repo_writes_performed": False,
            "git_writes_performed": False,
            "github_writes_performed": False,
            "network_calls_performed": False,
            "planned_actions": planned_actions,
            "planned_files": planned_files,
            "authority_warning": FORGE_PREVIEW_AUTHORITY_WARNING,
            "authority_notice": SITE_EXPORT_AUTHORITY_NOTICE,
            **extra,
        },
    )


def _web_action_kind(action: str) -> WebActionKind:
    mapping = {
        "local_issue_preview": WebActionKind.ISSUE_CREATE,
        "github_issue_preview": WebActionKind.ISSUE_PUBLISH_GITHUB,
        "github_issue_create": WebActionKind.ISSUE_PUBLISH_GITHUB,
        "github_pr_preview": WebActionKind.FORGE_PR_CREATE,
        "github_pr_create": WebActionKind.FORGE_PR_CREATE,
        "review_packet_preview": WebActionKind.REVIEW_PACKET_CREATE,
    }
    try:
        return mapping[action]
    except KeyError as exc:
        raise ValueError(f"unknown web action audit kind: {action}") from exc


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _performed_summary(result: dict[str, Any], key: str) -> str | None:
    if result.get(key) is True:
        return "performed"
    return None


def _live_response(kind: str, **payload: Any) -> ApiResponse:
    authority_notice = payload.pop("authority_notice", SITE_EXPORT_AUTHORITY_NOTICE)
    return ApiResponse(
        200,
        {
            "schema_version": READONLY_SERVER_SCHEMA_VERSION,
            "kind": kind,
            "source_of_truth": "repository",
            "authority_notice": authority_notice,
            **payload,
        },
    )


def _workspace_info_payload(info: Any) -> dict[str, Any]:
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


def _validation_payload(report: Any) -> dict[str, Any]:
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


def _artifact_payload(record: LoadedRecord) -> dict[str, Any]:
    artifact = cast(BaseArtifact, record.record)
    payload = artifact.model_dump(mode="json")
    payload["path"] = record.source_path.as_posix()
    payload["kb_root"] = record.kb_root_name
    payload["kb_root_readonly"] = record.kb_root_readonly
    if record.kb_relative_path is not None:
        payload["kb_relative_path"] = record.kb_relative_path.as_posix()
    return payload


def _repo_files_under(repo_root: Path, root: Path) -> list[str]:
    if not root.is_dir():
        return []
    return [
        _repo_relative_or_string(repo_root, path)
        for path in sorted(root.iterdir())
        if path.is_file()
    ]


def _read_json_file(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl_file(path: Path) -> list[dict[str, Any]] | ApiResponse:
    if not path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return _error(
            500,
            "audit_log_unreadable",
            "Web action audit log could not be read.",
        )
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            return _error(
                500,
                "audit_log_unreadable",
                f"Web action audit log line {index} is not valid JSON.",
            )
        if isinstance(raw, dict):
            entries.append(cast(dict[str, Any], raw))
    return entries


def _repo_relative_or_string(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _error(status: int, code: str, message: str) -> ApiResponse:
    return ApiResponse(
        status,
        {
            "schema_version": READONLY_SERVER_SCHEMA_VERSION,
            "code": code,
            "message": message,
            "blocking": True,
            "authority_notice": SITE_EXPORT_AUTHORITY_NOTICE,
        },
    )
