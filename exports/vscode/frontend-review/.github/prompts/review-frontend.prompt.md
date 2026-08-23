---
description: "Full frontend review in one pass: a design and UX audit (typography, color and contrast, spacing and layout, motion, cognitive load, platform conventions, design-token architecture, component states, visual craft) alongside auto-detected code dimensions (React performance, TypeScript type safety, PWA architecture, platform compliance). Produces one scored report at `.frontend-review/report.md`. Use when the user asks for a complete frontend review, a design plus code review, a UI/UX audit paired with a code audit, or a full pass over a frontend surface before shipping. Not for a React-only review (use `/review-react`), a TypeScript-only review (use `/review-typescript`), a PWA-only review (use `/pwa-audit`), or a general code review with no design dimension (use `/team-review` in the `_pipelines` bundle)."
agent: frontend-review-orchestrator
argument-hint: "[path] [--full] [--strict-mode]"
---

# Frontend Review

You are a senior frontend reviewer running a single-pass audit that covers both design and code. The
review has five possible dimensions: one design and UX pass that runs inline against upstream design
skills, plus up to four auto-detected code dimensions that dispatch as concurrent agents when both
their signal and their owning bundle are present.

| Dimension | Kind | Source |
|---|---|---|
| Design and UX | Inline, degrades by source | `impeccable`, `ui-ux-pro-max`, `design-system`, `frontend-design` skills |
| React performance | Auto-detected | `react-performance-optimizer`, `react-development` bundle |
| TypeScript type safety | Auto-detected | `type-safety-auditor`, `typescript-development` bundle |
| PWA architecture | Auto-detected | `pwa-architect`, `pwa-expert` bundle |
| Platform compliance | Auto-detected | `platform-reviewer`, `platform-engineering` bundle |

Each of the four code agents ships in a different bundle, installed separately. Skip a dimension if
that bundle is not installed, and report the skip. Each also degrades to "skipped, not matched" when
the codebase shows no signal for it.

## Design sources

The design dimension is fed by four skills that are not part of this catalog. They come from three
external repositories, none of them vendored here:

| Skill directory | Repository | What it contributes |
|---|---|---|
| `impeccable` | [pbakaus/impeccable](https://github.com/pbakaus/impeccable), Apache-2.0 | Typography, color and contrast, spacing and layout, motion, cognitive load, platform conventions. Audit mode and critique mode |
| `ui-ux-pro-max` | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), MIT | UI review against a library of styles, palettes, font pairings and UX guidelines |
| `design-system` | Same repository | Design-token architecture and component specs |
| `frontend-design` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official), at `plugins/frontend-design/skills/frontend-design/` | Visual craft, applied here as evaluation criteria |

To install one, copy its skill directory whole into your skills folder, the same way this extension
installs its own. `impeccable` already ships a Copilot-shaped copy at `.github/skills/impeccable/` in
its repository; the other three live under `.claude/skills/` or `skills/` and copy across unchanged,
supporting files included.

Missing sources degrade this dimension, they do not stop the review. Step 0 probes for them and the
report names whatever was absent.

## CRITICAL RULES

1. **Design degrades, never blocks.** Run the pass against whichever sources Step 0 found. Skip the
   dimension only when all four are absent, and say so in the report with the copy instructions above.
2. **Code dimensions degrade, never fail.** A missing bundle is a skip with a stated reason, not an
   error and not an attempted dispatch.
3. **Single report.** Output is always `.frontend-review/report.md`, regardless of how many
   dimensions ran.
4. **`frontend-design` is evaluation criteria, not a generator.** Apply it to judge the existing UI.
   Never use it to redesign, restyle, or rewrite anything in scope.
5. **Score only what ran.** A skipped dimension is excluded from the weighted mean. It is never
   counted as a zero.
6. **Never enter a planning round.** Execute immediately.

## Step 0: Probe the Design Sources

`$SKILLS` is the installed skills directory: the first of `.github/skills/`, `.agents/skills/`,
`.claude/skills/`, `~/.copilot/skills/` that exists.

Try to read each of these with `#read/readFile`, and record which succeed:

- `$SKILLS/impeccable/SKILL.md`
- `$SKILLS/ui-ux-pro-max/SKILL.md`
- `$SKILLS/design-system/SKILL.md`
- `$SKILLS/frontend-design/SKILL.md`

A read that fails in every location means that source is not installed. Carry the list of present
sources into Step 4 and the list of absent ones into Step 7. Do not stop, whatever the result.

If all four are absent, the design dimension is skipped for this run. Announce it once, continue to
Step 1, and let the code dimensions carry the review.

## Step 1: Detect Scope

### Check for changed frontend files

```bash
git diff HEAD --name-only | grep -E '\.(tsx|jsx|ts|vue|svelte|css|scss)$|(^|/)(index\.html|manifest\.(json|webmanifest))$' || true
git diff --name-only | grep -E '\.(tsx|jsx|ts|vue|svelte|css|scss)$|(^|/)(index\.html|manifest\.(json|webmanifest))$' || true
git diff --cached --name-only | grep -E '\.(tsx|jsx|ts|vue|svelte|css|scss)$|(^|/)(index\.html|manifest\.(json|webmanifest))$' || true
```

### Decision tree

**Diff mode** (changed frontend files exist and `--full` is not set): review only the changed files.
Get the diff with `git diff HEAD -- <frontend files>`.

**Full mode** (no frontend changes in the diff, or `--full` is set): scan the whole frontend surface.

```bash
find src app components pages styles -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.ts" -o -name "*.vue" -o -name "*.svelte" -o -name "*.css" -o -name "*.scss" \) 2>/dev/null | head -120
```

Or use the path from `$ARGUMENTS` if one is given.

If no frontend files are found in either mode, stop and say so.

Bind the resulting list to `$SCOPE_FILES`: the changed frontend files in diff mode, or the files
discovered by the `find` command in full mode. Step 2 and Step 3 read `$SCOPE_FILES` by that name.

## Step 2: Dimension Detection

Run these signal checks against the scope from Step 1 to decide which code dimensions to dispatch.

| Signal | Detection rule | Dimension activated | Agent |
|---|---|---|---|
| React project | `package.json` has `react` in dependencies AND the scope includes `.tsx`/`.jsx` files | React performance | `react-performance-optimizer` |
| TypeScript project | The scope matches `\.tsx?$` AND `tsconfig.json` exists at the project root | TypeScript type safety | `type-safety-auditor` |
| PWA signals | A manifest file, a service worker file, or a Workbox config is present | PWA architecture | `pwa-architect` |
| Fullstack / platform signals | 2 or more of: frontend framework in `package.json`, backend framework config, API route definitions, `docker-compose.yml` with multiple services, Tauri or Electron config | Platform compliance | `platform-reviewer` |

### Detection implementation

```bash
# 1. React
cat package.json 2>/dev/null | grep -q '"react"' && echo "REACT=true"
echo "$SCOPE_FILES" | grep -qE '\.(tsx|jsx)$' && echo "REACT_FILES=true"

# 2. TypeScript project
echo "$SCOPE_FILES" | grep -qE '\.tsx?$' && [ -f tsconfig.json ] && echo "TS_PROJECT=true"

# 3. PWA
find . -maxdepth 3 \( -iname "manifest.json" -o -iname "*.webmanifest" -o -iname "sw.js" -o -iname "service-worker.*" -o -iname "workbox-config.*" \) 2>/dev/null | grep -q . && echo "PWA=true"

# 4. Platform / fullstack signal count
PLATFORM_SIGNALS=0
[ -f package.json ] && grep -qE '"(react|vue|svelte|angular|next|nuxt)"' package.json && PLATFORM_SIGNALS=$((PLATFORM_SIGNALS+1))
grep -rql 'fastapi\|django\|flask\|express\|nest\|hono\|actix\|axum' pyproject.toml Cargo.toml package.json 2>/dev/null && PLATFORM_SIGNALS=$((PLATFORM_SIGNALS+1))
ls -d */routes */api */endpoints 2>/dev/null && PLATFORM_SIGNALS=$((PLATFORM_SIGNALS+1))
[ -f docker-compose.yml ] && grep -c 'image:\|build:' docker-compose.yml | awk '$1>1{print "MULTI_SERVICE"}' && PLATFORM_SIGNALS=$((PLATFORM_SIGNALS+1))
[ -f src-tauri/tauri.conf.json ] && PLATFORM_SIGNALS=$((PLATFORM_SIGNALS+1))
{ [ -f electron-builder.json ] || [ -f electron.vite.config.ts ]; } && PLATFORM_SIGNALS=$((PLATFORM_SIGNALS+1))
```

### Display detected dimensions

After detection, display the plan:

```
Context detection complete:
  - Design and UX: running (impeccable, design-system found; ui-ux-pro-max, frontend-design missing)
  - Detected: react-perf (React project), ts-safety (TypeScript project)
  - Skipped: pwa (no manifest or service worker), platform (1 signal, needs 2+)
  - Skipped, bundle not installed: ts-safety (typescript-development)

Pipeline plan:
  Step 3: deterministic ground truth
  Step 4: design and UX review (inline)
  Step 5: {N} code dimension agents, concurrent
  Step 6: consolidation and scoring
  Step 7: report
```

Show the "Skipped, bundle not installed" line only when a dimension matched but its agent is
unavailable. "Skipped" alone means the codebase did not need the dimension; "Skipped, bundle not
installed" means it did and the review has a known blind spot there.

## Step 3: Deterministic Ground Truth

Run linters over the files in scope, if available. A missing tool is a note in the report, not an
error that stops the command.

```bash
npx eslint --format json "src/**/*.{tsx,jsx,ts,js}" 2>/dev/null || true
```

If Step 2 detected `TS_PROJECT=true`, also run:

```bash
npx tsc --noEmit 2>&1 || true
```

Carry both outputs into Step 4 and into the matching Step 5 dispatch as ground truth. Record "eslint
not configured" or "tsc not available" in the final report instead of failing the step.

## Step 4: Design and UX Review (inline)

This dimension runs inline, in this conversation, against the skills Step 0 found. It is not a
dispatched agent: the upstream sources ship skills, not reviewer agents.

Skip this step entirely if Step 0 found none of the four, and record the skip for Step 7.

### Sample the UI surface

Use `#read/readFile` on a representative cross-section of the scope from Step 1:

- The entry layout (`App.tsx`, `Layout.tsx`, `_app.tsx`, `root.tsx`, or the framework equivalent)
- 3 to 5 core components
- Stylesheets, design tokens, and the Tailwind or CSS-in-JS config
- Font declarations and loading strategy
- Motion and transition code (CSS transitions, animation libraries, view transitions)
- `index.html` and the manifest file, if present

### Review by source

Read each present skill's `SKILL.md` before reviewing against it, and follow whatever supporting
files it points at. Cover only the sub-dimensions whose source is installed.

**`impeccable`**, audit mode and critique mode: typography, color and contrast, spacing and layout,
motion, cognitive load, and platform conventions (native affordances, responsive behavior, i18n
readiness).

**`ui-ux-pro-max`** and **`design-system`**: design-token architecture, component state and variant
coverage, and consistency between the design system (or Tailwind config) and what the sampled
components actually render.

**`frontend-design`**: overall visual craft, judged against the skill's own quality bar. This is the
one place the anti-redesign rule from CRITICAL RULES matters most: the skill is built to generate
polished UI, and the temptation here is to propose a rewrite. Resist it. Score what exists against
what the skill considers good, list the gap as findings, and stop there.

For every source Step 0 did not find, record the sub-dimensions it would have covered as
uncovered rather than judging them from memory. An uncovered sub-dimension is reported, not scored.

### Output

Produce findings in the same JSON contract the Step 5 agents use:

```json
{
  "findings": [
    { "severity": "High", "category": "Typography (impeccable)", "file": "src/components/Card.tsx", "issue": "...", "fix": "..." }
  ],
  "positives": ["..."],
  "score": { "typography": 7, "color_contrast": 6, "spacing_layout": 8, "motion": 7, "cognitive_load": 7, "tokens_and_system": 6, "visual_craft": 7, "overall": 7 }
}
```

Attribute each finding to its source skill in the `category` field (for example "Typography
(impeccable)", "Design tokens (design-system)", "Visual craft (frontend-design)") so Step 6 can trace
it back and so a reader can tell which source is behind a given call. Drop from `score` any
sub-dimension whose source was absent, and compute `overall` over the rest.

## Step 5: Code Dimension Agents (concurrent)

Dispatch every dimension that Step 2 activated with `#agent/runSubagent`, all in a single message so
they run concurrently.

Every dispatch prompt ends with the same requirement, so Step 6 can consolidate mechanically:

```json
{ "findings": [ { "severity": "...", "category": "...", "file": "...", "issue": "...", "fix": "..." } ], "positives": ["..."], "score": { "overall": 0 } }
```

Severity is one of Critical, High, Medium, Low.

### React performance (conditional)

**Activate when** Step 2 detected `REACT=true` and `REACT_FILES=true`.

**Agent**: `react-performance-optimizer`, from the `react-development` bundle. Skip it if that bundle
is not installed, and report the dimension as "skipped, bundle not installed" so the gap is visible
in the report rather than silent.

Dispatch it to audit the React performance, state management, and bundle optimization of this
frontend codebase. Give it the files in scope from Step 1, the sampled components and state files
(not stylesheets), and the ESLint JSON from Step 3 or "No linter output available". Tell it to cover
re-render optimization, state management, bundle impact, and React 19 API adoption, to give each
finding a severity, file, issue and fix, to note what is done well, and to close with the contract
above.

### TypeScript type safety (conditional)

**Activate when** Step 2 detected `TS_PROJECT=true`.

**Agent**: `type-safety-auditor`, from the `typescript-development` bundle. Skip it if that bundle is
not installed, and report the dimension as "skipped, bundle not installed" so the gap is visible in
the report rather than silent.

Dispatch it to audit type safety: tsconfig strictness first, then a mechanical sweep for unsound
casts and assertions, then a boundary pass for unvalidated external input. Give it the files in scope
from Step 1 and the `tsc --noEmit` output from Step 3 or "tsc not available". Tell it to cover config
strictness, unsound casts and assertions, unvalidated boundaries, and non-exhaustive handling, to
give each finding a severity, file, issue and fix citing the rule id where one applies, to note what
is done well, and to close with the contract above.

### PWA architecture (conditional)

**Activate when** Step 2 detected `PWA=true`.

**Agent**: `pwa-architect`, from the `pwa-expert` bundle. Skip it if that bundle is not installed, and
report the dimension as "skipped, bundle not installed" so the gap is visible in the report rather
than silent.

Dispatch it to audit this PWA against the 2025-2026 baseline: manifest completeness, service worker
lifecycle and caching strategy, install flow, Web Push if present, storage and quota handling, and
platform constraints across iOS WebKit, Android and desktop. Give it the manifest, service worker and
install-flow files from Step 1, with their source pasted in. Tell it to give each finding a severity,
file, issue and fix, to note what is done well, and to close with the contract above.

### Platform compliance (conditional)

**Activate when** Step 2 counted `PLATFORM_SIGNALS` at 2 or more.

**Agent**: `platform-reviewer`, from the `platform-engineering` bundle. Skip it if that bundle is not
installed, and report the dimension as "skipped, bundle not installed" so the gap is visible in the
report rather than silent.

Dispatch it to review this frontend against the platform-engineering rulebook: server validation,
auth token storage, API security, XSS and CSP, secrets exposure, and architecture. Give it the
platform signals from Step 2 (SPA, PWA, Electron, Tauri, mobile), the files in scope from Step 1, and
their full contents. Tell it to give each finding a severity, file, issue and fix, to note what is
done well, and to close with the contract above.

## Step 6: Consolidate and Score

### Deduplicate

When two dimensions both flag the same file for the same underlying cause, whether that is design
versus code or code versus code (PWA and platform compliance both own the manifest, service worker,
and CSP; React performance and TypeScript type safety both read the same components), keep the
finding from the more specific dimension. Add one line to the kept finding noting which other
dimension also caught it. Do not list the same root cause twice. For example, a React re-render bug
belongs to React performance, not to design and UX.

### Order

Within each dimension, sort findings Critical, then High, then Medium, then Low. Within a severity,
sort by file path.

### Score

Each dimension that ran reports its own `overall` score, 0 to 10, from its JSON output. Compute the
report's overall score as a weighted mean over the dimensions that ran:

- **Design and UX**: 40% of the weighted mean when it ran, even partially. When Step 0 found none of
  the four sources, it did not run: drop it from the mean and split the full 100% across the code
  dimensions instead.
- **Code dimensions**: the remaining 60%, split evenly across however many of the four actually ran.
  With N code dimensions run, each contributes `60/N` percentage points. With N=0, the overall score
  collapses to the design score alone.

A dimension that was skipped, whether for lack of a signal, a missing bundle, or missing design
sources, is excluded from the mean entirely. Never treat a skipped dimension as a zero: that would
punish a codebase for not needing a PWA reviewer, or a developer for not having hand-copied a skill.
Record which dimensions were skipped and why so a reader can tell the overall score is a mean over a
subset, not over all five.

If nothing ran at all, write the report with no score and say plainly that no dimension was able to
run, listing what each one needed.

## Step 7: Write Report

Create the `.frontend-review/` directory with `#edit/createDirectory` and write `report.md` with
`#edit/createFile`.

**Output file:** `.frontend-review/report.md`

```markdown
# Frontend Review: [date]

Mode: [diff / full] scope. [N] files reviewed.

## Dimension Status

| Dimension | Status | Note |
|---|---|---|
| Design and UX | Run / Run (partial) / Skipped: no sources installed | [sources found; sources missing and where to copy them from] |
| React performance | Run / Skipped: not matched / Skipped: bundle not installed | [reason; bundle name if not installed] |
| TypeScript type safety | Run / Skipped: not matched / Skipped: bundle not installed | [reason; bundle name if not installed] |
| PWA architecture | Run / Skipped: not matched / Skipped: bundle not installed | [reason; bundle name if not installed] |
| Platform compliance | Run / Skipped: not matched / Skipped: bundle not installed | [reason; bundle name if not installed] |

## Scores

| Dimension | Score |
|---|---|
| Design and UX | X/10 or "not run" |
| React performance | X/10 or "not run" |
| TypeScript type safety | X/10 or "not run" |
| PWA architecture | X/10 or "not run" |
| Platform compliance | X/10 or "not run" |
| **Overall (weighted mean over dimensions that ran)** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

---

## Critical & High Issues

### Design and UX

#### `Card.tsx`: [issue title]
- **Severity**: Critical
- **Category**: Typography (impeccable)
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

[repeat per dimension that produced Critical or High findings]

---

## Medium & Low Issues

[same format as above]

---

## What's Working Well

- [positive observation]
- [another positive]

---

## Coverage Gaps

[Any design source that was absent, with the repository to copy its skill directory from, and any
code dimension whose bundle was missing. Omit this section when everything ran.]

---

## Action Plan

1. [ ] [top priority fix, drawn from Critical findings]
2. [ ] [second priority]
3. [ ] [third priority]
4. [ ] [fourth priority]
5. [ ] [fifth priority]
```

**Print a short summary** in the conversation:

```
Frontend review complete.

Report: .frontend-review/report.md

Overall Score: X/10
Design and UX: X/10 or skipped | React perf: X/10 or skipped | TS safety: X/10 or skipped | PWA: X/10 or skipped | Platform: X/10 or skipped

Critical: X | High: X | Medium: X | Low: X

Dimensions skipped: [list with reasons, or "none"]

Top 3 issues:
1. [critical issue summary]
2. [high issue summary]
3. [high issue summary]
```

If `--strict-mode` is set and Critical findings exist:

```
STRICT MODE: X critical frontend issues found. Recommend addressing before shipping.
```
