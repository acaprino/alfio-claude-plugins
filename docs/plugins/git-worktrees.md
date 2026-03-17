# Git Worktrees Plugin

> Work on multiple branches at the same time without stashing or switching. Create isolated worktrees, pause and resume work, merge back when ready, and get early warnings about cross-worktree conflicts.

## Agents

### `worktree-agent`

Handles git worktree operations that need judgment -- guided merge flows with conflict detection, strategy recommendations, PR creation, and cleanup.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Merge strategy selection, conflict resolution guidance, cross-worktree conflict early warning |

**Invocation:**
```
Use the worktree-agent to merge feature-auth back to main
```

---

## Skills

### `worktree-manager`

Proactive worktree orchestration. Detects WIP state (uncommitted changes, stashes, unpushed commits) and offers to isolate work into worktrees.

| | |
|---|---|
| **Invoke** | Skill reference or `/wt` |
| **Trigger** | "show my worktrees", "what am I working on", "worktree status", "coordinate my work" |

**Capabilities:**
- **WIP detection** - Checks `git status`, `git stash list`, and unpushed commits at session start
- **WIP migration** - Moves uncommitted work into a new worktree (stash, create, pop)
- **Dashboard** - Overview of all active worktrees with status
- **Context recovery** - Resume work in a worktree with full context
- **Cleanup advisor** - Identify stale worktrees ready for removal
- **Conflict early warning** - Detect overlapping file changes across parallel worktrees

---

## Commands

### `/wt`

Git worktree management with subcommands for the full lifecycle.

```
/wt new feature-auth                    # create worktree
/wt new hotfix --from main              # create from specific branch
/wt list                                # show all worktrees
/wt status                              # detailed status with file changes
/wt pause feature-auth                  # save context and pause
/wt resume feature-auth                 # restore context and continue
/wt merge feature-auth --squash         # squash merge back
/wt merge feature-auth --pr             # create PR instead of local merge
/wt rm feature-auth                     # remove worktree and branch
```

| Subcommand | Purpose |
|------------|---------|
| `new <name>` | Create a worktree with optional `--branch`, `--from`, `--desc`, `--setup` flags |
| `list` | Show all registered worktrees |
| `status` | Detailed view with uncommitted changes, unpushed commits |
| `pause <name>` | Save session context for later resume |
| `resume <name>` | Restore context and continue working |
| `merge <name>` | Merge back with `--squash`, `--rebase`, or `--pr` strategy |
| `rm <name>` | Remove worktree, branch, and registry entry |

**Registry:** `.worktrees/registry.json` (auto-created, gitignored)

**Worktree location:** Sibling to repo at `../worktrees/<project>-<name>/`

**Optional dependency:** [senior-review](senior-review.md) for pre-merge code review.

---

**Related:** [workflows](workflows.md) (multi-phase pipelines that can run in worktrees) | [senior-review](senior-review.md) (pre-merge review)
