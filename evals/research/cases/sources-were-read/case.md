# Case: sources-were-read

## Run
Same run as `citations-resolve` (score both from one run), reading `<stem>.researchers.md`.

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Every URL in the report's Sources section appears in some researcher's or verifier's "Sources read" / "Third source" in the companion file |
| 2 | MUST | The companion file contains one section per researcher and verifier spawned, in spawn order |
| 3 | MUST | No researcher report cites a claim with zero `[S<n>]` ids |
| 4 | SHOULD | No URL is cited from a search snippet alone (a source in the table with no corresponding fetch in the transcript) |
