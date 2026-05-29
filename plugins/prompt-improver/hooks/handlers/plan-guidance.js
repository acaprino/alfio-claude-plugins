// Plan Mode Guidance - PreToolUse hook (matcher: EnterPlanMode)
// Injects plan-readability guidance when Claude Code enters plan mode.
// Re-ported to JS from upstream severity1/claude-code-prompt-improver scripts/plan-guidance.py.

function outputJson(text) {
  const output = {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      additionalContext: text
    }
  };
  process.stdout.write(JSON.stringify(output));
}

async function main() {
  try {
    // Consume stdin (required by the hook protocol, but the content is unused).
    process.stdin.setEncoding("utf8");
    for await (const chunk of process.stdin) {
      void chunk;
    }

    const guidance = [
      "Plan readability guidance:",
      "Keep the problem statement; omit decision history (rejected approaches, revision rationale, prior iterations).",
      "On plan revisions, rewrite the entire plan clean; do not append revision notes or annotate what changed.",
      "Use one action per step with file paths as anchors (e.g., src/auth.ts:42).",
      "Favor terse action steps over explanatory prose."
    ].join(" ");

    outputJson(guidance);

  } catch (error) {
    // Write to stderr so it doesn't corrupt the stdout JSON, but still surfaces for debugging.
    process.stderr.write(`[Plan Guidance Hook Error] ${error.message}\n`);
    // Silent fail - never block entering plan mode.
    process.exit(0);
  }
}

main();
