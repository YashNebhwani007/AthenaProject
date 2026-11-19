# ADR-21: Client-Side Markdown Rendering and KaTeX Sanitization

## Status
Accepted

## Context
Athena analytical reports contain Markdown, tabular metrics, LaTeX mathematical formulas
(e.g., KaTeX notation for statistical significance and formulas), and raw LLM-generated summaries.
Rendering arbitrary rich text on the client-side creates Cross-Site Scripting (XSS) vulnerabilities
if unsanitized HTML is injected into the DOM.

## Decision
1. Enforce DOMPurify sanitization before rendering any Markdown or LaTeX stream in the React UI.
2. Restrict Markdown rendering to a secure whitelist of HTML tags (`<p>`, `<span>`, `<code>`, `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<h3>`, `<h4>`).
3. Render mathematical KaTeX blocks with `throwOnError: false` to ensure client rendering stability.
4. Forbid inline script execution, inline event handlers (`onclick`, `onerror`), and `javascript:` URIs.

## Consequences
- Safe client-side rendering without risk of script injection.
- Consistent visual presentation of complex statistical equations across all browsers.
- Malicious HTML tags embedded in uploaded dataset columns or LLM completions are neutralised.
