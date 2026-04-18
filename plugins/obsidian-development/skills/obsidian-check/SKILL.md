---
name: obsidian-check
description: >
  Reviews code against all ObsidianReviewBot rules and reports violations with fixes. Use PROACTIVELY before any git push on an Obsidian plugin project.
  TRIGGER WHEN: preparing an Obsidian plugin for submission or before pushing code
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Obsidian Check

Review code against all ObsidianReviewBot rules before pushing. Reports violations grouped by severity with exact file locations and fixes.

## Usage

`/obsidian-check` -- scans the current Obsidian plugin project for all bot violations.

## Procedure

### Step 1: Verify project structure

Check that `manifest.json`, `package.json`, and `src/` exist. If not, abort with message.

### Step 2: Ensure eslint-plugin-obsidianmd is installed

Check if `eslint-plugin-obsidianmd` is in `package.json` devDependencies. If NOT installed:

1. Install it and its peer dependencies:

```bash
npm install --save-dev eslint eslint-plugin-obsidianmd @typescript-eslint/parser typescript-eslint @eslint/js
```

2. If no ESLint config file exists (`eslint.config.mjs`, `.eslintrc.*`), create `eslint.config.mjs`:

```javascript
import tsparser from "@typescript-eslint/parser";
import { defineConfig } from "eslint/config";
import obsidianmd from "eslint-plugin-obsidianmd";

export default defineConfig([
  ...obsidianmd.configs.recommended,
  {
    files: ["**/*.ts"],
    languageOptions: {
      parser: tsparser,
      parserOptions: { project: "./tsconfig.json" },
    },
  },
]);
```

3. Inform the user that `eslint-plugin-obsidianmd` was installed and configured.

### Step 3: Run TypeScript check

```bash
npx tsc --noEmit
```

Report any type errors.

### Step 4: Run eslint-plugin-obsidianmd

```bash
npx eslint src/ 2>&1
```

This covers sentence case (`ui/sentence-case`), inline styles, command rules, manifest validation, TFile/TFolder casts, forbidden elements, and more. Report all ESLint errors and warnings.

### Step 5: Manual checks (scan all .ts files in src/)

These checks catch issues NOT covered by eslint-plugin-obsidianmd. Run by reading the source code:

#### Required (blocking)

| # | Check | How to detect |
|---|-------|---------------|
| 1 | **No unnecessary type assertions** | Search for `as Type` where `??` fallback makes it redundant |
| 2 | **Promises handled** | Search for async function calls without `await`, `void`, `.catch()`, or `.then()` with rejection |
| 3 | **No async without await** | Search for `async` methods with no `await` inside |
| 4 | **No promise where void expected** | Search for async callbacks in event handlers that expect void |
| 5 | **No object stringification** | Search for template literals with `??` where left side could be an object |
| 6 | **Setting.setHeading()** | Search for `createEl('h1')`, `createEl('h2')`, `createEl('h3')` in settings/modals |

#### Optional (warnings)

| # | Check | How to detect |
|---|-------|---------------|
| 1 | **Unused imports** | TypeScript check catches these |
| 2 | **Unused variables** | TypeScript check catches these |
| 3 | **console.log in lifecycle** | Search for `console.log` in `onload()`/`onunload()` |

### Step 6: Check manifest.json

- `id`: alphanumeric + dashes, no "obsidian", no "plugin" suffix
- `name`: no "Obsidian", no "Plugin" suffix
- `description`: no "Obsidian", no "This plugin", must end with `. ? ! )`, under 250 chars
- All required fields present: `id`, `name`, `version`, `minAppVersion`, `description`, `author`
- `version` matches latest git tag (if any)

### Step 7: Check LICENSE

- File exists
- Copyright year is current year
- Copyright holder is not placeholder

### Step 8: Report

Output a structured report:

```
## Obsidian Lint Report

### TypeScript: [PASS/FAIL]
[errors if any]

### ESLint: [PASS/FAIL]
[errors if any]

### Required Violations: [count]
[grouped by rule, with file:line and suggested fix]

### Optional Warnings: [count]
[grouped by rule]

### Manifest: [PASS/FAIL]
[issues if any]

### License: [PASS/FAIL]
[issues if any]

---
**Result: [READY TO PUSH / FIX REQUIRED ISSUES FIRST]**
[count] required issues, [count] warnings
```

### Step 9: Offer to fix

If violations are found, ask:
1. Fix all automatically
2. Fix only required violations
3. Show me the details, I'll fix manually

For auto-fix, apply changes following the obsidian-plugin-development skill rules (move styles to CSS classes, fix sentence case, remove unnecessary assertions, void unhandled promises, etc.).
