---
title: Use satisfies Record for complete lookup tables
impact: MEDIUM
impactDescription: a missing key becomes a compile error instead of an undefined handler
tags: exhaust, satisfies, records
---

## Use satisfies Record for complete lookup tables

**Impact: MEDIUM (a missing key becomes a compile error instead of an undefined handler)**

A lookup table keyed by a union should be provably complete. An annotation (`: Record<Kind, Handler>`) achieves that but widens the value types; `satisfies` checks completeness while preserving the precise inferred types of each entry.

**Incorrect (unchecked table, the new kind resolves to undefined):**

```typescript
const handlers = {
  created: onCreated,
  deleted: onDeleted,
}
handlers[event.kind](event) // 'updated' added to the union, not here
```

**Correct (satisfies proves completeness, inference stays precise):**

```typescript
const handlers = {
  created: onCreated,
  updated: onUpdated,
  deleted: onDeleted,
} satisfies Record<EventKind, (e: AppEvent) => void>
```

**Detection:** Reading heuristic: object literals indexed by a union-typed key (`table[x.kind]`) without `satisfies` or a `Record` annotation.
