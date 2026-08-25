---
title: Type the results of JSON.parse, response.json(), and catch immediately
impact: CRITICAL
impactDescription: untyped ingress makes every downstream type a lie
tags: any, boundary, json
---

## Type the results of JSON.parse, response.json(), and catch immediately

**Impact: CRITICAL (untyped ingress makes every downstream type a lie)**

`JSON.parse` and `response.json()` return `any`. Assigning that result to a typed variable is an unchecked cast in disguise: the annotation asserts a shape nobody verified. Route the value through `unknown` and a schema or guard before it reaches typed code.

**Incorrect (the annotation asserts, nothing verifies):**

```typescript
const config: AppConfig = JSON.parse(raw)
startServer(config.port) // port may be undefined or a string
```

**Correct (parse to unknown, validate, then trust the type):**

```typescript
const parsed: unknown = JSON.parse(raw)
const config = AppConfigSchema.parse(parsed) // throws with a precise error on drift
startServer(config.port)
```

**Detection:** `rg -n 'JSON\.parse\(|\.json\(\)' --type ts`. Flag any hit whose result lands in a typed binding without a schema parse or guard between.
