// Subagent Routing Nudge - SubagentStart hook
// Token-efficiency guidance when a research/planning agent (Explore, Plan)
// spawns. Self-cancelling: inert for agent types it does not name.
// Re-ported to JS from upstream severity1/claude-code-prompt-improver
// nudges/SubagentStart/00-subagent-routing.json (v0.6.0 nudge engine).

const MATCHED_AGENT_TYPES = /\b(Explore|Plan)\b/;

function outputJson(text) {
  const output = {
    hookSpecificOutput: {
      hookEventName: "SubagentStart",
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
    let agentType = "";
    try {
      const data = JSON.parse(raw);
      agentType = data.agent_type || data.agentType || data.subagent_type || "";
    } catch {
      process.exit(0);
    }

    if (!agentType || !MATCHED_AGENT_TYPES.test(agentType)) {
      process.exit(0);
    }

    const guidance = [
      "If this is a broad read-only research or planning pass: favor breadth over depth.",
      "Read excerpts rather than whole files, return conclusions rather than raw dumps, and keep the report tight so the parent context stays lean.",
      "If this agent is doing focused implementation work instead, ignore this guidance."
    ].join(" ");

    outputJson(guidance);
  } catch (error) {
    process.stderr.write(`[Subagent Routing Hook Error] ${error.message}\n`);
    // Silent fail - never block the subagent.
    process.exit(0);
  }
}

main();
