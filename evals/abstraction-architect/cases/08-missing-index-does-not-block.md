# Case 8: A missing concept index does not block diff mode

**Guards:** the agent's mode-selection notes ("With no X-ray output at all, diff runs on the concept index plus Glob and Grep, at reduced confidence, and says so in Gaps"), `references/concept-index-protocol.md` `unusable` freshness state.

**Why it decays:** requiring an index before auditing sounds like responsible caution, no baseline means no reliable diff, and a future edit worried about false negatives from an ungrounded run could turn the documented graceful degradation into a hard precondition. That is the shape a defensive-sounding change takes, which is what makes it likely to survive review.

**Stimulus:**

> Run diff mode against a repository that has never had `.abstraction-architect/concept-index.json` generated, auditing a change that touches a handful of files.

**Assertion (PASS):** the review completes and produces findings from diff-anchored discovery alone. Gaps names the reduced coverage specifically, for example that no concept index was available and global competing-authority coverage was not attempted.

**Assertion (FAIL):** the run aborts, or the report states that an index is required before auditing can proceed.
