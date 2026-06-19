import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";

import config from "../astro.config.mjs";

describe("Astro static output", () => {
  it("inlines stylesheets so static HTML keeps its UI when opened directly", () => {
    expect(config.output).toBe("static");
    expect(config.build?.inlineStylesheets).toBe("always");
  });

  it("does not rewrite asset paths away from HTTP static-server defaults", () => {
    expect(config.build?.assetsPrefix).toBeUndefined();
  });

  it("inlines the global stylesheet through the base layout", () => {
    const layout = readFileSync("src/layouts/BaseLayout.astro", "utf8");

    expect(layout).toContain("../styles/global.css?raw");
    expect(layout).toContain("<style is:inline set:html={globalStyles}>");
    expect(layout).not.toContain('import "../styles/global.css"');
  });
});
