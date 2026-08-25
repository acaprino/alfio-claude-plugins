# XSS and Content Security Policy

Cross-site scripting remains one of the most prevalent web vulnerabilities. Its impact varies dramatically across platforms.

## XSS Severity by Platform

| Platform | XSS consequence |
|----------|----------------|
| **SPA** | Session hijacking, data theft, DOM manipulation |
| **PWA** | All SPA risks + persistent service worker hijacking that survives browser restart |
| **Native Mobile** | WebView XSS can access native bridges if JavaScript is enabled in WebViews |
| **Electron** | **XSS to RCE** if `nodeIntegration: true` or `contextIsolation: false` -- DOM injection becomes full system compromise |
| **Tauri** | XSS limited to web context; Rust backend not directly accessible unless commands are overly permissive |

## MUST

- **Implement Content Security Policy headers.** Minimum baseline:
  ```
  default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'
  ```
  CSP is critical for all web-based platforms (SPA, PWA, Electron).
  - **British Airways Magecart attack (2018):** attackers injected malicious JavaScript via a compromised third-party script that skimmed credit card data from 380,000 transactions, resulting in a GBP 20 million GDPR fine. A strict CSP with Subresource Integrity would have blocked the unauthorized script execution.

- **Use anti-CSRF tokens** for all state-changing operations when using cookie-based authentication. Combine with SameSite=Strict cookies.

- **Sanitize all user input** with context-appropriate encoding -- HTML entities for HTML output, parameterized queries for SQL, URL encoding for URLs. Use DOMPurify or equivalent for any HTML that must be rendered from user content.

## DO

- Use modern frameworks (React, Angular, Vue) that auto-escape output by default, but remain vigilant about escape hatches: `dangerouslySetInnerHTML` in React, `[innerHTML]` in Angular, `v-html` in Vue.
- Implement Subresource Integrity (SRI) for all third-party scripts.

## DON'T

- Use `innerHTML`, `document.write()`, or `eval()` with user-supplied data.
- Disable CSP for developer convenience.
- Use `unsafe-inline` or `unsafe-eval` in CSP directives -- they defeat the purpose entirely.

## Official docs

- OWASP XSS Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- MDN Content Security Policy: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
- W3C CSP Level 3: https://www.w3.org/TR/CSP3/
- MDN SameSite cookies: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite
- MDN Subresource Integrity: https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity
- DOMPurify: https://github.com/cure53/DOMPurify
- British Airways Magecart case: https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2020/10/ico-fines-british-airways-20m-for-data-breach-affecting-more-than-400-000-customers/
