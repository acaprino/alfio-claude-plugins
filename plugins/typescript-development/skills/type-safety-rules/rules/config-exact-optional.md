---
title: Enable exactOptionalPropertyTypes
impact: MEDIUM
impactDescription: distinguishes a missing property from one explicitly set to undefined
tags: config, optional
---

## Enable exactOptionalPropertyTypes

**Impact: MEDIUM (distinguishes a missing property from one explicitly set to undefined)**

Without the flag, `{ retries?: number }` accepts `{ retries: undefined }`, which spreads and serializes differently from an absent key (`'retries' in obj`, `Object.keys`, JSON output). APIs that distinguish "not provided" from "explicitly cleared" break silently.

**Incorrect (explicit undefined sneaks into an optional slot):**

```typescript
const opts: RetryOpts = { retries: undefined } // accepted without the flag
JSON.stringify(opts) // '{}' vs '{"retries":null}' surprises downstream
```

**Correct (with the flag, absence is expressed by omission):**

```typescript
const opts: RetryOpts = {} // retries genuinely absent
```

**Detection:** Read `tsconfig.json`: `exactOptionalPropertyTypes` absent or false is a finding, severity Medium.
