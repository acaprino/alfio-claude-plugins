---
title: A type predicate must verify the whole shape it claims
impact: HIGH
impactDescription: an unsound guard converts unknown to a trusted type on false evidence
tags: generics, type-guards, predicates
---

## A type predicate must verify the whole shape it claims

**Impact: HIGH (an unsound guard converts unknown to a trusted type on false evidence)**

`x is T` is a promise the compiler takes on faith: after a true return, `x` IS `T` everywhere downstream. A guard that checks one field and claims the whole shape is a cast wearing a disguise. Check every field the consuming code relies on, or delegate to a schema's `safeParse` so the check and the type cannot drift.

**Incorrect (one field checked, whole shape claimed):**

```typescript
function isUser(x: unknown): x is User {
  return typeof x === 'object' && x !== null && 'id' in x
}
// passes for { id: 1 }; user.email.toLowerCase() then throws
```

**Correct (the schema is the guard; check and type share one source):**

```typescript
function isUser(x: unknown): x is User {
  return UserSchema.safeParse(x).success
}
```

**Detection:** `rg -n '\): \w+ is ' --type ts`; read each predicate body and compare the checks against the claimed type's required fields.
