import { describe, expect, it } from "vitest";

import {
  HUMAN_REVIEW_DECISION_OPTIONS,
  REVIEW_DECISION_ENDPOINTS,
  REVIEW_DECISION_LABELS,
  buildReviewDecisionPayload
} from "../src/lib/reviewDecisionWorkbench";

describe("review decision workbench helpers", () => {
  const hasChinese = (value: string) => /\p{Script=Han}/u.test(value);

  it("uses the exact B2.6.2 review decision endpoints", () => {
    expect(REVIEW_DECISION_ENDPOINTS.preview).toBe(
      "/api/reviews/decisions/preview"
    );
    expect(REVIEW_DECISION_ENDPOINTS.create).toBe(
      "/api/reviews/decisions/create"
    );
  });

  it("exposes all required human review decisions", () => {
    expect(HUMAN_REVIEW_DECISION_OPTIONS.map((option) => option.value)).toEqual([
      "accept_for_private_use",
      "accept_for_public_candidate",
      "changes_requested",
      "keep_draft",
      "refute_candidate",
      "mark_obsolete"
    ]);
    for (const option of HUMAN_REVIEW_DECISION_OPTIONS) {
      expect(hasChinese(option.label.zh)).toBe(true);
      expect(hasChinese(option.label.en)).toBe(false);
    }
  });

  it("builds explicit human review decision payloads", () => {
    expect(
      buildReviewDecisionPayload(
        {
          artifactId: " claim.fixture.review-decision ",
          reviewer: " Ada Reviewer ",
          decision: "accept_for_private_use",
          reviewNotes: " Checked by hand. ",
          scope: " private ",
          limitations: " Fixture only. ",
          dependenciesChecked: true,
          sourcesChecked: true,
          evidenceChecked: true,
          gateStateAcknowledged: true,
          explicitHumanConfirmation: true
        },
        { confirm: true }
      )
    ).toEqual({
      artifact_id: "claim.fixture.review-decision",
      reviewer: "Ada Reviewer",
      decision: "accept_for_private_use",
      review_notes: "Checked by hand.",
      scope: "private",
      limitations: "Fixture only.",
      dependencies_checked: true,
      sources_checked: true,
      evidence_checked: true,
      gate_state_acknowledged: true,
      explicit_human_confirmation: true,
      confirm: true
    });
  });

  it("keeps labels switchable and rejects AI-as-reviewer wording", () => {
    for (const value of Object.values(REVIEW_DECISION_LABELS)) {
      expect(value.en).not.toContain(" / ");
      expect(value.zh).not.toContain(" / ");
      expect(hasChinese(value.zh)).toBe(true);
      expect(hasChinese(value.en)).toBe(false);
    }
    expect(REVIEW_DECISION_LABELS.authorityNotice.en).toContain(
      "AI/Codex cannot be recorded as reviewer"
    );
    expect(REVIEW_DECISION_LABELS.authorityNotice.zh).toContain("AI/Codex");
  });
});
