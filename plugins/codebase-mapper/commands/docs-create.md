---
description: >
  Create accurate technical documentation by analyzing the codebase first -- API docs, architecture guides, component docs, or full project documentation.
  TRIGGER WHEN: the user asks to create API docs, architecture guides, component docs, or new technical documentation for a codebase.
  DO NOT TRIGGER WHEN: the user wants to audit existing docs (use /codebase-mapper:docs-maintain) or just a README (use /docs:maintain-readme).
argument-hint: "<target path or description> [--api-only] [--architecture] [--format markdown|html] [--output <path>]"
---

# Create Documentation

## CRITICAL RULES

1. **Analyze code before writing.** Read the actual source code first. Never write documentation based on assumptions.
2. **Bottom-up approach.** Start from code structure, then build documentation that reflects reality.
3. **Confirm scope with user.** Present what will be documented before generating.
4. **Never enter plan mode.** Execute immediately.

## Step 1: Analyze Target

Determine what to document from `$ARGUMENTS`:

- If a file/directory path: scan the code structure
- If a class/module name: find it in the codebase
- If no target: scan the entire project

```bash
# Discover project structure
find [target] -type f \( -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.rs" -o -name "*.go" -o -name "*.java" \) | head -50
```

Identify:
- **Language & framework** (from package.json, Cargo.toml, pyproject.toml, etc.)
- **Key modules** (entry points, API routes, core business logic)
- **Existing docs** (README, docstrings, JSDoc, rustdoc, etc.)
- **Public API surface** (exports, endpoints, CLI commands)

## Step 2: Confirm Documentation Plan

Present the plan and ask for approval:

```
Documentation plan for: [target]

Language: [detected]
Framework: [detected]

Files to document:
- [file1] -- [type: API endpoint / class / module / utility]
- [file2] -- [type]
- ...

Documentation type:
- [ ] API reference (endpoints, parameters, responses)
- [ ] Architecture guide (system design, component relationships)
- [ ] Component documentation (individual module docs)
- [ ] Full project documentation (all of the above)

Output: [format] at [output path]

1. Proceed with this plan
2. Adjust scope -- I'll tell you what to change
3. Cancel
```

Use AskUserQuestion. Do NOT proceed until the user confirms.

## Step 3: Generate Documentation

Use the `documentation-engineer` agent for the heavy lifting:

```
Task:
  subagent_type: "codebase-mapper:documentation-engineer"
  description: "Generate documentation for [target]"
  prompt: |
    Create accurate technical documentation by analyzing the source code.

    ## Target
    [Insert path and description]

    ## Source Code
    [Insert contents of key files -- the agent needs to see the actual code]

    ## Documentation Type
    [API reference / Architecture / Component / Full -- from user's choice]

    ## Instructions
    Analyze the code bottom-up and generate documentation that includes:

    For API Reference (--api-only):
    - Every endpoint with method, path, parameters, request/response schemas
    - Authentication requirements
    - Error responses with status codes
    - Example requests/responses

    For Architecture (--architecture):
    - System overview with component diagram (Mermaid)
    - Component responsibilities and boundaries
    - Data flow between components
    - Key design decisions and trade-offs

    For Component Documentation:
    - Module purpose and responsibility
    - Public API (functions, classes, methods) with signatures and descriptions
    - Usage examples
    - Dependencies and relationships

    For Full Project Documentation:
    - All of the above, organized with table of contents
    - Getting started guide
    - Development workflow

    CRITICAL: Every claim must come from reading the actual code. Do not guess or assume.
    If something is unclear from the code, say so rather than inventing documentation.

    Write the documentation as a structured markdown document.
```

## Step 4: AI Trace Removal

Before saving, pass the generated documentation through the `text-humanizer` agent to remove AI writing traces (inflated significance, AI vocabulary, filler phrases, promotional language, etc.).

```
Task:
  subagent_type: "digital-marketing:text-humanizer"
  description: "Remove AI writing traces from generated documentation (use codebase-mapper:doc-humanizer or digital-marketing:text-humanizer)"
  prompt: |
    Humanize this technical documentation. Remove AI patterns while preserving
    all factual content, code examples, and technical accuracy. Focus on:
    - Removing AI vocabulary and filler phrases
    - Breaking formulaic structures
    - Making prose sound natural and direct
    - Keeping code blocks and diagrams unchanged

    Do NOT add the self-evaluation pass -- just return the cleaned text.

    Documentation:
    [generated documentation]
```

## Step 5: Review & Write Output

Present a brief summary of the generated documentation:

```
Documentation generated:

- Sections: [count]
- API endpoints documented: [count] (if applicable)
- Components documented: [count]
- Architecture diagrams: [count]
- Total length: ~[X] lines
- AI trace removal: applied

1. Write to [output path] -- save the documentation
2. Show full preview -- display before saving
3. Revise -- adjust content or scope
```

Write the documentation to the specified output path (default: `docs/` directory).

If the output directory doesn't exist, create it.

## Quick Examples

- `/docs-create src/api` -- Document all API endpoints in src/api
- `/docs-create UserService` -- Document the UserService class
- `/docs-create --architecture` -- Generate architecture documentation for the project
- `/docs-create src/utils --api-only` -- Document only public exports from utils
- `/docs-create src/ --output docs/technical.md` -- Full docs to a specific file
