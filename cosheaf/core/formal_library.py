"""Formal library manifest models.

These models describe external Lean libraries referenced by artifact
formalization metadata. They do not run Lean and do not prove that any symbol
exists or is aligned with an informal statement.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, Protocol, Self

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

LIBRARY_REF_PATTERN = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?:\.[a-z][a-z0-9]*(?:-[a-z0-9]+)*)*$"
)


class FormalLibraryManifestError(ValueError):
    """Expected formal library manifest or reference validation error."""


class FormalizationRefLike(Protocol):
    """Minimal protocol for objects carrying a formal library reference."""

    library_ref: str


class FormalLibrary(BaseModel):
    """Pinned metadata for one external Lean library checkout."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    system: Literal["lean4"]
    git: str = Field(min_length=1)
    commit: str = Field(min_length=1)
    lean_version: str = Field(min_length=1)
    lake_manifest: str = Field(min_length=1)
    notes: str = ""

    @field_validator(
        "id",
        "name",
        "git",
        "commit",
        "lean_version",
        "lake_manifest",
        "notes",
    )
    @classmethod
    def _strip_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        return validate_library_ref(value)

    @field_validator("name", "git", "commit", "lean_version", "lake_manifest")
    @classmethod
    def _validate_required_strings(cls, value: str) -> str:
        if not value:
            raise ValueError("formal library manifest field must not be empty")
        return value


class FormalLibraryManifest(BaseModel):
    """Manifest of external formal libraries referenced by artifact metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    libraries: list[FormalLibrary] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_unique_library_ids(self) -> Self:
        seen: set[str] = set()
        duplicates: list[str] = []
        for library in self.libraries:
            if library.id in seen:
                duplicates.append(library.id)
            seen.add(library.id)
        if duplicates:
            duplicate_list = ", ".join(sorted(set(duplicates)))
            raise ValueError(f"duplicate formal library id(s): {duplicate_list}")
        return self

    @property
    def library_ids(self) -> tuple[str, ...]:
        """Return manifest library IDs in manifest order."""
        return tuple(library.id for library in self.libraries)

    def get_library(self, library_ref: str) -> FormalLibrary | None:
        """Return a library by manifest ID, or None when absent."""
        validated = validate_library_ref(library_ref)
        for library in self.libraries:
            if library.id == validated:
                return library
        return None

    def require_library_ref(self, library_ref: str) -> FormalLibrary:
        """Return a library by manifest ID, or raise a manifest error."""
        validated = validate_library_ref(library_ref)
        library = self.get_library(validated)
        if library is None:
            available = ", ".join(self.library_ids)
            raise FormalLibraryManifestError(
                f"unknown library_ref: {validated}; "
                f"available library_ref ids: {available}"
            )
        return library


def validate_library_ref(value: str) -> str:
    """Validate and return a formal library manifest ID."""
    stripped = value.strip()
    if not LIBRARY_REF_PATTERN.fullmatch(stripped):
        raise ValueError(
            "library_ref must be a manifest library id using lowercase slug "
            "segments such as 'cslib-main' or 'lean.mathlib-main'"
        )
    return stripped


def validate_formalization_library_refs(
    refs: list[FormalizationRefLike] | tuple[FormalizationRefLike, ...],
    manifest: FormalLibraryManifest,
) -> None:
    """Require every formalization reference to resolve in a manifest."""
    for ref in refs:
        manifest.require_library_ref(ref.library_ref)


def load_formal_library_manifest(path: str | Path) -> FormalLibraryManifest:
    """Load a formal library manifest YAML file."""
    manifest_path = Path(path)
    raw_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if raw_data is None:
        raw_data = {}
    return FormalLibraryManifest.model_validate(raw_data)
