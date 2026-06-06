"""Deterministic memory graph and global PageRank sidecar builder."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import Field, ValidationError, field_validator
from yaml import YAMLError

from cosheaf.core.artifact import BaseArtifact, SourceMetadata
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import repo_relative_posix
from cosheaf.core.task import AgentTask
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.loader import (
    IssueRecord,
    LoadedRecord,
    LoadError,
    ReviewRecord,
    load_artifacts,
)
from cosheaf.storage.repo import RepoContext

MEMORY_GRAPH_SIDECAR = Path(".cosheaf") / "memory" / "graph_snapshot.json"
DETERMINISTIC_GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)
MEMORY_GRAPH_WARNINGS = (
    "memory graph is a rebuildable ranking sidecar, not source of truth",
    "formal links are metadata only unless a checker verifies them",
)

NodeKind = Literal[
    "artifact",
    "issue",
    "review",
    "source_note",
    "verifier_result",
    "task_run",
    "formalization",
]
EdgeKind = Literal[
    "depends_on",
    "supersedes",
    "cites_source",
    "reviews",
    "formalizes",
    "retrieved_for",
    "used_in_success",
    "used_in_failure",
    "rejected_by_verifier",
    "promoted_after_review",
    "same_domain",
    "same_issue_context",
]

EDGE_WEIGHTS: dict[EdgeKind, float] = {
    "depends_on": 3.0,
    "supersedes": 2.0,
    "cites_source": 1.5,
    "reviews": 3.0,
    "formalizes": 1.5,
    "retrieved_for": 0.5,
    "used_in_success": 3.0,
    "used_in_failure": 0.5,
    "rejected_by_verifier": 2.0,
    "promoted_after_review": 3.0,
    "same_domain": 0.25,
    "same_issue_context": 0.5,
}


class MemoryGraphError(ValueError):
    """Raised for expected memory-graph build or read failures."""


class MemoryGraphNode(MemoryModel):
    """One node in the deterministic memory graph sidecar."""

    node_id: str
    kind: NodeKind
    record_id: str
    path: str = ""
    title: str = ""
    status: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("node_id", "record_id")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("graph node identifiers must not be empty")
        return normalized

    @field_validator("path", "title", "status")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        return value.strip()


class MemoryGraphEdge(MemoryModel):
    """One weighted edge in the deterministic memory graph sidecar."""

    source: str
    target: str
    kind: EdgeKind
    weight: float
    evidence: str = ""

    @field_validator("source", "target")
    @classmethod
    def _validate_endpoint(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("graph edge endpoint must not be empty")
        return normalized

    @field_validator("weight")
    @classmethod
    def _validate_weight(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("graph edge weight must be positive")
        return round(value, 6)

    @field_validator("evidence")
    @classmethod
    def _strip_evidence(cls, value: str) -> str:
        return value.strip()


class MemoryGraphSnapshot(MemoryModel):
    """Deterministic rebuildable memory graph snapshot."""

    schema_version: Literal[1] = 1
    generated_at: datetime = DETERMINISTIC_GENERATED_AT
    graph_fingerprint: str
    nodes: list[MemoryGraphNode]
    edges: list[MemoryGraphEdge]
    warnings: list[str] = Field(default_factory=list)

    @field_validator("graph_fingerprint")
    @classmethod
    def _validate_fingerprint(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.startswith("sha256:"):
            raise ValueError("graph_fingerprint must start with sha256:")
        return normalized

    @property
    def node_count(self) -> int:
        """Return the number of graph nodes."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Return the number of graph edges."""
        return len(self.edges)


class PageRankRow(MemoryModel):
    """One deterministic global PageRank row."""

    rank: int
    node_id: str
    kind: NodeKind
    record_id: str
    score: float

    @field_validator("rank")
    @classmethod
    def _validate_rank(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("rank must be positive")
        return value

    @field_validator("score")
    @classmethod
    def _validate_score(cls, value: float) -> float:
        if value < 0:
            raise ValueError("PageRank score must be non-negative")
        return round(value, 12)


class PageRankResult(MemoryModel):
    """Deterministic weighted PageRank result for a memory graph."""

    schema_version: Literal[1] = 1
    algorithm: Literal["weighted-pagerank"] = "weighted-pagerank"
    damping: float = 0.85
    iterations: int
    graph_fingerprint: str
    rows: list[PageRankRow]
    warnings: list[str] = Field(default_factory=list)

    @field_validator("iterations")
    @classmethod
    def _validate_iterations(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("iterations must be positive")
        return value


def build_memory_graph(
    context: RepoContext,
    *,
    persist: bool = False,
) -> MemoryGraphSnapshot:
    """Build a deterministic memory graph from YAML plus optional sidecars."""
    try:
        records = tuple(load_artifacts(context))
    except LoadError as exc:
        raise MemoryGraphError(f"cannot load repository records: {exc}") from exc

    review_records = _load_review_records(context)
    all_records = records + review_records
    nodes: dict[str, MemoryGraphNode] = {}
    edges: set[MemoryGraphEdge] = set()

    artifact_ids: set[str] = set()
    issue_related: dict[str, tuple[str, ...]] = {}
    task_issue_by_id: dict[str, str] = {}
    domains_by_artifact: dict[str, tuple[str, ...]] = {}

    for loaded in all_records:
        record = loaded.record
        if isinstance(record, BaseArtifact):
            artifact_ids.add(record.id)
            domains_by_artifact[record.id] = tuple(sorted(record.domain))
            _add_node(nodes, _artifact_node(loaded, record))
            _add_artifact_edges(edges, loaded, record)
            _add_source_nodes_and_edges(nodes, edges, loaded, record)
            _add_formalization_nodes_and_edges(nodes, edges, loaded, record)
        elif isinstance(record, IssueRecord):
            issue_related[record.id] = tuple(sorted(record.related_artifacts))
            _add_node(nodes, _issue_node(loaded, record))
            _add_issue_edges(edges, loaded, record)
        elif isinstance(record, ReviewRecord):
            _add_node(nodes, _review_node(loaded, record))
            _add_review_edges(edges, loaded, record)
        elif isinstance(record, AgentTask):
            task_issue_by_id[record.task_id] = record.issue_id

    _add_same_domain_edges(edges, domains_by_artifact)
    _add_verifier_result_nodes_and_edges(context, nodes, edges)
    _add_task_run_nodes_and_edges(
        context,
        nodes,
        edges,
        task_issue_by_id=task_issue_by_id,
        issue_related=issue_related,
    )

    pruned_edges = _prune_edges_to_known_nodes(edges, nodes)
    ordered_nodes = sorted(nodes.values(), key=_node_sort_key)
    ordered_edges = sorted(pruned_edges, key=_edge_sort_key)
    graph_fingerprint = _graph_fingerprint(ordered_nodes, ordered_edges)
    snapshot = MemoryGraphSnapshot(
        graph_fingerprint=graph_fingerprint,
        nodes=ordered_nodes,
        edges=ordered_edges,
        warnings=list(MEMORY_GRAPH_WARNINGS),
    )
    if persist:
        write_memory_graph_snapshot(context, snapshot)
    return snapshot


def write_memory_graph_snapshot(
    context: RepoContext,
    snapshot: MemoryGraphSnapshot,
) -> Path:
    """Write a deterministic rebuildable memory graph sidecar."""
    path = context.resolve(MEMORY_GRAPH_SIDECAR)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(snapshot.to_json(), encoding="utf-8", newline="\n")
    return path


def load_memory_graph_snapshot(context: RepoContext) -> MemoryGraphSnapshot:
    """Read the existing memory graph sidecar."""
    path = context.resolve(MEMORY_GRAPH_SIDECAR)
    if not path.is_file():
        raise MemoryGraphError(
            "memory graph sidecar is missing; run "
            "`cosheaf memory graph build` first"
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MemoryGraphError(f"invalid memory graph sidecar JSON: {exc}") from exc
    try:
        return MemoryGraphSnapshot.model_validate(raw)
    except ValidationError as exc:
        raise MemoryGraphError(f"invalid memory graph sidecar schema: {exc}") from exc


def compute_global_pagerank(
    graph: MemoryGraphSnapshot,
    *,
    damping: float = 0.85,
    max_iterations: int = 50,
    tolerance: float = 1e-12,
) -> PageRankResult:
    """Compute deterministic weighted PageRank for a memory graph snapshot."""
    if not graph.nodes:
        return PageRankResult(
            iterations=1,
            graph_fingerprint=graph.graph_fingerprint,
            rows=[],
            warnings=list(graph.warnings),
        )
    if not 0 < damping < 1:
        raise MemoryGraphError("damping must be between 0 and 1")
    if max_iterations <= 0:
        raise MemoryGraphError("max_iterations must be positive")
    if tolerance < 0:
        raise MemoryGraphError("tolerance must be non-negative")

    node_ids = tuple(node.node_id for node in sorted(graph.nodes, key=_node_sort_key))
    node_by_id = {node.node_id: node for node in graph.nodes}
    count = len(node_ids)
    initial = 1.0 / count
    scores = {node_id: initial for node_id in node_ids}
    incoming: dict[str, list[tuple[str, float]]] = {node_id: [] for node_id in node_ids}
    outgoing_weight = {node_id: 0.0 for node_id in node_ids}

    for edge in sorted(graph.edges, key=_edge_sort_key):
        if edge.source not in outgoing_weight or edge.target not in incoming:
            continue
        outgoing_weight[edge.source] += edge.weight
        incoming[edge.target].append((edge.source, edge.weight))

    iterations = max_iterations
    for iteration in range(1, max_iterations + 1):
        sink_score = sum(
            scores[node_id]
            for node_id in node_ids
            if outgoing_weight[node_id] == 0
        )
        next_scores: dict[str, float] = {}
        delta = 0.0
        for node_id in node_ids:
            rank = (1.0 - damping) / count
            rank += damping * sink_score / count
            rank += damping * sum(
                scores[source] * weight / outgoing_weight[source]
                for source, weight in incoming[node_id]
                if outgoing_weight[source] > 0
            )
            next_scores[node_id] = rank
            delta += abs(rank - scores[node_id])
        scores = next_scores
        iterations = iteration
        if delta <= tolerance:
            break

    ordered = sorted(
        (
            (node_id, round(score, 12))
            for node_id, score in scores.items()
        ),
        key=lambda item: (-item[1], item[0]),
    )
    rows = [
        PageRankRow(
            rank=rank,
            node_id=node_id,
            kind=node_by_id[node_id].kind,
            record_id=node_by_id[node_id].record_id,
            score=score,
        )
        for rank, (node_id, score) in enumerate(ordered, start=1)
    ]
    return PageRankResult(
        iterations=iterations,
        graph_fingerprint=graph.graph_fingerprint,
        rows=rows,
        warnings=list(graph.warnings),
    )


def _load_review_records(context: RepoContext) -> tuple[LoadedRecord, ...]:
    review_root = context.resolve("reviews")
    if not review_root.exists():
        return ()
    loaded: list[LoadedRecord] = []
    review_paths = sorted(review_root.rglob("*.yaml")) + sorted(
        review_root.rglob("*.yml")
    )
    for path in review_paths:
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, YAMLError):
            continue
        if not isinstance(raw, dict) or raw.get("type") != "review":
            continue
        try:
            review = ReviewRecord.model_validate(raw)
        except ValidationError:
            continue
        loaded.append(
            LoadedRecord(
                source_path=Path(repo_relative_posix(context.repo_root, path)),
                record=review,
            )
        )
    return tuple(
        sorted(loaded, key=lambda item: (item.source_path.as_posix(), item.id))
    )


def _artifact_node(loaded: LoadedRecord, artifact: BaseArtifact) -> MemoryGraphNode:
    return MemoryGraphNode(
        node_id=_node_id("artifact", artifact.id),
        kind="artifact",
        record_id=artifact.id,
        path=loaded.source_path.as_posix(),
        title=artifact.title,
        status=artifact.status.value,
        metadata={
            "artifact_type": artifact.type.value,
            "domain": ",".join(sorted(artifact.domain)),
            "root": loaded.kb_root_name or "workspace",
        },
    )


def _issue_node(loaded: LoadedRecord, issue: IssueRecord) -> MemoryGraphNode:
    return MemoryGraphNode(
        node_id=_node_id("issue", issue.id),
        kind="issue",
        record_id=issue.id,
        path=loaded.source_path.as_posix(),
        title=issue.title,
        status=issue.status,
        metadata={"severity": issue.severity, "tags": ",".join(sorted(issue.tags))},
    )


def _review_node(loaded: LoadedRecord, review: ReviewRecord) -> MemoryGraphNode:
    return MemoryGraphNode(
        node_id=_node_id("review", review.id),
        kind="review",
        record_id=review.id,
        path=loaded.source_path.as_posix(),
        title=review.title,
        status=review.status,
        metadata={"decision": review.decision, "target": review.target},
    )


def _source_note_node(
    source: SourceMetadata,
) -> MemoryGraphNode:
    record_id = _source_record_id(source)
    return MemoryGraphNode(
        node_id=_node_id("source_note", record_id),
        kind="source_note",
        record_id=record_id,
        title=source.title or source.kind,
        status="metadata",
        metadata={
            "kind": source.kind,
            "authors": ",".join(source.authors),
            "year": str(source.year or ""),
            "doi": source.doi,
            "arxiv": source.arxiv,
            "url": source.url,
            "theorem_number": source.theorem_number,
            "page": source.page,
        },
    )


def _formalization_node(
    artifact_id: str,
    formalization_id: str,
    *,
    library: str,
    import_path: str,
    symbol: str,
    status: str,
) -> MemoryGraphNode:
    return MemoryGraphNode(
        node_id=_node_id("formalization", formalization_id),
        kind="formalization",
        record_id=formalization_id,
        title=symbol,
        status=status,
        metadata={
            "artifact_id": artifact_id,
            "library": library,
            "import_path": import_path,
            "symbol": symbol,
        },
    )


def _add_artifact_edges(
    edges: set[MemoryGraphEdge],
    loaded: LoadedRecord,
    artifact: BaseArtifact,
) -> None:
    artifact_node = _node_id("artifact", artifact.id)
    for dependency_id in artifact.depends_on:
        if dependency_id.startswith("external:"):
            continue
        _add_edge(
            edges,
            artifact_node,
            _node_id("artifact", dependency_id),
            "depends_on",
            evidence=loaded.source_path.as_posix(),
        )
    for superseded_id in artifact.supersedes:
        _add_edge(
            edges,
            artifact_node,
            _node_id("artifact", superseded_id),
            "supersedes",
            evidence=loaded.source_path.as_posix(),
        )


def _add_source_nodes_and_edges(
    nodes: dict[str, MemoryGraphNode],
    edges: set[MemoryGraphEdge],
    loaded: LoadedRecord,
    artifact: BaseArtifact,
) -> None:
    artifact_node = _node_id("artifact", artifact.id)
    for source in artifact.sources:
        source_node = _source_note_node(source)
        _add_node(nodes, source_node)
        _add_edge(
            edges,
            artifact_node,
            source_node.node_id,
            "cites_source",
            evidence=loaded.source_path.as_posix(),
        )


def _add_formalization_nodes_and_edges(
    nodes: dict[str, MemoryGraphNode],
    edges: set[MemoryGraphEdge],
    loaded: LoadedRecord,
    artifact: BaseArtifact,
) -> None:
    artifact_node = _node_id("artifact", artifact.id)
    for formalization in artifact.formalizations:
        formal_node = _formalization_node(
            artifact.id,
            formalization.id,
            library=formalization.library,
            import_path=formalization.import_path,
            symbol=formalization.symbol,
            status=formalization.status,
        )
        _add_node(nodes, formal_node)
        _add_edge(
            edges,
            artifact_node,
            formal_node.node_id,
            "formalizes",
            evidence=loaded.source_path.as_posix(),
        )


def _add_issue_edges(
    edges: set[MemoryGraphEdge],
    loaded: LoadedRecord,
    issue: IssueRecord,
) -> None:
    issue_node = _node_id("issue", issue.id)
    for artifact_id in sorted(issue.related_artifacts):
        artifact_node = _node_id("artifact", artifact_id)
        _add_edge(
            edges,
            issue_node,
            artifact_node,
            "same_issue_context",
            evidence=loaded.source_path.as_posix(),
        )
        _add_edge(
            edges,
            artifact_node,
            issue_node,
            "retrieved_for",
            evidence=loaded.source_path.as_posix(),
        )


def _add_review_edges(
    edges: set[MemoryGraphEdge],
    loaded: LoadedRecord,
    review: ReviewRecord,
) -> None:
    review_node = _node_id("review", review.id)
    artifact_node = _node_id("artifact", review.target)
    _add_edge(
        edges,
        review_node,
        artifact_node,
        "reviews",
        evidence=loaded.source_path.as_posix(),
    )
    if review.status in {"human_reviewed", "accepted"} and review.decision == "approve":
        _add_edge(
            edges,
            review_node,
            artifact_node,
            "promoted_after_review",
            evidence=loaded.source_path.as_posix(),
        )


def _add_same_domain_edges(
    edges: set[MemoryGraphEdge],
    domains_by_artifact: dict[str, tuple[str, ...]],
) -> None:
    artifacts_by_domain: dict[str, list[str]] = defaultdict(list)
    for artifact_id, domains in domains_by_artifact.items():
        for domain in domains:
            artifacts_by_domain[domain].append(artifact_id)
    for domain, artifact_ids in artifacts_by_domain.items():
        ordered = sorted(set(artifact_ids))
        for source in ordered:
            for target in ordered:
                if source == target:
                    continue
                _add_edge(
                    edges,
                    _node_id("artifact", source),
                    _node_id("artifact", target),
                    "same_domain",
                    evidence=f"domain:{domain}",
                )


def _add_verifier_result_nodes_and_edges(
    context: RepoContext,
    nodes: dict[str, MemoryGraphNode],
    edges: set[MemoryGraphEdge],
) -> None:
    reports_dir = context.resolve(Path(".cosheaf") / "reports")
    if not reports_dir.exists():
        return
    for path in sorted(reports_dir.glob("*-gate-report.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        gates = raw.get("gates") if isinstance(raw, dict) else None
        if not isinstance(gates, list):
            continue
        for gate in gates:
            if not isinstance(gate, dict) or gate.get("id") != "G6":
                continue
            details = gate.get("details")
            if not isinstance(details, list):
                continue
            for index, detail in enumerate(details):
                if not isinstance(detail, dict):
                    continue
                _add_verifier_detail_node_and_edge(
                    context,
                    nodes,
                    edges,
                    path=path,
                    detail=detail,
                    index=index,
                )


def _add_verifier_detail_node_and_edge(
    context: RepoContext,
    nodes: dict[str, MemoryGraphNode],
    edges: set[MemoryGraphEdge],
    *,
    path: Path,
    detail: dict[str, Any],
    index: int,
) -> None:
    artifact_id = _optional_artifact_id(detail.get("artifact_id"))
    if artifact_id is None:
        return
    status = str(detail.get("status") or "").strip()
    verifier = str(detail.get("verifier") or "verifier").strip() or "verifier"
    relative_path = repo_relative_posix(context.repo_root, path)
    record_id = _stable_id(
        "verifier",
        {
            "artifact_id": artifact_id,
            "verifier": verifier,
            "status": status,
            "path": relative_path,
            "index": str(index),
        },
    )
    node = MemoryGraphNode(
        node_id=_node_id("verifier_result", record_id),
        kind="verifier_result",
        record_id=record_id,
        path=relative_path,
        title=f"{verifier} {status}".strip(),
        status=status or "unknown",
        metadata={
            "artifact_id": artifact_id,
            "verifier": verifier,
            "message": str(detail.get("message") or ""),
        },
    )
    _add_node(nodes, node)
    if status in {"fail", "error"}:
        _add_edge(
            edges,
            node.node_id,
            _node_id("artifact", artifact_id),
            "rejected_by_verifier",
            evidence=relative_path,
        )
    elif status == "pass":
        _add_edge(
            edges,
            node.node_id,
            _node_id("artifact", artifact_id),
            "used_in_success",
            evidence=relative_path,
        )


def _add_task_run_nodes_and_edges(
    context: RepoContext,
    nodes: dict[str, MemoryGraphNode],
    edges: set[MemoryGraphEdge],
    *,
    task_issue_by_id: dict[str, str],
    issue_related: dict[str, tuple[str, ...]],
) -> None:
    task_root = context.resolve(Path(".cosheaf") / "tasks")
    if not task_root.exists():
        return
    for run_path in sorted(task_root.glob("*/runs/*/run.yaml")):
        try:
            raw = yaml.safe_load(run_path.read_text(encoding="utf-8"))
        except (OSError, YAMLError):
            continue
        if not isinstance(raw, dict):
            continue
        task_id = str(raw.get("task_id") or "").strip()
        run_id = run_path.parent.name
        if not task_id:
            continue
        issue_id = task_issue_by_id.get(task_id)
        status = str(raw.get("status") or "").strip() or "unknown"
        relative_path = repo_relative_posix(context.repo_root, run_path)
        record_id = _stable_id(
            "task-run",
            {"task_id": task_id, "run_id": run_id, "path": relative_path},
        )
        node = MemoryGraphNode(
            node_id=_node_id("task_run", record_id),
            kind="task_run",
            record_id=record_id,
            path=relative_path,
            title=f"{task_id} {run_id}",
            status=status,
            metadata={
                "task_id": task_id,
                "run_id": run_id,
                "issue_id": issue_id or "",
            },
        )
        _add_node(nodes, node)
        if issue_id is not None:
            edge_kind: EdgeKind = (
                "used_in_success"
                if status == "completed"
                else "used_in_failure"
            )
            _add_edge(
                edges,
                node.node_id,
                _node_id("issue", issue_id),
                edge_kind,
                evidence=relative_path,
            )
            for artifact_id in issue_related.get(issue_id, ()):
                _add_edge(
                    edges,
                    node.node_id,
                    _node_id("artifact", artifact_id),
                    edge_kind,
                    evidence=relative_path,
                )


def _prune_edges_to_known_nodes(
    edges: set[MemoryGraphEdge],
    nodes: dict[str, MemoryGraphNode],
) -> set[MemoryGraphEdge]:
    known = frozenset(nodes)
    return {
        edge
        for edge in edges
        if edge.source in known and edge.target in known
    }


def _add_node(
    nodes: dict[str, MemoryGraphNode],
    node: MemoryGraphNode,
) -> None:
    nodes.setdefault(node.node_id, node)


def _add_edge(
    edges: set[MemoryGraphEdge],
    source: str,
    target: str,
    kind: EdgeKind,
    *,
    evidence: str,
) -> None:
    edges.add(
        MemoryGraphEdge(
            source=source,
            target=target,
            kind=kind,
            weight=EDGE_WEIGHTS[kind],
            evidence=evidence,
        )
    )


def _source_record_id(source: SourceMetadata) -> str:
    key = {
        "kind": source.kind,
        "title": source.title,
        "authors": source.authors,
        "year": source.year,
        "doi": source.doi,
        "arxiv": source.arxiv,
        "url": source.url,
        "theorem_number": source.theorem_number,
        "page": source.page,
    }
    return _stable_id("source", key)


def _stable_id(prefix: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"{prefix}.{digest[:16]}"


def _node_id(kind: NodeKind, record_id: str) -> str:
    return f"{kind}:{record_id}"


def _optional_artifact_id(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return validate_artifact_id(value.strip())
    except ValueError:
        return None


def _graph_fingerprint(
    nodes: list[MemoryGraphNode],
    edges: list[MemoryGraphEdge],
) -> str:
    payload = {
        "nodes": [node.to_dict() for node in nodes],
        "edges": [edge.to_dict() for edge in edges],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _node_sort_key(node: MemoryGraphNode) -> tuple[str, str, str, str]:
    return (node.kind, node.record_id, node.node_id, node.path)


def _edge_sort_key(edge: MemoryGraphEdge) -> tuple[str, str, str, str]:
    return (edge.kind, edge.source, edge.target, edge.evidence)
