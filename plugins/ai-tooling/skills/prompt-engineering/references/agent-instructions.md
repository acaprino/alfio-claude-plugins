# Agent instructions, tool descriptions and instruction files

On-demand reference for the `prompt-engineer` agent and the `/prompt-optimize` command. Read it
when the archetype is agentic / tool-use, when the prompt is a system policy that drives an agent
loop, or when the text under review is a tool or function description, an instruction file
(CLAUDE.md, AGENTS.md, copilot-instructions), a skill description, or the brief an orchestrator
hands a worker. It answers one question: which parts of an agent's instruction surface have a
measured effect, in which direction, on which model class. Injection defense, eagerness dials and
the vendor tool-writing rules live in the `prompt-engineer` role and are assumed here.

Every number below is **measured** on the named model and benchmark at the cited date, and
**predicted** on yours until you run the eval at the end. Numbers checked 2026-09-07.

## Four facts that frame every agent prompt

**A tool description is purpose, usage guidance and parameter semantics; examples are optional.**
On MCP-Universe (arXiv 2602.14878 v3), enriching tool descriptions with purpose, guidance, limits,
parameter explanations and examples raised median task success by 5.85 points and the partial-goal
evaluator score by 15.12, took GPT-4.1 from 18.18% to 29.44% and Qwen3-Coder-480B-A35B from
19.91% to 25.97%,
and also raised execution steps by 67.46% and regressed 16.67% of tasks. Removing the examples
from the enriched descriptions cost no material success; a compact purpose-plus-guidance
description was sometimes better than the full one. The vendor rule that the description is "by
far the most important factor" holds; the corollary that longer is better does not.

**In a coding agent's rule file, prohibitions have evidence and generic guidance does not.** On
SWE-bench Verified with Claude Code on Opus 4.6 (arXiv 2604.11088 v2), every rule condition beat
the 50.0% no-rule baseline of its Experiment 1, one trajectory per task, by 6.9 to 13.8 points,
random rules tied expert-curated ones at 63.8%,
every rule that helped on its own was a negative constraint and every rule that hurt was a
positive directive, and removing the one guardrail "do not refactor unrelated code" cost 20
points (McNemar p = 0.016). Growing the file from 0 to 50 rules stayed in a 59% to 67% band with
no collapse (Experiment 2, averaged over three seeds: 60.3% at zero rules, 66.7% at fifty; the
study attributes part of the distance from Experiment 1's 50.0% to run-to-run stochasticity, so
the two zero-rule figures are not a disagreement). Read that band for what it measures: the
study's success criterion is a patch that passes the repository's test suite, and it reports no
rule-adherence or joint-compliance metric anywhere, so a pass rate that holds across rule counts
cannot tell "followed fifty rules" apart from "ignored the rules the benchmark never scored".
The exception it buys is scoped to guardrail-type rules, prohibitions on scope, files, commands
and refactors: those are not a set of simultaneously verifiable output constraints, so the
role's over-constraining anti-pattern does not apply to them. An output obligation a rule file
carries counts like any other simultaneous constraint.

**How much history an agent sees is a per-model setting, not a virtue.** On an MCP hardware-design
benchmark (arXiv 2608.26199), Llama-3.1-8B scored 0.445 with task-scoped history against 0.157
with the whole run's history replayed; larger open models showed the opposite or a much smaller
effect. In the same benchmark, moving the system prompt from Markdown instructions to few-shot
demonstrations dropped Gemma 4 31B from 0.956 to 0.571 and Gemma 4 E4B from 0.731 to 0.179 on
correctly executed expected calls, while gpt-oss and Qwen hybrids barely moved. Demonstrations in a tool agent's system prompt
are a per-model risk to measure, never a default.

**A long-horizon goal needs verified state, not a reminder.** PushBench (arXiv 2605.23574) asks an
agent to keep producing valid artifacts to a quota. Claude Code on Sonnet 4.6 and Codex on GPT-5.4
did reasonably at 50 artifacts and fell to 3 successful runs in 9 per condition at 100. A
controller that exposes externally verified progress (`verified_done / target`) reached 69% to
78% and eliminated duplicate submissions; a plainer backlog controller reached only 25% to 50%. Write the quota as a checkable invariant the harness
maintains, not as "keep going until you have N".

## Tool and function descriptions

The anatomy that measured, in the order to write it: what the tool is for, when to use it and
when not to, what each parameter means and what values are valid, what it returns, and its limits
(rate, size, side effects). Add an example only when an eval shows the model misusing the tool
without one. Name parameters unambiguously; no isolated ablation of parameter renaming alone was
found, so treat that as vendor guidance. Pass tools through the API's tool field rather than
pasting schemas into the system prompt: OpenAI's GPT-4.1 guide reports +2% on SWE-bench Verified
from that change alone (vendor-measured, 2025-04). Instrument steps and call counts alongside
success: the MCP result above is a case where success rose while steps rose faster.

## The agent's system prompt

- **Zero-shot first for tool use.** The Gemma collapse above is the measured case against
  demonstrations in the system prompt; if the model misformats calls, fix the tool schema or the
  serving stack's tool parser before adding examples.
- **Scope the history.** Small models: current task plus a compact persistent state. Larger
  models: measure both; the direction differs by model.
- **State as an invariant.** For quotas, budgets and multi-step goals, expose the verified count,
  the remaining budget and the stop condition as data the harness updates, and have the prompt
  read them. Prose persistence lines ("keep going until resolved") are the eagerness dial the role
  describes, and they do not survive 100 items.
- **Resolve contradictions before shipping.** The role's positioning rules apply; on GPT-6 class
  models a conflict pauses the agent rather than being talked past (see `model-guidance.md`).

## Instruction files, skills and progressive disclosure

- **Guardrails over guidance.** Write the things the agent must not do (scope, files, commands,
  refactors) before the things it should prefer. On Opus 4.6 the prohibitions carried the gain;
  do not pad the file with positive style advice for completeness.
- **Count is not the constraint for guardrails.** Fifty prohibitions did not collapse a coding
  agent; conflicting rules and rules the agent cannot verify are the failure modes to hunt. An
  output obligation the file carries is not exempt: it counts like any other simultaneous
  constraint.
- **A skill or instruction file's description says what and when.** That is Anthropic's Agent
  Skills design (a compact name and description always visible, the body loaded only after
  selection) and the same principle on Claude Code, Codex and Copilot instruction files. No public
  isolated measurement of progressive disclosure against loading everything, of description
  length, or of trigger-phrase calibration was found; they are architecture and vendor guidance,
  labelled as such, and the role's overtriggering rule is the one measured constraint on trigger
  wording.

## Orchestrator briefs and worker summaries

No controlled measurement of a brief format or a return-summary format was found in the window.
What is documented practice: a brief carries the objective as one paragraph with what a complete
answer contains, the boundaries (what a neighbouring worker owns), the budget, and the exact
return format; the worker returns a condensed summary (Anthropic's context-engineering guidance
suggests 1,000 to 2,000 tokens) rather than its transcript. Label any claim about brief shape as
predicted, and put the eval on the orchestrator's end state, not on the brief's wording.

## Coding agents

- **Generate tests in a context that has not seen the implementation.** Across five models
  (arXiv 2607.05139 v1), tests written after the faulty code detected 14% of faults against 25%
  when written independently; giving the test generator the task alone rather than the agent's
  history improved fault detection by about 13.6 points on GPT-5-mini, 17.7 on GPT-4.1-mini, 10.6
  on Claude Haiku 4.5, 13.8 on DeepSeek-V4-Flash and 7.9 on Llama 3.3-70B. A separate test-writing worker
  with a fresh context is the measured shape. The prompt-shape claim is what this file owns; the
  workflow that runs it belongs to the `testing` plugin, a prose pointer that needs no dependency
  declaration.
- **Retrieve exemplars by similarity for transformation tasks.** In a 14-technique study over ten
  software-engineering tasks (arXiv 2506.05614, DeepSeek-V3 and o3-mini among the models),
  nearest-neighbour exemplar selection gave the most consistent gains: code translation CodeBLEU
  30.19 to 42.08, assert generation BLEU 25.24 to 65.44, exception-type prediction accuracy 78.16
  to 82.50; bug fixing and summarization gained nothing from any technique, and no technique
  dominated overall.
- **Techniques age across model generations.** A partial replication across model versions
  (arXiv 2608.24641, ICSME 2026) found the few-shot-versus-zero-shot effect reversing on average
  from Qwen2 (-4.2, -4.2, -8.2 across three settings) to Qwen2.5 (+7.2, +1.4, -1.3) and shrinking
  from GPT-3.5 to GPT-4o. A prompting result on the previous
  generation is a hypothesis on the current one.
- **Specification-first and repository-context phrasing** were not isolated by any controlled
  study found in the window; agent systems bundle them with retrieval and harness changes. Leave
  them as practice, labelled predicted.

## By model class

| Class | What measured | What to do |
|---|---|---|
| **Frontier reasoning model** | Rule files help (Opus 4.6, +6.9 to +13.8), guardrails carry it, 50 rules do not collapse the pass rate; quota persistence fails at 100 items without verified state (Sonnet 4.6, GPT-5.4); test generation in a fresh context +13.6 (GPT-5-mini) | Guardrail-first instruction files; verified state for long jobs; a separate test-writing context |
| **Hybrid open reasoner** | Enriched tool descriptions +6.06 (Qwen3-Coder 480B); Markdown system prompt versus few-shot barely matters on gpt-oss and Qwen hybrids | Purpose-plus-guidance descriptions; measure before adding examples |
| **Small open-weight instruct model** | Task-scoped history 0.445 versus 0.157 cumulative (Llama-3.1-8B); few-shot system demonstrations collapse Gemma 4 E4B (0.731 to 0.179) and 31B (0.956 to 0.571) | Scope the history to the task; no demonstrations in the system prompt; enforce tool-call shape in the stack (`structured-output.md`) |
| **Older non-reasoning model** | Enriched tool descriptions +11.26 (GPT-4.1); API tool field +2% SWE-bench (vendor) | Richer descriptions pay most here; tools through the API |

## The eval an agent prompt needs

Task success and partial-goal completion as two numbers; steps and tool calls per task next to
them, because a description that raises success by six points and steps by two thirds is a
trade, not a win; the per-task regression list, since the MCP enrichment regressed one task in
six while improving the median; pass^k rather than pass@k when consistency is what the caller
buys; and for long jobs, the count of verified artifacts against the quota at 50 and at 100
items, where prompt-only persistence was measured to fail.

## Sources

- "Model Context Protocol (MCP) Tool Descriptions Are Smelly! Towards Improving AI Agent Efficiency with Augmented MCP Tool Descriptions", arXiv 2602.14878 v3, 2026-05, ACM journal template dated 2026-06
- "Guardrails Beat Guidance: A Large-Scale Study of Rules, Skills, and Persistent Configuration for Coding Agents" (v1 title "Do Agent Rules Shape or Distort?"), arXiv 2604.11088 v2, 2026-05, no venue stated
- "Benchmarking AI Agents for Hardware Design Automation via MCP Tool Calling", arXiv 2608.26199 v1, 2026-08, no venue stated
- "Push Your Agent: Measuring and Enforcing Quantitative Goal Persistence", arXiv 2605.23574 v1, 2026-05, no venue stated
- "On the risk of coding before testing", arXiv 2607.05139 v1, 2026-07, no venue stated
- "Which Prompting Technique Should I Use? An Empirical Investigation of Prompting Techniques for Software Engineering Tasks", arXiv 2506.05614 v1, 2025-06, no venue stated
- "Aging of Prompt Engineering Techniques Across LLM Versions", arXiv 2608.24641, ICSME 2026
- OpenAI, GPT-4.1 prompting guide (2025-04), the tool-field result; Anthropic, Agent Skills and "Writing tools for agents" (2025); Claude Code, Codex and GitHub Copilot instruction-file documentation
- Not measured, worth the next refresh: progressive disclosure against full loading, skill-description length, trigger-phrase calibration, orchestrator brief and return-summary formats, parameter-naming ablations, specification-first phrasing on current agents
