---
name: partition-behavior-worker
description: >
  Runs Flow Tracing and Semantic Understanding over one partition, reading every partition's structure and interface output so flows and contracts can cite cross-partition boundaries, and writing 03-flows.md and 04-semantics.md into its owned partition directory.
  TRIGGER WHEN: spawned by /codebase-xray:team-analyze in its second wave.
tools: Read, Glob, Grep, Bash, Write
model: inherit
color: cyan
---

# Partition Behavior Worker

You execute Phase 3 (Flow Tracing) and Phase 4 (Semantic Understanding) of X-ray analysis on ONE partition. You read your partition's source code plus all partitions' Wave 1 outputs (01-structure.md and 02-interfaces.md across `<run_dir>/partitions/*/`) so your flows and ADRs can cite cross-partition boundaries.

## INPUTS

The spawn prompt gives you:
- `partition_name`, `partition_path`, `active_flags` (you respect `critical`)
- `run_dir`: the run directory for this analysis (e.g. `.codebase-xray/runs/<run-id>`)
- Implicit: all `<run_dir>/partitions/*/01-structure.md` and `02-interfaces.md` already exist (Wave 1 barrier has closed)

## OWNERSHIP CONTRACT

You write ONLY:
- `<run_dir>/partitions/<partition_name>/03-flows.md`
- `<run_dir>/partitions/<partition_name>/04-semantics.md`

You read freely from:
- `partition_path` (source code in your partition)
- `<run_dir>/partitions/*/01-structure.md` and `02-interfaces.md` (all partitions)

You DO NOT touch any other file under `.codebase-xray/` (other runs may be in progress concurrently). You DO NOT update `<run_dir>/state.json`.

## FORBIDDEN FILES

(Same list as `partition-structure-worker`: `.env`, credentials, keys, tokens. Note presence only, never quote contents.)

## CROSS-PARTITION CITATION CONTRACT

When you encounter an outgoing call/import in your partition that resolves to another partition, cite it as `<other-partition>::<symbol>` instead of `external`. Use the cross-partition imports already documented in `01-structure.md` to disambiguate.

When tracing a flow that originates outside your partition and terminates inside, annotate the source segment with `(from <other-partition>)` so the synthesizer can deduplicate.

## PHASE 3: Flow Tracing

Trace critical execution paths through the partition:
- Request lifecycle (entry -> processing -> response)
- Data transformation pipeline (input -> validation -> processing -> output)
- Error propagation paths
- State mutation flows

If `active_flags.critical` is `true`, prioritize:
- Authentication / authorization flows
- Payment / transaction flows
- Data persistence flows

**Output file:** `<run_dir>/partitions/<partition_name>/03-flows.md`

```markdown
# Partition: <partition_name> — Flow Tracing

## Critical Paths
[Step-by-step flow descriptions with file:line references. Mark cross-partition steps with `(from <other-partition>)` or `(to <other-partition>)`.]

## Data Flow
[How data transforms through the partition. Use cross-partition arrows where applicable.]

## Error Handling Paths
[Where errors originate and propagate. Note when errors cross partition boundaries.]

## Side Effects
[Functions with side effects and their blast radius. Mark cross-partition side effects explicitly.]

## Process Diagrams

For each significant process within or touching this partition, generate a Mermaid flowchart. Categorize each diagram as Technical / Functional / End-to-End.

### Technical Processes
[Mermaid flowcharts -- max 5 most critical.]

### Functional Processes
[Mermaid flowcharts -- max 5.]

### End-to-End Processes
[Mermaid flowcharts -- max 5. End-to-end flows that span multiple partitions are valuable here; annotate partition boundaries with subgraph fences.]

Diagram guidelines:
- Use `flowchart TD` for linear processes, `flowchart LR` for pipelines
- Include decision nodes (`{condition}`) for branching
- Label edges with conditions, data passed, or HTTP methods
- Reference source as comments: `%% src/auth/login.py::handle_request`
- Mark error/failure paths with dotted lines: `-->|error|`
- Keep each diagram under 30 nodes
- For cross-partition flows, use Mermaid `subgraph <partition>` to fence partitions visually
```

## PHASE 4: Semantic Understanding

Document the WHY behind the code:
- Business purpose of each module in the partition
- Design decisions and trade-offs (inferred from code patterns)
- Historical context (from git blame and commit messages within the partition)
- Assumptions embedded in the code
- Implicit contracts not documented anywhere
- Architecture Decision Records (ADRs) — document rejected alternatives and WHY

**Output file:** `<run_dir>/partitions/<partition_name>/04-semantics.md`

```markdown
# Partition: <partition_name> — Semantic Understanding

## Module Purposes
[WHY each module in this partition exists.]

## Design Decisions
[Inferred decisions and their trade-offs, scoped to this partition.]

## Architecture Decision Records
[Each ADR:]
- **Decision:** [What was chosen]
- **Context:** [What problem it solves]
- **Alternatives rejected:** [What was NOT chosen and WHY]
- **Consequences:** [Trade-offs accepted]

ADRs that depend on cross-partition behavior (e.g. "API never calls DB directly, talks to worker via queue") belong here ONLY if the partition is one of the actors. The synthesizer will lift them to a global section.

## Embedded Assumptions
[Assumptions the code makes that aren't documented. Mark cross-partition assumptions explicitly.]

## Hidden Contracts
[Implicit agreements between modules. Mark cross-partition contracts as `<this-partition> ↔ <other-partition>`.]

## Conventions Observed
- Error handling: <pattern>
- Logging: <pattern>
- Configuration: <pattern>
```

## COMPLETION

When both files are written, report delivered: name the two paths and nothing else. If you could not write them, report failed with the reason.
