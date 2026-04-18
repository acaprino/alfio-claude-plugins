---
name: worktree-manager
description: >
  Proactive git worktree orchestration -- detects WIP state (uncommitted changes, stashes, unpushed commits) and offers to isolate work into worktrees. MUST activate BEFORE any implementation task (add, create, build, implement, develop, make, fix, refactor) when the working directory has uncommitted changes or stashes. Also provides dashboard, context recovery, multi-worktree creation, cleanup advisor, and conflict early warning across parallel development sessions. Triggers: any implementation request when WIP exists, "show my worktrees", "what am I working on", "help me manage parallel tasks", "worktree status", "coordinate my work".
  TRIGGER WHEN: before any implementation task (add, create, build, fix, refactor) when the working directory has uncommitted changes, stashes, or unpushed commits; when the user asks about worktrees, branches, or parallel development.
  DO NOT TRIGGER WHEN: the repo state is clean and the user is doing a single-file read-only task.
---

# Worktree Manager

Orchestrate parallel development through git worktrees. Proactively detect WIP state and offer isolation. Provide dashboards, context recovery, and conflict warnings.

## Proactive Trigger

Activate when session starts and working directory has WIP state. Detection:

```bash
# Uncommitted or staged changes
git status --porcelain

# Stashes
git stash list

# Unpushed commits (may fail if no upstream - that's ok)
git log --oneline @{u}..HEAD 2>/dev/null
```

If ANY of these return output, present:

```
I notice you have work in progress:
  [X modified files / Y staged files / Z stashes / N unpushed commits]

Would you like to:
  A) Move this WIP into a worktree (stash, create worktree, apply there)
  B) Continue on current branch (I'll back off)
  C) Show details first
```

### Option A - Move WIP to worktree

1. Ask for worktree name and description
2. `git stash push -m "wt-migration: <name>"`
3. Create worktree via `/wt new <name> --desc "..."` -- pass name and description directly, never prompt for category or work type
4. In the new worktree: `git stash pop`
5. Confirm: "WIP moved to worktree '<name>'. Current branch is now clean."

### Option B - Continue on current branch

Back off for the session. Do not prompt again about WIP state.

### Option C - Show details

Show full output of all three detection commands, then re-offer A/B.

## Dashboard

When asked "show my worktrees", "what am I working on", or "worktree status":

1. Read `.worktrees/registry.json`
2. For each worktree, gather:
   - `git -C <path> log --oneline <base>..<branch>` - commits ahead
   - `git -C <path> log --oneline <branch>..<base>` - commits behind base
   - `git -C <path> status --porcelain` - uncommitted changes
   - `git -C <path> log -1 --format=%ar` - last activity
3. Present:

```
Parallel Development Dashboard
==============================

[1] auth-refactor [active] - 2h ago
    Branch: wt/auth-refactor (from master)
    +5 commits, 0 behind | 3 modified files
    "Refactoring auth middleware for compliance"

[2] fix-login [paused] - 1d ago
    Branch: wt/fix-login (from master)
    +2 commits, 3 behind | clean
    "Fix OAuth login redirect bug"

Warnings:
  - fix-login is 3 commits behind master - consider rebasing
```

## Context Recovery

When user says "what am I working on" or returns after a break:

1. Show dashboard (above)
2. For the most recently active worktree, show:
   - Last 3 commit messages
   - Files currently modified
   - Any TODO/FIXME comments added in the branch diff
3. Suggest: "Want to continue with '<name>'? cd <path>"

## Multi-Worktree Creation

When user says "I need to work on N things" or lists multiple tasks:

1. Parse the tasks from user input
2. For each task, derive a worktree name and description from the user's task list -- never prompt for categories or work types
3. Show plan:
   ```
   I'll create 3 worktrees:
     1. auth-refactor  -> wt/auth-refactor  "Refactor auth middleware"
     2. fix-login      -> wt/fix-login      "Fix OAuth redirect bug"
     3. add-dashboard  -> wt/add-dashboard  "New analytics dashboard"

   Proceed?
   ```
4. On confirmation, create all worktrees sequentially via `/wt new` flow
5. Show final dashboard

## Cleanup Advisor

When asked "clean up worktrees" or detected during dashboard:

Identify candidates:
- **Done**: worktrees where branch is fully merged into base
- **Stale**: worktrees with no commits in >7 days and status "active"
- **Missing**: registry entries where path no longer exists

Present:

```
Cleanup recommendations:

  Done (branch merged):
    - fix-login: branch wt/fix-login merged into master
      -> /wt rm fix-login

  Stale (no activity >7 days):
    - old-experiment: last commit 12 days ago
      -> Pause? Remove?

  Missing (path gone):
    - deleted-wt: path .worktrees/deleted-wt not found
      -> Remove from registry
```

## Conflict Early Warning

When asked "check for conflicts" or proactively during dashboard if >1 active worktree:

1. For each pair of active worktrees, check file overlap:
   ```bash
   # Files changed in each worktree vs its base
   git -C <path1> diff --name-only <base1>...<branch1>
   git -C <path2> diff --name-only <base2>...<branch2>
   ```
2. Find intersection of changed files
3. For overlapping files, check if changes touch the same lines:
   ```bash
   git -C <path1> diff <base1>...<branch1> -- <file>
   git -C <path2> diff <base2>...<branch2> -- <file>
   ```
4. Report:

```
Conflict Risk Assessment
========================

auth-refactor vs fix-login:
  Overlapping files: 2
    src/middleware/auth.ts - LIKELY CONFLICT (both modify lines 45-80)
    src/config.ts - low risk (different sections)

auth-refactor vs add-dashboard:
  No overlapping files - clean

Recommendation: Merge auth-refactor first, then rebase fix-login.
```

## Commands Reference

Direct the user to `/wt` command for operations:
- `/wt new <name>` - create worktree
- `/wt list` - compact listing
- `/wt status` - detailed dashboard
- `/wt pause <name>` / `/wt resume <name>` - toggle status
- `/wt rm <name>` - remove worktree
- `/wt merge <name>` - guided merge flow
