---
name: typescript-write
description: >
  Write TypeScript and JavaScript code following modern best practices and coding standards. Use
  when writing or reviewing TypeScript/JavaScript code, including types, generics, async patterns,
  module boundaries, and style conventions. Not for React-specific performance work, which the
  react-development bundle covers, Node.js build and packaging, or deep enterprise type-system work,
  which the mastering-typescript skill covers.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: typescript-development
---

# TypeScript/JavaScript Development Skill

## When to Invoke

- Writing new TypeScript or JavaScript files
- Refactoring existing TS/JS code
- Reviewing code for type safety and best practices
- Converting JavaScript to TypeScript
- Designing module APIs and type interfaces
- Fixing type errors or improving type coverage

## Code Style

### Naming Conventions
- `camelCase` for variables, functions, parameters
- `PascalCase` for types, interfaces, classes, enums, React components
- `UPPER_SNAKE_CASE` for constants and enum members
- Prefix interfaces with `I` only if project convention requires it - otherwise plain `PascalCase`
- Boolean variables: use `is`, `has`, `should`, `can` prefixes (`isLoading`, `hasPermission`)
- Event handlers: `handleClick`, `onSubmit` pattern

### File Organization
- One primary export per file when possible
- Group related types with their implementation
- Barrel exports (`index.ts`) for public module APIs only - avoid deep barrel re-exports
- File naming: `kebab-case.ts` for utilities, `PascalCase.tsx` for React components

### Import Ordering
1. Node built-in modules (`node:fs`, `node:path`)
2. External packages (`react`, `lodash`)
3. Internal aliases (`@/utils`, `@/components`)
4. Relative imports (`./helpers`, `../types`)
5. Type-only imports (`import type { Foo }`)
- Blank line between each group

## TypeScript Patterns

### Strict Mode
- Enable `strict: true` in `tsconfig.json` - never disable individual strict checks
- No `// @ts-ignore` or `// @ts-expect-error` without an explanatory comment
- Prefer `unknown` over `any` - narrow with type guards

### Proper Typing
- Avoid `any` - use `unknown` and narrow, or define a proper type
- Prefer `interface` for object shapes that may be extended
- Prefer `type` for unions, intersections, mapped types, and utility types
- Use `readonly` for properties that should not be mutated
- Use `as const` for literal type inference on objects and arrays

### Discriminated Unions
```typescript
type Result<T> =
  | { success: true; data: T }
  | { success: false; error: Error };

function handle<T>(result: Result<T>) {
  if (result.success) {
    // result.data is T here
    return result.data;
  }
  // result.error is Error here
  throw result.error;
}
```

### Type Guards
```typescript
// User-defined type guard
function isString(value: unknown): value is string {
  return typeof value === "string";
}

// Assertion function
function assertDefined<T>(value: T | undefined, name: string): asserts value is T {
  if (value === undefined) {
    throw new Error(`Expected ${name} to be defined`);
  }
}
```

### Generic Constraints
```typescript
// Constrain generics to what you actually need
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// Use defaults for common cases
type ApiResponse<T = unknown> = {
  data: T;
  status: number;
  timestamp: string;
};
```

### Utility Types
- `Partial<T>` - all properties optional (use for update/patch operations)
- `Required<T>` - all properties required
- `Pick<T, K>` - select subset of properties
- `Omit<T, K>` - exclude properties
- `Record<K, V>` - typed key-value map
- `Extract<T, U>` / `Exclude<T, U>` - filter union members
- Prefer built-in utility types over manual type manipulation

### Enums vs Union Types
- Prefer string union types for simple sets: `type Status = "active" | "inactive"`
- Use `const enum` only if you need numeric values and tree-shaking
- Use regular `enum` when you need runtime reverse mapping or iteration

## React Patterns

### Component Typing
```typescript
// Function components - type props inline or with interface
interface ButtonProps {
  label: string;
  variant?: "primary" | "secondary";
  onClick: () => void;
  children?: React.ReactNode;
}

function Button({ label, variant = "primary", onClick, children }: ButtonProps) {
  return <button className={variant} onClick={onClick}>{children ?? label}</button>;
}
```

### Hooks Rules
- Call hooks at the top level only - never inside conditions, loops, or nested functions
- Custom hooks must start with `use` prefix
- Specify dependency arrays accurately - never suppress exhaustive-deps lint
- Use `useCallback` for functions passed as props to memoized children
- Use `useMemo` for expensive computations - not for every variable

### State Management
- Colocate state as close to where it is used as possible
- Lift state up only when siblings need to share it
- Use `useReducer` for complex state with multiple sub-values or transitions
- Context for truly global state (theme, auth, locale) - not for frequently changing data

### Event Handling
```typescript
// Type event handlers properly
function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
  setValue(e.target.value);
}

function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
  e.preventDefault();
  // ...
}
```

## Testing

### File Naming
- Test files: `*.test.ts` or `*.spec.ts` alongside the source file
- Or in `__tests__/` directory mirroring the source structure
- Test utilities: `test-utils.ts` or `testing/` directory

### Test Structure
```typescript
describe("calculateTotal", () => {
  it("returns 0 for empty cart", () => {
    expect(calculateTotal([])).toBe(0);
  });

  it("sums item prices with quantities", () => {
    const items = [
      { price: 10, quantity: 2 },
      { price: 5, quantity: 1 },
    ];
    expect(calculateTotal(items)).toBe(25);
  });

  it("throws for negative quantities", () => {
    expect(() => calculateTotal([{ price: 10, quantity: -1 }])).toThrow();
  });
});
```

### Assertion Patterns
- Use `toBe` for primitives, `toEqual` for objects/arrays
- Use `toThrow` for error cases - wrap in arrow function
- Use `toHaveBeenCalledWith` for spy/mock assertions
- Prefer specific matchers over generic `toBeTruthy`/`toBeFalsy`
- Type test fixtures and mocks - avoid `as any` in tests

### Mocking
- Mock external dependencies, not internal implementation
- Use `vi.fn()` (Vitest) or `jest.fn()` for function mocks
- Use `vi.spyOn` / `jest.spyOn` to mock methods while preserving type safety
- Reset mocks in `beforeEach` or use `afterEach(() => vi.restoreAllMocks())`

## Common Anti-Patterns

### Using `any` Instead of Proper Types
```typescript
// BAD
function parse(data: any) { return data.name; }

// GOOD
function parse(data: unknown): string {
  if (typeof data === "object" && data !== null && "name" in data) {
    return String((data as { name: unknown }).name);
  }
  throw new Error("Invalid data");
}
```

### Non-Null Assertion Overuse
```typescript
// BAD
const name = user!.name!;

// GOOD
if (!user?.name) throw new Error("User name required");
const name = user.name;
```

### Barrel File Performance Issues
```typescript
// BAD - importing everything through deep barrel
import { Button } from "@/components";  // pulls entire component tree

// GOOD - direct import
import { Button } from "@/components/Button";
```

### Ignoring Return Types
```typescript
// BAD - return type inferred as complex union
function getData(id: string) {
  if (!id) return null;
  return fetch(`/api/${id}`).then(r => r.json());
}

// GOOD - explicit return type
async function getData(id: string): Promise<ApiResponse | null> {
  if (!id) return null;
  const r = await fetch(`/api/${id}`);
  return r.json() as Promise<ApiResponse>;
}
```

### Mutating Function Parameters
```typescript
// BAD
function addItem(items: Item[], item: Item) {
  items.push(item);  // mutates input
  return items;
}

// GOOD
function addItem(items: readonly Item[], item: Item): Item[] {
  return [...items, item];
}
```

## Error Handling

### Result Pattern
```typescript
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

async function fetchUser(id: string): Promise<Result<User>> {
  try {
    const res = await fetch(`/api/users/${id}`);
    if (!res.ok) return { ok: false, error: new Error(`HTTP ${res.status}`) };
    const user = await res.json();
    return { ok: true, value: user };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e : new Error(String(e)) };
  }
}
```

### Async Error Handling
- Always `try/catch` around `await` calls that can fail
- Never use `.catch()` and `await` on the same promise chain
- Prefer returning error results over throwing in library code
- Throw only for programmer errors (assertion failures, invariant violations)
- Log errors at the boundary, not at every level

### Error Boundaries (React)
- Wrap major UI sections in error boundaries
- Provide meaningful fallback UI - not blank screens
- Log errors to monitoring service in `componentDidCatch`
- Reset error boundary state on navigation changes

### Typed Errors
```typescript
class NotFoundError extends Error {
  readonly code = "NOT_FOUND" as const;
  constructor(resource: string, id: string) {
    super(`${resource} ${id} not found`);
    this.name = "NotFoundError";
  }
}

class ValidationError extends Error {
  readonly code = "VALIDATION" as const;
  constructor(public readonly fields: Record<string, string>) {
    super("Validation failed");
    this.name = "ValidationError";
  }
}
```
