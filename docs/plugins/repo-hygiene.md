# repo-hygiene

Workspace tidying decided by the filesystem and git alone. Committed build output,
`.gitignore` gaps and stale rules, filesystem garbage, scratch directories, orphan
doc-assets, and stale git state.

**Install:** ships with the marketplace. No dependencies: it is a leaf by rule.

| | |
|---|---|
| **Command** | `/repo-hygiene:tidy` |
| **Agent** | `repo-hygiene:workspace-auditor` |
| **Skill** | `repo-hygiene:repo-hygiene` |
| **Dependencies** | none |

## What decides the boundary

One question separates this plugin from `senior-review`: **what kind of evidence
answers the check?**

`git ls-files`, `git check-ignore`, `git stash list`, a directory listing. No source
file is read and no symbol is understood. That is this plugin.

What a symbol is for, whether a reference reaches it, whether removing it changes
behavior. Dynamic imports, decorators, framework conventions, module augmentation. That
is `senior-review:cleanup-auditor`, and this plugin never reaches for it.

The split is not about risk or size. A tracked `dist/` directory can be larger and more
consequential than a dead export, and it still belongs here, because deciding it needs
`git ls-files` and not a parser.

## The seven checks

| | Check | Full | Lite |
|---|---|---|---|
| C1 | Filesystem garbage: `nul`, `.DS_Store`, `Thumbs.db`, shell-redirection artifacts | yes | yes |
| C2 | Generated artifacts tracked in git, checked against publication conventions first | yes | yes |
| C3 | `.gitignore` completeness, per detected ecosystem | yes | partial |
| C4 | `.gitignore` archaeology: stale rules, overly-broad rules, with `git check-ignore -v` provenance | yes | no |
| C5 | Scratch and pipeline-output directories | yes | no |
| C6 | Orphan doc-assets, widened past literal Markdown links | yes | no |
| C7 | Git auxiliary state: stale stashes, orphan worktrees, gone-upstream and merged branches | yes | no |

**Two profiles, one set of definitions.** The full profile runs over the working tree.
The lite profile runs over the files a diff adds, and is what the inline hygiene pass
of `/senior-review:code-review` and `/senior-review:pr-review` loads. C4 through C7 are
absent from the lite profile on purpose: they are repository-historical, so a diff under
review cannot have caused them, and reporting them there attributes old debt to an
innocent change.

## Three things it refuses to do

**It will not untrack a build output that is published on purpose.** A tracked `dist/`
reads exactly like an accident, and sometimes GitHub Pages serves from it or a generated
SDK ships to package consumers. C2 checks `.nojekyll`, `CNAME`, Pages workflows, and the
`files` allowlist in `package.json` before proposing anything. When a convention claims
the path, the finding is KEEP with the convention quoted, which also stops the next
audit from re-raising it.

**It will not delete a doc-asset on the strength of a basename Grep.** An image reaches
the rendered site through a `mkdocs.yml` value, a `url()` in a stylesheet, a generated
navigation entry, or a path composed in a template, none of which a Markdown search
sees. C6 widens to configs, stylesheets and templates, and removal still requires
item-level approval showing both searches that found nothing.

**It will never drop a stash, remove a worktree, or delete a branch.** C7 is
detection-only, permanently, and the reason is structural rather than cautious. Every
other check mutates tracked content, so a commit records the change and reverting
restores it. A dropped stash produces no diff for any commit to hold, a removed worktree
takes its uncommitted files with it, and a deleted branch survives only in a reflog that
expires. The rollback mechanism the command promises does not reach that far, so the
command does not go there. The findings carry the commands; the user runs them.

## `/repo-hygiene:tidy`

```
/repo-hygiene:tidy [path] [--fix] [--commit] [--phases=garbage,gitignore,scratch,git-state]
```

Detects and reports by default. `--fix` applies and leaves the working tree modified
with no commits. `--commit` implies `--fix` and adds one commit per phase. The flags
mean exactly what they mean in `/senior-review:code-review`.

Four phases, run in order: `garbage`, `gitignore`, `scratch`, `git-state`.

**There is no build-and-test gate between phases**, because nothing applied here is
code. For `gitignore`, the protection that matters is the per-item confirmation on
`git rm --cached`, not a test suite that passes because the untracked files are still
sitting on disk.

**Untracked removals go to quarantine**, at `.repo-hygiene/quarantine/<timestamp>/`,
preserving relative paths. Git holds no copy of an untracked file, so deletion would be
the one irreversible operation in the command, and it is not taken. This is what makes
`--fix` safe without commits: everything it does is undoable by hand.

**`--commit` requires a clean tree** because its per-phase commits are its revert
mechanism and an unrelated modified file would be swept into one. `--fix` has no such
requirement: it stages nothing, so nothing of yours is at risk. Staging is always by
explicit path, never `git add -A`.

## Inside a team review

`/senior-review:team-review` spawns `repo-hygiene:workspace-auditor` as an always-on
dimension alongside `senior-review:cleanup-auditor`. The two perimeters are disjoint by
construction, so consolidation has nothing to deduplicate between them. **A finding
appearing in both reports is a boundary violation to investigate, not an `echo` to
fold.**

## Related

- [senior-review](senior-review.md): everything hygiene-adjacent that needs source
  comprehension, plus Step 7c, which removes application code in five gated phases.
- [testing](testing.md): `/testing:test-consolidate` owns bulk removal of test files.
- [dependency-audit](dependency-audit.md): CVEs, licenses and version drift from each
  ecosystem's own tooling, which is a different question from whether a dependency is
  used.
