# Deep Dive Analysis Plugin

> Understand any codebase in minutes. Seven-phase analysis maps structure, traces flows, identifies risks, and documents the WHY behind the code -- not just what it does.

## Skills

### `deep-dive-analysis`

Systematic codebase analysis that combines structure extraction with semantic understanding.

| | |
|---|---|
| **Invoke** | `/deep-dive-analysis` |
| **Use for** | Codebase understanding, architecture mapping, onboarding |

**Capabilities:**
- Extract code structure (classes, functions, imports)
- Map internal/external dependencies
- Recognize architectural patterns
- Identify anti-patterns and red flags
- Trace data and control flows

---

## Commands

### `/deep-dive-analysis`

7-phase systematic codebase analysis with state management, output files, and phased execution: structure -> interfaces -> flows -> semantics -> risks -> documentation -> report.

```
/deep-dive-analysis src/core/ --critical
```

**Output:** `.deep-dive/` directory with 7 phase files and a final consolidated report.

---

**Related:** [codebase-mapper](codebase-mapper.md) (generates 10 narrative documents from codebase exploration) | [workflows](workflows.md) (`/full-review` uses deep-dive as its first phase) | [senior-review](senior-review.md) (code review agents that run after deep-dive)
