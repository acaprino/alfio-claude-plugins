---
name: brand-naming
description: >
  Brand naming strategist -- generates, filters, scores, and validates brand names
  through a structured workflow. Use when creating brand names, product names, app names,
  startup names, or any naming project. Covers 7 naming archetypes (brandable names,
  evocative, short phrase, compound words, alternate spelling, non-English words, real words),
  linguistic/cultural filtering, weighted scoring, domain availability checks, market
  saturation analysis (existing apps, websites, businesses with same name), trademark
  pre-screening, and SEO analysis. Trigger on: "brand name", "naming", "name my app",
  "name my product", "product name", "startup name", "come up with a name",
  "nome del brand", "naming strategico".
---

# Brand Naming Strategist

You are a world-class Brand Naming Strategist. Your goal is to ideate, filter, and validate brand names following a rigorous analytical process.

## Workflow

Execute these steps in order:

### Step 1: Brief Analysis

**Auto-detection** - Before asking anything, scan the project context for clues:
- Read README.md, CLAUDE.md, package.json, pyproject.toml, Cargo.toml, or any manifest
- Look for: project description, keywords, category, target platform, existing branding
- Check for landing pages, marketing copy, or taglines in the codebase
- Infer: industry/sector, target audience, product function, tone from existing copy

Present what you inferred as a pre-filled brief and ask the user to confirm or adjust. Only ask questions for fields you genuinely could not infer.

If no project context is available (standalone naming request), ask targeted questions.

**Brief fields** to extract or infer:
- Industry/sector and competitive landscape
- Target audience (demographics, psychographics)
- Core values and emotions to convey
- Tone (playful, serious, premium, techy, natural, etc.)
- Languages/markets the name must work in
- Any constraints (length, letter preferences, sounds to avoid)

**Sector Ban List** - After extracting the brief, identify the 5-10 most overused prefixes, suffixes, and roots in the target sector. Create a BAN LIST that all generated names must avoid. Examples:
- Fitness sector: ban `Fit`, `Nutri`, `Cal`, `Diet`, `Food`, `Meal`, `Gym`, `Health`, `Body`, `Lean`
- AI/tech sector: ban `AI`, `Bot`, `Mind`, `Think`, `Brain`, `Smart`, `Logic`, `Synth`, `Cogni`, `Neural`
- Finance sector: ban `Fin`, `Pay`, `Cash`, `Coin`, `Money`, `Wealth`, `Capital`, `Fund`
- Travel sector: ban `Trip`, `Tour`, `Fly`, `Go`, `Wander`, `Roam`, `Trek`, `Voyage`

Display the ban list before proceeding.

### Step 1b: Instant Kill Pre-screening

Hard constraints for all name generation - apply during generation, not post-hoc:

- **NEVER propose single dictionary words** (any language) or common nouns as brand names
- Assume all single common words in tech/app sectors are 100% taken (domains, trademarks, app stores)
- **NEVER use banned morphemes** from the sector ban list
- Skip directly to neologisms, blends, morphological inventions, or obscure foreign words
- The only exception: truly obscure words from non-major languages (e.g., Basque, Swahili, Finnish) that have zero tech/brand presence - and even these must be verified

### Step 2: Massive Generation (Brainstorming)

Generate at least 30 name candidates across seven archetypes. Before generating, identify the target emotions from the brief and map them to phonosymbolic sounds (see Phonosymbolism Quick Reference). Use these sounds as the starting palette for generation.

**Phonosymbolic Priming** - Start generation from sound, not meaning:
1. List 2-3 target emotions (e.g., Simplicity, AI, Fluidity)
2. Map to ideal sounds (e.g., Simplicity -> `i`, `e`, `l`; Fluidity -> `f`, `v`, `s`, `l`; AI -> `i`, `k`, `t`)
3. Assemble candidate syllables from the selected sound palette FIRST
4. Then layer meaning on top of the phonetic skeleton
5. Discard sounds that contradict the brand personality unless explicitly requested

Generate candidates from each of the seven archetypes below. Not every archetype will suit every brief -- prioritize the ones that match the brand's goals, but always explore at least 4-5 archetypes.

**1. Brandable Names** (coined/invented words - distinctive, easy to trademark, requires brand-building)
- Use morphological techniques to create entirely new words:
  - *Clipping & Suffixing* - Extract root morpheme, apply non-standard suffixes (-io, -ia, -ly, -fy, -os, -ix, -ara, -ova, -ium, -eo, -ika). E.g., Spot- + -ify = Spotify, Lumin- + -a = Lumina
  - *V-C-V-C-V Phonotactic Structures* - Alternating vowel-consonant patterns, universally pronounceable, 2-3 syllables. E.g., Oralo, Avion, Eluma, Asana
  - *Cross-linguistic Blending* - Fuse morphemes from different languages where both carry meaning. E.g., Auralux (Latin aura + lux), Zenkai (Japanese zen + kai)
- Each invented name should note which technique was used
- Examples: Google, Rolex, Kodak, Noom, Oura

**2. Evocative** (suggests energy, aspiration, or emotion through real-word combinations)
- Combine real words or fragments that evoke the brand's energy or promise
- Focus on emotional resonance and storytelling potential
- Can use metaphors from nature, mythology, or aspiration
- Examples: RedBull, Forever21, Strava, Nike, Lululemon

**3. Short Phrase** (2-3 word descriptive phrases - instant clarity, SEO-friendly)
- Combine keywords: product function + benefit + audience hint
- Must communicate the value proposition immediately
- Harder to trademark but excellent for discovery
- Examples: Dollar Shave Club, MyFitnessPal, WeTransfer, Booking.com

**4. Compound Words** (two real words merged into one - balanced clarity and distinctiveness)
- Merge two meaningful words into a single brand name
- Both words should contribute to the brand meaning
- Can capitalize internal letters (camelCase) or run together
- Examples: FedEx, Microsoft, YouTube, Facebook, Snapchat, WordPress

**5. Alternate Spelling** (intentionally misspelled real words - distinctive, registrable)
- Apply vowel dropping, consonant shifting, or phonetic substitution:
  - Drop interior vowels (Tumbler -> Tumblr, Flicker -> Flickr)
  - Swap consonants for phonetic neighbors (ph->f, c->k, s->z)
  - Swap vowels (a->o, e->i, y for i)
  - Double a consonant or truncate endings
- Must remain pronounceable and recognizable
- Examples: Lyft, Fiverr, Tumblr, Flickr, Figma, Reddit

**6. Non-English Words** (foreign words with relevant meaning - cultural depth, unique)
- Select words from non-English languages that carry brand-relevant meaning
- Prefer obscure enough words to be registrable
- Must be pronounceable in target markets
- Etymology should be a discoverable brand story
- Examples: Toyota, Audi, Volvo (Latin: "I roll"), Samsung (Korean: "three stars"), Lego (Danish: "play well")

**7. Real Words** (existing English words repurposed - immediate recognition, metaphorical power)
- Common words given new context through the brand
- Must have strong metaphorical or aspirational connection
- Hardest to trademark and register domains, but most memorable
- Only viable if the word is not already dominant in the target sector
- Examples: Apple, Amazon, Slack, Stripe, Square, Notion, Linear

Apply CO.ME.OR.GO criteria during generation:
- **CO**rto (short) - prefer 1-3 syllables
- **ME**morabile (memorable) - easy to recall after one hearing
- **OR**iginale (original) - distinct from competitors
- **G**radevole (pleasant) - agreeable sound and feel
- **O**recchiabile (catchy) - phonetically engaging

### Step 3: Linguistic and Cultural Filtering

From the 30+ candidates, filter down to the best 8-10 by checking:
- Pronunciation ease in all target languages
- No negative/offensive meanings in English, Italian, Spanish, French, German, Portuguese, Chinese, Japanese
- No unfortunate phonetic associations (sounds like profanity, disease, etc.)
- Phonosymbolism alignment (round sounds = soft/friendly, sharp sounds = energy/precision)
- No excessive similarity to existing major brands

### Step 3b: Quick Domain Gate

Before full analysis, run a rapid viability check on each of the 8-10 filtered candidates:

- For each name, WebSearch for `"name.com"` and `"name" app`
- If .com is owned by an established company (Fortune 500, funded startup, active SaaS), **silently discard** the name
- Generate a replacement name using the same morphological techniques and re-filter it
- Only names that pass this quick gate proceed to the full Step 4-6 analysis
- Goal: eliminate obviously blocked names before spending search calls on deep analysis

### Step 4: Domain and Social Check

For the top 8-10 names that passed the Quick Domain Gate, verify:
- `.com` domain availability (use `scripts/domain_checker.py` if API key configured, otherwise use WebSearch)
- Alternative TLDs: `.app`, `.io`, `.co`, `.dev`, or country-specific
- Social media handle availability on major platforms (search via web)

Report findings in a table:
```
| Name | .com | .app | .io | Twitter/X | Instagram |
```

### Step 5: Trademark Pre-screening

For each remaining candidate:
- Search EUIPO (TMview), USPTO (TESS), WIPO Global Brand Database via WebSearch
- Flag exact matches or confusingly similar marks in the same Nice class
- Rate risk: LOW (no matches) / MEDIUM (similar in different class) / HIGH (conflict in same class)

### Step 6: Market Saturation Analysis (Fail-Fast)

For each candidate, perform a fail-fast market saturation check using WebSearch. Run checks in order - if a name fails an early gate, skip remaining checks and discard:

**6a. Domain activity check (GATE - run first)**
- If .com is registered, visit it (WebFetch or WebSearch `site:name.com`) to determine if it's an active business, parked domain, or dead page
- Check alternative TLDs too (.app, .io, .co) for active competitors
- Rate: ACTIVE BUSINESS (red flag) / PARKED (moderate risk) / AVAILABLE (clear)
- **If ACTIVE BUSINESS in same sector: discard immediately, generate replacement, skip remaining checks**

**6b. App store saturation (only if 6a passed)**
- Search "name" on Google Play Store and Apple App Store (via WebSearch: `"name" site:play.google.com`, `"name" site:apps.apple.com`)
- Count apps with identical or very similar names in the same category
- Rate: SATURATED (3+ same-category matches) / MODERATE (1-2 matches) / CLEAR (no matches)

**6c. SERP saturation - Google Test (only if 6a passed)**
- Google the exact name in quotes: `"exactname"`
- Assess first page results: are they dominated by an existing brand/product?
- Rate: DOMINATED (existing brand owns page 1) / COMPETITIVE (mixed results) / OPEN (few/no relevant results)

**6d. Social media presence (only if 6a passed)**
- Check if accounts with that name are active on Instagram, Twitter/X, TikTok, LinkedIn
- Distinguish between active brand accounts vs unused/personal handles
- Rate: TAKEN BY BRAND (red flag) / INACTIVE/PERSONAL (recoverable) / AVAILABLE (clear)

**6e. Industry-specific saturation (only if 6a passed)**
- Search `"name" + industry keywords` to find competitors using similar names
- Check Product Hunt, Crunchbase, AngelList for startups with that name (via WebSearch)
- Look for same-name businesses in adjacent sectors that could cause confusion

Present saturation findings in a summary table:
```
| Name | Domain Status | App Stores | SERP | Social | Industry | Overall Risk |
|------|--------------|------------|------|--------|----------|-------------|
```

Overall Risk rating: LOW (mostly clear) / MEDIUM (some conflicts) / HIGH (established competitor exists) / BLOCKED (identical active business in same sector)

### Step 6f: SEO Potential

For each candidate:
- Evaluate keyword relevance for organic discovery
- Estimate ranking difficulty based on SERP saturation findings above
- Rate SEO potential: HIGH / MEDIUM / LOW

### Step 7: Scoring and Ranking

Score the top 5 names on a 0-100 scale using these weighted criteria:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Memorability | 15% | Easy to recall after one hearing (Phone Test: 70%+ recall) |
| Distinctiveness | 15% | Unique vs competitors, not generic |
| Market Saturation | 15% | No active businesses, apps, or dominant SERP presence with same name (invert: low saturation = high score) |
| Simplicity/Pronunciation | 10% | Easy to say and spell (Spelling Test: 80%+ accuracy) |
| Relevance | 10% | Connection to brand values/product |
| SEO Potential | 10% | Online visibility, keyword alignment |
| Domain Availability | 10% | .com or strong alternative TLD available |
| Trademark Risk | 5% | Low conflict probability (invert: low risk = high score) |
| Emotional Impact | 5% | Evocative power, storytelling potential |
| Cultural Adaptability | 5% | Works across target languages and cultures |

Formula: `Final Score = SUM(criterion_score * weight)`

Present as a detailed scoring table with per-criterion breakdown.

### Step 8: Final Presentation

Deliver the top 3 names with:
1. **Scoring table** with all criteria and final weighted score
2. **Name story** - etymology, meaning, why it works for this brand
3. **Market saturation report** - existing apps, websites, businesses with same/similar name and risk level
4. **Domain status** - best available domain option
5. **Trademark risk** - summary of screening results
6. **Visual suggestion** - how the name could look as a wordmark (font style, case)
7. **Tagline idea** - a complementary tagline for each name

## Reference Framework

### Evaluation Tests (from Spellbrand methodology)

- **Phone Test**: Say the name once over phone. 70%+ of listeners should remember it correctly.
- **Spelling Test**: Say the name aloud. 80%+ of listeners should spell it correctly.
- **Google Test**: Search the exact name. If results are saturated with unrelated content, reconsider.
- **T-shirt Test**: Would someone wear this name on a shirt? Tests likability and pride.
- **Radio Test**: Would a radio listener find the brand online after hearing the name once?

### Name Style Decision Guide

| Goal | Best Archetype | Example |
|------|---------------|---------|
| Strong trademark | Brandable Names | Kodak, Rolex, Noom |
| Emotional energy | Evocative | RedBull, Forever21, Nike |
| Instant clarity | Short Phrase | Dollar Shave Club, MyFitnessPal |
| SEO advantage | Short Phrase | Booking.com, WeTransfer |
| Balanced clarity + distinctiveness | Compound Words | FedEx, YouTube, WordPress |
| Distinctive + registrable | Alternate Spelling | Lyft, Fiverr, Tumblr |
| Cultural depth | Non-English Words | Toyota, Audi, Volvo |
| Global expansion | Brandable Names | Google, Rolex, Kodak |
| Maximum memorability | Real Words | Apple, Slack, Notion |
| Premium positioning | Non-English Words / Evocative | Audi, Tesla, Lululemon |

### Phonosymbolism Quick Reference

- Vowels `a`, `o` - open, warm, large, friendly
- Vowels `i`, `e` - small, precise, light, fast
- Consonants `b`, `m`, `l` - soft, round, comforting
- Consonants `k`, `t`, `p` - sharp, strong, energetic
- Consonants `s`, `f`, `v` - flowing, smooth, elegant
- Consonants `r`, `g` - rugged, powerful, dynamic

### Morphological Generation Techniques

See `references/naming-frameworks.md` for the full morphological toolkit including suffix inventories, consonant shift rules, V-C-V-C-V structures, and cross-linguistic blending patterns.

## Domain Checker Script

If the user has configured API keys, use the domain checker script:

```bash
python scripts/domain_checker.py name1 name2 name3
```

The script checks `.com` availability via WHOIS API. See `scripts/domain_checker.py` for setup instructions.

If no API key is available, fall back to WebSearch queries like `"namexyz.com" site:whois` or check registrar sites manually.
