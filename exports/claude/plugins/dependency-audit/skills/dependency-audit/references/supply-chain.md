# Supply-chain signals: verifiable only

Supply-chain review deals in signals, not verdicts. Every finding in this dimension is a pointer that a human must verify, and is phrased that way ("signal, verify by ..."). Two bans up front:

- **No toy typosquat detection.** Computing name distance against a hardcoded list of famous packages is theater: real typosquat detection needs registry-scale tooling. If a name looks suspicious, verify it directly against the registry (publish date, download counts, linked repository, maintainer history) instead of scoring string similarity. If the user wants systematic typosquat screening, point them at dedicated tooling rather than improvising one.
- **No behavioral claims without reading code.** "Package X exfiltrates data" is never a finding unless the flagged code was actually read. The signal is "declares a postinstall script fetching a remote URL"; the verdict belongs to the human who inspects it.

## Signal catalog

### 1. Lifecycle / install scripts

Packages executing code at install time are the highest-leverage attack surface.

- npm: list dependencies declaring `preinstall` / `install` / `postinstall`. On recent npm, `npm query ":attr(scripts, [postinstall])"` does this; otherwise grep the installed packages' `package.json` files.
- Python: `setup.py`-based sdists execute at build/install time by design; flag only unusual constructs (network fetches, subprocess calls in `setup.py`).
- Signal escalates when a **diff** introduces a new install script in a patch/minor update, or an existing script starts fetching remote content. Verification: read the script.

### 2. Registry metadata

Query the registry, report what it returns (TOOL-REPORTED):

- Package age and publish history (`npm view <pkg> time --json`, PyPI JSON API, crates.io API). Signals: brand-new package pulled in as a new transitive dependency; long-dormant package that suddenly published right before your resolved version.
- Maintainer roster (`npm view <pkg> maintainers`). Signal: maintainer change shortly before the resolved release. Verification: the project's release notes, repository transfer announcements.
- Repository link present and pointing at the claimed source. Signal when absent or mismatched.

### 3. Lockfile integrity

Review the lockfile (and its diff, when auditing a change):

- Resolved URLs pointing off the default registry: `git+http(s)` deps, tarball URLs on unknown hosts, registry mirrors nobody configured deliberately.
- Integrity hash changes without a version change in the diff.
- Dependencies resolved from `file:` or workspace paths that are not part of the repo.

Verification: explain each anomaly from the project's own config (`.npmrc`, mirror settings) or flag it.

### 4. Dependency confusion

For organizations with internal packages: check whether internal package names (scoped or not) also exist on the public registry, and whether the resolver could prefer the public one (missing scope registry pinning in `.npmrc` / `pip.conf` index configuration). Signal: public package shadowing an internal name, especially with an inflated version number. Verification: resolver config plus a dry-run install log showing the source registry per package.

### 5. Advisory and provenance databases

Primary sources to query, never to paraphrase from memory:

- OSV.dev (via `osv-scanner` or the HTTP API) for known malicious-package advisories (`MAL-` ids) alongside vulnerabilities.
- deps.dev API for cross-registry metadata (dependents, OpenSSF Scorecard results) when reachable.
- npm provenance attestations (`npm view <pkg> dist.attestations`) where the ecosystem supports them: presence is a positive signal, absence is neutral (most packages lack them), a failing verification is a finding.

## Reporting rule

Each signal reports: what was observed (TOOL-REPORTED), why it is a signal (one sentence), and the exact verification step for a human. Signals never aggregate into an invented "supply-chain risk score".
