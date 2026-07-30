#!/usr/bin/env python3
"""
generate_markmind.py

Generates an Obsidian MarkMind Rich format .md file from a JSON brainstorming outline.

Input (stdin): JSON with structure:
{
  "root": "🎯 Central Theme",
  "branches": [
    {
      "text": "🔴 Branch One",
      "color": "#ff6b6b",
      "children": [
        {
          "text": "⚙️ Sub A",
          "children": [
            { "text": "Detail 1" },
            { "text": "Detail 2" }
          ]
        }
      ]
    }
  ]
}

Output: .md file ready for Obsidian MarkMind plugin (Rich mode).

Usage:
  echo '{"root":"...","branches":[...]}' | python generate_markmind.py --output map.md
  python generate_markmind.py --output map.md --input outline.json
"""

import json
import sys
import argparse
import uuid
import math


# ── Layout Constants ──────────────────────────────────────────────

ROOT_X = 4120
ROOT_Y = 3700

# Horizontal offsets per level (from parent)
# Index 0 = L2, index 1 = L3, index 2 = L4, etc.
OFFSETS = [280, 150, 140, 130, 120, 110]

# Vertical spacing between sibling nodes
V_SPACING = 33

# Gap between branch clusters
BRANCH_GAP = 12

MAX_DEPTH_LIMIT = len(OFFSETS)


def generate_id(prefix="node"):
    """Generate a short unique ID."""
    short = uuid.uuid4().hex[:12]
    return f"{prefix}-{short}"


def count_leaves_depth(branch, max_depth, current_depth=1):
    """Count leaf nodes respecting max_depth limit."""
    if current_depth >= max_depth:
        return 1
    children = branch.get("children", [])
    if not children:
        return 1
    return sum(count_leaves_depth(c, max_depth, current_depth + 1) for c in children)


def cumulative_x_offset(level_index, sign):
    """Calculate x position for a given depth level (0-indexed from L2)."""
    total = 0
    for i in range(level_index + 1):
        offset = OFFSETS[i] if i < len(OFFSETS) else OFFSETS[-1]
        total += offset
    return ROOT_X + sign * total


def build_nodes(outline, max_depth=4):
    """
    Convert the brainstorming outline into a flat list of MarkMind nodes
    with calculated coordinates. Supports arbitrary depth up to max_depth.
    """
    nodes = []
    root_text = outline["root"]
    branches = outline.get("branches", [])

    # ── Root node ──
    root_id = generate_id("root")
    nodes.append({
        "id": root_id,
        "text": root_text,
        "isRoot": True,
        "main": True,
        "x": ROOT_X,
        "y": ROOT_Y,
        "isExpand": True,
        "layout": {"layoutName": "mindmap6", "direct": "mindmap"},
        "stroke": "",
        "style": {
            "color": "#ffffff",
            "background-color": "#ffffff",
            "border-color": "#ffffff",
            "text-align": "center"
        }
    })

    n_branches = len(branches)
    if n_branches == 0:
        return nodes

    # ── Split branches: right side (first half+extra), left side (second half) ──
    n_right = math.ceil(n_branches / 2)
    right_branches = branches[:n_right]
    left_branches = branches[n_right:]

    # ── Calculate total leaf count per side to center vertically ──
    def side_leaf_count(branch_list):
        total = 0
        for b in branch_list:
            total += count_leaves_depth(b, max_depth)
        total_gaps = max(0, len(branch_list) - 1)
        return total, total_gaps

    def layout_children(children, parent_id, color, sign, depth, y_cursor):
        """Recursively layout child nodes at any depth."""
        if depth > max_depth or not children:
            return y_cursor

        x = cumulative_x_offset(depth - 1, sign)

        for child in children:
            child_id = generate_id(f"n{depth + 1}")
            child_leaves = count_leaves_depth(child, max_depth, depth)

            child_y_start = y_cursor
            child_y_end = y_cursor + (child_leaves - 1) * V_SPACING
            child_y = (child_y_start + child_y_end) / 2

            nodes.append({
                "id": child_id,
                "text": child.get("text", ""),
                "stroke": color,
                "style": {},
                "x": x,
                "y": round(child_y),
                "layout": None,
                "isExpand": True,
                "pid": parent_id
            })

            grandchildren = child.get("children", [])
            if grandchildren and depth < max_depth:
                y_cursor = layout_children(
                    grandchildren, child_id, color, sign, depth + 1, child_y_start
                )
            else:
                y_cursor += V_SPACING

        return y_cursor

    def layout_side(branch_list, side, start_y_offset):
        """Layout all branches on one side."""
        sign = 1 if side == "right" else -1
        x_l2 = cumulative_x_offset(0, sign)
        current_y = start_y_offset

        for branch in branch_list:
            color = branch.get("color", "#888888")
            branch_id = generate_id("br")
            branch_leaves = count_leaves_depth(branch, max_depth)

            branch_y_start = current_y
            branch_y_end = current_y + (branch_leaves - 1) * V_SPACING
            branch_y = (branch_y_start + branch_y_end) / 2
            nodes.append({
                "id": branch_id,
                "text": branch.get("text", ""),
                "stroke": color,
                "style": {},
                "x": x_l2,
                "y": round(branch_y),
                "layout": None,
                "isExpand": True,
                "pid": root_id
            })

            children = branch.get("children", [])
            if not children:
                current_y += V_SPACING + BRANCH_GAP
                continue

            if max_depth > 1:
                current_y = layout_children(
                    children, branch_id, color, sign, 2, branch_y_start
                )
            else:
                current_y = branch_y_start + V_SPACING

            current_y += BRANCH_GAP

    # ── Calculate vertical extents ──
    right_leaves, right_gaps = side_leaf_count(right_branches)
    left_leaves, left_gaps = side_leaf_count(left_branches)

    right_total_height = right_leaves * V_SPACING + right_gaps * BRANCH_GAP
    left_total_height = left_leaves * V_SPACING + left_gaps * BRANCH_GAP

    right_start_y = ROOT_Y - right_total_height / 2
    left_start_y = ROOT_Y - left_total_height / 2

    layout_side(right_branches, "right", right_start_y)
    layout_side(left_branches, "left", left_start_y)

    return nodes


def generate_free_nodes(count=8):
    """Generate empty free nodes as required by MarkMind Rich format."""
    free = []
    for _ in range(count):
        free.append([{
            "id": generate_id("fn"),
            "text": "freeNode",
            "main": False,
            "x": 0,
            "y": 0,
            "layout": {"layoutName": "mindmap2", "direct": "mindmap"},
            "isExpand": True,
            "stroke": "",
            "style": {}
        }])
    return free


def build_markmind_json(nodes):
    """Assemble the complete MarkMind Rich JSON structure."""
    free_nodes = generate_free_nodes(8)
    mind_data = [nodes] + free_nodes

    return {
        "theme": "",
        "mindData": mind_data,
        "induceData": [],
        "wireFrameData": [],
        "relateLinkData": [],
        "calloutData": [],
        "opt": {
            "background": "transparent",
            "fontFamily": "",
            "fontSize": 16
        },
        "scrollLeft": ROOT_X - 817,
        "scrollTop": ROOT_Y - 370,
        "transformOrigin": [ROOT_X + 133.5, ROOT_Y + 160]
    }


def wrap_markdown(json_str):
    """Wrap JSON in MarkMind Rich markdown format."""
    return f"""---

mindmap-plugin: rich

---

# Root
``` json
{json_str}
```
"""


def main():
    parser = argparse.ArgumentParser(
        description="Generate Obsidian MarkMind Rich .md file from brainstorming outline"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output .md file path"
    )
    parser.add_argument(
        "--input", "-i",
        default=None,
        help="Input JSON file (default: stdin)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=4,
        help=f"Maximum depth levels below root (default: 4, range: 1-{MAX_DEPTH_LIMIT})"
    )
    args = parser.parse_args()

    # Clamp max_depth to valid range
    if args.max_depth < 1 or args.max_depth > MAX_DEPTH_LIMIT:
        print(f"Warning: max-depth clamped to range 1-{MAX_DEPTH_LIMIT} (was {args.max_depth})", file=sys.stderr)
        args.max_depth = max(1, min(MAX_DEPTH_LIMIT, args.max_depth))

    # Read input
    try:
        if args.input:
            with open(args.input, "r", encoding="utf-8") as f:
                outline = json.load(f)
        else:
            outline = json.load(sys.stdin)
    except FileNotFoundError:
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON input: {e.msg}", file=sys.stderr)
        sys.exit(1)

    # Validate
    if not isinstance(outline.get("root"), str):
        print("Error: JSON must have a 'root' string key", file=sys.stderr)
        sys.exit(1)
    if not isinstance(outline.get("branches"), list):
        print("Error: JSON must have a 'branches' list key", file=sys.stderr)
        sys.exit(1)

    # Build
    nodes = build_nodes(outline, max_depth=args.max_depth)
    markmind = build_markmind_json(nodes)
    json_str = json.dumps(markmind, ensure_ascii=False, separators=(",", ":"))

    # Write
    md_content = wrap_markdown(json_str)
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md_content)
    except OSError as e:
        print(f"Error: could not write output file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Generated: {args.output}", file=sys.stderr)
    print(f"Total nodes: {len(nodes)}", file=sys.stderr)


if __name__ == "__main__":
    main()
