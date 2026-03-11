# Utilities Plugin

> Tame messy folders and bloated codebases. Organizes files, finds duplicates, removes dead code, and cleans up directories with approval before any changes.

## Skills

### `file-organizer`

Personal organization assistant for maintaining clean, logical file structures.

| | |
|---|---|
| **Invoke** | Skill reference or `/organize-files` |
| **Use for** | Messy folders, duplicates, old files, project restructuring |

**Capabilities:**
- **Analyze** - Review folder structure and file types
- **Find Duplicates** - Identify duplicate files by hash
- **Suggest Structure** - Propose logical folder organization
- **Automate** - Move, rename, organize with approval
- **Cleanup** - Identify old/unused files for archiving

---

## Commands

### `/organize-files`

Quick command to organize files and directories.

```
/organize-files Downloads
```

**Examples:**
| Command | Action |
|---------|--------|
| `/organize-files Downloads` | Organize Downloads by type |
| `/organize-files ~/Documents find duplicates` | Find duplicate files |
| `/organize-files ~/Projects archive old` | Archive inactive projects |
| `/organize-files . cleanup` | Clean up current directory |

---

### `/cleanup-dead-code`

Find and remove dead code -- auto-detects language: Knip for TypeScript/JavaScript, vulture + ruff for Python.

| | |
|---|---|
| **Invoke** | `/cleanup-dead-code [path] [--dry-run] [--dependencies-only] [--exports-only] [--production]` |
| **Use for** | Dead code removal, dependency cleanup, export pruning, unused import removal |
