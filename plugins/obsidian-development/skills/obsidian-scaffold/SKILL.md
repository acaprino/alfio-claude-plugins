---
name: obsidian-scaffold
description: >
  Scaffolds project structure, manifest, tsconfig, esbuild config, and a minimal plugin class that passes Obsidian's automated plugin review.
  TRIGGER WHEN: the user asks to start, create, bootstrap, or initialize a new Obsidian community plugin
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Obsidian Plugin Scaffold

Scaffold a new Obsidian community plugin project that is review-compliant from day one.

## Usage

`/obsidian-scaffold` -- then answer the prompts for plugin ID, name, author, and description.

## What It Creates

```
my-plugin/
  src/
    main.ts           # Plugin class with onload/onunload
  styles.css          # Empty, scoped styles
  manifest.json       # Valid manifest (review-compliant)
  package.json        # Dependencies: obsidian, typescript, esbuild, @types/node
  tsconfig.json       # strict: true, target ES2018, moduleResolution node
  esbuild.config.mjs  # CJS bundle, externalizes obsidian + electron
  eslint.config.mjs   # eslint-plugin-obsidianmd + eslint-comments flat config
  LICENSE             # MIT with current year
  README.md           # Minimal description
  .gitignore          # node_modules, main.js, data.json
```

## Procedure

1. **Ask the user** for:
   - Plugin ID (alphanumeric + dashes, no "obsidian", no "plugin" suffix)
   - Plugin name (no "Obsidian", no "Plugin" suffix)
   - Author name
   - Description (no "Obsidian", no "This plugin", must end with `. ? ! )`, under 250 chars)
   - Author URL (optional)
   - Desktop only? (default: false)

2. **Validate inputs** against Obsidian automated review rules:
   - ID: `/^[a-z0-9-]+$/`, not containing "obsidian", not ending with "plugin"
   - Name: not containing "Obsidian", not ending with "Plugin"
   - Description: not starting with "This plugin", not containing "Obsidian", ending with `.?!)`

3. **Create all files** using the templates below.

4. **Run** `npm install` to install dependencies.

5. **Verify** `npx tsc --noEmit` passes with zero errors.

## Templates

### manifest.json
```json
{
  "id": "{{ID}}",
  "name": "{{NAME}}",
  "version": "1.0.0",
  "minAppVersion": "1.0.0",
  "description": "{{DESCRIPTION}}",
  "author": "{{AUTHOR}}",
  "authorUrl": "{{AUTHOR_URL}}",
  "isDesktopOnly": {{IS_DESKTOP_ONLY}}
}
```

### package.json
```json
{
  "name": "{{ID}}",
  "version": "1.0.0",
  "description": "{{DESCRIPTION}}",
  "main": "main.js",
  "scripts": {
    "dev": "node esbuild.config.mjs",
    "build": "tsc -noEmit -skipLibCheck && node esbuild.config.mjs production",
    "lint": "eslint src/ package.json"
  },
  "devDependencies": {
    "@eslint-community/eslint-plugin-eslint-comments": "^4.0.0",
    "@eslint/js": "^9.0.0",
    "@types/node": "^22.0.0",
    "esbuild": "^0.24.0",
    "eslint": "^9.0.0",
    "eslint-plugin-obsidianmd": "latest",
    "obsidian": "latest",
    "typescript": "^5.5.0",
    "typescript-eslint": "^8.0.0"
  }
}
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "inlineSourceMap": true,
    "inlineSources": true,
    "module": "ESNext",
    "target": "ES2018",
    "allowJs": true,
    "noImplicitAny": true,
    "moduleResolution": "node",
    "importHelpers": true,
    "isolatedModules": true,
    "strictNullChecks": true,
    "strict": true,
    "lib": ["DOM", "ES2018", "ES2021.String"]
  },
  "include": ["src/**/*.ts"]
}
```

### esbuild.config.mjs
```javascript
import esbuild from "esbuild";
import process from "process";
import { builtinModules as builtins } from "node:module";

const prod = process.argv[2] === "production";

esbuild.build({
  entryPoints: ["src/main.ts"],
  bundle: true,
  external: [
    "obsidian",
    "electron",
    "@codemirror/autocomplete",
    "@codemirror/collab",
    "@codemirror/commands",
    "@codemirror/language",
    "@codemirror/lint",
    "@codemirror/search",
    "@codemirror/state",
    "@codemirror/view",
    "@lezer/common",
    "@lezer/highlight",
    "@lezer/lr",
    ...builtins,
  ],
  format: "cjs",
  target: "es2018",
  logLevel: "info",
  sourcemap: prod ? false : "inline",
  treeShaking: true,
  outfile: "main.js",
  minify: prod,
}).catch(() => process.exit(1));
```

### src/main.ts
```typescript
import { Plugin } from 'obsidian';

export default class {{CLASS_NAME}} extends Plugin {
  onload(): void {
    // Plugin initialization here
  }

  onunload(): void {
    // Cleanup here (Obsidian handles leaf detachment automatically)
  }
}
```

### .gitignore
```
node_modules/
main.js
data.json
```

### eslint.config.mjs (ESLint 9+ flat config)

The eslint-comments block mirrors checks that Obsidian's review platform adds on top of the obsidianmd recommended config.

```javascript
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import obsidianmd from 'eslint-plugin-obsidianmd';
import comments from '@eslint-community/eslint-plugin-eslint-comments/configs';

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...obsidianmd.configs.recommended,
  comments.recommended,
  {
    rules: {
      '@eslint-community/eslint-comments/require-description': 'error',
      '@eslint-community/eslint-comments/no-restricted-disable': [
        'error',
        'obsidianmd/no-static-styles-assignment',
        'obsidianmd/ui/sentence-case',
      ],
    },
  },
  {
    languageOptions: {
      parserOptions: {
        project: './tsconfig.json',
      },
    },
  },
];
```

## Post-Scaffold

After creation, remind the user:
- Run `npm run dev` for watch mode during development
- Run `npm run build` for production build
- Run `npm run lint` to check against the automated review rules locally
- Create a GitHub release with `main.js`, `manifest.json`, and `styles.css` as individual assets
- Release tag must match version in manifest.json exactly (no `v` prefix)
- Submit the new plugin on community.obsidian.md: sign in with an Obsidian account, link GitHub, then "Plugins" > "New plugin" with the repo URL. The old PR workflow to `obsidianmd/obsidian-releases` was retired in May 2026
- Updates need no dashboard action: every new GitHub release is scanned automatically by the review system
