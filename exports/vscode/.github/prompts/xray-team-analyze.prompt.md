---
description: Systematic codebase X-ray. Auto-detects partitions (workspaces, dirs, language clusters), dispatches workers per partition across 2 waves, consolidates into a 01..07.md report set, then maps contracts, invariants, and integration hot-spots into 08-interconnect-map.md. Concurrent-safe runs under .deep-dive/.
agent: xray-orchestrator
argument-hint: <target> [--critical] [--comments] [--depth=lite|full] [--docs-only] [--partition <path>] [--skip-interconnect] [--skip-synthesis] [--run-name <name>] [--yes]
---

# X-Ray Analysis

Run the codebase X-ray pipeline on the target the user named in the chat input after `/xray-team-analyze`.

Expected form: `<target> [--critical] [--comments] [--depth=lite|full] [--docs-only] [--partition <path>] [--partition-name <name>] [--skip-interconnect] [--skip-synthesis] [--run-name <name>] [--yes]`

If no target was given, ask for the path and any flags with `#vscode/askQuestions` before doing anything else. Do not assume the workspace root.

Reject `--phase N` with an explicit error: phases are split across waves and workers, so starting mid-pipeline is not coherent. Suggest `--depth=lite`, `--docs-only`, or `--skip-interconnect` instead.

## Steps

1. **Resolve the skill directory.** Run with `#execute/runInTerminal`:

   ```bash
   for d in .github/skills/codebase-xray .agents/skills/codebase-xray \
            .claude/skills/codebase-xray "$HOME/.copilot/skills/codebase-xray"; do
     [ -d "$d" ] && echo "XRAY=$d" && break
   done
   ```

   On a shell without POSIX support, check the same four paths with `#search/listDirectory`. If nothing is found, stop and tell the user the `codebase-xray` skill is not installed. Everything below depends on it.

2. **Verify the subagents exist:** `xray-structure-worker`, `xray-behavior-worker`, `xray-quality-worker`, `xray-synthesizer`, `xray-interconnect-mapper`. They ship under `.github/agents/` and are declared in the `agents:` allowlist of `xray-orchestrator`. If `#agent/runSubagent` is unavailable, say so explicitly, then fall back to executing each worker role inline, one partition at a time, reading the agent definition for the phase spec and output template. Do not degrade silently.

3. **Read `$XRAY/SKILL.md`** for the concurrent runs model, the source-of-truth principle, the forbidden-files list, and the script CLI reference.

4. **Read `$XRAY/references/workflow.md`** for the full pipeline: pre-flight, run resolution, partition detection, the scope checkpoint, two-wave dispatch, barriers, synthesis, interconnect map, publish, and the next-steps menu.

5. **Execute.** Stop at the partition checkpoint unless `--yes` was passed. Do not improvise the phase structure or the output file names: downstream consumers read `.deep-dive/01-structure.md` through `08-interconnect-map.md` by exact path.

Read the other references (`AI_ANALYSIS_METHODOLOGY.md`, `SEMANTIC_PATTERNS.md`, `ANTIREZ_COMMENTING_STANDARDS.md`, `analysis-templates.md`) on demand when a phase calls for them. Do not preload them.

## Notes

- Small single-package repos are handled by the single-partition fallback (one partition named `root`). There is no separate lightweight command.
- The wave barriers are file-existence based: Wave 2 starts only once every partition has both `01-structure.md` and `02-interfaces.md` on disk, verified with `#search/fileSearch`. Do not trust worker summaries alone.
- Each worker owns an explicit file list. With `chat.useCustomAgentHooks` enabled, the workers' `PreToolUse` guard also confines writes to `.deep-dive/**`, so an off-contract write fails at the tool layer rather than silently corrupting a sibling partition.
- The scripts under `$XRAY/scripts/` require Python >= 3.10 and work with the stdlib alone. Tree-sitter is optional and improves Java, JavaScript, TypeScript, and Rust fidelity.
