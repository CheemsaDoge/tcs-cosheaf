"""Stable application-usecase boundary for non-CLI callers."""

from __future__ import annotations

from cosheaf.app.facade import CosheafApp, open_app

__all__ = [
    "CosheafApp",
    "open_app",
]
