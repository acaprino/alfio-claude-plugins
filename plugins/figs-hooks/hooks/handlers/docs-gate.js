// Docs Gate - PreToolUse hook (disablable, conditional by default)
// Blocks PR creation and merges to main/master when docs may need auditing
// Toggle: set "docsGate" to false in ~/.claude/figs-config.json to disable
// Mode: set "docsGateMode" to "always" to block unconditionally (default: "conditional")

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const configPath = path.join(process.env.HOME || process.env.USERPROFILE, ".claude", "figs-config.json");

// Read config
let enabled = true;
let mode = "conditional";
try {
  const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  if (config.docsGate === false) {
    enabled = false;
  }
  if (config.docsGateMode === "always") {
    mode = "always";
  }
} catch {
  // No config file = enabled by default, conditional mode
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

    // Bypass: --no-docs escape hatch
    if (command.includes("--no-docs")) {
      process.exit(0);
    }

    let triggered = false;

    // Check for PR creation
    if (/\bgh\s+pr\s+create\b/.test(command)) {
      triggered = true;
    }

    // Check for merge INTO main/master (same logic as review-gate)
    if (!triggered && /\bgit\s+merge\b/.test(command)) {
      const mergeMatch = command.match(/\bgit\s+merge\s+(?:--[^\s]+\s+)*([^\s-][^\s]*)/);
      if (mergeMatch) {
        const mergeSource = mergeMatch[1];
        if (!/^(main|master)$/.test(mergeSource)) {
          triggered = true;
        }
      }
    }

    if (!triggered) {
      process.exit(0);
    }

    // In conditional mode, check if doc files are in the diff
    if (mode === "conditional") {
      try {
        let diffOutput = "";
        try {
          diffOutput = execSync("git diff --cached --name-only", { encoding: "utf8", timeout: 5000 });
        } catch {
          // fallback
        }
        if (!diffOutput.trim()) {
          try {
            diffOutput = execSync("git diff --name-only HEAD", { encoding: "utf8", timeout: 5000 });
          } catch {
            // If we can't get diff, allow the operation
            process.exit(0);
          }
        }

        const files = diffOutput.trim().split("\n").filter(Boolean);
        const docPatterns = [
          /\.md$/i,
          /^docs\//i,
          /^readme/i,
          /^changelog/i
        ];

        const hasDocFiles = files.some((f) =>
          docPatterns.some((p) => p.test(f))
        );

        if (!hasDocFiles) {
          process.exit(0);
        }
      } catch {
        // If diff check fails entirely, allow the operation
        process.exit(0);
      }
    }

    const reason = mode === "always"
      ? "Run /docs-maintain before creating a PR, then retry. Add --no-docs to bypass."
      : "Documentation changes detected. Run /docs-maintain before creating a PR, then retry. Add --no-docs to bypass.";

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
