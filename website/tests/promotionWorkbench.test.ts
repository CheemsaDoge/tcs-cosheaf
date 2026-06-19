import { describe, expect, it } from "vitest";

import {
  PROMOTION_LABELS,
  buildPromotionPreviewPayload,
  buildPromotionConfirmPayload,
  canConfirmPromotion,
  groupPromotionReasons,
  promotionConfirmEndpoint,
  promotionPreviewEndpoint,
  promotionReadinessEndpoint,
  requiredPromotionConfirmation
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
    expect(promotionConfirmEndpoint("claim.fixture.ready")).toBe(
      "/api/artifacts/claim.fixture.ready/promotion/confirm"
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

  it("builds a confirmed promotion payload with typed human confirmation", () => {
    expect(requiredPromotionConfirmation("accepted")).toBe("PROMOTE TO ACCEPTED");
    expect(requiredPromotionConfirmation("refuted")).toBe("MARK REFUTED");
    expect(requiredPromotionConfirmation("obsolete")).toBe("MARK OBSOLETE");
    expect(
      buildPromotionConfirmPayload({
        artifactId: " claim.fixture.ready ",
        targetState: " accepted ",
        actor: " Ada Reviewer ",
        typedConfirmation: " PROMOTE TO ACCEPTED ",
        promotionJustification: " Reviewed the packet and gate output. "
      })
    ).toEqual({
      artifact_id: "claim.fixture.ready",
      target_state: "accepted",
      actor: "Ada Reviewer",
      typed_confirmation: "PROMOTE TO ACCEPTED",
      promotion_justification: "Reviewed the packet and gate output.",
      confirm: true
    });
  });

  it("enables confirm only after an unblocked preview, exact phrase, and notes", () => {
    expect(
      canConfirmPromotion({
        actor: "Ada Reviewer",
        targetState: "accepted",
        typedConfirmation: "PROMOTE TO ACCEPTED",
        promotionJustification: "Reviewed by hand.",
        promotionBlocked: false,
        previewLoaded: true
      })
    ).toBe(true);
    expect(
      canConfirmPromotion({
        actor: "Ada Reviewer",
        targetState: "accepted",
        typedConfirmation: "MARK REFUTED",
        promotionJustification: "Reviewed by hand.",
        promotionBlocked: false,
        previewLoaded: true
      })
    ).toBe(false);
    expect(
      canConfirmPromotion({
        actor: "Ada Reviewer",
        targetState: "accepted",
        typedConfirmation: "PROMOTE TO ACCEPTED",
        promotionJustification: "Reviewed by hand.",
        promotionBlocked: true,
        previewLoaded: true
      })
    ).toBe(false);
    expect(
      canConfirmPromotion({
        actor: "",
        targetState: "accepted",
        typedConfirmation: "PROMOTE TO ACCEPTED",
        promotionJustification: "Reviewed by hand.",
        promotionBlocked: false,
        previewLoaded: true
      })
    ).toBe(false);
    expect(
      canConfirmPromotion({
        actor: "Ada Reviewer",
        targetState: "accepted",
        typedConfirmation: "PROMOTE TO ACCEPTED",
        promotionJustification: " ",
        promotionBlocked: false,
        previewLoaded: true
      })
    ).toBe(false);
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
