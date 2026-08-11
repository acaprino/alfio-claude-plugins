# Case 6: Discovery stays high-recall even when the report is empty

**Guards:** the agent's discovery step (four search families run per concept), the report's Coverage line format ("Concepts censused: <n> | with more than one representation: <n>").

**Why it decays:** on a genuinely clean codebase, a shortcut that skips the census entirely and a real census that finds nothing produce the same visible output, an empty report. That makes the corner-cutting invisible from the report alone, so a future edit trading search thoroughness for speed on unpromising-looking codebases has no user-facing signal warning it happened, until the same shortcut is applied to a codebase that was not actually clean.

**Stimulus:**

> A small codebase of a dozen files, each with a distinct, non-overlapping responsibility and no duplicated logic, no repeated policy, and no parallel representations of anything. Audit it.

**Assertion (PASS):** the report is empty or near-empty, and the Gaps or Coverage section states concrete numbers: concepts censused, representations read, searches run per concept.

**Assertion (FAIL):** the report states there is nothing to find without any accompanying evidence that a census was actually run, for example no concept count anywhere in the output.
