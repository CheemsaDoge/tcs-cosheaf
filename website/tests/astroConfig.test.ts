// @vitest-environment node
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";

import config from "../astro.config.mjs";

describe("Astro static output", () => {
  it("inlines stylesheets so static HTML keeps its UI when opened directly", () => {
    expect(config.output).toBe("static");
    expect(config.build?.inlineStylesheets).toBe("always");
  });

  it("does not rewrite asset paths away from HTTP static-server defaults", () => {
    expect(config.vite?.base).toBeUndefined();
    expect(config.build?.assetsPrefix).toBeUndefined();
  });

  it("inlines the global stylesheet through the base layout", () => {
    const layout = readFileSync("src/layouts/BaseLayout.astro", "utf8");

    expect(layout).toContain("../styles/global.css?raw");
    expect(layout).toContain("<style is:inline set:html={globalStyles}>");
    expect(layout).not.toContain('import "../styles/global.css"');
  });

  it("keeps static list pagination scripts inline for direct file previews", () => {
    const layout = readFileSync("src/layouts/BaseLayout.astro", "utf8");
    const graphPage = readFileSync("src/pages/graph.astro", "utf8");

    expect(layout.match(/<script is:inline>/g)).toHaveLength(2);
    expect(layout).toContain("const initPagination");
    expect(layout).toContain("artifactRows");
    expect(graphPage).not.toContain("<script is:inline>");
  });

  it("shows configured local actor in the runtime banner without auth claims", () => {
    const layout = readFileSync("src/layouts/BaseLayout.astro", "utf8");

    expect(layout).toContain("runtime.local_actor");
    expect(layout).toContain("Local actor:");
    expect(layout).toContain("本地角色：");
    expect(layout).toContain("local_actor_is_auth");
  });
});
