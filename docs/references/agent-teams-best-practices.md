# Claude Code Agent Teams — Best Practices Reference

> Cross-cutting knowledge base for designing, reviewing, and restructuring agentic teams in Claude Code. Used to inform changes to the team pipelines in this marketplace (senior-review, codebase-xray, codebase-mapper, research) and the upstream wshobson/agents agent-teams plugin they build on, plus any agent that participates in a multi-agent pipeline.
>
> **Snapshot date:** 2026-05-16. Re-verify when Claude Code crosses a minor version or when the agent-teams feature flag is graduated out of experimental.

## TL;DR

Agentic teams in Claude Code cost **3-10× the tokens of a single Claude** (typical: ~7×), so they pay off only when the task has **genuinely independent work** that benefits from parallel exploration: multi-dimensional reviews, debug with competing hypotheses, feature work with non-overlapping ownership. For sequential tasks, same-file edits, or work with many dependencies, a single Claude or single-session subagents win.

The five load-bearing rules, converging between Anthropic docs and production lessons:

1. **Decompose context-centric, not problem-centric.** Group by context that can be truly isolated, not by job title (planner/coder/tester).
2. **Explicit file ownership** in every spawn prompt. Two teammates editing the same file = guaranteed overwrites.
3. **3-5 teammates** is the sweet spot (Anthropic docs); **2-3** when overhead must be minimized (community). Beyond 4-5, coordination overhead outgrows productivity.
4. **Delegate mode on the lead** — without it, an Opus lead implements the first task itself while teammates sit idle.
5. **Explicit task dependencies** (`addBlockedBy` / `addBlocks`) so teammates don't race to claim work that depends on unstable foundations.

## When to use a team (and when not to)

### Use a team when

- **Research / review with independent dimensions.** Security + performance + architecture in parallel, each as its own lens. A single reviewer gravitates to one type of issue and leaves the others under-examined.
- **New modules / features with separable ownership.** Each teammate owns a different directory; integration happens through interface contracts agreed upfront.
- **Debug with competing hypotheses.** Multiple investigators each push their own theory and try to disprove the others. Sequential investigation suffers from anchoring; adversarial parallel investigation surfaces the real root cause faster.
- **Cross-layer coordination.** Frontend / backend / tests with one teammate per layer.

### Don't use a team when

- Single-file fix or one-line bug fix. Coordination overhead exceeds the gain.
- Sequential task with many handoffs. A single Claude is faster and cheaper.
- Same-file edits across the work units. Use a single session.
- "Just to feel professional." Token cost is real; cheap-looking work becomes expensive.

### Three signals that multi-agent is the right call (Anthropic decision framework)

1. **Context protection** — a subtask generates >1000 tokens of irrelevant info that would dilute the main reasoning.
2. **Parallelization** — search/research across independent facets.
3. **Specialization** — a single agent struggles with a toolset of 20+ tools across unrelated domains; specialized agents with focused toolsets do better.

## Subagent vs. agent team

These are different mechanisms, not different sizes of the same thing.

| | **Subagent** | **Agent team** |
|---|---|---|
| **Context** | Own context window; results return to caller | Own context window; fully independent |
| **Communication** | Reports back to main agent only | Teammates message each other directly |
| **Coordination** | Main agent manages all work | Shared task list with self-coordination |
| **Best for** | Focused tasks where only the result matters | Complex work requiring discussion and collaboration |
| **Token cost** | Lower (summarized back to main) | Higher (each teammate is a full Claude) |

**Decision rule:** use a subagent when the worker can produce a self-contained result. Use a team when workers must share findings, challenge each other, or coordinate on their own.

## Configuration

### Enabling

In `~/.claude/settings.json` (preferred — persists across sessions):

```json
{
  "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" }
}
```

Shell-only `export` is scoped to a single terminal session and is a common source of "teammates not appearing" bugs.

Requires Claude Code **v2.1.32+**. Verify with `claude --version`.

### Display modes

- **In-process** (default in non-tmux terminals): all teammates inside the main terminal; Shift+Down cycles through them, message directly.
- **Split panes**: each teammate gets its own pane. Requires tmux or iTerm2 with `it2` CLI.
- Override with `teammateMode` in `~/.claude/settings.json` or `--teammate-mode in-process` flag.

### Permissions

Teammates **inherit the lead's permission mode at spawn**. Per-teammate modes can be changed after spawn but not set at spawn time. `--dangerously-skip-permissions` on the lead propagates to all teammates.

## Spawning teammates

### Use subagent definitions as teammate types

A subagent definition (`project / user / plugin / CLI` scope) can be referenced as the type of a teammate. The body of the definition is **appended** to the teammate's system prompt (not replaced).

**Caveats:**

- The `skills` and `mcpServers` frontmatter fields are **not applied** when the definition runs as a teammate. Skills and MCP servers load from project/user settings.
- The `tools` allowlist **is** honored, with the exception that team coordination tools (`SendMessage`, task management) are always available.

### Spawn prompt anatomy

Every teammate spawn prompt must include:

1. **Identity / name** the lead will use to address this teammate later.
2. **Scope** as explicit file / directory ownership ("you own `src/auth/`, do not touch `src/api/`").
3. **Context references** — pointers to specific files or sections (`CLAUDE.md` references, X-ray output paths, interconnect map anchors) the teammate must read before producing work.
4. **Output contract** — what they produce, where it goes (file path), in what format. If a downstream agent reads it, say so.
5. **Completion protocol** — for example: "When done, call `TaskUpdate` to mark completed before claiming the next task."

## Team sizing

| Team size | When | Notes |
|---|---|---|
| 2-3 | Most workflows. Community-preferred. | Lowest overhead, easiest to monitor and steer. |
| 3-5 | Anthropic docs default. | Good when each teammate owns ≥5 tasks. |
| 5-6 | Edge case. | Only when separation of concerns is exceptionally clean. |
| 7+ | Almost never simultaneous. | Anthropic's 16-agent C compiler project used ~2000 separate sessions, not simultaneous teammates. |

**Task sizing per teammate:** 5-6 tasks. Below that, coordination overhead dominates. Above that, the lead can't reassign work cleanly when someone stalls.

## Hooks for quality gates

Native hooks let you enforce rules without changing agent prompts:

| Hook | When it fires | Exit code 2 effect |
|---|---|---|
| `TeammateIdle` | A teammate is about to go idle | Send feedback, keep them working |
| `TaskCreated` | A task is being created | Block creation, send feedback |
| `TaskCompleted` | A task is being marked complete | Block completion, send feedback |

Pattern: use `TaskCompleted` to run lint / type-check / test before allowing a task to close. Converts "trust and hope" into "trust and verify".

## Verification panel + completeness critic (review pipelines)

Review pipelines (`/senior-review:team-review`, `/senior-review:code-review`) close with two quality gates whose canonical definition lives in the `senior-review:review-quality-gates` skill (`## Adversarial Verification Panel`, `## Completeness Critic`):

- **3-lens panel.** Each surviving finding is judged by three parallel verifiers with distinct mandates (reachability/correctness, false-positive causes, severity calibration). A finding survives on a 2-of-2 REAL vote from lenses 1-2; a tie leaves it `contested` rather than killing a possibly-real bug.
- **Completeness critic.** A final agent reports coverage gaps (dimensions not run, in-scope files no reviewer cited, unverified assumptions, uncovered high-risk hot-spots) and, for a high-risk uncovered area, triggers one bounded follow-up round.

The gate is default-on with a finding-count cost guard (threshold 25), a `--fast` opt-out, and a `--rigorous` force-full flag. In the prose/Agent substrate the cost guard is a finding-count proxy, not a token budget. A future Workflow-tool rewire replaces the proxy with a real budget and makes the majority vote and degradation deterministic.

## Hard limits (as of 2026-05)

- **One team per lead.** A lead can manage only one team at a time. Clean up before creating the next.
- **No nested teams.** Teammates cannot spawn their own teams or teammates.
- **Lead is fixed for the team's lifetime.** No promotion, no leadership transfer.
- **Permissions set at spawn.** Per-teammate at spawn time is not supported.
- **No session resumption for in-process teammates.** `/resume` and `/rewind` do not restore them. Plan checkpoints via the task list.
- **Split panes need tmux or iTerm2.** Not supported in VS Code integrated terminal, Windows Terminal, or Ghostty.
- **One message at a time per teammate.** Broadcast was removed; addressing each recipient by name is required.

## Operational do's and don'ts

### DO

1. Enable via `~/.claude/settings.json`, not shell-only env.
2. Start with **2-3 teammates** for clear-scope tasks; 4-5 only with truly independent work.
3. Write spawn prompts with explicit name, scope, context references, output contract, completion protocol.
4. Use existing subagent definitions (`senior-review:security-auditor` etc.) as teammate types when their dimension matches.
5. Set explicit task dependencies (`addBlockedBy` / `addBlocks`) when prerequisites exist (migrations → routes → tests).
6. Activate **delegate mode** on the lead when you observe lead-implementing-itself.
7. Install `TaskCompleted` hooks for lint / type / test gating before close.
8. Include the operational instruction "When done, call `TaskUpdate` to mark completed" in every teammate spawn prompt — task-status lag is a known bug.
9. Default to **subagents** (single-session) and escalate to a team only when teammates need to talk to each other.
10. For pipelines like `/team-review`, give each reviewer an explicit output file path and require writing to disk. Returning report text only forces a fragile fallback.

### DON'T

1. Don't decompose by role names ("planner / coder / tester / reviewer"). Decompose by isolable context.
2. Don't accept vague scope ("review the codebase", "fix the bug"). Bound everything.
3. Don't launch a team for 1-file fixes or 1-line bug fixes. Overhead eats the gain.
4. Don't leave the team unattended for long. Monitor and steer.
5. Don't share files across teammates without ownership. Race-write is guaranteed.
6. Don't put `--dangerously-skip-permissions` on the lead thinking it stays contained. It propagates.
7. Don't pre-create `~/.claude/teams/<name>/config.json` by hand. The runtime overwrites it.
8. Don't try to create a second team while one is active. Hard reject.
9. Don't rely on `/resume` / `/rewind` for in-process teammates. Plan manual checkpoints.
10. Don't conflate subagents and teams. Subagents return summaries; teams coordinate among themselves.

## Common failure modes (and fixes)

| Symptom | Root cause | Fix |
|---|---|---|
| Teammates not appearing | Env flag set in shell only; doesn't persist | Move to `~/.claude/settings.json` `env` block |
| Lead implements instead of delegating | No delegate mode active | Press Shift+Tab on the lead (coordination-only tools) |
| Two teammates overwrite same file | No ownership declared in spawn prompts | Add explicit file/directory ownership per teammate |
| 10-20 turns of codebase exploration per teammate | Scope too broad | Bound scope to specific files / modules in the prompt |
| Task list stuck on "in progress" after work is done | Teammate forgot `TaskUpdate` | Add explicit "call TaskUpdate when done" to spawn prompt |
| Lead shuts down before work is complete | Lead misjudges completion | "Wait for teammates to finish before proceeding" |
| Permission prompts flood the user | Lead-side prompts bubble up from each teammate | Pre-approve common operations in permission settings |
| Reviewer returns report as text, not file | Reviewer's system prompt does not mandate file write | Add an "Output Persistence" section to the reviewer agent body; ensure `Write` is in `tools` |
| Crash leaves orphaned tmux session | No native session resumption | `tmux ls`, `tmux kill-session -t <name>`, restart lead, recover from `~/.claude/tasks/{team-name}/` |

## Cost guidance

- **Multiplier:** plan for 3-10× a single-Claude run, with ~7× typical for plan-mode workflows.
- **Drivers:** number of teammates × token budget per teammate × duration of unsupervised exploration.
- **Cheap-team recipe:** Opus lead + Sonnet teammates, 2-3 teammates, scope-bounded prompts, Haiku for any subagent role where summarization is the main job.
- **Cost killers:** unbounded scope, no file ownership (forces rework), no task dependencies (forces rework on unstable foundations), no `TaskCompleted` gates (forces rework on broken code).

## How this applies to this repo

This reference is the source of truth for any change to:

- `plugins/codebase-xray/` — partition worker and synthesizer agents that participate in `/team-analyze`.
- `plugins/senior-review/` — every reviewer agent that participates in `/team-review` Phase 2.
- `plugins/codebase-mapper/` — writer agents in the parallel-writers pipeline.
- `plugins/research/` — `/research:team-research` is the lead; `deep-researcher` investigates one sub-question per parallel wave; `quick-searcher` handles single-fact lookups and verifier duty.
- Any new pipeline command that spawns multiple agents.

Before merging a change that touches an agent body, frontmatter `tools`, or a pipeline command, cross-check against the **Operational do's and don'ts** section above. Before introducing a new team preset, cross-check against **When to use a team (and when not to)**.

## Sources

Snapshot: 2026-05-16. Re-fetch when adopting major Claude Code versions.

**Authoritative (Anthropic):**

- [Orchestrate teams of Claude Code sessions](https://code.claude.com/docs/en/agent-teams)
- [Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Subagents in the SDK](https://platform.claude.com/docs/en/agent-sdk/subagents)
- [Multiagent sessions](https://platform.claude.com/docs/en/managed-agents/multi-agent)
- [When to use multi-agent systems (and when not to)](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)
- [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Claude Code Advanced Patterns webinar](https://www.anthropic.com/webinars/claude-code-advanced-patterns)
- [2026 Agentic Coding Trends Report (PDF)](https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf)

**Community / production lessons:**

- [Claude Code Agent Teams: The Practical Guide (LaoZhang AI)](https://blog.laozhang.ai/en/posts/claude-code-agent-teams)
- [Claude Code Agent Teams Setup & Usage Guide 2026 (claudefa.st)](https://claudefa.st/blog/guide/agents/agent-teams)
- [Claude Agent SDK in production: a studio's playbook (Autoolize)](https://autoolize.com/blog/claude-agent-sdk-production-playbook/)
- [Claude Code Agent Teams, Subagents, and MCP: The 2026 Playbook (Developers Digest)](https://www.developersdigest.tech/blog/claude-code-agent-teams-subagents-2026)
- [claude-code-ultimate-guide / agent-teams.md (GitHub)](https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/guide/workflows/agent-teams.md)

**Recency tracking:**

- [Claude Code Changelog (ClaudeLog)](https://claudelog.com/claude-code-changelog/)
- [Claude Code Changelog 2026 (claudefa.st)](https://claudefa.st/blog/guide/changelog)
