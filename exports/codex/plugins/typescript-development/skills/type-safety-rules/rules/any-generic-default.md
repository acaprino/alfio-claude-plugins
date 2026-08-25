---
title: Never default a type parameter to any
impact: HIGH
impactDescription: the default silently applies wherever the caller omits the argument
tags: any, generics
---

## Never default a type parameter to any

**Impact: HIGH (the default silently applies wherever the caller omits the argument)**

`<T = any>` looks like flexibility but means every call site that omits the type argument gets unchecked results without opting in. Require the parameter, constrain it, or derive it from a runtime schema argument so the type and the validation cannot diverge.

**Incorrect (omitting the type argument silently yields any):**

```typescript
function loadCache<T = any>(key: string): T {
  return store.get(key)
}
const user = loadCache('user') // user: any
```

**Correct (the schema argument fixes T and validates at runtime):**

```typescript
function loadCache<T>(key: string, schema: z.ZodType<T>): T {
  return schema.parse(store.get(key))
}
const user = loadCache('user', UserSchema)
```

**Detection:** `rg -n '= any>' --type ts`. Also flag `<T = unknown>` on functions that then cast internally.
