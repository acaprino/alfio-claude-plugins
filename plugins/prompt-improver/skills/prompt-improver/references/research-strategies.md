# Research Strategies for Context Gathering

This reference provides systematic approaches for researching codebase context, best practices, and patterns before formulating clarifying questions.

## Table of Contents

- [Research Planning Framework](#research-planning-framework)
- [Codebase Exploration Strategies](#codebase-exploration-strategies)
- [Documentation Research](#documentation-research)
- [Web Research for Best Practices](#web-research-for-best-practices)
- [Conversation History Mining](#conversation-history-mining)
- [Tool Selection Guide](#tool-selection-guide)
- [Research Execution Patterns](#research-execution-patterns)

## Research Planning Framework

### Phase 1: Identify What's Unclear

Before researching, explicitly identify gaps:

**Target Gap:**
- "Which file/function needs modification?"
- "What component is involved?"

**Approach Gap:**
- "How should this be implemented?"
- "What pattern should be used?"

**Scope Gap:**
- "How much should be changed?"
- "What's included in this request?"

**Context Gap:**
- "What's the current state?"
- "What patterns exist already?"

### Phase 2: Create Research Plan with TodoWrite

Use TodoWrite to create a research plan before executing. This ensures systematic investigation.

**Template:**
```
Research Plan for [Prompt Type]:
1. [What to research] - [Tool/approach]
2. [What to research] - [Tool/approach]
3. [What to research] - [Tool/approach]
```

### Phase 3: Execute Research

Systematically execute each research step, documenting findings.

### Phase 4: Document Findings

Summarize what you learned:
- Key files involved
- Existing patterns found
- Common approaches in the codebase
- Relevant best practices
- Constraints or requirements discovered

## Codebase Exploration Strategies

### Strategy 1: Pattern Discovery (Task/Explore Agent)

**When to use:** Need to understand architecture, find similar implementations, or explore unknown territory

### Strategy 2: Targeted File Search (Glob)

**When to use:** Know what you're looking for (file type, name pattern)

**Common patterns:**
```bash
# Find all authentication-related files
**/*auth*.ts

# Find test files
**/*.test.ts
**/*.spec.ts

# Find configuration files
**/*config*.{json,yaml,yml}
```

### Strategy 3: Content Search (Grep)

**When to use:** Looking for specific code patterns, function calls, or keywords

**Effective searches:**
```bash
# Find authentication implementations
pattern: "authenticate|login|auth"

# Find TODOs and FIXMEs
pattern: "TODO|FIXME|XXX|HACK"

# Find error handling
pattern: "try.*catch|throw new|Error\\("
```

### Strategy 4: Architecture Understanding (Read + Explore)

**When to use:** Need to understand how systems connect

**Approach:**
1. Start with entry points (index.ts, main.ts, app.ts)
2. Read key configuration files (package.json, tsconfig.json)
3. Explore directory structure
4. Read README.md and architecture docs

### Strategy 5: Historical Context (Git Commands)

**When to use:** Understanding evolution, finding related changes

**Useful git commands via Bash:**
```bash
# Recent commits
git log --oneline -20

# Commits affecting specific file
git log --oneline path/to/file

# Search commit messages
git log --grep="authentication" --oneline

# Find when function was added
git log -S "functionName" --oneline
```

## Documentation Research

### Strategy 1: Local Documentation (Read)

**Priority order:**
1. README.md at project root
2. docs/ directory
3. Package-specific READMEs
4. CONTRIBUTING.md
5. Architecture docs

### Strategy 2: Package Documentation (Read + WebFetch)

**When to use:** Understanding third-party library usage

### Strategy 3: Code Comments (Grep)

**When to use:** Finding design decisions, warnings, constraints

**Patterns:**
```bash
# Find important comments
pattern: "NOTE:|WARNING:|IMPORTANT:|FIXME:"

# Find constraint notes
pattern: "must|require|cannot|constraint"
```

## Web Research for Best Practices

### Strategy 1: Current Best Practices (WebSearch)

**When to use:** Need current approaches, recent changes, industry standards

### Strategy 2: Framework Documentation (WebFetch)

**When to use:** Need official guidance for frameworks in use

### Strategy 3: Common Architectures (WebSearch + WebFetch)

**When to use:** Implementing well-known patterns

## Conversation History Mining

### Strategy 1: Recent Context Review

**When to use:** Always (first step in research)

**Check for:**
- Error messages in recent messages
- File names mentioned
- Features discussed
- Decisions made
- Code shown or referenced

### Strategy 2: Topic Tracking

**When to use:** Understanding what user is working on

### Strategy 3: File View Context

**When to use:** User viewing specific file

## Tool Selection Guide

### Choosing the Right Tool

| Tool | When to Use |
|------|-------------|
| Task/Explore Agent | Broad exploration, architecture, similar patterns |
| Glob | Files by name pattern, known file types |
| Grep | Code content, function calls, pattern matching |
| Read | Specific files, documentation, configuration |
| Bash (git) | Historical context, recent changes |
| WebSearch | Current best practices, industry standards |
| WebFetch | Official documentation, API references |

### Multi-Tool Research Patterns

**Pattern 1: Architecture Discovery**
1. Read: package.json (understand stack)
2. Read: README.md (understand project)
3. Task/Explore: Map architecture
4. Glob: Find similar files
5. Read: Representative files

**Pattern 2: Implementation Approach**
1. Grep: Search for existing pattern
2. Read: Example implementation
3. WebSearch: Best practices
4. WebFetch: Official docs
5. Synthesize: Combine findings

**Pattern 3: Bug Investigation**
1. Review: Conversation history for errors
2. Grep: Search for error patterns
3. Bash: Git log for recent changes
4. Read: Affected files
5. Task/Explore: Find related code

## Research Execution Patterns

### Pattern 1: Quick Research (1-2 tools)
**When:** Simple ambiguity, limited scope

### Pattern 2: Moderate Research (3-4 tools)
**When:** Multiple unknowns, need pattern understanding

### Pattern 3: Comprehensive Research (5+ tools)
**When:** Major feature, architectural decision, complex implementation

## Summary Checklist

Before asking questions:

- [ ] Created research plan with TodoWrite
- [ ] Checked conversation history for context
- [ ] Explored codebase for existing patterns
- [ ] Searched for similar implementations
- [ ] Reviewed relevant documentation
- [ ] Researched best practices (if needed)
- [ ] Documented findings
- [ ] Generated specific options from research
- [ ] Verified each option is grounded in findings

**Critical Rules:**
1. NEVER skip research phase
2. ALWAYS ground questions in findings
3. NEVER assume based on general knowledge
4. ALWAYS use conversation history first
5. DOCUMENT research findings before asking
