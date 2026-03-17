<!-- MERGED FROM: docs/workflows.md (Mermaid diagrams) + docs/plugins/workflows.md (command reference) -->
# Workflows Plugin

> Run entire development workflows with one command. Chains brainstorming, planning, implementation, code review, and cleanup into automated pipelines with checkpoints at each stage.
>
> **Dependencies:** [frontend](frontend.md), [react-development](react-development.md), [senior-review](senior-review.md), [humanize](humanize.md), [ai-tooling](ai-tooling.md), [tauri-development](tauri-development.md), [mobile-development](mobile-development.md), [deep-dive-analysis](deep-dive-analysis.md)

## Commands

### `/feature-e2e`

End-to-end feature pipeline: brainstorm design, write implementation plan, execute with TDD checkpoints, review changes (architecture + security + patterns), and humanize code.

| | |
|---|---|
| **Invoke** | `/feature-e2e <feature description> [--skip-brainstorm] [--skip-humanize] [--strict-mode]` |
| **Pipeline** | brainstorming -> writing-plans -> executing-plans -> senior-review -> humanize |
| **Checkpoints** | After design, plan, execution, and review phases |
| **Dependencies** | [ai-tooling](ai-tooling.md), [senior-review](senior-review.md), [humanize](humanize.md) |

```mermaid
graph TD
    A["/feature-e2e 'add auth'"] --> B["Phase 1: Brainstorm Design"]
    B --> |"interactive Q&A"| C{{"Checkpoint 1: Approve design?"}}
    C --> D["Phase 2: Write Plan"]
    D --> |"TDD task breakdown"| E{{"Checkpoint 2: Approve plan?"}}
    E --> F["Phase 3: Execute Plan"]
    F --> |"batches of 3 tasks"| G{{"Checkpoint 3: Approve code?"}}
    G --> H["Phase 4: Code Review"]
    H --> H1["architect-review"]
    H --> H2["security-auditor"]
    H --> H3["pattern-quality-scorer"]
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

### `/frontend-redesign`

Full frontend redesign pipeline: UX audit, layout system design, implementation, React performance optimization, UI polish, and final design audit with visual report. Use this to **improve existing frontend code** -- not to plan or build from scratch.

| | |
|---|---|
| **Invoke** | `/frontend-redesign <target path> [--framework react\|vue\|svelte] [--skip-performance] [--strict-mode]` |
| **Pipeline** | ui-ux-designer -> ui-layout-designer -> frontend-design -> react-performance-optimizer -> ui-polisher -> design audit |
| **Checkpoints** | After layout spec and polish phases |
| **Output** | `.frontend-redesign/report.md` -- actionable checklist with before/after comparison |
| **Dependencies** | [frontend](frontend.md), [react-development](react-development.md) |

> **Not sure which to use?** `/frontend:premium-web-consultant` for strategy ("what to build"), `/frontend:ui-studio` for new builds ("build it from scratch"), `/frontend-redesign` for existing code ("improve what we have").

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
    I --> I1["UX Patterns"]
    I --> I2["Layout System"]
    I --> I3["CSS & Visual"]
    I1 & I2 & I3 --> J["Consolidated Report"]

    style I1 fill:#4a9eff,color:#fff
    style I2 fill:#4a9eff,color:#fff
    style I3 fill:#4a9eff,color:#fff
    style D fill:#f5a623,color:#fff
    style H fill:#f5a623,color:#fff
```

---

### `/code-review`

Auto-detects scope (uncommitted changes, commits, or PR) and fires review agents in parallel.

| | |
|---|---|
| **Invoke** | `/code-review [PR#] [--commits N] [--branch name] [--auto-comment]` |
| **Pipeline** | Detect scope -> Gather diff -> architect-review + security-auditor + pattern-quality-scorer in parallel -> Consolidated report |
| **Dependencies** | [senior-review](senior-review.md) |

```mermaid
graph TD
    A["/code-review"] --> B{"Auto-detect scope"}
    B --> |"uncommitted"| C["Gather diff + context"]
    B --> |"PR number"| C
    B --> |"branch diff"| C
    C --> D["Launch agents in parallel"]
    D --> D1["architect-review"]
    D --> D2["security-auditor"]
    D --> D3["pattern-quality-scorer"]
    D1 & D2 & D3 --> E["Consolidate findings"]
    E --> F["Confidence-scored review table"]

    style D1 fill:#4a9eff,color:#fff
    style D2 fill:#4a9eff,color:#fff
    style D3 fill:#4a9eff,color:#fff
```

---

### `/full-review`

Full codebase review pipeline: deep-dive structural analysis followed by senior multi-agent code review with consolidated scoring.

| | |
|---|---|
| **Invoke** | `/full-review <target path or description> [--skip-deep-dive] [--security-focus] [--performance-critical] [--strict-mode] [--framework react\|spring\|django\|rails]` |
| **Pipeline** | deep-dive-analysis -> architect-review -> security-auditor -> pattern-quality-scorer -> consolidated report |
| **Checkpoints** | After deep-dive and after architecture/security phases |
| **Dependencies** | [deep-dive-analysis](deep-dive-analysis.md), [senior-review](senior-review.md) |

```mermaid
graph TD
    A["/full-review src/"] --> B["Phase 1: Deep-Dive Analysis"]
    B --> C{{"Checkpoint: Approve?"}}
    C --> D["Phase 2: Senior Review (parallel)"]
    D --> D1["architect-review"]
    D --> D2["security-auditor"]
    D --> D3["pattern-quality-scorer"]
    D1 & D2 & D3 --> E{{"Checkpoint: Review findings"}}
    E --> F["Phase 3: Consolidated Report"]

    style D1 fill:#4a9eff,color:#fff
    style D2 fill:#4a9eff,color:#fff
    style D3 fill:#4a9eff,color:#fff
    style C fill:#f5a623,color:#fff
    style E fill:#f5a623,color:#fff
```

---

### `/mobile-intel`

Competitive mobile intelligence: analyze a competitor Android app via ADB, brainstorm differentiating features, design improved UX, write an implementation plan, and scaffold a Tauri 2 mobile app.

| | |
|---|---|
| **Invoke** | `/mobile-intel <app-package-name> [--device <device-id>] [--skip-scaffold]` |
| **Pipeline** | analyze-mobile-app -> brainstorming -> ui-ux-designer -> writing-plans -> tauri2-mobile |
| **Checkpoints** | After analysis, brainstorm, and plan phases |
| **Pre-flight** | Verifies ADB device connection |
| **Dependencies** | [mobile-development](mobile-development.md), [ai-tooling](ai-tooling.md), [frontend](frontend.md), [tauri-development](tauri-development.md) |

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

### `/tauri-pipeline`

End-to-end Tauri 2 desktop app pipeline: Rust backend review, Tauri IPC optimization, React performance, layout composition, and UI polish.

| | |
|---|---|
| **Invoke** | `/tauri-pipeline <target path> [--rust-only] [--frontend-only] [--strict-mode]` |
| **Pipeline** | rust-engineer -> tauri-optimizer -> react-performance-optimizer -> ui-layout-designer -> ui-polisher |
| **Checkpoints** | After Tauri IPC review |
| **Pre-flight** | Verifies `src-tauri/` directory and `tauri.conf.json` exist |
| **Dependencies** | [tauri-development](tauri-development.md), [frontend](frontend.md), [react-development](react-development.md) |

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

### `/mobile-tauri-pipeline`

End-to-end mobile app pipeline: competitor analysis via ADB, feature brainstorm, UX design, implementation plan, Tauri 2 mobile scaffold, Rust backend review, and IPC optimization.

| | |
|---|---|
| **Invoke** | `/mobile-tauri-pipeline <app-package-name or description> [--device <device-id>] [--skip-scaffold] [--skip-review] [--strict-mode]` |
| **Pipeline** | analyze-mobile-app -> brainstorming -> ui-ux-designer -> writing-plans -> tauri2-mobile -> rust-engineer -> tauri-optimizer |
| **Checkpoints** | After analysis, brainstorm, plan, and scaffold phases |
| **Dependencies** | [mobile-development](mobile-development.md), [ai-tooling](ai-tooling.md), [frontend](frontend.md), [tauri-development](tauri-development.md) |

---

### `/ui-studio`

End-to-end UI development pipeline: brainstorm product concept, design direction, layout, UX patterns, write implementation plan, execute with TDD, polish, performance review, and code review.

| | |
|---|---|
| **Invoke** | `/ui-studio <product goal or feature description> [--skip-brainstorm] [--skip-review] [--skip-humanize] [--strict-mode] [--framework react\|vue\|svelte\|html]` |
| **Pipeline** | brainstorming -> ui-ux-designer -> ui-layout-designer -> writing-plans -> executing-plans -> ui-polisher -> react-performance-optimizer -> code-review -> humanize |
| **Checkpoints** | After design, plan, execution, polish, and review phases |
| **Dependencies** | [ai-tooling](ai-tooling.md), [frontend](frontend.md), [react-development](react-development.md), [senior-review](senior-review.md), [humanize](humanize.md) |

---

## Diagram Legend

| Symbol | Meaning |
|--------|---------|
| Blue boxes | Parallel agents (run simultaneously) |
| Orange diamonds | Checkpoints (require your approval to proceed) |

---

**Related:** [senior-review](senior-review.md) (review agents used in pipelines) | [ai-tooling](ai-tooling.md) (brainstorming and planning skills) | [frontend](frontend.md) (UI agents for redesign pipelines)
