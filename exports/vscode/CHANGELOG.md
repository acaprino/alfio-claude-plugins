# Changelog

## 16.2.0

First release as a VS Code extension. The catalog was previously a set of 36 `.github/` bundles you copied into each project by hand.

- 81 agents and 47 prompts register through the `chatAgents` and `chatPromptFiles` contribution points.
- 66 skills are installed into `~/.copilot/skills/` on first start, so they load in every workspace. They are copied rather than contributed because 45 of them carry supporting files, and a contributed skill loads only its `SKILL.md` ([microsoft/vscode#304721](https://github.com/microsoft/vscode/issues/304721)).
- Commands to refresh, remove and reveal the installed skills, plus the `daodan.autoSync` and `daodan.skillsLocation` settings.
- Uninstalling removes only the skills the extension installed. A skill directory it did not create is reported and left alone.
- Fixes in the `research` bundle: `quick-searcher` and `deep-researcher` were missing `websearch` in their tool lists and so could not search the web; Claude Code tool names survived in prose; `$SKILLS` was used without being defined; and `team-research` had an empty section and a mangled step list left by the original port.

The bundles are still copyable per project for anyone who wants a narrower install.
