---
title: skipLibCheck may speed up third-party types, never hide first-party errors
impact: MEDIUM
impactDescription: your own declaration files must stay inside the checked perimeter
tags: config, declarations
---

## skipLibCheck may speed up third-party types, never hide first-party errors

**Impact: MEDIUM (your own declaration files must stay inside the checked perimeter)**

`skipLibCheck: true` skips ALL `.d.ts` files, including the ones this repository authors. That is an acceptable trade for `node_modules` compile time, but hand-written declarations and generated API types silently stop being checked. Keep first-party `.d.ts` content in `.ts` files where possible, or accept the flag knowingly with a comment.

**Incorrect (first-party declarations drift unchecked):**

```typescript
// src/types/api.d.ts, skipped by skipLibCheck, contradicts the runtime
declare interface ApiUser { id: number }
```

**Correct (first-party types live in checked .ts modules):**

```typescript
// src/types/api.ts, always checked
export interface ApiUser { id: string }
```

**Detection:** If `skipLibCheck` is true, `rg --files -g '*.d.ts' -g '!node_modules'`: each first-party `.d.ts` carrying hand-written declarations is a finding.
