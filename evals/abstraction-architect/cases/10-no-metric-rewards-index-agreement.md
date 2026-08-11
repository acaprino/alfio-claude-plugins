# Case 10: No score or gate rewards agreement with the index or the seed map

**Guards:** `references/concept-index-protocol.md` "No metric rewards agreement," report Coverage line format.

**Why it decays:** a percentage reads as more rigorous than a raw count. "87 percent index-corroborated coverage" sounds like a maturity metric worth optimizing toward. A future dashboard-minded edit adding a coverage percentage or an index-agreement score would not look like a regression to whoever added it; it would look like a quality improvement, while quietly creating an incentive to defer to the index instead of rereading source.

**Stimulus:**

> Inspect the shipped report template and any scoring or coverage language it, or the plugin's references, define.

**Assertion (PASS):** coverage is expressed only as counts, for example concepts censused, representations read, searches run per concept, indexed concepts revalidated, unindexed concepts discovered.

**Assertion (FAIL):** any percentage, ratio, or score exists anywhere in the report template or scoring guidance that rises with index utilisation, index citation, or seed-map coverage.
