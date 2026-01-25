# Example: Good .claude.md File

This is an example of a well-structured `.claude.md` file following best practices.

## Key Characteristics

- **Concise**: 87 lines (under 300 target)
- **Grounded**: All claims verifiable in codebase
- **Progressive disclosure**: References docs instead of embedding
- **Pointers not copies**: References files, doesn't duplicate code
- **Universal applicability**: Only always-relevant guidance

---

```markdown
# Project Context

This is a React 18 + TypeScript web application for task management.

**Tech Stack:**
- React 18.2 with functional components + hooks (see `package.json:12-13`)
- TypeScript 5.3 (see `tsconfig.json`)
- Vite 5.x for build tooling (see `vite.config.ts`)
- Zustand for state management (see `src/store/`)
- React Query for data fetching (see `src/hooks/useApi.ts`)
- Tailwind CSS for styling (see `tailwind.config.js`)

## Project Structure

```
src/
├── components/     # React components (functional + hooks pattern)
├── hooks/          # Custom hooks (ALWAYS follow patterns here)
├── store/          # Zustand state slices
├── api/            # API client and endpoints
├── types/          # TypeScript type definitions
└── utils/          # Shared utilities
```

See `docs/architecture.md` for detailed architecture decisions.

## Development Workflow

**Start dev server:**
```bash
npm run dev
```

**Run tests:**
```bash
npm test              # Unit tests with Vitest
npm run test:e2e      # E2E tests with Playwright
```

**Linting/Formatting:**
We use Biome for linting and formatting (see `biome.json`).
DO NOT suggest code style changes - Biome handles this automatically.

**Before committing:**
Pre-commit hooks run Biome and type checking automatically.

## Important Patterns

**Custom Hooks:**
- ALWAYS follow patterns in `src/hooks/` directory
- Use React Query for all data fetching
- Example: `useApi.ts`, `useAuth.ts`

**State Management:**
- Use Zustand slices (see `src/store/`)
- Keep state minimal and derived
- Example: `src/store/tasks.ts`

**Component Patterns:**
- Functional components only
- Props interface in same file
- Extract complex logic to custom hooks

**API Conventions:**
- All API calls through React Query hooks
- Error handling via error boundaries
- Loading states via query.isLoading

## Testing

**Unit tests:** Vitest for components and utilities
**E2E tests:** Playwright for user flows
**Coverage:** Target 80%+ (run `npm run coverage`)

See `docs/testing-guide.md` for detailed testing patterns.

## Deployment

CI/CD via GitHub Actions (see `.github/workflows/`)
Deploys to Vercel automatically on merge to main.

See `docs/deployment.md` for environment variables and configuration.

## Common Tasks

**Add new feature:**
1. Create component in `src/components/`
2. Add state slice in `src/store/` if needed
3. Add API hook in `src/hooks/` if data fetching required
4. Add tests
5. Update types in `src/types/`

**Add new API endpoint:**
1. Add to `src/api/endpoints.ts`
2. Create React Query hook in `src/hooks/`
3. Add TypeScript types
4. Add tests

## Key Principles

- **TypeScript strict mode enabled** - Fix type errors, don't use `any`
- **Accessibility matters** - Use semantic HTML, ARIA when needed
- **Performance conscious** - Lazy load routes, memoize expensive ops
- **Error boundaries** - Wrap risky components
- **Loading states** - Show feedback for async operations

## Additional Resources

- Architecture decisions: `docs/architecture.md`
- API patterns: `docs/api-patterns.md`
- Component guidelines: `docs/components.md`
- Testing guide: `docs/testing-guide.md`
- Deployment guide: `docs/deployment.md`
```

## Why This Works

### ✅ Best Practices Applied

1. **Concise (87 lines)**
   - Under 300 line target
   - No unnecessary verbosity
   - Progressive disclosure to docs/

2. **Grounded in Reality**
   - "React 18.2" → verifiable in package.json:12-13
   - "Vite 5.x" → verifiable in vite.config.ts
   - "Zustand" → verifiable in src/store/
   - File paths reference actual locations

3. **Progressive Disclosure**
   - "See `docs/architecture.md`" instead of embedding architecture
   - "See `docs/testing-guide.md`" instead of full testing docs
   - References actual files: `src/hooks/useApi.ts`

4. **Pointers Not Copies**
   - "ALWAYS follow patterns in `src/hooks/`" → points to code
   - "Use patterns in `src/store/tasks.ts`" → example reference
   - Doesn't duplicate code snippets that will go stale

5. **Delegates to Tools**
   - "DO NOT suggest code style changes - Biome handles this"
   - Doesn't embed linting rules in .claude.md
   - Lets pre-commit hooks enforce standards

6. **Universal Applicability**
   - Custom hooks pattern: always relevant
   - API conventions: always relevant
   - Component patterns: always relevant
   - Doesn't include task-specific details

7. **WHAT/WHY/HOW Structure**
   - WHAT: Tech stack, structure
   - WHY: Project purpose (task management app)
   - HOW: Development workflow, testing, deployment

### ❌ Anti-Patterns Avoided

- No code duplication from README
- No embedded type definitions
- No detailed formatting rules (delegates to Biome)
- No vague guidance ("write clean code")
- No invented features
- No outdated dependencies
- No over-instruction

### 📊 Metrics

- **Lines:** 87 (target: <300, ideal: <100) ✅
- **Instructions:** ~40-50 (leaves room in ~150-200 budget) ✅
- **File references:** All verified to exist ✅
- **Commands:** All verified in package.json ✅
- **Progressive disclosure:** 5 doc references ✅
- **Code duplication:** None ✅

## Contrast: Bad .claude.md Example

Here's what NOT to do:

```markdown
# Bad Example (450 lines)

## Code Style

- Use 2 spaces for indentation
- Single quotes for strings
- Semicolons required
- Max line length 80
- [... 100 more lines of style rules that Biome should handle ...]

## Component Template

```tsx
// Copy this template for every component
import React from 'react';

interface Props {
  // ...
}

export const Component: React.FC<Props> = ({ ... }) => {
  return <div>...</div>;
};
```
[PROBLEM: Code will go stale, use file reference instead]

## API Endpoints

POST /api/users
GET /api/users/:id
PUT /api/users/:id
DELETE /api/users/:id
[... 50 more lines duplicating what's in OpenAPI spec ...]

## File Structure

src/utils/helpers.ts contains utility functions
[PROBLEM: File was moved to src/lib/helpers.ts months ago]

## Testing

We plan to use Jest for testing
[PROBLEM: "Plan to" - not implemented yet, don't document]
```

**Problems:**
- 450 lines (way over 300)
- Style rules duplicate Biome config
- Code templates that go stale
- Duplicates OpenAPI spec
- Obsolete file reference (utils → lib)
- Documents unimplemented features
- Over-instruction (>200 directives)

## Verification Checklist

Before accepting a .claude.md, verify:

- [ ] Under 300 lines (ideally <100)
- [ ] All file paths exist
- [ ] All commands work
- [ ] All dependencies are accurate
- [ ] No code duplication
- [ ] No style policing
- [ ] Uses progressive disclosure
- [ ] References actual files
- [ ] No invented features
- [ ] Delegates formatting to tools
