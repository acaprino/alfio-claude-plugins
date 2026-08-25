# MarkMind Rich Format Specification

Reference document for the internal JSON structure used by the Obsidian MarkMind plugin in Rich mode.

## File Structure

A MarkMind Rich file is a standard `.md` with YAML frontmatter and a JSON code block:

```
---

mindmap-plugin: rich

---

# Root
``` json
{...full JSON...}
```
```

Important: the frontmatter requires blank lines before and after `mindmap-plugin: rich`.

## Top-Level JSON

```json
{
  "theme": "",
  "mindData": [ [main_nodes...], [freeNode1], [freeNode2], ... ],
  "induceData": [],
  "wireFrameData": [],
  "relateLinkData": [],
  "calloutData": [],
  "opt": {
    "background": "transparent",
    "fontFamily": "",
    "fontSize": 16
  },
  "scrollLeft": 3303,
  "scrollTop": 3330,
  "transformOrigin": [4253.5, 3860]
}
```

### mindData

Array of arrays. The first array contains all nodes of the main map (flat list, not nested). Subsequent arrays are free nodes (standalone nodes not connected to the tree).

### Node Fields

| Field     | Type    | Required | Description                                                    |
| --------- | ------- | -------- | -------------------------------------------------------------- |
| id        | string  | yes      | Unique identifier                                              |
| text      | string  | yes      | Display text. Supports emoji, `**bold**`, `![[image]]`         |
| pid       | string  | no       | Parent node ID. Absent only on root                            |
| isRoot    | boolean | root     | `true` only on root node                                       |
| main      | boolean | root     | `true` only on root node                                       |
| x         | number  | yes      | Absolute X coordinate on canvas                                |
| y         | number  | yes      | Absolute Y coordinate on canvas                                |
| stroke    | string  | yes      | Branch color (hex). Empty string on root                       |
| style     | object  | yes      | CSS properties: color, background-color, border-color, etc.    |
| layout    | object  | root     | `{"layoutName":"mindmap6","direct":"mindmap"}` on root, else `null` |
| isExpand  | boolean | yes      | Whether children are visible. Always `true` for generation     |

### Root Node Example

```json
{
  "id": "root-001",
  "text": "🎯 Central Theme",
  "isRoot": true,
  "main": true,
  "x": 4120,
  "y": 3700,
  "isExpand": true,
  "layout": {"layoutName": "mindmap6", "direct": "mindmap"},
  "stroke": "",
  "style": {
    "color": "#ffffff",
    "background-color": "#ffffff",
    "border-color": "#ffffff",
    "text-align": "center"
  }
}
```

### Child Node Example

```json
{
  "id": "node-abc123",
  "text": "⚙️ Process Flow",
  "stroke": "#ff6b6b",
  "style": {},
  "x": 4400,
  "y": 3575,
  "layout": null,
  "isExpand": true,
  "pid": "root-001"
}
```

### Free Node Example

Each free node is a separate array in mindData:

```json
[{
  "id": "fn-xyz789",
  "text": "freeNode",
  "main": false,
  "x": 0,
  "y": 0,
  "layout": {"layoutName": "mindmap2", "direct": "mindmap"},
  "isExpand": true,
  "stroke": "",
  "style": {}
}]
```

Standard generation includes 8 empty free nodes.

## Coordinate System

The canvas uses absolute pixel coordinates. Typical root position: (4120, 3700).

### Layout Algorithm

- Branches split left/right of root (first half + extra right, rest left)
- Horizontal offsets from parent:
  - Root to L2: 280px
  - L2 to L3: 150px
  - L3 to L4: 140px
- Vertical spacing between siblings: 33px
- Gap between branch clusters: 12px
- Each side centers vertically around ROOT_Y

### Viewport Settings

```
scrollLeft = ROOT_X - 817
scrollTop = ROOT_Y - 370
transformOrigin = [ROOT_X + 133.5, ROOT_Y + 160]
```

## Advanced Features

### induceData (Summary)

Groups consecutive sibling nodes under a label:

```json
{
  "induceData": {
    "nodeId": "first-node-id",
    "endNodeId": "last-node-id",
    "stroke": "#666",
    "root": "summary-root-id",
    "lineType": "solid",
    "id": 1234567890,
    "range": "0,2",
    "type": "left"
  },
  "mindData": [{
    "id": "summary-root-id",
    "text": "Summary Label",
    "style": {},
    "x": 3319,
    "y": 3681,
    "layout": null,
    "isExpand": true,
    "stroke": ""
  }]
}
```

### relateLinkData (Cross-branch connections)

Connects nodes from different branches with a styled line. Complex structure with bezier control points. Use sparingly and only for explicit cross-references.

### wireFrameData (Boundary)

Groups nodes visually with a surrounding frame. Currently empty array for standard generation.

## Color Palette

| # | Hex       | Name     |
| - | --------- | -------- |
| 1 | #ff6b6b   | Coral    |
| 2 | #4ecdc4   | Teal     |
| 3 | #95e77e   | Lime     |
| 4 | #a8e6cf   | Mint     |
| 5 | #ffd3b6   | Peach    |
| 6 | #d4a5f5   | Lavender |
| 7 | #f7dc6f   | Yellow   |
| 8 | #85c1e9   | Sky      |

Rule: all descendants of an L2 branch inherit that branch's stroke color.
