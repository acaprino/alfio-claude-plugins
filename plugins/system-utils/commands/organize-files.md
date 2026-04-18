---
description: >
  Organize, deduplicate, and restructure file hierarchies safely. Proposes a plan before moving or deleting anything; destructive operations require explicit confirmation per batch.
  TRIGGER WHEN: organizing messy folders (Downloads, Desktop, Documents), finding duplicate files, cleaning up directories, or restructuring file hierarchies.
  DO NOT TRIGGER WHEN: the task is about code refactoring (use clean-code or python-refactor).
argument-hint: "<path> [find duplicates | by type | by date]"
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
