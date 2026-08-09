<!-- upstream: ReScienceLab/opc-skills - skills/domain-hunter/references/spaceship-api.md -->
# Spaceship API Reference

Credentials are read from the environment:
- `SPACESHIP_API_KEY`
- `SPACESHIP_API_SECRET`

Base URL: `https://spaceship.dev/api`

## Authentication

All requests require these headers:
```bash
-H "X-Api-Key: $SPACESHIP_API_KEY"
-H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

Set both variables in the shell before any call.

POSIX shell:
```bash
export SPACESHIP_API_KEY="your_key"
export SPACESHIP_API_SECRET="your_secret"
```

PowerShell:
```powershell
$env:SPACESHIP_API_KEY = "your_key"
$env:SPACESHIP_API_SECRET = "your_secret"
```

**Pre-flight check.** Verify both are non-empty before the first call. An empty variable produces a 401 that reads like a permissions problem and sends you hunting the wrong bug.

```bash
if [ -z "$SPACESHIP_API_KEY" ] || [ -z "$SPACESHIP_API_SECRET" ]; then
  echo "ERROR: SPACESHIP_API_KEY and SPACESHIP_API_SECRET must both be set" >&2
  exit 1
fi
```

```powershell
if (-not $env:SPACESHIP_API_KEY -or -not $env:SPACESHIP_API_SECRET) {
  throw "SPACESHIP_API_KEY and SPACESHIP_API_SECRET must both be set"
}
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
curl -s -D - -X POST "https://spaceship.dev/api/v1/domains/{domain}" \
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
**Note:** Returns 202 Accepted. The operation id comes back in the `spaceship-async-operationid` **response header**, so the request must keep headers (`-D -` or `-i`). A plain `curl -s` throws them away and leaves you with no way to poll.

Capture the id for the poll step:
```bash
OPERATION_ID=$(curl -s -D - -o /dev/null -X POST "https://spaceship.dev/api/v1/domains/{domain}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{...}' \
  | tr -d '\r' | awk 'tolower($1) == "spaceship-async-operationid:" {print $2}')
```

**WARNING:** Never retry a paid POST (register, renew, transfer) whose outcome you do not know. Poll the async operation first. A blind retry can double-charge the account.

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
curl -s -D - -X POST "https://spaceship.dev/api/v1/domains/{domain}/transfer" \
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
**Note:** Async and paid, same as registration. Keep the headers (`-D -` or `-i`) and read `spaceship-async-operationid` from them, then poll. Never re-POST a transfer whose outcome is unknown.

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

Domain registration, transfer, etc. are async operations, returning `spaceship-async-operationid` header. Send those requests with `-D -` or `-i`, otherwise curl discards the header and the operation becomes unpollable.

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

# 3. Register domain, keeping the response headers so the operation id survives
OPERATION_ID=$(curl -s -D - -o /dev/null -X POST "https://spaceship.dev/api/v1/domains/example.com" ... -d '{...}' \
  | tr -d '\r' | awk 'tolower($1) == "spaceship-async-operationid:" {print $2}')

# 4. Poll for completion. Do NOT re-POST step 3 if this is unclear: that risks a double charge
curl -s -X GET "https://spaceship.dev/api/v1/async-operations/$OPERATION_ID" ...

# 5. Update nameservers to Cloudflare
curl -s -X PUT "https://spaceship.dev/api/v1/domains/example.com/nameservers" \
  ... -d '{"provider": "custom", "hosts": ["ns1.cloudflare.com", "ns2.cloudflare.com"]}'
```

### 2. Transfer Domain to Spaceship

```bash
# 1. Get auth code from current registrar
# 2. Unlock domain at current registrar
# 3. Initiate transfer, keeping the response headers so the operation id survives
OPERATION_ID=$(curl -s -D - -o /dev/null -X POST "https://spaceship.dev/api/v1/domains/example.com/transfer" ... \
  | tr -d '\r' | awk 'tolower($1) == "spaceship-async-operationid:" {print $2}')

# 4. Poll async operation for status. Never re-run step 3 to "check": poll instead
curl -s -X GET "https://spaceship.dev/api/v1/async-operations/$OPERATION_ID" ...
```
