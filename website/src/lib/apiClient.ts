import type {
  ArtifactCard,
  ArtifactsPayload,
  ContextPacksPayload,
  GatesPayload,
  GraphPayload,
  IssueSummary,
  IssuesPayload,
  SiteData,
  SitePayload,
  WorkspacePayload
} from "./siteData";
import type { RuntimeMetadata } from "./runtimeMode";

export type FetchLike = (
  input: string | URL,
  init?: RequestInit
) => Promise<Response>;

export interface FetchLiveSiteDataOptions {
  apiBase: string;
  fetcher?: FetchLike;
  fixtureData: SiteData;
  runtime: RuntimeMetadata;
  timeoutMs?: number;
}

interface LivePayload {
  authority_notice?: string;
  source_of_truth?: string;
}

export async function fetchLiveSiteData(
  options: FetchLiveSiteDataOptions
): Promise<SiteData> {
  const [workspace, status, artifacts, issues, gates] = await Promise.all([
    fetchJson(options, "/api/workspace/live"),
    fetchJson(options, "/api/status"),
    fetchJson(options, "/api/artifacts/live"),
    fetchJson(options, "/api/issues/live"),
    fetchJson(options, "/api/gates/latest")
  ]);

  return mapLiveSiteData({
    fixtureData: options.fixtureData,
    runtime: options.runtime,
    workspace,
    status,
    artifacts,
    issues,
    gates
  });
}

async function fetchJson(
  options: FetchLiveSiteDataOptions,
  endpoint: string
): Promise<Record<string, unknown>> {
  const fetcher = options.fetcher ?? globalThis.fetch;
  if (!fetcher) {
    throw new Error("fetch is not available");
  }
  const controller =
    typeof AbortController !== "undefined" ? new AbortController() : undefined;
  const timeout = controller
    ? globalThis.setTimeout(() => controller.abort(), options.timeoutMs ?? 5000)
    : undefined;
  try {
    const response = await fetcher(new URL(endpoint, options.apiBase), {
      signal: controller?.signal
    });
    if (!response.ok) {
      throw new Error(`${endpoint} returned HTTP ${response.status}`);
    }
    const payload = await response.json();
    if (!isRecord(payload)) {
      throw new Error(`${endpoint} did not return a JSON object`);
    }
    return payload;
  } finally {
    if (timeout !== undefined) {
      globalThis.clearTimeout(timeout);
    }
  }
}

function mapLiveSiteData(input: {
  fixtureData: SiteData;
  runtime: RuntimeMetadata;
  workspace: Record<string, unknown>;
  status: Record<string, unknown>;
  artifacts: Record<string, unknown>;
  issues: Record<string, unknown>;
  gates: Record<string, unknown>;
}): SiteData {
  const artifacts = mapArtifacts(input.fixtureData, input.artifacts);
  const issues = mapIssues(input.fixtureData, input.issues);
  const graph = mapGraph(input.fixtureData, artifacts.artifacts);
  return {
    site: mapSite(input.fixtureData.site),
    workspace: mapWorkspace(input.fixtureData, input.workspace),
    artifacts,
    issues,
    graph,
    gates: mapGates(input.fixtureData, input.gates),
    context_packs: mapContextPacks(input.fixtureData, issues.issues),
    reports: input.fixtureData.reports,
    authority_boundaries: input.fixtureData.authority_boundaries,
    runtime: input.runtime
  };
}

function mapSite(site: SitePayload): SitePayload {
  return {
    ...site,
    demo: false,
    public_only: false,
    source_of_truth: "repository"
  };
}

function mapWorkspace(
  fixtureData: SiteData,
  payload: Record<string, unknown>
): WorkspacePayload {
  const workspace = asRecord(payload.workspace);
  const roots = arrayOfRecords(workspace.kb_roots);
  return {
    ...fixtureData.workspace,
    authority_notice: authorityNotice(payload, fixtureData.workspace),
    workspace_name: text(workspace.name, fixtureData.workspace.workspace_name),
    mode: text(workspace.mode, fixtureData.workspace.mode),
    public_only: false,
    kb_roots: roots.map((root) => ({
      name: text(root.name, "workspace"),
      path: text(root.path, "."),
      readonly: Boolean(root.readonly),
      priority: numberValue(root.priority, 0),
      demo_private_fixtures_allowed: false
    }))
  };
}

function mapArtifacts(
  fixtureData: SiteData,
  payload: Record<string, unknown>
): ArtifactsPayload {
  const artifacts = arrayOfRecords(payload.artifacts).map((artifact) =>
    artifactCard(artifact)
  );
  return {
    ...fixtureData.artifacts,
    authority_notice: authorityNotice(payload, fixtureData.artifacts),
    artifacts,
    count: artifacts.length,
    public_only: false,
    demo_private_fixtures_allowed: false
  };
}

function artifactCard(artifact: Record<string, unknown>): ArtifactCard {
  return {
    id: text(artifact.id, ""),
    title: text(artifact.title, text(artifact.id, "Untitled artifact")),
    type: text(artifact.type, "artifact"),
    status: text(artifact.status, "draft"),
    root_scope: text(artifact.kb_root, "workspace"),
    summary: text(artifact.summary, text(artifact.statement, "")),
    statement:
      typeof artifact.statement === "string" ? artifact.statement : undefined,
    domain: stringArray(artifact.domain),
    authors: stringArray(artifact.authors),
    tags: stringArray(artifact.tags),
    depends_on: stringArray(artifact.depends_on),
    supersedes: stringArray(artifact.supersedes),
    demo_fixture: false,
    verifier_state: "not_run",
    review_state: text(asRecord(artifact.review).state, "requested"),
    risk_flags: riskFlags(artifact),
    sources: sourceLabels(artifact.sources),
    path: text(artifact.path, "")
  };
}

function mapIssues(
  fixtureData: SiteData,
  payload: Record<string, unknown>
): IssuesPayload {
  const issues = arrayOfRecords(payload.issues).map((issue) => issueSummary(issue));
  return {
    ...fixtureData.issues,
    authority_notice: authorityNotice(payload, fixtureData.issues),
    issues,
    count: issues.length
  };
}

function issueSummary(issue: Record<string, unknown>): IssueSummary {
  return {
    id: text(issue.id, ""),
    title: text(issue.title, text(issue.id, "Untitled issue")),
    type: text(issue.type, "issue"),
    status: text(issue.status, "open"),
    scope: text(issue.scope, "private"),
    severity: text(issue.severity, "medium"),
    summary: text(issue.summary, text(issue.description, "")),
    authors: stringArray(issue.authors),
    labels: stringArray(issue.labels),
    related_artifacts: stringArray(issue.related_artifacts),
    related_sources: stringArray(issue.related_sources),
    demo_fixture: false
  };
}

function mapGraph(fixtureData: SiteData, artifacts: ArtifactCard[]): GraphPayload {
  const nodes = artifacts.map((artifact) => ({
    artifact_id: artifact.id,
    artifact_type: artifact.type,
    title: artifact.title,
    status: artifact.status,
    domain: artifact.domain,
    path: artifact.path
  }));
  const knownIds = new Set(artifacts.map((artifact) => artifact.id));
  const edges = artifacts.flatMap((artifact) =>
    artifact.depends_on
      .filter((target) => !target.startsWith("external:") && knownIds.has(target))
      .map((target) => ({ source_id: artifact.id, target_id: target }))
  );
  return {
    ...fixtureData.graph,
    nodes,
    edges,
    cycles: [],
    missing_dependencies: [],
    accepted_draft_violations: []
  };
}

function mapContextPacks(
  fixtureData: SiteData,
  issues: IssueSummary[]
): ContextPacksPayload {
  return {
    ...fixtureData.context_packs,
    context_packs: issues.map((issue) => ({
      issue_id: issue.id,
      card_count: issue.related_artifacts.length,
      public_only: false,
      private_context_included: false,
      demo_private_context_included: false,
      related_artifacts: issue.related_artifacts
    }))
  };
}

function mapGates(
  fixtureData: SiteData,
  payload: Record<string, unknown>
): GatesPayload {
  const gateReport = asRecord(payload.gate_report);
  const report = asRecord(gateReport.report);
  const reportPath = text(gateReport.path, "");
  const verdict = text(gateReport.verdict, text(report.verdict, "not_run"));
  return {
    ...fixtureData.gates,
    authority_notice: authorityNotice(payload, fixtureData.gates),
    verdict,
    note: reportPath
      ? `Live gate report read from ${reportPath}.`
      : "No live gate report exists under .cosheaf/reports.",
    gates: arrayValue(report.gates),
    blocking_issues: arrayValue(report.blocking_issues),
    nonblocking_issues: arrayValue(report.nonblocking_issues),
    report_paths: reportPath ? [reportPath] : []
  };
}

function authorityNotice(
  payload: LivePayload,
  fallback: { authority_notice: string }
): string {
  return text(payload.authority_notice, fallback.authority_notice);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asRecord(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function arrayOfRecords(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function arrayValue(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function text(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function numberValue(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function riskFlags(artifact: Record<string, unknown>): string[] {
  const risk = asRecord(artifact.risk);
  const level = text(risk.level, "");
  return level ? [`risk:${level}`] : [];
}

function sourceLabels(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((source) => {
        if (typeof source === "string") {
          return source;
        }
        const record = asRecord(source);
        return text(record.title, text(record.url, text(record.doi, "")));
      }).filter((source) => source.length > 0)
    : [];
}
