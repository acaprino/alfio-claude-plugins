# CC Usage Plugin

> Track your Claude Code token usage, costs, and activity. Parses local JSONL session data to generate reports with billing block monitoring, per-model breakdowns, tool usage stats, and daily trends.

## Skills

### `cc-usage`

Analyzes Claude Code session data from local JSONL files to generate usage reports.

| | |
|---|---|
| **Invoke** | Skill reference or `/cc-usage` |
| **Trigger** | "usage", "costs", "tokens", "burn rate", "billing block", "how much am I spending" |

**Data sources:** Reads from `~/.config/claude/projects/` (primary), `~/.claude/projects/` (legacy), or custom path via `CLAUDE_CONFIG_DIR`.

**Report sections:**
1. **Overview** - Total tokens, messages, cost for the period
2. **Current Billing Block** - Active 5-hour block with remaining time, burn rate, projected cost
3. **Usage by Model** - Token and cost split between Opus, Sonnet, Haiku
4. **Tool Usage** - Most-used tools with visual bar chart
5. **Projects** - Per-project token and cost breakdown
6. **Recent Sessions** - Most recently active sessions
7. **Daily Breakdown** - Day-by-day token and cost trend

**Pricing tiers (per MTok):**
| Model | Input | Output | Cache Create | Cache Read |
|-------|-------|--------|--------------|------------|
| Opus | $15 | $75 | $18.75 | $1.50 |
| Sonnet | $3 | $15 | $3.75 | $0.30 |
| Haiku | $0.80 | $4 | $1 | $0.08 |

When the JSONL data includes `costUSD`, that native value takes priority over calculated estimates.

**Inspired by:** [paulrobello/par_cc_usage](https://github.com/paulrobello/par_cc_usage)

---

## Commands

### `/cc-usage`

Analyze your Claude Code token usage, costs, and activity.

```
/cc-usage              # Full 7-day report
/cc-usage 30d          # Last 30 days
/cc-usage brief        # Quick summary only
/cc-usage block        # Current billing block only
/cc-usage project:figs  # Filter to one project
/cc-usage json         # Machine-readable output
```

| Argument | Effect |
|----------|--------|
| `7d` / `30d` / `90d` | Time period (default: 7 days) |
| `project:<name>` | Filter to a specific project |
| `json` | Output raw JSON data |
| `brief` | Show only overview and billing block |
| `block` | Show only current billing block |

Runs a Python analysis script under the hood and displays the markdown output directly -- tables render in the conversation.

---

**Related:** [marketplace-ops](marketplace-ops.md) (plugin ecosystem management)
