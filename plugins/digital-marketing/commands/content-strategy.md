# Content Strategy

Use the `content-marketer` agent to perform a marketing material and conversion optimization audit for:

$ARGUMENTS

## Workflow

Execute as a structured, multi-phase process. Analyze the target (URL or local files) for UX patterns, CTAs, copy quality, product presentation, social media readiness, and conversion optimization. Use Playwright browser tools for live page analysis when working with URLs.

### Phase 1: Audit Scope

Establish what you're working with before diving in.

1. **Read target** — navigate to URL (Playwright) or read local files
2. **Identify page types** — classify each page: landing page, product page, blog post, about page, contact, pricing, checkout, category, FAQ
3. **Understand the business** — extract value proposition, target audience, product/service offering, competitive positioning from existing content
4. **Baseline metrics** — note current state: page count, content volume, CTA count, form count, social links

Present scope summary and confirm focus areas before proceeding.

### Phase 2: UX & Conversion Audit

Evaluate every element that affects user behavior and conversion.

**Page Layout**
- Visual hierarchy: clear focal points, F-pattern or Z-pattern compliance
- Above-the-fold: value prop + primary CTA visible without scrolling
- Whitespace: adequate breathing room, not cramped
- Content sections: logical flow from problem → solution → proof → action
- Page length: appropriate for page type (long-form landing vs. concise product)

**Calls-to-Action**
- Presence: every page has a clear next step
- Clarity: button text uses action verbs ("Start free trial", not "Submit")
- Contrast: CTAs visually distinct from surrounding elements
- Placement: above fold, after value props, after social proof, at page bottom
- Urgency/scarcity: appropriate use (not manipulative)
- Primary vs. secondary: clear hierarchy, one primary CTA per section
- Mobile CTAs: thumb-reachable, full-width on small screens

**Social Proof**
- Testimonials: present, attributed (name, role, company), specific results
- Reviews/ratings: star ratings, review count, from credible sources
- Trust badges: security seals, certifications, payment icons, money-back guarantee
- Client logos: recognizable brands, "as seen in" media mentions
- Case studies: linked or summarized with metrics
- Numbers: user count, years in business, satisfaction rate

**Product Presentation**
- Gallery: 5+ images minimum (front, side, detail, in-use, scale reference)
- Image quality: high-res, consistent lighting/style, zoom capability
- Video: product demo, explainer, or testimonial video present
- Alt text: descriptive for accessibility and SEO
- 360-view: available for physical products (nice-to-have)

**Pricing**
- Clarity: prices visible, no hidden fees, transparent billing
- Comparison table: feature matrix for multiple plans
- Anchoring: recommended plan highlighted, value framing
- Free trial/demo: CTA prominently placed near pricing
- FAQ near pricing: addresses common objections and billing questions
- Money-back guarantee: visible near purchase CTA

**Forms**
- Field count: minimize friction (name + email for lead gen, not 10 fields)
- Labels: clear, visible, not placeholder-only
- Error handling: inline validation, specific error messages
- Progress indicators: for multi-step forms
- Autofill support: proper input types and autocomplete attributes
- Mobile-friendly: appropriate keyboard types, large touch targets

**Navigation**
- Clear hierarchy: logical menu structure, max 7 top-level items
- Breadcrumbs: present on deep pages
- Search: available, functional, returns relevant results
- Mobile menu: hamburger with clear labels, not just icons
- Sticky header: accessible navigation on long pages
- Footer: sitemap links, contact info, legal links

### Phase 2b: Social Media Audit

Evaluate social presence and share-readiness.

**OG/Twitter Tags**
- og:title, og:description, og:image (1200x630), og:type, og:url, og:site_name
- twitter:card, twitter:title, twitter:description, twitter:image (1200x675)
- Validate share previews: how pages render when shared on Facebook, Twitter/X, LinkedIn, WhatsApp

**Social Profiles**
- Linked from website: header/footer social icons
- Consistent branding: same name, logo, bio across platforms
- Active presence: recent posts (not abandoned accounts)

**Share Buttons**
- Placement: visible but not intrusive, on shareable content
- Platforms: relevant to audience (not every platform)
- Mobile-friendly: functional on touch devices
- Share counts: displayed if numbers are impressive

**Social Content Strategy**
- Content mix: 80/20 value/promotion ratio
- Posting frequency: consistent schedule appropriate to platform
- Engagement: responding to comments, community building
- Platform-specific: content adapted to each platform's format and audience

**Platform-Specific** (assess which are relevant)
- Instagram: visual consistency, hashtag strategy, bio link optimization, Stories/Reels
- LinkedIn: thought leadership, company page completeness, employee advocacy
- Twitter/X: thread strategy, engagement tactics, brand voice
- Facebook: community building, events, groups, ad integration

**Social Commerce** (if applicable)
- Shoppable posts: product tagging on social platforms
- Direct checkout links: minimal friction from social to purchase
- User-generated content: reviews, photos, unboxing shared on social

### Phase 3: Content & Copy Audit

Evaluate all written content for clarity, persuasion, and SEO.

**Headlines**
- Clarity: reader understands the offer in 5 seconds
- Benefit-driven: focuses on outcome, not features
- Keyword presence: natural, not stuffed
- Emotional triggers: curiosity, urgency, exclusivity (appropriate use)
- Hierarchy: H1 → H2 → H3 support scanning

**Body Copy**
- Scannable: short paragraphs (3-4 lines), bullets, subheadings every 2-3 paragraphs
- Benefit-focused: features translated to user benefits
- Objection handling: addresses "why not?" and "what if?"
- Specificity: numbers, timeframes, concrete examples (not vague claims)
- Reading level: appropriate for target audience (aim for grade 8-10 for general)

**Tone & Voice**
- Consistency: same voice across all pages
- Audience-appropriate: matches target demographic expectations
- Brand alignment: reflects brand personality (professional, friendly, bold, etc.)
- Authenticity: not generic or AI-sounding boilerplate

**SEO Copy**
- Keyword density: natural (1-2%), not stuffed
- Internal links: contextual links to related content
- Meta descriptions: compelling, include CTA, within character limits
- Featured snippet targeting: answer boxes, lists, tables for question-based queries
- Content length: appropriate for search intent (pillar pages 2000+, product pages 300+)

**Microcopy**
- Button labels: specific ("Download the guide" vs. "Click here")
- Form hints: helpful placeholder text and field descriptions
- Error messages: friendly, specific, actionable
- Empty states: helpful guidance when no content/results
- Loading states: informative progress indicators
- Confirmation messages: clear next steps after form submission

**Product Descriptions**
- Feature → benefit framing: what it does → why it matters to the user
- Specifications: complete, organized, scannable
- Comparison: how it differs from alternatives
- Use cases: specific scenarios where the product excels

### Phase 4: Visual & Media Audit

Evaluate imagery and media assets.

**Images**
- Quality: high-resolution, professional, not pixelated or stretched
- Relevance: support the content, not generic stock photos
- Consistency: unified style, color palette, treatment across the site
- Alt text: descriptive, keyword-relevant
- Performance: optimized file sizes, WebP/AVIF format, lazy loading

**Product Gallery**
- Count: 5+ images per product (front, side, detail, lifestyle/in-use, scale)
- Angles: variety of perspectives showing key features
- Zoom: click-to-zoom or hover-zoom functionality
- Lifestyle shots: product in context, showing real-world usage
- Consistency: uniform background, lighting, and style across catalog

**Video**
- Hero video: brand/product overview on key landing pages
- Product demos: showing the product in action
- Testimonials: customer stories on video
- Thumbnail quality: compelling, not auto-generated frames
- Loading: doesn't block page render, plays on interaction

**Icons & Illustrations**
- Consistent style: same weight, style, and color system
- Meaningful: convey information, not purely decorative
- Accessible: not relying solely on icons for meaning (paired with labels)

### Phase 5: Plan & Confirm

Synthesize findings into an actionable plan.

1. **Findings summary**: grouped by category, severity (critical / important / nice-to-have)
2. **Specific improvements**: before/after examples for key changes
3. **Quick wins**: changes with high impact and low effort
4. **Major recommendations**: bigger changes requiring design/content decisions
5. **Estimated impact**: which changes are likely to improve conversion the most

**Wait for user approval** on which improvements to implement.

### Phase 6: Apply & Report

Implement approved changes and document results.

1. **Apply changes**: implement in logical batches (copy first, then structure, then media)
2. **Before/after comparison**: show what changed on each page
3. **Summary report**: changes made, expected impact, conversion optimization rationale
4. **Remaining recommendations**: items requiring manual intervention (photography, video production, design work)
5. **Ongoing strategy**: content calendar suggestions, A/B testing opportunities, metrics to track

## Quick Examples

- `/content-strategy https://example.com` — Full marketing material audit of a live website
- `/content-strategy https://example.com/pricing` — Audit pricing page for conversion optimization
- `/content-strategy src/pages/landing.html` — Audit local landing page files
- `/content-strategy https://example.com --focus cta,social-proof` — Focused audit on CTAs and social proof
- `/content-strategy https://example.com --competitor https://rival.com` — Compare marketing effectiveness against a competitor
- `/content-strategy https://example.com --social` — Focus on social media presence and share optimization
