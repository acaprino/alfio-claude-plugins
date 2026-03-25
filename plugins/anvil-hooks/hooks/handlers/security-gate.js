// Security Gate - PostToolUse hook (disablable)
// Checks for hardcoded secrets in Write/Edit operations
// Toggle: set "securityGate" to false in ~/.claude/figs-config.json to disable

const fs = require("fs");
const path = require("path");

const configPath = path.join(process.env.HOME || process.env.USERPROFILE, ".claude", "figs-config.json");

// Check if security gate is enabled
let enabled = true;
try {
  const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  if (config.securityGate === false) {
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

    // Only check Write and Edit operations
    if (toolName !== "Write" && toolName !== "Edit") {
      process.exit(0);
    }

    const filePath = event.tool_input?.file_path || "";
    const ext = path.extname(filePath).toLowerCase();

    // Skip non-source files
    const skipExts = [".env", ".json", ".md", ".sql", ".lock", ".toml", ".yaml", ".yml", ".xml", ".csv"];
    const skipPatterns = ["migration", "config", ".env"];

    if (skipExts.includes(ext)) {
      process.exit(0);
    }

    if (skipPatterns.some(p => filePath.toLowerCase().includes(p))) {
      process.exit(0);
    }

    // Check content for potential secrets
    const content = event.tool_input?.content || event.tool_input?.new_string || "";

    // Common secret patterns
    const secretPatterns = [
      /(?:api[_-]?key|apikey)\s*[:=]\s*["'][a-zA-Z0-9_\-]{20,}["']/i,
      /(?:secret|password|passwd|pwd)\s*[:=]\s*["'][^"']{8,}["']/i,
      /(?:token)\s*[:=]\s*["'][a-zA-Z0-9_\-]{20,}["']/i,
      /(?:sk|pk)[-_](?:live|test)[-_][a-zA-Z0-9]{20,}/,
      /(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}/,
      /xox[bpors]-[a-zA-Z0-9\-]{10,}/,
      /eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}/,
      /AKIA[0-9A-Z]{16}/,
      /-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----/,
    ];

    for (const pattern of secretPatterns) {
      if (pattern.test(content)) {
        console.error(`\x1b[31m[Security Gate]\x1b[0m Potential hardcoded secret detected in ${path.basename(filePath)}`);
        console.error(`Pattern matched: ${pattern.source.substring(0, 40)}...`);
        console.error("Move secrets to .env or a secure vault.");
        process.exit(1);
      }
    }

    process.exit(0);
  } catch {
    // If we can't parse input, allow the operation
    process.exit(0);
  }
});
