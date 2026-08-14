# Consolidating the broker plugins into one

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Merge `ibkr-trading`, `mt5-trading` and `trading-broker-connectivity` into a single plugin, `trading-broker-integration`, and delete the machinery that existed only to keep three separate plugins consistent.

**Architecture:** One plugin, several skills. The container is the existing `trading-broker-connectivity` renamed, absorbing the other two as skills alongside its own. Agents and commands move with them. The conformance contract, its linter, its tests and its CI step are deleted, because they coordinate independently authored plugins and there are no longer any.

**Spec:** `docs/superpowers/specs/2026-08-13-trading-broker-connectivity-design.md` (the phase this amends). Its "Raised after the phase shipped" section lists five open design questions; **three of them dissolve here** and that is a reason for this change rather than a coincidence. B (`verified` unreachable for two archetypes), C (a FIX engine fits no scope value) and D (who is bound by the contract) are all questions about a declaration system that this plan removes.

## Why, in one paragraph

The WH SelfInvest reconnaissance established that the durable unit of knowledge is the platform, not the broker: its Multi-Market account is contractually an Interactive Brokers account, its NanoTrader is a Fipertec product, its futures run over CQG. A broker that resells three platforms does not produce a plugin, it touches three. If the unit is not the broker, one plugin per broker is the wrong partition, and the contract, the archetype axis, the scope axis and the linter are all solving a problem we created by choosing it.

## Global Constraints

- **No dash-asides**: a clause bracketed between em dashes, double hyphens or spaced hyphens. Hyphenated compounds are fine.
- **Preserve content byte for byte where it moves.** This is a relocation, not a rewrite. The only content edits are the ones each task names.
- **`git mv`, not copy-and-delete**, so history follows the files.
- **Stage explicit paths.** Never `git add -A`.
- **Do not push.** Commit only.

## Naming

| Old | New |
|---|---|
| plugin `trading-broker-connectivity` | plugin `trading-broker-integration` |
| plugin `ibkr-trading` | skill `ibkr` inside it |
| plugin `mt5-trading` | skill `mt5` inside it |
| skill `trading-broker-connectivity` | skill `broker-vocabulary` inside it |
| `ibkr-trading:ibkr-architect` | `trading-broker-integration:ibkr-architect` |
| `mt5-trading:mt5-architect` | `trading-broker-integration:mt5-architect` |

Commands keep their own names (`ibkr-audit`, `ibkr-verify`, `mt5-audit`), since those are already vendor-prefixed and unambiguous inside one plugin.

---

### Task 1: The move

**Files:** everything under `plugins/ibkr-trading/` and `plugins/mt5-trading/`; the `trading-broker-connectivity` tree; `.claude-plugin/marketplace.json`.

- [ ] **Step 1: Rename the container and its skill**

```bash
git mv plugins/trading-broker-connectivity plugins/trading-broker-integration
git mv plugins/trading-broker-integration/skills/trading-broker-connectivity \
       plugins/trading-broker-integration/skills/broker-vocabulary
```

Update the skill's own `name:` frontmatter to `broker-vocabulary`.

- [ ] **Step 2: Move the two vendor plugins in**

```bash
git mv plugins/ibkr-trading/skills/ibkr-trading plugins/trading-broker-integration/skills/ibkr
git mv plugins/mt5-trading/skills/mt5-trading  plugins/trading-broker-integration/skills/mt5
git mv plugins/ibkr-trading/agents/ibkr-architect.md plugins/trading-broker-integration/agents/
git mv plugins/mt5-trading/agents/mt5-architect.md   plugins/trading-broker-integration/agents/
git mv plugins/ibkr-trading/commands/*.md plugins/trading-broker-integration/commands/
git mv plugins/mt5-trading/commands/*.md  plugins/trading-broker-integration/commands/
```

Then remove the now-empty `plugins/ibkr-trading/` and `plugins/mt5-trading/` directories. Update each moved skill's `name:` frontmatter to `ibkr` and `mt5`.

- [ ] **Step 3: Delete the coordination machinery**

```bash
git rm -r .claude/skills/broker-plugin-contract
git rm scripts/lint_broker_plugins.py tests/test_broker_plugins_lint.py
```

Remove the `Broker plugin contract lint` step from `.github/workflows/consistency.yml`.

Remove the three declaration lines (`**Contract level:**`, `**Archetype:**`, `**Scope:**`) from both vendor skills' `SKILL.md`. They declared conformance to a contract that no longer exists.

**Keep the mapping tables.** Inside one plugin, translating between a vendor's vocabulary and the reference model is what the plugin is for, rather than an intrusion into a vendor's file. That objection was about three plugins.

- [ ] **Step 4: Salvage the authoring checklist**

The contract is deleted, but the question it answered survives: what should a new vendor skill in this plugin contain? Add a short section to `skills/broker-vocabulary/SKILL.md` titled `## Adding a vendor skill`, naming the required sections (Quick start, Key decision points, Symptoms to entry points, Reference materials), the requirement to state provenance on load-bearing facts, and the requirement to map the vendor's order vocabulary onto the reference model.

Prose only, no levels, no declarations, no linter. Roughly fifteen lines. Read the deleted contract before writing it and keep what a human would actually use.

- [ ] **Step 5: Rewrite the marketplace entry**

Replace the three entries with one, keeping category `algotrading`, merging the keyword sets, and listing three skills (`broker-vocabulary`, `ibkr`, `mt5`), two agents, three commands. Version `2.0.0`, since this is a breaking restructure of an existing entry. `metadata.version` to `24.0.0`.

- [ ] **Step 6: Verify and commit**

```bash
python scripts/lint_plugin_registration.py
python scripts/lint_bundled_paths.py
python scripts/lint_dependency_graph.py
python -m unittest discover -s tests
```

Expect `lint_fact_anchors.py` to fail on moved owner paths; Task 2 fixes it. Everything else must pass.

---

### Task 2: References, anchors and the dependency rule

- [ ] **Step 1: Sweep the namespaces**

Five references to `ibkr-trading:` and `mt5-trading:` exist repo-wide outside the moved trees. Find and update them:

```bash
grep -rn "ibkr-trading\|mt5-trading" --include="*.md" --include="*.json" --include="*.py" . | grep -v "^./.superpowers\|^./exports\|^./docs/superpowers"
```

Distinguish a namespace reference (`ibkr-trading:agent-name`, which must change) from prose naming the old plugin in a historical statement (which must not).

- [ ] **Step 2: Re-point the fact anchors**

`scripts/lint_fact_anchors.py`'s two broker anchors name owner files by path. Both owners moved. Update the paths, run `--report`, and confirm both still resolve with no conflict and no orphan.

- [ ] **Step 3: Remove the forbidden edges**

`FORBIDDEN_EDGES` in `scripts/lint_dependency_graph.py` gained two entries forbidding the generic plugin from dispatching into the broker plugins. Those plugins no longer exist. Remove both entries and leave the pre-existing `codebase-xray` one untouched.

- [ ] **Step 4: Verify and commit**

The full suite, including `lint_fact_anchors.py`, must now pass.

---

### Task 3: Documentation

- [ ] **Step 1: `CLAUDE.md`**

The Build / CI section loses check 8 and returns to seven Python checks; renumber the packaging job. The Repo workflows table loses the `broker-plugin-contract` row and returns to four. The `## Broker plugin contract` standing-policy section is replaced by a much shorter one recording that broker knowledge lives in one plugin, why (the platform is the durable unit, with WH SelfInvest as the worked example), and that the contract and its linter were removed in this consolidation so nobody reintroduces them.

**Keep the phrase `the five archetypes`**: it is fact-anchored.

- [ ] **Step 2: `README.md` and `docs/plugins/`**

Merge three table rows into one. Recount the four badges with the command in the previous plan rather than adjusting them by hand. Merge the three `docs/plugins/*.md` pages into one and delete the other two.

- [ ] **Step 3: Verify and commit**

`python scripts/lint_fact_anchors.py` and `python scripts/lint_bundled_paths.py`.

---

### Task 4: The export

- [ ] **Step 1: Load `downstream-exports` and follow it.**

- [ ] **Step 2:** Delete the `exports/vscode/ibkr-trading/` and `exports/vscode/mt5-trading/` bundles, let the mirror script rebuild under the new plugin, and hand-adapt the four `SKILL.md` twins.

- [ ] **Step 3:** A `## 24.0.0` section in `exports/vscode/CHANGELOG.md` describing the consolidation and naming the removed plugins, since anyone tracking them needs to find out where they went.

- [ ] **Step 4: Verify**

```bash
python .claude/skills/downstream-exports/scripts/check_export.py
python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check
python scripts/mirror_export.py --check --since origin/master
python scripts/check_version_bumps.py origin/master HEAD
```

Then the whole consistency suite as a final gate. **Do not push.**
