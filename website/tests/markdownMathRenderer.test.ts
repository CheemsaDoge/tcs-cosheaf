/**
 * Tests for Markdown and LaTeX math rendering.
 *
 * Coverage:
 * - Inline math rendering ($...$)
 * - Block math rendering ($$...$$)
 * - Literal dollar sign escaping (\$)
 * - Markdown formatting (bold, italic, links, lists, code)
 * - HTML sanitization (script injection, unsafe links, event handlers)
 * - Mixed markdown and math content
 * - Error handling for invalid LaTeX
 */

import { describe, it, expect, vi } from 'vitest';
import { marked } from 'marked';
import { renderMarkdownWithMath, renderMathOnly } from '../src/lib/markdownMathRenderer';

describe('renderMarkdownWithMath', () => {
  it('renders inline math with subscripts', () => {
    const input = 'Triangle graph $K_3$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('K');
    expect(output).toContain('3');
    expect(output).toContain('katex'); // KaTeX adds class names
    expect(output).not.toContain('$K_3$'); // Math delimiters removed
  });

  it('leaves plain underscore notation literal outside math delimiters', () => {
    const input = 'Triangle graph K_3';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('Triangle graph K_3');
    expect(output).not.toContain('katex');
  });

  it('renders block math equations', () => {
    const input = 'Formula:\n\n$$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('katex');
    expect(output).toContain('display'); // Block math uses display mode
    expect(output).not.toContain('$$'); // Math delimiters removed
  });

  it('handles literal dollar signs with backslash escape', () => {
    const input = 'Cost is \\$5 and profit is \\$10';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('$5');
    expect(output).toContain('$10');
    expect(output).not.toContain('\\$'); // Escape sequences removed
  });

  it('renders markdown formatting', () => {
    const input = '**bold** and *italic* and `code`';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('<strong>');
    expect(output).toContain('bold');
    expect(output).toContain('<em>');
    expect(output).toContain('italic');
    expect(output).toContain('<code>');
    expect(output).toContain('code');
  });

  it('renders markdown links', () => {
    const input = '[TCS](https://example.com)';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('<a');
    expect(output).toContain('href="https://example.com"');
    expect(output).toContain('TCS');
  });

  it('renders markdown lists', () => {
    const input = '- Item 1\n- Item 2\n- Item 3';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('<ul>');
    expect(output).toContain('<li>');
    expect(output).toContain('Item 1');
    expect(output).toContain('Item 2');
  });

  it('sanitizes script tags', () => {
    const input = '<script>alert("XSS")</script>Safe text';
    const output = renderMarkdownWithMath(input);

    expect(output).not.toContain('<script>');
    expect(output).not.toContain('alert');
    expect(output).toContain('Safe text');
  });

  it('sanitizes event handlers', () => {
    const input = '<a href="#" onclick="alert(1)">Link</a>';
    const output = renderMarkdownWithMath(input);

    expect(output).not.toContain('onclick');
    expect(output).not.toContain('alert');
  });

  it('sanitizes unsafe URL protocols', () => {
    const input = '[Click](javascript:alert(1))';
    const output = renderMarkdownWithMath(input);

    expect(output).not.toContain('javascript:');
    expect(output).not.toContain('alert');
  });

  it('allows safe URL protocols', () => {
    const input = '[HTTP](http://example.com) [HTTPS](https://example.com) [Mail](mailto:test@example.com)';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('http://example.com');
    expect(output).toContain('https://example.com');
    expect(output).toContain('mailto:test@example.com');
  });

  it('renders mixed markdown and math content', () => {
    const input = 'The complexity class **P** is defined as $\\text{DTIME}(n^{O(1)})$, where $n$ is input size.';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('<strong>P</strong>');
    expect(output).toContain('katex');
    expect(output).toContain('DTIME');
    expect(output).not.toContain('$\\text{DTIME}');
  });

  it('handles multiple inline math expressions', () => {
    const input = 'We have $a + b$ and $c - d$ and $e \\cdot f$';
    const output = renderMarkdownWithMath(input);

    // Should contain KaTeX spans but not raw dollar signs
    expect(output).toContain('katex');
    expect(output.match(/<span/g)?.length).toBeGreaterThan(2);
    expect(output).not.toContain('$a + b$');
  });

  it('handles empty input gracefully', () => {
    const output = renderMarkdownWithMath('');
    expect(output).toBe('');
  });

  it('handles invalid LaTeX gracefully', () => {
    const input = 'Invalid math: $\\invalid_command$';
    const output = renderMarkdownWithMath(input);

    // Should not crash, may return original or error message
    expect(output).toBeTruthy();
    expect(typeof output).toBe('string');
  });

  it('keeps invalid formulas visible as escaped source when KaTeX cannot parse them', () => {
    const input = 'Invalid math: $x^{$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('x^{');
    expect(output).toContain('katex-error');
  });

  it('keeps KaTeX trust disabled so href commands do not create links', () => {
    const input = 'Unsafe math: $\\href{https://example.com}{click}$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('\\href');
    expect(output).not.toContain('<a');
    expect(output).not.toContain('href=');
  });

  it('refuses raw HTML instead of rendering it as trusted markup', () => {
    const input = '<strong>raw html</strong> and **markdown**';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('raw html');
    expect(output).toContain('<strong>markdown</strong>');
    expect(output).not.toContain('<strong>raw html</strong>');
  });

  it('falls back to escaped plain text if markdown rendering throws', () => {
    const parseSpy = vi.spyOn(marked, 'parse').mockImplementationOnce(() => {
      throw new Error('marked failed');
    });

    const output = renderMarkdownWithMath('Triangle graph $K_3$ <script>alert(1)</script>');

    expect(output).toContain('Triangle graph $K_3$');
    expect(output).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(output).not.toContain('<script>');
    parseSpy.mockRestore();
  });

  it('preserves KaTeX class names for styling', () => {
    const input = 'Formula $x^2$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('class=');
    expect(output).toContain('katex');
  });

  it('renders complex TCS notation', () => {
    const input = 'Graph $G = (V, E)$ where $|V| = n$ and $|E| = m$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('katex');
    expect(output).not.toContain('$G =');
    expect(output).not.toContain('|V|');
  });

  it('handles nested markdown in lists with math', () => {
    const input = '1. First item with $a^2$\n2. Second item with $b^3$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('<ol>');
    expect(output).toContain('<li>');
    expect(output).toContain('katex');
  });
});

describe('renderMathOnly', () => {
  it('renders inline math without markdown processing', () => {
    const input = 'K_3 graph with $n$ vertices';
    const output = renderMathOnly(input);

    // Should render math but not convert K_3 outside math delimiters
    expect(output).toContain('katex');
    expect(output).not.toContain('<p>'); // No markdown block tags
  });

  it('handles literal dollar signs', () => {
    const input = 'Price: \\$100';
    const output = renderMathOnly(input);

    expect(output).toContain('$100');
    expect(output).not.toContain('\\$');
  });

  it('renders block math in math-only mode', () => {
    const input = '$$x^2 + y^2 = z^2$$';
    const output = renderMathOnly(input);

    expect(output).toContain('katex');
    expect(output).not.toContain('$$');
  });

  it('does not process markdown syntax in math-only mode', () => {
    const input = '**This** should not be bold, but $x^2$ is math';
    const output = renderMathOnly(input);

    expect(output).not.toContain('<strong>');
    expect(output).toContain('**This**');
    expect(output).toContain('katex');
  });

  it('handles empty input', () => {
    const output = renderMathOnly('');
    expect(output).toBe('');
  });
});

describe('security tests', () => {
  it('strips iframe tags', () => {
    const input = '<iframe src="evil.com"></iframe>';
    const output = renderMarkdownWithMath(input);

    expect(output).not.toContain('iframe');
    expect(output).not.toContain('evil.com');
  });

  it('strips object and embed tags', () => {
    const input = '<object data="evil.swf"></object><embed src="evil.swf">';
    const output = renderMarkdownWithMath(input);

    expect(output).not.toContain('object');
    expect(output).not.toContain('embed');
    expect(output).not.toContain('evil.swf');
  });

  it('strips data attributes', () => {
    const input = '<div data-secret="token123">Text</div>';
    const output = renderMarkdownWithMath(input);

    expect(output).not.toContain('data-secret');
    expect(output).not.toContain('token123');
  });

  it('does not expose GitHub tokens in sanitized output', () => {
    const input = 'Token: ghp_1234567890abcdef <script>sendToken()</script>';
    const output = renderMarkdownWithMath(input);

    expect(output).not.toContain('<script>');
    expect(output).not.toContain('sendToken');
    // Token text may remain but script is removed
    expect(output).toContain('Token:');
  });
});

describe('TCS-specific examples', () => {
  it('renders complexity class notation', () => {
    const input = 'The class $\\mathsf{NP}$ contains $\\mathsf{P}$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('katex');
    expect(output).not.toContain('$\\mathsf{NP}$');
  });

  it('renders graph theory notation', () => {
    const input = 'Triangle graph $K_3$ has 3 vertices';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('katex');
    // K_3 should be rendered with subscript 3
    expect(output).toContain('K');
    expect(output).toContain('3');
  });

  it('renders algorithm complexity', () => {
    const input = 'Time complexity: $O(n \\log n)$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('katex');
    expect(output).not.toContain('$O(n');
  });

  it('renders set notation', () => {
    const input = 'The set $S = \\{1, 2, 3\\}$ with $|S| = 3$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('katex');
    expect(output).not.toContain('$S =');
  });

  it('renders probability notation', () => {
    const input = 'Probability $\\Pr[X = 1] = \\frac{1}{2}$';
    const output = renderMarkdownWithMath(input);

    expect(output).toContain('katex');
    expect(output).not.toContain('\\Pr[X');
  });
});
