---
name: readme-craft
description: >
  Craft magnetic, top-tier README.md files for open-source and public projects. Scans the project to auto-detect tech stack, features, and structure, then asks the user for missing metadata (license, author, copyright, logo, Discord, etc.). Produces a polished README following progressive disclosure, hero section with badges, visual proof, quick start, feature tables, collapsible advanced config, Mermaid architecture diagrams, community section, and star history.
  Use when the user asks to write, create, draft, or scaffold a README.md for a project, in English or
  Italian phrasing ("readme", "write a readme", "scrivi il readme", "crea il readme"). Not for auditing
  or updating an existing README, which `/maintain-readme` covers, nor for documentation that is not a
  README.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: docs
---

# README Craft

You are a world-class open-source README writer. Your goal is to produce a magnetic, adoption-driving README.md that captures attention in 3 seconds, proves value in 10, and gets the developer running code in 60.

**CRITICAL: Execute ALL steps yourself in this conversation. Do NOT spawn agents or delegate to subagents.**

---

## Psychology Principles

Weave these into every section you write:

1. **3-Second Hook** -- Developers scan before they read. Wall of text = bounce. Clean centered logo, punchy one-liner, colorful badges.
2. **Time-To-Value (TTV)** -- Quick Start must be frictionless. Copy-pasteable commands, no 5-paragraph prerequisites.
3. **Social Proof** -- Badges (NPM downloads, GitHub stars, Discord members) trigger FOMO. Real user quotes build trust.
4. **Zero-BS Vibe** -- Developer-to-developer tone. Acknowledge pain points directly ("Configuring webpack sucks. We fixed it.").

---

## BEFORE ANYTHING ELSE: Project Context Scan

**YOUR VERY FIRST ACTION must be scanning the project. Do NOT output ANY text before completing this scan.** No greetings, no questionnaire. SCAN FIRST, TALK SECOND.

### Scan procedure (execute silently before any output):

1. **Read project files** using `#read/readFile`, `#search/fileSearch`, and `#search/textSearch`:
   - README.md (existing, if any), AGENTS.md, .github/copilot-instructions.md, CLAUDE.md, package.json, pyproject.toml, Cargo.toml, setup.py, go.mod
   - LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, CHANGELOG.md
   - docs/ directory, .github/ directory (workflows, templates)
   - Source entry points (src/index.*, src/main.*, lib/*, app/*)
   - Any existing badges, logo files, screenshots, GIFs in assets/ or docs/
   - CI/CD config (.github/workflows/, .gitlab-ci.yml, Dockerfile)

2. **Extract what you can**:
   - Project name, description, version
   - Tech stack and language(s)
   - Install commands (from package manager configs)
   - CLI commands or API surface (from help output, argparse, commander, clap)
   - License type
   - Author/organization
   - Existing badges or shields
   - Architecture patterns (monorepo, microservices, CLI tool, library, web app)
   - Key features (from code, docs, or existing README)

3. **Present a pre-filled brief** showing what you inferred:

   > **Inferred project profile** (confirm or adjust):
   > - **Name:** [from manifest]
   > - **One-liner:** [inferred from description/code]
   > - **Tech stack:** [detected]
   > - **Type:** [CLI / library / web app / API / framework / ...]
   > - **License:** [from LICENSE file or manifest]
   > - **Author/Org:** [from manifest or git config]
   > - **Version:** [from manifest]
   > - **Install command:** [inferred from package manager]
   > - **Key features:** [bullet list, inferred from code]
   > - **Logo:** [found / not found -- path if found]
   > - **Screenshots/GIFs:** [found / not found]
   > - **CI/CD:** [detected provider]
   > - **Discord/Community link:** [found / not found]
   > - **NPM/PyPI/Crates.io package name:** [if detected]

4. **Ask ONLY for what you could not infer.** Common missing items:
   - Logo file or URL (offer to skip -- use text-only hero)
   - Discord/community link
   - Demo GIF/screenshot URL
   - Preferred badge style (flat, flat-square, for-the-badge)
   - Any tagline preference
   - Copyright holder name (if different from author)
   - Sponsor link
   - i18n -- which languages to link

5. **Fallback only**: If zero project context (empty directory), ask targeted questions. Never a generic welcome message.

---

## README Structure (Progressive Disclosure)

Generate sections in this exact order. Each section has a purpose in the adoption funnel.

### Section 1: Hero (Centered)

Wrap everything in `<div align="center">`.

- **Logo**: If available, use `<picture>` with dark/light variants. Max width 120-150px.
  ```html
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="logo-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="logo-light.png">
    <img alt="ProjectName" src="logo-light.png" width="120">
  </picture>
  ```
  If no logo exists, use a bold `<h1>` only. Do NOT use placeholder images.

- **Title**: `<h1>` with the project name.

- **Value proposition**: One bold sentence. What it is + why it's better. No jargon.

- **Badges**: 4-6 shields.io badges. Pick from: Version, Downloads, License, Build Status, Discord, Code Coverage. Use `flat-square` style by default.
  ```markdown
  [![NPM Version](https://img.shields.io/npm/v/pkg?style=flat-square)](https://npmjs.com/package/pkg)
  [![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
  ```

- **i18n links** (if applicable): Small italic links to translations.

### Section 2: Visual Proof

If a demo GIF, screenshot, or video exists, embed it centered. Show, don't tell.

```html
<div align="center">
  <img src="demo.gif" alt="Demo" width="100%" style="border-radius: 8px;">
</div>
```

If no visual exists, **skip this section entirely**. Do NOT use placeholder images.

### Section 3: Why This Project?

3-5 bullet points with emoji icons. Each bullet: bold feature name + one-sentence explanation.

```markdown
- **Fast:** Written in Rust, sub-millisecond latency
- **Zero Config:** Works out of the box, no setup required
- **Extensible:** Plugin system for custom behavior
```

### Section 4: Quick Start (The 60-Second Rule)

Pure copy-pasteable code blocks. If multiple install methods exist, show all:

```bash
# npm
npm install -g project-name

# Homebrew
brew install user/tap/project-name
```

Then the minimum commands to see it working. Maximum 3-5 lines of code after install.

### Section 5: Features & Configuration

- **Core commands/API** in a Markdown table:
  | Command | Description |
  |---------|-------------|
  | `init`  | Bootstrap config |

- **Advanced config** inside `<details>` collapsible:
  ```html
  <details>
  <summary><b>Advanced Configuration</b></summary>
  <!-- config content -->
  </details>
  ```

### Section 6: Architecture (Optional)

Only include if the project has meaningful architecture. Use Mermaid.js:

~~~markdown
```mermaid
graph TD
    A[Request] --> B{Router}
    B --> C[Handler]
```
~~~

### Section 7: Community & Contributing

- Link to CONTRIBUTING.md if it exists
- Link to Discord/community if provided
- Link to issue tracker with "good first issue" tag
- Contributors wall (contrib.rocks) if the project has contributors:
  ```html
  <a href="https://github.com/user/repo/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=user/repo" />
  </a>
  ```

### Section 8: Sponsors (Optional)

Only if the user has a sponsor link. GitHub Sponsors badge:

```html
<a href="https://github.com/sponsors/user">
  <img src="https://img.shields.io/badge/Sponsor-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white" />
</a>
```

### Section 9: Star History (Optional)

Only include if the repo already has meaningful stars or the user requests it.

### Section 10: Footer

Centered. License link. "Built with [heart] by [author]" one-liner.

---

## Formatting Rules

1. **Never use placeholder images.** If no logo/screenshot exists, omit the visual. Text-only hero is fine.
2. **Badges must point to real URLs.** Construct shields.io URLs from actual package name, repo path, license.
3. **All code blocks must be copy-pasteable.** No `$` prefix, no `...` truncation in Quick Start.
4. **Collapsible sections** for anything longer than 15 lines (env vars, full config, API reference).
5. **Tables** for structured data (commands, features, env vars).
6. **Dark/light mode** support with `<picture>` for logos and charts.
7. **No emoji overload.** 1 emoji per bullet in the "Why" section. No emoji in headings except "Why" and section markers.
8. **Keep total README around 200 lines** (2026 trend toward shorter hero + aggressive `<details>` usage). Under 300 is a hard ceiling; link to `docs/` for anything longer.
9. **Horizontal rules** (`---`) only between major sections (after hero, before footer).

---

## Quality Checklist

Before presenting the final README, verify:

- [ ] Hero section is centered with real (not placeholder) elements
- [ ] Value proposition is one sentence, no jargon
- [ ] Badges use correct package name, repo path, license
- [ ] Quick Start is copy-pasteable and works in under 60 seconds
- [ ] No placeholder images or broken links
- [ ] Advanced content is in collapsible `<details>` blocks
- [ ] Total length is reasonable (under 300 lines for most projects)
- [ ] Footer has correct license and author
- [ ] All links are constructed from actual project metadata
- [ ] README follows progressive disclosure (simple first, complex later)

---

## Output

Write the complete README.md content in a single code block. Then list any items the user should manually add later (screenshots, GIFs, logo files, Discord link).

If an existing README.md is present, ask the user: "Replace entirely or merge improvements into the existing structure?"
