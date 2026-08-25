#!/usr/bin/env python3
"""
generate_forcegraph.py

Generates a single self-contained interactive HTML file from a mindmap JSON outline
using force-graph (https://github.com/vasturiano/force-graph).

Input: JSON with standard mindmap outline format (root + branches + children).
Output: .html file with interactive force-directed graph (requires internet for CDN).

Usage:
  python generate_forcegraph.py --input outline.json --output mindmap.html
  cat outline.json | python generate_forcegraph.py --output mindmap.html
"""

import json
import sys
import argparse
import html


MAX_DEPTH_DEFAULT = 6
MAX_DEPTH_LIMIT = 10


def flatten_tree(outline, max_depth=MAX_DEPTH_DEFAULT):
    """Convert the mindmap tree into flat nodes and links lists."""
    nodes = []
    links = []
    node_id = 0

    def walk(item, parent_id, depth, branch_color):
        nonlocal node_id
        if depth > max_depth:
            return

        current_id = node_id
        node_id += 1

        text = item.get("text", item.get("root", ""))
        color = item.get("color", branch_color)

        nodes.append({
            "id": current_id,
            "label": text,
            "depth": depth,
            "color": color,
        })

        if parent_id is not None:
            links.append({
                "source": parent_id,
                "target": current_id,
                "color": color,
            })

        for child in item.get("children", []):
            walk(child, current_id, depth + 1, color)

    # Root node
    root_id = node_id
    node_id += 1
    nodes.append({
        "id": root_id,
        "label": outline["root"],
        "depth": 0,
        "color": "#ffffff",
    })

    for branch in outline.get("branches", []):
        branch_color = branch.get("color", "#888888")
        walk(branch, root_id, 1, branch_color)

    return nodes, links


def generate_html(nodes, links, title):
    """Generate the interactive HTML file content."""
    graph_data = json.dumps({"nodes": nodes, "links": links}, ensure_ascii=True)
    # Prevent </script> injection in JSON embedded inside <script> tag
    graph_data = graph_data.replace("</", "<\\/")
    safe_title = html.escape(title)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #1a1a2e; overflow: hidden; font-family: system-ui, -apple-system, sans-serif; }}
  #graph {{ width: 100vw; height: 100vh; }}
  #info {{
    position: fixed; top: 16px; left: 16px; z-index: 10;
    background: rgba(26, 26, 46, 0.85); color: #e0e0e0;
    padding: 12px 18px; border-radius: 8px; font-size: 13px;
    backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.1);
    max-width: 320px; pointer-events: none;
  }}
  #info h2 {{ font-size: 15px; margin-bottom: 6px; color: #fff; }}
  #info p {{ opacity: 0.7; line-height: 1.4; }}
</style>
</head>
<body>
<div id="info">
  <h2>{safe_title}</h2>
  <p>Drag to pan. Scroll to zoom. Click a node to focus.</p>
</div>
<div id="graph"></div>
<script src="https://unpkg.com/force-graph@1.48.0/dist/force-graph.min.js"></script>
<script>
(function() {{
  const data = {graph_data};

  const sizeByDepth = {{ 0: 14, 1: 8, 2: 5, 3: 3.5, 4: 2.5, 5: 2, 6: 1.5 }};

  const graph = ForceGraph()(document.getElementById('graph'))
    .graphData(data)
    .backgroundColor('#1a1a2e')
    .nodeLabel(n => n.label)
    .nodeVal(n => sizeByDepth[n.depth] || 1.5)
    .nodeColor(n => n.depth === 0 ? '#ffffff' : n.color)
    .nodeCanvasObject((node, ctx, globalScale) => {{
      const size = sizeByDepth[node.depth] || 1.5;
      const r = Math.sqrt(size) * 3;

      // Node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
      ctx.fillStyle = node.depth === 0 ? '#ffffff' : node.color;
      ctx.fill();

      // Label
      const fontSize = Math.max(12 / globalScale, node.depth === 0 ? 5 : 3);
      ctx.font = (node.depth === 0 ? 'bold ' : '') + fontSize + 'px system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = node.depth === 0 ? '#ffffff' : node.color;
      ctx.fillText(node.label, node.x, node.y + r + 2);
    }})
    .nodeCanvasObjectMode(() => 'replace')
    .linkColor(l => l.color + '66')
    .linkWidth(l => 1.5)
    .linkDirectionalParticles(1)
    .linkDirectionalParticleWidth(2)
    .linkDirectionalParticleColor(l => l.color)
    .d3Force('charge').strength(n => n.depth === 0 ? -400 : -120);

  const nodeMap = Object.fromEntries(data.nodes.map(n => [n.id, n]));
  graph.d3Force('link').distance(l => {{
    const src = nodeMap[typeof l.source === 'object' ? l.source.id : l.source];
    return src && src.depth === 0 ? 120 : 60;
  }});

  // Click to zoom
  graph.onNodeClick(node => {{
    graph.centerAt(node.x, node.y, 800);
    graph.zoom(3, 800);
  }});

  // Initial zoom to fit
  setTimeout(() => graph.zoomToFit(400, 40), 500);
}})();
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Generate interactive force-graph HTML from mindmap JSON outline"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output .html file path"
    )
    parser.add_argument(
        "--input", "-i",
        default=None,
        help="Input JSON file (default: stdin)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=MAX_DEPTH_DEFAULT,
        help=f"Maximum depth levels below root (default: {MAX_DEPTH_DEFAULT}, max: {MAX_DEPTH_LIMIT})"
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
        print(f"Error: invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate
    if not isinstance(outline.get("root"), str):
        print("Error: JSON must have a 'root' string key", file=sys.stderr)
        sys.exit(1)
    if not isinstance(outline.get("branches"), list):
        print("Error: JSON must have a 'branches' list key", file=sys.stderr)
        sys.exit(1)

    # Build
    nodes, links = flatten_tree(outline, max_depth=args.max_depth)
    title = outline["root"]
    html_content = generate_html(nodes, links, title)

    # Write
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html_content)
    except OSError as e:
        print(f"Error: could not write output file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Generated: {args.output}", file=sys.stderr)
    print(f"Total nodes: {len(nodes)}, links: {len(links)}", file=sys.stderr)


if __name__ == "__main__":
    main()
