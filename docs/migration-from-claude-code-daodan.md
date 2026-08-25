# Migrating from `claude-code-daodan` to `daodan`

The repository is now one marketplace with three native front ends. The same 40 plugins are compiled
from one set of content kernels into Claude Code, GitHub Copilot and Codex packages, at one identical
version everywhere. Two things changed for existing users: the repository name, and the removal of the
VS Code extension.

## What replaced what

| Before | After |
|---|---|
| `acaprino/claude-code-daodan` | `acaprino/daodan` |
| Claude packages under `plugins/<name>` | compiled packages under `exports/claude/plugins/<name>` |
| A VS Code extension built from `exports/vscode` | a native Copilot marketplace at `.github/plugin/marketplace.json` |
| No Codex distribution | a native Codex marketplace at `.agents/plugins/marketplace.json` |

Plugin names did not change. Command, agent and skill names did not change on Claude Code.

## One-time migration

### Claude Code

```bash
claude plugin marketplace remove claude-code-daodan
claude plugin marketplace add acaprino/daodan
claude plugin install <plugin>@daodan
```

Start a fresh session afterwards and check that no plugin name appears twice: a stale marketplace left
registered is the only way to end up with two copies of the same plugin.

### GitHub Copilot

Uninstall the old extension first. It is no longer built, and leaving it installed keeps a second copy
of every skill in `~/.copilot/skills/`:

```bash
code --uninstall-extension acaprino.claude-code-daodan
```

Then register the repository as a marketplace and install what you want:

```bash
copilot plugin marketplace add acaprino/daodan
copilot plugin install <plugin>@daodan
```

### Codex

```bash
codex plugin marketplace add acaprino/daodan
codex plugin install <plugin>@daodan
```

## The VS Code extension is not coming back

The `.vsix` was a distribution workaround from before Copilot read plugin marketplaces. It shipped one
bundle per plugin plus a JavaScript lifecycle that copied skill directories into `~/.copilot/skills/`,
and it had no auto-update path: every upgrade meant downloading an asset and running
`code --install-extension`. The native Copilot marketplace replaces all of it.

Historical GitHub Release assets are left untouched, and they are unsupported. They install content
from before the universal migration, they will never be rebuilt, and nothing checks them.

## Rollback

Roll back with a Git revert and a **new** patch marketplace version. Published versions are never
reused: a consumer that already installed `26.0.0` must be able to tell a rollback from the original
by its version alone.

```bash
git revert <cutover-sha>
# bump metadata.version in .claude-plugin/marketplace.json to the next patch
python scripts/daodan_build.py
python scripts/daodan_build.py --check
```

The repository name is not part of rollback. GitHub keeps redirecting the old name, renaming back
would break the redirect in both directions, and the marketplace identity (`daodan`) is what consumers
actually resolve.

## Curated host directories

A future submission to any curated directory references an immutable release tag or SHA. That is
independent of publication from this repository: registering `acaprino/daodan` as a marketplace
installs from `master`, and a directory listing installs from whatever revision it pinned.
