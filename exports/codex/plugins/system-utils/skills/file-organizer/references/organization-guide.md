# File Organization Reference Guide

Condensed best practices for naming, structuring, and maintaining files. Use as optional suggestions -- propose to users during organization, never force.

---

## Organization Philosophies

Propose these when a user needs a top-level structure. Let them choose based on personality and context.

### PARA Method (Tiago Forte)

Four folders ordered by actionability. Max 2-3 levels deep.

```
00_Inbox/
01_Projects/       ← active work with deadlines
02_Areas/          ← ongoing responsibilities (no deadline)
03_Resources/      ← reference material by interest
04_Archives/       ← anything no longer active
```

Best for: freelancers, creatives, knowledge workers wanting simplicity.
Weakness: ambiguity between Areas and Resources.

### Johnny Decimal

Numeric IDs: max 10 areas (00-99), max 10 categories each. Item format: `AC.ID` (e.g. `23.04`). Never more than 2 levels deep.

```
10-19 Finanze/
│   ├── 11 Tasse/
│   │   ├── 11.01 FY2024
│   │   └── 11.02 FY2025
│   └── 12 Estratti-Conto/
20-29 Lavoro/
    └── 21 Clienti/
        ├── 21.01 Acme-Corp
        └── 21.02 Globex-Inc
```

Best for: methodical users, shared environments needing unambiguous references.
Weakness: rigid -- hard to restructure after initial setup.

### GTD File System (David Allen)

Separate Reference (consultation) from Actionable (action). Flat alphabetical A-Z for reference. Digital flow: Inbox → Active Projects → Reference → Someday/Maybe → Archive.

Best for: complementary philosophy layered onto other systems.

### 7-Folder Rule

Max 7 folders per level, max 3 levels deep = 343 folders reachable in 1-3 clicks. Simple, predictable, great for teams and SMBs.

---

## Naming Conventions

### Formula

```
[Date]_[Context]_[Description]_[Version].ext
```

All lowercase. No spaces, no accents, no special characters.

### Dates -- ISO 8601

Always `YYYY-MM-DD`. Guarantees correct alphabetical sort across all OSes. Position at start when chronological order matters, after context when grouping by project matters.

### Versioning

`v` + zero-padded digits: `v01`, `v02`, `v03`. Minor revisions: `v01.1`, `v01.2`. Always last element before extension. Status prefixes: `WIP_`, `DRAFT_`, `REVIEW_`, `APPROVED_`.

### Separators

Prefer `kebab-case` or `snake_case`. Never spaces. CamelCase acceptable for project folder names only.

### Zero-Padding

Always pad numbers: `01`, `02`... `99` -- avoids `1, 10, 11, 2` sort order.

### Examples

| Bad | Good |
|-----|------|
| `report finale.docx` | `2026-03-03_report-vendite-Q1_v03.pdf` |
| `Copia di budget (2).xlsx` | `budget-2026_marketing_v02.xlsx` |
| `IMG_20260303_142355.jpg` | `2026-03-03_evento-lancio_001.jpg` |
| `notes march 3rd meeting!!.txt` | `2026-03-03_meeting-notes_team-design.md` |

### Characters to Avoid

`< > : " / \ | ? *`, accents (`è, ñ, ü`), emoji, leading dots (hidden on Unix), Windows reserved names (`CON, PRN, AUX, NUL`).

### Path Length

Windows limit: 260 characters for full path. Deep hierarchies with long names hit this easily.

---

## Context-Specific Structures

### Photos & Video

Year → date+event, with RAW/Edited/Export subfolders.

```
Photos/
└── 2025/
    ├── 2025-01_capodanno-roma/
    │   ├── RAW/
    │   ├── Edited/
    │   └── Export/
    └── 2025-06_vacanza-sardegna/
```

File naming: `YYYY-MM-DD_event_location_NNN.ext`.

### Music

```
Artist/
└── [Year] Album/
    └── NN - Track.ext
```

Always fill Album Artist tag to prevent phantom albums from compilations.

### Work Projects

Numbered prefixes for logical order. Template folder to duplicate for new projects.

```
Clients/
└── ClientName/
    └── 2025_ProjectName/
        ├── 01_Brief/
        ├── 02_Research/
        ├── 03_Assets/
        ├── 04_Deliverables/
        │   ├── WIP/
        │   └── FINAL_APPROVED/
        ├── 05_Meetings/
        └── 06_Admin/
```

### Personal Archive & Finance

Include expiry dates in filenames: `passport_exp_2030.pdf`. Finance by year → type (invoices, statements, tax returns, receipts). Invoice naming: `invoice_NNN_client_YYYY-MM-DD.pdf`.

### Code / Developer Workspace

GOPATH-inspired mapping of local paths to remote URLs.

```
Code/
├── github.com/
│   ├── my-username/
│   │   ├── project-portfolio/
│   │   └── side-project/
│   └── org-work/
│       └── backend-api/
├── sandbox/        (temporary experiments)
└── archive/        (finished projects)
```

---

## Anti-Patterns to Detect

Flag these during analysis and propose fixes:

- **Desktop as archive** -- zero permanent files on Desktop
- **`New Folder (3)`** -- unnamed folders with unknown content
- **`document_FINAL_v2_DEFINITIVE_copy.docx`** -- broken versioning
- **Downloads never cleaned** -- thousands of unsorted files
- **No backup strategy** -- recommend 3-2-1 rule (3 copies, 2 media, 1 offsite)
- **Duplicates everywhere** -- 78% of professionals have this problem
- **One file, multiple locations** -- use shortcuts/aliases instead of copies

---

## Maintenance Schedule

Propose this after organizing -- adapt frequency to user's needs.

| Frequency | Duration | Tasks |
|-----------|----------|-------|
| Weekly | 15 min | Empty Downloads, process Inbox to zero, verify recent files are in place |
| Monthly | 45 min | Scan for duplicates, verify backups, archive completed projects |
| Quarterly | 2 hours | Disk space audit (WizTree/ncdu), archive projects inactive 3+ months, test backup restore, review automation rules |
| Yearly | Half day | Full disaster recovery test, retention policy review, top-level structure update |

### Inbox Principle

Single entry point for all new files. Must be empty after each review session. No file stays in Inbox longer than 7 days.

### Archive Tiers

- **Hot** -- active files on SSD
- **Warm** -- recent files on HDD/NAS
- **Cold** -- archive on external disk or cheap cloud

Compressed archives: `YYYY-MM_project-name_archive.7z` with a `README.txt` describing contents and archive date.
