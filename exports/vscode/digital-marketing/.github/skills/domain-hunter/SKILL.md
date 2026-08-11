---
name: domain-hunter
description: >
  Finds what is available and what it truly costs, promo codes included.
  Use when the user wants to buy a domain, check domain prices, compare registrars, find domain
  deals, or search for .ai/.com names.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: digital-marketing
---

<!-- upstream: ReScienceLab/opc-skills - skills/domain-hunter/SKILL.md -->
<!-- Local drift: Step 3 (Find Promo Codes) uses WebSearch queries instead of upstream Python scripts -->

# Domain Hunter Skill

Help users find and purchase domain names at the best price.

## Workflow

### Step 1: Generate Domain Ideas & Check Availability

Based on the user's project description, generate 5-10 creative domain name suggestions.

**Guidelines:**
- Keep names short (under 15 characters)
- Make them memorable and brandable
- Consider: `{action}{noun}`, `{noun}{suffix}`, `{prefix}{keyword}`
- Common suffixes: app, io, hq, ly, ify, now, hub

**CRITICAL: Always check availability before presenting domains to user!**

Use one of these methods to verify availability:

**Method 1: RDAP check (most reliable)**
```bash
# Prints the HTTP status: 404 = AVAILABLE, 200 = TAKEN, anything else = UNKNOWN
curl -s -o /dev/null -w "%{http_code}" "https://rdap.org/domain/{domain}.{tld}"
```

A failed command (no network, timeout, rate limit, empty output, any other status) means **UNKNOWN**. Never read a failure as TAKEN and never read it as AVAILABLE. Report UNKNOWN domains as unverified and retry them.

**Method 1b: whois confirmation (only where the binary exists)**
```bash
whois {domain}.{tld}
```
Use this to confirm an RDAP result, not to replace it. A registration record means TAKEN. "No match" or "not found" in a successful response means AVAILABLE. A missing binary, a non-zero exit, or empty output means UNKNOWN, not TAKEN. Parked-domain banners can contain the word "available", so read the record itself rather than grepping for substrings.

**Method 2: Registrar search page**
Open the registrar's domain search in browser to verify:
```bash
open "https://www.spaceship.com/domains/?search={domain}.{tld}"
```

**Method 3: Bulk check via Namecheap/Dynadot**
- https://www.namecheap.com/domains/registration/results/?domain={domain}
- https://www.dynadot.com/domain/search?domain={domain}

**IMPORTANT:**
- Only present domains that are confirmed AVAILABLE
- Mark any uncertain domains with "(unverified)". An UNKNOWN result is unverified, not taken, so never discard a candidate on it
- Present suggestions to user and **wait for confirmation** before proceeding
- Ask user to pick their preferred options or provide feedback
- Only move to Step 2 after user approves domain name(s)

### Step 2: Compare Prices

Use **WebSearch** to find current prices:

```
WebSearch: "cheapest .{tld} domain registrar 2026 site:tld-list.com"
WebSearch: ".{tld} domain price comparison tldes.com"
```

**Key price comparison sites:**
- tld-list.com/tld/{tld}
- tldes.com/{tld}
- domaintyper.com/{tld}-domain

### Step 3: Find Promo Codes

Use **WebSearch** to search registrar social accounts and communities for promo codes:

**Twitter/X search** - search registrar accounts for recent promos:
```
WebSearch: "site:x.com from:{registrar} promo code"
WebSearch: "site:x.com {registrar} promo code coupon"
```

**Reddit search** - search domain communities for deals:
```
WebSearch: "site:reddit.com r/Domains {registrar} promo code"
WebSearch: "site:reddit.com r/Domains {registrar} coupon discount"
```

**Major registrar Twitter handles:**
- @spaceship, @Dynadot, @Namecheap, @Porkbun, @namesilo, @Cloudflare

### Step 4: Recommend

Present final recommendation in this format:

```
## Recommendation

**Domain:** example.ai
**Best Registrar:** Spaceship
**Price:** $68.98/year (2-year minimum = $137.96)
**Promo Code:** None available for .ai
**Purchase Link:** https://www.spaceship.com/

### Price Comparison
| Registrar | Year 1 | Renewal | 2-Year Total |
|-----------|--------|---------|--------------|
| Spaceship | $68.98 | $68.98  | $137.96      |
| Cloudflare| $70.00 | $70.00  | $140.00      |
| Porkbun   | $71.40 | $72.40  | $143.80      |
```

## Important Notes

1. **Premium TLDs** (.ai, .io) rarely have promo codes - wholesale costs are too high
2. **.ai domains** require 2-year minimum registration
3. **Cloudflare** offers at-cost pricing with no markup
4. **Renewal prices** often differ from registration - always check both
5. **WHOIS privacy** is free at most registrars (Cloudflare, Namecheap, Porkbun)

## Domain Checker Script

For bulk availability checks, use the domain checker script:

```bash
python "$SKILLS/domain-hunter/scripts/domain_checker.py" name1 name2 --tlds .com,.io
```

`$SKILLS` is the first of `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` that exists. The script checks availability via RDAP. No API key and no third-party packages are needed. It defaults to `.com`, `.app`, `.io`, `.co`; pass `--tlds` to override. Each line reports `AVAILABLE`, `TAKEN`, or `UNKNOWN`, and UNKNOWN means the lookup failed rather than that the domain is free.

If the script cannot run, fall back to the RDAP curl check (Step 1, Method 1) or web searches (this needs a web-search tool, see the bundle README).

## References

- [references/registrars.md](./references/registrars.md) - Detailed registrar comparison
- [references/spaceship-api.md](./references/spaceship-api.md) - Spaceship API for automated domain operations
