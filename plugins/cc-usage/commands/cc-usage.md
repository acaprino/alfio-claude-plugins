---
description: >
  "Analyze Claude Code token usage, costs, billing blocks, and tool activity from local session data" argument-hint: "[--days N] [--session <id>] [--breakdown]".
  TRIGGER WHEN: the user requires assistance with tasks related to this domain.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# /cc-usage

Analyze your Claude Code token usage, costs, and activity.

## Usage

```
/cc-usage [options]
```

## Options

- `7d` / `30d` / `90d` - Time period (default: 7 days)
- `project:<name>` - Filter to a specific project
- `json` - Output raw JSON data
- `brief` - Show only overview and billing block
- `block` - Show only current billing block

## Examples

```
/cc-usage              # Full 7-day report
/cc-usage 30d          # Last 30 days
/cc-usage brief        # Quick summary only
/cc-usage block        # Current billing block only
/cc-usage project:acp  # Filter to one project
/cc-usage json         # Machine-readable output
```

## What to do

Parse the user's arguments, then run the analysis script:

```bash
python plugins/cc-usage/skills/cc-usage/scripts/cc_usage.py [flags]
```

Map user arguments to script flags:
- `7d` / `30d` / `90d` -> `-d 7` / `-d 30` / `-d 90`
- `project:<name>` -> `-p <name>`
- `json` -> `--json`
- `brief` -> `--no-tools --no-sessions --no-projects -n 5`
- `block` -> `--no-tools --no-sessions --no-projects`

Present the markdown output directly -- it contains formatted tables that render well in the conversation.

If the user asks follow-up questions about specific projects, sessions, or tools, re-run with appropriate filters or dig into the data programmatically using the script's JSON output mode.
