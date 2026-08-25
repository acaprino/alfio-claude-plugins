---
title: as unknown as X is a type-system bypass
impact: CRITICAL
impactDescription: defeats assignability checking entirely between any two types
tags: cast, unknown, bypass
---

## as unknown as X is a type-system bypass

**Impact: CRITICAL (defeats assignability checking entirely between any two types)**

The compiler rejects a direct `as` between unrelated types precisely because it is never safe. `as unknown as X` launders the value through `unknown` to silence that rejection. Whatever made the direct cast illegal is still true at runtime. Write a converter function or a guard that constructs the target shape explicitly.

**Incorrect (two unrelated types force-bridged):**

```typescript
const req = event as unknown as HttpRequest
handle(req.headers) // headers does not exist on event
```

**Correct (an explicit converter states and checks the mapping):**

```typescript
function toHttpRequest(event: LambdaEvent): HttpRequest {
  return { headers: event.rawHeaders ?? {}, body: event.body ?? '' }
}
handle(toHttpRequest(event).headers)
```

**Detection:** `rg -n 'as unknown as' --type ts`. Every hit is a finding; the only acceptable ones live in test doubles, and even those deserve a comment.
