---
description: >
  Generate a mind map in Obsidian MarkMind Rich format from any topic, text, or file.
  TRIGGER WHEN: the user asks for a MarkMind mind map, mappa mentale for Obsidian, or visual concept map in Obsidian-compatible format.
  DO NOT TRIGGER WHEN: the user wants a force-graph web mindmap (use learning:forcegraph-exporter) or just a text outline.
argument-hint: "<topic | \"text to map\" | path/to/file.md>"
---

Generate a MarkMind mind map for: $ARGUMENTS

Execute immediately -- no plan mode. This command chains two skills:

1. **Generate mindmap outline** (skill: `learning:generate-mindmap`): brainstorm internally (do not show to user), identify the central theme (2-4 words), extract branches and sub-concepts scaled to complexity level, assign emoji and colors. Save the JSON outline to a temporary file.

2. **Render to MarkMind** (skill: `learning:markmind-exporter`): pipe the JSON outline to `${CLAUDE_PLUGIN_ROOT}/skills/markmind-exporter/scripts/generate_markmind.py` with `--output` flag to produce the `.md` file.

3. **Present the `.md` file** to the user, ready to drop into their Obsidian vault with the MarkMind plugin.

See `learning:generate-mindmap` for content principles, emoji semantic code, and color palette.
See `learning:markmind-exporter` for the renderer script usage and MarkMind Rich format details.
