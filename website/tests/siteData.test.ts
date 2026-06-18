import { describe, expect, it } from "vitest";

import {
  REQUIRED_DATA_FILES,
  ROUTES,
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
});
