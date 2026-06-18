"""Read-only local HTTP API for website preview."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from urllib.parse import unquote, urlparse

from cosheaf.app import CosheafApp
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

    def handle(self, method: str, raw_path: str) -> ApiResponse:
        """Return a JSON response for one HTTP-like request."""
        if method.upper() != "GET":
            return _error(
                405,
                "method_not_allowed",
                "The local website API is read-only and only accepts GET.",
            )

        path = _normalize_path(raw_path)
        if path == "/api/health":
            return ApiResponse(200, self._health_payload())
        if path in _EXPORT_ENDPOINTS:
            return ApiResponse(200, self._payload_file(_EXPORT_ENDPOINTS[path]))
        if path.startswith("/api/context/"):
            issue_id = path.removeprefix("/api/context/")
            return self._context_payload(issue_id)
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
            self._send(api.handle("POST", self.path))

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
            self.end_headers()
            self.wfile.write(body)

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
