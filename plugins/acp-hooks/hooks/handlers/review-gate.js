// Review Gate - PreToolUse hook (disablable)
// Blocks PR creation and merges to main/master until /code-review is run
// Toggle: set "reviewGate" to false in ~/.claude/acp-config.json to disable

const fs = require("fs");
const path = require("path");

const configPath = path.join(process.env.HOME || process.env.USERPROFILE, ".claude", "acp-config.json");

// Check if review gate is enabled
let enabled = true;
try {
  const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  if (config.reviewGate === false) {
    enabled = false;
  }
} catch {
  // No config file = enabled by default
}

if (!enabled) {
  process.exit(0);
}

// Get the tool event from stdin
let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  try {
    const event = JSON.parse(input);
    const toolName = event.tool_name || "";

    // Only check Bash commands
    if (toolName !== "Bash") {
      process.exit(0);
    }

    const command = (event.tool_input?.command || "").trim();

    // Bypass: --no-review escape hatch
    if (command.includes("--no-review")) {
      process.exit(0);
    }

    let triggered = false;
    let reason = "";

    // Check for PR creation
    if (/\bgh\s+pr\s+create\b/.test(command)) {
      triggered = true;
      reason = "PR creation detected. Run /code-review before creating a PR, then retry this command.";
    }

    // Check for merge INTO main/master
    if (!triggered && /\bgit\s+merge\b/.test(command)) {
      // Get the current branch to determine if we're ON main/master (merging into it)
      // The merge target is the current branch, not the argument
      // "git merge feature-x" while on main = merging INTO main = block
      // We can't easily detect the current branch from the command alone,
      // so we check if the merge source is NOT main/master
      // (if source IS main/master, user is merging main into feature = fine)
      const mergeMatch = command.match(/\bgit\s+merge\s+(?:--[^\s]+\s+)*([^\s-][^\s]*)/);
      if (mergeMatch) {
        const mergeSource = mergeMatch[1];
        // If merging FROM a non-main branch, user might be on main - block to be safe
        // If merging FROM main/master, user is on a feature branch pulling in main - allow
        if (!/^(main|master)$/.test(mergeSource)) {
          triggered = true;
          reason = "Merge detected that may target main/master. Run /code-review before merging to main/master, then retry this command. If this merge does not target main/master, add --no-review to bypass.";
        }
      }
    }

    if (!triggered) {
      process.exit(0);
    }

    const output = {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        decision: "block",
        reason: reason
      }
    };

    process.stdout.write(JSON.stringify(output));
  } catch {
    // If we can't parse input, allow the operation
    process.exit(0);
  }
});
