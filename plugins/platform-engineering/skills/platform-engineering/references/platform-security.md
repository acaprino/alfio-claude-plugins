# Platform-Specific Security

## Mobile Security

### MUST

- **Use iOS Keychain and Android Keystore** for all sensitive data storage.
- Enforce TLS 1.2+ via App Transport Security (iOS, enabled by default) and Network Security Config (Android).
- Implement **certificate pinning** for critical API endpoints using public key (SPKI) pins with backup pins and a documented rotation runbook.

### DO

- Implement root/jailbreak detection for high-security applications (banking, healthcare) using layered detection methods.
- Enable ProGuard/R8 obfuscation on Android.
- Implement biometric authentication via system APIs (LocalAuthentication on iOS, BiometricPrompt on Android) -- never store biometric data directly.
- Use `FLAG_SECURE` on Android to prevent screenshots of sensitive screens.
- Exclude sensitive data from device backups.

### DON'T

- Embed secrets in app binaries -- extractable via MobSF, Frida, and jadx.
- Use embedded WebViews for OAuth login.
- Rely solely on client-side jailbreak detection -- combine with server-side risk scoring.
- Reference: OWASP MASVS L1/L2 and the MAS Testing Guide.

## Desktop Security - Electron

### MUST

- **Set `nodeIntegration: false`, `contextIsolation: true`, and `sandbox: true`** in all renderer processes. These are defaults in modern Electron but must be verified. Without contextIsolation, web page scripts can access Electron internals. Without sandbox, renderer processes have broad OS access. Define a strict CSP.

### Incident History

- **CVE-2018-1000136:** `nodeIntegration` re-enabled via `<webview>` tags, affecting Atom, VS Code, Slack, Discord -- XSS became RCE on all affected apps.
- **CVE-2021-43908:** XSS in a VS Code webview chained with path traversal for full remote code execution.
- **2024 audit of 112 popular Electron apps:** found "overwhelmingly poor" security, with a majority enabling insecure features.
- **electron-updater signature bypass (CVE-2020-15174):** MITM attackers delivered unsigned malicious updates because signature verification had a "fail-open" condition.

### MUST

- **Code-sign your application** on all platforms (Windows Authenticode, macOS Developer ID + Notarization) and cryptographically verify auto-update signatures before installation.

### DO

- Use preload scripts with `contextBridge.exposeInMainWorld()` to create a controlled API surface.
- Validate all IPC messages in the main process as untrusted input.
- Keep Electron/Chromium updated -- bundled Chromium doesn't auto-update, so track security releases and treat them as ship-blocking.
- Use Electron Fuses to disable `runAsNode` in production.

### DON'T

- Load remote content with `nodeIntegration` enabled.
- Use `shell.openExternal()` with unvalidated URLs.
- Expose broad IPC channels that call `child_process`, `fs`, or `require`.
- Ship with `webSecurity: false`.

## Desktop Security - Tauri

### MUST

- **Keep exposed commands minimal.** Tauri's deny-by-default capability system means the frontend can only invoke explicitly exposed Rust commands. Fundamentally more secure than Electron's model.

### Tauri Advantages

- No bundled Node.js (no supply chain attacks via npm)
- Rust memory safety (no buffer overflows)
- Compiled binaries (~3MB vs Electron's ~85MB+) harder to reverse-engineer

## PWA Security

### MUST

- **Serve everything over HTTPS** -- service workers only function on HTTPS.
- Limit service worker scope to the narrowest necessary path.
- Never cache sensitive data (auth tokens, PII) in the Cache API -- it persists and is accessible to any script on the origin.
  - TU Wien research: since the Cache API is accessible from the entire origin, malicious scripts can achieve persistent person-in-the-middle capabilities against cached content, bypassing security headers including CSP.

### DO

- Implement cache versioning and expiration.
- Use SRI for all third-party scripts.
- Validate data before caching to prevent cache poisoning.
- Implement forced service worker update mechanisms.

## Security Headers Matrix

| Header | SPA | PWA | Mobile | Electron | Tauri |
|--------|-----|-----|--------|----------|-------|
| **CSP** | Critical | Critical | WebViews only | Critical | Relevant |
| **HSTS** (`max-age=31536000; includeSubDomains; preload`) | Critical | Critical | Backend only | Backend only | Backend only |
| **X-Frame-Options** (`DENY`) | Critical | Critical | N/A | Important | N/A |
| **X-Content-Type-Options** (`nosniff`) | Important | Important | N/A | Important | N/A |
| **Referrer-Policy** (`strict-origin-when-cross-origin`) | Important | Important | N/A | Important | N/A |
| **Permissions-Policy** | Important | Important | N/A | Important | N/A |
