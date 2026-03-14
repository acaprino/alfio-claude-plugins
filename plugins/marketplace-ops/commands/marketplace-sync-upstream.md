---
description: "Sync upstream-sourced plugins with their remote repositories -- fetches latest content, compares with local, preserves local additions, and updates versions"
argument-hint: "[plugin-name] [--dry-run] [--all]"
---

# Sync Upstream Plugins

Synchronize locally-ported plugins with their upstream source repositories.

## Upstream registry

| Plugin | Skill/Command | Upstream repo | Upstream path |
|--------|--------------|---------------|---------------|
| frontend | frontend-design | anthropics/claude-code | plugins/frontend-design/skills/frontend-design/SKILL.md |
| ai-tooling | brainstorming | obra/superpowers | skills/brainstorming/SKILL.md |
| ai-tooling | writing-plans | obra/superpowers | skills/writing-plans/SKILL.md |
| ai-tooling | executing-plans | obra/superpowers | skills/executing-plans/SKILL.md |
| frontend | css-master | paulirish/dotfiles | agents/paulirish-skills/skills/modern-css/SKILL.md |
| deep-dive-analysis | deep-dive-analysis | gsd-build/get-shit-done | agents/gsd-codebase-mapper.md |

## Sync procedure

For each upstream mapping (or the specific one requested):

### 1. Fetch upstream content

```bash
gh api repos/<owner>/<repo>/contents/<path> --jq '.content' | base64 -d > /tmp/upstream_content.md
```

### 2. Read local file

Read the corresponding local file for comparison.

### 3. Diff and merge

- Preserve local additions: source attribution lines, plugin-specific sections
- Replace `superpowers:` skill references with `ai-tooling:` equivalents
- Replace `superpowers:using-git-worktrees` with generic guidance about git worktrees
- Replace `superpowers:finishing-a-development-branch` with generic branch completion guidance
- Replace `superpowers:subagent-driven-development` with generic sub-agent guidance
- Keep `docs/plans/` path (not upstream's `docs/superpowers/plans/`)

### 4. Apply changes

If changes detected:
- Write updated local file
- Bump plugin version in marketplace.json (patch bump)
- Bump metadata.version in marketplace.json

### 5. Report

Show diff summary for each synced file with change count.

## Flags

- `--dry-run`: Show what would change without writing files
- `--all`: Sync all upstream plugins (default syncs only the specified one)
- No arguments: interactive - list upstream plugins and ask which to sync
