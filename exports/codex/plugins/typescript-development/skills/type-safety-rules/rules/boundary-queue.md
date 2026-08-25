---
title: Validate queue and event messages before processing
impact: CRITICAL
impactDescription: producers and consumers deploy independently; the schema is the only contract
tags: boundary, queue, events
---

## Validate queue and event messages before processing

**Impact: CRITICAL (producers and consumers deploy independently; the schema is the only contract)**

A queue consumer receives whatever an older or newer producer serialized. Typing the handler parameter is an assumption about a foreign deployment. Validate every message on receipt and route failures to a dead-letter path instead of letting a malformed message poison the handler mid-flight.

**Incorrect (the parameter type asserts a foreign producer's behavior):**

```typescript
channel.consume('orders', (msg: OrderCreated) => {
  reserveStock(msg.items)
})
```

**Correct (validate on receipt, dead-letter on failure):**

```typescript
channel.consume('orders', (raw: unknown) => {
  const result = OrderCreatedSchema.safeParse(raw)
  if (!result.success) return deadLetter(raw, result.error)
  reserveStock(result.data.items)
})
```

**Detection:** `rg -n 'consume\(|subscribe\(|on\(.message' --type ts`; flag handlers whose parameter is a domain type with no parse in the body.
