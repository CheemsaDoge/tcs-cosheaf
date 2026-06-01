"""Deterministic YAML writing helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel


def _to_plain_data(data: Any) -> Any:
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    return data


def dump_yaml_deterministic(data: Any) -> str:
    """Serialize data to YAML without sorting mapping keys."""
    text = yaml.safe_dump(
        _to_plain_data(data),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    return text if text.endswith("\n") else f"{text}\n"


def write_yaml_deterministic(path: Path, data: Any) -> None:
    """Write deterministic YAML to a path, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml_deterministic(data), encoding="utf-8", newline="\n")
