# AMO Publishing and Security Reference

The Firefox add-on store (addons.mozilla.org) review process and the security rules that get extensions rejected. Distribution mechanics, signing commands, and i18n boilerplate live upstream; this file is the gotchas + the rejection-trigger checklist.

## When to use

Submitting a Firefox extension to AMO (listed = public) or self-distributing (unlisted = signed only). For pre-publish lint checks, use the `firefox-lint` command.

## Distribution channel cheat sheet

| Channel | Review | Signing | Auto-updates |
|---------|--------|---------|--------------|
| **AMO Listed** | Auto + manual post-publication | AMO signs | AMO handles |
| **Self-distributed (unlisted)** | Auto only | AMO signs | Extension manages via `update_url` |

Each version must have a unique version number -- AMO does not allow re-uploading the same version, even after a delete.

## Publishing in 4 commands

```bash
web-ext build                                  # produce the .xpi/.zip
web-ext sign --channel listed                  # AMO listing (manual review follows)
# OR
web-ext sign --channel unlisted \
  --api-key $WEB_EXT_API_KEY \
  --api-secret $WEB_EXT_API_SECRET             # self-distribution
```

## Gotchas (the things that get extensions rejected)

- **Modified third-party libraries = instant rejection.** Bundle libraries unmodified; if you must patch, document the diff and submit source.
- **Remote script loading = instant rejection.** Bundle ALL code locally. No CDN scripts, no `eval(fetch(...))`. The reviewer's automated scanner catches `<script src="https://...">` in extension pages.
- **`eval()` is forbidden in MV3** (CSP enforced). In MV2 it's allowed but flagged as dangerous. Don't use it.
- **Overly broad `<all_urls>` host permissions without justification** trigger manual review and often rejection. Request only what you need; use `activeTab` when possible.
- **Submit source code for ANY minified/transpiled build** with `--upload-source-code` flag. AMO reviewers won't accept obfuscated bundles without it. Even Webpack output qualifies as "minified."
- **Outdated libraries with known CVEs can trigger AMO blocking** post-publication, not just rejection. Keep deps current; lint with `eslint-plugin-no-unsanitized` to catch dangerous DOM patterns.
- **Don't expose `moz-extension://{UUID}` to web pages** -- it's a fingerprinting vector. If you inject scripts, use `web_accessible_resources` with `matches` constraints, not blanket exposure.
- **Use REST APIs for analytics, never embedded tracking JS.** Embedded GA/Mixpanel/etc. scripts in extension pages = rejection.
- **Always use safe DOM methods**: `createElement()`, `setAttribute()`, `textContent`. Sanitize HTML with **DOMPurify 2.0.7+** for any HTML insertion. Never `.innerHTML = userInput`.

## CSP differences (MV2 vs MV3)

The single most common manifest gotcha when migrating MV2 → MV3:

```json
// MV2 (string)
{ "content_security_policy": "script-src 'self'; object-src 'self'" }

// MV3 (object with extension_pages key)
{ "content_security_policy": { "extension_pages": "script-src 'self'; object-src 'self'" } }
```

Other CSP rules: default policy restricts `eval()` and inline scripts. MV3 forbids `eval()` entirely. Remote script loading blocked by default in both. `wasm-unsafe-eval` allowed for WebAssembly in MV3. Extension pages and sandbox pages can have different policies.

## i18n one-liners (the parts that are non-obvious)

Manifest reference: `"name": "__MSG_extensionName__"`, `"default_locale": "en"`. Files: `_locales/<lang>/messages.json`. JS: `browser.i18n.getMessage("key", ["arg1"])`. HTML: `data-l10n-id="key"` or inline `__MSG_key__`.

Full schema and placeholder syntax: see MDN i18n link below.

## Official docs

- AMO submission portal: https://addons.mozilla.org/developers/
- AMO Add-on Policies (the rejection rulebook): https://extensionworkshop.com/documentation/publish/add-on-policies/
- Source-code submission policy: https://extensionworkshop.com/documentation/publish/source-code-submission/
- Self-distribution: https://extensionworkshop.com/documentation/publish/signing-and-distribution-overview/#distributing-your-addon
- web-ext sign reference: https://extensionworkshop.com/documentation/develop/web-ext-command-reference/#web-ext-sign
- Extension Workshop security best practices: https://extensionworkshop.com/documentation/develop/build-a-secure-extension/
- CSP for WebExtensions: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_Security_Policy
- i18n full guide: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Internationalization
- DOMPurify: https://github.com/cure53/DOMPurify

## Related

- `browser-api-reference.md` -- which permissions to declare for which APIs
- `manifest-schema.md` -- CSP placement + Firefox-specific keys
- `best-practices.md` -- the MV3 footgun catalog (Bugzilla bugs, listener registration rules, port-disconnection patterns)
- `mdn-api-urls.md` -- direct MDN deep-links for every API
