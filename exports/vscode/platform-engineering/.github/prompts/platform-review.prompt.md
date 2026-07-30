---
description: Standalone cross-platform security, architecture, and performance review - audits code against the platform-engineering rulebook (server validation, auth token storage, WebAuthn/passkeys, API security, XSS/CSP, secrets, architecture patterns, bundle/perf) for SPA, PWA, mobile (iOS/Android), Electron, and Tauri. Use when the user asks for a platform-level review, cross-platform security audit, Electron/Tauri hardening check, or "review this for SPA/PWA/mobile/desktop compliance". Not for generic code quality without platform-specific concerns, UI design alone, or pure backend API code with no client-side dimension.
agent: platform-reviewer
argument-hint: [target-path] [--platform spa|pwa|mobile|electron|tauri|auto] [--focus security|arch|perf]
---

# Platform Engineering Review

Standalone invocation of the `platform-reviewer` agent, for targeted cross-platform audits.

## CRITICAL RULES

1. **Detect platform first**. Scan `package.json`, `Cargo.toml`, `manifest.json`, `tauri.conf.json`, build configs to identify the platform mix. If `--platform auto` is set (default), report the detected platforms before reviewing.
2. **Run in parallel when multiple platforms are present**. A single repo may ship SPA + mobile + Tauri; load all applicable rulebooks.
3. **Write output to `.platform-review/REPORT.md`** for persistence.
4. **Never auto-fix**. Report findings; user decides what to apply.

## Procedure

### 1. Scope detection

Parse `$ARGUMENTS`:
- target path (default: current directory)
- `--platform`: force a specific platform or let auto-detect handle it
- `--focus`: restrict to `security` | `arch` | `perf` (default: all three)

Detect platforms:
- SPA: React/Vue/Svelte + no service worker
- PWA: `manifest.webmanifest` + service worker registered
- Mobile: Expo / React Native, Capacitor, NativeScript, Flutter
- Electron: `electron` in `package.json`
- Tauri: `@tauri-apps/api` + `src-tauri/`

### 2. Run the review

Run the review over the target, the detected platforms, and the focus flag, loading the relevant references from the `platform-engineering` skill's `references/` directory:

- Security: `server-validation.md`, `auth-tokens.md`, `passkeys-webauthn.md`, `api-security.md`, `xss-csp.md`, `secrets-management.md`, `platform-security.md`
- Architecture: `client-server-architecture.md`, `api-design.md`, `offline-first.md`, `infrastructure.md`
- Performance: `frontend-performance.md`, `backend-and-platform-performance.md`

For Electron / Tauri specifically, the agent also loads platform-security.md for the hardening checklist (fuses, asar integrity, capabilities, allowlists).

### 3. Output report

`.platform-review/REPORT.md`:

```markdown
# Platform Review -- <target> -- <date>

## Detected platforms
- SPA | PWA | Mobile | Electron | Tauri

## Summary
- Critical issues: N
- High: N
- Medium: N

## Findings

### [CRITICAL]
- <file:line> <issue> -- <rule violated> -- <fix>

### [HIGH]
- ...

### [MEDIUM]
- ...

## Hardening checklist (Electron / Tauri if applicable)
- [ ] fuses.yml configured with hardened defaults
- [ ] asar-integrity enabled for signed releases
- [ ] Capabilities scoped per window (Tauri)
- [ ] CSP includes 'strict-dynamic' + nonces
- [ ] Auto-updater signature verification

## Auth posture
- [ ] No JWT in localStorage (SPA/PWA)
- [ ] Refresh tokens in httpOnly + Secure + SameSite=Strict cookies
- [ ] PKCE for OAuth on SPA/Mobile/Desktop
- [ ] Platform-native secure storage for mobile/desktop tokens
- [ ] WebAuthn / passkeys implemented for new auth flows (recommended for 2025+)

## Recommendations ordered by impact
1. ...
```

## Synergies

These live in sibling bundles of the same catalog; skip any that are not installed.

- Deeper multi-dimension code review -> `/team-review` in the `_pipelines` bundle
- Tauri-specific hardening -> the `tauri-desktop` agent in the `tauri-development` bundle
- React performance inside a platform context -> `/review-react` in the `react-development` bundle
- Security-specific audit only -> the `review-security-auditor` agent in the `_pipelines` bundle
