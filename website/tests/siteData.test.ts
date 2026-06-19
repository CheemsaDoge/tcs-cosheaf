import { describe, expect, it } from "vitest";

import {
  AUTHORITY_GUIDE,
  REQUIRED_DATA_FILES,
  ROUTES,
  artifactById,
  contextPackForIssue,
  dependentsFor,
  dependenciesFor,
  filterArtifacts,
  gateVerdictExplanation,
  graphLayoutMode,
  issueById,
  loadSiteData,
  shouldDrawGraphConnector
} from "../src/lib/siteData";
import { decideRuntimeMode, runtimeModeLabel } from "../src/lib/runtimeMode";
import {
  PREVIEW_API_BASE,
  PREVIEW_AUTHORITY_WARNING,
  buildPreviewRequests
} from "../src/lib/previewActions";

describe("site data contract", () => {
  const hasChinese = (value: string) => /\p{Script=Han}/u.test(value);

  it("defines the required W2.1 routes", () => {
    expect(ROUTES.map((route) => route.path)).toEqual([
      "/",
      "/docs",
      "/demo",
      "/artifacts",
      "/issues",
      "/graph",
      "/gates",
      "/authority"
    ]);
  });

  it("loads every static export fixture file", async () => {
    const data = await loadSiteData();

    expect(REQUIRED_DATA_FILES).toEqual([
      "site.json",
      "workspace.json",
      "artifacts.json",
      "issues.json",
      "graph.json",
      "gates.json",
      "context_packs.json",
      "reports.json",
      "authority_boundaries.json"
    ]);

    expect(Object.keys(data).sort()).toEqual([
      "artifacts",
      "authority_boundaries",
      "context_packs",
      "gates",
      "graph",
      "issues",
      "reports",
      "runtime",
      "site",
      "workspace"
    ]);

    for (const payload of [
      data.site,
      data.workspace,
      data.artifacts,
      data.issues,
      data.graph,
      data.gates,
      data.context_packs,
      data.reports,
      data.authority_boundaries
    ]) {
      expect(payload.schema_version).toBe(1);
      expect(payload.authority_notice.length).toBeGreaterThan(20);
    }
  });

  it("keeps website authority boundaries explicit", async () => {
    const data = await loadSiteData();

    expect(data.authority_boundaries.website_is_authority).toBe(false);
    expect(data.authority_boundaries.frontend_credentials_allowed).toBe(false);
    expect(data.authority_boundaries.skipped_is_pass).toBe(false);
    expect(data.gates.verdict).toBe("not_run");
  });

  it("filters artifacts by status type and domain", async () => {
    const data = await loadSiteData();

    expect(
      filterArtifacts(data.artifacts.artifacts, {
        status: "draft",
        type: "definition",
        domain: "graph-theory"
      }).map((artifact) => artifact.id)
    ).toEqual(["definition.graph"]);
  });

  it("links issues to their context pack and related artifacts", async () => {
    const issue = issueById("issue.example-private-claim");
    const contextPack = contextPackForIssue("issue.example-private-claim");

    expect(issue?.related_artifacts).toEqual([
      "claim.example-private",
      "definition.graph"
    ]);
    expect(contextPack?.public_only).toBe(true);
    expect(contextPack?.related_artifacts).toEqual(issue?.related_artifacts);
  });

  it("derives dependency and reverse dependency relationships", async () => {
    const data = await loadSiteData();

    expect(dependenciesFor("claim.example-private", data.graph.edges)).toEqual([
      "definition.graph"
    ]);
    expect(dependentsFor("definition.graph", data.graph.edges)).toEqual([
      "claim.example-private"
    ]);
  });

  it("chooses graph layouts that do not overlap multi-node exports", () => {
    expect(graphLayoutMode(0)).toBe("empty");
    expect(graphLayoutMode(1)).toBe("list");
    expect(graphLayoutMode(2)).toBe("pair");
    expect(graphLayoutMode(3)).toBe("list");

    expect(shouldDrawGraphConnector(2, 1)).toBe(true);
    expect(shouldDrawGraphConnector(2, 0)).toBe(false);
    expect(shouldDrawGraphConnector(3, 2)).toBe(false);
  });

  it("explains gate verdicts without turning pass into accepted truth", async () => {
    const data = await loadSiteData();

    expect(gateVerdictExplanation(data.gates)).toContain("not run");
    expect(gateVerdictExplanation({ ...data.gates, verdict: "pass" })).toContain(
      "does not accept"
    );
  });

  it("covers the authority-boundary guide without overclaiming", () => {
    expect(AUTHORITY_GUIDE.map((entry) => entry.title)).toEqual([
      "What Cosheaf is / Cosheaf 是什么",
      "What Cosheaf is not / Cosheaf 不是什么",
      "Why gate pass is not truth / 为什么门禁通过不等于真理",
      "Why AI output is review context / 为什么 AI 输出只是审阅上下文",
      "Why skipped verifier is not pass / 为什么 skipped 不是 pass",
      "How public and private KB roots work / 公开与私有 KB 根如何工作",
      "How a result becomes accepted / 结果如何成为 accepted"
    ]);

    const guideText = AUTHORITY_GUIDE.map((entry) => entry.body).join(" ");

    expect(guideText).not.toMatch(/automatic theorem proving/i);
    expect(guideText).not.toMatch(/automatic promotion/i);
    expect(guideText).not.toMatch(/production ready/i);
  });

  it("keeps primary user-facing website chrome bilingual", () => {
    for (const route of ROUTES) {
      expect(route.label).toContain(" / ");
      expect(hasChinese(route.label)).toBe(true);
    }

    for (const entry of AUTHORITY_GUIDE) {
      expect(entry.title).toContain(" / ");
      expect(hasChinese(entry.title)).toBe(true);
      expect(hasChinese(entry.body)).toBe(true);
    }

    expect(PREVIEW_AUTHORITY_WARNING).toContain(" / ");
    expect(hasChinese(PREVIEW_AUTHORITY_WARNING)).toBe(true);
  });

  it("builds preview-only action requests without write endpoints or tokens", async () => {
    const data = await loadSiteData();
    const requests = buildPreviewRequests(data, {
      base: "main",
      head: "website-preview-actions"
    });

    expect(PREVIEW_API_BASE).toBe("http://127.0.0.1:8765");
    expect(PREVIEW_AUTHORITY_WARNING).toContain("dry-run");
    expect(requests.map((request) => request.id)).toEqual([
      "local-issue",
      "github-issue",
      "github-pr",
      "review-packet"
    ]);
    expect(requests.map((request) => request.endpoint)).toEqual([
      "/api/forge/local-issues/preview",
      "/api/forge/issues/preview",
      "/api/forge/prs/preview",
      "/api/forge/review-packets/preview"
    ]);
    expect(requests.map((request) => request.label)).toEqual([
      "Local issue / 本地议题",
      "GitHub issue / GitHub 议题",
      "Pull request / 拉取请求",
      "Review packet / 审阅包"
    ]);

    for (const request of requests) {
      expect(request.method).toBe("POST");
      expect(JSON.stringify(request.payload)).not.toMatch(/token|confirm|create/i);
    }
  });

  it("chooses runtime mode with bilingual labels", () => {
    expect(decideRuntimeMode({ dev: true, mode: "auto" }).mode).toBe(
      "live-local"
    );
    expect(decideRuntimeMode({ dev: false, mode: "auto" }).mode).toBe(
      "static-demo"
    );
    expect(decideRuntimeMode({ dev: false, mode: "hosted" }).mode).toBe(
      "hosted-workspace"
    );
    expect(runtimeModeLabel("live-local")).toBe(
      "Live local workspace mode / 本地实时工作区模式"
    );
  });

  it("loads live backend data all at once when live mode is available", async () => {
    const calls: string[] = [];
    const payloads: Record<string, unknown> = {
      "/api/workspace/live": {
        schema_version: 1,
        kind: "workspace_live",
        source_of_truth: "repository",
        authority_notice: "display only",
        workspace: {
          name: "live-workspace",
          mode: "legacy",
          kb_roots: [
            { name: "framework", path: "kb", readonly: false, priority: 0 }
          ],
          repo_root: "H:/repo"
        }
      },
      "/api/status": {
        schema_version: 1,
        kind: "repository_status",
        source_of_truth: "repository",
        authority_notice: "display only",
        status: "ok",
        validation: { ok: true, checked_count: 2, failures: [] }
      },
      "/api/artifacts/live": {
        schema_version: 1,
        kind: "artifacts_live",
        source_of_truth: "repository",
        authority_notice: "display only",
        count: 1,
        artifacts: [
          {
            id: "definition.live",
            type: "definition",
            title: "Live definition",
            status: "accepted",
            statement: "Live definition statement.",
            domain: ["graph-theory"],
            tags: ["live"],
            depends_on: [],
            review: { state: "accepted" },
            risk: { level: "low" },
            kb_root: "framework",
            kb_root_readonly: false,
            path: "kb/accepted/definitions/live.yaml"
          },
          {
            id: "claim.live",
            type: "claim",
            title: "Live claim",
            status: "draft",
            statement: "Live statement.",
            domain: ["graph-theory"],
            tags: ["live"],
            depends_on: ["definition.live"],
            review: { state: "requested" },
            risk: { level: "low" },
            kb_root: "framework",
            kb_root_readonly: false,
            path: "kb/draft/claims/live.yaml"
          }
        ]
      },
      "/api/issues/live": {
        schema_version: 1,
        kind: "issues_live",
        source_of_truth: "repository",
        authority_notice: "display only",
        count: 1,
        issues: [
          {
            id: "issue.live",
            type: "issue",
            title: "Live issue",
            status: "open",
            scope: "private",
            severity: "medium",
            summary: "Live issue summary.",
            labels: ["live"],
            related_artifacts: ["claim.live"],
            related_sources: []
          }
        ]
      },
      "/api/gates/latest": {
        schema_version: 1,
        kind: "gate_latest",
        source_of_truth: "repository",
        authority_notice: "display only",
        gate_report: {
          exists: true,
          path: ".cosheaf/reports/live-gate-report.json",
          verdict: "pass",
          report: {
            verdict: "pass",
            gates: [{ id: "G1", status: "pass" }],
            blocking_issues: [],
            nonblocking_issues: [],
            summary: { records_checked: 2 }
          }
        }
      }
    };
    const fetcher = async (url: string | URL): Promise<Response> => {
      const pathname = new URL(url.toString()).pathname;
      calls.push(pathname);
      return new Response(JSON.stringify(payloads[pathname]), { status: 200 });
    };

    const data = await loadSiteData({
      env: { dev: true, mode: "live", apiBase: "http://127.0.0.1:8765" },
      fetcher
    });

    expect(calls).toEqual([
      "/api/workspace/live",
      "/api/status",
      "/api/artifacts/live",
      "/api/issues/live",
      "/api/gates/latest"
    ]);
    expect(data.runtime.mode).toBe("live-local");
    expect(data.runtime.fallback).toBe(false);
    expect(data.workspace.workspace_name).toBe("live-workspace");
    expect(data.artifacts.artifacts.map((artifact) => artifact.id)).toEqual([
      "definition.live",
      "claim.live"
    ]);
    expect(data.graph.edges).toEqual([
      { source_id: "claim.live", target_id: "definition.live" }
    ]);
    expect(data.context_packs.context_packs[0].issue_id).toBe("issue.live");
    expect(data.gates.verdict).toBe("pass");
    expect(artifactById("claim.live", data)?.title).toBe("Live claim");
  });

  it("falls back entirely to fixtures when any live endpoint is unavailable", async () => {
    const data = await loadSiteData({
      env: { dev: true, mode: "live", apiBase: "http://127.0.0.1:8765" },
      fetcher: async () => {
        throw new Error("backend offline");
      }
    });

    expect(data.runtime.mode).toBe("static-demo");
    expect(data.runtime.fallback).toBe(true);
    expect(data.runtime.fallback_reason).toContain("backend offline");
    expect(data.artifacts.artifacts.map((artifact) => artifact.id)).toContain(
      "claim.example-private"
    );
    expect(artifactById("claim.live", data)).toBeUndefined();
  });
});
