// Figs ASCII Logo - SessionStart hook
// When running inside Figs (FIGS_SESSION=1), suppress Claude's banner
// since Figs shows its own AsciiLogo overlay in Terminal.tsx.
// Outside Figs, this hook is a no-op -- Claude's default banner shows normally.

try {
  if (process.env.FIGS_SESSION === "1") {
    // Inside Figs: emit empty hookSpecificOutput to suppress Claude's banner
    const output = JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "SessionStart",
      },
    });
    process.stdout.write(output);
  }
  // Outside Figs: output nothing, Claude shows its own logo
} catch {
  process.exit(0);
}
