# Humanize Plugin

> Make AI-generated code indistinguishable from human-written code. Fixes vague names, removes boilerplate comments, and adds meaningful documentation -- with mandatory test validation.

## Agents

### `humanize`

Rewrites source code to make it more readable and human-friendly without changing behavior.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Code cleanup, naming improvements, removing AI-generated boilerplate |

**Invocation:**
```
Use the humanize agent to clean up [file/module]
```

**What it does:**
- Renames vague variables and parameters to domain-meaningful names
- Removes paraphrase comments and empty boilerplate docstrings
- Adds brief why-comments for non-obvious business logic

**What it does NOT do:**
- Does not reorder code, extract functions, or change control flow
- Does not remove error handling, validations, or imports
- Does not modify test files (unless renaming symbols it renamed in source)

---

## Commands

### `/humanize`

Quick command to humanize source files.

```
/humanize src/utils.py
```

**Examples:**
| Command | Action |
|---------|--------|
| `/humanize src/utils.py` | Humanize a specific file |
| `/humanize src/` | Humanize all source files in a directory |
| `/humanize src/api/ --dry-run` | Preview changes without modifying files |

---

**Related:** [workflows](workflows.md) (`/feature-e2e` runs humanize as its final phase) | [senior-review](senior-review.md) (code review before humanizing)
