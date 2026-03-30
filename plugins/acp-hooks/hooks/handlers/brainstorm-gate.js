// Brainstorm Gate - UserPromptSubmit hook
// Reminds Claude to invoke brainstorming + worktree-manager skills
// before jumping into exploration or implementation for creative/building tasks.

const TRIGGER_WORDS = ["add", "create", "build", "implement", "develop", "make", "design"];
const BYPASS_WORDS = ["fix", "debug", "resolve", "repair", "patch"];

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  try {
    const event = JSON.parse(input);
    const prompt = (event.prompt || "").trim();

    // Bypass: empty, slash commands, hash prefix (memory)
    if (!prompt || prompt.startsWith("/") || prompt.startsWith("#")) {
      process.exit(0);
    }

    // Bypass: asterisk prefix (explicit bypass)
    if (prompt.startsWith("*")) {
      process.exit(0);
    }

    // Bypass: single-word prompts
    if (!prompt.includes(" ")) {
      process.exit(0);
    }

    // Bypass: questions (ends with ?)
    if (prompt.trimEnd().endsWith("?")) {
      process.exit(0);
    }

    const lower = prompt.toLowerCase();

    // Bypass: bug fix / debug prompts
    if (BYPASS_WORDS.some((w) => lower.includes(w))) {
      process.exit(0);
    }

    // Check for trigger words (match whole words)
    const triggered = TRIGGER_WORDS.some((w) => {
      const re = new RegExp("\\b" + w + "\\b", "i");
      return re.test(lower);
    });

    if (!triggered) {
      process.exit(0);
    }

    const context = [
      "<IMPORTANT>",
      "[Brainstorm Gate] This prompt contains creative/building intent.",
      "",
      "Before exploring the codebase or writing any code, you MUST:",
      "1. Invoke the `ai-tooling:brainstorming` skill (via the Skill tool) to explore requirements and design",
      "2. Invoke the `git-worktrees:worktree-manager` skill (via the Skill tool) to check WIP state and optionally isolate work",
      "",
      "Do NOT skip these steps. Do NOT use Explore/Grep/Read first. Brainstorm and check worktree state FIRST.",
      "</IMPORTANT>"
    ].join("\n");

    const output = {
      hookSpecificOutput: {
        hookEventName: "UserPromptSubmit",
        additionalContext: context
      }
    };

    process.stdout.write(JSON.stringify(output));
  } catch {
    // Silent fail - never block prompt submission
    process.exit(0);
  }
});
