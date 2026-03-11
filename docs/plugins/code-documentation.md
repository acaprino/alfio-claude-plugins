# Code Documentation Plugin

> Generate docs that match reality. Analyzes your code bottom-up before writing a single line -- so documentation reflects what the code actually does, not what someone assumed.

## Agents

### `documentation-engineer`

Expert documentation engineer that creates accurate technical documentation by analyzing existing code first. Uses bottom-up analysis to ensure documentation reflects reality.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | API docs, architecture docs, tutorials, documentation management |

**Invocation:**
```
Use the documentation-engineer agent to document [codebase/feature]
```

**Capabilities:**
- Documentation-as-code workflows
- API documentation generation
- Architecture and design docs
- Tutorials and onboarding guides
- Documentation reorganization and compaction

---

## Commands

### `/docs-create`

Analyze code bottom-up and generate accurate documentation -- API reference, architecture guides, or full project docs. Confirms scope before generating.

```
/docs-create src/api/ --api-only
```

---

### `/docs-maintain`

Audit and refactor existing documentation to ensure accuracy and completeness.

```
/docs-maintain docs/
```
