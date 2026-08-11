# Case 11: Semantic units are extracted from a diff, not only structural ones

**Guards:** the agent's semantic-unit-extraction step ("A changed literal inside an existing function is a semantic unit even when no structural unit changed... without semantic extraction D1 to D4 cannot form a hypothesis").

**Why it decays:** off-the-shelf diff tooling is built around structural change, added or modified functions and classes, so an implementation that leans on that tooling for speed or simplicity regresses to seeing only structural units. A one-line literal change produces no AST node worth diffing, so it is the first thing to silently disappear from coverage, and the disappearance looks like "nothing changed here" rather than a bug.

**Stimulus:**

> The diff changes one line: `HIGH_VALUE_THRESHOLD = 1000` becomes `HIGH_VALUE_THRESHOLD = 1500`. No function signature, class, or structural unit changes. Two other files in the codebase separately compare amounts against the literal `1000`. Audit the change.

**Assertion (PASS):** the report contains a D1 or D2 finding about the threshold, or at minimum states a hypothesis that the changed literal may now disagree with the two other hardcoded comparisons.

**Assertion (FAIL):** the report states there are no added units to examine, or is empty.
