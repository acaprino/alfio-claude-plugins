---
title: Use as const for literal narrowing instead of widening annotations
impact: MEDIUM
impactDescription: preserves literal types that unions and lookups depend on
tags: cast, const, literals
---

## Use as const for literal narrowing instead of widening annotations

**Impact: MEDIUM (preserves literal types that unions and lookups depend on)**

Annotating a literal with a wide type (`string[]`, `Record<string, string>`) throws away the literal information the compiler inferred. `as const` keeps it, giving you free union types and readonly guarantees that downstream exhaustiveness checks rely on.

**Incorrect (the annotation widens and loses the literals):**

```typescript
const ROLES: string[] = ['admin', 'editor', 'viewer']
type Role = string // any string passes
```

**Correct (as const keeps the literals and derives the union):**

```typescript
const ROLES = ['admin', 'editor', 'viewer'] as const
type Role = (typeof ROLES)[number] // 'admin' | 'editor' | 'viewer'
```

**Detection:** Reading heuristic: literal arrays and objects annotated with wide types, then compared with `===` against specific members elsewhere.
