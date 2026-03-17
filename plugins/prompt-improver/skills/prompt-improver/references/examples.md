# Comprehensive Examples of Prompt Improvement

This reference provides real-world examples showing the complete flow from vague prompts through research, question formulation, and execution.

## Example Format

Each example follows this structure:

1. **Original Prompt**: What the user said
2. **Evaluation**: Clarity assessment
3. **Research Plan** (if vague): What to investigate
4. **Research Findings** (if vague): What was discovered
5. **Questions Asked** (if vague): AskUserQuestion tool call
6. **User Answers** (if vague): What user selected
7. **Execution**: How the request was fulfilled

## Vague Prompts (Research Required)

### Example 1: Generic Bug Fix

**Original Prompt:** "fix the bug"

**Evaluation:**
- Target: no file, function, or bug specified
- Action: what needs fixing?
- Context: Check conversation history

**Research Findings:**
- FIXME in auth.ts:89: "FIXME: Token validation is broken"
- 2 failing tests related to token validation
- Error logging at auth.ts:145 for invalid tokens

**Questions:**
```json
{
  "question": "Which bug should be fixed?",
  "header": "Bug target",
  "multiSelect": false,
  "options": [
    {
      "label": "Token validation (auth.ts:89)",
      "description": "FIXME comment indicates broken token validation. 2 failing tests related to this."
    },
    {
      "label": "Login redirect (recent commit)",
      "description": "Recent commit 2 days ago attempted to fix login redirect. May have residual issues."
    },
    {
      "label": "Invalid token logging (auth.ts:145)",
      "description": "Errors being logged for invalid tokens. May be symptom of validation bug or separate issue."
    }
  ]
}
```

### Example 2: Generic Refactoring Request

**Original Prompt:** "refactor the code to be better"

**Research Findings:**
- users.ts is 450 lines, all logic in one file
- Other APIs (products) use service layer separation
- Current code mixes validation, business logic, data access

**Questions:**
```json
[
  {
    "question": "What aspect of the code should be improved?",
    "header": "Improvement",
    "multiSelect": false,
    "options": [
      {
        "label": "Extract service layer",
        "description": "Create UserService class matching ProductService pattern. Separates concerns and improves testability."
      },
      {
        "label": "Split into multiple files",
        "description": "Break 450-line file into smaller modules. Easier to navigate and maintain."
      },
      {
        "label": "Reduce function complexity",
        "description": "Refactor long functions (updateUser at 89 lines) into smaller, focused functions."
      }
    ]
  }
]
```

### Example 3: Ambiguous Feature Request

**Original Prompt:** "add authentication"

**Research Findings:**
- No existing authentication
- Express.js backend with REST API
- Microservices architecture planned
- Must support mobile app (stateless preferred)

**Questions:**
```json
[
  {
    "question": "Which authentication method should be implemented?",
    "header": "Auth method",
    "multiSelect": false,
    "options": [
      {
        "label": "JWT with refresh tokens",
        "description": "Stateless authentication. Best for microservices and mobile apps."
      },
      {
        "label": "Session-based with MongoDB",
        "description": "Server-side sessions. Simpler to implement, easier to invalidate."
      },
      {
        "label": "OAuth 2.0 integration",
        "description": "Delegate to third-party providers (Google, GitHub)."
      }
    ]
  },
  {
    "question": "What should be included in the authentication scope?",
    "header": "Scope",
    "multiSelect": true,
    "options": [
      {
        "label": "Login/register endpoints",
        "description": "Basic authentication flow."
      },
      {
        "label": "Password reset flow",
        "description": "Forgot password email workflow."
      },
      {
        "label": "Role-based access control",
        "description": "User roles with permission checking."
      }
    ]
  }
]
```

## Clear Prompts (Proceed Immediately)

### Example 4: Specific File and Action

**Prompt:** "Refactor the getUserById function in src/api/users.ts to use async/await instead of promise chains"

**Evaluation:** All criteria pass - specific target, clear action, defined success criteria.

**Decision:** PROCEED IMMEDIATELY (no research or questions)

### Example 5: Specific Bug with Context

**Prompt:** "Fix the TypeError at line 145 in src/auth/login.ts where user.profile.name is undefined"

**Decision:** PROCEED IMMEDIATELY

### Example 6: Clear Feature with Details

**Prompt:** "Add input validation to the registration form using Joi schema. Validate: Email (required, valid format), Password (required, min 8 chars), Username (required, 3-20 chars, alphanumeric)"

**Decision:** PROCEED IMMEDIATELY

## Bypass Prompts (Pass Through)

### Example 7: Asterisk Bypass
**Prompt:** "* just add a quick comment explaining this function"
**Detection:** Bypass prefix `*` detected. Strip and pass through.

### Example 8: Slash Command
**Prompt:** "/commit"
**Detection:** Slash command format detected. Pass through unchanged.

### Example 9: Hash Prefix (Memory)
**Prompt:** "# remember to use TypeScript strict mode for all new files"
**Detection:** Hash prefix `#` detected. Pass through to memory system.

## Context-Dependent Prompts

### Example 10: File Viewing Context Makes Clear
**Context:** User opened src/components/LoginForm.tsx
**Prompt:** "refactor this to use hooks"
**Decision:** PROCEED IMMEDIATELY (file context provides target)

### Example 11: Recent Error Provides Context
**Previous:** "Error: ECONNREFUSED at 127.0.0.1:5432"
**Prompt:** "fix this connection error"
**Decision:** PROCEED IMMEDIATELY (error message provides all details)

### Example 12: Ongoing Discussion Provides Context
**History:** Discussion about Prisma vs TypeORM, user chose Prisma
**Prompt:** "set it up"
**Decision:** PROCEED (conversation context makes this clear)

## Summary: Decision Patterns

### Proceed Immediately If:
- Specific file and function mentioned with clear action
- Error message provides full context
- File viewing context clarifies ambiguous "this"
- Recent conversation establishes clear decisions

### Research and Ask If:
- Generic action verbs without target
- No file or component mentioned
- Multiple valid approaches
- Architectural decisions needed

### Pass Through If:
- Bypass prefix detected (`*`, `/`, `#`)
- User explicitly opted out of evaluation
