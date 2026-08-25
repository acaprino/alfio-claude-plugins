---
title: Access environment variables through one validated config module
impact: HIGH
impactDescription: turns deploy-time misconfiguration into a startup error instead of a mid-request crash
tags: boundary, env, config
---

## Access environment variables through one validated config module

**Impact: HIGH (turns deploy-time misconfiguration into a startup error instead of a mid-request crash)**

`process.env.X` is `string | undefined` everywhere, which breeds scattered `!` assertions and silent fallbacks. One module that parses the whole environment at startup fails fast with a complete list of what is missing, and every consumer imports typed values.

**Incorrect (scattered access, assertion-silenced):**

```typescript
const db = connect(process.env.DATABASE_URL!)
const port = Number(process.env.PORT) // NaN when unset
```

**Correct (one schema, parsed once at startup):**

```typescript
// config.ts
export const env = z.object({
  DATABASE_URL: z.string().url(),
  PORT: z.coerce.number().default(3000),
}).parse(process.env)

// elsewhere
const db = connect(env.DATABASE_URL)
```

**Detection:** `rg -n 'process\.env\.' --type ts --glob '!**/config*'`; hits outside the config module are findings.
