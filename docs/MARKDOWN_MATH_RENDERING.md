# Markdown and LaTeX Math Rendering

Status: Implemented in Task B2.9.3

## Purpose

The web Workbench renders user-authored TCS text with Markdown and LaTeX math
for human reading. Repository Markdown/YAML remains the canonical source. The
rendered HTML is presentation only and never creates source metadata, human
review, verifier pass, gate pass, accepted status, or promotion authority.

## Components

- `website/src/lib/markdownMathRenderer.ts`
  - `renderMarkdownWithMath(text, options)` renders Markdown plus `$...$` and
    `$$...$$` formulas.
  - `renderMathOnly(text, options)` renders short inline text with math support
    but without Markdown block processing.
- `website/src/components/MarkdownRenderer.astro` is the shared Astro wrapper
  for display surfaces.
- `website/src/components/MarkdownMathHint.astro` is the compact editor hint
  shown near narrative textareas.

## Authoring Rules

Use math delimiters for formulas:

```markdown
Triangle graph $K_3$ has 3 vertices.

$$
\sum_{i=1}^n i = \frac{n(n+1)}{2}
$$
```

Plain `K_3` remains literal text. Escape literal dollar signs with a backslash:

```markdown
The cost is \$100.
```

## Security And Failure Behavior

- Raw HTML is refused before Markdown rendering.
- Dangerous raw HTML blocks such as `script`, `style`, `iframe`, `object`, and
  `embed` are removed.
- Final HTML is sanitized with DOMPurify.
- Markdown links are sanitized and limited to safe protocols.
- KaTeX is called with `trust: false` and `throwOnError: false`.
- Malformed formulas stay visible as escaped/error source instead of crashing
  the page.
- If Markdown rendering itself throws, the renderer falls back to escaped plain
  text.

## Surfaces

The shared renderer is used for formula-bearing artifact, issue, context, gate,
dashboard, demo, and graph-detail text surfaces. The same source text is used
in static fixture mode and live-local mode.

Textareas for artifact statements, issue summaries, source/evidence notes,
review notes, promotion justification, and issue close reasons show a compact
Markdown/LaTeX hint. A small client-side preview helper warns about unmatched
`$` or `$$` delimiters. This helper does not block writes and is not a
validator; the renderer remains responsible for safe display.

## Tests

Run the website tests with:

```bash
cd website
npm test
```

Coverage includes:

- inline and block math rendering;
- `Triangle graph $K_3$`;
- plain `Triangle graph K_3` staying literal;
- literal dollar escaping;
- raw HTML refusal and unsafe link sanitization;
- KaTeX `trust: false` behavior;
- `throwOnError: false` malformed-formula behavior;
- renderer fallback to escaped plain text; and
- source-level wiring for shared renderer surfaces and editor hints.

## Non-Goals

- No large editor framework.
- No source-file rewrite to rendered HTML.
- No client-side trusted raw HTML.
- No authority semantics change.
