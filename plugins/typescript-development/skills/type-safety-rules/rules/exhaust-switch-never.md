---
title: Discriminated unions get a never assertion in the default branch
impact: MEDIUM
impactDescription: adding a variant becomes a compile error at every switch instead of a silent fallthrough
tags: exhaust, unions, never
---

## Discriminated unions get a never assertion in the default branch

**Impact: MEDIUM (adding a variant becomes a compile error at every switch instead of a silent fallthrough)**

A switch over a discriminated union that lacks a `never` default compiles cleanly when a new variant is added and simply does nothing for it at runtime. The `never` assertion turns every unhandled variant into a compile error listing exactly the switches to update.

**Incorrect (the new 'refunded' status falls through silently):**

```typescript
switch (order.status) {
  case 'pending': return queue(order)
  case 'paid': return ship(order)
}
```

**Correct (the compiler enumerates unhandled variants):**

```typescript
switch (order.status) {
  case 'pending': return queue(order)
  case 'paid': return ship(order)
  default: {
    const unhandled: never = order.status
    throw new Error(`unhandled status: ${unhandled}`)
  }
}
```

**Detection:** `rg -n 'switch \(' --type ts` on files defining union types; flag switches over a discriminant with no `never`-typed default.
