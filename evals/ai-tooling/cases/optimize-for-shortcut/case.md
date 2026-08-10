# Case: optimize-for-shortcut

The mirror of `frontier-preserved`. Showing the frontier is mandatory only when the user has NOT declared a target. A user who already knows their pole must not be made to answer a question they have already answered.

## Setup

None. Run in any scratch directory.

## Run

```
/prompt-optimize "You are a helpful assistant. Please carefully review the following text and provide a detailed and thorough summary that captures all of the most important points, making sure to be comprehensive and complete in your coverage of the material." --optimize-for tokens
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The efficiency pole is delivered directly; the session does not ask the user to choose a pole |
| 2 | MUST | The compression uses real technique (redundancy removal, imperative rewriting, moving reasoning cost down) rather than only deleting adjectives, and says which technique it applied |
| 3 | MUST | The token claim is labeled as an estimate with its method stated, not asserted as measured |
| 4 | SHOULD | The trade-off accepted in exchange for the token saving is named, even though the user chose the pole |

## Scoring notes

This source prompt is deliberately full of filler ("please carefully", "detailed and thorough", "comprehensive and complete"). A large token reduction is expected and is not itself the assertion. Assertion 2 fails if the output is only a shorter paraphrase with no named technique, because that is the behavior the efficiency pole was redesigned away from in 4.1.0.
