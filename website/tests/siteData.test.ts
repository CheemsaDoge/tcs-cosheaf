import { describe, expect, it } from "vitest";

import {
  AUTHORITY_GUIDE,
  REQUIRED_DATA_FILES,
  ROUTES,
  contextPackForIssue,
  dependentsFor,
  dependenciesFor,
  filterArtifacts,
  gateVerdictExplanation,
  issueById,
  loadSiteData
} from "../src/lib/siteData";

describe("site data contract", () => {
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
      "site",
      "workspace"
    ]);

    for (const payload of Object.values(data)) {
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

  it("explains gate verdicts without turning pass into accepted truth", async () => {
    const data = await loadSiteData();

    expect(gateVerdictExplanation(data.gates)).toContain("not run");
    expect(gateVerdictExplanation({ ...data.gates, verdict: "pass" })).toContain(
      "does not accept"
    );
  });

  it("covers the authority-boundary guide without overclaiming", () => {
    expect(AUTHORITY_GUIDE.map((entry) => entry.title)).toEqual([
      "What Cosheaf is",
      "What Cosheaf is not",
      "Why gate pass is not truth",
      "Why AI output is review context",
      "Why skipped verifier is not pass",
      "How public and private KB roots work",
      "How a result becomes accepted"
    ]);

    const guideText = AUTHORITY_GUIDE.map((entry) => entry.body).join(" ");

    expect(guideText).not.toMatch(/automatic theorem proving/i);
    expect(guideText).not.toMatch(/automatic promotion/i);
    expect(guideText).not.toMatch(/production ready/i);
  });
});
