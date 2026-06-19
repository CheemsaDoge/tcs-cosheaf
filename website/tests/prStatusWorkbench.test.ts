import { describe, expect, it } from "vitest";

import {
  PR_STATUS_ENDPOINT,
  PR_STATUS_LABELS,
  buildPrStatusUrl,
  checklistSummary,
  githubReviewIsCosheafAuthority,
  hasPrSelector,
  statusTone,
  visibleCommentCount
} from "../src/lib/prStatusWorkbench";

describe("PR status workbench helpers", () => {
  const isLocalizedText = (
    value: unknown
  ): value is { en: string; zh: string } =>
    typeof value === "object" &&
    value !== null &&
    "en" in value &&
    "zh" in value;

  it("uses the read-only PR status endpoint", () => {
    expect(PR_STATUS_ENDPOINT).toBe("/api/forge/pr-status");
    expect(
      buildPrStatusUrl("http://127.0.0.1:8765", {
        number: " 570 ",
        base: " main ",
        head: " web-pr-review-status "
      }).toString()
    ).toBe(
      "http://127.0.0.1:8765/api/forge/pr-status?number=570&base=main&head=web-pr-review-status"
    );
  });

  it("keeps labels switchable instead of inline bilingual", () => {
    for (const value of Object.values(PR_STATUS_LABELS)) {
      expect(isLocalizedText(value)).toBe(true);
      expect(value.en).not.toContain(" / ");
      expect(value.zh).not.toContain(" / ");
    }
  });

  it("requires either a PR number or a head branch", () => {
    expect(hasPrSelector({})).toBe(false);
    expect(hasPrSelector({ number: "570" })).toBe(true);
    expect(hasPrSelector({ head: "web-pr-review-status" })).toBe(true);
  });

  it("summarizes checklist and comments without expanding everything", () => {
    expect(checklistSummary({ completed: 2, total: 5 })).toBe("2 / 5");
    expect(
      visibleCommentCount({
        pr_status: {
          review_comments: [{}, {}, {}, {}, {}]
        }
      })
    ).toBe(3);
  });

  it("never treats GitHub review as Cosheaf authority", () => {
    expect(githubReviewIsCosheafAuthority()).toBe(false);
  });

  it("maps status values to compact visual tones", () => {
    expect(statusTone("success")).toBe("good");
    expect(statusTone("failure")).toBe("bad");
    expect(statusTone("not_imported")).toBe("warning");
    expect(statusTone("2")).toBe("neutral");
  });
});
