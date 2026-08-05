---
title: Parse HTTP payloads with a schema at the edge
impact: CRITICAL
impactDescription: the API contract is enforced where the data enters, not assumed
tags: boundary, http, zod
---

## Parse HTTP payloads with a schema at the edge

**Impact: CRITICAL (the API contract is enforced where the data enters, not assumed)**

Request bodies and response payloads are `unknown` at runtime no matter what the client types say. One schema parse at the boundary turns drift into a precise error at the edge; without it, drift becomes an undefined-property crash three modules deep.

**Incorrect (the handler trusts the wire format):**

```typescript
app.post('/orders', (req) => {
  const order = req.body as Order
  charge(order.total) // total arrives as a string from this client
})
```

**Correct (the schema is the contract, parsed once at ingress):**

```typescript
app.post('/orders', (req) => {
  const order = OrderSchema.parse(req.body)
  charge(order.total)
})
```

**Detection:** Locate route handlers and API clients (`rg -n 'req\.body|\.json\(\)' --type ts`); flag any that reach typed code without a schema parse or guard.
