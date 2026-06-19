import artifactsPayload from "../fixtures/site-data/artifacts.json";
import authorityBoundariesPayload from "../fixtures/site-data/authority_boundaries.json";
import contextPacksPayload from "../fixtures/site-data/context_packs.json";
import gatesPayload from "../fixtures/site-data/gates.json";
import graphPayload from "../fixtures/site-data/graph.json";
import issuesPayload from "../fixtures/site-data/issues.json";
import reportsPayload from "../fixtures/site-data/reports.json";
import sitePayload from "../fixtures/site-data/site.json";
import workspacePayload from "../fixtures/site-data/workspace.json";

export const REQUIRED_DATA_FILES = [
  "site.json",
  "workspace.json",
  "artifacts.json",
  "issues.json",
  "graph.json",
  "gates.json",
  "context_packs.json",
  "reports.json",
  "authority_boundaries.json"
] as const;

export const ROUTES = [
  { path: "/", label: "Home" },
  { path: "/docs", label: "Docs / Concepts" },
  { path: "/demo", label: "Demo" },
  { path: "/artifacts", label: "Artifacts" },
  { path: "/issues", label: "Issues" },
  { path: "/graph", label: "Graph" },
  { path: "/gates", label: "Gate Reports" },
  { path: "/authority", label: "Authority Boundaries" }
] as const;

export const AUTHORITY_GUIDE = [
  {
    title: "What Cosheaf is",
    body: "Cosheaf is a Git-backed workflow for typed research artifacts, review context, evidence records, and reproducible handoff."
  },
  {
    title: "What Cosheaf is not",
    body: "It is not a hosted prover, a human reviewer, a source of private-public promotion, or a replacement for repository records."
  },
  {
    title: "Why gate pass is not truth",
    body: "A gate result can unblock or block workflow review, but it does not prove a statement or make an artifact accepted."
  },
  {
    title: "Why AI output is review context",
    body: "AI output can propose drafts, summaries, or checks for a human to inspect; it cannot become human review by itself."
  },
  {
    title: "Why skipped verifier is not pass",
    body: "Skipped, unavailable, and not-run verifier states mean no successful check was recorded."
  },
  {
    title: "How public and private KB roots work",
    body: "Public KB roots are normally readonly and citable; private KB roots are writable overlays for local research and must not leak into public exports."
  },
  {
    title: "How a result becomes accepted",
    body: "Accepted status comes from repository records, source metadata, validation, gate policy, real human review, and explicit promotion."
  }
] as const;

export interface SiteExportPayload {
  schema_version: 1;
  kind: string;
  authority_notice: string;
  [key: string]: unknown;
}

export interface ArtifactCard {
  id: string;
  title: string;
  type: string;
  status: string;
  root_scope: string;
  summary: string;
  domain: string[];
  tags: string[];
  depends_on: string[];
  demo_fixture: boolean;
  verifier_state: string;
  review_state: string;
  risk_flags: string[];
}

export interface IssueSummary {
  id: string;
  title: string;
  type: string;
  status: string;
  scope: string;
  severity: string;
  summary: string;
  labels: string[];
  related_artifacts: string[];
  related_sources: string[];
  demo_fixture: boolean;
}

export interface ContextPackSummary {
  issue_id: string;
  card_count: number;
  public_only: boolean;
  private_context_included: boolean;
  demo_private_context_included: boolean;
  related_artifacts: string[];
}

export interface GraphNode {
  artifact_id: string;
  artifact_type: string;
  title: string;
  status: string;
  domain: string[];
  path: string;
}

export interface GraphEdge {
  source_id: string;
  target_id: string;
}

export type GraphLayoutMode = "empty" | "pair" | "list";

export interface SitePayload extends SiteExportPayload {
  demo: boolean;
  public_only: boolean;
  files: string[];
  source_of_truth: string;
}

export interface WorkspacePayload extends SiteExportPayload {
  workspace_name: string;
  mode: string;
  public_only: boolean;
  kb_roots: Array<{
    name: string;
    path: string;
    readonly: boolean;
    priority: number;
    demo_private_fixtures_allowed: boolean;
  }>;
  policy: Record<string, boolean>;
}

export interface ArtifactsPayload extends SiteExportPayload {
  artifacts: ArtifactCard[];
  count: number;
  public_only: boolean;
  demo_private_fixtures_allowed: boolean;
}

export interface IssuesPayload extends SiteExportPayload {
  issues: IssueSummary[];
  count: number;
}

export interface GraphPayload extends SiteExportPayload {
  nodes: GraphNode[];
  edges: GraphEdge[];
  cycles: unknown[];
  missing_dependencies: unknown[];
  accepted_draft_violations: unknown[];
}

export interface GatesPayload extends SiteExportPayload {
  verdict: string;
  note: string;
  gates: unknown[];
  blocking_issues: unknown[];
  nonblocking_issues: unknown[];
  report_paths: string[];
}

export interface ContextPacksPayload extends SiteExportPayload {
  context_packs: ContextPackSummary[];
}

export interface AuthorityBoundariesPayload extends SiteExportPayload {
  website_is_authority: boolean;
  export_is_source_of_truth: boolean;
  frontend_credentials_allowed: boolean;
  skipped_is_pass: boolean;
  gate_pass_is_truth: boolean;
  verifier_pass_is_truth: boolean;
  ai_output_is_human_review: boolean;
  accepted_write_performed: boolean;
  notices: string[];
}

export interface SiteData {
  site: SitePayload;
  workspace: WorkspacePayload;
  artifacts: ArtifactsPayload;
  issues: IssuesPayload;
  graph: GraphPayload;
  gates: GatesPayload;
  context_packs: ContextPacksPayload;
  reports: SiteExportPayload;
  authority_boundaries: AuthorityBoundariesPayload;
}

const data: SiteData = {
  site: sitePayload as SitePayload,
  workspace: workspacePayload as WorkspacePayload,
  artifacts: artifactsPayload as ArtifactsPayload,
  issues: issuesPayload as IssuesPayload,
  graph: graphPayload as GraphPayload,
  gates: gatesPayload as GatesPayload,
  context_packs: contextPacksPayload as ContextPacksPayload,
  reports: reportsPayload as SiteExportPayload,
  authority_boundaries: authorityBoundariesPayload as AuthorityBoundariesPayload
};

export async function loadSiteData(): Promise<SiteData> {
  return data;
}

export function artifactById(id: string): ArtifactCard | undefined {
  return data.artifacts.artifacts.find((artifact) => artifact.id === id);
}

export function issueById(id: string): IssueSummary | undefined {
  return data.issues.issues.find((issue) => issue.id === id);
}

export function contextPackForIssue(id: string): ContextPackSummary | undefined {
  return data.context_packs.context_packs.find((pack) => pack.issue_id === id);
}

export interface ArtifactFilter {
  status?: string;
  type?: string;
  domain?: string;
}

export function filterArtifacts(
  artifacts: ArtifactCard[],
  filter: ArtifactFilter
): ArtifactCard[] {
  return artifacts.filter((artifact) => {
    const statusMatch = !filter.status || artifact.status === filter.status;
    const typeMatch = !filter.type || artifact.type === filter.type;
    const domainMatch = !filter.domain || artifact.domain.includes(filter.domain);
    return statusMatch && typeMatch && domainMatch;
  });
}

export function uniqueSorted(values: string[]): string[] {
  return [...new Set(values)].sort((left, right) => left.localeCompare(right));
}

export function artifactHref(id: string): string {
  return `/artifacts/${encodeURIComponent(id)}/`;
}

export function issueHref(id: string): string {
  return `/issues/${encodeURIComponent(id)}/`;
}

export function contextHref(issueId: string): string {
  return `/context/${encodeURIComponent(issueId)}/`;
}

export function statusExplanation(status: string): string {
  if (status === "accepted") {
    return "Accepted status must still come from repository records and promotion policy, not the website.";
  }
  if (status === "draft") {
    return "Draft means review context only; it is not accepted knowledge.";
  }
  if (status === "not_run") {
    return "Not checked: no verifier or gate pass is implied.";
  }
  if (status === "skipped") {
    return "Skipped is not pass.";
  }
  if (status === "requested") {
    return "Review requested is not human-reviewed or accepted.";
  }
  return "Website badges are display context only.";
}

export function dependenciesFor(id: string, edges: GraphEdge[]): string[] {
  return uniqueSorted(
    edges.filter((edge) => edge.source_id === id).map((edge) => edge.target_id)
  );
}

export function dependentsFor(id: string, edges: GraphEdge[]): string[] {
  return uniqueSorted(
    edges.filter((edge) => edge.target_id === id).map((edge) => edge.source_id)
  );
}

export function graphLayoutMode(nodeCount: number): GraphLayoutMode {
  if (nodeCount === 0) {
    return "empty";
  }
  if (nodeCount === 2) {
    return "pair";
  }
  return "list";
}

export function shouldDrawGraphConnector(
  nodeCount: number,
  edgeCount: number
): boolean {
  return graphLayoutMode(nodeCount) === "pair" && edgeCount > 0;
}

export function gateVerdictExplanation(gates: GatesPayload): string {
  if (gates.verdict === "not_run") {
    return "Gate was not run in this static export; no pass is implied.";
  }
  if (gates.verdict === "pass") {
    return "Gate pass may unblock review workflow, but it does not accept artifacts or prove truth.";
  }
  if (gates.verdict === "fail" || gates.verdict === "error") {
    return "Gate result blocks review until the reported issues are resolved.";
  }
  return "Gate output is workflow context only, not accepted authority.";
}

export function statusTone(status: string): "neutral" | "warning" | "good" {
  if (status === "accepted") {
    return "good";
  }
  if (status === "draft" || status === "not_run" || status === "requested") {
    return "warning";
  }
  return "neutral";
}
