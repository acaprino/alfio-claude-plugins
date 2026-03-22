// Skill Awareness - SessionStart hook
// Injects the anvil-forge skill content into every session so Claude
// knows to check for and invoke relevant skills before responding.
// Mirrors the pattern from obra/superpowers using-superpowers hook.

const fs = require("fs");
const path = require("path");

const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, "../..");
const anvilToolsetRoot = path.resolve(pluginRoot, "../..");

// Try multiple path patterns to find anvil-forge SKILL.md:
// 1. Dev layout:        <root>/plugins/ai-tooling/skills/anvil-forge/SKILL.md
// 2. Marketplace cache: <root>/ai-tooling/<version>/skills/anvil-forge/SKILL.md
function findSkillFile() {
  // Pattern 1: dev layout (running from source repo)
  const devPath = path.join(anvilToolsetRoot, "plugins", "ai-tooling", "skills", "anvil-forge", "SKILL.md");
  if (fs.existsSync(devPath)) return devPath;

  // Pattern 2: marketplace cache (each plugin in its own versioned dir)
  const cacheDir = path.join(anvilToolsetRoot, "ai-tooling");
  if (fs.existsSync(cacheDir)) {
    try {
      const versions = fs.readdirSync(cacheDir).sort().reverse();
      for (const ver of versions) {
        const cachePath = path.join(cacheDir, ver, "skills", "anvil-forge", "SKILL.md");
        if (fs.existsSync(cachePath)) return cachePath;
      }
    } catch {}
  }

  return null;
}

const skillPath = findSkillFile();
if (!skillPath) process.exit(0);

let skillContent = "";
try {
  skillContent = fs.readFileSync(skillPath, "utf8");
} catch {
  process.exit(0);
}

try {
  const context = `<IMPORTANT>\nYou have the Anvil skill system.\n\n**Below is the full content of your 'ai-tooling:anvil-forge' skill -- your guide to using skills. For all other skills, use the 'Skill' tool:**\n\n${skillContent}\n</IMPORTANT>`;

  const output = {
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: context
    }
  };

  process.stdout.write(JSON.stringify(output));
} catch {
  // Silent fail -- never block session startup
  process.exit(0);
}
