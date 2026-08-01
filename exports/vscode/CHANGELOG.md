# Changelog

## 17.0.0

- Tracks marketplace 17.0.0, which removed the `prompt-improver` plugin from the source marketplace. Nothing changes in the shipped bundles: that plugin was never exported (a `UserPromptSubmit` hook with no VS Code equivalent). The listing no longer describes it and the `prompt-optimize` prompt drops its routing reference to the hook.

## 16.2.3

- The React performance optimizer is decoupled from Tauri. It no longer hands off to the `tauri-development` bundle: native desktop backend work (Rust, IPC, shell configuration) is reported as out of scope instead. The direction that remains is the correct one, where `tauri-desktop` routes pure React performance work here.

## 16.2.0

First release as a VS Code extension. The catalog was previously a set of 36 `.github/` bundles you copied into each project by hand.

- 81 agents and 47 prompts register through the `chatAgents` and `chatPromptFiles` contribution points.
- 66 skills are installed into `~/.copilot/skills/` on first start, so they load in every workspace. They are copied rather than contributed because 45 of them carry supporting files, and a contributed skill loads only its `SKILL.md` ([microsoft/vscode#304721](https://github.com/microsoft/vscode/issues/304721)).
- Commands to refresh, remove and reveal the installed skills, plus the `daodan.autoSync` and `daodan.skillsLocation` settings.
- Uninstalling removes only the skills the extension installed. A skill directory it did not create is reported and left alone.
- Fixes in the `research` bundle: `quick-searcher` and `deep-researcher` were missing `websearch` in their tool lists and so could not search the web; Claude Code tool names survived in prose; `$SKILLS` was used without being defined; and `team-research` had an empty section and a mangled step list left by the original port.

The bundles are still copyable per project for anyone who wants a narrower install.
