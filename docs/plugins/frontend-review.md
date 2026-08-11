# Frontend Review Plugin

> Full frontend review in one pass: an always-on design and UX audit driven by the four design skills from the three upstream plugins, paired with up to four auto-detected code dimensions (React performance, TypeScript type safety, PWA architecture, platform compliance). Produces one scored report per run and vendors no design content of its own.

## Prerequisites

Three upstream design plugins back the design and UX dimension. All three are hard, qualified dependencies with unconditional stop-and-install phrasing: Step 0 of the command loads all four skills before anything else runs, and the command stops without a partial design pass if any load fails.

```bash
claude plugin marketplace add pbakaus/impeccable
claude plugin install impeccable@impeccable
claude plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
claude plugin install ui-ux-pro-max@ui-ux-pro-max-skill
claude plugin install frontend-design@claude-plugins-official
```

| Dependency | Provides | Referenced as |
|---|---|---|
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (plugin 4.0.4, Apache-2.0) | `audit` mode (accessibility, performance, responsive checks) and `critique` mode (UX heuristic scoring): typography, color and contrast, spacing and layout, motion, cognitive load, platform conventions | `impeccable:impeccable` |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (plugin 2.11.0, MIT) | UI review against a style/palette/font-pairing library, plus design-token architecture and component state and variant coverage | `ui-ux-pro-max:ui-ux-pro-max`, `ui-ux-pro-max:design-system` |
| `frontend-design` (Anthropic, `claude-plugins-official` marketplace, Apache-2.0) | Visual craft evaluation criteria, applied to judge the existing UI, never to generate or redesign it | `frontend-design:frontend-design` |

`impeccable` also ships four support agents and a hooks file, and `ui-ux-pro-max` ships five more skills (`design`, `ui-styling`, `brand`, `banner-design`, `slides`); this plugin loads none of them.

The four code dimensions below are bare, local hard `dependencies` instead: `react-development`, `typescript-development`, `pwa-expert`, `platform-engineering`. The marketplace installs them with this plugin, so each is skipped only when the codebase shows no signal for it. The design dimension needs its own install-or-stop gate because its three plugins come from other marketplaces and the user installs them by hand.

---

## Commands

### `/frontend-review:review-frontend`

```
/frontend-review:review-frontend [path] [--full] [--strict-mode]
```

**Scope detection:**
- **Diff mode** (default): reviews only changed frontend files (`.tsx .jsx .ts .vue .svelte .css .scss`, plus `index.html` and manifest files) from `git diff`
- **Full mode**: scans the whole frontend surface (`src/ app/ components/ pages/ styles/`, or the given `path`) when no frontend changes exist in the diff, or `--full` is set

`--strict-mode` prints an explicit warning line if any Critical findings exist, on top of the normal report.

**Dimensions:**

| Dimension | Kind | Source |
|---|---|---|
| Design and UX | Always-on, inline | `impeccable`, `ui-ux-pro-max`, `frontend-design` |
| React performance | Auto-detected | `react-development` plugin |
| TypeScript type safety | Auto-detected | `typescript-development` plugin |
| PWA architecture | Auto-detected | `pwa-expert` plugin |
| Platform compliance | Auto-detected | `platform-engineering` plugin |

Design and UX runs inline in the command's own context, against the four loaded skills; it is not a spawned agent, because the upstream plugins ship skills rather than reviewer agents. The four code dimensions spawn as parallel agents, one per matched signal, only when both the signal and the owning plugin are present.

**Activation, per code dimension:**

| Plugin | Backs | Skipped: not matched |
|---|---|---|
| `react-development` | React performance | No `react` dependency in `package.json`, or no `.tsx`/`.jsx` files in scope |
| `typescript-development` | TypeScript type safety | No `.tsx?` files in scope, or no `tsconfig.json` at the project root |
| `pwa-expert` | PWA architecture | No manifest, service worker, or Workbox config found |
| `platform-engineering` | Platform compliance | Fewer than 2 of the fullstack/platform signals present |

There is one skip reason and it is always about the codebase: the dimension did not match. A missing plugin is not a reason, because all four are hard dependencies. A spawn failing with "Agent type not found" means a broken install, and the command stops and reports it rather than scoring a partial review.

**Scoring model:**

Each dimension that ran reports its own `overall` score, 0 to 10. The report's overall score is a weighted mean over the dimensions that ran, not over all five:

- **Design and UX**: 40% of the weighted mean. It always contributes, since it is hard-gated: if it did not run, the command already stopped at Step 0.
- **Code dimensions**: the remaining 60%, split evenly across however many of the four actually ran. With `N` code dimensions run, each contributes `60/N` percentage points. With `N=0`, the overall score collapses to the design score alone.

A skipped dimension, whether skipped for lack of a signal or for a missing plugin, is excluded from the mean entirely. It is never treated as a zero.

**Report:** `.frontend-review/report.md`, always at that path regardless of how many dimensions ran:

- Header with date and mode (diff or full), and file count
- Dimension status table (Run / Skipped: not matched, with the reason)
- Scores table per dimension plus the weighted overall
- Findings grouped Critical/High then Medium/Low, each with a `- [ ] Fixed` checkbox
- `## What's Working Well`
- `## Action Plan` with the top 5 fixes

A console summary prints alongside the file: overall score, per-dimension scores or skip status, severity counts, skipped dimensions with reasons, and the top 3 issues.

---

## Upstream pinning

Bindings verified against `impeccable` 4.0.4, `ui-ux-pro-max` 2.11.0, and the `frontend-design` skill on the official `claude-plugins-official` marketplace, as of 2026-08-05. A rename or skill move on any of the three breaks the Step 0 load, surfaced as "not installed" rather than as a clear upstream-drift error. Re-verify these three bindings on the `custom-plugin-refresh` cadence rather than waiting for a user report.

---

**Related:** [react-development](react-development.md) (React performance dimension source) | [typescript-development](typescript-development.md) (TypeScript type safety dimension source) | [pwa-expert](pwa-expert.md) (PWA architecture dimension source) | [platform-engineering](platform-engineering.md) (platform compliance dimension source) | [senior-review](senior-review.md) (general code review with no design dimension; see `/senior-review:code-review`)
