# Obsidian Development Plugin

> Obsidian community plugin development with ObsidianReviewBot compliance, project scaffolding, and pre-submission checks.

## Skills

### `obsidian-plugin-development`

Write Obsidian plugin code that passes ObsidianReviewBot on first submission. Covers all required eslint-plugin-obsidianmd rules with code examples.

| | |
|---|---|
| **Trigger** | Writing, reviewing, or fixing Obsidian community plugin code |
| **Coverage** | 21 required rules (sentence case, no inline styles, promise handling, etc.), API reference |
| **Reference** | Condensed TypeScript API reference for Plugin, Vault, Workspace, Setting, Modal, and more |

### `obsidian-scaffold`

Scaffold a new Obsidian community plugin project -- bot-compliant from day one.

| | |
|---|---|
| **Trigger** | Creating a new Obsidian plugin from scratch |
| **Creates** | `manifest.json`, `package.json`, `tsconfig.json`, `esbuild.config.mjs`, `.eslintrc.json`, `src/main.ts` |
| **Validates** | Plugin ID, name, and description against ObsidianReviewBot rules |

### `obsidian-check`

Pre-submission lint and review. Auto-installs `eslint-plugin-obsidianmd` if missing, runs all 28 ESLint rules (including `ui/sentence-case`), plus manual checks the linter does not cover.

| | |
|---|---|
| **Trigger** | Before pushing or submitting an Obsidian plugin |
| **Auto-setup** | Installs `eslint-plugin-obsidianmd` with recommended config if not present |
| **Checks** | TypeScript compilation, 28 ESLint rules (sentence case, inline styles, commands, manifest, etc.), 6 manual checks, manifest validation, LICENSE |
| **Output** | Structured report with severity grouping, file:line locations, and suggested fixes |

---

**Related:** [typescript-development](typescript-development.md) (TypeScript coding standards) | [learning](learning.md) (mind maps for Obsidian MarkMind)
