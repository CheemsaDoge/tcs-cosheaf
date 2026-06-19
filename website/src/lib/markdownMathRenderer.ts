/**
 * Markdown and LaTeX math renderer for TCS content.
 *
 * Renders user-authored text with Markdown formatting and inline/block LaTeX math.
 * Repository files remain plain Markdown/YAML; this is display-only rendering.
 *
 * Required by Task B2.9.3: Markdown and LaTeX rendering polish.
 */

import { marked } from 'marked';
import katex from 'katex';
import DOMPurify from 'isomorphic-dompurify';

/**
 * Escapes special regex characters in a string.
 */
function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Configuration for the markdown renderer.
 */
export interface MarkdownRenderOptions {
  /**
   * Custom KaTeX options.
   */
  katexOptions?: katex.KatexOptions;
}

function katexOptions(
  displayMode: boolean,
  options: katex.KatexOptions = {}
): katex.KatexOptions {
  return {
    ...options,
    displayMode,
    throwOnError: false,
    trust: false,
  };
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function fallbackPlainText(text: string): string {
  return escapeHtml(text);
}

function refuseRawHtml(text: string): string {
  return text
    .replace(/<(script|style|iframe|object|embed)\b[^>]*>[\s\S]*?<\/\1>/gi, '')
    .replace(/<(script|style|iframe|object|embed)\b[^>]*\/?>/gi, '')
    .replace(/<\/?[A-Za-z][^>]*>/g, '');
}

/**
 * Renders markdown text with LaTeX math support.
 *
 * Supports:
 * - GFM/CommonMark markdown
 * - Inline math: $...$
 * - Block math: $$...$$
 * - Escaped dollar signs: \$ for literal $
 *
 * Security:
 * - Sanitizes HTML output via DOMPurify
 * - Strips scripts, unsafe links, and event handlers
 * - Refuses raw HTML before Markdown rendering
 *
 * Example inputs:
 * - "Triangle graph $K_3$" renders K with subscript 3
 * - "Formula: $$\sum_{i=1}^n i = \frac{n(n+1)}{2}$$" renders a block equation
 * - "Cost is \$5" renders a literal dollar sign
 *
 * @param text Plain markdown text with optional LaTeX
 * @param options Rendering configuration
 * @returns Sanitized HTML string
 */
export function renderMarkdownWithMath(
  text: string,
  options: MarkdownRenderOptions = {}
): string {
  if (!text) {
    return '';
  }

  try {
    return renderMarkdownWithMathUnsafe(text, options);
  } catch (error) {
    console.error('Markdown rendering error:', error);
    return fallbackPlainText(text);
  }
}

function renderMarkdownWithMathUnsafe(
  text: string,
  options: MarkdownRenderOptions = {}
): string {
  const { katexOptions: customKatexOptions = {} } = options;

  // Step 1: Extract and protect literal dollar signs
  // Replace \$ with a placeholder to avoid treating as math delimiter
  const literalDollarPlaceholder = '\x00LITERAL_DOLLAR\x00';
  let processed = text.replace(/\\\$/g, literalDollarPlaceholder);

  // Step 2: Process block math first ($$...$$)
  // Use a placeholder map to protect rendered math from markdown processing
  const blockMathMap = new Map<string, string>();
  let blockMathIndex = 0;

  processed = processed.replace(/\$\$([\s\S]+?)\$\$/g, (match, mathContent) => {
    try {
      const rendered = katex.renderToString(
        mathContent.trim(),
        katexOptions(true, customKatexOptions)
      );
      const placeholder = `\x00BLOCKMATH${blockMathIndex}\x00`;
      blockMathMap.set(placeholder, rendered);
      blockMathIndex++;
      return placeholder;
    } catch (error) {
      console.error('KaTeX block math rendering error:', error);
      return escapeHtml(match);
    }
  });

  // Step 3: Process inline math ($...$)
  const inlineMathMap = new Map<string, string>();
  let inlineMathIndex = 0;

  processed = processed.replace(/\$([^\$\n]+?)\$/g, (match, mathContent) => {
    try {
      const rendered = katex.renderToString(
        mathContent.trim(),
        katexOptions(false, customKatexOptions)
      );
      const placeholder = `\x00INLINEMATH${inlineMathIndex}\x00`;
      inlineMathMap.set(placeholder, rendered);
      inlineMathIndex++;
      return placeholder;
    } catch (error) {
      console.error('KaTeX inline math rendering error:', error);
      return escapeHtml(match);
    }
  });

  processed = refuseRawHtml(processed);

  // Step 4: Configure marked for GFM
  marked.setOptions({
    gfm: true,
    breaks: false,
    headerIds: false,
    mangle: false,
  });

  // Step 5: Render markdown
  let html = marked.parse(processed) as string;

  // Step 6: Restore math placeholders
  blockMathMap.forEach((rendered, placeholder) => {
    html = html.replace(new RegExp(escapeRegExp(placeholder), 'g'), rendered);
  });

  inlineMathMap.forEach((rendered, placeholder) => {
    html = html.replace(new RegExp(escapeRegExp(placeholder), 'g'), rendered);
  });

  // Step 7: Restore literal dollar signs
  html = html.replace(new RegExp(literalDollarPlaceholder, 'g'), '$');

  // Step 8: Sanitize HTML
  const sanitized = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre',
      'a', 'ul', 'ol', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'span', 'div', // KaTeX uses these
    ],
    ALLOWED_ATTR: [
      'href', 'title', 'class', 'style', 'aria-hidden', // KaTeX needs class and style
    ],
    ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto):)/i, // Only safe protocols
    ALLOW_DATA_ATTR: false,
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick'], // No event handlers
  });

  return sanitized;
}

/**
 * Renders plain text with LaTeX math only (no markdown processing).
 * Useful for shorter text fields where markdown formatting is not expected.
 *
 * @param text Plain text with optional LaTeX
 * @param options Rendering configuration
 * @returns Sanitized HTML string
 */
export function renderMathOnly(
  text: string,
  options: MarkdownRenderOptions = {}
): string {
  if (!text) {
    return '';
  }

  const { katexOptions: customKatexOptions = {} } = options;
  const literalDollarPlaceholder = '\x00LITERAL_DOLLAR\x00';
  let processed = text.replace(/\\\$/g, literalDollarPlaceholder);
  const blockMathMap = new Map<string, string>();
  let blockMathIndex = 0;
  const inlineMathMap = new Map<string, string>();
  let inlineMathIndex = 0;

  // Process block math
  processed = processed.replace(/\$\$([\s\S]+?)\$\$/g, (match, mathContent) => {
    try {
      const placeholder = `\x00BLOCKMATH${blockMathIndex}\x00`;
      blockMathMap.set(
        placeholder,
        katex.renderToString(mathContent.trim(), katexOptions(true, customKatexOptions))
      );
      blockMathIndex++;
      return placeholder;
    } catch (error) {
      console.error('KaTeX block math rendering error:', error);
      return escapeHtml(match);
    }
  });

  // Process inline math
  processed = processed.replace(/\$([^\$\n]+?)\$/g, (match, mathContent) => {
    try {
      const placeholder = `\x00INLINEMATH${inlineMathIndex}\x00`;
      inlineMathMap.set(
        placeholder,
        katex.renderToString(mathContent.trim(), katexOptions(false, customKatexOptions))
      );
      inlineMathIndex++;
      return placeholder;
    } catch (error) {
      console.error('KaTeX inline math rendering error:', error);
      return escapeHtml(match);
    }
  });

  processed = refuseRawHtml(processed);

  blockMathMap.forEach((rendered, placeholder) => {
    processed = processed.replace(new RegExp(escapeRegExp(placeholder), 'g'), rendered);
  });

  inlineMathMap.forEach((rendered, placeholder) => {
    processed = processed.replace(new RegExp(escapeRegExp(placeholder), 'g'), rendered);
  });

  // Restore literal dollar signs
  processed = processed.replace(new RegExp(literalDollarPlaceholder, 'g'), '$');

  // Escape HTML but preserve KaTeX output
  const sanitized = DOMPurify.sanitize(processed, {
    ALLOWED_TAGS: ['span', 'div'],
    ALLOWED_ATTR: ['class', 'style', 'aria-hidden'],
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed'],
  });

  return sanitized;
}
