<!-- upstream: ReScienceLab/opc-skills - skills/domain-hunter/examples/auto-video-editing-domain.md -->
# Domain Hunter Example: Finding a Domain for Auto Video Editing Project

This is a complete conversation example showing how the domain-hunter skill helps users find and purchase domain names at the best price.

---

## Conversation

### User

> I am working on an auto video editing project. I need to buy a new domain. Please find one for me.

### Assistant

I'll help you find a domain for your auto video editing project. Let me generate some creative domain name suggestions and check their availability.

**Checking domain availability via RDAP:**

```bash
for domain in "autoedit.io" "clipcraft.io" "videoedit.ai" "cutflow.io" "autocuts.io" "editsnap.io" "vidflow.ai" "clipflow.io" "autoclipper.io" "smartcut.io"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://rdap.org/domain/$domain")
  case "$code" in
    404) echo "Checking $domain... -> AVAILABLE" ;;
    200) echo "Checking $domain... -> TAKEN" ;;
    *)   echo "Checking $domain... -> UNKNOWN (lookup failed, retry)" ;;
  esac
done
```

Any status other than 404 or 200 is UNKNOWN. A failed lookup is never reported as TAKEN or AVAILABLE.

**Results - First Batch:**
```
Checking autoedit.io...   -> TAKEN
Checking clipcraft.io...  -> TAKEN
Checking videoedit.ai...  -> TAKEN
Checking cutflow.io...    -> AVAILABLE
Checking autocuts.io...   -> AVAILABLE
Checking editsnap.io...   -> AVAILABLE
Checking vidflow.ai...    -> TAKEN
Checking clipflow.io...   -> TAKEN
Checking autoclipper.io...-> AVAILABLE
Checking smartcut.io...   -> TAKEN
```

**Results - Second Batch:**
```
Checking autovidz.io...   -> AVAILABLE
Checking clipauto.io...   -> AVAILABLE
Checking videotrim.ai...  -> AVAILABLE
Checking cliphero.io...   -> AVAILABLE
Checking quickclip.io...  -> TAKEN
Checking autosnip.io...   -> AVAILABLE
Checking vidauto.io...    -> TAKEN
Checking clipmagic.io...  -> TAKEN
Checking autorender.io... -> TAKEN
Checking editbot.io...    -> AVAILABLE
```

Here are the **available domain suggestions** for your auto video editing project:

## Available Domains

| Domain | Notes |
|--------|-------|
| **cutflow.io** | Short, memorable - "cut" + "flow" for editing workflow |
| **autocuts.io** | Direct - auto video cuts |
| **editsnap.io** | Quick, snappy editing |
| **autoclipper.io** | Descriptive - auto video clipping |
| **autovidz.io** | Casual/trendy - auto videos |
| **clipauto.io** | Simple - clip automation |
| **videotrim.ai** | .ai TLD - video trimming |
| **cliphero.io** | Brandable - hero for clips |
| **autosnip.io** | Short clips/snips |
| **editbot.io** | Bot/AI angle for editing |

**My top picks:**
1. **cutflow.io** - Short (7 chars), professional, memorable
2. **autocuts.io** - Clear purpose, good branding
3. **videotrim.ai** - .ai TLD fits AI/auto theme well

**Which domain(s) would you like me to check prices for?** Once you pick your favorites, I'll compare prices across registrars and look for promo codes.

---

### User

> cutflow.io looks good, I need to know where can I get the cheapest price to buy it? Also, is there any promo code?

### Assistant

*Searching Twitter/X and Reddit for promo codes...*

**Step 1: Web Search for Price Comparison**

Fetched data from https://tld-list.com/tld/io showing current .io domain prices:

| Registrar | Registration | Renewal | Notes |
|-----------|--------------|---------|-------|
| Spaceship | $14.98 | $46.58 | Promo code **IO85** (85% off, limit 1) |
| Sav | $14.99 | $38.95 | No promo needed |
| Dynadot | $28.89 | $47.70 | - |
| Regery | $28.99 | $47.99 | - |
| Gandi.net | $31.99 | $69.99 | - |

**Step 2: Twitter/X Search for Promo Codes**

```
WebSearch: "site:x.com from:spaceship promo code"
```

**Results from @spaceship:**
- @spaceship: "Feel free to use the SPSR86 promo code for the disc"
- @spaceship: "Yes, you are right. You can use this promo c"

```
WebSearch: "site:x.com from:Dynadot promo code"
```

**Results from @Dynadot:**
- @Dynadot: "Transfer your .COM domains to Dynadot for just $10.49 with..."
- @Dynadot: "We did have a .com promo code in April a..."

```
WebSearch: "site:x.com from:Namecheap promo code"
```

**Results from @Namecheap:**
- @Namecheap: "If you are a new customer, you can get..."
- @Namecheap: "For new users, we've got our NEWCOM598 code at..."

**Step 3: Reddit Search for Promo Codes**

```
WebSearch: "site:reddit.com r/Domains spaceship domain promo code"
```

**Results from r/Domains:**
- Domain pricing question: Cloudflare vs Spaceship renewals
- Best registrar for a throwaway .com domain
- Spaceship Buyer Hub

---

## Final Recommendation

**Domain:** cutflow.io

### Price Comparison

| Registrar | Year 1 | Renewal | Notes |
|-----------|--------|---------|-------|
| **Spaceship** | **$14.98** | $46.58 | Use promo code **IO85** (85% off, limit 1) |
| Sav | $14.99 | $38.95 | No promo needed |
| Dynadot | $28.89 | $47.70 | No .io promo found |
| Regery | $28.99 | $47.99 | - |
| Namecheap | $34.98 | $57.98 | 40% off first year |
| Hostinger | $31.99 | $67.99 | - |

### Best Deal

**Winner: Spaceship at $14.98/year** (with promo code **IO85**)

- **Promo Code:** `IO85` (85% off .io registration, limit 1 per customer)
- **Free Features:** DNS, Email Forwarding, WHOIS Privacy
- **Renewal:** $46.58/year (industry standard for .io)

**Purchase Link:** https://www.spaceship.com/

### Alternative if renewal matters

**Sav.com at $14.99/year** with the **cheapest renewal at $38.95/year** - best 3-year value if you plan to keep the domain long-term.

---

**Note:** .io domains have high wholesale costs (~$45), so the first-year promos are significant discounts. Renewal prices are similar across registrars.

---

## Key Takeaways

1. **RDAP checks** are used to verify domain availability before presenting options (404 available, 200 taken, anything else unknown)
2. **Price comparison** from tld-list.com provides up-to-date registrar pricing
3. **WebSearch with site:x.com** searches registrar accounts for promo codes
4. **WebSearch with site:reddit.com** searches r/Domains community for user-shared deals
5. **Final recommendation** includes best price, promo code, and purchase link
