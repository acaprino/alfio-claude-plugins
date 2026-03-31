# Platform Engineering Plugin

> Cross-platform development rulebook covering security, architecture, and performance for SPA, PWA, mobile (iOS/Android), and desktop (Electron/Tauri) applications. MUST/DO/DON'T framework with real-world incident references and platform-specific guidance.

## Agents

### `platform-reviewer`

Adversarial cross-platform code reviewer that audits code against the platform-engineering rulebook.

| | |
|---|---|
| **Model** | `opus` |
| **Tools** | `Read, Glob, Grep, Bash` |
| **Use for** | Reviewing PRs or code for security, architecture, or performance compliance across SPA, PWA, mobile, and desktop platforms |

**Invocation:**
```
Use the platform-reviewer agent to audit [path or PR]
```

**What it audits:**
- Server validation and trust boundaries
- Auth token storage (cookies vs localStorage vs secure storage)
- API security (CORS, rate limiting, HTTPS)
- XSS/CSP headers
- Secrets exposure
- Architecture patterns (client-server, REST vs GraphQL, offline-first)
- Performance (bundles, images, Core Web Vitals, SSR/SSG, CDN caching)

---

## Skills

### `platform-engineering`

Comprehensive cross-platform development rulebook with 12 reference documents covering security, architecture, and performance.

| | |
|---|---|
| **Trigger** | Cross-platform app review, security posture checks, architecture validation, performance optimization |

**Reference documents:** server-validation, auth-tokens, api-security, xss-csp, secrets-management, platform-security, client-server-architecture, api-design, offline-first, infrastructure, frontend-performance, backend-and-platform-performance.

---

**Related:** [senior-review](senior-review.md) (code-level review) | [agent-teams](agent-teams.md) (team presets include platform review) | [tauri-development](tauri-development.md) (desktop/mobile platform)
