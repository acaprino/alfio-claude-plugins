---
description: >
  "Git worktree management -- create, list, pause, resume, remove, merge, and monitor parallel development worktrees" argument-hint: "<subcommand> [args] [--branch X] [--from Y] [--desc '...'] [--setup 'cmd'] [--no-setup] [--squash|--rebase|--pr]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Worktree Manager

Manage git worktrees for parallel development. Registry lives in `.worktrees/registry.json` (gitignored). Worktrees are created inside the project at `.worktrees/<name>/`.

## Critical Rules

- Follow this spec exactly. Never invent menus, categories, options, or workflows not defined here.
- Never ask about work type, category, or priority. These concepts do not exist in this system.
- Only ask questions explicitly scripted in each subcommand section below.
- If the user's message contains enough context, extract values directly instead of asking.

## Intent Inference

Before parsing `$ARGUMENTS` for an explicit subcommand, check if the user's natural language implies one:

| User says (examples) | Inferred subcommand |
|---|---|
| "start a new worktree", "create a worktree", "new worktree for X" | `new` |
| "show my worktrees", "list worktrees" | `list` |
| "worktree status", "how are my worktrees" | `status` |
| "pause X", "stop working on X" | `pause` |
| "resume X", "continue X", "pick up X" | `resume` |
| "remove X", "delete X worktree", "clean up X" | `rm` |
| "merge X", "land X", "finish X" | `merge` |

If intent maps to a subcommand, proceed directly with that subcommand -- no confirmation menu.

## Parse Subcommand

From `$ARGUMENTS`, extract the subcommand and its arguments:

| Subcommand | Pattern |
|---|---|
| `new` | `/wt new <name> [flags]` |
| `list` | `/wt list` |
| `status` | `/wt status` |
| `pause` | `/wt pause <name>` |
| `resume` | `/wt resume <name>` |
| `rm` | `/wt rm <name>` |
| `merge` | `/wt merge <name> [--squash\|--rebase\|--pr]` |

If no explicit subcommand AND no inferable intent from user context, show usage summary and exit.

## Initialization

On first run (no `.worktrees/` directory):

1. Create `.worktrees/` directory
2. Write `.worktrees/.gitignore` with single line: `*`
3. Detect project name from directory basename or `package.json`/`Cargo.toml`/`pyproject.toml` name field
4. Write `.worktrees/registry.json`:

```json
{
  "project": "<project-name>",
  "worktree_dir": ".worktrees",
  "default_setup": "auto",
  "worktrees": []
}
```

## Subcommand: `new <name>`

Create a new worktree for parallel development.

### Flags

- `--branch <X>` - branch name (default: `wt/<name>`)
- `--from <Y>` - base branch (default: current branch)
- `--desc "..."` - description (if omitted, ask user for a one-liner)
- `--setup "cmd"` - override setup command
- `--no-setup` - skip setup entirely

### Constraints

- Only ask for name (if not provided) and description (if no `--desc` flag).
- Never ask about work type, category, priority, or any other classification.
- If the user's message contains descriptive context (e.g. "worktree for fixing OAuth"), extract it as the description automatically instead of asking.

### Steps

1. Validate `<name>` is kebab-case, not already in registry
2. Read registry, determine paths:
   - Branch: `--branch` or `wt/<name>`
   - Base: `--from` or current branch
   - Path: `<worktree_dir>/<name>/`
3. Create worktree:
   ```bash
   git worktree add -b <branch> <path> <base>
   ```
4. If `--desc` not provided, ask user: "Brief description for this worktree:"
5. Run setup unless `--no-setup`:
   - If `--setup "cmd"` provided, run that command in the worktree directory
   - Otherwise, auto-detect setup command (see Setup Auto-detection below)
   - Show setup output, warn on failure but don't abort
6. Register in `.worktrees/registry.json`:
   ```json
   {
     "name": "<name>",
     "branch": "<branch>",
     "base": "<base>",
     "path": "<path>",
     "desc": "<description>",
     "status": "active",
     "created": "<ISO-8601 timestamp>",
     "setup_cmd": "<detected or provided command>"
   }
   ```
7. Report:
   ```
   Worktree created: <name>
     Branch: <branch> (from <base>)
     Path:   <path>
     Setup:  <setup_cmd> [ok/skipped/failed]

   To work in this worktree:
     cd <path>
   ```

### Setup Auto-detection

Check the worktree directory for lock/manifest files in this priority order (first match wins):

| File found | Command |
|---|---|
| `uv.lock` | `uv sync` |
| `Pipfile.lock` | `pipenv install` |
| `requirements.txt` | `pip install -r requirements.txt` |
| `pnpm-lock.yaml` | `pnpm install` |
| `yarn.lock` | `yarn install` |
| `package-lock.json` | `npm install` |
| `bun.lockb` | `bun install` |
| `Cargo.lock` | `cargo build` |
| `go.sum` | `go mod download` |
| `Gemfile.lock` | `bundle install` |
| `composer.lock` | `composer install` |
| Makefile with `setup` target | `make setup` |
| None found | Skip, inform user |

## Subcommand: `list`

Show compact table from registry.

```
Name            Branch              Base     Status   Created      Description
auth-refactor   wt/auth-refactor    master   active   2026-03-17   Refactoring auth middleware
fix-login       wt/fix-login        master   paused   2026-03-16   Fix OAuth login redirect bug
```

If no worktrees registered, show: "No worktrees. Create one with: /wt new <name>"

## Subcommand: `status`

Dashboard with git status per worktree. For each registered worktree:

1. Check if path exists (mark as "missing" if not)
2. Run in worktree directory:
   - `git status --porcelain` - uncommitted changes count
   - `git log --oneline @{u}..HEAD 2>/dev/null` - unpushed commits count
   - `git log --oneline HEAD..@{u} 2>/dev/null` - commits behind upstream
   - `git log -1 --format=%ar` - time since last commit

```
Worktree Status Dashboard

auth-refactor [active]
  Branch: wt/auth-refactor (from master)
  Changes: 3 modified, 1 untracked
  Commits: 5 ahead, 0 behind
  Last activity: 2 hours ago
  Desc: Refactoring auth middleware

fix-login [paused]
  Branch: wt/fix-login (from master)
  Changes: clean
  Commits: 2 ahead, 3 behind
  Last activity: 1 day ago
  Desc: Fix OAuth login redirect bug
```

## Subcommand: `pause <name>`

1. Find `<name>` in registry (error if not found)
2. Set `status` to `"paused"`
3. Save registry
4. Report: "Paused worktree: <name>"

## Subcommand: `resume <name>`

1. Find `<name>` in registry (error if not found)
2. Verify path still exists (warn if missing)
3. Set `status` to `"active"`
4. Save registry
5. Report: "Resumed worktree: <name>"

## Subcommand: `rm <name>`

1. Find `<name>` in registry (error if not found)
2. If path exists, check for uncommitted changes:
   - Run `git -C <path> status --porcelain`
   - If dirty, warn and ask for confirmation:
     ```
     Worktree '<name>' has uncommitted changes:
       M src/auth.ts
       ? src/temp.js

     1. Remove anyway (changes will be lost)
     2. Cancel
     ```
3. Remove worktree: `git worktree remove <path> --force` (if user confirmed or clean)
4. Delete branch if fully merged: `git branch -d <branch>` (use `-d` not `-D`, let git refuse if unmerged)
   - If branch not fully merged, inform user: "Branch <branch> not fully merged. Delete anyway? (git branch -D <branch>)"
5. Remove entry from registry
6. Report: "Removed worktree: <name>"

## Subcommand: `merge <name>`

Delegate to the `worktree-agent` for guided merge flow:

```
Agent:
  subagent_type: "git-worktrees:worktree-agent"
  description: "Merge worktree <name>"
  prompt: |
    Perform a guided merge for worktree '<name>'.

    Registry path: .worktrees/registry.json
    Flags from user: [--squash|--rebase|--pr or none]

    Follow the merge flow in your instructions:
    1. Read registry, find the worktree entry
    2. Check for uncommitted changes
    3. Show diff stats
    4. Check for conflicts
    5. Run /code-review on worktree changes (senior-review plugin)
    6. Recommend merge strategy based on commit count
    7. If --pr flag: delegate to /pr-review for full PR with risk assessment
    8. After merge: check if CLAUDE.md needs updating based on merged changes
    9. Offer cleanup
```

## Error Handling

- If `git worktree` command fails, show the git error message and suggest fixes
- If registry is corrupted or missing entries, offer to rebuild from `git worktree list`
- If a worktree path no longer exists, mark as "missing" in status and offer cleanup

$ARGUMENTS
