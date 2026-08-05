---
title: Use @ts-expect-error with a reason, never @ts-ignore
impact: HIGH
impactDescription: expect-error self-heals; ignore rots silently
tags: assert, suppression
---

## Use @ts-expect-error with a reason, never @ts-ignore

**Impact: HIGH (expect-error self-heals; ignore rots silently)**

`@ts-ignore` suppresses whatever error happens to be on the next line, forever, including new errors introduced later. `@ts-expect-error` fails the build when the suppressed error disappears, so stale suppressions clean themselves up. The reason text tells the next reader what was being suppressed and why.

**Incorrect (suppresses today's error and every future one):**

```typescript
// @ts-ignore
legacyInit(options)
```

**Correct (scoped, reasoned, self-expiring):**

```typescript
// @ts-expect-error legacyInit's .d.ts lags v4; remove after upstream #123
legacyInit(options)
```

**Detection:** `rg -n '@ts-ignore|@ts-nocheck' --type ts`: every hit is a finding. `rg -n '@ts-expect-error$' --type ts`: expect-error with no reason text is a lesser finding.
