<!-- upstream: ReScienceLab/opc-skills - skills/domain-hunter/references/spaceship-api.md -->
# Spaceship API Reference

API keys configured in `~/.zshrc`:
- `SPACESHIP_API_KEY`
- `SPACESHIP_API_SECRET`

Base URL: `https://spaceship.dev/api`

## Authentication

All requests require these headers:
```bash
-H "X-Api-Key: $SPACESHIP_API_KEY"
-H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

Load environment variables:
```bash
export SPACESHIP_API_KEY="$(grep SPACESHIP_API_KEY ~/.zshrc | cut -d'"' -f2)"
export SPACESHIP_API_SECRET="$(grep SPACESHIP_API_SECRET ~/.zshrc | cut -d'"' -f2)"
```

## Domains API

### List Domains
```bash
curl -s -X GET "https://spaceship.dev/api/v1/domains?take=100&skip=0" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

### Check Domain Availability (Batch)
```bash
curl -s -X POST "https://spaceship.dev/api/v1/domains/available" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"domains": ["example.com", "test.ai"]}'
```
Response: `result` = "available" | "taken" | "reserved"

### Check Single Domain Availability
```bash
curl -s -X GET "https://spaceship.dev/api/v1/domains/{domain}/available" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

### Get Domain Info
```bash
curl -s -X GET "https://spaceship.dev/api/v1/domains/{domain}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

### Register Domain (Purchase)
```bash
curl -s -X POST "https://spaceship.dev/api/v1/domains/{domain}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "autoRenew": true,
    "years": 1,
    "privacyProtection": {
      "level": "high",
      "userConsent": true
    },
    "contacts": {
      "registrant": "CONTACT_ID",
      "admin": "CONTACT_ID",
      "tech": "CONTACT_ID",
      "billing": "CONTACT_ID"
    }
  }'
```
**Note:** Returns 202 Accepted, poll async-operations for result

### Update Nameservers (Configure to Cloudflare)
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/domains/{domain}/nameservers" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "custom",
    "hosts": ["ns1.cloudflare.com", "ns2.cloudflare.com"]
  }'
```

### Update Auto-Renewal
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/domains/{domain}/autorenew" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"isEnabled": true}'
```

### Renew Domain
```bash
curl -s -X POST "https://spaceship.dev/api/v1/domains/{domain}/renew" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"years": 1}'
```

### Update Privacy Protection
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/domains/{domain}/privacy" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "level": "high",
    "userConsent": true
  }'
```
Levels: "high" | "medium" | "none"

### Update Domain Contacts
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/domains/{domain}/contacts" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "registrant": "CONTACT_ID",
    "admin": "CONTACT_ID",
    "tech": "CONTACT_ID",
    "billing": "CONTACT_ID"
  }'
```

### Get Auth Code (for Transfer Out)
```bash
curl -s -X GET "https://spaceship.dev/api/v1/domains/{domain}/auth-code" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

### Update Transfer Lock
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/domains/{domain}/transfer-lock" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"isEnabled": true}'
```

### Transfer In Domain
```bash
curl -s -X POST "https://spaceship.dev/api/v1/domains/{domain}/transfer" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "authCode": "AUTH_CODE_FROM_CURRENT_REGISTRAR",
    "autoRenew": true,
    "privacyProtection": {
      "level": "high",
      "userConsent": true
    },
    "contacts": {
      "registrant": "CONTACT_ID",
      "admin": "CONTACT_ID",
      "tech": "CONTACT_ID",
      "billing": "CONTACT_ID"
    }
  }'
```

## Contacts API

### Save Contact
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/contacts/{contactId}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "organization": "Company Inc",
    "email": "john@example.com",
    "phone": "+1.5551234567",
    "address1": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "postalCode": "94102",
    "country": "US"
  }'
```

### Get Contact
```bash
curl -s -X GET "https://spaceship.dev/api/v1/contacts/{contactId}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

## DNS Records API

### Get DNS Records
```bash
curl -s -X GET "https://spaceship.dev/api/v1/dns-records/{domain}?take=100&skip=0" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

### Save DNS Records
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/dns-records/{domain}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600},
      {"type": "CNAME", "name": "www", "target": "example.com", "ttl": 3600},
      {"type": "TXT", "name": "@", "content": "v=spf1 ...", "ttl": 3600},
      {"type": "MX", "name": "@", "mailHost": "mail.example.com", "priority": 10, "ttl": 3600}
    ]
  }'
```

### Delete DNS Records
```bash
curl -s -X DELETE "https://spaceship.dev/api/v1/dns-records/{domain}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "A", "name": "@", "address": "1.2.3.4"}
    ]
  }'
```

## Async Operations

Domain registration, transfer, etc. are async operations, returning `spaceship-async-operationid` header.

### Get Operation Status
```bash
curl -s -X GET "https://spaceship.dev/api/v1/async-operations/{operationId}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```
Status: "pending" | "success" | "failed"

## API Permissions

| Scope | Description |
|-------|-------------|
| domains:read | Read domain information |
| domains:write | Manage domain settings |
| domains:transfer | Domain transfer in/out |
| domains:billing | Domain purchase and renewal |
| contacts:read | Read contacts |
| contacts:write | Save contacts |
| dnsrecords:read | Read DNS records |
| dnsrecords:write | Write DNS records |
| asyncoperations:read | Query async operations |

## Rate Limits

| Operation | Limit |
|-----------|-------|
| List domains | 300 req / 300s per user |
| Check availability (batch) | 30 req / 30s per user |
| Check availability (single) | 5 req / 300s per domain |
| Get domain info | 5 req / 300s per domain |
| Register domain | 30 req / 30s per user |
| Update nameservers | 5 req / 300s per domain |
| Async operations | 60 req / 300s per user |

## Common Workflows

### 1. Purchase Domain + Configure Cloudflare NS

```bash
# 1. Check availability
curl -s -X GET "https://spaceship.dev/api/v1/domains/example.com/available" ...

# 2. Get existing contact ID from another domain
curl -s -X GET "https://spaceship.dev/api/v1/domains?take=1&skip=0" ... | jq '.items[0].contacts.registrant'

# 3. Register domain
curl -s -X POST "https://spaceship.dev/api/v1/domains/example.com" ... -d '{...}'
# Note the operationId from response header

# 4. Poll for completion
curl -s -X GET "https://spaceship.dev/api/v1/async-operations/{operationId}" ...

# 5. Update nameservers to Cloudflare
curl -s -X PUT "https://spaceship.dev/api/v1/domains/example.com/nameservers" \
  ... -d '{"provider": "custom", "hosts": ["ns1.cloudflare.com", "ns2.cloudflare.com"]}'
```

### 2. Transfer Domain to Spaceship

```bash
# 1. Get auth code from current registrar
# 2. Unlock domain at current registrar
# 3. Initiate transfer
curl -s -X POST "https://spaceship.dev/api/v1/domains/example.com/transfer" ...

# 4. Poll async operation for status
curl -s -X GET "https://spaceship.dev/api/v1/async-operations/{operationId}" ...
```
