---
description: Propose a plan first, then move or delete only what the user confirms, batch by batch. Use when organizing messy folders (Downloads, Desktop, Documents), finding duplicate files, cleaning up directories, or restructuring file hierarchies. Not for code refactoring, which /clean-code in the `clean-code` bundle and /python-refactor in the `python-development` bundle cover.
argument-hint: <path> [find duplicates | by type | by date]
---

# File Organizer

Use the `file-organizer` skill to organize, cleanup, and restructure:

$ARGUMENTS

**Safety**: the skill always proposes a plan and asks for approval before moving or deleting anything. Destructive operations (duplicate removal, file deletion) require explicit confirmation per batch.

## Quick Examples

- `/organize-files Downloads` - Organize Downloads folder by file type
- `/organize-files ~/Documents find duplicates` - Find and remove duplicate files
- `/organize-files ~/Projects archive old` - Archive inactive projects
- `/organize-files . cleanup` - Clean up current directory
