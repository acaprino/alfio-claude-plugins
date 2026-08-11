# Case 12: A concern matching no catalogued pattern is still reported

**Guards:** `references/dimensions.md` "The catalogs are not admission gates," the agent's `Pattern: uncatalogued` instruction.

**Why it decays:** `dimensions.md` names this exact failure as the original defect the plugin was rebuilt to fix, which makes it the single most likely regression to reintroduce. Growing the pattern catalog, as an earlier task in this recentering already did by adding P13 to P18, makes the catalog look more complete each time, and that completeness is what tempts a future implementation toward treating catalog matching as a filter step rather than an illustration.

**Stimulus:**

> Three services each implement their own bespoke seniority calculation for routing support tickets to the right tier of agent, using different weightings of tenure and ticket count. The logic fits none of the eighteen catalogued unification patterns. Audit it.

**Assertion (PASS):** the finding is reported with `Pattern: uncatalogued`, described in the reviewer's own words rather than mapped onto an ill-fitting catalogued pattern.

**Assertion (FAIL):** the finding is dropped for not matching a catalogued pattern, or it is forced into the nearest pattern despite a poor fit.
