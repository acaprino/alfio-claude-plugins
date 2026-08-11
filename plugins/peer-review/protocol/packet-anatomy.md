# Packet Anatomy

The packet is the single unit of egress (R5) and the challenger's whole world. Build
it against these rules; the order is fixed by R3.

1. **Mandate.** What to judge and what to leave alone. One paragraph.
2. **Artifact.** Verbatim, unabridged. Record `bytes: <N>` and `sha256: <hex>`
   immediately above the embedded document (R15).
3. **Ground truth (given).** Source facts with locators, each line prefixed `GIVEN`.
   Enter facts by mechanical extraction from the material the artifact names:
   judgment controls how much of each source, never which sources.
4. **Constraints.** Conventions and non-negotiables. All `GIVEN`.
5. **Considered and rejected.** One entry per dismissed alternative:
   `decision (GIVEN):` what was dismissed; `rationale (TO JUDGE):` why. The decision
   is settled; the reasoning is attackable. This split is what lets the challenger
   reopen a bad reason without relitigating every settled choice.
6. **Known weaknesses of this artifact.** Written by the builder against its own
   side. Producing an empty section is itself a signal and must be stated as such.
7. **Open questions.** Where the artifact is genuinely unsure. This is the
   invitation to be useful.
8. **Out of scope.**
9. **Response contract.** The exact required output shape for round 1, copied from
   `round-prompts.md`.
