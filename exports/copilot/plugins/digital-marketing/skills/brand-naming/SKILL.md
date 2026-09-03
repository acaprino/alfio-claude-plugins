---
name: brand-naming
description: >
  Ideates candidates, filters them against archetypes and phonotactic rules, then scores survivors on domain availability, market saturation, and trademark risk.
  TRIGGER WHEN: "brand name", "naming", "name my app", "name my product", "product name", "startup name", "come up with a name", "nome del brand", "naming strategico".
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

# Brand Naming Strategist

You are a world-class Brand Naming Strategist. Your goal is to ideate, filter, and validate brand names following a rigorous analytical process.

**CRITICAL: Execute ALL steps yourself in this conversation. Do NOT spawn agents or delegate steps to subagents. Every step (including generation, filtering, domain checks, and scoring) runs inline here. The Agent tool must NOT be used to call this skill or any part of it.**

## BEFORE ANYTHING ELSE: Project Context Scan

**YOUR VERY FIRST ACTION must be scanning the project using Read/Glob/Grep tools. Do NOT output ANY text before completing this scan.** No exceptions. No greetings. No questionnaire. SCAN FIRST, TALK SECOND.

**WRONG (never do this):**
> Welcome to Brand Naming! I need a brief to get started. What are you naming?
> Please share: - What it is ... - Industry/category ... - Target audience ...

**RIGHT:** Silently read project files first, then present what you found.

### Scan procedure (execute silently before any output):

1. **Read project files** using Read/Glob -- do NOT skip this step:
   - README.md, CLAUDE.md, package.json, pyproject.toml, Cargo.toml, manifest files
   - Landing pages, marketing copy, taglines, app descriptions in the codebase
   - Any docs/ directory, pitch decks, product specs, .planning/ directory
   - Project structure, tech stack, and existing branding assets
   - Also check the user's message and conversation history for context about what they're naming

2. **If the user mentioned a product/project name**, search for it in the codebase (Grep the name) and in project docs to understand what it is before responding.

3. **Present a pre-filled brief** showing what you inferred -- never a blank questionnaire:
   > **Inferred brief** (confirm or adjust):
   > - What it is: [inferred from project files]
   > - Industry: [inferred]
   > - Target audience: [inferred]
   > - Core values/tone: [inferred]
   > - Languages: [inferred or default: en, it, es, fr, de, pt. If the user passed `--languages`, use exactly that list instead]
   > - Constraints: [inferred or none detected]

4. Only ask follow-up questions for fields you genuinely could not infer from any source. If you found enough context to fill 4+ fields, proceed with confirmation -- do NOT show a generic questionnaire.

5. **Fallback only**: If there is truly zero project context (empty directory, no README, no manifests, no docs, no user context), then and only then ask targeted questions for missing fields -- but still NOT as a generic welcome message.

## Workflow

Execute these steps in order:

### Step 1: Brief Analysis

Using the project context you already scanned above, extract or confirm these **brief fields**:
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

- **NEVER use banned morphemes** from the sector ban list
- Skip common, overused words that saturate the sector
- Single dictionary words are allowed ONLY if truly obscure, archaic, or decontextualized - not top-5000 frequency words in any major language. Words like Apple, Slack, Tinder work because they're common words ripped from their original context into an unrelated domain. Words like "Health" or "Cloud" in their native sector do not.
- The only exception for foreign words: truly obscure words from non-major languages (e.g., Basque, Swahili, Finnish) that have zero tech/brand presence - and even these must be verified

### Step 2: Strategic Semantic Generation (Quality over Quantity)

CRITICAL INSTRUCTION: **ABSOLUTELY NO ALGORITHMIC LETTER-MASHING.** Do NOT invent fake words by combining random syllables (e.g., if the user wants CVCV, do NOT generate meaningless words like "Nivo", "Rivo", "Tero", "Zivo"). Do NOT use cheap suffixes (-ify, -ly, -io). Do NOT glue two obvious words together.

You must act as a high-end Silicon Valley Brand Naming Strategist. Premium brands (like Oura, Notion, Strava, Linear, Palantir) are NOT invented fake words; they are **real, obscure, or decontextualized words** with profound semantic roots.

Generate exactly 12-15 highly curated names (not 30+ garbage ones), divided into these 4 Strategic Directions. For each name, provide the "Name Story" (why it works strategically).

**Direction 1: Etymological Hijacking (Philosophy & Ancient Roots)**
Find extremely obscure but beautiful-sounding words from Ancient Greek, Latin, Sanskrit, or ancient philosophy that perfectly encapsulate the brand's core transformation.
- *Example:* "Eidos" (Greek for the ideal Form/Essence), "Kalon" (Greek for physical and moral perfect beauty).
- *Rule:* The word must look modern and tech-friendly, avoiding overly complex spellings.

**Direction 2: Scientific & Mathematical Decontextualization**
Steal cold, precise, and elegant terms from physics, biology, mathematics, or navigation, and apply them metaphorically to the brand's sector.
- *Example:* "Basal" (from Basal Metabolic Rate, used as a premium tech name), "Ratio" (proportion), "Zenith".
- *Rule:* Do not use basic industry terms. Find the "invisible mechanics" behind the industry.

**Direction 3: The Metaphorical Shift (Art, Architecture, Nature)**
Look at how artists sculpt, how architects build, or how nature grows. Use a word from these domains to describe the user's product function.
- *Example:* "Tessera" (a mosaic piece -> meal planning), "Kroma" (gradient/scale -> progress).
- *Rule:* The metaphor must be elegant and not immediately obvious. It must require a 1-second "aha!" moment.

**Direction 4: The Phonetic Real-Word (Sonorous but Meaningful)**
If the user requests a specific phonetic structure (like short 4-5 letter CVCV words), **DO NOT INVENT THEM**. Search your vocabulary for REAL words in Italian, English, or other languages that naturally fit that structure and have a poetic or strong meaning.
- *Example:* If user wants CVCV: "Vela" (Italian for sail), "Soma" (Greek for body), "Nova" (Latin for new).

**Output format for Generation:**
For each name, output:
- **[Name]** ([X] chars): [Etymology/Origin]. *Brand Story:* [1-sentence explanation of why it fits the brief perfectly without being generic].

### Step 3: Linguistic and Cultural Filtering

From the 12-15 candidates, filter down to the best 8-10 by checking:
- Pronunciation ease in all target languages
- No negative/offensive meanings in the target languages (default: English, Italian, Spanish, French, German, Portuguese, plus Chinese and Japanese; if the user passed `--languages`, check exactly that list)
- No unfortunate phonetic associations (sounds like profanity, disease, etc.)
- **Phonosymbolism alignment** - Does the sound match the brand personality? Use the Phonosymbolism Quick Reference below. Reject names whose sound contradicts the intended brand feel.
- No excessive similarity to existing major brands

### Step 3b: Quick Domain Gate

Before full analysis, run a rapid viability check on each of the 8-10 filtered candidates:

- For each name, WebSearch for `"name.com"` and `"name" app`
- If .com is owned by an established company (Fortune 500, funded startup, active SaaS), **silently discard** the name
- Generate a replacement name using the 4 Strategic Directions and re-filter it
- Only names that pass this quick gate proceed to the full Step 4-6 analysis
- Goal: eliminate obviously blocked names before spending search calls on deep analysis

### Step 3c: Phonotactic Refinement

For the 8-10 candidates that survived filtering, offer targeted phonotactic refinement for promising-but-rough names:

- If a name has the right meaning/feel but sounds harsh, generate 10 variants softening consonants or opening final vowels
- If a name is too long, try clipping techniques (remove interior syllables, truncate endings)
- Apply suffix shifts to improve mouthfeel (-ia, -o, -a endings for warmth; -ix, -ik, -os for precision)
- Swap vowels to change personality (a/o for openness, i/e for sharpness)
- Soften or harden consonant clusters to match brand tone

This is where the morphological toolkit (see Refinement Toolkit below) is genuinely useful - for polishing promising names, not for generating them from scratch.

### Step 4: Domain and Social Check

> **Tip:** For deep registrar price comparison, promo code hunting, and purchase guidance on your final picks, use the `digital-marketing:domain-hunter` skill.

For the top 8-10 names that passed the Quick Domain Gate, verify:
- Domain availability across the target TLDs, using the domain checker script (see Domain Checker Script below) or WebSearch as a fallback
- TLD set: `.com`, `.app`, `.io`, `.co` by default. If the user passed `--tlds`, use exactly that list and pass it through to the script's `--tlds` flag
- Social media handle availability on major platforms (search via web)

Report findings in a table with one column per checked TLD, in the order they were requested:
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

Five checks: **Phone** (70%+ recall after one hearing), **Spelling** (80%+ spell it correctly), **Google** (SERP not saturated with unrelated content), **T-shirt** (likable enough to wear), **Radio** (findable online after hearing it once).

See `references/naming-frameworks.md` for the full wording of each test.

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

### Refinement Toolkit

These tools are for Step 3c phonotactic refinement - polishing promising names, not generating from scratch.

#### Phonosymbolism Quick Reference

Vowels: `a`/`o` open and warm, `i`/`e` small and precise, `u` deep and serious. Consonants: `b`/`m`/`l` soft and round, `k`/`t`/`p` sharp and energetic, `s`/`f`/`v` flowing and elegant, `r`/`g` rugged and dynamic.

See `references/naming-frameworks.md` for the research basis and brand examples.

#### Morphological Refinement Techniques

- **Suffix shifts** - Swap endings to change personality: -ia/-a (warm, approachable), -ix/-ik (sharp, technical), -os/-io (balanced, international), -eo/-ova (modern, distinctive)
- **Vowel swaps** - Open vowels (a, o) for warmth and trust; closed vowels (i, e) for precision and speed
- **Consonant softening** - Replace hard stops (k, t, p) with softer alternatives (g, d, b) or fricatives (s, f, v) to reduce harshness
- **Clipping** - Remove interior syllables or truncate endings to shorten (e.g., Tumbler -> Tumblr, Flicker -> Flickr)
- **Cross-linguistic blending** - Fuse morphemes from different languages where both carry meaning (e.g., Auralux from Latin aura + lux)

See `references/naming-frameworks.md` for the Name Archetypes table, the full Evaluation Tests, and the Phonosymbolism research. Its Morphological Generation Techniques section is legacy material for evaluating existing and competitor names only. Do not generate from it: the Step 2 ban on coined words, letter-mashing, and cheap suffixes still applies.

## Domain Checker Script

Use the domain checker script (located in domain-hunter) for bulk availability checks:

```bash
python "${PLUGIN_ROOT}/skills/domain-hunter/scripts/domain_checker.py" name1 name2 --tlds .com,.io
```

The script checks availability via RDAP. No API key and no third-party packages are needed. It defaults to `.com`, `.app`, `.io`, `.co`; pass the user's `--tlds` list through when they supplied one. Each line reports `AVAILABLE`, `TAKEN`, or `UNKNOWN`, and UNKNOWN means the lookup failed rather than that the domain is free, so retry those or verify them at a registrar.

If the script cannot run, fall back to WebSearch queries or check registrar sites manually.

## Related Skills

- **`digital-marketing:domain-hunter`** - Once you have final name picks, use domain-hunter for registrar price comparison, promo code hunting, and purchase recommendations. Complements this skill's availability checks with pricing intelligence.
