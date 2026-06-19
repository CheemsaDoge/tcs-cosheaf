import { describe, expect, it } from "vitest";

import {
  REVIEW_PACKET_ENDPOINTS,
  REVIEW_PACKET_LABELS,
  buildReviewPacketPayload
} from "../src/lib/reviewPacketWorkbench";

describe("review packet workbench helpers", () => {
  const hasChinese = (value: string) => /\p{Script=Han}/u.test(value);

  it("uses the exact B2.6.1 review packet endpoints", () => {
    expect(REVIEW_PACKET_ENDPOINTS.preview).toBe("/api/reviews/packets/preview");
    expect(REVIEW_PACKET_ENDPOINTS.create).toBe("/api/reviews/packets/create");
  });

  it("builds review packet payloads without authority-changing fields", () => {
    expect(
      buildReviewPacketPayload({
        issueId: " issue.fixture.review-packet ",
        artifactId: " claim.fixture.review-packet "
      })
    ).toEqual({
      issue_id: "issue.fixture.review-packet",
      artifact_id: "claim.fixture.review-packet"
    });

    expect(
      buildReviewPacketPayload(
        {
          issueId: "issue.fixture.review-packet",
          artifactId: ""
        },
        { confirm: true }
      )
    ).toEqual({
      issue_id: "issue.fixture.review-packet",
      confirm: true
    });
  });

  it("keeps labels switchable and avoids review-complete wording", () => {
    for (const value of Object.values(REVIEW_PACKET_LABELS)) {
      expect(value.en).not.toContain(" / ");
      expect(value.zh).not.toContain(" / ");
      expect(hasChinese(value.zh)).toBe(true);
      expect(hasChinese(value.en)).toBe(false);
      expect(`${value.en} ${value.zh}`).not.toMatch(/human_reviewed/i);
      expect(`${value.en} ${value.zh}`).not.toMatch(/accepted authority/i);
    }
  });
});
