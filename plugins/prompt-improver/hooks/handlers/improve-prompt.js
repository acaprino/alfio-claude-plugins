// Prompt Improver - UserPromptSubmit hook
// Evaluates prompts for clarity and invokes the prompt-improver skill for vague cases.

function outputJson(text) {
  const output = {
    hookSpecificOutput: {
      hookEventName: "UserPromptSubmit",
      additionalContext: text
    }
  };
  process.stdout.write(JSON.stringify(output));
}

async function main() {
  try {
    let input = "";
    process.stdin.setEncoding("utf8");
    
    // Modern approach to reading from stdin
    for await (const chunk of process.stdin) {
      input += chunk;
    }

    const event = JSON.parse(input);
    const prompt = (event.prompt || "").trim();

    if (!prompt) {
      process.exit(0);
    }

    // Bypass: explicit * prefix (user opted out)
    if (prompt.startsWith("*")) {
      outputJson(prompt.slice(1).trim());
      process.exit(0);
    }

    // Bypass: slash commands and memorize feature
    if (prompt.startsWith("/") || prompt.startsWith("#")) {
      process.exit(0);
    }

    // Build the evaluation wrapper using XML tags (Claude's preferred format)
    // This entirely removes the need for manual regex string escaping.
    const wrapped = `PROMPT EVALUATION

<original_request>
${prompt}
</original_request>

EVALUATE: Is this prompt clear enough to execute, or does it need enrichment?

PROCEED IMMEDIATELY if:
- Detailed/specific OR you have sufficient context OR can infer intent

ONLY USE SKILL if genuinely vague (e.g., "fix the bug" with no context):
- If vague:
  1. First, preface with brief note: "Hey! The Prompt Improver Hook flagged your prompt as a bit vague because [specific reason: ambiguous scope/missing context/unclear target/etc]."
  2. Then use the prompt-improver skill to research and generate clarifying questions
- The skill will guide you through research, question generation, and execution
- Trust user intent by default. Check conversation history before using the skill.

If clear, proceed with the original request. If vague, invoke the skill.`;

    outputJson(wrapped);
    
  } catch (error) {
    // Write to stderr so it doesn't break stdout JSON parsing, but allows for debugging
    process.stderr.write(`[Prompt Improver Hook Error] ${error.message}\n`);
    // Silent fail - never block prompt submission
    process.exit(0);
  }
}

main();