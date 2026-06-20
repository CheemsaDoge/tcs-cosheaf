import { describe, expect, it } from "vitest";

import {
  FORGE_ISSUE_ENDPOINTS,
  FORGE_ISSUE_LABELS,
  FORGE_PR_FLOW_ENDPOINTS,
  FORGE_PR_FLOW_LABELS,
  buildBranchCreatePayload,
  buildCommitCreatePayload,
  buildGitHubIssuePublishPayload,
  buildPrCreatePayload,
  buildPushCreatePayload,
  canCreateBranch,
  canCreatePr,
  canPushBranch,
  extractGitHubIssueUrl,
  extractPrUrl,
  isProtectedBranch
} from "../src/lib/forgeWorkbench";

describe("forge PR submit workbench helpers", () => {
  const isLocalizedText = (
    value: unknown
  ): value is { en: string; zh: string } =>
    typeof value === "object" &&
    value !== null &&
    "en" in value &&
    "zh" in value;

  it("uses the exact B2.8.1 forge flow endpoints", () => {
    expect(FORGE_PR_FLOW_ENDPOINTS).toEqual({
      branchPreview: "/api/forge/branch/preview",
      branchCreate: "/api/forge/branch/create",
      commitPreview: "/api/forge/commit/preview",
      commitCreate: "/api/forge/commit/create",
      pushPreview: "/api/forge/push/preview",
      pushCreate: "/api/forge/push/create",
      prPreview: "/api/forge/pr/preview",
      prCreate: "/api/forge/pr/create"
    });
  });

  it("uses the exact B2.3.2 GitHub issue publish endpoints", () => {
    expect(FORGE_ISSUE_ENDPOINTS).toEqual({
      preview: "/api/forge/issues/preview",
      create: "/api/forge/issues/create"
    });
  });

  it("keeps labels switchable instead of inline bilingual", () => {
    for (const value of [
      ...Object.values(FORGE_PR_FLOW_LABELS),
      ...Object.values(FORGE_ISSUE_LABELS)
    ]) {
      expect(isLocalizedText(value)).toBe(true);
      expect(value.en).not.toContain(" / ");
      expect(value.zh).not.toContain(" / ");
    }
  });

  it("blocks main and master as writable heads", () => {
    expect(isProtectedBranch("main")).toBe(true);
    expect(isProtectedBranch(" master ")).toBe(true);
    expect(isProtectedBranch("feature.web-pr")).toBe(false);

    expect(canCreateBranch({ branch: "main" })).toBe(false);
    expect(canPushBranch({ head: "master", confirm: true })).toBe(false);
    expect(canCreatePr({ base: "main", head: "main", confirm: true })).toBe(false);
  });

  it("builds confirmed branch commit push and PR payloads", () => {
    expect(buildBranchCreatePayload({ branch: "feature.web-pr" })).toEqual({
      branch: "feature.web-pr",
      confirm: true
    });
    expect(buildCommitCreatePayload({ message: "Add Forge PR flow" })).toEqual({
      message: "Add Forge PR flow",
      confirm: true
    });
    expect(buildPushCreatePayload({ head: "feature.web-pr" })).toEqual({
      head: "feature.web-pr",
      confirm: true
    });
    expect(
      buildPrCreatePayload({
        base: "main",
        head: "feature.web-pr",
        draft: true
      })
    ).toEqual({
      base: "main",
      head: "feature.web-pr",
      draft: true,
      confirm: true
    });
  });

  it("requires explicit confirmation before push or PR create", () => {
    expect(canPushBranch({ head: "feature.web-pr", confirm: false })).toBe(false);
    expect(canPushBranch({ head: "feature.web-pr", confirm: true })).toBe(true);
    expect(
      canCreatePr({ base: "main", head: "feature.web-pr", confirm: false })
    ).toBe(false);
    expect(
      canCreatePr({ base: "main", head: "feature.web-pr", confirm: true })
    ).toBe(true);
  });

  it("builds GitHub issue publish payloads without implicit confirmation", () => {
    expect(
      buildGitHubIssuePublishPayload({
        sourcePath: " issues/open/issue.fixture.yaml "
      })
    ).toEqual({ source_path: "issues/open/issue.fixture.yaml" });
    expect(
      buildGitHubIssuePublishPayload({
        sourcePath: "issues/open/issue.fixture.yaml",
        confirm: true
      })
    ).toEqual({
      source_path: "issues/open/issue.fixture.yaml",
      confirm: true
    });
  });

  it("extracts the created PR URL from action payloads", () => {
    expect(
      extractPrUrl({
        forge_action: {
          github_pr_url: "https://github.com/CheemsaDoge/tcs-cosheaf/pull/1004"
        }
      })
    ).toBe("https://github.com/CheemsaDoge/tcs-cosheaf/pull/1004");
    expect(extractPrUrl({ forge_action: {} })).toBe("");
  });

  it("extracts the created GitHub issue URL from action payloads", () => {
    expect(
      extractGitHubIssueUrl({
        forge_action: {
          github_issue_url:
            "https://github.com/CheemsaDoge/tcs-cosheaf/issues/1004"
        }
      })
    ).toBe("https://github.com/CheemsaDoge/tcs-cosheaf/issues/1004");
    expect(extractGitHubIssueUrl({ forge_action: {} })).toBe("");
  });
});
