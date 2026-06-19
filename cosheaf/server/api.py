"""Read-only local HTTP API for website preview."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal, cast
from urllib.parse import unquote, urlparse

from cosheaf.app import CosheafApp
from cosheaf.forge import FORGE_PREVIEW_AUTHORITY_WARNING
from cosheaf.site import REQUIRED_SITE_EXPORT_FILES, SITE_EXPORT_AUTHORITY_NOTICE

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
    ) -> None:
        self.app = app
        self.host = host

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
        if path in _EXPORT_ENDPOINTS:
            return ApiResponse(200, self._payload_file(_EXPORT_ENDPOINTS[path]))
        if path.startswith("/api/context/"):
            issue_id = path.removeprefix("/api/context/")
            return self._context_payload(issue_id)
        return _error(404, "not_found", f"Unknown endpoint: {path}")

    def _handle_post(self, path: str, body: str | bytes) -> ApiResponse:
        if path not in _PREVIEW_ENDPOINTS:
            return _error(
                405,
                "method_not_allowed",
                "POST is only available for preview-only endpoints.",
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
        return _preview_response(
            "github_issue_preview",
            planned_actions=["create GitHub issue preview"],
            planned_files=[source_path],
            forge_preview=result_payload,
            github_issue_plan=result_payload.get("github_issue_plan"),
        )

    def _preview_github_pr(self, payload: dict[str, Any]) -> ApiResponse:
        result = self.app.forge_pr_preview(
            base=_required_text(payload, "base"),
            head=_required_text(payload, "head"),
        )
        result_payload = result.model_dump(mode="json")
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
