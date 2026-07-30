---
description: Generate a mind map in Obsidian MarkMind Rich format from any topic, text, or file. Chains the generate-mindmap and markmind-exporter skills, then hands back a .md file ready for an Obsidian vault.
argument-hint: <topic | "text to map" | path/to/file.md>
---

# Export to MarkMind

Generate a MarkMind mind map for whatever the user named in the chat input after `/export-to-markmind`.

Execute immediately, without a planning round. This command chains two skills.

## Resolve the skills directory

The bundle can be installed in more than one place. Probe these in order and use the first that exists, calling it `$SKILLS`:

1. `.github/skills/`
2. `.agents/skills/`
3. `.claude/skills/`
4. `~/.copilot/skills/`

## Steps

1. **Generate the mindmap outline.** Load the `generate-mindmap` skill. Brainstorm internally without showing the working to the user, identify the central theme (2-4 words), extract branches and sub-concepts scaled to the complexity level, and assign emoji and colors. Save the JSON outline to a temporary file.

2. **Render to MarkMind.** Load the `markmind-exporter` skill, then pipe the JSON outline through `$SKILLS/markmind-exporter/scripts/generate_markmind.py` with the `--output` flag to produce the `.md` file. Run it with `#execute/runInTerminal`.

3. **Present the `.md` file** to the user, ready to drop into their Obsidian vault with the MarkMind plugin.

## References

- `generate-mindmap` holds the content principles, the emoji semantic code, and the color palette.
- `markmind-exporter` holds the renderer script usage and the MarkMind Rich format details.

For an interactive web mindmap instead of an Obsidian one, use the `forcegraph-exporter` skill.
