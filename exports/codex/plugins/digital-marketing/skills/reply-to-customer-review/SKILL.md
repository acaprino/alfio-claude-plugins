---
name: reply-to-customer-review
description: >
  Reads sentiment and severity, then adapts tone and operational advice to the sector, hospitality or e-commerce.
  TRIGGER WHEN: review, recensione, reply to review, respond to review, risposta recensione, customer review, negative review, bad review, rispondere alla recensione, gestione recensioni, review response.
---

# Reply to Customer Review

Generate a professional, empathetic response to a customer review. Analyze the review, craft an adaptive response, and provide operational suggestions.

## Input

The user pastes a customer review (or invokes via `/reply-to-customer-review`). Optional parameters:

- **--brand "Name"** -- business name to use in the response
- **--tone formal|friendly|casual** -- override tone (default: professional-empathetic)
- **--lang XX** -- force output language (default: same as review)
- **--sector hospitality|ecommerce|auto** -- force sector (default: auto-detect)

If invoked without arguments, prompt the user to paste a review.

## Process

Execute all four steps inline. Do NOT spawn subagents.

### Step 1: Analysis

Analyze the review and determine:

**Language** -- identify the review language. For mixed-language reviews, identify the dominant language and note secondary languages.

**Sentiment** -- classify as one of:
- POSITIVE -- satisfied customer, praise, recommendation
- NEUTRAL -- factual, neither praise nor complaint
- NEGATIVE -- dissatisfaction, complaint, criticism
- MIXED -- contains both positive and negative elements

**Key Points** -- extract the specific topics mentioned (e.g., cleanliness, shipping speed, product quality, staff attitude, app stability, price, location).

**Severity** (negative/mixed reviews only) -- assess as one of:
- UNFOUNDED -- no real issue, emotional venting, unrealistic expectations
- MINOR -- real issue but limited impact, easy to address
- MAJOR -- serious issue requiring immediate attention, systemic problem
- ABUSIVE -- contains threats, profanity, personal attacks. Flag for platform reporting. Recommend not responding publicly or generate a minimal professional response. Never mirror hostility.

**Sector** -- auto-detect from vocabulary and context:
- HOSPITALITY -- mentions stay, check-in, room, host, property, booking, location, amenities, noise, breakfast
- ECOMMERCE -- mentions shipping, delivery, return, refund, product, app, crash, bug, update, order, package
- GENERIC -- does not clearly match either sector

Load the appropriate reference file: `references/hospitality-patterns.md` or `references/ecommerce-patterns.md`. If generic, use general best practices.

### Edge Cases

- **Star-only (no text):** Ask the user for the star rating. Generate a brief acknowledgment appropriate to the implied sentiment.
- **Very short (under 5 words):** Flag ambiguity in Analysis. Generate a brief response inviting the customer to share more details.
- **Mixed-language:** Respond in the dominant language. Note secondary language in Analysis.

### Step 2: Response Generation

Craft the response following these rules:

**Tone:** Use the user-specified tone or default to professional-empathetic. The tone scale:
- `formal` -- corporate, third-person, measured language
- `friendly` -- warm, first-person, conversational but professional (this is the professional-empathetic default)
- `casual` -- relaxed, direct, uses contractions and informal phrasing

**Language:** Respond in the same language as the review unless --lang overrides.

**Brand:** If --brand is provided, sign off with the brand name. If not, use a generic professional sign-off.

**Adaptive strategy for negative reviews:**

| Severity | Strategy | Key Elements |
|----------|----------|-------------|
| UNFOUNDED | Diplomatic-defensive | Acknowledge feelings, provide factual context, invite private contact |
| MINOR | Empathetic-proactive | Thank for feedback, acknowledge the issue, describe corrective action taken, invite return |
| MAJOR | Empathetic-proactive (urgent) | Sincere apology, take full responsibility, describe immediate corrective action, offer compensation, provide direct contact for follow-up |
| ABUSIVE | Minimal/No response | If responding: brief, professional, offer private channel. May recommend not responding and reporting to platform instead |

**For positive reviews:** Thank sincerely, reference specific points mentioned, reinforce the positive experience, invite return/continued use. Keep it genuine -- avoid sounding templated.

**For neutral reviews:** Thank for taking the time, address any suggestions, invite further engagement.

**Response length guidelines:**
- Positive reviews: 2-4 sentences
- Neutral reviews: 2-3 sentences
- Negative (minor): 3-5 sentences
- Negative (major): 4-6 sentences
- Abusive: 1-2 sentences max (if responding at all)

### Step 3: Humanization (inline, no subagent)

Load the `text-humanizer:anti-ai-writing-patterns` skill and apply its patterns to every drafted reply. It is the single source of truth for AI writing tells: inflated significance, promotional tone, AI vocabulary, copula avoidance, negative parallelisms, rule of three, synonym cycling, dash overuse, boldface and emoji, servile tone, filler, hedging, and generic positive conclusions. Do not restate or re-derive those rules here.

Then apply the review-reply rules the upstream ruleset does not cover:

1. No review-reply boilerplate: "We are sorry to hear...", "Thank you for taking the time...", "Your feedback is valuable...", "Your satisfaction is our priority...", "Thank you so much for your kind words!"
2. React to what the customer actually wrote. Reference specific details from their review instead of generic praise or generic regret.
3. Write idiomatically in the review's language. A translated-sounding reply reads as automated even when every word is correct.
4. Plain text ready to paste into the platform: no markdown, no headings, no bullet lists, no emoji.
5. Never invent facts, and never promise refunds, compensation, or fixes the user has not authorized.
6. Stay inside the length guideline for the sentiment and severity determined in Step 2.
7. Final check: "Would a real owner of this business actually write this?" If a sentence sounds like a chatbot or a corporate template, rewrite it.

### Step 4: Output

Present three clearly separated sections:

**RESPONSE**

The ready-to-copy response text (after AI trace removal), formatted for the review platform. No markdown formatting -- plain text that can be pasted directly.

**ANALYSIS**

| Field | Value |
|-------|-------|
| Language | [detected language] |
| Sentiment | [POSITIVE/NEUTRAL/NEGATIVE/MIXED] |
| Severity | [UNFOUNDED/MINOR/MAJOR/ABUSIVE or N/A] |
| Sector | [HOSPITALITY/ECOMMERCE/GENERIC] |
| Key Points | [comma-separated list] |
| Flags | [any concerns requiring attention, or "None"] |

**OPERATIONAL SUGGESTIONS**

Bulleted list of recommended internal actions based on the review content. Examples:
- Flag issue to [specific team]
- Update [specific asset] to reflect current state
- Contact customer privately via [channel]
- Offer [specific compensation]
- Monitor for recurring pattern of [issue]
- No action needed -- positive reinforcement

If the review is positive with no issues, suggest ways to leverage it (e.g., "Consider featuring this review on your website", "Share with the team as positive feedback").

## Refinement

After presenting the output, the user may request adjustments:
- "more formal" / "more casual" -- regenerate with adjusted tone
- "shorter" / "longer" -- adjust response length
- "in English" / "in italiano" -- regenerate in specified language
- "don't mention X" / "add Y" -- specific content adjustments

Regenerate only the RESPONSE section when adjusting. Keep Analysis and Operational Suggestions unchanged unless the user specifically asks to revise them.
