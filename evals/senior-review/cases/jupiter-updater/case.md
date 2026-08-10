# Case: jupiter-updater

The strongest case in the harness: ground truth from a production post-mortem (2026-08-10), including one defect a four-reviewer team review initially archived as harmless on correct-but-wrong-question arithmetic.

- **Repo:** `D:\Projects\jupiter`
- **Review rev:** `936ba644` (feat(desktop): silent auto-update, no manual installer)
- **Fix rev (do not show the reviewer):** `361169cc`
- **Review scope:** `jupiter-desktop/src-react/src/hooks/useUpdater.ts`, `jupiter-desktop/src-react/src/store/slices/updaterSlice.ts`, `jupiter-desktop/src-react/src/components/molecules/UpdateNotification/`, `jupiter-desktop/src-react/src/components/molecules/SettingsMenu/SettingsMenu.tsx` (or the diff `936ba644~1..936ba644`)

## Ground truth (7 bugs)

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | A failed install stays silent (surfaced=false on the scheduler path), then 5 minutes later the app re-announces the same version as good news; no memory of the failed version, so re-download + re-notify repeats daily | temporal-resilience |
| 2 | Download retry without backoff or cap: a failed `download()` resets phase to `idle` and the next 5-minute pass restarts the full transfer; nothing is resumable, worst case ~2 GB/day | temporal-resilience |
| 3 | No timeout on `check()` or `download()`: a black-holed connection leaves the in-flight guard set forever, the chained timer never re-arms, the updater dies silently for the process lifetime | temporal-resilience |
| 4 | Supersede path installs an unannounced version: user accepts "Tonight" for 1.2.15, 1.2.16 arrives and silently replaces it | logic-integrity / architecture |
| 5 | Dead click on "Check for Updates" while an automatic pass holds the flow with nothing on screen | architecture / ui |
| 6 | `announceAvailable` leaves the banner unreachable when the window is in the tray and the toast is not delivered | ui / architecture |
| 7 | Comments and docs contradict the code: `runAutoCheck` claims "never puts anything on screen", docs describe an hourly check and a "Riavvia ora" button that no longer exist | documentation / hygiene |

## Scoring notes

- Bug 2 is the calibration trap: a reviewer that derives "288 downloads/day" from the code overestimates 100x (measured: 2/day, the phase machine self-limits); a reviewer that measures "2/day, bounded" and closes the finding misses that bug 1 (the silence) is the real defect. Full credit requires either the measured number or the user-visible-consequence framing; arithmetic alone in either direction is `partial`.
- Bug 3 is the lethal one (silent permanent death). A miss here weighs the hardest qualitatively.
