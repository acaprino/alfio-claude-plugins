# Question Patterns for Effective Clarification

This reference provides templates, patterns, and best practices for formulating clarifying questions that are grounded in research and lead to actionable answers.

## Table of Contents

- [Question Construction Principles](#question-construction-principles)
- [AskUserQuestion Tool Format](#askuserquestion-tool-format)
- [Question Templates by Category](#question-templates-by-category)
- [Number of Questions Guidelines](#number-of-questions-guidelines)
- [Option Generation Best Practices](#option-generation-best-practices)
- [Common Pitfalls](#common-pitfalls)

## Question Construction Principles

### Core Principles

1. **Ground in Research**: Every option must come from actual findings
   - Codebase exploration results
   - Documentation references
   - Web search for best practices
   - Git history for patterns

2. **Be Specific**: Avoid generic options
   - Bad: "Use a different approach"
   - Good: "Use JWT tokens with HttpOnly cookies"

3. **Provide Context**: Explain trade-offs in descriptions
   - Why this option exists
   - What it implies
   - When it's appropriate

4. **Stay Focused**: One decision point per question
   - Bad: "Which file and what approach?"
   - Good: "Which file?" (separate question for approach)

5. **Enable Choice**: 2-4 options per question
   - Fewer than 2: Not a choice
   - More than 4: Overwhelming
   - "Other" is always available automatically

### Question Quality Checklist

Before formulating questions, verify:

- [ ] Completed research phase with documented findings
- [ ] Each option based on actual research (not assumptions)
- [ ] Each option is specific and actionable
- [ ] Context/trade-offs included in descriptions
- [ ] Questions are independent (can be answered in any order)
- [ ] Total questions: 1-6 based on complexity

## AskUserQuestion Tool Format

### Complete Tool Structure

```json
{
  "questions": [
    {
      "question": "Clear, specific question ending with ?",
      "header": "Short label (max 12 chars)",
      "multiSelect": false,
      "options": [
        {
          "label": "Concise choice (1-5 words)",
          "description": "Context about this option, trade-offs, implications"
        },
        {
          "label": "Another choice",
          "description": "Why this option, when to use it"
        }
      ]
    }
  ]
}
```

### Field Guidelines

**question:**
- Must end with `?`
- Should be conversational and clear
- Include context from research if helpful
- Examples:
  - "Which authentication approach should we implement?"
  - "Where should the validation logic be added?"
  - "What scope should this refactoring cover?"

**header:**
- Maximum 12 characters (strict limit)
- Acts as visual label/tag in UI
- Should be noun or noun phrase
- Examples:
  - "Auth method" (11 chars)
  - "File target" (11 chars)
  - "Scope" (5 chars)
  - "Approach" (8 chars)

**multiSelect:**
- `false`: User selects exactly one option (default for most cases)
- `true`: User can select multiple options (when choices aren't mutually exclusive)
- Always explicitly specify (don't rely on defaults)

**options:**
- Minimum 2, maximum 4 options
- Each must have `label` and `description`

**label:**
- 1-5 words typically
- Specific and scannable
- Examples:
  - "JWT with refresh tokens"
  - "Session-based auth"
  - "OAuth 2.0 integration"

**description:**
- Explain what this option means
- Include trade-offs or implications
- Provide context for decision-making
- Examples:
  - "Stateless authentication using JWT access tokens (short-lived) and refresh tokens (stored securely). Best for distributed systems."
  - "Server-side session storage using Redis. Simpler but requires sticky sessions or shared session store."

## Question Templates by Category

### Target Identification Questions

**When:** Unclear which file, function, or component to modify

**Template 1: File Selection**
```json
{
  "question": "Which file should be modified?",
  "header": "Target file",
  "multiSelect": false,
  "options": [
    {
      "label": "src/auth/login.ts",
      "description": "Main login handler with authentication logic (currently 245 lines)"
    },
    {
      "label": "src/auth/middleware.ts",
      "description": "Authentication middleware used by all protected routes (89 lines)"
    },
    {
      "label": "src/auth/session.ts",
      "description": "Session management and validation utilities (156 lines)"
    }
  ]
}
```

**Template 2: Function/Method Selection**
```json
{
  "question": "Which function needs the changes?",
  "header": "Function",
  "multiSelect": false,
  "options": [
    {
      "label": "validateUser()",
      "description": "Validates user credentials against database (auth.ts:45)"
    },
    {
      "label": "authenticateToken()",
      "description": "Verifies JWT token signature and expiration (auth.ts:89)"
    },
    {
      "label": "refreshSession()",
      "description": "Extends active session duration (auth.ts:134)"
    }
  ]
}
```

### Approach/Implementation Questions

**When:** Target is clear, but implementation approach is ambiguous

**Template 1: Technical Approach**
```json
{
  "question": "Which authentication approach should we implement?",
  "header": "Auth method",
  "multiSelect": false,
  "options": [
    {
      "label": "JWT with HttpOnly cookies",
      "description": "Store JWT in HttpOnly cookies. Prevents XSS attacks, simpler client-side code. Requires CSRF protection."
    },
    {
      "label": "JWT in Authorization header",
      "description": "Client stores JWT in memory, sends in Bearer token. More flexible for mobile apps, requires client-side token management."
    },
    {
      "label": "Session-based with Redis",
      "description": "Server-side sessions stored in Redis. Traditional approach, easier to invalidate, requires session store infrastructure."
    }
  ]
}
```

### Scope Questions

**When:** Unclear how much work should be done

**Template 1: Feature Scope**
```json
{
  "question": "What scope should this refactoring cover?",
  "header": "Scope",
  "multiSelect": false,
  "options": [
    {
      "label": "Single function only",
      "description": "Refactor just getUserById(). Minimal change, quick to implement and test."
    },
    {
      "label": "Entire UserRepository class",
      "description": "Refactor all user data access methods (8 functions). Consistent patterns across class."
    },
    {
      "label": "All repository classes",
      "description": "Apply pattern to UserRepository, ProductRepository, OrderRepository (3 classes, 24 functions). Codebase-wide consistency."
    }
  ]
}
```

### Configuration Questions

**When:** Implementation requires configuration choices

**Template 1: Library/Tool Selection**
```json
{
  "question": "Which validation library should be used?",
  "header": "Library",
  "multiSelect": false,
  "options": [
    {
      "label": "Zod",
      "description": "TypeScript-first schema validation. Excellent type inference, modern API. Already used in frontend."
    },
    {
      "label": "Joi",
      "description": "Mature validation library. Large ecosystem, extensive documentation. Used by many enterprise projects."
    },
    {
      "label": "class-validator",
      "description": "Decorator-based validation. Works well with TypeORM entities. Already in package.json."
    }
  ]
}
```

## Number of Questions Guidelines

### 1-2 Questions: Simple Clarification

**Use when:**
- Single point of ambiguity
- Binary or ternary choice
- Target identification only

### 3-4 Questions: Moderate Complexity

**Use when:**
- Multiple independent decisions needed
- Approach and scope both unclear
- Configuration plus implementation questions

### 5-6 Questions: Complex Scenarios

**Use when:**
- Major feature with multiple architectural decisions
- Multiple aspects needing clarification
- Configuration, approach, scope, and priority all unclear

**Important:** Only use 5-6 questions when truly necessary. Most scenarios should use 1-4 questions.

## Option Generation Best Practices

### Grounding Options in Research

**Bad (Assumption-Based):**
```json
{
  "label": "Use MongoDB",
  "description": "NoSQL database, good for flexibility"
}
```

**Good (Research-Grounded):**
```json
{
  "label": "Use MongoDB",
  "description": "NoSQL database. Project already uses MongoDB for user data (see db/connection.ts). Consistent with existing stack."
}
```

### Providing Actionable Context

**Bad (Vague):**
```json
{
  "label": "Refactor approach",
  "description": "Better way to organize code"
}
```

**Good (Specific):**
```json
{
  "label": "Extract to service layer",
  "description": "Move business logic from controllers to UserService class. Follows repository pattern already used in OrderService and ProductService."
}
```

### Including Trade-offs

**Bad (One-Sided):**
```json
{
  "label": "Microservices architecture",
  "description": "Modern, scalable approach"
}
```

**Good (Balanced):**
```json
{
  "label": "Microservices architecture",
  "description": "Split into auth-service and user-service. Better scaling and independence, but adds deployment complexity. Team has Docker expertise."
}
```

## Common Pitfalls

### Pitfall 1: Generic Options
Not actionable, no clear guidance. Fix: use specific, research-grounded options.

### Pitfall 2: Too Many Options
Overwhelming, decision paralysis. Fix: narrow to 2-4 most relevant based on research.

### Pitfall 3: Leading Questions
Biased question influences answer. Fix: present options neutrally with balanced trade-offs.

### Pitfall 4: Compound Questions
Mixing multiple decisions, exponential option growth. Fix: separate into independent questions.

### Pitfall 5: Asking Without Research
Not grounded in codebase reality. Fix: always research first, generate options from findings.

## Summary Checklist

Before using AskUserQuestion tool:

- [ ] Completed research phase with documented findings
- [ ] Each option grounded in research (not assumptions)
- [ ] Each option is specific and actionable (not generic)
- [ ] Descriptions include context and trade-offs
- [ ] Questions are focused (one decision per question)
- [ ] Using 1-6 questions based on complexity
- [ ] Each question has 2-4 options
- [ ] header field is <=12 characters
- [ ] multiSelect explicitly set (true/false)
- [ ] question ends with `?`
