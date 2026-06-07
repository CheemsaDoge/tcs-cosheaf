from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from cosheaf.core.artifact import FormalizationRef
from cosheaf.core.formal_library import (
    FormalLibraryManifest,
    FormalLibraryManifestError,
    load_formal_library_manifest,
    validate_formalization_library_refs,
)

ROOT = Path(__file__).resolve().parents[1]


def _formalization_ref(*, library_ref: str = "cslib-main") -> FormalizationRef:
    return FormalizationRef(
        id="cslib.fixture.link",
        system="lean4",
        library="CSLib",
        library_ref=library_ref,
        import_path="CSLib.Graph.Basic",
        symbol="CSLib.Graph.Basic.fixture_symbol",
        declaration_kind="theorem",
        status="planned",
        check_mode="external_library_ref",
    )


def test_formal_library_manifest_parses_required_pinned_metadata() -> None:
    manifest = FormalLibraryManifest.model_validate(
        {
            "schema_version": 1,
            "libraries": [
                {
                    "id": "cslib-main",
                    "name": "CSLib",
                    "system": "lean4",
                    "git": "https://example.invalid/cslib.git",
                    "commit": "0123456789abcdef0123456789abcdef01234567",
                    "lean_version": "lean4-example",
                    "lake_manifest": "lake-manifest.json",
                    "notes": "Fixture manifest entry; metadata only.",
                }
            ],
        }
    )

    library = manifest.require_library_ref("cslib-main")
    assert library.id == "cslib-main"
    assert library.name == "CSLib"
    assert library.system == "lean4"
    assert library.commit == "0123456789abcdef0123456789abcdef01234567"
    assert manifest.library_ids == ("cslib-main",)


def test_formal_library_manifest_rejects_duplicate_ids() -> None:
    with pytest.raises(ValidationError):
        FormalLibraryManifest.model_validate(
            {
                "schema_version": 1,
                "libraries": [
                    {
                        "id": "cslib-main",
                        "name": "CSLib",
                        "system": "lean4",
                        "git": "https://example.invalid/cslib.git",
                        "commit": "0123456789abcdef0123456789abcdef01234567",
                        "lean_version": "lean4-example",
                        "lake_manifest": "lake-manifest.json",
                    },
                    {
                        "id": "cslib-main",
                        "name": "CSLib duplicate",
                        "system": "lean4",
                        "git": "https://example.invalid/cslib.git",
                        "commit": "abcdef0123456789abcdef0123456789abcdef01",
                        "lean_version": "lean4-example",
                        "lake_manifest": "lake-manifest.json",
                    },
                ],
            }
        )


def test_formalization_library_ref_uses_manifest_id_syntax() -> None:
    with pytest.raises(ValidationError):
        _formalization_ref(library_ref="CSLib.Graph.Basic")


def test_formalization_refs_must_resolve_against_manifest() -> None:
    manifest = FormalLibraryManifest.model_validate(
        {
            "schema_version": 1,
            "libraries": [
                {
                    "id": "cslib-main",
                    "name": "CSLib",
                    "system": "lean4",
                    "git": "https://example.invalid/cslib.git",
                    "commit": "0123456789abcdef0123456789abcdef01234567",
                    "lean_version": "lean4-example",
                    "lake_manifest": "lake-manifest.json",
                }
            ],
        }
    )

    validate_formalization_library_refs([_formalization_ref()], manifest)
    with pytest.raises(FormalLibraryManifestError, match="unknown library_ref"):
        validate_formalization_library_refs(
            [_formalization_ref(library_ref="mathlib-main")],
            manifest,
        )


def test_example_lean_libraries_manifest_loads() -> None:
    manifest = load_formal_library_manifest(
        ROOT / "formal-libs" / "lean-libraries.example.yaml"
    )

    assert manifest.schema_version == 1
    assert "cslib-main" in manifest.library_ids
    assert "mathlib-main" in manifest.library_ids
