import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function source(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

describe("review UX component sources", () => {
  it("ships the B2.9.2 review components", () => {
    for (const component of [
      "ReviewChecklist.astro",
      "GateStatusBadge.astro",
      "DependencyImpact.astro",
      "DiffViewer.astro",
      "ConfirmationModal.astro",
      "PromotionReasonGroups.astro"
    ]) {
      expect(source(`src/components/${component}`).trim().length).toBeGreaterThan(0);
    }
  });

  it("wires review and promotion pages through the shared components", () => {
    const reviewPage = source("src/pages/artifacts/[id]/review-decision.astro");
    const promotionPage = source("src/pages/artifacts/[id]/promotion.astro");

    expect(reviewPage).toContain("ReviewChecklist");
    expect(reviewPage).toContain("GateStatusBadge");
    expect(promotionPage).toContain("ConfirmationModal");
    expect(promotionPage).toContain("DiffViewer");
    expect(promotionPage).toContain("DependencyImpact");
    expect(promotionPage).toContain("PromotionReasonGroups");
  });

  it("keeps promotion confirmation modal notes required before submit", () => {
    const client = source("src/lib/promotionWorkbenchClient.ts");
    const modal = source("src/components/ConfirmationModal.astro");
    const page = source("src/pages/artifacts/[id]/promotion.astro");

    expect(page).toContain("ConfirmationModal");
    expect(modal).toContain("data-confirmation-modal");
    expect(modal).toContain('name="promotionJustification"');
    expect(client).toContain("promotionJustification");
    expect(client).toContain("data-modal-confirm");
  });
});
