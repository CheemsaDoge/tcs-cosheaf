import { describe, expect, it } from "vitest";

import config from "../astro.config.mjs";

describe("Astro static output", () => {
  it("inlines stylesheets so static HTML keeps its UI when opened directly", () => {
    expect(config.output).toBe("static");
    expect(config.build?.inlineStylesheets).toBe("always");
  });
});
