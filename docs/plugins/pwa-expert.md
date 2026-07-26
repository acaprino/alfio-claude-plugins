# PWA Expert Plugin

> Progressive Web App design, scaffolding, and auditing for the 2025-2026 baseline: Web App Manifest, Service Workers (Workbox 7, Serwist), Web Push (VAPID, Declarative Push for Safari 18.4+), install flows, OPFS storage, Project Fugu APIs, Core Web Vitals (INP < 200ms), framework integration (Vite, Next.js, Angular, Nuxt), and store distribution (Bubblewrap, PWA Builder, Capacitor).

## Agents

### `pwa-architect`

Expert architect for Progressive Web Apps. Designs and implements complete PWAs end-to-end: manifest, service worker, Web Push, install flow, storage, framework integration, and store distribution. Reasons about platform asymmetry (Chromium full support, iOS WebKit constrained, Firefox partial) and applies progressive enhancement rather than assuming feature parity.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch |
| **Use for** | Building or auditing PWAs, manifests, service workers, push pipelines, install flows, OPFS storage, framework-specific PWA integration, store distribution |

**Invocation:**
```
Use the pwa-architect agent to build/audit [PWA feature or codebase]
```
Also delegated to by all three commands below.

**Workflow:** target platforms first (which of Chromium desktop, Android Chrome, iOS Safari, desktop Safari, Firefox does the user need, and what constraints follow), then manifest design, service-worker strategy per route type, a push plan only if it adds user-visible notifications, install UX per platform, storage design, a distribution plan, and a production-checklist gate before shipping. Every deliverable cites the reference file backing the recommendation.

**Routing:** hands off generic frontend styling to the `frontend` plugin (if installed), React-specific performance to `react-development:review-react`, cross-platform security beyond PWA mechanics to `platform-engineering:platform-review`, Tauri/Electron wrapping to `tauri-development`, GA4/analytics to `digital-marketing:ga4-implementation-expert`, and Stripe integration to `stripe:stripe-integrator`.

---

## Skills

### `pwa-development`

Knowledge base for building, auditing, and shipping PWAs in 2025-2026, loaded automatically by `pwa-architect` and referenced on-demand (never preloaded in bulk).

**Reference files:**
- `manifest.md` -- Web App Manifest members, icons, splash screens, iOS meta tags
- `service-workers.md` -- SW lifecycle, caching strategies, Workbox 7, updates, debugging
- `background-execution.md` -- Background Sync, Periodic Sync, Background Fetch, Wake Lock
- `push-notifications.md` -- Web Push end-to-end: VAPID, RFCs, Declarative Push, Badge API
- `install-flows.md` -- `beforeinstallprompt`, iOS manual install, Window Controls Overlay
- `permissions.md` -- Permissions API, `Permissions-Policy` header, platform availability
- `storage-persistence.md` -- IndexedDB, OPFS, quotas, persistent storage
- `capabilities-fugu.md` -- Project Fugu API matrix and worked examples
- `platform-constraints.md` -- iOS / Android / Desktop per-platform reality check
- `performance.md` -- Core Web Vitals 2025, INP < 200ms, audit tooling
- `security.md` -- HTTPS, CSP for service workers, COOP / COEP, secure contexts
- `distribution.md` -- Bubblewrap / TWA, PWA Builder MSIX, Capacitor, Meta Quest
- `frameworks-tooling.md` -- Vite, Next.js, Angular, Nuxt wiring plus debugging surface
- `production-checklist.md` -- full deploy checklist consumed directly by `/pwa-checklist`

**Decision quick-reference table** answers common either/or questions inline (which caching strategy per route type, minimum icon sizes, whether to call `skipWaiting()` by default, iOS Web Push requirements) so the agent doesn't have to open a reference file for a one-line lookup.

---

## Commands

### `/pwa-expert:pwa-audit`

Adversarial PWA audit. Auto-detects mode from the argument: a URL triggers live-mode auditing via `playwright-skill` (manifest fetch, install-criteria check, security headers, offline behavior, Core Web Vitals); a path or omitted argument triggers local-code mode (locates and reads the manifest, service worker, registration call, iOS meta tags, and header config in source).

```
/pwa-expert:pwa-audit                    # local code mode, current directory
/pwa-expert:pwa-audit src/               # local code mode, specific path
/pwa-expert:pwa-audit https://example.com  # live URL mode via Playwright
```

Findings are numbered `C1, C2, ...` (Critical), `I1, I2, ...` (Important), `N1, N2, ...` (Nice-to-have) so they stay referenceable across follow-up prompts. Falls back to manual-check suggestions with explicit "could not verify" markers if `playwright-skill` is unavailable. Notes upfront that Safari Web Inspector cannot inspect installed Home Screen PWAs, so live-mode results don't cover the post-install standalone experience.

---

### `/pwa-expert:pwa-scaffold`

Scaffolds a production-ready PWA into the current project: manifest, service worker, iOS meta tags, registration code, icon stubs, and a headers-recommendations doc. Detects the framework (Vite, Next.js, Angular, Nuxt, or vanilla) from `package.json` and config files, or accepts it as an argument.

```
/pwa-expert:pwa-scaffold          # auto-detect framework
/pwa-expert:pwa-scaffold next     # force Next.js (@serwist/next)
```

Collects app name, short name, description, theme/background colors, and up to two manifest shortcuts via `AskUserQuestion` before generating files. Never silently overwrites an existing manifest or service worker: shows a diff and asks whether to overwrite, merge, or skip. Does not generate a Capacitor/Cordova project, a push-notification server, or auto-apply security headers to deploy config; each of those is documented instead (`distribution.md`, `push-notifications.md`, `headers-recommendations.md`).

---

### `/pwa-expert:pwa-checklist`

Walks the production deploy checklist from `production-checklist.md` interactively against the codebase (or a live URL) and reports **PASS** / **FAIL** / **N/A** per item with a per-category summary table. Deterministic by design: two runs against the same target produce a structurally identical report, which makes it suitable as a CI release gate (unlike `/pwa-audit`, which is open-ended and adversarial).

```
/pwa-expert:pwa-checklist                    # walk against current codebase
/pwa-expert:pwa-checklist https://example.com  # walk against a live deployment
```

Every **FAIL** links back to the matching reference file for self-service remediation. Use `/pwa-checklist` for release gates and CI integration; use `/pwa-audit` for design reviews and pre-launch deep-dives.

---

**Related:** [platform-engineering](platform-engineering.md) (cross-platform security/architecture/performance beyond PWA mechanics) | [react-development](react-development.md) (React-specific performance) | [tauri-development](tauri-development.md) (desktop/mobile native wrappers) | [playwright-skill](playwright-skill.md) (optional dependency for live-URL audit mode)
