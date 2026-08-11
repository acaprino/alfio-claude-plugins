# Case: jupiter-credential-refill

Source: production incident, 2026-08-10. A `/senior-review:team-review` run reported
a Critical finding that was false at the system level. Ground truth is the code and
the project's own documentation at the reviewed revision.

repo: D:\Projects\jupiter
review_rev: a0bb4f10
review_scope: the agent heartbeat and auto-registration modules

## must_not_report

- claim: "heartbeat responses cannot refill strategy credentials"
  why_false: >
    Two heartbeat paths exist. The periodic path carries metadata without strategy
    fields, which is true and is what the false finding was built on. The probe
    response path carries the credentials, so the refill converges.
  local_fact_that_is_true: "periodic heartbeat metadata carries no strategy fields"
  evidence:
    - docs/00_navigation/SEARCH_INDEX.md, entry "Credential Refill"
    - docs/01_domains/agents/heartbeat.md, section explaining the two paths
    - docs/01_domains/agents/auto_registration.md, the routable-but-mute record
    - the probe response handler in the agent heartbeat module
  what_should_catch_it:
    - Phase 0c should surface SEARCH_INDEX.md and heartbeat.md as leads
    - Phase 1c should record the second path under Multiplicity findings
    - Lens 0 should return REFUTED, target PREMISE, citing the probe response handler

## known_bugs

(none required: this case scores precision, not recall)

## Notes for the scorer

The failure mode is specifically that four dimensions "confirmed" the finding
independently while all four had been handed the same premise. When scoring a run,
check the consolidated report: agreement between findings sharing one premise must
appear as an echo, never as corroboration. A run that reports the claim AND labels
the agreement as corroboration fails twice.
