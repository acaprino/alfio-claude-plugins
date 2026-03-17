# Learning Plugin

> Generate mind maps from any content -- books, articles, topics, notes, or conversations. Export to Obsidian MarkMind Rich format or interactive force-graph HTML.

## Skills

### `generate-mindmap`

Brainstorm and generate a structured mindmap JSON outline from any content. Analyzes content, designs hierarchy, assigns emoji and colors, and outputs a renderer-agnostic JSON structure.

| | |
|---|---|
| **Invoke** | Skill reference or via `/export-to-markmind` |
| **Use for** | Content analysis, brainstorming, hierarchy extraction, concept mapping |

**Workflow:**
1. **Analyze** -- identify subject matter, key themes, and relationships
2. **Build outline** -- extract central theme, main branches (L2), sub-concepts (L3), leaf details (L4+)
3. **Output** -- JSON (default) or markdown nested list with root, branches, children, colors, and emoji

### `markmind-exporter`

Render a mindmap JSON outline into Obsidian MarkMind Rich format. Takes a pre-built JSON structure and converts it to a `.md` file for the MarkMind plugin.

| | |
|---|---|
| **Invoke** | Skill reference or via `/export-to-markmind` |
| **Use for** | Converting mindmap JSON to MarkMind Rich format for Obsidian |

**Workflow:**
1. **Locate** -- find the mindmap outline JSON (file, prior generate-mindmap output, or inline)
2. **Render** -- pipe JSON to `generate_markmind.py` script for coordinate calculation and formatting
3. **Output** -- ready-to-use `.md` file for Obsidian MarkMind plugin

**Includes:**
- `references/markmind-rich-spec.md` -- MarkMind Rich format specification
- `scripts/generate_markmind.py` -- JSON-to-MarkMind generator script

### `forcegraph-exporter`

Export a mindmap JSON outline as a single self-contained HTML file using force-graph. Produces a zoomable, draggable visualization that opens in any browser.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Interactive web-based mindmap visualization |

**Workflow:**
1. **Locate** -- find the mindmap outline JSON
2. **Export** -- run `generate_forcegraph.py` to produce a self-contained HTML file
3. **Output** -- single `.html` file with embedded force-directed graph

**Includes:**
- `scripts/generate_forcegraph.py` -- JSON-to-HTML force-graph generator script

---

## Commands

### `/export-to-markmind`

Generate a MarkMind mind map from any topic, text, or file. Chains `generate-mindmap` (brainstorming) and `markmind-exporter` (rendering).

```
/export-to-markmind Python asyncio patterns
/export-to-markmind "text to map"
/export-to-markmind path/to/file.md
```

**Output:** `.md` file ready for Obsidian MarkMind plugin.

---

**Related:** [obsidian-development](obsidian-development.md) (Obsidian plugin development) | [ai-tooling](ai-tooling.md) (brainstorming skill for ideation)
