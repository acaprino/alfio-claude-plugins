# Case: citations-resolve

## Run
Fresh session, scratch directory:
```
/research:team-research "How do Rust, Go and Zig handle error propagation, and what do practitioners complain about in each?" --auto --depth standard
```

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Every `[n]` in the report body resolves to an entry `[n]` in the Sources section |
| 2 | MUST | Every entry in Sources is cited at least once in the body |
| 3 | MUST | The header carries "Citation check: done" |
| 4 | MUST | No factual sentence in Key findings lacks a citation, or it is explicitly marked unverified |
| 5 | SHOULD | Source entries carry title, site, the date the page carries, URL and an authority rank |
