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

**Reference documents:** server-validation, auth-tokens, passkeys-webauthn, api-security, xss-csp, secrets-management, platform-security, client-server-architecture, api-design, offline-first, infrastructure, frontend-performance, backend-and-platform-performance.

---

## Commands

### `/platform-review`

Standalone cross-platform security, architecture, and performance review. Auto-detects the platform mix (SPA, PWA, mobile, Electron, Tauri) from `package.json`, `Cargo.toml`, `manifest.json`, and `tauri.conf.json`, then spawns the `platform-reviewer` agent against every applicable rulebook. Writes a persistent report to `.platform-review/REPORT.md`. Report-only; never auto-fixes.

```
/platform-review                              # current directory, auto-detect platforms, all 3 dimensions
/platform-review src/ --focus security        # security-only audit on a subdirectory
/platform-review --platform tauri --focus arch # Tauri architecture review
```

**Arguments:**
| Flag | Effect |
|------|--------|
| `[target-path]` | Path to review (default: current directory) |
| `--platform spa\|pwa\|mobile\|electron\|tauri\|auto` | Force a platform or let auto-detect handle it (default: `auto`) |
| `--focus security\|arch\|perf` | Restrict scope to one dimension (default: all three) |

**Output sections in `REPORT.md`:** detected platforms, summary counts, findings by severity (CRITICAL / HIGH / MEDIUM) with `file:line` plus rule violated and suggested fix, hardening checklist for Electron / Tauri, auth posture checklist, recommendations ordered by impact.

**When to invoke:**
- Before a PR touching auth, secrets, or platform integration
- Quarterly cross-platform hygiene
- After adding a new platform target (e.g., shipping mobile alongside web)
- Electron / Tauri release hardening

---

**Related:** [senior-review](senior-review.md) (code-level review) | [agent-teams](agent-teams.md) (team presets include platform review) | [tauri-development](tauri-development.md) (desktop/mobile platform)
