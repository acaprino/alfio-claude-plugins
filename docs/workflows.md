# Quick Start Workflows

## Feature End-to-End (`/feature-e2e`)

The most complete pipeline -- takes a feature idea from brainstorming through implementation to code review in a single command.

```
/feature-e2e "add user authentication"
```

```mermaid
graph TD
    A["/feature-e2e 'add auth'"] --> B["Phase 1: Brainstorm Design"]
    B --> |"interactive Q&A"| C{{"Checkpoint 1: Approve design?"}}
    C --> D["Phase 2: Write Plan"]
    D --> |"TDD task breakdown"| E{{"Checkpoint 2: Approve plan?"}}
    E --> F["Phase 3: Execute Plan"]
    F --> |"batches of 3 tasks"| G{{"Checkpoint 3: Approve code?"}}
    G --> H["Phase 4: Code Review"]
    H --> H1["Architecture Agent"]
    H --> H2["Security Agent"]
    H --> H3["Pattern Scoring Agent"]
    H1 & H2 & H3 --> I{{"Checkpoint 4: Review findings"}}
    I --> J["Phase 5: Humanize Code"]
    J --> K["Done"]

    style H1 fill:#4a9eff,color:#fff
    style H2 fill:#4a9eff,color:#fff
    style H3 fill:#4a9eff,color:#fff
    style C fill:#f5a623,color:#fff
    style E fill:#f5a623,color:#fff
    style G fill:#f5a623,color:#fff
    style I fill:#f5a623,color:#fff
```

---

## Code Review (`/code-review`)

Auto-detects scope (uncommitted changes, commits, or PR) and fires 4 agents in parallel.

```
/code-review              # auto-detect scope
/code-review 42           # review PR #42
/code-review --auto-comment  # post findings as PR comments
```

```mermaid
graph TD
    A["/code-review"] --> B{"Auto-detect scope"}
    B --> |"uncommitted"| C["Gather diff + context"]
    B --> |"PR number"| C
    B --> |"branch diff"| C
    C --> D["Launch 4 agents in parallel"]
    D --> D1["Architecture Review"]
    D --> D2["Security Audit"]
    D --> D3["Pattern Scoring"]
    D --> D4["Dead Code Detection"]
    D1 & D2 & D3 & D4 --> E["Consolidate findings"]
    E --> F["Confidence-scored review table"]
    F --> |"--auto-comment"| G["Post to PR"]
    F --> H["Output to terminal"]

    style D1 fill:#4a9eff,color:#fff
    style D2 fill:#4a9eff,color:#fff
    style D3 fill:#4a9eff,color:#fff
    style D4 fill:#4a9eff,color:#fff
```

---

## Full Review (`/full-review`)

Deep 6-phase review with progressive parallelization -- each wave builds on prior findings.

```
/full-review src/ --security-focus
```

```mermaid
graph TD
    A["/full-review src/"] --> B["Phase 1: Architecture Review"]
    B --> C["Phase 2: Security & Performance"]
    C --> C1["Security Agent"]
    C --> C2["Performance Agent"]
    C1 & C2 --> D{{"Checkpoint: Approve?"}}
    D --> E["Phase 3: Testing & Docs"]
    E --> E1["Test Coverage Agent"]
    E --> E2["API & Docs Agent"]
    E1 & E2 --> F["Phase 4: Best Practices"]
    F --> F1["Framework Agent"]
    F --> F2["CI/CD Agent"]
    F --> F3["Dead Code Agent"]
    F1 & F2 & F3 --> G["Phase 5: Quality Scoring"]
    G --> |"reads all prior phases"| H["Phase 6: Consolidated Report"]

    style C1 fill:#4a9eff,color:#fff
    style C2 fill:#4a9eff,color:#fff
    style E1 fill:#4a9eff,color:#fff
    style E2 fill:#4a9eff,color:#fff
    style F1 fill:#4a9eff,color:#fff
    style F2 fill:#4a9eff,color:#fff
    style F3 fill:#4a9eff,color:#fff
    style D fill:#f5a623,color:#fff
```

---

## AI-Assisted Planning

Three skills that chain together -- each one feeds into the next with hard gates preventing premature implementation.

```mermaid
graph LR
    A["Brainstorming"] --> |"design doc"| B["Writing Plans"]
    B --> |"task plan"| C["Executing Plans"]

    A1["Explore context"] --> A2["Clarifying Q&A"]
    A2 --> A3["2-3 approaches"]
    A3 --> A4["Write design doc"]

    B1["Read design"] --> B2["Break into tasks"]
    B2 --> B3["5 steps per task: test-first"]
    B3 --> B4["Save plan .md"]

    C1["Load plan"] --> C2["Execute batch of 3"]
    C2 --> C3["Report + wait feedback"]
    C3 --> |"next batch"| C2

    subgraph "1. brainstorming skill"
        A1 --> A2 --> A3 --> A4
    end
    subgraph "2. writing-plans skill"
        B1 --> B2 --> B3 --> B4
    end
    subgraph "3. executing-plans skill"
        C1 --> C2 --> C3
    end

    style A fill:#7c3aed,color:#fff
    style B fill:#7c3aed,color:#fff
    style C fill:#7c3aed,color:#fff
```

---

## Frontend Redesign (`/frontend-redesign`)

Full redesign pipeline from UX audit to polished implementation with parallel final audit.

```
/frontend-redesign src/ --framework react
```

```mermaid
graph TD
    A["/frontend-redesign"] --> B["Phase 1: UX Audit"]
    B --> C["Phase 2: Layout & Grid"]
    C --> D{{"Checkpoint 1: Approve designs?"}}
    D --> E["Phase 3: Implement Designs"]
    E --> F["Phase 4: React Performance"]
    F --> G["Phase 5: UI Polish"]
    G --> H{{"Checkpoint 2: Final approval?"}}
    H --> I["Phase 6: Design Audit"]
    I --> I1["UX Patterns Agent"]
    I --> I2["Layout System Agent"]
    I --> I3["CSS & Visual Agent"]
    I1 & I2 & I3 --> J["Consolidated Report"]

    style I1 fill:#4a9eff,color:#fff
    style I2 fill:#4a9eff,color:#fff
    style I3 fill:#4a9eff,color:#fff
    style D fill:#f5a623,color:#fff
    style H fill:#f5a623,color:#fff
```

---

## Tauri Pipeline (`/tauri-pipeline`)

Desktop app optimization across Rust backend, Tauri IPC, and React frontend layers.

```
/tauri-pipeline             # full pipeline
/tauri-pipeline --rust-only  # backend only
```

```mermaid
graph TD
    A["/tauri-pipeline"] --> B["Phase 1: Rust Backend Review"]
    B --> C["Phase 2: Tauri IPC Optimization"]
    C --> D{{"Checkpoint: Approve backend?"}}
    D --> E["Phase 3: React Performance"]
    E --> F["Phase 4: Layout Composition"]
    F --> G["Phase 5: UI Polish"]
    G --> H["Phase 6: Consolidated Report"]

    style D fill:#f5a623,color:#fff
```

---

## Mobile Intelligence (`/mobile-intel`)

Competitive analysis pipeline -- analyze a competitor Android app and scaffold your own.

```
/mobile-intel com.competitor.app
```

```mermaid
graph TD
    A["/mobile-intel"] --> B["Phase 1: Competitor Analysis"]
    B --> |"ADB screenshots"| C{{"Checkpoint 1: Review analysis?"}}
    C --> D["Phase 2: Brainstorm Features"]
    D --> |"interactive Q&A"| E{{"Checkpoint 2: Approve features?"}}
    E --> F["Phase 3: UX Design"]
    F --> G["Phase 4: Implementation Plan"]
    G --> H{{"Checkpoint 3: Approve plan?"}}
    H --> I["Phase 5: Scaffold Tauri 2 App"]

    style C fill:#f5a623,color:#fff
    style E fill:#f5a623,color:#fff
    style H fill:#f5a623,color:#fff
```

---

## More Workflows

### Python Development
```
1. /python-scaffold FastAPI microservice
2. Implement features with python-pro agent
3. /python-refactor on complex modules
4. Use python-tdd for test coverage
```

### Legacy Code Modernization
```
1. /deep-dive-analysis to understand codebase
2. /python-refactor on legacy modules
3. Use python-tdd to add test coverage
4. /humanize to clean up naming and comments
```

### Tauri App Optimization
```
1. Use tauri-optimizer for IPC and Rust backend
2. Use react-performance-optimizer for React frontend
3. Use ui-layout-designer for page composition
4. Use ui-polisher for animations and polish
```

### CLAUDE.md Maintenance
```
1. /maintain-claude-md for quarterly maintenance
2. Review audit findings
3. Choose: audit-only or apply improvements
4. Or /create-claude-md to start fresh
```

### Optimization & Scheduling with CSP
```
1. Use or-tools-expert agent for constraint programming
2. Model problem with variables, domains, and constraints
3. Enable parallelism and performance optimizations
4. Test on small instances before scaling up
```

**Example problems:** Employee shift scheduling, job shop scheduling, bin packing, vehicle routing, assignment problems with cost minimization.

---

## Diagram Legend

| Symbol | Meaning |
|--------|---------|
| Blue boxes | Parallel agents (run simultaneously) |
| Orange diamonds | Checkpoints (require user approval to proceed) |
| Purple boxes | Skills (knowledge modules with structured workflows) |
