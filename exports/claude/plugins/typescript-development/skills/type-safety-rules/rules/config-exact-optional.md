---
title: Enable exactOptionalPropertyTypes
impact: MEDIUM
impactDescription: distinguishes a missing property from one explicitly set to undefined
tags: config, optional
---

## Enable exactOptionalPropertyTypes

**Impact: MEDIUM (distinguishes a missing property from one explicitly set to undefined)**

Without the flag, `{ retries?: number }` accepts `{ retries: undefined }`, which differs from an absent key under presence checks (`'retries' in obj` is true, `Object.keys` includes the key). APIs that distinguish "not provided" from "explicitly cleared" break silently.

**Incorrect (explicit undefined sneaks into an optional slot):**

```typescript
const opts: RetryOpts = { retries: undefined } // accepted without the flag
'retries' in opts // true, though the code reads it as absent
```

**Correct (with the flag, absence is expressed by omission):**

```typescript
const opts: RetryOpts = {} // retries genuinely absent
```

**Detection:** Read `tsconfig.json`: `exactOptionalPropertyTypes` absent or false is a finding, severity Medium.
