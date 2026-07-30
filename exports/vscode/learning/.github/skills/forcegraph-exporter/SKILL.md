---
name: forcegraph-exporter
description: >
  Export a mindmap JSON outline as an interactive HTML file using force-graph (requires internet for the
  CDN). Use when the user wants an interactive, web-based, zoomable and draggable visualization of a
  mindmap, or says "interactive map", "force graph", "web mindmap", "HTML mindmap". Not for Obsidian
  MarkMind format, which markmind-exporter covers, nor for a static text outline.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: learning
---

# Force Graph Exporter

Convert a mindmap JSON outline into an interactive HTML file with a force-directed graph visualization powered by [force-graph](https://github.com/vasturiano/force-graph). The output file can be opened in any browser -- no server required, but needs internet to load the force-graph library from CDN.

## Input

A JSON file with the standard mindmap outline format (same as generate-mindmap output):

```json
{
  "root": "Central Theme",
  "branches": [
    {
      "text": "Branch One",
      "color": "#ff6b6b",
      "children": [
        { "text": "Sub-concept A", "children": [...] }
      ]
    }
  ]
}
```

## Workflow

### Step 0: Check for input

If no mindmap JSON is available (no file path, no prior `generate-mindmap` output, no inline JSON in the conversation), invoke the `generate-mindmap` skill first to brainstorm and produce the JSON outline. Then continue with Step 1.

### Step 1: Locate the mindmap JSON

Find the mindmap outline JSON -- either a file path provided by the user, output from a prior `generate-mindmap` invocation, or inline JSON.

### Step 2: Run the exporter

```bash
python scripts/generate_forcegraph.py --input outline.json --output /path/to/mindmap.html --max-depth 6
```

Or from stdin:

```bash
cat outline.json | python scripts/generate_forcegraph.py --output /path/to/mindmap.html
```

Options:
- `--max-depth N` -- maximum depth levels below root (default: 6, max: 10)

The script:
- Converts the mindmap JSON tree into a flat nodes/links structure
- Loads force-graph library from CDN (unpkg.com, pinned version) in the HTML
- Colors nodes and links by their L2 branch color
- Sizes nodes by depth (root largest, leaves smallest)
- Adds labels, hover tooltips, and click-to-focus
- Produces a single `.html` file

### Step 3: Deliver

Present the generated `.html` file to the user. Mention it can be opened directly in any browser.

## Checklist Before Delivery

- HTML file opens in browser without errors
- All nodes from the mindmap JSON are present in the graph
- Root node is visually prominent (larger, centered)
- Branch colors match the original outline
- Graph is interactive (drag, zoom, hover)
- Internet connection available (CDN dependency for force-graph library)
