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
  status: string;
  scope: string;
  severity: string;
  summary: string;
  labels: string[];
  related_artifacts: string[];
  demo_fixture: boolean;
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
  context_packs: SiteExportPayload;
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
  context_packs: contextPacksPayload as SiteExportPayload,
  reports: reportsPayload as SiteExportPayload,
  authority_boundaries: authorityBoundariesPayload as AuthorityBoundariesPayload
};

export async function loadSiteData(): Promise<SiteData> {
  return data;
}

export function artifactById(id: string): ArtifactCard | undefined {
  return data.artifacts.artifacts.find((artifact) => artifact.id === id);
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
