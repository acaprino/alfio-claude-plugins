---
name: file-organizer
description: >
  Scope, plan, and execute the reorganization behind approval gates.
  Use when organizing messy folders (Downloads, Desktop, Documents), finding duplicate files,
  cleaning up old files, restructuring project directories, separating work from personal files, or
  automating file cleanup tasks.
user-invocable: true
license: MIT
metadata:
  author: ComposioHQ
  source: acaprino/claude-code-daodan
  upstream-plugin: system-utils
---

# File Organizer

## Instructions

### 1. Understand Scope

Ask clarifying questions before starting:
- Which directory needs organization?
- Main problem? (can't find things, duplicates, no structure, general mess)
- Files or folders to avoid? (active projects, sensitive data)
- How aggressive? (conservative vs comprehensive cleanup)

For broad reorganization, briefly propose a philosophy from the reference guide (PARA, Johnny Decimal, GTD, 7-Folder). Let user choose - never force one. Skip for scoped tasks like cleaning Downloads.

### 2. Analyze Current State

```bash
ls -la [target_directory]
find [target_directory] -type f -exec file {} \; | head -20
du -sh [target_directory]/* | sort -rh | head -20
find [target_directory] -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn
```

Summarize: total files/folders, type breakdown, size distribution, date ranges, obvious issues.

**Anti-patterns to flag:**
- Desktop used as permanent archive (goal: zero permanent files on Desktop)
- Unnamed folders (`New Folder`, `New Folder (3)`)
- Broken versioning (`document_FINAL_v2_DEFINITIVE_copy.docx`)
- Downloads folder never cleaned (thousands of unsorted files)
- Same file duplicated across locations (use shortcuts instead)

### 3. Identify Organization Patterns

**By type:**
- Documents (PDF, DOCX, TXT), Images (JPG, PNG, SVG), Videos (MP4, MOV)
- Archives (ZIP, TAR, DMG), Code/Projects, Spreadsheets (XLSX, CSV), Presentations (PPTX, KEY)

**By purpose:**
- Work vs Personal, Active vs Archive, Project-specific, Reference, Temporary/scratch

**By date:**
- Current year/month, Previous years, Very old (archive candidates)

**Context-specific structures:**
- Photos/Video: `Year/YYYY-MM_event-location/` with RAW, Edited, Export subfolders
- Music: `Artist/[Year] Album/NN - Track.ext`
- Work projects: numbered prefixes (`01_Brief/`, `02_Research/`, `03_Assets/`, `04_Deliverables/`) with WIP/FINAL_APPROVED separation
- Finance/personal docs: include expiry dates in filenames (`passport_exp_2030.pdf`), organize by year then type
- Code: map local paths to remote URLs (`github.com/username/repo/`)

See `references/organization-guide.md` for detailed templates.

### 4. Find Duplicates

When requested:
```bash
find [directory] -type f -exec md5 {} \; | sort | uniq -d
find [directory] -type f -printf '%f\n' | sort | uniq -d
```

For each duplicate set: show paths, sizes, dates, recommend which to keep. ALWAYS confirm before deleting. Suggest shortcuts/aliases instead of keeping copies.

### 5. Propose Organization Plan

Present plan before making changes. Include:
- Current state summary (file count, size, type breakdown, problems found)
- Anti-patterns detected
- Proposed folder tree structure
- Changes to make: new folders, file moves, renames, deletions
- Files needing user decision (ambiguous placement)
- Ask for explicit approval before proceeding

### 6. Execute Organization

After approval, organize systematically.

**Rules:**
- Always confirm before deleting anything
- Log all moves for potential undo
- Preserve original modification dates
- Handle filename conflicts gracefully
- Stop and ask on unexpected situations

**File renaming conventions** (only when user agrees - never auto-rename):
- ISO dates: `YYYY-MM-DD` for correct alphabetical sort
- Formula: `[Date]_[Context]_[Description]_[Version].ext`
- Zero-padded versions: `v01`, `v02` (minor: `v01.1`)
- Separators: `kebab-case` or `snake_case` (never spaces)
- All lowercase, filenames under 25-30 chars, let folder context provide the rest
- Zero-pad sequences: `001`, `002` (prevents `1, 10, 11, 2` sort)
- Status prefixes when useful: `WIP_`, `DRAFT_`, `REVIEW_`, `APPROVED_`
- Avoid: `< > : " / \ | ? *`, accents, emoji, leading dots, Windows reserved names (`CON`, `PRN`, `AUX`, `NUL`)
- Watch full path length approaching Windows 260-character limit

### 7. Provide Summary

After organizing, report:
- Folders created, files organized, space freed, anti-patterns fixed
- New folder tree structure
- Maintenance schedule (below)
- Custom bash commands for ongoing cleanup

**Maintenance Schedule:**

| Frequency | Time | Tasks |
|-----------|------|-------|
| Weekly | 15 min | Empty Downloads, process Inbox to zero, verify recent files are in place |
| Monthly | 45 min | Scan for duplicates, verify backups, archive completed projects |
| Quarterly | 2 hrs | Disk space audit, archive projects inactive 3+ months, test backup restore |
| Yearly | Half day | Disaster recovery test, retention policy review, structure update |
