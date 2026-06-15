from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from cosheaf.verification.counterexample_evidence import (
    CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
    SKIPPED_CHECKED_COUNTEREXAMPLE_LIMITATION,
    CandidateSource,
    CheckedCounterexampleEvidenceRecord,
    CheckedResult,
    CheckMethod,
)

ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = datetime(2026, 6, 15, 0, 0, tzinfo=UTC)


def _record_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": 1,
        "evidence_id": (
            "checked-counterexample.claim.fixture.target."
            "candidate.fixture.0001.habc123"
        ),
        "target_artifact_id": "claim.fixture.target",
        "candidate_id": "candidate.fixture.0001",
        "candidate_source": "worker_bundle",
        "check_method": "verifier_result",
        "checked_result": "checked_refutes",
        "verifier_evidence_ids": [
            "verifier-evidence.claim.fixture.target.python.habc123"
        ],
        "review_record_paths": [],
        "evidence_paths": [".cosheaf/evidence/candidate-check.json"],
        "created_at": CREATED_AT.isoformat(),
        "checker": "python-checker",
        "limitations": [
            "Checked counterexample evidence is evidence for review only.",
            CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
        ],
    }
    data.update(overrides)
    return data


def test_checked_counterexample_evidence_serializes_deterministically() -> None:
    record = CheckedCounterexampleEvidenceRecord.model_validate(_record_data())

    serialized = record.to_dict()

    assert list(serialized) == [
        "schema_version",
        "evidence_id",
        "target_artifact_id",
        "candidate_id",
        "candidate_source",
        "check_method",
        "checked_result",
        "verifier_evidence_ids",
        "review_record_paths",
        "evidence_paths",
        "created_at",
        "checker",
        "limitations",
    ]
    assert record.candidate_source is CandidateSource.WORKER_BUNDLE
    assert record.check_method is CheckMethod.VERIFIER_RESULT
    assert record.checked_result is CheckedResult.CHECKED_REFUTES
    assert record.is_checked_refutation
    assert record.to_json() == record.to_json()


def test_checked_refutes_requires_supporting_evidence() -> None:
    with pytest.raises(ValidationError, match="checked_refutes requires"):
        CheckedCounterexampleEvidenceRecord.model_validate(
            _record_data(
                verifier_evidence_ids=[],
                review_record_paths=[],
                evidence_paths=[],
            )
        )


def test_skipped_requires_skipped_not_pass_limitation() -> None:
    with pytest.raises(ValidationError, match="skipped is not pass"):
        CheckedCounterexampleEvidenceRecord.model_validate(
            _record_data(
                checked_result="skipped",
                verifier_evidence_ids=[],
                evidence_paths=[],
                limitations=[CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE],
            )
        )

    record = CheckedCounterexampleEvidenceRecord.model_validate(
        _record_data(
            checked_result="skipped",
            verifier_evidence_ids=[],
            evidence_paths=[],
            limitations=[
                CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
                SKIPPED_CHECKED_COUNTEREXAMPLE_LIMITATION,
            ],
        )
    )
    assert record.is_skipped
    assert not record.is_checked_refutation


@pytest.mark.parametrize(
    "path",
    [
        "../outside.yaml",
        "C:/secret/evidence.yaml",
        "/tmp/evidence.yaml",
        "kb/accepted/evidence/unsafe.yaml",
    ],
)
def test_paths_must_be_repository_local_and_nonaccepted(path: str) -> None:
    with pytest.raises(ValidationError):
        CheckedCounterexampleEvidenceRecord.model_validate(
            _record_data(evidence_paths=[path])
        )


def test_schema_file_defines_v1_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas" / "counterexample_evidence.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "TCS-Cosheaf Checked Counterexample Evidence"
    assert schema["additionalProperties"] is False
    assert schema["required"] == [
        "schema_version",
        "evidence_id",
        "target_artifact_id",
        "candidate_id",
        "candidate_source",
        "check_method",
        "checked_result",
        "created_at",
        "checker",
        "limitations",
    ]
    assert schema["properties"]["schema_version"]["const"] == 1
    assert schema["properties"]["candidate_source"]["enum"] == [
        "worker_bundle",
        "failure_log",
        "artifact",
        "manual_note",
        "verifier",
    ]
    assert schema["properties"]["checked_result"]["enum"] == [
        "checked_refutes",
        "checked_does_not_refute",
        "inconclusive",
        "error",
        "skipped",
    ]
    assert schema["allOf"][0]["properties"]["limitations"]["contains"]["const"] == (
        CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE
    )
    assert schema["allOf"][2]["then"]["properties"]["limitations"]["contains"][
        "const"
    ] == SKIPPED_CHECKED_COUNTEREXAMPLE_LIMITATION
