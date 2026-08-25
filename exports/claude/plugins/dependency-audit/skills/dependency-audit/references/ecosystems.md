# Per-ecosystem tool matrix

Commands for vulnerability audit, outdated detection, license inventory, and dependency-tree queries, per ecosystem. Two rules apply everywhere:

- **Flags drift across tool versions.** If a listed flag errors, drop to the tool's default output and parse the text. Never fake machine-readable output that a tool did not produce.
- **Prefer the package manager the lockfile identifies.** Running a different manager's audit against someone else's lockfile produces incomplete or misleading results.

## Summary

| Ecosystem | Detect via | Audit | Outdated | Licenses |
|---|---|---|---|---|
| npm | `package-lock.json` | `npm audit --json` | `npm outdated --json` | `license-checker` |
| pnpm | `pnpm-lock.yaml` | `pnpm audit --json` | `pnpm outdated` | `pnpm licenses list` |
| yarn | `yarn.lock` | `yarn audit --json` (classic) / `yarn npm audit --json` (berry) | `yarn outdated` (classic) | `license-checker` |
| bun | `bun.lock` / `bun.lockb` | `bun audit` | `bun outdated` | `license-checker` |
| Python | `pyproject.toml`, `requirements.txt`, `uv.lock`, `poetry.lock` | `pip-audit -f json` | `pip list --outdated --format json` | `pip-licenses --format=json` |
| Rust | `Cargo.toml` / `Cargo.lock` | `cargo audit --json` | `cargo outdated` | `cargo license` |
| Go | `go.mod` / `go.sum` | `govulncheck -json ./...` | `go list -u -m -json all` | `go-licenses report ./...` |
| Ruby | `Gemfile` / `Gemfile.lock` | `bundler-audit check --update` | `bundle outdated` | `license_finder` |
| PHP | `composer.json` / `composer.lock` | `composer audit --format=json` | `composer outdated --format=json` | `composer licenses` |
| Java | `pom.xml`, `build.gradle(.kts)` | OWASP dependency-check plugin | `mvn versions:display-dependency-updates` / versions plugin | license-maven-plugin |
| .NET | `*.csproj`, `packages.config` | `dotnet list package --vulnerable --include-transitive` | `dotnet list package --outdated` | `nuget-license` |
| Any | lockfiles | `osv-scanner --recursive .` | - | - |

## JavaScript / TypeScript (npm, pnpm, yarn, bun)

- Identify the manager from the lockfile before running anything. Mixed lockfiles (two managers' lockfiles side by side) are themselves a hygiene finding; report them.
- `npm audit --json` (registry advisory data; requires a lockfile). Parse the `vulnerabilities` map: entries carry `severity`, `via` (chain to the advisory), `range`, `fixAvailable`. `fixAvailable: { isSemVerMajor: true }` marks fixes that need a major jump: those go to the individual-review bucket, never auto-applied.
- Yarn classic `yarn audit --json` emits NDJSON (one JSON object per line); berry uses `yarn npm audit --json`.
- Direct vs transitive: `npm ls <pkg> --all`, `pnpm why <pkg>`, `yarn why <pkg>`.
- Licenses: `npx license-checker --json` (or the maintained `license-checker-rseidelsohn` fork); both read installed `node_modules`, so install first. pnpm ships `pnpm licenses list` natively.
- Registry metadata (supply-chain steps): `npm view <pkg> time --json`, `npm view <pkg> maintainers`.

## Python

- `pip-audit` (PyPA; sources: PyPI advisory db + OSV). Modes: `pip-audit` against the active environment, `pip-audit -r requirements.txt` against a requirements file.
- uv projects: `uv export --format requirements-txt > /tmp/req.txt` then `pip-audit -r /tmp/req.txt`, or `uvx pip-audit` inside the project environment.
- Poetry: `poetry show --outdated` for lag; export for pip-audit: `poetry export -f requirements.txt`.
- Licenses: `pip-licenses --format=json` reads installed metadata; run in the project environment.

## Rust

- `cargo audit --json` (RustSec advisory db; install: `cargo install cargo-audit`). Reads `Cargo.lock`.
- Outdated: `cargo outdated` (install: `cargo install cargo-outdated`).
- Licenses: `cargo license` (install: `cargo install cargo-license`); when the project carries a `deny.toml`, prefer `cargo deny check licenses` since it evaluates the project's own policy.
- Reverse tree: `cargo tree -i <crate>`.

## Go

- `govulncheck -json ./...` (install: `go install golang.org/x/vuln/cmd/govulncheck@latest`). Call-graph aware: it distinguishes vulnerabilities in *called* code from merely *imported* modules. Report the distinction verbatim; it is the tool's headline feature and materially changes priority.
- Outdated: `go list -u -m -json all` (entries with an `Update` field lag).
- Licenses: `go-licenses report ./...` (install: `go install github.com/google/go-licenses@latest`).
- Why is it here: `go mod why <module>`, full graph: `go mod graph`.

## Ruby

- `bundler-audit check --update` (`--update` refreshes the local ruby-advisory-db copy first; that flag updates the advisory database, not the project).
- Outdated: `bundle outdated`.
- Licenses: `license_finder` (multi-ecosystem, works for Ruby when Bundler is present).

## PHP

- `composer audit --format=json` (Composer >= 2.4; sources: Packagist security advisories).
- Outdated: `composer outdated --format=json` (`--direct` limits to direct deps).
- Licenses: `composer licenses`.

## Java (Maven / Gradle)

- Vulnerabilities: OWASP dependency-check (`mvn org.owasp:dependency-check-maven:check`, or the `dependency-check-gradle` plugin). It downloads NVD data on first run, which is slow and may need an NVD API key; if the project has not configured it, report the gap and offer `osv-scanner` against the build files as the lighter alternative rather than injecting build plugins uninvited.
- Outdated: `mvn versions:display-dependency-updates`; Gradle: the ben-manes `versions` plugin (`gradle dependencyUpdates`) when applied.
- Licenses: `license-maven-plugin` when configured; otherwise report the gap.

## .NET

- `dotnet list package --vulnerable --include-transitive` (advisory source: GitHub Advisory Database via NuGet).
- Outdated: `dotnet list package --outdated`.
- Licenses: `nuget-license` dotnet tool when installed; otherwise report the gap.

## Cross-ecosystem second source: osv-scanner

`osv-scanner --recursive <path>` scans lockfiles across all of the above against OSV.dev. Use it (a) as the fallback when an ecosystem's native tool is missing, (b) as a second opinion beside native results. Label its findings as osv-scanner output and report source disagreements side by side; do not merge them into one deduplicated list silently.
