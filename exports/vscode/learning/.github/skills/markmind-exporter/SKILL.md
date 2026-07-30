---
name: markmind-exporter
description: >
  Render a mindmap JSON outline into Obsidian MarkMind Rich format. Use after generating a mindmap
  outline (via generate-mindmap or any other source) to convert it into a .md file ready for the
  Obsidian MarkMind plugin, or when the user says "markmind", "render to markmind", or needs MarkMind
  Rich output from an existing mindmap JSON structure. Not for an interactive HTML mindmap, which
  forcegraph-exporter covers, nor for a plain text outline.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: learning
---

# MarkMind Exporter

Render a mindmap JSON outline into Obsidian MarkMind Rich format. This skill takes a pre-built mindmap JSON structure (produced by `generate-mindmap` or any other source) and converts it into a `.md` file the user can drop directly into their Obsidian vault and open with the MarkMind plugin.

## Input

A JSON file with the standard mindmap outline format:

```json
{
  "root": "🎯 Central Theme",
  "branches": [
    {
      "text": "🔴 Branch One",
      "color": "#ff6b6b",
      "children": [
        {
          "text": "⚙️ Sub-concept A",
          "children": [
            { "text": "Detail 1" },
            { "text": "Detail 2" }
          ]
        }
      ]
    }
  ]
}
```

## Workflow

### Step 0: Check for input

If no mindmap JSON is available (no file path, no prior `generate-mindmap` output, no inline JSON in the conversation), invoke the `generate-mindmap` skill first to brainstorm and produce the JSON outline from the user's topic or content. Then continue with Step 1.

### Step 1: Locate the mindmap JSON

Find the mindmap outline JSON -- either a file path provided by the user, output from a prior `generate-mindmap` invocation, or inline JSON.

### Step 2: Run the renderer

Pipe the JSON outline to `scripts/generate_markmind.py`:

```bash
cat <<'EOF' | python scripts/generate_markmind.py --output /path/to/output.md --max-depth 4
{...mindmap JSON...}
EOF
```

Or from a file:

```bash
python scripts/generate_markmind.py --input outline.json --output /path/to/output.md --max-depth 4
```

The script automatically:
- Generates unique node IDs
- Splits branches left/right of root
- Calculates x/y coordinates with proper spacing (recursive, supports any depth)
- Truncates nodes beyond `--max-depth` (default: 4)
- Creates 8 empty free nodes
- Wraps everything in valid MarkMind Rich format

### Step 3: Deliver

Present the generated `.md` file to the user. Mention it's ready to drop into Obsidian.

## Reference

Read `references/markmind-rich-spec.md` for the full MarkMind Rich JSON schema if needed.

## Checklist Before Delivery

- All `pid` references point to existing `id` values
- Root has `isRoot: true`, `main: true`, layout object
- No `pid` on root node
- Each L2 branch has a unique stroke color
- All descendants inherit their L2 ancestor's stroke
- Coordinates don't overlap (V_SPACING respected)
- JSON is valid (no trailing commas, balanced brackets)
- 8 empty free nodes present
- No node exceeds the configured max depth
