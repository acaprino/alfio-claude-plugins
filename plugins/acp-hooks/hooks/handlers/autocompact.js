// Autocompact - PostToolUse hook (configurable)
// Triggers context compaction when usage approaches 100%.
// Toggle: set "autocompact" to false in ~/.claude/acp-config.json to disable
// Threshold: set "autocompactThreshold" (0-100) in acp-config.json (default: 80)
//
// Reads context metrics from the statusline bridge file written by
// gsd-statusline.js. When used_pct exceeds the threshold, injects an
// additionalContext message instructing Claude to /compact.
//
// Cooldown: fires once per threshold crossing per session.

const fs = require("fs");
const os = require("os");
const path = require("path");

const DEFAULT_THRESHOLD = 80;
const STALE_SECONDS = 60;

const configPath = path.join(process.env.HOME || process.env.USERPROFILE, ".claude", "acp-config.json");

// Check config: enabled + threshold
let enabled = true;
let threshold = DEFAULT_THRESHOLD;
try {
  const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  if (config.autocompact === false) {
    enabled = false;
  }
  if (typeof config.autocompactThreshold === "number") {
    threshold = Math.max(50, Math.min(99, config.autocompactThreshold));
  }
} catch {
  // No config file = enabled with default threshold
}

if (!enabled) {
  process.exit(0);
}

let input = "";
const stdinTimeout = setTimeout(() => process.exit(0), 3000);
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const sessionId = data.session_id;

    if (!sessionId) {
      process.exit(0);
    }

    const tmpDir = os.tmpdir();
    const metricsPath = path.join(tmpDir, `claude-ctx-${sessionId}.json`);

    if (!fs.existsSync(metricsPath)) {
      process.exit(0);
    }

    const metrics = JSON.parse(fs.readFileSync(metricsPath, "utf8"));
    const now = Math.floor(Date.now() / 1000);

    // Ignore stale metrics
    if (metrics.timestamp && (now - metrics.timestamp) > STALE_SECONDS) {
      process.exit(0);
    }

    const usedPct = metrics.used_pct;

    // Not yet at threshold
    if (usedPct < threshold) {
      process.exit(0);
    }

    // Cooldown: only trigger once per threshold crossing
    const cooldownPath = path.join(tmpDir, `claude-autocompact-${sessionId}.json`);
    if (fs.existsSync(cooldownPath)) {
      try {
        const cooldown = JSON.parse(fs.readFileSync(cooldownPath, "utf8"));
        if (cooldown.triggered && cooldown.threshold >= threshold) {
          process.exit(0);
        }
      } catch {
        // Corrupted, proceed
      }
    }

    // Mark as triggered
    fs.writeFileSync(cooldownPath, JSON.stringify({
      triggered: true,
      usedPct,
      threshold,
      timestamp: now
    }));

    const output = {
      hookSpecificOutput: {
        hookEventName: "PostToolUse",
        additionalContext:
          `AUTOCOMPACT: Context usage is at ${usedPct}% (threshold: ${threshold}%). ` +
          "You MUST run /compact now to free up context before it is exhausted. " +
          "Finish your current thought, then immediately compact."
      }
    };

    process.stdout.write(JSON.stringify(output));
  } catch {
    // Silent fail - never block tool execution
    process.exit(0);
  }
});
