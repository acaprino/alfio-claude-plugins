# AI-Powered Code Analysis Methodology

> This document defines how Claude should semantically analyze source code beyond mechanical AST extraction.

---

## Core Principle: Understanding Over Extraction

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         THE SEMANTIC ANALYSIS MANDATE                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Scripts extract STRUCTURE:  "This file has class Foo with method bar()"    ║
║  Claude extracts MEANING:    "Foo implements the Repository pattern for     ║
║                               caching user sessions with TTL expiration"    ║
║                                                                              ║
║  NEVER stop at structure. ALWAYS pursue understanding.                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## The Five Layers of Code Understanding

### Layer 1: WHAT (Structural) - Scripts handle this
- Classes, functions, imports
- Line counts, dependencies
- AST-extractable information

### Layer 2: HOW (Mechanical) - Claude's first pass
- Algorithm implementation details
- Data flow through functions
- State transformations

### Layer 3: WHY (Intent) - Claude's deep analysis
- Business purpose of the code
- Problem being solved
- Design decisions made

### Layer 4: WHEN (Temporal) - Claude's behavioral analysis
- Execution conditions and triggers
- Lifecycle and state transitions
- Concurrency and timing

### Layer 5: CONSEQUENCES (Impact) - Claude's systems thinking
- Side effects and mutations
- Downstream dependencies
- Failure modes and edge cases

---

## Semantic Analysis Questions

When analyzing ANY code unit, Claude must answer these questions:

### Identity Questions
```
□ What is this code's single responsibility?
□ What abstraction does it represent?
□ What would break if this code didn't exist?
```

### Behavior Questions
```
□ What are ALL possible inputs?
□ What are ALL possible outputs (including side effects)?
□ What state does it read? What state does it mutate?
□ What are the preconditions for correct operation?
□ What are the postconditions guaranteed after execution?
```

### Integration Questions
```
□ Who calls this code? Under what circumstances?
□ What does this code call? Why those specific dependencies?
□ What contracts/interfaces does it fulfill?
□ What would need to change if this code's signature changed?
```

### Quality Questions
```
□ What could go wrong? How is failure handled?
□ Are there implicit assumptions that could break?
□ Is there hidden coupling to global state or external systems?
□ Are there race conditions or timing dependencies?
```

---

## Analysis Patterns by Code Type

### Pattern: Service/Manager Class
```
RECOGNIZE BY:
- Name ends in Service, Manager, Handler, Controller
- Has multiple public methods
- Coordinates between other components

ANALYZE FOR:
1. What domain concept does this service own?
2. What operations does it expose? (CRUD? Commands? Queries?)
3. What resources does it manage? (connections, state, caches)
4. What is the lifecycle? (singleton? per-request? pooled?)
5. What are the thread-safety guarantees?

DOCUMENT:
- Primary responsibility (one sentence)
- Key operations with preconditions
- Resource management strategy
- Error handling approach
- Integration points
```

### Pattern: Data Model/Entity
```
RECOGNIZE BY:
- Name is a noun (User, Order, Transaction)
- Primarily contains fields/attributes
- May have validation logic

ANALYZE FOR:
1. What real-world concept does this represent?
2. What are the invariants? (fields that must always be valid)
3. What are the valid state transitions?
4. What is the identity? (which fields make it unique)
5. What are the relationships to other entities?

DOCUMENT:
- Domain meaning
- Field semantics (not just types)
- Validation rules
- State machine (if applicable)
- Relationship cardinality
```

### Pattern: Algorithm/Processor
```
RECOGNIZE BY:
- Name contains process, calculate, compute, transform
- Takes input, produces output
- May be stateless

ANALYZE FOR:
1. What transformation does this perform?
2. What is the algorithmic complexity? (time/space)
3. What are the edge cases?
4. Are there numerical stability concerns?
5. Is it deterministic?

DOCUMENT:
- Input → Output transformation description
- Algorithm explanation (for non-trivial cases)
- Complexity analysis
- Edge case handling
- Example inputs and outputs
```

### Pattern: Adapter/Integration
```
RECOGNIZE BY:
- Name contains Adapter, Client, Gateway, Connector
- Wraps external system
- Handles serialization/deserialization

ANALYZE FOR:
1. What external system does this wrap?
2. What is the retry/resilience strategy?
3. How are credentials managed?
4. What is the connection lifecycle?
5. How are errors from the external system translated?

DOCUMENT:
- External system and protocol
- Authentication mechanism
- Retry and timeout configuration
- Error mapping strategy
- Connection pooling details
```

### Pattern: Event Handler/Callback
```
RECOGNIZE BY:
- Name contains on_, handle_, process_
- Takes event/message as parameter
- Often async

ANALYZE FOR:
1. What event triggers this handler?
2. What is the expected event frequency?
3. What happens if handling fails?
4. Is ordering guaranteed?
5. Is idempotency required/implemented?

DOCUMENT:
- Triggering event/condition
- Expected behavior
- Failure handling
- Ordering and idempotency guarantees
- Side effects produced
```

### Pattern: Factory/Builder
```
RECOGNIZE BY:
- Name contains Factory, Builder, Creator
- Returns instances of other classes
- May have configuration methods

ANALYZE FOR:
1. What does this create?
2. Why is direct construction not used?
3. What configuration options exist?
4. Are created objects cached or always new?
5. What validation happens during creation?

DOCUMENT:
- What is being created and why factory pattern
- Configuration options and defaults
- Lifecycle of created objects
- Validation performed
```

### Pattern: State Machine
```
RECOGNIZE BY:
- Enum of states
- Transition methods
- State-dependent behavior

ANALYZE FOR:
1. What are ALL valid states?
2. What are ALL valid transitions?
3. What triggers each transition?
4. What side effects occur on transition?
5. What is the terminal state(s)?

DOCUMENT:
- State diagram (Mermaid)
- Transition table with triggers
- Side effects per transition
- Error/recovery states
```

---

## Flow Tracing Methodology

When tracing a flow through the system:

### Step 1: Identify Entry Point
```
□ Where does this flow begin? (API endpoint, message handler, timer, etc.)
□ What triggers it? (user action, external event, scheduled task)
□ What data enters at this point?
```

### Step 2: Trace Data Transformations
```
□ How is input data validated?
□ What transformations occur?
□ Where is data enriched with additional information?
□ Where is data persisted?
```

### Step 3: Identify Decision Points
```
□ Where are conditional branches?
□ What determines which branch is taken?
□ Are there early returns or short-circuits?
```

### Step 4: Map Side Effects
```
□ What external systems are called?
□ What state is mutated?
□ What events are emitted?
□ What logs are produced?
```

### Step 5: Document Exit Points
```
□ What are the success outcomes?
□ What are the failure outcomes?
□ What cleanup occurs?
```

---

## Red Flags to Identify

Claude should actively look for and document these issues:

### Architecture Red Flags
```
⚠ GOD CLASS: Class with >10 public methods or >500 LOC
⚠ FEATURE ENVY: Method that uses more of another class than its own
⚠ SHOTGUN SURGERY: Change requires touching many files
⚠ CIRCULAR DEPENDENCY: A → B → C → A
⚠ LEAKY ABSTRACTION: Implementation details exposed in interface
```

### Reliability Red Flags
```
⚠ SWALLOWED EXCEPTION: except: pass or empty catch blocks
⚠ MISSING TIMEOUT: Network/IO calls without timeout
⚠ UNBOUNDED GROWTH: Collections that grow without limit
⚠ RACE CONDITION: Shared mutable state without synchronization
⚠ RESOURCE LEAK: Opened resources not closed
```

### Security Red Flags
```
⚠ HARDCODED SECRET: Passwords, API keys in code
⚠ SQL INJECTION: String concatenation in queries
⚠ MISSING VALIDATION: User input used without sanitization
⚠ OVERLY PERMISSIVE: Catch-all permissions or access
⚠ SENSITIVE LOGGING: Passwords, tokens in log output
```

### Maintainability Red Flags
```
⚠ MAGIC NUMBER: Unexplained numeric constants
⚠ DEAD CODE: Unreachable or unused code
⚠ COPY-PASTE: Duplicated logic blocks
⚠ DEEP NESTING: >4 levels of indentation
⚠ LONG METHOD: >50 lines without clear sections
```

---

## Documentation Output Standards

### For Each Code Unit, Produce:

```markdown
## {ClassName/FunctionName}

**Purpose:** {One sentence explaining WHY this exists}

**Responsibility:** {What this code OWNS in the system}

### Behavior

{Description of what this code DOES, not HOW it does it}

### Inputs
| Parameter | Type | Semantic Meaning | Constraints |
|-----------|------|------------------|-------------|
| ... | ... | ... | ... |

### Outputs
| Return/Effect | Type | Semantic Meaning | Conditions |
|---------------|------|------------------|------------|
| ... | ... | ... | ... |

### Dependencies
- **{Dependency}**: {WHY this dependency is needed}

### State Changes
- {What state is mutated and why}

### Error Conditions
| Condition | Behavior | Recovery |
|-----------|----------|----------|
| ... | ... | ... |

### Usage Example
```python
# Concrete example showing typical usage
```

### Notes
- {Any non-obvious insights, edge cases, or gotchas}
```

---

## Incremental Understanding Protocol

As analysis progresses through the codebase:

### Build Mental Model
```
1. Start with entry points (main, API handlers, event listeners)
2. Trace primary flows to understand core behavior
3. Map shared utilities and how they're used
4. Identify cross-cutting concerns (logging, auth, error handling)
5. Document architectural patterns in use
```

### Cross-Reference Continuously
```
1. When analyzing File B, reference findings from File A
2. Update earlier documentation when new insights emerge
3. Build glossary of domain terms as they appear
4. Map acronyms and abbreviations to full meanings
```

### Validate Understanding
```
1. After analyzing a subsystem, summarize it in one paragraph
2. Predict what a function does before reading it (from name/context)
3. If prediction is wrong, document the surprising behavior
4. Look for inconsistencies between similar components
```

---

## Integration with Scripts

The mechanical scripts support AI analysis:

| Script | Provides | Claude Adds |
|--------|----------|-------------|
| `classifier.py` | Complexity metrics | Semantic complexity assessment |
| `ast_parser.py` | Structure extraction | Behavioral understanding |
| `usage_finder.py` | Where symbols are used | Why they're used there |
| `doc_review.py` | Documentation health | Documentation accuracy |

**Workflow:**
1. Run scripts to get structural overview
2. Use Claude to analyze semantics
3. Cross-reference script output with Claude insights
4. Produce final documentation combining both

---

*This methodology transforms code analysis from mechanical extraction to genuine understanding.*
