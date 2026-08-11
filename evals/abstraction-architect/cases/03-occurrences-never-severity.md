# Case 3: Occurrence count never sets severity

**Guards:** `references/dimensions.md` "Occurrences are evidence, never severity", `references/decision-frame.md` severity calibration.

**Why it decays:** a count is the easiest thing to compute and sort by, and a future edit optimizing the report for scannability, for example sorting findings so the most-duplicated thing surfaces first, reintroduces exactly the mapping the plugin was rebuilt to reject: two occurrences read as minor, four as major, regardless of what each pair or quartet actually costs.

**Stimulus:**

> Two independent modules each define their own authoritative rule for whether a user has admin permission, and they can disagree. Separately, four files each hardcode the same date-format string on a logging path nobody has touched in two years. Audit it.

**Assertion (PASS):** the permission finding is High, argued from the security consequence of two competing authorities, not from having only two occurrences. The date-format finding is Low, argued from the absence of concrete pressure, not from having four occurrences.

**Assertion (FAIL):** severity tracks the occurrence count in either direction, for example the permission finding downgraded for having "only two" instances, or the date-format finding upgraded for having "four" instances.
