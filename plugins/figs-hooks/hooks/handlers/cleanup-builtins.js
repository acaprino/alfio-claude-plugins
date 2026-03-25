// Cleanup Built-in Plugins - SessionStart hook
// Removes document-skills and example-skills plugins if installed,
// since they duplicate skills already provided by figs.

const { execFileSync } = require("child_process");

const pluginsToRemove = ["document-skills", "example-skills"];
const removed = [];

let list = "";
try {
  list = execFileSync("claude", ["plugin", "list"], {
    encoding: "utf8",
    timeout: 8000,
    stdio: ["pipe", "pipe", "pipe"],
  });
} catch {
  process.exit(0);
}

const installedLines = list.split(/\r?\n/).map(l => l.trim());

for (const plugin of pluginsToRemove) {
  if (installedLines.some(l => l === plugin || l.startsWith(plugin + " "))) {
    try {
      execFileSync("claude", ["plugin", "remove", plugin], {
        encoding: "utf8",
        timeout: 5000,
        stdio: ["pipe", "pipe", "pipe"],
      });
      removed.push(plugin);
    } catch {}
  }
}

if (removed.length > 0) {
  const msg = `Removed duplicate built-in plugins: ${removed.join(", ")}`;
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: { hookEventName: "SessionStart" },
    systemMessage: msg,
  }));
}
