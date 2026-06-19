"""CLI adapter for the read-only local website API server."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from cosheaf.app import open_app
from cosheaf.server.api import (
    READONLY_SERVER_HOST,
    READONLY_SERVER_PORT,
    serve_readonly_api,
)

server_app = typer.Typer(
    add_completion=False,
    help="Local read-only API server commands.",
    no_args_is_help=True,
)


@server_app.command("serve")
def server_serve(
    readonly: bool = typer.Option(
        False,
        "--readonly",
        help="Required guard confirming the server will expose read-only APIs.",
    ),
    port: int = typer.Option(
        READONLY_SERVER_PORT,
        "--port",
        min=1,
        max=65535,
        help="Loopback TCP port.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to serve.",
    ),
    local_actor: str | None = typer.Option(
        None,
        "--local-actor",
        help=(
            "Local operator name recorded in web-action audit logs. This is "
            "not authentication or cryptographic identity."
        ),
    ),
) -> None:
    """Serve local read-only website JSON APIs on localhost."""
    console = Console(width=120, markup=False)
    if not readonly:
        console.print("server_serve_refused: pass --readonly to expose local APIs")
        raise typer.Exit(code=1)

    app = open_app(repo_root)
    console.print(
        f"Serving read-only website API on http://{READONLY_SERVER_HOST}:{port}"
    )
    console.print("- writes: disabled")
    local_actor_label = local_actor.strip() if local_actor else "not set"
    console.print(f"- local actor: {local_actor_label}")
    console.print("- authority: display context only")
    serve_readonly_api(
        app,
        host=READONLY_SERVER_HOST,
        port=port,
        local_actor=local_actor,
    )
