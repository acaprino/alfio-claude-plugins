// Background Exec Nudge - PreToolUse hook (matcher: Bash)
// On a long-running or never-exiting Bash command (dev server, watcher, tail),
// encourages background execution and token-efficient polling. Self-cancelling
// for short-lived commands.
// Re-ported to JS from upstream severity1/claude-code-prompt-improver
// nudges/PreToolUse/10-background-exec.json (v0.6.0 nudge engine).

const LONG_RUNNING_PATTERNS = [
  /\b(npm|pnpm|yarn|bun)\s+(run\s+)?(dev|start|serve|watch)\b/i,
  /\b(vite|webpack(-dev-server)?|nodemon|next\s+dev|rails\s+server|flask\s+run|uvicorn|gunicorn)\b/i,
  /--watch\b/i,
  /\btail\s+-[fF]\b/i,
  /\b(http\.server|live-server|serve)\b/i
];

function outputJson(text) {
  const output = {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      additionalContext: text
    }
  };
  process.stdout.write(JSON.stringify(output));
}

async function readStdin() {
  process.stdin.setEncoding("utf8");
  let raw = "";
  for await (const chunk of process.stdin) {
    raw += chunk;
  }
  return raw;
}

async function main() {
  try {
    const raw = await readStdin();
    let command = "";
    try {
      const data = JSON.parse(raw);
      command = (data.tool_input && data.tool_input.command) || "";
    } catch {
      // Unparseable input: stay silent.
      process.exit(0);
    }

    if (!command || !LONG_RUNNING_PATTERNS.some((re) => re.test(command))) {
      process.exit(0);
    }

    const guidance = [
      "This looks like a long-running or never-exiting process (dev server, watcher, tail). Run it in the background rather than blocking the turn.",
      "Design for token efficiency: when you poll it, surface only the output that matters: the error, the 'ready' line, the specific signal you are waiting for. Filter at the source (grep, tail, --quiet) instead of piping whole logs into context.",
      "If this command is short-lived, ignore this guidance."
    ].join(" ");

    outputJson(guidance);
  } catch (error) {
    process.stderr.write(`[Background Exec Hook Error] ${error.message}\n`);
    // Silent fail - never block the tool call.
    process.exit(0);
  }
}

main();
