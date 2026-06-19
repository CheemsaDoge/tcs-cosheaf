import { describe, expect, it } from "vitest";

import {
  ARTIFACT_METADATA_ENDPOINTS,
  ARTIFACT_METADATA_LABELS,
  buildEvidencePayload,
  buildSourcePayload
} from "../src/lib/artifactMetadataWorkbench";

describe("artifact metadata workbench helpers", () => {
  it("uses the exact B2.5.2 source and evidence endpoints", () => {
    expect(ARTIFACT_METADATA_ENDPOINTS.previewSource("claim.fixture.web")).toBe(
      "/api/artifacts/claim.fixture.web/preview-source"
    );
    expect(ARTIFACT_METADATA_ENDPOINTS.source("claim.fixture.web")).toBe(
      "/api/artifacts/claim.fixture.web/source"
    );
    expect(ARTIFACT_METADATA_ENDPOINTS.previewEvidence("claim.fixture.web")).toBe(
      "/api/artifacts/claim.fixture.web/preview-evidence"
    );
    expect(ARTIFACT_METADATA_ENDPOINTS.evidence("claim.fixture.web")).toBe(
      "/api/artifacts/claim.fixture.web/evidence"
    );
  });

  it("keeps labels switchable and avoids accepted-authority wording", () => {
    for (const value of Object.values(ARTIFACT_METADATA_LABELS)) {
      expect(value.en).not.toContain(" / ");
      expect(value.zh).not.toContain(" / ");
      expect(`${value.en} ${value.zh}`).not.toMatch(/accepted authority/i);
    }
  });

  it("builds explicit source metadata payloads", () => {
    expect(
      buildSourcePayload({
        kind: "paper",
        title: "A graph paper",
        authors: "Ada, Grace",
        year: "2026",
        doi: "10.0000/example",
        arxiv: "",
        url: "",
        theoremNumber: "Theorem 1",
        page: "12",
        notes: "Used for the statement only."
      })
    ).toEqual({
      kind: "paper",
      title: "A graph paper",
      authors: ["Ada", "Grace"],
      year: 2026,
      doi: "10.0000/example",
      arxiv: "",
      url: "",
      theorem_number: "Theorem 1",
      page: "12",
      notes: "Used for the statement only."
    });
  });

  it("builds evidence payloads with confirm only when explicit", () => {
    expect(
      buildEvidencePayload(
        {
          kind: "python_checker",
          path: "docs/checker-output.md",
          summary: "Checker output for review."
        },
        { confirm: true }
      )
    ).toEqual({
      kind: "python_checker",
      path: "docs/checker-output.md",
      summary: "Checker output for review.",
      confirm: true
    });
  });
});
