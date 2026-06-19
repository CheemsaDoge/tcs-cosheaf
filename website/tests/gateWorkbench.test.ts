import { describe, expect, it } from "vitest";

import {
  CHECK_RUN_ENDPOINTS,
  CHECK_RUN_LABELS,
  summarizeCheckStatuses
} from "../src/lib/gateWorkbench";

describe("gate workbench helpers", () => {
  const isLocalizedText = (
    value: unknown
  ): value is { en: string; zh: string } =>
    typeof value === "object" &&
    value !== null &&
    "en" in value &&
    "zh" in value;

  it("uses the exact B2.4.2 check run endpoints", () => {
    expect(CHECK_RUN_ENDPOINTS.validate).toBe("/api/validate/run");
    expect(CHECK_RUN_ENDPOINTS.gate).toBe("/api/gate/run");
  });

  it("keeps gate workbench labels switchable", () => {
    for (const value of Object.values(CHECK_RUN_LABELS)) {
      expect(isLocalizedText(value)).toBe(true);
      expect(value.en).not.toContain(" / ");
      expect(value.zh).not.toContain(" / ");
    }
  });

  it("counts pass, fail, and skipped rows separately", () => {
    expect(
      summarizeCheckStatuses([
        { status: "pass" },
        { status: "fail" },
        { result: "skipped" },
        { verdict: "error" },
        { state: "unavailable" }
      ])
    ).toEqual({
      pass: 1,
      fail: 2,
      skipped: 2
    });
  });
});
