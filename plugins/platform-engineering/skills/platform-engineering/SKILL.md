---
name: platform-engineering
description: >
  Cross-platform development rulebook covering security, architecture, and performance
  for SPA, PWA, mobile (iOS/Android), and desktop (Electron/Tauri) applications.
  MUST/DO/DON'T framework with real-world incident references and platform-specific guidance.
  TRIGGER WHEN: reviewing or building cross-platform apps, checking security posture,
  validating architecture decisions, optimizing performance, or auditing code against
  industry standards (OWASP, Core Web Vitals, OAuth 2.1).
  DO NOT TRIGGER WHEN: the task is purely about UI design, copywriting, or business logic
  unrelated to platform engineering concerns.
---

# Cross-Platform Development Rulebook

Three pillars govern every application you ship -- Security, Architecture, and Performance. Each rule is tagged with severity (MUST/DO/DON'T) and platform applicability.

## Quick Platform Decision Matrix

| Concern | SPA | PWA | Mobile | Electron | Tauri |
|---------|-----|-----|--------|----------|-------|
| **Auth token storage** | JS memory + httpOnly cookies | JS memory + httpOnly cookies | Platform Keychain/Keystore | OS credential store | OS credential store |
| **OAuth flow** | Auth Code + PKCE | Auth Code + PKCE | System browser + PKCE | Standard PKCE | Standard PKCE |
| **XSS impact** | Session hijack | + persistent SW hijack | WebView bridge access | XSS to RCE | Limited to web context |
| **CSP** | Critical | Critical | WebViews only | Critical | Relevant |
| **Offline strategy** | Optional | IndexedDB + Cache API + SW | Room/CoreData + sync queue | Optional | Optional |
| **Bundle target** | <170KB compressed JS | <170KB compressed JS | <20MB APK/IPA | 80-150MB (Chromium) | <10MB total |
| **API style** | REST or GraphQL | REST (SW caching) | GraphQL (fewer round-trips) | REST (server-side aggregation) | REST |
| **State management** | Zustand/Redux + TanStack Query | IndexedDB + Cache API | ViewModel+StateFlow / SwiftUI | IPC + context isolation | Rust invoke commands |

## When to Load References

- **Security review or audit**: Load `server-validation`, `auth-tokens`, `api-security`, `xss-csp`, `secrets-management`, `platform-security`
- **Architecture decisions**: Load `client-server-architecture`, `api-design`, `offline-first`, `infrastructure`
- **Performance optimization**: Load `frontend-performance`, `backend-and-platform-performance`
- **Full platform review**: Load all 12 references

## Reference Materials

### Security (Part 1)

1. **server-validation.md** -- Server-side validation rules, trust boundaries, real-world bypass incidents
2. **auth-tokens.md** -- Token storage per platform, OAuth 2.1 flows, JWT best practices, secure storage APIs
3. **api-security.md** -- Endpoint auth, rate limiting, CORS, OWASP API risks, Peloton/Parler case studies
4. **xss-csp.md** -- XSS severity by platform, CSP directives, anti-CSRF, sanitization, British Airways incident
5. **secrets-management.md** -- Secret exposure risks, environment variables, vault services, GitGuardian stats
6. **platform-security.md** -- Mobile (Keychain/Keystore, cert pinning), Electron (nodeIntegration, contextIsolation, sandbox), Tauri (deny-by-default), PWA (service worker scope, Cache API risks), security headers matrix

### Architecture (Part 2)

7. **client-server-architecture.md** -- Thin client principle, BFF pattern, server-authoritative design
8. **api-design.md** -- REST vs GraphQL trade-offs by platform, pagination strategies, state management per platform
9. **offline-first.md** -- Conflict resolution strategies (LWW, CRDTs, OT), optimistic UI, sync patterns
10. **infrastructure.md** -- Monolith-first principle, database access patterns, CI/CD pipelines per platform, observability, feature flag lifecycle

### Performance (Part 3)

11. **frontend-performance.md** -- Bundle size optimization, image formats and responsive loading, Core Web Vitals (LCP, INP, CLS) with business impact data
12. **backend-and-platform-performance.md** -- API/DB performance (pagination, indexing, connection pooling), mobile battery/memory, SSR/SSG/ISR rendering strategies, CDN caching patterns
