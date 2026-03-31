# Clean Code Plugin

> Rewrite source code to be more readable and human-friendly without changing behavior. Improves naming, removes AI boilerplate, simplifies structure, and adds clarity comments -- with mandatory validation before and after.

## Agents

### `clean-code-agent`

Rewrites source code for readability and maintainability with zero behavior changes.

| | |
|---|---|
| **Model** | `opus` |
| **Tools** | `Read, Edit, Write, Glob, Grep, Bash, Task` |
| **Use for** | Code cleanup, naming improvements, removing AI-generated boilerplate, simplifying structure |

**Invocation:**
```
Use the clean-code-agent to clean up [file/module]
```

**What it does:**
- Renames vague variables and parameters to domain-meaningful names
- Removes paraphrase comments and empty boilerplate docstrings
- Adds brief why-comments for non-obvious business logic
- Simplifies overly complex expressions and control flow

**Safety rules -- what it must never touch:**
- Error handling (try/catch, try/except, error callbacks)
- Validations and type-checks (guard clauses, assertions)
- Import statements (may have side effects)
- Top-level declaration order
- Test files (unless renaming symbols it renamed in source)

---

## Commands

### `/clean-code`

Rewrite source code for readability with validation checkpoints.

```
/clean-code src/utils.py
/clean-code src/ --dry-run
/clean-code src/ --yes --strict
```

| Flag | Effect |
|------|--------|
| `--dry-run` | Preview changes without modifying files |
| `--yes` | Skip confirmation prompts at Steps 2 and 3 |
| `--strict` | Stricter cleanup rules |
| `--force` | Proceed even without tests or type checker |

**Pipeline:** Identify target -> Establish validation baseline -> (Checkpoint) -> Clean code -> Validate no regressions

---

**Related:** [agent-teams](agent-teams.md) (`/team-feature` can include clean-code as a final step) | [senior-review](senior-review.md) (code review before cleaning)
