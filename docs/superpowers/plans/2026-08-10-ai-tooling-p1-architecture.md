# ai-tooling P1 Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn ai-tooling from a plugin that knows a lot of volatile facts into one that knows which of its own facts it must not trust, and that preserves a prompt's behavior while optimizing it.

**Architecture:** Two independent redesigns in one plugin. `agent-sdk-builder` becomes a thin decision core plus five on-demand references, governed by a three-tier source-of-truth policy (installed SDK, then official docs, then bundled references). `prompt-engineer` gains a behavioral contract it extracts before rewriting and a semantic diff it reports after, an archetype-aware rubric that scores only the dimensions a given prompt actually wants, audit depth proportional to consequence, and a strict predicted/measured/verified vocabulary.

**Tech Stack:** Static markdown. No build step, no runtime. Verification is the repo's four stdlib-only Python checkers plus grep assertions.

## Global Constraints

- Source of truth for plugin content is `plugins/`; `exports/vscode/` is derived and mirrored in the same commit (`downstream-exports` skill, step 3 of the marketplace workflow).
- `agent-sdk-builder` is one of two bundles that deliberately keep Claude Code vocabulary. Never de-brand it, never rename its tool names. `check_export.py` excludes it; keep it that way.
- No dash-aside construct anywhere in new content: not `—`, not `--`, not ` - ` used to bracket a parenthetical clause. Rewrite into separate sentences, parentheses, or colons. Hyphenated compounds are fine.
- Bundled reference paths inside a skill are skill-relative (`references/foo.md`), matching every other skill in this marketplace. Cross-component paths in agents and commands use `${CLAUDE_PLUGIN_ROOT}/...`.
- Agent frontmatter: `model: inherit`, `color` from the allowed set, long `description` in YAML `>` form. `prompt-engineer` keeps `Read, Write, Edit, Glob, Grep` and does not regain `Bash`.
- Frozen non-goals from the approved backlog: no `commands/` to `skills/` migration, no per-plugin `plugin.json`, no change to the mandatory frontier behavior in `/prompt-optimize` (CRITICAL RULE 3 stands), no removal of `Write`/`Edit`, no unverified TodoWrite migration, no new agents.
- Deferred deliberately: the three-way split of `references/reasoning-patterns.md` into selection / catalog / evidence appeared in the review body but not in the frozen P1 backlog. Do not do it here. Task 7 leaves a note recording why.
- Marketplace bump discipline: `.claude-plugin/marketplace.json` is shared with other sessions. Before staging it, run `git diff -- .claude-plugin/marketplace.json` and confirm every hunk is yours. If a foreign hunk is present, stage only your own content (see Task 8, Step 3).

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md` | Decision core: what to inspect, how to choose, how to build, how to validate, what is dangerous, where the detail lives | Rewrite, 1068 lines to under 260 |
| `.../agent-sdk-builder/references/sdk-api.md` | Install, `query()`, options table, built-in tools, streaming, structured output, cost tracking, migration, V2 removal | Create |
| `.../agent-sdk-builder/references/sessions-subagents.md` | Sessions, forking, introspection, subagents, Python client methods | Create |
| `.../agent-sdk-builder/references/permissions-hooks-security.md` | Permission modes and order, `canUseTool`, hooks, security practices | Create |
| `.../agent-sdk-builder/references/mcp-plugins-skills.md` | In-process MCP tools, external MCP servers, loading plugins and settings | Create |
| `.../agent-sdk-builder/references/deployment.md` | Hosting shapes, sandbox isolation, worked end-to-end patterns | Create |
| `.../agent-sdk-builder/references/reasoning-patterns.md` | Unrelated: consumed by `prompt-engineer`, mirrored here for the export | Untouched |
| `plugins/ai-tooling/agents/prompt-engineer.md` | Behavioral contract, archetype rubric, audit depth, semantic diff, epistemic labels | Modify in four passes |
| `plugins/ai-tooling/commands/prompt-optimize.md` | Command surface; inherits the agent's new vocabulary | Modify once (Task 6) |
| `exports/vscode/ai-tooling/.github/**` | Derived mirror | Mirror in Task 8 |

Section-to-reference mapping for the split, by the current `## N.` numbering of `SKILL.md`:

| Current sections | Destination |
|---|---|
| 1 Installation, 2 Core API, 3 Configuration Options, 4 Built-in Tools, 11 Streaming, 12 Structured Output, 14 Cost Tracking, 18 Migration, 19 V2 removed | `references/sdk-api.md` |
| 6 Subagents, 7 Session Management, 8 Introspection, 20 ClaudeSDKClient Methods | `references/sessions-subagents.md` |
| 9 Permissions, 10 Hooks, 16 Security Best Practices | `references/permissions-hooks-security.md` |
| 5 Custom Tools via MCP, 13 Plugins and Skills | `references/mcp-plugins-skills.md` |
| 15 Hosting & Deployment, 17 Common Patterns | `references/deployment.md` |
| Quick Reference, Official Resources, the version-sensitivity note | Stay in `SKILL.md` |

---

### Task 1: Split agent-sdk-builder into five references

Pure content move. No sentence is rewritten in this task except the H2 renumbering. The point of keeping it mechanical is that Task 2 can then be reviewed as new writing, and this task can be reviewed as "nothing was lost".

**Files:**
- Create: `plugins/ai-tooling/skills/agent-sdk-builder/references/sdk-api.md`
- Create: `plugins/ai-tooling/skills/agent-sdk-builder/references/sessions-subagents.md`
- Create: `plugins/ai-tooling/skills/agent-sdk-builder/references/permissions-hooks-security.md`
- Create: `plugins/ai-tooling/skills/agent-sdk-builder/references/mcp-plugins-skills.md`
- Create: `plugins/ai-tooling/skills/agent-sdk-builder/references/deployment.md`
- Read only this task: `plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md` (do not modify it yet)

**Interfaces:**
- Produces: five reference files, each opening with an H1 title and a one-line scope statement, then the moved sections renumbered from 1 within that file. Task 2 links to them by exact filename.
- Consumes: nothing.

- [ ] **Step 1: Snapshot the section inventory**

```bash
grep -n '^## ' plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md \
  > "$SCRATCH/sections-before.txt"
cat "$SCRATCH/sections-before.txt"
```

Use your scratchpad directory for `$SCRATCH`. Expect 24 H2 lines: `Quick Reference`, `1.` through `20.`, and `Official Resources`.

- [ ] **Step 2: Create `references/sdk-api.md`**

Header, then sections 1, 2, 3, 4, 11, 12, 14, 18, 19 moved verbatim and renumbered 1 through 9 in that order.

```markdown
# Agent SDK: core API

Installation, the `query()` entry point, the full options table, built-in tools, streaming,
structured output, cost tracking, and the migration from `claude-code-sdk`.

Option shapes and tool names in this file are API-sensitive. Resolve them against the project's
installed SDK or https://code.claude.com/docs/en/agent-sdk/ before emitting code, per the
source-of-truth policy in `SKILL.md`. Entries marked *(verify)* failed documentation
resolution at the last refresh and are unconfirmed.
```

- [ ] **Step 3: Create `references/sessions-subagents.md`**

Header, then sections 6, 7, 8, 20 moved verbatim and renumbered 1 through 4.

```markdown
# Agent SDK: sessions and subagents

Multi-turn sessions, resuming, forking, session metadata, introspection, subagent definitions
and behavior, and the Python `ClaudeSDKClient` runtime methods.

Method names and option shapes here are API-sensitive: resolve them against the installed SDK
or the current documentation before use, per the source-of-truth policy in `SKILL.md`.
```

- [ ] **Step 4: Create `references/permissions-hooks-security.md`**

Header, then sections 9, 10, 16 moved verbatim and renumbered 1 through 3. The three-mechanism table and the "Do not use `canUseTool` as an always-on security interceptor" rule move with section 16 and stay intact.

```markdown
# Agent SDK: permissions, hooks, and security

Permission modes, the evaluation order, the `canUseTool` fallback, the hook events and their
matchers, and the security practices that follow from all three.

The one rule to carry out of this file: coarse policy is `allowedTools`/`disallowedTools`/
`permissionMode`, always-on enforcement is a `PreToolUse` hook, and `canUseTool` is only the
interactive fallback for calls nothing earlier resolved.
```

- [ ] **Step 5: Create `references/mcp-plugins-skills.md`**

Header, then sections 5 and 13 moved verbatim and renumbered 1 and 2.

```markdown
# Agent SDK: custom tools, MCP servers, plugins and skills

Defining your own tools as in-process MCP servers, connecting external MCP servers over stdio
and HTTP, the `mcp__<server>__<tool>` naming convention, and loading Claude Code plugins and
filesystem settings into an SDK run.
```

- [ ] **Step 6: Create `references/deployment.md`**

Header, then sections 15 and 17 moved verbatim and renumbered 1 and 2.

```markdown
# Agent SDK: deployment and worked patterns

Ephemeral versus long-running session hosting, custom process spawning, sandbox isolation, and
three end-to-end patterns: a CI/CD review agent, a multi-agent research pipeline, and an
interactive chat loop.
```

- [ ] **Step 7: Verify nothing was lost**

Write this checker to your scratchpad and run it from the repo root. It compares the body text of the pre-split `SKILL.md` at HEAD against the concatenation of the five new files, ignoring headers and blank lines, and reports any content line that vanished.

```python
# $SCRATCH/check_split.py
import re, subprocess, pathlib

SKILL = "plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md"
REFS = ["sdk-api", "sessions-subagents", "permissions-hooks-security",
        "mcp-plugins-skills", "deployment"]
BASE = pathlib.Path("plugins/ai-tooling/skills/agent-sdk-builder/references")

# Lines that legitimately stay behind in the core or are headers we renumbered.
KEEP_IN_CORE = re.compile(r"^(#|\|\s*\*?\*?(TypeScript|Package|Install|Auth|Core function|GitHub)|"
                          r"- \[.*\]\(https://code\.claude\.com|The CLI package|\*\*Key distinction)")

old = subprocess.run(["git", "show", f"HEAD:{SKILL}"],
                     capture_output=True, text=True, check=True).stdout
new = "\n".join((BASE / f"{r}.md").read_text(encoding="utf-8") for r in REFS)

def body(text):
    return {ln.strip() for ln in text.splitlines()
            if ln.strip() and not ln.startswith("#") and not KEEP_IN_CORE.match(ln)}

missing = sorted(body(old) - body(new))
print(f"{len(missing)} line(s) present before the split and absent after")
for ln in missing[:40]:
    print("  MISSING:", ln[:110])
```

Run: `python "$SCRATCH/check_split.py"`
Expected: `0 line(s)`. Any other number means a section was dropped in the move. Fix it before continuing; do not proceed with a non-zero count.

- [ ] **Step 8: Commit**

```bash
git add plugins/ai-tooling/skills/agent-sdk-builder/references/
git commit -m "Split agent-sdk-builder detail into five on-demand references

Pure content move, no rewriting. Sections 1-20 of SKILL.md are
redistributed by subject so the core can become a decision layer in
the next commit."
```

---

### Task 2: Rewrite the agent-sdk-builder core as a resolver

The core stops being an encyclopedia. It answers: which language and version am I on, which shape does this need, where is the detail, and which of my own claims must I not trust.

**Files:**
- Modify: `plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md` (full rewrite of the body; frontmatter unchanged)

**Interfaces:**
- Consumes: the five reference filenames created in Task 1.
- Produces: the phrase `source-of-truth policy` and the three tier names, which the references in Task 1 already point back to.

- [ ] **Step 1: Replace the body, keeping the frontmatter**

The frontmatter block (lines 1 through 7, `name` / `description`) is unchanged. Everything after it becomes:

````markdown
# Claude Agent SDK

Build applications that run the Claude Code agent loop programmatically: agents that read files,
write code, run commands, search the web, and delegate to subagents from inside your own program.

**Key distinction**: the Agent SDK (`claude-agent-sdk`) runs the full agent loop with built-in
tools. The Anthropic Client SDK (`anthropic`) makes raw API calls. Use the Agent SDK when you
want an autonomous tool-using agent, not a chat completion.

| | TypeScript | Python |
|---|---|---|
| **Package** | `@anthropic-ai/claude-agent-sdk` | `claude-agent-sdk` |
| **Install** | `npm install @anthropic-ai/claude-agent-sdk` | `pip install claude-agent-sdk` |
| **Auth** | `ANTHROPIC_API_KEY` env var | `ANTHROPIC_API_KEY` env var |
| **Entry point** | `query()` | `query()` |
| **Source** | `anthropics/claude-agent-sdk-typescript` | `anthropics/claude-agent-sdk-python` |

The CLI package `@anthropic-ai/claude-code` ships inside the SDK. No separate install.

---

## Source of truth

This SDK changes faster than any bundled document. Option shapes, tool names, defaults, and
whole features move between releases: `fork_session` changed type, `plugins` changed from paths
to config objects, and the TypeScript V2 preview was removed outright. Treat this skill's
knowledge as orientation, never as the authority.

Three tiers. Stop at the first one that answers the question:

1. **The project's installed SDK.** TypeScript: the type definitions under
   `node_modules/@anthropic-ai/claude-agent-sdk/` and its `package.json` version. Python: the
   installed package under `site-packages/claude_agent_sdk/`, or `inspect.signature()` on the
   symbol. This tier wins over everything else, because it is what the user's code will run
   against.
2. **Current official documentation**, https://code.claude.com/docs/en/agent-sdk/. Use it when
   nothing is installed yet, or when the question is about behavior rather than a signature.
3. **The references in this skill.** Worked examples and orientation. Never the last word on a
   signature, an option shape, a default, or whether a feature still exists.

Classify a claim before you rely on it:

| Class | Example | Resolve with |
|---|---|---|
| STABLE | "Restrict `allowedTools` to what the task needs." | This skill |
| API-SENSITIVE | "`forkSession` is a boolean used with `resume`." | Tier 1, then tier 2 |
| MODEL-SENSITIVE | "This model id and effort level exist." | Tier 2 |

Never emit API-sensitive code from memory when tier 1 or tier 2 can settle it. Items marked
*(verify)* in the references are the ones that failed tier-2 resolution at the last refresh:
they are unconfirmed, not confirmed-absent, and checking them is cheap.

---

## Step 1: Detect the environment

Do this before writing a line of code, and state what you found.

- **Language.** `package.json` naming `@anthropic-ai/claude-agent-sdk` means TypeScript.
  `pyproject.toml`, `requirements.txt`, or `uv.lock` naming `claude-agent-sdk` means Python.
- **Installed version.** `npm ls @anthropic-ai/claude-agent-sdk` or `pip show claude-agent-sdk`.
  Record it: every API-sensitive answer you give is relative to that version.
- **Nothing installed.** Say so, install the current release, and resolve signatures from tier 2.
- **Version pinned below current.** Honor the pin. Resolve against the installed types, and if
  the user asks for a feature that release does not have, say which version added it instead of
  emitting code that cannot run.

## Step 2: Pick the shape

| Need | Shape | Reference |
|---|---|---|
| One task, run to completion | `query()` | `references/sdk-api.md` |
| Multi-turn with retained context | `ClaudeSDKClient` (Python), or `query()` with `resume` | `references/sessions-subagents.md` |
| Branch a conversation without mutating it | `resume` plus `forkSession` | `references/sessions-subagents.md` |
| Delegate specialized work | `agents` plus the `Agent` tool | `references/sessions-subagents.md` |
| Give the agent your own functions | in-process MCP server | `references/mcp-plugins-skills.md` |
| Reuse existing Claude Code plugins | `plugins` and `settingSources` | `references/mcp-plugins-skills.md` |
| A machine-readable result | `outputFormat` with a JSON schema | `references/sdk-api.md` |
| Coarse "what may it use at all" | `allowedTools` / `disallowedTools` / `permissionMode` | `references/permissions-hooks-security.md` |
| A rule that must hold on every call | `PreToolUse` hook | `references/permissions-hooks-security.md` |
| Decide unresolved requests in code | `canUseTool` | `references/permissions-hooks-security.md` |
| Run untrusted work | sandbox and container isolation | `references/deployment.md` |
| Ship it somewhere | ephemeral or long-running hosting | `references/deployment.md` |

Load only the reference the chosen row names. Loading all five defeats the point.

## Step 3: Security model

Three mechanisms, three jobs. Substituting one for another is the most common way an SDK
application ends up with security that does not run:

| Mechanism | Job |
|---|---|
| `allowedTools` / `disallowedTools` / `permissionMode` | Coarse policy: what the agent may use at all |
| `PreToolUse` hook | Always-on enforcement: runs for every matching call, before permission resolution |
| `canUseTool` | Interactive fallback: runs only for calls no rule, mode, or hook already resolved |

**A validation rule that must always hold belongs in a `PreToolUse` hook.** Anything you
allow-list never reaches `canUseTool`, so a check placed there stops running the moment the tool
is approved, silently. `disallowedTools` is the only hard block and outranks even
`bypassPermissions`. Details and worked examples: `references/permissions-hooks-security.md`.

Also standing: set `maxTurns` and `maxBudgetUsd` on anything autonomous, keep secrets out of
prompts (`env` or an MCP tool instead), and isolate untrusted work in a container.

## Step 4: Build and validate

1. Write the smallest program that does the job. Resist adding options you have not verified.
2. Resolve every API-sensitive detail against tier 1, then tier 2.
3. Type-check where the project supports it (`tsc --noEmit`, or the project's type checker).
4. Run it once on a cheap prompt with `maxTurns` and `maxBudgetUsd` set low, before running it
   for real.
5. Report which facts came from the installed SDK, which from the documentation, and name
   anything you could not verify. A named gap is useful; a confident guess is not.

---

## References

| File | Holds |
|---|---|
| `references/sdk-api.md` | Install, `query()`, full options table, built-in tools, streaming, structured output, cost tracking, migration from `claude-code-sdk` |
| `references/sessions-subagents.md` | Sessions, resume, fork, session metadata, introspection, subagent definitions, Python client methods |
| `references/permissions-hooks-security.md` | Permission modes and evaluation order, `canUseTool`, hook events and matchers, security practices |
| `references/mcp-plugins-skills.md` | Custom tools as in-process MCP servers, external MCP servers, loading plugins and settings |
| `references/deployment.md` | Hosting shapes, sandbox isolation, CI/CD review agent, research pipeline, chat loop |

`references/reasoning-patterns.md` in this directory belongs to the `prompt-engineer` agent, not
to the SDK. It is here because the VS Code export mirrors plugin-root references into the
consuming skill directory.

## Official documentation

- [Overview](https://code.claude.com/docs/en/agent-sdk/overview)
- [TypeScript reference](https://code.claude.com/docs/en/agent-sdk/typescript)
- [Python reference](https://code.claude.com/docs/en/agent-sdk/python)
- [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)
- [Hooks](https://code.claude.com/docs/en/agent-sdk/hooks)
- [Sessions](https://code.claude.com/docs/en/agent-sdk/sessions)
- [Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)
- [Custom tools and MCP](https://code.claude.com/docs/en/agent-sdk/custom-tools)
- [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)
- [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- [Migration guide](https://code.claude.com/docs/en/agent-sdk/migration-guide)
- [Demo apps](https://github.com/anthropics/claude-agent-sdk-demos)
````

- [ ] **Step 2: Verify the size and the links**

```bash
wc -l plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md
for f in sdk-api sessions-subagents permissions-hooks-security mcp-plugins-skills deployment; do
  test -f "plugins/ai-tooling/skills/agent-sdk-builder/references/$f.md" \
    && grep -q "references/$f.md" plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md \
    && echo "ok   $f" || echo "FAIL $f"
done
grep -c 'platform\.claude\.com' plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md
```

Expected: line count under 260. Five `ok` lines. Zero `platform.claude.com` hits (the count command prints `0`).

- [ ] **Step 3: Verify no dash-asides entered the new prose**

```bash
grep -nE ' -- | — ' plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md
```

Expected: no output. Any hit is a house-style violation in text you just wrote; rewrite the sentence.

- [ ] **Step 4: Commit**

```bash
git add plugins/ai-tooling/skills/agent-sdk-builder/SKILL.md
git commit -m "Rewrite agent-sdk-builder core as a version-aware resolver

1068 lines to ~230. The core now holds the source-of-truth policy
(installed SDK, then current docs, then bundled references), the
claim-classification table, environment detection, the shape decision
tree, the three-mechanism security model, and the build-and-validate
workflow. Every volatile detail moved to the references in the
previous commit and is loaded on demand."
```

---

### Task 3: Give prompt-engineer a behavioral contract and a semantic diff

The failure mode this prevents: an optimizer that returns a prettier prompt that no longer does the same thing. Extraction happens before the rewrite, the diff after.

**Files:**
- Modify: `plugins/ai-tooling/agents/prompt-engineer.md` (insert two new blocks; edit `<prompt_audit_process>`)

**Interfaces:**
- Produces: the block names `<behavioral_contract>` and `<semantic_diff>`, referenced by Task 5's audit-depth ladder and by Task 6's command wiring.

- [ ] **Step 1: Insert `<behavioral_contract>` before `<prompt_design_framework>`**

Insert immediately after the closing `</reasoning_patterns_library>` tag:

```xml
<behavioral_contract>
Before rewriting any existing prompt, extract its contract. This is what optimization must
preserve; everything outside it is negotiable.

- **Goal** - the behavior the prompt must produce, in one sentence.
- **Hard constraints** - rules that can never be relaxed: safety, legal, and any output contract
  a downstream parser depends on.
- **Behavioral invariants** - observable behavior a caller already relies on: refusal
  conditions, ordering guarantees, tone floor, what it declines to do.
- **Interface** - inputs, outputs, schemas, tool names, variable placeholders. Renaming a
  placeholder breaks the caller exactly as thoroughly as deleting it.
- **Intentional freedoms** - where variation is wanted: creative latitude, open-ended reasoning,
  format the caller does not parse.
- **Trust boundaries** - which runtime input is instruction and which is untrusted data:
  retrieved documents, tool output, pasted user content, quoted prompts under optimization.
- **Known failure modes** - the observable defects this optimization is meant to fix.

Two rules follow. Never resolve an ambiguous goal silently: state the reading you optimized for.
Never treat an unstated freedom as a defect: absence of a constraint is not automatically a gap
to fill, and filling it changes behavior.
</behavioral_contract>
```

- [ ] **Step 2: Insert `<semantic_diff>` immediately after `<behavioral_contract>`**

```xml
<semantic_diff>
After rewriting, report what changed in behavior, not in wording. Print only the lines that are
true; omit the rest rather than padding with "unchanged".

```
Constraints:  strengthened | relaxed: <which>
Behaviors:    removed: <what> | added: <what>
Interface:    changed: <old> -> <new>
Tool policy:  changed: <what>
Reasoning:    changed: <what>
Trust:        hardened: <what> | weakened: <what>
```

If every line would read "unchanged", say "No behavioral change: wording, structure, and token
count only." That is a real and good result, not a failure to find something.

Any relaxed, removed, weakened, or changed line is a behavior change the caller has to approve.
Lead with it. Never bury it under a token saving, and never let a rubric score stand in for it:
a prompt can score higher and still have stopped doing its job.
</semantic_diff>
```

- [ ] **Step 3: Rewrite `<prompt_audit_process>` so it does not compete with the contract**

Replace the whole existing block with:

```xml
<prompt_audit_process>
When reviewing an existing prompt:

1. **Extract the contract** - `<behavioral_contract>`. This comes first; everything downstream
   depends on it.
2. **Classify** - purpose, target model class, archetype (see `<evaluation_rubric>`).
3. **Decompose** - persona, instructions, constraints, examples, format.
4. **Diagnose** - anti-patterns from `<anti_patterns>`, plus the failure modes named in the
   contract. Diagnose against the archetype, not against a generic ideal.
5. **Rewrite** - preserving the contract.
6. **Diff** - `<semantic_diff>`. Any behavior change gets surfaced, not summarized away.
7. **Score** - the applicable rubric dimensions only, as a diagnostic.
8. **Recommend validation** - the eval that would turn the prediction into a measurement.
</prompt_audit_process>
```

- [ ] **Step 4: Verify the blocks exist and are well formed**

```bash
grep -c '<behavioral_contract>\|</behavioral_contract>\|<semantic_diff>\|</semantic_diff>' \
  plugins/ai-tooling/agents/prompt-engineer.md
grep -n 'Extract the contract' plugins/ai-tooling/agents/prompt-engineer.md
```

Expected: `4` (both tags, opened and closed once each), and one hit for the audit-process step 1.

- [ ] **Step 5: Commit**

```bash
git add plugins/ai-tooling/agents/prompt-engineer.md
git commit -m "prompt-engineer: extract a behavioral contract, report a semantic diff

Optimization now starts by naming the goal, hard constraints,
invariants, interface, intentional freedoms, trust boundaries and
known failure modes, and ends by reporting behavior changes rather
than only token deltas. The audit process is rewired around both."
```

---

### Task 4: Make the rubric archetype-aware

A universal rubric rewards the wrong things. Maximum output determinism is correct for an extractor and actively harmful for a creative prompt. The fix is to classify first and score only what the archetype wants.

**Files:**
- Modify: `plugins/ai-tooling/agents/prompt-engineer.md` (replace `<evaluation_rubric>`)

**Interfaces:**
- Consumes: `<behavioral_contract>` from Task 3 (the archetype is classified during audit step 2).
- Produces: the dimension names used by Task 5's deep-pass ladder.

- [ ] **Step 1: Replace the entire `<evaluation_rubric>` block**

```xml
<evaluation_rubric>
## 1. Classify the archetype first

| Archetype | Typical instance |
|---|---|
| extraction / classification | pull fields from a document, label a ticket |
| structured generation | emit JSON, fill a fixed report template |
| creative / generative | copy, fiction, naming, brainstorming |
| reasoning | analysis, diagnosis, math, planning |
| agentic / tool-use | an agent loop that calls tools |
| judge / evaluator | LLM-as-judge, scoring a candidate output |
| system policy | a system prompt governing a product surface |
| meta-prompt | a prompt whose output is another prompt |

## 2. Score only the dimensions that archetype wants

| Dimension | 1 (poor) | 3 (adequate) | 5 (excellent) | Applies to |
|---|---|---|---|---|
| **Intent alignment** | solves a different problem | mostly on target | exactly the stated goal | all |
| **Instruction clarity** | multiple readings | minor ambiguity | one reading only | all |
| **Constraint correctness** | contradictory or wrong | mostly right | every rule needed, none conflicting | all |
| **Model fit** | written for another model class | workable | matched to this model's defaults | all |
| **Context efficiency** | redundant, bloated | some slack | dense, nothing wasted | all |
| **Robustness** | breaks on unusual input | handles common variation | graceful on adversarial and edge input | all but throwaway one-offs |
| **Output determinism** | different shape each run | mostly stable | identical structure every run | only when something parses the output |
| **Tool-use correctness** | tools underspecified | usable descriptions | unambiguous names, triggers calibrated | agentic only |
| **Trust boundaries** | data can issue instructions | partial separation | data and instructions fully separated | only when untrusted input reaches the prompt |
| **Evalability** | untestable | some assertions possible | concrete pass/fail criteria | production prompts |
| **Creative latitude** | over-constrained to boilerplate | some room | room to vary where variation is wanted | generative archetypes |

Mark every other dimension `N/A` with a short clause saying why.

## 3. Scoring rules

- Score against the archetype, never against a generic ideal. Forcing identical structure onto a
  creative prompt or maximum specificity onto an exploratory one makes the prompt worse while
  making the score look better.
- The target is the right profile, not 5/5 everywhere. Say so when a dimension is deliberately
  left mid-scale.
- Flag anti-patterns from `<anti_patterns>` separately: they are defects, not scores.
- These scores are diagnostic. They locate weaknesses. They do not demonstrate improvement, and
  a before/after score pair is not evidence. See `<epistemic_status>`.
- Revise before presenting when an applicable dimension sits below 4 and the archetype wants it
  high. Do not revise to raise a dimension the archetype does not want.
</evaluation_rubric>
```

- [ ] **Step 2: Verify the dimension names are consistent across the file**

```bash
grep -n 'Output Consistency\|Specificity\|Completeness' plugins/ai-tooling/agents/prompt-engineer.md
```

Expected: no output. Those are the retired dimension names from the old rubric; any survivor is a stale reference to a dimension that no longer exists.

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-tooling/agents/prompt-engineer.md
git commit -m "prompt-engineer: archetype-aware rubric with N/A dimensions

Eight archetypes, eleven dimensions, five of them conditional. Scoring
a creative prompt on output determinism or an exploratory one on
maximum specificity rewarded the wrong shape; the rubric now scores
only what the prompt's function actually wants and marks the rest N/A."
```

---

### Task 5: Replace mandatory self-evaluation with adaptive audit depth

The current instruction runs the full rubric plus every anti-pattern check before any output, including for an eighty-token throwaway. That is both expensive and a source of overthinking on modern models.

**Files:**
- Modify: `plugins/ai-tooling/agents/prompt-engineer.md` (replace the `## Mandatory Self-Evaluation` subsection inside `<operating_instructions>`)

**Interfaces:**
- Consumes: `<behavioral_contract>` and `<semantic_diff>` from Task 3, the archetype table from Task 4.

- [ ] **Step 1: Replace the `## Mandatory Self-Evaluation` subsection**

Everything from the `## Mandatory Self-Evaluation` heading down to (not including) `## Output Formats` becomes:

```markdown
## Audit depth

Match effort to consequence. Decide once, before starting, and name which pass you ran.

**Quick pass.** Single-turn, no tools, no untrusted input, no production consumer, cheap to get
wrong: extract the contract, diagnose the defects, rewrite, confirm the contract survived. Skip
the archetype table, skip the full rubric, skip the reference reads.

**Deep pass.** Any one of these is enough to require it: it is a system or developer prompt, it
drives an agent or tool loop, it ships to production, a consumer parses its output, it handles
untrusted input, or a regression is expensive.

1. Contract (`<behavioral_contract>`)
2. Archetype (`<evaluation_rubric>` step 1)
3. Failure analysis: anti-patterns, plus the failure modes the contract named
4. Load only the references this task needs (reasoning patterns, evals)
5. Rewrite
6. Semantic diff (`<semantic_diff>`)
7. Rubric on applicable dimensions only
8. Eval recommendation

One question settles the choice: **if this prompt regresses, who finds out?** If the answer is
"a user, in production", run the deep pass.

Two rules bind both passes. Never add a reasoning pattern for completeness: check the model class
first, and record the decision when you decide against one. Never present a rewrite whose
contract you have not re-checked.
```

- [ ] **Step 2: Verify the old instruction is gone and the new one is wired**

```bash
grep -n 'Mandatory Self-Evaluation\|Before outputting ANY' plugins/ai-tooling/agents/prompt-engineer.md
grep -n 'Audit depth\|Quick pass\|Deep pass' plugins/ai-tooling/agents/prompt-engineer.md
```

Expected: no output from the first command. Three or more hits from the second.

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-tooling/agents/prompt-engineer.md
git commit -m "prompt-engineer: audit depth proportional to consequence

The mandatory full-rubric pass ran identically for an eighty-token
throwaway and a production system prompt. Quick and deep passes now
split on a single test: if this prompt regresses, who finds out."
```

---

### Task 6: Separate predicted, measured, and verified

A self-assigned score is a prediction. Today the agent and the command can both let a number read as a measurement.

**Files:**
- Modify: `plugins/ai-tooling/agents/prompt-engineer.md` (add `<epistemic_status>`; reconcile the `## Parity Claims` subsection; adjust `## Output Formats`)
- Modify: `plugins/ai-tooling/commands/prompt-optimize.md` (scorecard heading, comparison table, honesty note)

**Interfaces:**
- Consumes: the rubric from Task 4 (its scores are labeled predicted), the semantic diff from Task 3.

- [ ] **Step 1: Add `<epistemic_status>` immediately before `<prompt_evals>`**

```xml
<epistemic_status>
Three words, never interchangeable. Label every claim about prompt quality with one of them:

- **Predicted** - your own judgment. Every rubric score, every parity estimate, every "this
  should be more reliable" produced in a single pass is predicted. Say the word out loud; do not
  let a number imply more.
- **Measured** - an eval was actually run. Report the method with the number: identical inputs
  per variant, the grader used, the sample size.
- **Verified** - measured, plus an independent check: a held-out set, a judge from a different
  model family, or human review.

"Reliability improved 30%" without a run is a false claim, not an optimistic one. The honest form
names the mechanism instead: "predicted: fewer malformed outputs, because the schema is now
stated before the task rather than after it."

Rubric scores are diagnostic. They locate weaknesses. A before/after score pair written by the
same model that wrote the rewrite is not evidence that the rewrite is better, and formatting
changes alone are known to swing task accuracy, so a single side-by-side comparison is noise.
</epistemic_status>
```

- [ ] **Step 2: Reconcile `## Parity Claims` so it points at the new block**

In `<optimization_techniques>`, replace the second bullet of `## Parity Claims` with:

```markdown
- Without an eval run, parity is predicted, never measured or verified: see `<epistemic_status>`
  for the three labels and what each one requires
```

Leave the other three bullets of that subsection as they are. They carry the model-class and
shot-regime caveats, which the new block does not duplicate.

- [ ] **Step 3: Relabel the optimization report in `## Output Formats`**

Replace the `**Optimization report**` bullet with:

```markdown
- **Optimization report** - token estimates before and after (state the estimation method), each
  quality claim labeled predicted, measured, or verified per `<epistemic_status>`, the semantic
  diff, and risk notes
```

- [ ] **Step 4: Apply the same vocabulary to the command**

Three edits in `plugins/ai-tooling/commands/prompt-optimize.md`:

Rename the scorecard heading so it cannot read as a performance measurement:

```
### Diagnostic Scorecard (original, predicted)
```

Rename the comparison column:

```
| Variant | Tokens (est.) | Delta vs original | Technique applied | Predicted gains | What you give up |
```

becomes

```
| Variant | Tokens (est.) | Delta vs original | Technique applied | Predicted effect (unmeasured) | What you give up |
```

And add one line to the `### Honesty note` list, after the existing first bullet:

```
    - Label every quality claim predicted, measured, or verified. A score this pass assigned is
      predicted by definition, including the scorecard above.
```

- [ ] **Step 5: Verify both files carry the vocabulary and the command's frontier rule is untouched**

```bash
grep -c 'predicted\|Predicted' plugins/ai-tooling/agents/prompt-engineer.md
grep -n 'Diagnostic Scorecard\|Predicted effect' plugins/ai-tooling/commands/prompt-optimize.md
grep -n 'Show the frontier' plugins/ai-tooling/commands/prompt-optimize.md
grep -n '<analysis>' plugins/ai-tooling/commands/prompt-optimize.md
```

Expected: several hits in the agent. Two hits in the command for the renamed labels. CRITICAL RULE 3 (`Show the frontier`) still present and unmodified, because changing it is a frozen non-goal. Zero `<analysis>` hits, confirming the P0 fix from 4.2.0 did not regress.

- [ ] **Step 6: Commit**

```bash
git add plugins/ai-tooling/agents/prompt-engineer.md plugins/ai-tooling/commands/prompt-optimize.md
git commit -m "ai-tooling: separate predicted, measured and verified claims

A self-assigned rubric score is a prediction. The agent gains an
epistemic-status block, the parity guidance points at it instead of
restating it, and the command renames its scorecard and comparison
column so a single-pass estimate can no longer read as a measurement."
```

---

### Task 7: Record the deferred reasoning-patterns split

One item from the review body did not make the frozen backlog. Recording why keeps the next pass from either re-litigating it or silently doing it.

**Files:**
- Modify: `plugins/ai-tooling/references/reasoning-patterns.md` (one paragraph after the H1 intro)

- [ ] **Step 1: Add the maintenance note after the opening paragraph**

```markdown
> **Maintenance note.** This file mixes three kinds of content with different shelf lives:
> selection policy (stable), the pattern catalog (slow-moving), and empirical results (dated,
> model-specific). Splitting it into selection / catalog / evidence was considered in the
> 2026-08-10 review and deliberately deferred: the selection cheat sheet and the reasoning-model
> section are the parts actually read on most invocations, and they are already at the top. If
> the empirical numbers below start driving decisions on their own, that is the signal to split
> and to date each result.
```

- [ ] **Step 2: Verify placement**

```bash
head -12 plugins/ai-tooling/references/reasoning-patterns.md
```

Expected: the note sits after the H1 and its intro line, before `## Selection cheat sheet`.

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-tooling/references/reasoning-patterns.md
git commit -m "Record why the reasoning-patterns split was deferred"
```

---

### Task 8: Mirror to the VS Code export, bump, verify, push

The export is derived. The SDK skill body is a byte-copy under export frontmatter; the agent and the command are adapted, so they need the adaptation table applied rather than a blind copy.

**Files:**
- Create: `exports/vscode/ai-tooling/.github/skills/agent-sdk-builder/references/{sdk-api,sessions-subagents,permissions-hooks-security,mcp-plugins-skills,deployment}.md`
- Modify: `exports/vscode/ai-tooling/.github/skills/agent-sdk-builder/SKILL.md`
- Modify: `exports/vscode/ai-tooling/.github/agents/prompt-engineer.agent.md`
- Modify: `exports/vscode/ai-tooling/.github/prompts/prompt-optimize.prompt.md`
- Modify: `exports/vscode/ai-tooling/.github/skills/agent-sdk-builder/references/reasoning-patterns.md`
- Modify: `.claude-plugin/marketplace.json`, `exports/vscode/package.json`, `exports/vscode/CHANGELOG.md`

- [ ] **Step 1: Mirror the skill and its references**

The five new reference files are byte-copies. The `SKILL.md` body is a byte-copy spliced under the export's own frontmatter, which stays exactly as it is.

```bash
SRC=plugins/ai-tooling/skills/agent-sdk-builder
DST=exports/vscode/ai-tooling/.github/skills/agent-sdk-builder
cp "$SRC"/references/{sdk-api,sessions-subagents,permissions-hooks-security,mcp-plugins-skills,deployment}.md "$DST/references/"
```

Then splice the body of `$SRC/SKILL.md` under the existing frontmatter of `$DST/SKILL.md`, keeping that frontmatter byte for byte. Reuse the splice script from the 4.2.0 mirror if it is still in your scratchpad; it verifies the destination body matched the pre-edit source body before writing.

`agent-sdk-builder` keeps Claude Code vocabulary by design. Do not de-brand it, do not rename its tool names, and do not add `$SKILLS` definitions to files that do not need them. Skill-relative `references/foo.md` links work unchanged in the export, because the whole directory is copied together.

- [ ] **Step 2: Mirror the agent and the command with adaptations**

These two are adapted files, not byte-copies. Apply the same body edits from Tasks 3 through 6, preserving the export's existing divergences:

- `prompt-engineer.agent.md` keeps its VS Code frontmatter (`user-invocable`, namespaced `tools:` ids, `agents: []`) and its attribution comment. Its tools list already dropped the terminal ids in 4.2.0; do not reintroduce them.
- Both files keep `$SKILLS/agent-sdk-builder/references/reasoning-patterns.md` where the plugin uses `${CLAUDE_PLUGIN_ROOT}/references/reasoning-patterns.md`, and keep the `$SKILLS` definition line.
- The maintenance note from Task 7 goes into the mirrored `reasoning-patterns.md` too.
- Any prose naming a Claude Code tool in the agent or command body follows the tool-name mapping (`Read` to `read/readFile`, and so on). New prose in Tasks 3 through 6 names no tools, so this should be a no-op; check rather than assume.

- [ ] **Step 3: Bump versions, checking for foreign hunks first**

```bash
git diff -- .claude-plugin/marketplace.json
```

Read the output before staging anything. If it shows changes to plugins other than `ai-tooling`, another session is mid-work in this file: bump only the `ai-tooling` entry and `metadata.version`, then stage the file only if every remaining hunk is yours. If foreign hunks are present, hand the registry bump back to the user rather than sweeping their work into your commit. That is exactly how marketplace 19.0.1 shipped half a restructure.

- `ai-tooling` version: `4.2.0` to `5.0.0`. Major, because both components change their operating contract: the skill's core no longer answers API questions directly, and the agent's rubric emits `N/A` dimensions and a semantic diff that consumers of its output will see.
- `metadata.version`: next patch above whatever it currently holds.
- `exports/vscode/package.json` version: same value as `metadata.version`.
- `exports/vscode/CHANGELOG.md`: a new top entry describing the resolver split and the prompt-engineer redesign.

- [ ] **Step 4: Run every check**

```bash
python .claude/skills/downstream-exports/scripts/check_export.py
python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check
python scripts/lint_dependency_graph.py
```

Expected: `all checks passed` from the first and third, `manifest is fresh` from the second. No agent or prompt was added, renamed, or removed in this plan, so the manifest should already be fresh. If it is not, regenerate it with the same script without `--check` and bump `exports/vscode/package.json` again.

- [ ] **Step 5: Commit and verify the bump gate**

```bash
git add plugins/ai-tooling exports/vscode/ai-tooling .claude-plugin/marketplace.json \
        exports/vscode/package.json exports/vscode/CHANGELOG.md
git commit -m "Restructure ai-tooling around version-sensitive knowledge (v5.0.0)

agent-sdk-builder becomes a decision core plus five on-demand
references, governed by a three-tier source-of-truth policy: the
project's installed SDK, then current official documentation, then
these bundled files. The core no longer answers API questions from
memory.

prompt-engineer extracts a behavioral contract before rewriting and
reports a semantic diff after, scores an archetype-aware rubric with
N/A dimensions instead of a universal one, picks audit depth from
consequence instead of running the full pass every time, and labels
every quality claim predicted, measured, or verified.

Mirrored into exports/vscode."

python scripts/check_version_bumps.py HEAD~1 HEAD
```

Expected: `ok    version bumps`.

- [ ] **Step 6: Push and confirm CI**

```bash
git push
gh run list --limit 2
```

Expected: the newest run for this push completes `success`. A failure here means one of the four checks disagrees with the local run; read it before doing anything else.

---

## Self-Review

**Spec coverage against the frozen P1 backlog:**

| Backlog item | Task |
|---|---|
| shrink `agent-sdk-builder` core | 1, 2 |
| move volatile API detail to references | 1 |
| installed SDK to official docs to bundled reference hierarchy | 2 |
| semantic-invariant pass in `prompt-engineer` | 3 |
| archetype-aware rubric | 4 |
| adaptive fast/deep audit | 5 |
| measured vs predicted distinction | 6 |

Plus Task 7 (record the deferred item) and Task 8 (mirror, bump, verify), which the marketplace workflow requires of any plugin change.

**Out of scope by explicit approval:** the P2 layer (root-level `evals/ai-tooling/`, a hardcoded-path check added to the consistency CI, drift checks taught to `custom-plugin-refresh`). It lands after this plan, against a plugin whose shape has stopped moving.

**Type consistency:** the block names `<behavioral_contract>`, `<semantic_diff>`, `<epistemic_status>`, and `<evaluation_rubric>` are introduced in Tasks 3, 3, 6, and 4 and referenced by exactly those names in Tasks 5 and 6. The five reference filenames are fixed in Task 1 and reused verbatim in Tasks 2 and 8.
