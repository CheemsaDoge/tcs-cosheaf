import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRECTORIES = [
    "kb/accepted/definitions",
    "kb/accepted/claims",
    "kb/accepted/proofs",
    "kb/accepted/constructions",
    "kb/accepted/algorithms",
    "kb/accepted/reductions",
    "kb/accepted/counterexamples",
    "kb/draft/definitions",
    "kb/draft/claims",
    "kb/draft/proofs",
    "kb/draft/constructions",
    "kb/draft/algorithms",
    "kb/draft/reductions",
    "kb/draft/counterexamples",
    "kb/refuted",
    "kb/obsolete",
    "issues/open",
    "issues/closed",
    "experiments/evaluators",
    "experiments/runs",
    "experiments/logs",
    "experiments/seeds",
    "reviews/ai",
    "reviews/human",
    "reviews/gatekeeper",
]

SCHEMA_FILES = [
    "schemas/artifact.schema.json",
    "schemas/issue.schema.json",
    "schemas/review.schema.json",
    "schemas/verifier.schema.json",
]

EXAMPLE_FILES = [
    "examples/issues/issue.example.yaml",
    "examples/claims/claim.example.yaml",
    "examples/proofs/proof.example.yaml",
    "examples/constructions/graph.example.yaml",
    "examples/constructions/graph.toy.yaml",
    "examples/reviews/review.example.yaml",
]


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_required_directories_exist() -> None:
    for relative_path in REQUIRED_DIRECTORIES:
        path = ROOT / relative_path
        assert path.is_dir(), f"missing directory: {relative_path}"


def test_schema_files_exist_and_are_valid_json() -> None:
    for relative_path in SCHEMA_FILES:
        path = ROOT / relative_path
        assert path.is_file(), f"missing schema: {relative_path}"

        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert isinstance(schema.get("properties"), dict)


def test_example_files_exist_and_are_valid_yaml() -> None:
    for relative_path in EXAMPLE_FILES:
        path = ROOT / relative_path
        assert path.is_file(), f"missing example: {relative_path}"

        example = _read_yaml(path)
        assert isinstance(example["id"], str)
        assert isinstance(example["type"], str)
        assert isinstance(example["status"], str)
