# Testing Plugin

> Language-agnostic testing toolkit - TDD methodology with red-green-refactor loop and behavior-driven test generation for any language.

## Agents

### `test-writer`

Generates focused, behavior-driven test suites or guides interactive TDD sessions. Works with any language and test framework.

| | |
|---|---|
| **Model** | inherit |
| **Use for** | Writing tests for existing code, TDD for new features, test quality review |
| **Modes** | Generate (write complete test suite) or Interactive TDD (guide red-green-refactor cycle) |

**How it works:**

1. Reads the target code and existing tests
2. Identifies behaviors to test (not implementation details)
3. Generates tests following deep-module philosophy - simple interfaces, comprehensive coverage
4. Applies proper mocking boundaries (mock at architectural boundaries, not internals)

---

## Skills

### `tdd`

TDD methodology knowledge base ported from [mattpocock/skills](https://github.com/mattpocock/skills). Activates automatically when writing tests or practicing TDD.

| | |
|---|---|
| **Trigger** | Writing tests, TDD, red-green-refactor, test-driven development |
| **Source** | Upstream-synced with mattpocock/skills |

**Reference docs included:**

| Reference | Content |
|-----------|---------|
| `tests.md` | Test structure, naming, behavioral focus, anti-patterns |
| `deep-modules.md` | Deep module philosophy - simple interfaces hiding complexity |
| `mocking.md` | When and how to mock - architectural boundaries, not internals |
| `interface-design.md` | Designing testable interfaces |
| `refactoring.md` | Safe refactoring patterns with test coverage |

### `e2e-testing-patterns`

End-to-end testing patterns with Playwright and Cypress. Covers test philosophy, page object model, fixtures, waiting strategies, network mocking, visual regression, parallel sharding, and accessibility testing.

| | |
|---|---|
| **Trigger** | Implementing E2E tests, debugging flaky tests, establishing testing standards, setting up Playwright or Cypress |
| **Source** | Upstream-synced with wshobson/agents |

**Patterns covered:**

| Pattern | Framework | Description |
|---------|-----------|-------------|
| Page Object Model | Playwright | Encapsulate page logic in reusable classes |
| Fixtures for Test Data | Playwright | Typed fixtures with setup/teardown |
| Waiting Strategies | Playwright | Auto-waiting assertions, network response waits |
| Network Mocking | Playwright | API mocking, request interception, third-party service stubs |
| Custom Commands | Cypress | Reusable typed commands with `Chainable` |
| Intercept | Cypress | Response mocking, modification, simulated slow network |
| Visual Regression | Playwright | Screenshot comparison with pixel diff thresholds |
| Parallel Sharding | Playwright | Test sharding for CI parallelism |
| Accessibility | Playwright | axe-core integration for WCAG compliance |

---

**Related:** [python-development](python-development.md) (Python-specific TDD with pytest) | [senior-review](senior-review.md) (code review with test assessment) | [playwright-skill](playwright-skill.md) (browser automation with Playwright)
