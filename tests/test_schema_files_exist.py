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
    "schemas/counterexample_evidence.schema.json",
    "schemas/issue.schema.json",
    "schemas/operator_handoff.schema.json",
    "schemas/review.schema.json",
    "schemas/site_export.schema.json",
    "schemas/attempt_evidence_summary.schema.json",
    "schemas/attempt_failure_record.schema.json",
    "schemas/attempt_next_action.schema.json",
    "schemas/attempt_policy_finding.schema.json",
    "schemas/loop_review_summary.schema.json",
    "schemas/operator_result_failure.schema.json",
    "schemas/previous_failure_summary.schema.json",
    "schemas/research_run.schema.json",
    "schemas/research_loop.schema.json",
    "schemas/research_loop_attempt.schema.json",
    "schemas/research_loop_attempt_memory.schema.json",
    "schemas/research_loop_attempt_memory_entry.schema.json",
    "schemas/research_loop_budget.schema.json",
    "schemas/research_loop_decision.schema.json",
    "schemas/research_loop_failure_cluster.schema.json",
    "schemas/research_loop_import_result.schema.json",
    "schemas/research_loop_metrics.schema.json",
    "schemas/research_loop_next_result.schema.json",
    "schemas/research_loop_operator_result.schema.json",
    "schemas/research_loop_operator_task.schema.json",
    "schemas/research_loop_run_result.schema.json",
    "schemas/research_loop_scan.schema.json",
    "schemas/research_loop_scan_finding.schema.json",
    "schemas/research_loop_step_result.schema.json",
    "schemas/research_loop_stop_condition.schema.json",
    "schemas/verifier.schema.json",
    "schemas/verifier_evidence.schema.json",
    "schemas/task.schema.json",
    "schemas/orchestrator_run.schema.json",
    "schemas/worker_bundle_v2.schema.json",
    "schemas/formal_library.schema.json",
    "schemas/web_action.schema.json",
    "schemas/agent_access/context_build_request.schema.json",
    "schemas/agent_access/context_build_result.schema.json",
    "schemas/agent_access/create_task_request.schema.json",
    "schemas/agent_access/create_task_result.schema.json",
    "schemas/agent_access/draft_artifact_write_request.schema.json",
    "schemas/agent_access/draft_artifact_write_result.schema.json",
    "schemas/agent_access/error_result.schema.json",
    "schemas/agent_access/gate_run_result.schema.json",
    "schemas/agent_access/memory_search_request.schema.json",
    "schemas/agent_access/memory_search_result.schema.json",
    "schemas/agent_access/model_call_request.schema.json",
    "schemas/agent_access/model_call_result.schema.json",
    "schemas/agent_access/provider_run_record.schema.json",
    "schemas/agent_access/validate_result.schema.json",
    "schemas/agent_access/worker_bundle_submit_request.schema.json",
    "schemas/agent_access/worker_bundle_submit_result.schema.json",
    "schemas/agent_access/workspace_info_result.schema.json",
]

EXAMPLE_FILES = [
    "examples/issues/issue.example.yaml",
    "examples/issues/issue.agent-dry-run.demo.yaml",
    "examples/claims/claim.example.yaml",
    "examples/claims/claim.agent-dry-run.demo.yaml",
    "examples/claims/claim.formal-link.example.yaml",
    "examples/claims/claim.lean-core-formal-link-pilot.yaml",
    "examples/proofs/proof.example.yaml",
    "examples/constructions/graph.example.yaml",
    "examples/constructions/graph.toy.yaml",
    "examples/reviews/review.example.yaml",
    "examples/tasks/task.example.yaml",
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


def test_artifact_schema_defines_optional_formal_link_fields() -> None:
    schema = json.loads(
        (ROOT / "schemas/artifact.schema.json").read_text(encoding="utf-8")
    )
    properties = schema["properties"]

    assert "formalizations" not in schema["required"]
    assert "alignment" not in schema["required"]
    assert "verification_policy" not in schema["required"]

    formalization = properties["formalizations"]["items"]
    assert formalization["additionalProperties"] is False
    assert formalization["required"] == [
        "id",
        "system",
        "library",
        "library_ref",
        "import_path",
        "symbol",
        "declaration_kind",
        "status",
        "check_mode",
    ]
    assert "expected_type" not in formalization["required"]
    assert "notes" not in formalization["required"]
    assert formalization["properties"]["system"]["enum"] == ["lean4"]
    assert formalization["properties"]["status"]["enum"] == [
        "planned",
        "linked",
        "checked",
        "broken",
        "deprecated",
    ]
    assert formalization["properties"]["check_mode"]["enum"] == [
        "external_library_ref",
        "local_file",
    ]
    assert "CSLib.Graph.Basic" not in formalization["properties"]["library_ref"][
        "pattern"
    ]
    assert "[a-z][a-z0-9]*" in formalization["properties"]["library_ref"]["pattern"]

    alignment = properties["alignment"]
    assert alignment["additionalProperties"] is False
    assert alignment["properties"]["status"]["enum"] == [
        "none",
        "requested",
        "human_reviewed",
        "rejected",
    ]

    verification_policy = properties["verification_policy"]
    assert verification_policy["additionalProperties"] is False
    assert verification_policy["properties"]["level"]["enum"] == [
        "source_reviewed",
        "source_reviewed_with_formal_link",
        "machine_checked",
        "lean_required",
    ]
    assert verification_policy["properties"]["require_formal_link"]["type"] == "boolean"
    assert verification_policy["properties"]["require_lean_check"]["type"] == "boolean"
    assert (
        verification_policy["properties"]["require_alignment_review"]["type"]
        == "boolean"
    )


def test_artifact_schema_defines_optional_failure_log() -> None:
    schema = json.loads(
        (ROOT / "schemas/artifact.schema.json").read_text(encoding="utf-8")
    )
    properties = schema["properties"]

    assert "failure_log" not in schema["required"]
    failure_log = properties["failure_log"]
    assert failure_log["type"] == "array"
    failure_entry = failure_log["items"]
    assert failure_entry["additionalProperties"] is False
    assert failure_entry["required"] == [
        "failure_id",
        "attempted_at",
        "recorded_by",
        "origin",
        "attempt_kind",
        "direction",
        "summary",
        "failed_because",
        "status",
        "limitations",
    ]
    assert failure_entry["properties"]["origin"]["enum"] == [
        "human",
        "agent",
        "provider",
        "verifier",
        "imported_bundle",
    ]
    assert failure_entry["properties"]["attempt_kind"]["enum"] == [
        "proof_attempt",
        "reduction_attempt",
        "construction_attempt",
        "counterexample_search",
        "formalization_attempt",
        "verifier_attempt",
        "retrieval_attempt",
        "other",
    ]
    assert failure_entry["properties"]["status"]["enum"] == [
        "open",
        "superseded",
        "invalidated",
        "resolved",
        "archived",
    ]
    assert failure_entry["properties"]["attempted_at"] == {
        "type": "string",
        "format": "date-time",
    }
    assert failure_entry["properties"]["evidence_paths"]["items"] == {
        "$ref": "#/$defs/repository_local_nonaccepted_path"
    }


def test_formal_library_schema_defines_manifest_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas/formal_library.schema.json").read_text(encoding="utf-8")
    )

    assert schema["required"] == ["schema_version", "libraries"]
    assert schema["properties"]["schema_version"]["const"] == 1
    library = schema["properties"]["libraries"]["items"]
    assert library["additionalProperties"] is False
    assert library["required"] == [
        "id",
        "name",
        "system",
        "git",
        "commit",
        "lean_version",
        "lake_manifest",
    ]
    assert library["properties"]["system"]["enum"] == ["lean4"]


def test_example_files_exist_and_are_valid_yaml() -> None:
    for relative_path in EXAMPLE_FILES:
        path = ROOT / relative_path
        assert path.is_file(), f"missing example: {relative_path}"

        example = _read_yaml(path)
        if relative_path.startswith("examples/tasks/"):
            assert isinstance(example["task_id"], str)
            assert isinstance(example["issue_id"], str)
            assert isinstance(example["worker_type"], str)
            assert isinstance(example["status"], str)
            continue
        assert isinstance(example["id"], str)
        assert isinstance(example["type"], str)
        assert isinstance(example["status"], str)


def test_formal_link_example_uses_planned_fake_cslib_reference() -> None:
    example = _read_yaml(ROOT / "examples/claims/claim.formal-link.example.yaml")

    assert example["status"] == "draft"
    assert example["evidence"] == []
    assert example["alignment"]["status"] == "requested"
    assert (
        example["verification_policy"]["level"]
        == "source_reviewed_with_formal_link"
    )
    assert example["verification_policy"]["require_formal_link"] is True
    assert example["verification_policy"]["require_lean_check"] is False

    formalization = example["formalizations"][0]
    assert formalization["system"] == "lean4"
    assert formalization["library"] == "CSLib"
    assert formalization["library_ref"] == "cslib-main"
    assert formalization["import_path"] == "CSLib.Graph.Basic"
    assert formalization["symbol"] == "CSLib.Graph.Basic.example_symbol"
    assert formalization["status"] == "planned"
    assert formalization["check_mode"] == "external_library_ref"
    assert "Illustrative CSLib symbol only" in formalization["notes"]


def test_lean_core_formal_link_pilot_is_linked_but_not_checked() -> None:
    example = _read_yaml(
        ROOT / "examples/claims/claim.lean-core-formal-link-pilot.yaml"
    )

    assert example["status"] == "draft"
    assert example["evidence"] == []
    assert example["alignment"]["status"] == "requested"
    assert example["alignment"]["reviewer"] == ""
    assert example["verification_policy"]["require_formal_link"] is True
    assert example["verification_policy"]["require_lean_check"] is False
    assert example["verification_policy"]["require_alignment_review"] is False
    assert example["review"]["state"] == "requested"

    formalization = example["formalizations"][0]
    assert formalization["system"] == "lean4"
    assert formalization["library"] == "Lean core"
    assert formalization["library_ref"] == "lean-core"
    assert formalization["import_path"] == "Init"
    assert formalization["symbol"] == "Nat"
    assert formalization["status"] == "linked"
    assert formalization["check_mode"] == "external_library_ref"
    assert "does not prove semantic alignment" in formalization["notes"]


def test_worker_bundle_v2_schema_is_strict() -> None:
    schema = json.loads(
        (ROOT / "schemas/worker_bundle_v2.schema.json").read_text(encoding="utf-8")
    )

    assert schema["additionalProperties"] is False
    assert schema["required"] == [
        "bundle_id",
        "task_id",
        "worker_role",
        "created_at",
        "summary",
        "used_artifacts",
        "used_sources",
        "claims",
        "proposed_artifacts",
        "verification_requests",
        "failures_or_counterexamples",
        "risk_flags",
        "next_steps",
        "confidence",
    ]
    assert schema["properties"]["confidence"]["enum"] == ["low", "medium", "high"]
    assert schema["properties"]["worker_role"] == {"$ref": "#/$defs/worker_type"}
    for optional_review_field in [
        "assumptions",
        "uncertainty",
        "failed_attempts",
        "counterexamples",
        "counterexample_candidates",
        "dependency_questions",
    ]:
        assert optional_review_field not in schema["required"]
        if optional_review_field == "counterexample_candidates":
            assert schema["properties"][optional_review_field]["items"] == {
                "$ref": "#/$defs/counterexample_candidate"
            }
        else:
            assert schema["properties"][optional_review_field]["uniqueItems"] is True
    assert schema["$defs"]["worker_type"]["enum"] == [
        "reasoner",
        "verifier",
        "counterexampleer",
        "construction_searcher",
        "formalizer",
        "literature_scout",
        "orchestrator",
    ]
    proposed_artifact = schema["$defs"]["proposed_artifact"]
    assert proposed_artifact["additionalProperties"] is False
    assert proposed_artifact["required"] == ["path", "summary"]
    counterexample_candidate = schema["$defs"]["counterexample_candidate"]
    assert counterexample_candidate["additionalProperties"] is False
    assert counterexample_candidate["required"] == [
        "candidate_id",
        "construction_summary",
        "evidence_paths",
        "verifier_request_ids",
        "status",
        "limitations",
    ]
    assert counterexample_candidate["properties"]["status"]["enum"] == [
        "proposed",
        "needs_check",
        "checked_false",
        "checked_true",
        "rejected",
        "superseded",
    ]
