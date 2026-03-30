// ACP ASCII Logo - SessionStart hook
// When running inside ACP (ACP_SESSION=1), suppress Claude's banner
// since ACP shows its own AsciiLogo overlay in Terminal.tsx.
// Outside ACP, this hook is a no-op -- Claude's default banner shows normally.

try {
  if (process.env.ACP_SESSION === "1") {
    // Inside ACP: emit empty hookSpecificOutput to suppress Claude's banner
    const output = JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "SessionStart",
      },
    });
    process.stdout.write(output);
  }
  // Outside ACP: output nothing, Claude shows its own logo
} catch {
  process.exit(0);
}
