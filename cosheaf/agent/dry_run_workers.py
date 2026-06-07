"""Deterministic local dry-run workers for orchestrator workflow demos.

The module is intentionally local-only. It writes worker bundle v2 manifests
for review workflow testing, but it does not call hosted model providers, use
network services, run gates, request review, write proposal artifacts, or
promote knowledge.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import yaml  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from cosheaf.agent.orchestrator_state import TaskNode
    from cosheaf.agent.task import AgentTask

WORKER_ROLES = (
    "reasoner",
    "verifier",
    "counterexampleer",
    "construction_searcher",
    "formalizer",
    "literature_scout",
    "orchestrator",
)
REASONER = "reasoner"
VERIFIER = "verifier"


def dry_run_worker_command(
    *,
    bundle_path: Path,
    task: AgentTask,
    node: TaskNode,
    proposal_path: str,
    created_at: datetime,
) -> list[str]:
    """Return the explicit argv for one fake local dry-run worker."""
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "--bundle",
        bundle_path.as_posix(),
        "--task-id",
        task.task_id,
        "--worker-role",
        node.worker_type.value,
        "--node-id",
        node.node_id,
        "--proposal",
        proposal_path,
        "--created-at",
        _format_timestamp(created_at),
    ]


def main(argv: list[str] | None = None) -> int:
    """CLI entry point used by the local orchestrator runner."""
    args = _parser().parse_args(argv)
    bundle_path = Path(args.bundle)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = build_dry_run_bundle(
        task_id=args.task_id,
        worker_role=args.worker_role,
        node_id=args.node_id,
        proposal_path=args.proposal,
        created_at=args.created_at,
    )
    bundle_path.write_text(yaml.safe_dump(bundle, sort_keys=False), encoding="utf-8")
    print(f"worker_bundle_v2={bundle_path.as_posix()}")
    return 0


def build_dry_run_bundle(
    *,
    task_id: str,
    worker_role: str,
    node_id: str,
    proposal_path: str,
    created_at: str,
) -> dict[str, object]:
    """Build one role-aware worker bundle v2 mapping."""
    role = worker_role
    if role not in WORKER_ROLES:
        raise ValueError(f"unsupported worker role: {role}")
    base = {
        "bundle_id": f"bundle.{node_id}",
        "task_id": task_id,
        "worker_role": role,
        "created_at": created_at,
        "used_artifacts": [],
        "used_sources": [],
        "proposed_artifacts": [
            {
                "path": proposal_path,
                "summary": "Dry-run proposal path; no artifact is written.",
            }
        ],
        "confidence": "low",
    }
    if role == REASONER:
        return {
            **base,
            "summary": f"Fake local reasoner drafted proposal metadata for {node_id}.",
            "claims": [
                "Candidate reasoning only; this dry-run does not establish a proof.",
                "Any artifact proposal must stay draft until reviewed separately.",
            ],
            "verification_requests": [
                "Ask a verifier worker or external gate step to inspect the draft.",
            ],
            "failures_or_counterexamples": [
                "No proof checker or human review was performed.",
            ],
            "risk_flags": [
                "dry_run_only",
                "draft_proposal_only",
                "needs_verifier",
                "needs_human_review",
            ],
            "next_steps": [
                "Inspect the proposal bundle before any separate review workflow.",
            ],
        }
    if role == VERIFIER:
        return {
            **base,
            "summary": f"Fake local verifier recorded dry-run checks for {node_id}.",
            "claims": [
                "Verifier dry-run observed only bundle structure and workflow shape.",
            ],
            "verification_requests": [
                "Run repository validation and gates outside this dry-run.",
                "Use real verifier adapters separately when a claim requires them.",
            ],
            "failures_or_counterexamples": [
                "No gate, Lean, SAT, SMT, or promotion result was produced.",
            ],
            "risk_flags": [
                "dry_run_only",
                "not_machine_checked",
                "needs_gate",
                "needs_human_review",
            ],
            "next_steps": [
                "Treat this as review context only, not as verification evidence.",
            ],
        }
    return {
        **base,
        "summary": f"Fake local orchestrator worker recorded dry-run step {node_id}.",
        "claims": [
            "This bundle records workflow progress only.",
        ],
        "verification_requests": [
            "Keep gate, review, and promotion as separate explicit steps.",
        ],
        "failures_or_counterexamples": [
            "No external service or authority-bearing review was invoked.",
        ],
        "risk_flags": [
            "dry_run_only",
            "draft_proposal_only",
            "needs_human_review",
        ],
        "next_steps": [
            "Inspect generated bundles before any manual follow-up.",
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a deterministic local dry-run worker bundle."
    )
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--worker-role", required=True, choices=WORKER_ROLES)
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--created-at", required=True)
    return parser


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


if __name__ == "__main__":
    raise SystemExit(main())
