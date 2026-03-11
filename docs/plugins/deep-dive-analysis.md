# Deep Dive Analysis Plugin

> Understand any codebase in minutes. Seven-phase analysis maps structure, traces flows, identifies risks, and documents the WHY behind the code -- not just what it does.

## Skills

### `deep-dive-analysis`

AI-powered systematic codebase analysis combining structure extraction with semantic understanding.

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
