---
title: Constrain type parameters on public APIs
impact: MEDIUM
impactDescription: an unconstrained T pushes impossible types and bad inference onto every caller
tags: generics, constraints
---

## Constrain type parameters on public APIs

**Impact: MEDIUM (an unconstrained T pushes impossible types and bad inference onto every caller)**

An unconstrained `<T>` on an exported function accepts types the implementation cannot actually handle, and gives callers `unknown`-quality inference on the way out. Constrain the parameter to what the implementation truly requires, and let inference flow from a value argument whenever possible.

**Incorrect (T admits primitives the implementation will crash on):**

```typescript
export function merge<T>(base: T, patch: Partial<T>): T {
  return { ...base, ...patch } // spread of a number compiles here
}
```

**Correct (the constraint states the real requirement):**

```typescript
export function merge<T extends object>(base: T, patch: Partial<T>): T {
  return { ...base, ...patch }
}
```

**Detection:** `rg -n 'export function \w+<T[,>]' --type ts`; flag exported generics with bare `<T>` whose bodies spread, index, or iterate the value.
