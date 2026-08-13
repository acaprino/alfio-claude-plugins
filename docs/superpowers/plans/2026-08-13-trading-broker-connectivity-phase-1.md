# trading-broker-connectivity Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a leaf plugin that owns the archetype-generic vocabulary of broker integration, a maintenance skill that states what a broker plugin must contain, and a CI check that enforces the mechanically decidable half, then bring `ibkr-trading` and `mt5-trading` onto it.

**Architecture:** One new skill-only plugin under `plugins/`, one new maintenance skill under `.claude/skills/`, one new stdlib-only linter under `scripts/` with unit tests under `tests/`. No new dependencies in any direction: the generic plugin is a leaf and neither broker plugin declares it. Coherence between the duplicated vocabulary copies is held by `lint_fact_anchors.py`, not by a runtime dependency.

**Tech Stack:** Markdown content, stdlib-only Python 3 for the linter, `unittest` for its tests, GitHub Actions for CI.

**Spec:** `docs/superpowers/specs/2026-08-13-trading-broker-connectivity-design.md`

## Global Constraints

- **No dash-asides anywhere**, in any file this plan touches. The banned construct is a clause bracketed between dashes in any form: `—`, `--`, ` - `. Substituting `--` for `—` is not the fix. Rewrite into separate sentences, parentheses, or a colon. Hyphenated compounds (`local-terminal`, `multi-agent`) are unrelated and fine.
- **The generic plugin never dispatches into a broker plugin.** It may name Interactive Brokers and MetaTrader 5 in prose. It must never instruct a reader to load `ibkr-trading` or `mt5-trading`, spawn their agents, or run their commands. That would create two hard local dependencies under the dependency policy in `CLAUDE.md` and invert the graph.
- **The generic plugin declares no local dependency**, and neither broker plugin gains one.
- **Stdlib only** for every script. No third-party imports, no network access at check time.
- **Self-references inside a plugin use `${CLAUDE_PLUGIN_ROOT}`** or a skill-relative `references/...` path. A literal `plugins/<name>/...` path inside plugin content fails `lint_bundled_paths.py`, because installed users have no such path.
- **The five canonical archetype names**, verbatim and closed: `direct-api`, `local-terminal`, `vendor-gateway`, `bridge`, `in-platform`.
- **The three provenance tags**, verbatim: `MEASURED`, `DOCUMENTED`, `ASSUMED`.
- **The evidence ladder has six ranks.** Rank 4 states that a client library's source code is proof about the library and only a hypothesis about the broker.
- **Version bumps land in the same push** as the content: each touched plugin's `version` plus `metadata.version` in `.claude-plugin/marketplace.json`, or `check_version_bumps.py` fails the range.
- **Stage explicit paths.** Never `git add -A`. Several sessions run this repository at once and blanket staging has already published a half-state.

---

## File Structure

| Path | Responsibility |
|---|---|
| `plugins/trading-broker-connectivity/skills/trading-broker-connectivity/SKILL.md` | Entry point: the archetype table, the ladder summary, routing into the four references |
| `.../references/access-archetypes.md` | The five archetypes and where IBKR and MT5 sit |
| `.../references/order-lifecycle-reference-model.md` | Vendor-neutral order state machine, identifiers, the three acceptance layers |
| `.../references/session-and-recovery.md` | Session exclusivity, unattended auth, reconnection, reconciliation |
| `.../references/evidence-and-probes.md` | Six-rank ladder, three provenance tags, probe design, demo-environment limits |
| `.claude/skills/broker-plugin-contract/SKILL.md` | What a broker plugin must contain, at level `base` and level `verified` |
| `scripts/lint_broker_plugins.py` | The mechanically decidable half of the contract |
| `tests/test_broker_plugins_lint.py` | Unit tests for the linter, on throwaway fixture trees |
| `.claude-plugin/marketplace.json` | Registration of the new plugin and skill, three version bumps |
| `docs/plugins/trading-broker-connectivity.md` | Per-plugin documentation page |
| `.github/workflows/consistency.yml` | The eighth Python check |
| `CLAUDE.md` | CI section, repo-workflows table, the contract as standing policy |
| `README.md` | Plugin table row and recounted badges |
| `exports/vscode/trading-broker-connectivity/.github/...` | VS Code bundle: adapted `SKILL.md`, byte-copied references |
| `exports/vscode/CHANGELOG.md` | The 23.0.0 section |

**Note on prose files.** For the five markdown content files, this plan specifies the exact required headings, the closed vocabularies verbatim, and the acceptance checks. The connecting prose is authored during execution against those constraints. Reproducing every paragraph here would mean writing the plugin twice, and the constraints below are what a reviewer would actually check.

---

### Task 1: The generic plugin, created and registered

**Files:**
- Create: `plugins/trading-broker-connectivity/skills/trading-broker-connectivity/SKILL.md`
- Create: `plugins/trading-broker-connectivity/skills/trading-broker-connectivity/references/access-archetypes.md`
- Create: `plugins/trading-broker-connectivity/skills/trading-broker-connectivity/references/order-lifecycle-reference-model.md`
- Create: `plugins/trading-broker-connectivity/skills/trading-broker-connectivity/references/session-and-recovery.md`
- Create: `plugins/trading-broker-connectivity/skills/trading-broker-connectivity/references/evidence-and-probes.md`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Produces: the five archetype names, the three provenance tags, and the six-rank ladder, which Tasks 2, 3, 4 and 5 all reference. The `SKILL.md` path, which Task 7 mirrors into the export.

- [ ] **Step 1: Write `access-archetypes.md`**

Required headings, in order: `## The five archetypes`, `## What changes per archetype`, `## Where the two integrated brokers sit`.

The first section carries this table verbatim, because the linter validates declarations against exactly these names:

```markdown
| Archetype | Meaning |
|---|---|
| `direct-api` | A cloud API reached over the network. No vendor component runs on your machine |
| `local-terminal` | A vendor application must run locally, holds session state, and may perform order handling itself rather than relaying it |
| `vendor-gateway` | A vendor-operated gateway or protocol engine you connect to, usually behind onboarding or conformance certification |
| `bridge` | Third-party software sitting between a platform and a broker, operated by neither of them |
| `in-platform` | Code that runs inside the vendor's own application rather than beside it |
```

The second section covers, per archetype: where session state lives, what dies when each component dies, what the developer is responsible for running and keeping alive, and the failure surface the archetype adds that the others do not have.

The third section states that Interactive Brokers (through the TWS API and IB Gateway) and MetaTrader 5 are both `local-terminal`, and lists the consequences they therefore share: order handling performed locally rather than relayed, headless operation as an open question, authentication that assumes a human, session exclusivity on a second login, scheduled restart windows, and state lost when the terminal dies. Name both products. Do not tell the reader to load either plugin.

- [ ] **Step 2: Write `order-lifecycle-reference-model.md`**

Required headings: `## The reference state machine`, `## The three layers that can refuse`, `## Identifiers`, `## What a successful place call proves`, `## Mapping a vendor's vocabulary onto this one`.

The three layers are: transport acceptance, broker validation acceptance, venue acceptance. State explicitly that a synchronous success at one layer says nothing about the next, and that asynchronous refusal after a synchronous success is the normal case rather than an anomaly.

Identifiers: client-assigned order ID, broker order ID, execution ID. Per identifier state who assigns it, its uniqueness scope, and whether it survives a cancel or replace.

The last section is the point of the file: it gives the procedure for stating "this vendor calls X what this model calls Y" rather than silently substituting one for the other.

- [ ] **Step 3: Write `session-and-recovery.md`**

Required headings: `## Session exclusivity`, `## Authentication without a human`, `## Reconnection and the healthy-looking dead connection`, `## Reconciling ground truth after a gap`, `## What must be persisted`.

Vendor-neutral throughout. Where a concrete example is needed, name the archetype rather than the vendor.

- [ ] **Step 4: Write `evidence-and-probes.md`**

Required headings: `## The evidence ladder`, `## Provenance tags`, `## Designing a probe`, `## What a demo environment cannot settle`.

The ladder is adopted from `plugins/ibkr-trading/skills/ibkr-trading/references/venue-questions-and-probes.md` lines 13 to 47. Read that file first and generalize the wording only, replacing IBKR-specific nouns with vendor-neutral ones. Preserve: six ranks; rank 1 is your own probe transcript; rank 6 is a search-engine or AI summary and is explicitly not evidence at any strength; rank 4 states that a client library's source code is proof about the library and never about the broker.

The provenance tags section carries exactly three tags, `MEASURED`, `DOCUMENTED` and `ASSUMED`, with the rule that unmeasured assumptions are unavoidable and hiding them is the defect.

The last section states which classes of question a demo environment can settle (protocol behaviour, validation, capability, error codes) and which it cannot (fills, latency, liquidity, queue position).

- [ ] **Step 5: Write the `SKILL.md`**

Frontmatter:

```yaml
---
name: trading-broker-connectivity
description: >
  Vendor-neutral vocabulary for programmatic broker integration: the five access archetypes, the
  reference order state machine, session and recovery, and the evidence ladder that decides what a
  claim about a venue is worth.
  TRIGGER WHEN: comparing brokers or integration paths, starting an integration against a broker with
  no dedicated plugin, or naming what kind of access path a system uses.
  DO NOT TRIGGER WHEN: the question is about one specific broker that has its own plugin, or about
  strategy, backtesting, or portfolio construction.
---
```

Body: a short statement of what the plugin is for, the archetype table repeated in compact form, a one-line summary of the ladder and the three tags, and a Reference materials list with one descriptive line per file.

- [ ] **Step 6: Register the plugin**

In `.claude-plugin/marketplace.json`, append to `plugins[]`:

```json
{
  "name": "trading-broker-connectivity",
  "source": "./plugins/trading-broker-connectivity",
  "description": "Vendor-neutral vocabulary for programmatic broker integration: five access archetypes, a reference order state machine with the three layers that can refuse an order, session and recovery patterns, and the six-rank evidence ladder with provenance tags that decides what a claim about a venue is worth",
  "version": "1.0.0",
  "author": { "name": "Alfio" },
  "license": "MIT",
  "keywords": [
    "broker", "connectivity", "algotrading", "fix-protocol", "order-lifecycle",
    "gateway", "archetypes", "evidence-ladder", "integration"
  ],
  "category": "algotrading",
  "strict": false,
  "skills": ["./skills/trading-broker-connectivity"]
}
```

Set `metadata.version` to `23.0.0`. Do not add an `agents` or `commands` key: this plugin has neither, and `obsidian-development` is the precedent for a skill-only entry.

- [ ] **Step 7: Verify registration and paths**

Run:
```bash
python scripts/lint_plugin_registration.py
python scripts/lint_bundled_paths.py
```
Expected: both pass. If `lint_bundled_paths.py` fails, a reference wrote a literal `plugins/...` path; convert it to `${CLAUDE_PLUGIN_ROOT}/...` or a skill-relative `references/...`.

- [ ] **Step 8: Commit**

```bash
git add plugins/trading-broker-connectivity .claude-plugin/marketplace.json
git commit -m "Add the trading-broker-connectivity plugin with the shared archetype vocabulary"
```

---

### Task 2: The contract skill and its linter

**Files:**
- Create: `.claude/skills/broker-plugin-contract/SKILL.md`
- Create: `scripts/lint_broker_plugins.py`
- Create: `tests/test_broker_plugins_lint.py`

**Interfaces:**
- Consumes: the five archetype names and three provenance tags from Task 1.
- Produces: `**Contract level:** <base|verified>` and `**Archetype:** <name>` as the two declaration lines that Tasks 3 and 4 add to the two broker plugins. The linter entry point `python scripts/lint_broker_plugins.py`, wired into CI by Task 5.

- [ ] **Step 1: Write the contract skill**

`.claude/skills/broker-plugin-contract/SKILL.md`, with frontmatter in the shape of the other four maintenance skills (`name`, `description` with `TRIGGER WHEN` and `DO NOT TRIGGER WHEN`).

Required headings: `## The two levels`, `## Level base`, `## Level verified`, `## How a plugin declares its level`, `## The describe-but-never-dispatch rule`, `## What the linter checks and what it cannot`.

`Level base` lists, as a checklist:
1. A `<broker>-architect` agent, a `<broker>-audit` command, and one skill with a `references/` directory, all three registered in `.claude-plugin/marketplace.json` and not merely present on disk.
2. The skill `description` carries both `TRIGGER WHEN` and `DO NOT TRIGGER WHEN`.
3. The `SKILL.md` carries four sections: Quick start, Key decision points, Symptoms to entry points, Reference materials.
4. The plugin declares one of the five canonical archetype names.
5. The plugin uses the reference model's names for order states, and where the vendor uses different ones it maps them explicitly.

`Level verified` adds:
1. A `<broker>-verify` command with probe scripts that measure against a demo or paper environment.
2. A register of open questions, each paired with the experiment that would settle it, in a reference file.
3. Every `MEASURED` fact carries its date and the instrument that measured it.
4. The probe tooling refuses production structurally, not by configuration.

`How a plugin declares its level` states the two exact lines and that `<broker>` is the plugin directory name with a trailing `-trading` removed.

`The describe-but-never-dispatch rule` restates the Global Constraint above with its reasoning: a prose pointer is not a dependency, an instruction to load is, and adding one inverts the dependency graph.

The last section names what stays prose-enforced: whether a fact genuinely has the provenance it claims, and whether the shared vocabulary is used correctly inside prose.

- [ ] **Step 2: Write the failing tests**

`tests/test_broker_plugins_lint.py`. Follow `tests/test_concept_index.py`: stdlib only, real throwaway trees rather than mocks, because the script's job is to answer questions about a directory layout.

```python
"""Tests for the broker-plugin contract linter.

Stdlib only. Each test builds a real throwaway marketplace tree, because the
script's whole job is to answer questions about a directory layout and a
mocked filesystem would test the mock.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "lint_broker_plugins.py"

SKILL_TEMPLATE = """---
name: {skill}
description: >
  A knowledge base.
  TRIGGER WHEN: building against {broker}.
  DO NOT TRIGGER WHEN: another broker is the subject.
---

# {broker}

**Contract level:** {level}
**Archetype:** {archetype}

## Quick start
Connect, then place an order.

## Key decision points
| Decision | Default |
|---|---|
| Library | the official one |

## Symptoms to entry points
| Symptom | Read |
|---|---|
| Nothing fills | `orders.md` |

## Reference materials
- `orders.md` - how orders behave
"""


def build(root, name="acme-trading", level="base", archetype="local-terminal",
          refs=("orders.md",), listed=("orders.md",), agent=True, command=True,
          register=True, verify=False, probe=False, register_verify=False,
          category="algotrading", sections=None):
    """Write one plugin plus a marketplace.json describing it."""
    broker = name[:-len("-trading")] if name.endswith("-trading") else name
    plugin = root / "plugins" / name
    skill = plugin / "skills" / name
    (skill / "references").mkdir(parents=True)
    body = SKILL_TEMPLATE.format(skill=name, broker=broker, level=level,
                                 archetype=archetype)
    if sections is not None:
        body = sections
    listing = "\n".join(f"- `{r}` - description" for r in listed)
    body = body.replace("- `orders.md` - how orders behave", listing)
    (skill / "SKILL.md").write_text(body, encoding="utf-8")
    for ref in refs:
        (skill / "references" / ref).write_text("# ref\n", encoding="utf-8")

    entry = {"name": name, "source": f"./plugins/{name}", "version": "1.0.0",
             "category": category, "skills": [f"./skills/{name}"]}
    if agent:
        (plugin / "agents").mkdir(parents=True, exist_ok=True)
        (plugin / "agents" / f"{broker}-architect.md").write_text("x", encoding="utf-8")
        if register:
            entry["agents"] = [f"./agents/{broker}-architect.md"]
    commands = []
    if command:
        (plugin / "commands").mkdir(parents=True, exist_ok=True)
        (plugin / "commands" / f"{broker}-audit.md").write_text("x", encoding="utf-8")
        commands.append(f"./commands/{broker}-audit.md")
    if verify:
        (plugin / "commands").mkdir(parents=True, exist_ok=True)
        (plugin / "commands" / f"{broker}-verify.md").write_text("x", encoding="utf-8")
        if register_verify:
            commands.append(f"./commands/{broker}-verify.md")
    if commands and register:
        entry["commands"] = commands
    if probe:
        (skill / "scripts").mkdir(parents=True, exist_ok=True)
        (skill / "scripts" / f"{broker}_probe.py").write_text("x", encoding="utf-8")
        (skill / "references" / "open-questions.md").write_text(
            "# q\n\n## Open questions\n\n- one\n", encoding="utf-8")

    mp = root / ".claude-plugin"
    mp.mkdir(exist_ok=True)
    (mp / "marketplace.json").write_text(
        json.dumps({"metadata": {"version": "1.0.0"}, "plugins": [entry]}),
        encoding="utf-8")
    return root


def run(root):
    return subprocess.run([sys.executable, str(SCRIPT)], cwd=root,
                          capture_output=True, text=True)


class ContractLinter(unittest.TestCase):

    def test_conformant_base_plugin_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp))
            result = run(Path(tmp))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unknown_archetype_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), archetype="socket-thing")
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("socket-thing", result.stdout + result.stderr)

    def test_missing_declaration_on_algotrading_plugin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), sections="---\nname: acme-trading\ndescription: x\n---\n\n# acme\n")
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Contract level", result.stdout + result.stderr)

    def test_unregistered_agent_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), register=False)
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)

    def test_reference_on_disk_but_not_listed_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), refs=("orders.md", "extra.md"), listed=("orders.md",))
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("extra.md", result.stdout + result.stderr)

    def test_reference_listed_but_absent_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), refs=("orders.md",), listed=("orders.md", "ghost.md"))
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ghost.md", result.stdout + result.stderr)

    def test_verified_without_verify_command_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), level="verified")
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("verify", result.stdout + result.stderr)

    def test_verified_with_unregistered_verify_command_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), level="verified", verify=True, probe=True,
                  register_verify=False)
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)

    def test_fully_conformant_verified_plugin_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), level="verified", verify=True, probe=True,
                  register_verify=True)
            result = run(Path(tmp))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_section_heading_case_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build(Path(tmp))
            skill = root / "plugins" / "acme-trading" / "skills" / "acme-trading" / "SKILL.md"
            skill.write_text(skill.read_text(encoding="utf-8")
                             .replace("## Quick start", "## Quick Start")
                             .replace("## Key decision points", "## Key Decision Points"),
                             encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m unittest tests.test_broker_plugins_lint -v`
Expected: every test errors, because `scripts/lint_broker_plugins.py` does not exist yet.

- [ ] **Step 4: Write the linter**

`scripts/lint_broker_plugins.py`. Module docstring in the voice of `scripts/lint_fact_anchors.py`: say what the check is for, why a self-declaring roster needs the category cross-check, and that fixing a declaration is the response to a failure rather than adding an allowlist entry.

```python
import json
import re
import sys
from pathlib import Path

GENERIC_PLUGIN = "trading-broker-connectivity"
BROKER_CATEGORY = "algotrading"

ARCHETYPES = {"direct-api", "local-terminal", "vendor-gateway", "bridge", "in-platform"}
LEVELS = {"base", "verified"}

REQUIRED_SECTIONS = ("quick start", "key decision points",
                     "symptoms to entry points", "reference materials")

OPEN_QUESTION_HEADINGS = ("open questions", "questions the documentation does not answer")

LEVEL_RE = re.compile(r"^\*\*Contract level:\*\*\s*(\S+)\s*$", re.MULTILINE)
ARCHETYPE_RE = re.compile(r"^\*\*Archetype:\*\*\s*(\S+)\s*$", re.MULTILINE)
HEADING_RE = re.compile(r"^#{2,3}\s+(.+?)\s*$", re.MULTILINE)
LISTED_REF_RE = re.compile(r"^[-*]\s+`([^`]+\.md)`", re.MULTILINE)

# Heuristic misreads only, each with a reason. Never add an entry to make a
# real conformance failure go away: fix the plugin instead.
ALLOWLIST = {}


def broker_token(plugin_name):
    """`ibkr-trading` -> `ibkr`. A plugin not ending in -trading keeps its name."""
    suffix = "-trading"
    return plugin_name[:-len(suffix)] if plugin_name.endswith(suffix) else plugin_name


def load_marketplace(root):
    data = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    return {p["name"]: p for p in data["plugins"]}


def skill_files(root, plugin_name):
    return sorted((root / "plugins" / plugin_name).glob("skills/*/SKILL.md"))


def check(root):
    failures = []
    entries = load_marketplace(root)

    for name, entry in sorted(entries.items()):
        if name == GENERIC_PLUGIN:
            continue
        skills = skill_files(root, name)
        declared = [s for s in skills if LEVEL_RE.search(s.read_text(encoding="utf-8"))]

        if not declared:
            if entry.get("category") == BROKER_CATEGORY:
                failures.append(
                    f"{name}: category is {BROKER_CATEGORY} but no SKILL.md carries a "
                    f"**Contract level:** line. Declare base or verified.")
            continue

        for skill in declared:
            failures.extend(check_plugin(root, name, entry, skill))

    return failures


def check_plugin(root, name, entry, skill_path):
    out = []
    text = skill_path.read_text(encoding="utf-8")
    plugin_dir = root / "plugins" / name
    token = broker_token(name)

    level = LEVEL_RE.search(text).group(1)
    if level not in LEVELS:
        out.append(f"{name}: contract level {level!r} is not one of {sorted(LEVELS)}")
        return out

    archetype_match = ARCHETYPE_RE.search(text)
    if not archetype_match:
        out.append(f"{name}: no **Archetype:** line")
    elif archetype_match.group(1) not in ARCHETYPES:
        out.append(f"{name}: archetype {archetype_match.group(1)!r} is not one of "
                   f"{sorted(ARCHETYPES)}")

    description = text.split("---")[1] if text.startswith("---") else ""
    for clause in ("TRIGGER WHEN:", "DO NOT TRIGGER WHEN:"):
        if clause not in description:
            out.append(f"{name}: skill description is missing {clause}")

    headings = {h.strip().lower() for h in HEADING_RE.findall(text)}
    for section in REQUIRED_SECTIONS:
        if section not in headings:
            out.append(f"{name}: SKILL.md has no '{section}' section")

    out.extend(check_references(name, skill_path, text))
    out.extend(check_structure(name, entry, plugin_dir, token))
    if level == "verified":
        out.extend(check_verified(name, entry, plugin_dir, skill_path, token))
    return out


def check_references(name, skill_path, text):
    out = []
    ref_dir = skill_path.parent / "references"
    on_disk = {p.name for p in ref_dir.glob("*.md")} if ref_dir.is_dir() else set()
    listed = {Path(r).name for r in LISTED_REF_RE.findall(text) if r.endswith(".md")}
    for missing in sorted(on_disk - listed):
        out.append(f"{name}: references/{missing} exists but is not listed in SKILL.md")
    for ghost in sorted(listed - on_disk):
        out.append(f"{name}: SKILL.md lists {ghost} but references/ has no such file")
    return out


def check_structure(name, entry, plugin_dir, token):
    out = []
    wanted = [
        (plugin_dir / "agents" / f"{token}-architect.md", entry.get("agents", []),
         f"./agents/{token}-architect.md"),
        (plugin_dir / "commands" / f"{token}-audit.md", entry.get("commands", []),
         f"./commands/{token}-audit.md"),
    ]
    for path, registered, rel in wanted:
        if not path.is_file():
            out.append(f"{name}: base level requires {path.relative_to(plugin_dir.parent.parent)}")
        elif rel not in registered:
            out.append(f"{name}: {rel} exists on disk but is not registered in marketplace.json")
    return out


def check_verified(name, entry, plugin_dir, skill_path, token):
    out = []
    verify = plugin_dir / "commands" / f"{token}-verify.md"
    rel = f"./commands/{token}-verify.md"
    if not verify.is_file():
        out.append(f"{name}: level verified requires commands/{token}-verify.md")
    elif rel not in entry.get("commands", []):
        out.append(f"{name}: {rel} exists on disk but is not registered in marketplace.json")

    scripts = skill_path.parent / "scripts"
    if not (scripts.is_dir() and any(scripts.glob("*probe*.py"))):
        out.append(f"{name}: level verified requires a probe script under skills/*/scripts/")

    ref_dir = skill_path.parent / "references"
    found = False
    for ref in sorted(ref_dir.glob("*.md")) if ref_dir.is_dir() else []:
        headings = {h.strip().lower() for h in HEADING_RE.findall(ref.read_text(encoding="utf-8"))}
        if headings & set(OPEN_QUESTION_HEADINGS):
            found = True
            break
    if not found:
        out.append(f"{name}: level verified requires an open-questions register in references/")
    return out


def main():
    root = Path.cwd()
    failures = [f for f in check(root) if f not in ALLOWLIST]

    if failures:
        print(f"{len(failures)} contract violation(s):\n")
        for failure in failures:
            print(f"  {failure}")
        sys.exit("\nfix the plugin, not the linter; see .claude/skills/broker-plugin-contract/")
    print("all broker plugins conform to the contract")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m unittest tests.test_broker_plugins_lint -v`
Expected: 10 tests, all PASS. The linter body in Step 4 is a starting point written against the fixtures, not code that has been executed: where a test fails, the test states the contract and the implementation is what gives way.

- [ ] **Step 6: Run against the real repository**

Run: `python scripts/lint_broker_plugins.py`
Expected: FAIL, naming `ibkr-trading` and `mt5-trading` as lacking a `**Contract level:**` line. That is the correct state at this point; Tasks 3 and 4 fix it. Record the exact output, it is the checklist for the next two tasks.

- [ ] **Step 7: Commit**

```bash
git add .claude/skills/broker-plugin-contract scripts/lint_broker_plugins.py tests/test_broker_plugins_lint.py
git commit -m "Add the broker plugin contract and the linter that enforces its decidable half"
```

---

### Task 3: Bring `ibkr-trading` onto the contract

**Files:**
- Modify: `plugins/ibkr-trading/skills/ibkr-trading/SKILL.md`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: the two declaration lines from Task 2, the archetype names from Task 1.

- [ ] **Step 1: Add the declaration lines**

In `plugins/ibkr-trading/skills/ibkr-trading/SKILL.md`, immediately after the `# Interactive Brokers Integration` heading and its lead paragraph, insert:

```markdown
**Contract level:** verified
**Archetype:** local-terminal
```

- [ ] **Step 2: Align the ladder wording**

`references/venue-questions-and-probes.md` keeps its six ranks and three tags unchanged. Add one sentence under `## The evidence ladder` stating that this ladder is the vendor-neutral one from the `trading-broker-connectivity` skill, applied to IBKR. Do not instruct the reader to load that skill: name it as the origin, nothing more.

- [ ] **Step 3: Bump the version**

In `.claude-plugin/marketplace.json`, set `ibkr-trading` `version` to `2.9.0`. `metadata.version` is already `23.0.0` from Task 1.

- [ ] **Step 4: Verify**

Run: `python scripts/lint_broker_plugins.py`
Expected: `ibkr-trading` no longer appears; `mt5-trading` still fails on the missing declaration.

- [ ] **Step 5: Commit**

```bash
git add plugins/ibkr-trading .claude-plugin/marketplace.json
git commit -m "Declare ibkr-trading verified against the broker plugin contract"
```

---

### Task 4: Bring `mt5-trading` onto the contract

**Files:**
- Modify: `plugins/mt5-trading/skills/mt5-trading/SKILL.md`
- Modify: `plugins/mt5-trading/skills/mt5-trading/references/*.md` (separator pass)
- Modify: `plugins/mt5-trading/agents/mt5-architect.md` (separator pass)
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: the two declaration lines from Task 2.

- [ ] **Step 1: Add the declaration lines and the missing routing clause**

After the `# MetaTrader 5 Python Algotrading` heading and its lead paragraph, insert:

```markdown
**Contract level:** base
**Archetype:** local-terminal
```

In the frontmatter `description`, append a routing clause after the existing `TRIGGER WHEN` sentence:

```
  DO NOT TRIGGER WHEN: the broker is Interactive Brokers (use ibkr-trading), or the question is about
  strategy design rather than the terminal and its API.
```

- [ ] **Step 2: Add the Symptoms to entry points table**

Insert between `## Reference Materials` and `## Key Decision Points`:

```markdown
## Symptoms to entry points

| Symptom | Read |
|---|---|
| An API call returned `None` and nothing was logged | `api-architecture.md` |
| Order rejected with retcode 10030 | `order-execution.md` |
| Positions netted when hedging was expected | `order-execution.md` |
| A tick or candle handler never fires | `event-system-polling.md` |
| Bars disagree with the chart, or timestamps look shifted | `data-feed-historical.md` |
| The terminal is running but the API answers nothing | `production-resilience.md` |
| Everything stops on Saturday and resumes wrong on Monday | `production-resilience.md` |
```

Every entry must point at a file that exists, or the linter's bidirectional reference check will not catch it but a reader will.

- [ ] **Step 3: The separator pass**

Run:
```bash
grep -rn " -- " plugins/mt5-trading/
```
Expected: 61 occurrences across 7 files. Classify each one:
- **List separator** (`` `file.md` -- description ``, `Symptom -- remedy`): replace ` -- ` with ` - `, matching `ibkr-trading`. Not a rule violation, a style divergence.
- **Bracketed aside** (a clause opened and closed by dashes): this is the actual `CLAUDE.md` violation. Rewrite into two sentences, parentheses, or delete the aside. Substituting `--` for `—` is not a fix and neither is substituting ` - `.

Do not batch-replace with a regex. The two cases need different treatment and only reading them distinguishes the two.

- [ ] **Step 4: Bump the version**

Set `mt5-trading` `version` to `1.2.0` in `.claude-plugin/marketplace.json`.

- [ ] **Step 5: Verify**

Run:
```bash
python scripts/lint_broker_plugins.py
grep -rn " -- " plugins/mt5-trading/ | wc -l
```
Expected: the linter prints `all broker plugins conform to the contract`; the grep count is 0.

- [ ] **Step 6: Commit**

```bash
git add plugins/mt5-trading .claude-plugin/marketplace.json
git commit -m "Bring mt5-trading to base level of the broker plugin contract"
```

---

### Task 5: Fact anchors and the CI wiring

**Files:**
- Modify: `scripts/lint_fact_anchors.py`
- Modify: `.github/workflows/consistency.yml`

**Interfaces:**
- Consumes: the vocabulary now stated in three places (generic plugin, `ibkr-trading`, `mt5-trading`).

- [ ] **Step 1: Add the anchors**

In the `ANCHORS` dict of `scripts/lint_fact_anchors.py`, add two entries owned by the generic plugin:

```python
    "broker-archetype-local-terminal": (
        "plugins/trading-broker-connectivity/skills/trading-broker-connectivity/"
        "references/access-archetypes.md",
        r"`(local-terminal)`",
        "canonical archetype name echoed by every local-terminal broker plugin",
    ),
    "evidence-ladder-ranks": (
        "plugins/trading-broker-connectivity/skills/trading-broker-connectivity/"
        "references/evidence-and-probes.md",
        r"ladder has \*\*(\w+) ranks\*\*",
        "the evidence ladder's rank count, stated in the generic plugin and in ibkr-trading",
    ),
```

The owning file must state each fact in the captured form, or the linter reports an orphan. Check the wording of the reference files written in Task 1 and adjust either the regex or the prose so they agree.

- [ ] **Step 2: Verify the anchors resolve**

Run: `python scripts/lint_fact_anchors.py --report`
Expected: both new anchors appear with a value, not `(not found)`. An orphan here means the regex does not match the prose that was actually written.

- [ ] **Step 3: Wire the linter into CI**

In `.github/workflows/consistency.yml`, after the `Fact anchor lint` step, insert:

```yaml
      - name: Broker plugin contract lint
        run: python scripts/lint_broker_plugins.py
```

The linter's unit tests need no new step: `python -m unittest discover -s tests -v` already runs everything under `tests/`.

- [ ] **Step 4: Run the whole suite locally**

Run:
```bash
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python -m unittest discover -s tests -v
python scripts/lint_plugin_registration.py
python scripts/lint_fact_anchors.py
python scripts/lint_broker_plugins.py
python .claude/skills/downstream-exports/scripts/check_export.py
```
Expected: all pass except possibly `check_export.py`, which Task 7 satisfies. If `lint_dependency_graph.py` fails, the generic plugin dispatched into a broker plugin somewhere: find the reference and turn it back into prose.

- [ ] **Step 5: Commit**

```bash
git add scripts/lint_fact_anchors.py .github/workflows/consistency.yml
git commit -m "Anchor the shared broker vocabulary and add the contract lint to CI"
```

---

### Task 6: Documentation

**Files:**
- Create: `docs/plugins/trading-broker-connectivity.md`
- Modify: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write the plugin documentation page**

`docs/plugins/trading-broker-connectivity.md`, following the shape of `docs/plugins/mt5-trading.md`: an H1, a blockquote with the marketplace description, then a `## Skills` section (no `## Agents` and no `## Commands` sections, because the plugin has neither) listing the skill and its four references.

- [ ] **Step 2: Update the README**

Add a row to the plugin table next to the two existing trading rows:

```markdown
| **[trading-broker-connectivity](docs/plugins/trading-broker-connectivity.md)** | Vendor-neutral broker integration vocabulary - access archetypes, order lifecycle, evidence ladder | 0 | 1 | 0 |
```

Then recount the badges rather than incrementing them. The plugins badge currently reads `40` while `marketplace.json` holds 41 plugins and the directory-tree comment says 41, so it is already stale by one and a blind increment would carry the error forward. Recount mechanically:

```bash
python -c "import json;d=json.load(open('.claude-plugin/marketplace.json',encoding='utf-8'));p=d['plugins'];print('plugins',len(p));print('agents',sum(len(x.get('agents',[])) for x in p));print('skills',sum(len(x.get('skills',[])) for x in p));print('commands',sum(len(x.get('commands',[])) for x in p))"
```
Set each of the four badges to the printed number. Update the `# 41 plugins total` comment in the directory tree and the `With 41 plugins installed` sentence to the new count.

- [ ] **Step 3: Update `CLAUDE.md`**

Three edits:
1. In the Build / CI section, change "Seven checks" to "Eight checks" and add a numbered entry for `lint_broker_plugins.py` describing what it checks and what it deliberately does not, in the voice of entries 1 to 4.
2. In the Repo workflows table, add a fifth row: `broker-plugin-contract` | Authoring or reviewing a plugin for a specific broker. Holds the two conformance levels, the declaration lines, and the describe-but-never-dispatch rule.
3. Add a short standing-policy paragraph recording the contract, the two levels with the reason they exist (a plugin that has not earned verification is visibly at base rather than silently non-compliant), and the constraint that the generic plugin never dispatches into a broker plugin.

- [ ] **Step 4: Verify**

Run: `python scripts/lint_bundled_paths.py`
Expected: pass. `CLAUDE.md` and `README.md` are not plugin bodies, so repository-relative paths in them are correct and expected.

- [ ] **Step 5: Commit**

```bash
git add docs/plugins/trading-broker-connectivity.md README.md CLAUDE.md
git commit -m "Document the broker connectivity plugin and record the contract as policy"
```

---

### Task 7: The VS Code export

**Files:**
- Create: `exports/vscode/trading-broker-connectivity/.github/skills/trading-broker-connectivity/SKILL.md` (adapted by hand)
- Create: `exports/vscode/trading-broker-connectivity/.github/skills/trading-broker-connectivity/references/*.md` (byte-copied by script)
- Modify: `exports/vscode/package.json` (regenerated)
- Modify: `exports/vscode/CHANGELOG.md`
- Modify: `exports/vscode/mt5-trading/...` and `exports/vscode/ibkr-trading/...` (adapted halves re-ported)

- [ ] **Step 1: Load the export skill**

Invoke the `downstream-exports` skill and follow it. It owns the source map, the four dispatch shapes, and the adaptations to re-apply. Do not improvise this task from the plan alone.

- [ ] **Step 2: Generate the mechanical half**

Run:
```bash
python scripts/mirror_export.py
python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py
```
Fix mode always exits 0, so a clean exit is not evidence of correctness. Inspect what it wrote.

- [ ] **Step 3: Hand-port the adapted half**

Every `SKILL.md` is adapted, not byte-copied: frontmatter rewritten, tool names renamed, namespaces stripped, dispatch rerouted. That covers the new plugin's `SKILL.md` and the two broker `SKILL.md` files changed in Tasks 3 and 4.

- [ ] **Step 4: Write the changelog section**

Add a `## 23.0.0` section to `exports/vscode/CHANGELOG.md` describing the new plugin, the contract, and the two plugin realignments. This must be in this commit: the release guard fails on a version with no section, and the version is computed rather than written.

- [ ] **Step 5: Verify the export**

Run:
```bash
python .claude/skills/downstream-exports/scripts/check_export.py
python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check
python scripts/mirror_export.py --check --since origin/master
python scripts/extension_release_notes.py 23.0.0
```
Expected: all pass. The third names any adapted file whose source moved without it, which is the failure a green structural check is compatible with.

- [ ] **Step 6: Commit**

```bash
git add exports/vscode
git commit -m "Mirror the broker connectivity plugin into the VS Code export"
```

- [ ] **Step 7: Final full verification before pushing**

Run every check in Task 5 Step 4, plus:
```bash
python scripts/check_version_bumps.py origin/master HEAD
```
Expected: all pass. Only then push.

---

## Self-Review

**Spec coverage.** Section 1 of the spec maps to Task 1; Section 2 to Task 2 Step 1; Section 3 to Task 2 Steps 2 to 6; Section 4 to Tasks 3 and 4; Section 5 to Tasks 1, 5, 6 and 7. Section 6 is phase 2 and deliberately has no task. The describe-but-never-dispatch constraint appears in the Global Constraints, in the contract text (Task 2 Step 1), and as a verification in Task 5 Step 4.

**Placeholders.** None. The two prose-heavy tasks specify exact headings, verbatim tables and acceptance checks rather than deferring content, and the note under File Structure states why the connecting prose is authored at execution time.

**Type consistency.** The declaration lines `**Contract level:**` and `**Archetype:**` match between the contract text, the linter regexes, the test fixture template, and Tasks 3 and 4. `broker_token()` is defined once in Task 2 and used by `check_structure` and `check_verified` in the same file. The archetype set and the level set are defined once, at the top of the linter, and echoed verbatim in Task 1's table.
