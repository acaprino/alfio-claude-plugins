# Wrong Abstraction Patterns

Twelve canonical cases where an existing abstraction has gone bad and should be inlined or decomposed. Each pattern is *false unification*: the unified layer hides forces that want to evolve independently. The longer the layer survives, the higher the eventual cost of breaking it apart.

For each pattern: structural signature, why it is wrong, how to escape (inline, decompose, replace with explicit duplication), retrospective indicator that the abstraction has gone bad.

The escape move is almost always *temporarily worse-looking*: you will have more total lines after re-inlining, but the call sites become honest about what they do, which lets the real pattern reveal itself later.

> Patterns are discovery aids and classification examples, never an exhaustive catalog or a prerequisite for a finding.

These twelve serve **D7 abstraction fitness**, whose proof is friction inside one abstraction and not a count of copies. An abstraction that is fighting its callers in a way none of these describes is still a D7 finding, reported with `Pattern: uncatalogued`.

Anti-patterns keep their `A1.` to `A12.` ids inside this file. Elsewhere they are cited as `anti-pattern A1` to avoid colliding with the form gates `A1` to `A5` in `references/evidence-tracks.md`.

---

## A1. God service / utils dumping ground

**Structural signature:** a module called `utils.py`, `helpers/`, `common/`, `shared/`, or `misc.py` that has accumulated dozens of unrelated functions. The module imports nothing related across its own functions. Its public surface looks like `format_currency`, `parse_xml`, `send_slack_alert`, `chunk_list`, `retry_with_backoff`, `validate_email`, `now_utc`, and `slugify`, with no shared theme. Callers import from it because "that is where the helpers live", not because of a conceptual fit.

**Why it is wrong:** the module hides the fact that each helper belongs to a different concern. Currency formatting belongs to the money concept, Slack alerting belongs to the notification concept, retry belongs to the resilience layer, and so on. Grouping them by "they are short" instead of "they share a force of change" produces a magnet for further additions. Once a `utils` module exists, every new orphan function lands there, and nothing ever leaves. The module also defeats grep-based discovery: a reader looking for "how do we format money in this codebase" sees a file that promises nothing.

**Escape move:** re-home each function to the caller most likely to own it or to a concept-named module (`money/`, `notifications/`, `resilience/`, `text/`). When the only caller is one file, inline the function back into that file. The success state is the `utils` module shrinking to empty and being deleted. Resist the urge to "categorize" by creating `utils/string_utils.py`, `utils/date_utils.py`; that just buys time before the same accretion happens one level deeper.

**Retrospective indicator that this abstraction has gone bad:** the module's diff churn shows additions from every team in the company over the past year, with no removals. Asking "what does this module own?" produces a list of nouns rather than a single concept. New hires ask "where do I put this?" and the answer is "in utils".

---

## A2. Flag-soup function (8+ boolean parameters)

**Structural signature:** a function or method with a long parameter list, half of them booleans: `def process_order(order, dry_run=False, skip_validation=False, send_notification=True, legacy_pricing=False, retry_on_failure=True, verbose=False, allow_partial=False, async_mode=False)`. Internally the body branches on each flag, often with `if flag_a and not flag_b` combinations. The function is called from many call sites, each setting a different subset of the flags.

**Why it is wrong:** every boolean is a hidden mode. Eight booleans expose 256 possible combinations, of which only three or four are actually exercised. The combinations not exercised are bugs waiting to happen, because the test suite cannot reasonably cover them. The function's name (`process_order`) no longer describes what it does, since what it does depends on the flags. Callers cannot read a call site like `process_order(o, True, False, True, False, True, False, False, True)` without flipping back to the signature. New requirements add another flag instead of forcing a redesign, because adding a flag is the path of least resistance.

**Escape move:** split into two or three explicit functions with clear names: `process_order`, `process_order_dry_run`, `process_legacy_order`. Each function calls the same private helpers but tells the caller exactly which mode it is operating in. If three or more flags are about *which* validation to run, extract a `ValidationPolicy` value object instead of more booleans. Boolean parameters are acceptable up to two; past that the function is asking to be decomposed.

**Retrospective indicator that this abstraction has gone bad:** every new feature adds another boolean parameter. The signature grows wider every quarter. Code review comments include the phrase "what does `True, False, True` mean here?" Tests for the function are written as a combinatorial table because no one trusts the implicit precedence between flags.

---

## A3. Premature interface / abstract class with one implementation

**Structural signature:** `interface UserRepository { findById, save, delete }` paired with exactly one concrete class `PostgresUserRepository implements UserRepository`. The interface lives in a `contracts/` or `domain/` directory; the implementation lives in `infrastructure/`. Dependency injection wires the interface to the concrete class at startup. No second implementation has ever shipped. The interface was created "so we can swap the database later" or "for testing", but the test suite mocks at a higher level and the database has not changed in three years.

**Why it is wrong:** the interface adds indirection without optionality. Every method on the concrete class must be mirrored on the interface, and changes require touching two files instead of one. The promised future substitution rarely arrives; when it does, the interface usually needs reshaping anyway because the original was guessed from one implementation. The "for testing" justification is weak: tests can mock or fake the concrete class directly, or use a real lightweight backend like SQLite. The interface also lies to readers, suggesting that another implementation exists somewhere when it does not.

**Escape move:** delete the interface, inline the concrete class. Update the dependency injection wiring to register the concrete type. If the codebase later needs a second implementation (a stub for tests, a different storage backend), extract the interface *at that moment* from the two concrete classes, when the real shape of the contract is visible. This is the Rule of Three applied to interfaces: do not create the abstraction before the second implementation exists in code.

**Retrospective indicator that this abstraction has gone bad:** the interface file has not been touched in years except to mirror additions on the concrete class. A `git log --follow` on the interface shows it follows the concrete class one-for-one. No second implementation has appeared, and no PR proposing one has ever been opened.

---

## A4. Generic Repository<T>

**Structural signature:** a base class `Repository<T>` with `findById(id): T`, `findAll(): List<T>`, `save(entity: T)`, `delete(id)`, parameterized over every entity type. Specific repositories extend it: `UserRepository extends Repository<User>`, `OrderRepository extends Repository<Order>`. Most queries go through the base methods. As soon as a non-trivial query appears (`findByEmailWithProfileAndLastLogin`, `findOrdersInStateBetweenDates`), it lives as a one-off method on the subclass, breaking the uniform abstraction.

**Why it is wrong:** the generic shape assumes all entities are queried the same way, but in practice every entity has its own join pattern, index strategy, and filter combinations. The base class becomes a thin pass-through to the ORM, providing no real abstraction over what the ORM already does. Worse, the uniformity invites N+1 queries, because callers reach for `findAll()` followed by per-item lookups instead of writing the right join. The generic interface also forces awkward generic constraints and type-erasure workarounds in languages like Java, adding ceremony without value.

**Escape move:** replace with entity-specific repositories that own their queries explicitly. `UserRepository` has `findById`, `findByEmail`, `findActiveSubscribers`, each implemented with the right query for that entity. No base class. If two entities genuinely share a query pattern (rare), extract that single pattern into a named helper, not a generic base. The result is more methods total, but each one is honest about what it does and how it performs.

**Retrospective indicator that this abstraction has gone bad:** subclasses are mostly empty extends declarations followed by a growing list of one-off methods that bypass the base interface. The base `findAll()` causes performance incidents because callers use it instead of writing the right query. Reviews keep asking "why are we using the generic method here?" and the answer is "because it exists".

---

## A5. Speculative generality

**Structural signature:** extension points that no one uses. Overridable methods declared `protected virtual` with default implementations and no override in the codebase. Hook methods (`beforeSave`, `afterValidate`, `onPreSubmit`) with empty bodies and no subclass touching them. Subclass template patterns where the base class has six abstract methods but only one subclass exists. Configuration parameters that allow swapping behavior but every caller passes the same default.

**Why it is wrong:** the speculation was wrong, but the cost is still being paid. Every extension point widens the surface of the class: more methods to read, more conditions to consider, more test cases to cover the "what if the hook is overridden" path. Readers cannot tell which methods are real and which are placeholders waiting for a future need. The flexibility is invisible to the IDE's call hierarchy because no one calls into the hooks. The cost compounds because subsequent contributors mirror the pattern, adding hooks of their own.

**Escape move:** inline the hooks back into the call sites. Delete the `protected virtual` methods that no one overrides. Remove the configuration parameters whose every caller passes the same default. If a real second use case appears later, the extension point can be carved out at that moment, with the shape that the actual second case demands rather than the shape that was guessed in advance.

**Retrospective indicator that this abstraction has gone bad:** running "find usages" on the extension methods returns zero overrides. The hook bodies are empty across the codebase. Configuration values default to the same literal in every caller. Reviews of the base class include the phrase "what is this hook for?" and no one remembers.

---

## A6. Leaky abstraction exposing vendor types

**Structural signature:** a class named `EmailService`, `StorageProvider`, or `LLMClient` whose public methods take or return vendor-specific types: `def send(message: SendGridMessage)`, `def upload(): aws_sdk.S3Response`, `def complete(prompt: str) -> openai.ChatCompletion`. The class purports to be vendor-neutral, but the type signatures bind callers directly to the vendor's SDK. Switching vendors requires touching every caller, not just the implementation.

**Why it is wrong:** the abstraction promises substitutability but delivers a wrapper. Callers cannot be tested without the vendor SDK installed; callers cannot run against a different vendor without changing their type signatures; the supposed seam is not actually a seam. The intent (decouple from vendor) is fine, but the execution (expose vendor types in the public surface) defeats it. Worse, the vendor-neutral name in the file gives a false sense of safety, so reviewers stop questioning the bindings.

**Escape move:** introduce a real translation layer with domain types: `EmailMessage`, `UploadResult`, `Completion`, defined in the project's own types. The vendor SDK is used only inside the implementation; the public surface uses local types. If translating every field is too expensive, drop the pretense of vendor-neutrality, rename the class to `SendGridClient` or `S3StorageProvider`, and let the binding be honest. Callers then know they are tied to the vendor and can plan accordingly.

**Retrospective indicator that this abstraction has gone bad:** a proposal to switch vendors requires changes in every caller's type imports, not just inside the wrapper. Tests import the vendor SDK to construct test fixtures. The phrase "we are vendor-neutral" appears in the README but the import graph contradicts it.

---

## A7. Strategy pattern for two strategies

**Structural signature:** an `interface PricingStrategy` with two implementations, `StandardPricing` and `DiscountedPricing`, wired up by a `PricingStrategyFactory` that selects based on a customer attribute. Total: one interface, two classes, one factory, four files. The original code that this replaced was a six-line `if customer.is_premium: ... else: ...`.

**Why it is wrong:** the Strategy pattern earns its ceremony when there are many strategies that vary independently and need substitution at runtime. Two strategies do not justify the apparatus. The factory adds a layer of indirection between caller and behavior, so reading a call site requires opening four files instead of one. The pattern's value (open for extension, closed for modification) is theoretical until a third strategy appears, and most of the time it does not.

**Escape move:** inline the two strategies back into an `if/else` (or `match`) at the single call site that needed them. Document the two cases with comments naming each branch. If a third strategy arrives later, that is the moment to extract the abstraction, when the real shape of the variation is visible. Two is a coincidence; three is a pattern.

**Retrospective indicator that this abstraction has gone bad:** the two strategies have not changed in years, no third has been added, and reviewers ask "why is this not just an if/else?". The factory is the only consumer of the interface and adds no real decision logic beyond a single attribute lookup. The combined line count of interface + two classes + factory exceeds five times the original conditional.

---

## A8. Premature event bus / pub-sub between two modules

**Structural signature:** module A publishes an `OrderPlacedEvent` to an in-process event bus; module B subscribes to it and handles the order. A direct method call would do the same work. There is no third subscriber. The event bus implementation lives in the project and dispatches events synchronously within the same process. The original intent was "decouple A and B so they can evolve independently".

**Why it is wrong:** the two modules already evolve together because they always need to stay consistent. Adding an event bus between them buys no decoupling; it only obscures the call graph. Reading "what happens when an order is placed" now requires grepping for `OrderPlacedEvent` subscribers, finding the right handler, and tracing back what state it depends on. Static analysis tools cannot follow the indirection, so "find usages" on the order-placed code returns the publish site only. Errors thrown in subscribers may be swallowed by the bus, depending on its policy. The flow is harder to trace, debug, and reason about, with no offsetting decoupling benefit.

**Escape move:** replace the event with a direct method call from A to B. Delete the event bus if no other event genuinely has multiple subscribers. Reintroduce pub-sub when at least three subscribers exist for the same event, or when one of them is genuinely a different process or service that must be reached asynchronously. In-process pub-sub for synchronous two-party flows is almost always a wrong abstraction.

**Retrospective indicator that this abstraction has gone bad:** the event has exactly one subscriber. Debugging a production issue requires asking "where does this event go?" and grepping the codebase. New contributors do not realize that publishing the event has side effects in B, so they break B when they change A.

---

## A9. Internal DSL or rules engine for a finite hardcoded case set

**Structural signature:** a project includes a `RulesEngine` class plus a `rules/` directory full of YAML files that describe pricing rules, validation rules, or routing rules. The engine parses the YAML at startup, builds an internal AST, and evaluates it at runtime against incoming requests. The total number of distinct rules is small (four, six, ten) and has not changed in two years. The engine is several thousand lines, with a parser, validator, and evaluator. The same logic in plain code would be twenty lines of `if/elif/else`.

**Why it is wrong:** a DSL is justified when non-developers author the rules, when the rule set is large enough to benefit from a declarative syntax, or when the rules change faster than the codebase. For a finite hardcoded case set authored by developers, the DSL is overhead without payoff. The parser adds attack surface (malformed YAML, injection of unintended rules). The runtime evaluator is harder to debug than equivalent code, because stack traces point into the engine's evaluator instead of the rule that misbehaved. Type checking does not reach into the YAML. The "flexibility" benefit is theoretical because no one outside the development team touches the rules.

**Escape move:** replace the engine and YAML files with explicit `if/elif/else` branches or a table-driven test: a Python `dict` or Go `map` keyed by the rule's input shape, with values being functions or constants. Twenty lines of code beats two thousand lines of engine. If a future requirement adds dozens of rules authored by non-developers, revisit the decision then, with the actual non-developer authoring need in evidence.

**Retrospective indicator that this abstraction has gone bad:** the rules directory contains the same number of files it had two years ago. The engine's commit history is mostly bug fixes to the evaluator, not new rules. Debugging a misbehaving rule requires stepping through the engine, not reading the rule. The README has a section explaining the YAML schema, suggesting that the schema is non-obvious to readers.

---

## A10. Test setup helpers grown into 12-parameter factories

**Structural signature:** a test helper named `createUserWithOrdersAndPaymentsAndDiscounts(options)` accepting twelve optional parameters: `email`, `verified`, `orderCount`, `orderState`, `paymentMethod`, `discountTier`, `country`, `currency`, `createdAt`, `lastLoginAt`, `subscriptionStatus`, and a freeform `overrides` dict. Most tests call it with three or four parameters set, leaving the rest as defaults. The factory is called from a hundred tests. Each test reads as `const user = createUser({ orderCount: 3, country: 'IT' })` without the reader knowing whether the user has payments, discounts, a subscription, or anything else.

**Why it is wrong:** tests should be readable in isolation. A reader opening a single test should understand its setup without learning the factory's defaults. The 12-parameter factory hides those defaults behind a single function name, so the test's full context lives in a different file. Worse, changing a default in the factory changes the behavior of every test that did not explicitly override it, breaking the "tests as documentation" property. When a test fails, the developer has to trace which defaults applied to decide whether the failure is real or a side effect of an unrelated default change.

**Escape move:** split into focused factories that name what they build: `createUserWithThreeOrders`, `createItalianCustomerWithPremiumDiscount`, `createUserPendingVerification`. Each factory takes one or two parameters at most and returns a fully constructed object. Tests become slightly more verbose, but each test stands on its own. If two factories share construction logic, extract that as a small private builder, not as a parameter on the public factory.

**Retrospective indicator that this abstraction has gone bad:** test failures cascade across the suite when a factory default changes. Writing a new test starts with "let me find a similar test and copy its setup" because no one knows the defaults. Code review comments include "what does this test actually set up?" The factory file is one of the largest test-support files in the project.

---

## A11. Universal entity/DTO mapper via reflection

**Structural signature:** a method `mapper.map(source, TargetType)` that uses reflection (or runtime metadata in Go/TypeScript) to copy fields from the source object into a new instance of the target type, matching by name. Used everywhere to convert between database entities, DTOs, and API response objects. Configured by attributes or annotations on the source class. Works for the simple cases (`User.email -> UserDTO.email`) and breaks for everything else.

**Why it is wrong:** the moment a field needs computation (`UserDTO.fullName = firstName + " " + lastName`), renaming (`User.created_at -> UserDTO.signupDate`), masking (`User.email -> UserDTO.email[:3] + "***"`), or type conversion (`Decimal` to formatted string), the reflective mapper either fails silently or requires per-field configuration that ends up larger than just writing the mapping by hand. Reflection also defeats static analysis: refactoring tools cannot tell that renaming `User.email` will break the mapper. Compilers cannot type-check the mapping. The behavior is opaque to readers because there is no code to read.

**Escape move:** write explicit `UserDTO.fromUser(user: User): UserDTO` constructors per entity. Each mapper is a few lines, type-checked, refactorable, and explicit about which fields are transformed. The total line count goes up, but the cost of every future refactor goes down. If the entity has dozens of fields and they all map one-to-one, a small generated mapper (compile-time codegen, not runtime reflection) is acceptable; runtime reflection is not.

**Retrospective indicator that this abstraction has gone bad:** the project has a `mapper-config.yaml` or attribute soup that describes special cases, and the file keeps growing. Refactoring an entity name breaks production because the mapper found no match and silently set the field to null. New developers spend time learning the mapper's configuration language before they can do their first real task.

---

## A12. Configuration abstraction that hides important runtime choices

**Structural signature:** a `RulesEngine.evaluate(context)`, `WorkflowOrchestrator.run(spec)`, or `PolicyResolver.decide(request)` whose actual behavior is determined by external configuration files. The Java/Python/JS code is generic; the real logic lives in YAML, JSON, or a database table that operators edit. Reading the source code tells you nothing about what the system does, because the source is a configuration interpreter and the configuration is elsewhere.

**Why it is wrong:** important runtime choices have been pushed out of the type-checked, version-controlled, code-reviewed source and into configuration that has none of those guarantees. A change to a YAML file in production can alter business logic without anyone seeing the diff in a code review. New developers cannot read the codebase to understand the system; they have to acquire the configuration and read that too. Tracing a bug requires correlating the code path through the interpreter with the configuration that drove it, doubling the cognitive load. The pattern is sometimes the right answer (when the configuration genuinely changes faster than the code), but it is misapplied when the configuration is authored by the same developers who own the code.

**Escape move:** surface the runtime choices as named, typed code paths. If there are five pricing rules and they are stable, write five named functions, one per rule, and route to them with a `match` or `switch`. The rules become part of the code, get reviewed, get type-checked, and show up in `git blame`. Keep configuration files for things that genuinely vary per environment (database URLs, feature flags toggled by operators, secrets), not for business logic.

**Retrospective indicator that this abstraction has gone bad:** "what does this system do" requires reading the configuration, not the code. Bugs are introduced by configuration edits that bypass code review. The interpreter's behavior is harder to test than equivalent code, because tests have to set up the configuration before exercising the code path. New developers ask "where is the actual logic?" and the answer is "in the YAML files".
