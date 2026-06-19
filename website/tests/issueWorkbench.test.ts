import { describe, expect, it } from "vitest";

import {
  ISSUE_ACTION_ENDPOINTS,
  ISSUE_WORKBENCH_LABELS,
  buildIssueActionPayload,
  parseDelimitedList
} from "../src/lib/issueWorkbench";

describe("issue workbench helpers", () => {
  const hasChinese = (value: string) => /\p{Script=Han}/u.test(value);
  const isLocalizedText = (
    value: unknown
  ): value is { en: string; zh: string } =>
    typeof value === "object" &&
    value !== null &&
    "en" in value &&
    "zh" in value;

  it("uses the exact B2.3.1 issue action endpoints", () => {
    expect(ISSUE_ACTION_ENDPOINTS.previewCreate).toBe("/api/issues/preview-create");
    expect(ISSUE_ACTION_ENDPOINTS.create).toBe("/api/issues/create");
    expect(ISSUE_ACTION_ENDPOINTS.previewUpdate("issue.fixture.web")).toBe(
      "/api/issues/issue.fixture.web/preview-update"
    );
    expect(ISSUE_ACTION_ENDPOINTS.update("issue.fixture.web")).toBe(
      "/api/issues/issue.fixture.web/update"
    );
    expect(ISSUE_ACTION_ENDPOINTS.previewClose("issue.fixture.web")).toBe(
      "/api/issues/issue.fixture.web/preview-close"
    );
    expect(ISSUE_ACTION_ENDPOINTS.close("issue.fixture.web")).toBe(
      "/api/issues/issue.fixture.web/close"
    );
  });

  it("keeps workbench labels switchable instead of inline bilingual", () => {
    for (const value of Object.values(ISSUE_WORKBENCH_LABELS)) {
      expect(isLocalizedText(value)).toBe(true);
      expect(value.en).not.toContain(" / ");
      expect(value.zh).not.toContain(" / ");
      expect(hasChinese(value.zh)).toBe(true);
      expect(hasChinese(value.en)).toBe(false);
    }
  });

  it("parses form text into stable arrays without token-shaped fields", () => {
    expect(parseDelimitedList("alpha, beta\nalpha\n gamma ")).toEqual([
      "alpha",
      "beta",
      "gamma"
    ]);

    const payload = buildIssueActionPayload({
      issueId: " issue.fixture.web ",
      title: " Web issue ",
      summary: " Create from browser ",
      scope: "public",
      labels: "web, issue-workbench",
      relatedArtifacts: "claim.fixture.web\nclaim.fixture.extra",
      relatedSources: "",
      authors: "human, reviewer"
    });

    expect(payload).toEqual({
      issue_id: "issue.fixture.web",
      title: "Web issue",
      summary: "Create from browser",
      scope: "public",
      labels: ["web", "issue-workbench"],
      related_artifacts: ["claim.fixture.web", "claim.fixture.extra"],
      related_sources: [],
      authors: ["human", "reviewer"]
    });
    expect(JSON.stringify(payload)).not.toMatch(/token|password|secret|confirm/i);
  });

  it("adds confirm only for explicit confirm submissions", () => {
    const payload = buildIssueActionPayload(
      {
        issueId: "issue.fixture.web",
        title: "Web issue",
        summary: "",
        scope: "private",
        labels: "",
        relatedArtifacts: "",
        relatedSources: "",
        authors: ""
      },
      { confirm: true }
    );

    expect(payload.confirm).toBe(true);
  });
});
