---
name: firefox-extension-dev
description: >
  Reference knowledge base for Firefox WebExtension development. Contains browser API reference,
  manifest schema, AMO publishing guide, MDN URL index, and best practices. Used by the
  firefox-extension-dev agent for documentation lookup. Use when building, implementing, writing,
  coding, creating, debugging, or publishing a Firefox/WebExtension add-on (manifest.json,
  browser.* APIs, AMO submission, web-ext CLI). Not for targeting Chrome-only extensions, Safari
  extensions, or userscripts/bookmarklets.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: browser-extensions
---

# Firefox Extension Development References

This skill provides reference files for the `firefox-extension-dev` agent. The agent handles all active development work (scaffolding, coding, debugging, publishing). These reference files serve as its knowledge base.

## Reference Files

- `references/browser-api-reference.md` - Complete list of all 51 browser.* APIs with methods, events, and permissions
- `references/manifest-schema.md` - Full manifest.json key reference with MV2/MV3 examples
- `references/amo-publishing.md` - AMO publishing checklist, review policies, CSP, security best practices, i18n
- `references/mdn-api-urls.md` - Direct MDN URL index for all browser.* APIs, manifest keys, and Extension Workshop resources
- `references/best-practices.md` - Best practices, pitfalls, and anti-patterns: JS patterns, Workers, sessions, startup, security, performance, cross-browser
