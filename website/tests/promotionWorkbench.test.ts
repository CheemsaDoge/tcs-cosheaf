import { describe, expect, it } from "vitest";

import {
  PROMOTION_LABELS,
  buildPromotionPreviewPayload,
  groupPromotionReasons,
  promotionPreviewEndpoint,
  promotionReadinessEndpoint
} from "../src/lib/promotionWorkbench";

describe("promotion workbench helpers", () => {
  const hasChinese = (value: string) => /\p{Script=Han}/u.test(value);

  it("uses the exact B2.7.1 promotion endpoints", () => {
    expect(promotionReadinessEndpoint("claim.fixture.ready")).toBe(
      "/api/artifacts/claim.fixture.ready/promotion-readiness"
    );
    expect(promotionPreviewEndpoint("claim.fixture.ready")).toBe(
      "/api/artifacts/claim.fixture.ready/promotion/preview"
    );
  });

  it("builds a minimal promotion preview payload", () => {
    expect(
      buildPromotionPreviewPayload({
        artifactId: " claim.fixture.ready ",
        targetState: " accepted "
      })
    ).toEqual({
      artifact_id: "claim.fixture.ready",
      target_state: "accepted"
    });
  });

  it("keeps bilingual labels natural and switchable", () => {
    expect(PROMOTION_LABELS.checkPromotion.en).toBe("Check promotion");
    expect(PROMOTION_LABELS.checkPromotion.zh).toBe("检查晋升");
    expect(PROMOTION_LABELS.ready.zh).toBe("可晋升");
    expect(PROMOTION_LABELS.blocked.zh).toBe("阻断");
    for (const value of Object.values(PROMOTION_LABELS)) {
      expect(value.en).not.toContain(" / ");
      expect(value.zh).not.toContain(" / ");
      expect(hasChinese(value.zh)).toBe(true);
      expect(hasChinese(value.en)).toBe(false);
    }
  });

  it("groups readiness reasons by user-facing requirement area", () => {
    const groups = groupPromotionReasons([
      {
        code: "dependency_risk",
        severity: "blocking",
        message: "dependency is not accepted"
      },
      {
        code: "missing_source_metadata",
        severity: "blocking",
        message: "source metadata is missing"
      },
      {
        code: "skipped_verifier",
        severity: "blocking",
        message: "skipped is not a pass"
      },
      {
        code: "repository_gate_blocker",
        severity: "blocking",
        message: "gate blocks promotion"
      }
    ]);

    expect(groups.map((group) => group.key)).toEqual([
      "dependencies",
      "source_metadata",
      "verifier_checks",
      "gate_checks"
    ]);
    expect(groups[2].label.en).toBe("Verifier checks");
    expect(groups[2].items[0].code).toBe("skipped_verifier");
  });
});
