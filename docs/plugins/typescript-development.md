# TypeScript Development Plugin

> Build production TypeScript with a hands-on engineer agent plus deep standards and mastery skills. Covers architecture + implementation, Knip dead code detection, Metabase coding patterns, and enterprise-grade TypeScript with type-safe patterns, modern tooling, and framework integration.

## Agents

### `typescript-engineer`

Hands-on TypeScript 5.x engineer. Designs architecture AND writes production code using modern tooling (pnpm/bun, Vite/tsup, Vitest, ESLint 9 flat config, Zod/Valibot). Type-safe, strict-mode, well-tested. Parallel to `python-engineer`.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Planning new TypeScript projects, designing architecture, making tech-stack decisions, implementing TS features, migrating JavaScript to TypeScript, setting up monorepos |

**Invocation:**
```
Use the typescript-engineer agent to [design/implement/migrate] [feature]
```

**Expertise:**
- Language: TS 5.10+ (const type parameters, `using` / `await using`, `satisfies`, template-literal types, discriminated unions, conditional/mapped types)
- Tooling: pnpm / bun, Vite / tsup / rollup, Vitest / Jest, ESLint 9 flat config, Biome, oxlint
- Web: Fastify / Hono / Nest 10+, React 19 SSR + RSC, tRPC for end-to-end type safety
- Data: Zod / Valibot runtime validation, Drizzle ORM / Prisma, SQLite / PostgreSQL, Redis
- Monorepo: Turborepo / Nx, pnpm workspaces, shared TS config via `tsconfig-base`
- Infra: Docker multi-stage (oven/bun or node:22-alpine), ESBuild-based production builds

**Conventions:** strict mode only (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`), no `any` without comment, runtime validation at boundaries, `satisfies` over annotation where inference wins, discriminated unions with exhaustive `switch` + `never` assertion, Result<T, E> pattern at module boundaries.

---

## Skills

### `typescript-write`

Write TypeScript and JavaScript following Metabase coding standards and best practices.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | TypeScript/JavaScript development, code refactoring, coding standards |

### `knip`

Find unused files, dependencies, exports, and types in JavaScript/TypeScript projects with Knip. Plugin system covers frameworks (React, Next.js, Vite), test runners (Vitest, Jest), and build tools.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Dead code detection, unused dependency cleanup, bundle size optimization, CI dependency hygiene |

### `mastering-typescript`

Master enterprise-grade TypeScript development with type-safe patterns, modern tooling, and framework integration. Upstream-synced from SpillwaveSolutions/mastering-typescript-skill.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | TypeScript 5.9+ development, type system fundamentals (generics, mapped types, conditional types, satisfies operator), enterprise patterns (error handling, Zod validation), React integration, NestJS APIs, LangChain.js AI apps, JavaScript migration, modern toolchain configuration (Vite 7, pnpm, ESLint, Vitest) |

**Reference files:**
| File | Content |
|------|---------|
| type-system.md | Type system fundamentals, utility types, type guards |
| generics.md | Generic patterns, constraints, inference |
| enterprise-patterns.md | Error handling, validation, architecture patterns |
| react-integration.md | Type-safe React components, hooks, state management |
| nestjs-integration.md | NestJS scalable API patterns |
| toolchain.md | Vite 7, pnpm, ESLint, Vitest configuration |

---

**Related:** [senior-review](senior-review.md) (`/code-review --fix` delegates to Knip for TS/JS) | [react-development](react-development.md) (React-specific optimization)
