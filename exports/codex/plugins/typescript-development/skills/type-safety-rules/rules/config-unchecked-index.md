---
title: Enable noUncheckedIndexedAccess
impact: HIGH
impactDescription: makes index access tell the truth about absence
tags: config, index-access
---

## Enable noUncheckedIndexedAccess

**Impact: HIGH (makes index access tell the truth about absence)**

Without this flag, `arr[i]` and `record[key]` type as `T` even when the element does not exist, which is exactly how out-of-bounds and missing-key bugs pass review. With it, index access types as `T | undefined` and the compiler forces the check the runtime always required.

**Incorrect (the type claims presence the runtime does not guarantee):**

```typescript
const first = rows[0] // typed Row, is undefined for an empty result
render(first.id)
```

**Correct (with the flag on, absence must be handled):**

```typescript
const first = rows[0] // typed Row | undefined
if (!first) return renderEmpty()
render(first.id)
```

**Detection:** Read `tsconfig.json`: `noUncheckedIndexedAccess` absent or false is a finding. It is not part of `strict`, so check it explicitly.
