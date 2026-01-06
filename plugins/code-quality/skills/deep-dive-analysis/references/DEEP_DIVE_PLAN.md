# Comprehensive Codebase Analysis & Documentation Plan (v3)

## 1. Objective

Systematically analyze every source file in your codebase to:
1. Build a complete mental model of the system
2. Map all interactions, dependencies, and logic flows
3. Produce comprehensive, maintainable documentation
4. Identify architectural risks and improvement opportunities

**Relationship to Existing Documentation:**
- `CONTEXT.md` - High-level architecture overview (keep updated)
- This plan produces **module-level deep dives** that supplement the context file
- Final deliverables link back to CONTEXT.md for navigation

---

## 2. Methodology: "The Inverted Pyramid"

Work **Bottom-Up**: shared primitives → data structures → messaging → business logic → adapters → UI.

### CRITICAL PRINCIPLE: ABSOLUTE SOURCE OF TRUTH

> **THE DOCUMENTATION PRODUCED BY THIS ANALYSIS IS THE ABSOLUTE AND UNQUESTIONABLE SOURCE OF TRUTH FOR YOUR PROJECT.**
>
> **ANY INFORMATION NOT VERIFIED WITH IRREFUTABLE EVIDENCE FROM SOURCE CODE IS FALSE, UNRELIABLE, AND LEADS TO INEVITABLE FAILURE.**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        THE IRON LAW OF DOCUMENTATION                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  DOCUMENTATION = f(SOURCE_CODE) + VERIFICATION                               ║
║                                                                              ║
║  If NOT verified_against_code(statement) → statement is FALSE                ║
║  If NOT exists_in_codebase(reference)    → reference is FABRICATED           ║
║  If NOT traceable_to_source(claim)       → claim is SPECULATION              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Mandatory Rules (VIOLATION = FAILURE):**
1. **NEVER** document anything without reading the actual source code first
2. **NEVER** assume any existing documentation, comment, or docstring is accurate
3. **NEVER** write documentation based on memory, inference, or "what should be"
4. **ALWAYS** derive truth EXCLUSIVELY from reading and tracing actual code
5. **ALWAYS** provide source file + line number for every technical claim
6. **ALWAYS** verify state machines, enums, constants against actual definitions
7. **TREAT** all pre-existing docs as unverified claims requiring validation
8. **MARK** any unverifiable statement as `[UNVERIFIED - REQUIRES CODE CHECK]`

**Why This is Non-Negotiable:**
- Documentation drifts. **Code is the ONLY truth.**
- Starting from existing docs risks propagating lies
- Unverified documentation is worse than no documentation - it creates false confidence
- A single fabricated claim can cascade into catastrophic misunderstanding

**Verification Status Markers (Required on ALL Documentation):**
- `[VERIFIED: file.py:123]` - Confirmed against source code at specific line
- `[VERIFIED: trace_id=xyz]` - Confirmed against runtime logs
- `[UNVERIFIED]` - Awaiting verification, DO NOT TRUST
- `[DEPRECATED]` - Source code has changed, documentation is stale

### CRITICAL PRINCIPLE: NO HISTORICAL DEPTH

> **DOCUMENTATION DESCRIBES ONLY THE CURRENT STATE OF THE ART.**
>
> **NO HISTORY. NO ARCHAEOLOGY. NO "WAS". ONLY "IS".**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                     THE TEMPORAL PURITY PRINCIPLE                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Documentation = PRESENT_TENSE(current_implementation)                       ║
║                                                                              ║
║  FORBIDDEN:                                                                  ║
║  ✗ "was/were/previously/formerly/used to"                                    ║
║  ✗ "deprecated since version X" → just REMOVE it                             ║
║  ✗ "changed from X to Y" → only describe Y                                   ║
║  ✗ "in the old system..." → irrelevant, delete                               ║
║  ✗ inline changelogs → use CHANGELOG.md or git                               ║
║                                                                              ║
║  REQUIRED:                                                                   ║
║  ✓ Present tense: "The system uses..." not "The system used..."              ║
║  ✓ Current state only: Document what IS, not what WAS                        ║
║  ✓ Git for archaeology: History lives in version control, not docs           ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Why This is Non-Negotiable:**
- Historical context in documentation creates cognitive load without actionable value
- "It used to work differently" is noise for someone trying to understand how it works NOW
- Version control exists precisely to preserve history - docs don't need to duplicate it
- Temporal language creates ambiguity: "was changed" - when? by whom? is it still valid?
- Documentation describing past states risks being mistaken for current truth

**The Rule:**
> When you find documentation containing historical language, **DELETE IT**.
> Git blame exists for archaeology. Documentation exists for the present.

### File Classification (Apply Before Analysis)

| Classification | Criteria | Verification Required |
|---------------|----------|----------------------|
| **Critical** | Handles authentication, security, encryption, sensitive data | Mandatory |
| **High-Complexity** | >300 LOC, >5 dependencies, state machines | Mandatory |
| **Standard** | Normal business logic | Recommended |
| **Utility** | Pure functions, helpers | Optional |

### The Analysis Loop (Per File)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CLASSIFY: Determine criticality & complexity             │
├─────────────────────────────────────────────────────────────┤
│ 2. READ & MAP                                               │
│    - Classes, functions, global variables                   │
│    - State mutations and side effects                       │
│    - Error handling patterns                                │
├─────────────────────────────────────────────────────────────┤
│ 3. DEPENDENCY CHECK                                         │
│    - Internal imports (within project)                      │
│    - External imports (third-party)                         │
│    - External calls (database, network, filesystem, etc.)   │
├─────────────────────────────────────────────────────────────┤
│ 4. CONTEXT ANALYSIS                                         │
│    - Where are this file's symbols used?                    │
│    - What calls INTO this file?                             │
│    - What message types flow through here?                  │
├─────────────────────────────────────────────────────────────┤
│ 5. RUNTIME VERIFICATION (if Critical/High-Complexity)       │
│    - Use log analysis to observe actual behavior            │
│    - Trace a real trace_id through this component           │
│    - Compare documented flow vs actual flow                 │
├─────────────────────────────────────────────────────────────┤
│ 6. DOCUMENTATION                                            │
│    - Internal: Verify/add docstrings                        │
│    - External: Add entry to Module Analysis Report          │
│    - Cross-reference: Link to CONTEXT.md sections           │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Progress Tracking

Progress is tracked in `analysis_progress.json` with the following structure:

```json
{
  "metadata": {
    "started": "2024-XX-XX",
    "last_updated": "2024-XX-XX",
    "current_phase": 1
  },
  "files": [
    {
      "path": "src/types/enums.py",
      "phase": 1,
      "status": "pending|analyzing|done|blocked",
      "classification": "standard|critical|high-complexity|utility",
      "verification_required": true,
      "verification_done": false,
      "notes": "",
      "analyzed_at": null
    }
  ],
  "phases": {
    "1": { "name": "Foundation", "progress": "0/15", "status": "in_progress" },
    "2": { "name": "Data Layer", "progress": "0/25", "status": "pending" }
  }
}
```

---

## 4. Execution Phases (Template)

Adapt these phases to your project structure. The key principle is **bottom-up analysis**: start with shared utilities, then move to data models, then messaging/orchestration, then business logic, then adapters, then UI.

### Phase 1: The Foundation (`lib/` or `common/`)
**Goal:** Master the "language" of the system - primitives, contracts, utilities.

| Priority | File/Module | Classification | Notes |
|----------|-------------|----------------|-------|
| 1.1 | `types/enums.py` | Standard | All domain enums |
| 1.2 | `config.py` | High-Complexity | Central config |
| 1.3 | `exceptions.py` | Standard | Error contracts |
| 1.4 | `utils/` | Standard/Critical | Utility functions |

**Deliverable:** `docs/01_foundation/COMMON_LIBRARY.md`

**Cross-Cutting Analysis:**
- Document logging patterns
- Document error handling conventions
- Document ID generation (trace_id, correlation_id)

---

### Phase 2: The Data Layer (`models/` or `entities/`)
**Goal:** Map the data model - all entities, their relationships, and persistence.

| Priority | File/Module | Classification | Notes |
|----------|-------------|----------------|-------|
| 2.1 | `models/` | Critical | All data models |
| 2.2 | `schemas/` | Standard | Validation schemas |
| 2.3 | `db/` or `repositories/` | High-Complexity | Database access |

**Deliverable:** `docs/02_core/DATA_MODELS.md`
- Entity-Relationship Diagram (Mermaid)
- State transition diagrams

---

### Phase 3: The Messaging/Orchestration Layer
**Goal:** Understand orchestration & message routing BEFORE business logic.

| Priority | File/Module | Classification | Notes |
|----------|-------------|----------------|-------|
| 3.1 | `messaging/` or `ipc/` | Critical | Message routing |
| 3.2 | `middleware/` | Critical | Request handling |
| 3.3 | `handlers/` | High-Complexity | Event handlers |

**Deliverable:** `docs/03_infrastructure/MESSAGING.md`

**Runtime Verification (Mandatory):**
- Trace a real request through the system
- Document actual flow vs designed flow

---

### Phase 4: The Business Logic (`services/` or `core/`)
**Goal:** Understand the decision logic and business rules.

| Priority | File/Module | Classification | Notes |
|----------|-------------|----------------|-------|
| 4.1 | `services/` | Critical | Business services |
| 4.2 | `workers/` or `agents/` | Critical | Background processors |

**Deliverable:** `docs/02_core/BUSINESS_LOGIC.md`

---

### Phase 5: The Adapters (`adapters/` or `integrations/`)
**Goal:** Map all external interfaces.

| Priority | File/Module | Classification | Notes |
|----------|-------------|----------------|-------|
| 5.1 | `adapters/` | Critical | External integrations |
| 5.2 | `api/` | High-Complexity | API handlers |

**Deliverable:** `docs/03_infrastructure/ADAPTERS.md`

---

### Phase 6: The User Interface (`frontend/` or `ui/`)
**Goal:** Map user interaction to system commands.

| Priority | File/Module | Classification | Notes |
|----------|-------------|----------------|-------|
| 6.1 | `components/` | Standard | UI components |
| 6.2 | `stores/` or `state/` | High-Complexity | State management |

**Deliverable:** `docs/06_ui/UI_ARCHITECTURE.md`

---

### Phase 7: Infrastructure & Operations
**Goal:** Operational mastery - deployment, monitoring, tooling.

| Priority | File/Module | Classification | Notes |
|----------|-------------|----------------|-------|
| 7.1 | `deployments/` | High-Complexity | Deployment configs |
| 7.2 | `scripts/` or `bin/` | Standard | Utility scripts |

**Deliverable:** `docs/04_operations/OPERATIONAL_MANUAL.md`

---

## 5. Cross-Cutting Concerns (Analyze Throughout)

These patterns span multiple phases - document as encountered:

| Concern | Where to Document | Key Questions |
|---------|-------------------|---------------|
| **Telemetry** | `docs/05_observability/TELEMETRY.md` | How does trace_id propagate? What's logged where? |
| **Error Handling** | `docs/05_observability/ERROR_HANDLING.md` | Exception hierarchy? Retry policies? |
| **Resilience** | `docs/03_infrastructure/RESILIENCE.md` | Circuit breakers? Timeouts? Fallbacks? |
| **Security** | `docs/04_operations/SECURITY.md` | Auth flows? Secret management? |

---

## 6. Verification Checkpoints

After each phase, verify documentation accuracy:

1. **Static Verification:** Code review of documented flows
2. **Runtime Verification:** Use observability tools to trace real requests
3. **Peer Review:** Walk through documentation, identify gaps

**Mandatory Runtime Traces:**
- [ ] Phase 3: Trace a message through the messaging layer
- [ ] Phase 4: Trace a request through business logic services
- [ ] Phase 5: Trace an external API call through adapters
- [ ] Phase 5.5: Trace a REST API request end-to-end

---

## 7. Immediate Next Steps

1. Create `analysis_progress.json` with all files pre-populated
2. Begin **Phase 1: Foundation** (common libraries)
3. Start with `config_loader.py` (high-complexity, affects everything)
4. Document cross-cutting logging/telemetry patterns as encountered

---

---

## 8. Phase 8: Documentation Maintenance & Cleanup

**Goal:** Ensure all documentation under `/docs` is accurate, consistent, and up-to-date with verified source code.

### 8.1 Documentation Review Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DISCOVERY                                                │
│    ├── Scan all .md files under /docs                       │
│    ├── Count files per directory                            │
│    ├── Identify files with TODO/FIXME/TBD markers           │
│    └── Catalog last_updated dates                           │
├─────────────────────────────────────────────────────────────┤
│ 2. LINK VALIDATION                                          │
│    ├── Extract all relative links from each doc             │
│    ├── Verify target files exist                            │
│    ├── Identify broken links to deleted files               │
│    └── Generate broken link report                          │
├─────────────────────────────────────────────────────────────┤
│ 3. SOURCE CODE VERIFICATION                                 │
│    ├── For each technical doc, identify code references     │
│    ├── Verify documented behavior matches actual code       │
│    ├── Flag documentation drift                             │
│    └── Mark as VERIFIED or NEEDS_UPDATE                     │
├─────────────────────────────────────────────────────────────┤
│ 4. MAINTENANCE ACTIONS                                      │
│    ├── Fix broken links (update or remove)                  │
│    ├── Update outdated content                              │
│    ├── Remove obsolete files                                │
│    ├── Merge redundant documentation                        │
│    ├── Split overly large files                             │
│    └── Update navigation indexes                            │
├─────────────────────────────────────────────────────────────┤
│ 5. STATISTICS UPDATE                                        │
│    ├── Update SEARCH_INDEX.md keyword counts                │
│    ├── Update BY_DOMAIN.md file references                  │
│    ├── Update version and last_updated dates                │
│    └── Generate documentation health report                 │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Documentation Categories

| Category | Path Pattern | Review Priority |
|----------|-------------|-----------------|
| **Navigation** | `docs/00_navigation/` | High - user entry points |
| **Domains** | `docs/01_domains/` | Critical - core business logic |
| **Core Systems** | `docs/02_core_systems/` | Critical - technical reference |
| **Infrastructure** | `docs/03_infrastructure/` | High - deployment/messaging |
| **Operations** | `docs/04_operations/` | Medium - operational guides |
| **Development** | `docs/05_development/` | Medium - developer guides |
| **UI** | `docs/06_user_interfaces/` | Medium - UI documentation |
| **ADR** | `docs/02_adr/` | Low - architectural decisions (historical) |
| **Plans** | `docs/plans/` | Low - may contain obsolete plans |

### 8.3 Maintenance Actions

| Action | When to Apply | Execution |
|--------|--------------|-----------|
| **FIX_LINKS** | Broken relative links | Update path or remove reference |
| **UPDATE_CONTENT** | Source code changed | Rewrite section from code analysis |
| **DELETE** | File references deleted code/features | Remove file, update indexes |
| **MERGE** | Multiple files covering same topic | Consolidate into single authoritative doc |
| **SPLIT** | File >1500 lines or covers multiple topics | Create focused sub-documents |
| **UPDATE_STATS** | After any doc changes | Refresh navigation indexes |

### 8.4 Deliverables

1. **doc_health_report.json** - Documentation health metrics
2. **Updated navigation indexes** - SEARCH_INDEX.md, BY_DOMAIN.md refreshed
3. **Clean documentation tree** - No broken links, no obsolete files
4. **Verified timestamps** - All last_updated dates accurate

---

## 9. Success Criteria

The deep dive is complete when:
- [ ] All source files analyzed and documented (Phases 1-7)
- [ ] All mandatory runtime verifications passed
- [ ] CONTEXT.md updated with links to detailed docs
- [ ] No undocumented critical paths remain
- [ ] **Documentation health check passed (Phase 8)**
- [ ] **All broken links fixed**
- [ ] **Navigation indexes up-to-date**
- [ ] **No obsolete documentation files**
- [ ] New contributor can understand system from docs alone
