// @vitest-environment node
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";

function read(path: string): string {
  return readFileSync(path, "utf8");
}

describe("Markdown and math surface wiring", () => {
  it("uses the shared renderer on formula-bearing display surfaces", () => {
    const expectedUses = [
      ["src/pages/artifacts.astro", "<MarkdownRenderer content={artifact.summary}"],
      ["src/pages/issues.astro", "<MarkdownRenderer content={issue.summary.split"],
      ["src/pages/issues/[id].astro", "<MarkdownRenderer content={issue.summary}"],
      ["src/pages/context/[issueId].astro", "<MarkdownRenderer content={artifact.summary}"],
      ["src/pages/gates.astro", "<MarkdownRenderer content={data.gates.note}"],
      ["src/pages/demo.astro", "<MarkdownRenderer content={issue.summary.split"],
      ["src/pages/index.astro", "<MarkdownRenderer content={issue.title} inline"],
      ["src/pages/index.astro", "<MarkdownRenderer content={artifact.title} inline"],
      ["src/pages/graph.astro", "<MarkdownRenderer content={node.title} inline"]
    ];

    for (const [path, marker] of expectedUses) {
      expect(read(path)).toContain(marker);
    }
  });

  it("shows compact Markdown and LaTeX hints near editable textareas", () => {
    expect(existsSync("src/components/MarkdownMathHint.astro")).toBe(true);
    expect(read("src/components/MarkdownMathHint.astro")).toContain(
      "data-markdown-math-feedback"
    );

    const expectedHintFiles = [
      "src/pages/artifacts/create.astro",
      "src/pages/artifacts/[id]/edit.astro",
      "src/pages/artifacts/[id]/sources.astro",
      "src/pages/artifacts/[id]/evidence.astro",
      "src/pages/artifacts/[id]/review-decision.astro",
      "src/pages/issues/create.astro",
      "src/pages/issues/[id].astro",
      "src/pages/issues/[id]/edit.astro",
      "src/components/ConfirmationModal.astro"
    ];

    for (const path of expectedHintFiles) {
      expect(read(path)).toContain("<MarkdownMathHint");
    }
  });

  it("checks formula delimiter mistakes when previewing editable text", () => {
    const layout = read("src/layouts/BaseLayout.astro");

    expect(layout).toContain("data-markdown-math-feedback");
    expect(layout).toContain("validateMarkdownMathInput");
    expect(layout).toContain("[data-preview]");
    expect(layout).toContain("unmatched $");
  });
});
