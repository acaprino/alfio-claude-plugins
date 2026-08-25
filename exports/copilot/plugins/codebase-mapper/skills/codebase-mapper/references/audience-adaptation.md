# Audience Adaptation

Documentation must reflect the project it describes and serve the people who will actually read it. A security CLI and a consumer mobile app should not read the same way. This reference defines the Project Profile (what the explorer infers about a project) and the register model (how every writer calibrates tone, depth, and structure to that profile). All codebase-mapper writers read this file on demand, not upfront.

## Project Profile (schema)

The `codebase-explorer` produces this profile as the first section of `context-brief.md`. Every writer consumes it. Fields:

- **Project type / domain**: the closest of security or infrastructure tool, developer library or SDK, CLI tool, consumer web or mobile app, internal line-of-business app, data or ML pipeline, game, framework, API or backend service. Add a domain tag (for example banking, healthcare, devtools, e-commerce).
- **Primary audience**: the main reader (for example backend engineers, mobile developers, banking operators, data scientists, end users, stakeholders).
- **Secondary audiences**: other readers to serve at the plain-language layer (for example PMs, QA, designers, new hires, clients).
- **Register**: a point on the spectrum from `technical-precise` through `balanced` to `accessible-vivid`.
- **Purpose / problem solved**: one short paragraph. The WHY: what problem this solves and for whom.
- **Scope**: what the project does.
- **Non-goals**: what it deliberately does not do.
- **Maturity**: prototype, active, production, or maintenance.
- **Confidence + signals**: for each inference above, a confidence (high, medium, low) and the signals it rests on (dependencies, naming, README framing, UI presence, distribution channel, domain vocabulary, git history). Low-confidence items are surfaced at the confirm step.

## Register matrix

How the profile maps to output parameters:

| Register | Tone | Jargon policy | Example style | Diagram emphasis | Depth split | Plain layer and glossary |
|---|---|---|---|---|---|---|
| Technical-precise (tool, library, CLI, infra) | Exact, terse, contract-aware | Use freely, define on first use | API calls, config snippets, signatures | Architecture, sequence, data model | Internals deep, plain layer brief | Short executive summary, glossary for domain terms |
| Balanced (service, API, internal app) | Clear, explanatory | Use but explain | Request and response, workflows | Architecture plus workflows | Even | Moderate executive summary, full glossary |
| Accessible-vivid (consumer app, game) | Friendly, benefit-led, concrete | Avoid, explain everything in plain words | User flows, screenshots, scenarios | Flowcharts, mindmaps | Internals light, plain layer is the centerpiece | Prominent executive summary, full plain-language glossary |

The register is a dial, not three buckets. Pick the nearest column and lean toward the profile.

## Archetypes

Concrete calibrations. Match by the signals line, then write per the how line.

**Technical or infrastructure tool** (security tool, library, SDK, CLI)
- Signals: no end-user UI; distributed via a package registry or a binary; the dependency list is developer tooling; the README addresses developers; the vocabulary is technical.
- How: precise and complete. Lead with contracts, invariants, threat surface, and exact interfaces. Internals go deep. The plain layer is a short hand-off, not the focus.

**Consumer app** (web or mobile, end-user facing)
- Signals: a UI framework is present; distribution is an app store or the web; product or landing copy lives in the repo; feature names are user-facing.
- How: benefit-led and vivid. Lead with what the user can do and why it matters. Use user-flow framing and scenarios. Keep internals light. The plain layer is the centerpiece.

**Domain or business app** (internal line-of-business)
- Signals: heavy domain vocabulary; integrations with internal systems; role and permission models; the README assumes domain knowledge.
- How: glossary-heavy and workflow-led. Frame everything around the business process and the operator's task. Define every domain term.

**Data or ML pipeline**
- Signals: dataset handling, model code, batch or stream processing, notebooks, training or evaluation scripts.
- How: dataset-and-transform framing. Lead with data lineage: where data comes from, how it is transformed, where it lands. Document schemas, evaluation, and cost.

**Game**
- Signals: a game loop, rendering, physics or asset libraries, scene or entity systems.
- How: core-loop and mechanics framing. Lead with what the player does and how the loop runs, then the systems (input, render, state).

## The "for everyone" rule

Every guide produces two always-present documents, whatever the register:

- `00-executive-summary.md`: a plain-language entry point anyone can read, including non-technical stakeholders. What it is, the problem it solves, who it is for, why it matters. Zero unexplained jargon. Use an analogy where it helps.
- `11-glossary.md`: a domain and technical glossary with plain definitions.

Only their prominence and length scale with the profile. For a technical project the executive summary is brief and hands off quickly to the deep docs. For a consumer or mixed-audience project it is the centerpiece and the glossary is generous. They are never omitted, because "comprehensible by everyone" needs at least one no-jargon door into the project.

## How writers apply this

- `overview-writer`: owns `00-executive-summary.md`; calibrates the register of 01 and 02; leads with the WHY for accessible profiles.
- `tech-writer`: the depth of tech-stack and architecture scales with register; uses plain analogies for accessible profiles.
- `flow-writer`: workflow and data-model framing follows the archetype (user-flow, data-lineage, or core-loop).
- `onboarding-writer`: getting-started tone matches the primary audience; non-technical readers get orientation, not only commands.
- `ops-writer`: project-anatomy stays reference-grade; jargon is softened for mixed audiences.
- `config-writer`: configuration recipes use the audience's vocabulary.
- `guide-reviewer`: owns `11-glossary.md`; checks register consistency and that the plain layer serves a non-technical reader.
