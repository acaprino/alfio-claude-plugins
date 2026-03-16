# Writing Guidelines for Codebase Mapper

## Voice and Tone

### Do
- Use active voice: "The router dispatches requests to handlers" not "Requests are dispatched by the router"
- Address the reader directly: "You'll find the config in..." not "One can find the config in..."
- Use concrete examples: "For instance, when a user clicks Submit, `handleSubmit()` in `src/components/Form.tsx` validates the input" not "The form handles submission"
- Explain jargon inline: "...uses a message broker (a service that routes messages between parts of the system)..."
- Be specific about locations: always include file paths when referencing code

### Don't
- Start with "This document covers..." or "In this section we will..."
- End with "In summary..." or "As we've seen..."
- Use "Let's dive in", "Let's explore", "Let's take a look"
- Use "leverages", "utilizes", "facilitates" - use plain words instead
- Write empty transitions: "Now that we understand X, let's move on to Y"
- Use hedging language: "It seems like", "It appears that" - either state the fact or mark it as uncertain in 08-open-questions.md

## Structure

### Document Layout
1. Title (H1) - descriptive, not clever
2. One-paragraph intro - what this document covers and why it matters
3. Content sections (H2) - each covering one concept
4. Subsections (H3) where needed - avoid going deeper than H3

### Progressive Disclosure
- Start each document with a 2-3 sentence summary of the key takeaway
- Begin sections with the "what" and "why" before the "how"
- Put the most important information first in every section
- Use diagrams early to give visual orientation before text details

### File Path References
- Always use relative paths from project root: `src/api/routes.ts`, not absolute paths
- Bold the file path on first mention in a section: **`src/api/routes.ts`**
- Group related files: "The authentication logic lives in `src/auth/` - specifically `login.ts` (credentials), `session.ts` (token management), and `middleware.ts` (route protection)"

## Handling Uncertainty

When something cannot be determined from the code alone:
- State what you can determine
- Mark the gap clearly: "Needs clarification: [specific question]"
- Add the item to 08-open-questions.md with context about why it matters
- Never fabricate an explanation to fill a gap

## Cross-References

Use relative markdown links between documents:
- "See [Architecture](04-architecture.md) for how these components connect"
- "The data model for this workflow is documented in [Data Model](06-data-model.md#entity-name)"
- Include section anchors for specific topics

## Length Guidelines

- 01-overview.md: 100-200 lines
- 02-features.md: 150-300 lines
- 03-tech-stack.md: 100-250 lines
- 04-architecture.md: 200-400 lines
- 05-workflows.md: 200-400 lines
- 06-data-model.md: 150-350 lines
- 07-getting-started.md: 100-200 lines
- 08-open-questions.md: 50-150 lines
- INDEX.md: 50-100 lines
