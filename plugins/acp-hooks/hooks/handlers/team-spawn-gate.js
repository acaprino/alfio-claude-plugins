// Team Spawn Gate - UserPromptSubmit hook (advisory, not blocking)
// Detects team-worthy requests: matches presets first, then falls back to
// complexity detection so Claude can freely compose a custom team.
// Toggle: set "teamSpawnGate" to false in ~/.claude/acp-config.json to disable

const fs = require("fs");
const path = require("path");

const homeDir = process.env.HOME || process.env.USERPROFILE;
const acpConfigPath = path.join(homeDir, ".claude", "acp-config.json");

let enabled = true;
try {
  const config = JSON.parse(fs.readFileSync(acpConfigPath, "utf8"));
  if (config.teamSpawnGate === false) enabled = false;
} catch {
  // No config = enabled by default
}

if (!enabled) process.exit(0);

// Require agent teams feature flag -- no point suggesting teams if disabled
if (!process.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS) process.exit(0);

// --- Preset detection rules ---
// Each preset has:
//   phrases: high-confidence multi-word patterns (any match = suggest)
//   keywords + minWords: lower-confidence single words that need complexity confirmation
//   scopeBoost: words that lower the minWords threshold by 5

const PRESETS = [
  {
    name: "review",
    command: "/agent-teams:team-spawn review",
    shortCommand: "/senior-review:code-review",
    desc: "Multi-dimensional code review (security + architecture + performance)",
    phrases: [
      "code review", "full review", "comprehensive review",
      "review the code", "review this code", "review my code",
      "multi-dimensional review", "architecture review",
      "revisiona il codice", "revisione completa"
    ],
    keywords: ["review", "audit", "revisiona", "revisione"],
    minWords: 8,
    scopeBoost: ["comprehensive", "full", "thorough", "deep", "completa", "completo"]
  },
  {
    name: "security",
    command: "/agent-teams:team-spawn security",
    desc: "Security audit with OWASP, platform, and distributed flow analysis",
    phrases: [
      "security audit", "security scan", "vulnerability scan",
      "owasp audit", "pentest", "penetration test",
      "audit di sicurezza", "analisi sicurezza"
    ],
    keywords: ["security", "vulnerability", "owasp", "sicurezza"],
    minWords: 8,
    scopeBoost: ["comprehensive", "full", "complete", "completa"]
  },
  {
    name: "debug",
    command: "/agent-teams:team-debug",
    desc: "Competing hypotheses debugging with parallel investigation",
    phrases: [
      "competing hypotheses", "multiple causes", "parallel debug",
      "root cause analysis", "can't figure out why",
      "investigate with hypotheses", "debug in parallel",
      "ipotesi concorrenti", "cause multiple"
    ],
    keywords: ["debug", "investigate", "trace"],
    minWords: 10,
    scopeBoost: ["hypotheses", "causes", "parallel", "competing", "ipotesi"]
  },
  {
    name: "feature",
    command: "/agent-teams:team-feature",
    desc: "Parallel feature development with file ownership boundaries",
    phrases: [
      "build a feature", "implement the feature", "develop a feature",
      "parallel development", "parallel implementation",
      "sviluppa in parallelo", "implementa in parallelo"
    ],
    keywords: ["build", "implement", "create", "develop", "costruisci", "implementa"],
    minWords: 12,
    scopeBoost: ["parallel", "multiple files", "across", "end to end", "from scratch",
                  "da zero", "completo", "parallelo"]
  },
  {
    name: "fullstack",
    command: "/agent-teams:team-spawn fullstack",
    desc: "Full-stack development with frontend, backend, and test agents",
    phrases: [
      "full stack", "fullstack", "frontend and backend",
      "backend and frontend", "end to end feature",
      "full-stack", "frontend e backend"
    ],
    keywords: [],
    minWords: 10,
    scopeBoost: []
  },
  {
    name: "deep-search",
    command: "/agent-teams:team-research",
    desc: "Deep multi-source research with parallel investigators",
    phrases: [
      "deep research", "thorough research", "comprehensive research",
      "systematic investigation", "deep dive research",
      "ricerca approfondita", "ricerca sistematica"
    ],
    keywords: ["research", "investigate", "ricerca"],
    minWords: 10,
    scopeBoost: ["deep", "thorough", "comprehensive", "systematic", "approfondita"]
  },
  {
    name: "research",
    command: "/agent-teams:team-spawn research",
    desc: "Parallel codebase, web, and documentation research",
    phrases: [
      "research this topic", "find out how", "research across",
      "parallel research"
    ],
    keywords: [],
    minWords: 12,
    scopeBoost: ["parallel", "multiple sources", "codebase and web"]
  },
  {
    name: "migration",
    command: "/agent-teams:team-spawn migration",
    desc: "Large-scale migration or refactor with coordination",
    phrases: [
      "migrate from", "migration from", "port from", "upgrade from",
      "large refactor", "codebase migration", "large-scale refactor",
      "migra da", "migrazione da"
    ],
    keywords: ["migrate", "migration", "migra", "migrazione"],
    minWords: 12,
    scopeBoost: ["entire", "all", "codebase", "large", "complete", "tutto", "intero"]
  },
  {
    name: "docs",
    command: "/agent-teams:team-spawn docs",
    desc: "Parallel documentation generation with exploration + writing + review",
    phrases: [
      "document the codebase", "map the codebase", "generate documentation",
      "write documentation for", "comprehensive docs",
      "documenta il codice", "mappa il codebase"
    ],
    keywords: ["document", "documentation", "documenta", "documentazione"],
    minWords: 15,
    scopeBoost: ["entire", "full", "comprehensive", "codebase", "project", "completa"]
  },
  {
    name: "app-analysis",
    command: "/agent-teams:team-spawn app-analysis",
    desc: "Competitive app analysis with UX audit + research + design extraction",
    phrases: [
      "analyze the app", "competitor app", "competitive analysis",
      "reverse engineer the ui", "app audit", "ux audit",
      "analizza l'app", "analisi competitiva"
    ],
    keywords: [],
    minWords: 10,
    scopeBoost: ["competitor", "competitive", "reverse engineer"]
  },
  {
    name: "tauri",
    command: "/agent-teams:team-spawn tauri",
    desc: "Tauri desktop/mobile development with Rust + frontend + platform agents",
    phrases: [
      "tauri app", "tauri desktop", "tauri mobile",
      "build with tauri", "create a tauri", "develop a tauri"
    ],
    keywords: ["tauri"],
    minWords: 15,
    scopeBoost: ["from scratch", "full", "desktop", "mobile", "da zero"]
  },
  {
    name: "ui-studio",
    command: "/agent-teams:team-design",
    desc: "Parallel UI design and build pipeline (design + layout + UX + polish)",
    phrases: [
      "ui from scratch", "design from scratch", "redesign the ui",
      "build the ui", "design system from scratch", "new design system",
      "ui da zero", "redesign completo", "ridisegna la ui"
    ],
    keywords: ["redesign", "ridisegna"],
    minWords: 15,
    scopeBoost: ["from scratch", "complete", "entire", "da zero", "completo"]
  }
];

function countWords(text) {
  return text.split(/\s+/).filter(Boolean).length;
}

function matchWord(text, word) {
  const re = new RegExp("\\b" + word.replace(/\s+/g, "\\s+") + "\\b", "i");
  return re.test(text);
}

function matchPreset(prompt) {
  const lower = prompt.toLowerCase();
  const words = countWords(prompt);

  // Tier 1: phrase matching (high confidence)
  for (const preset of PRESETS) {
    for (const phrase of preset.phrases) {
      if (lower.includes(phrase)) {
        return preset;
      }
    }
  }

  // Tier 2: keyword + complexity matching
  for (const preset of PRESETS) {
    if (!preset.keywords.length) continue;

    const hasKeyword = preset.keywords.some(kw => {
      const re = new RegExp("\\b" + kw + "\\b", "i");
      return re.test(lower);
    });

    if (!hasKeyword) continue;

    // Apply scope boost: each matching scope word reduces minWords by 5
    let effectiveMin = preset.minWords;
    if (preset.scopeBoost) {
      const boostCount = preset.scopeBoost.filter(sw => matchWord(lower, sw)).length;
      effectiveMin = Math.max(5, effectiveMin - boostCount * 5);
    }

    if (words >= effectiveMin) {
      return preset;
    }
  }

  return null;
}

// --- Tier 3: free-form complexity detection ---
// When no preset matches, detect whether the prompt is complex enough
// that Claude should compose a custom team from available agents.

const ACTION_VERBS = [
  "build", "implement", "create", "develop", "add", "write", "design",
  "refactor", "rewrite", "restructure", "optimize", "fix", "integrate",
  "set up", "setup", "configure", "deploy", "migrate", "convert",
  // Italian
  "costruisci", "implementa", "crea", "sviluppa", "aggiungi", "scrivi",
  "progetta", "rifattorizza", "riscrivi", "ottimizza", "sistema",
  "integra", "configura", "distribuisci"
];

const SCOPE_WORDS = [
  "entire", "whole", "full", "complete", "all", "across", "multiple",
  "end to end", "end-to-end", "from scratch", "comprehensive",
  // Italian
  "intero", "tutto", "completo", "completa", "multipli", "da zero"
];

const DOMAIN_KEYWORDS = [
  "frontend", "backend", "database", "api", "auth", "ui", "ux",
  "css", "react", "python", "rust", "tauri", "test", "tests",
  "deploy", "ci", "docker", "websocket", "graphql", "rest",
  "queue", "cache", "redis", "postgres", "mongo", "stripe"
];

// SYNC: update this catalog when agents are added or removed from the marketplace
const AGENT_CATALOG = [
  "python-development:python-engineer -- Python implementation",
  "python-development:python-test-engineer -- Python tests",
  "python-development:python-refactor-agent -- Python refactoring",
  "frontend:frontend-engineer -- Frontend/React implementation",
  "frontend:web-designer -- Web design, CSS, aesthetics",
  "frontend:ui-layout-designer -- Layout, grid, responsive",
  "tauri-development:rust-engineer -- Rust implementation",
  "tauri-development:tauri-desktop -- Tauri desktop apps",
  "tauri-development:tauri-mobile -- Tauri mobile apps",
  "testing:test-writer -- Test suites (any language)",
  "research:deep-researcher -- Multi-source investigation",
  "research:quick-searcher -- Fast fact-finding",
  "senior-review:security-auditor -- Security review",
  "senior-review:code-auditor -- Architecture/quality review",
  "senior-review:distributed-flow-auditor -- Cross-service flows",
  "senior-review:ui-race-auditor -- UI race conditions",
  "senior-review:chicken-egg-detector -- Circular dependencies",
  "platform-engineering:platform-reviewer -- Cross-platform compliance",
  "react-development:react-performance-optimizer -- React performance",
  "codebase-mapper:codebase-explorer -- Codebase understanding",
  "codebase-mapper:documentation-engineer -- Documentation writing",
  "app-analyzer:app-analyzer -- App navigation/UX analysis",
  "agent-teams:team-lead -- Team coordination",
  "agent-teams:team-implementer -- General implementation",
  "agent-teams:team-reviewer -- General review",
  "agent-teams:team-debugger -- Hypothesis-driven debugging",
].join("\n  ");

function detectComplexity(prompt) {
  const lower = prompt.toLowerCase();
  const words = countWords(prompt);

  // Too short to be complex
  if (words < 10) return false;

  // Must have at least one action verb
  const hasAction = ACTION_VERBS.some(v => matchWord(lower, v));
  if (!hasAction) return false;

  // Score complexity signals
  let score = 0;

  // Word count contributes
  if (words >= 20) score += 2;
  else if (words >= 15) score += 1;

  // Scope words (entire, full, from scratch, etc.)
  const scopeCount = SCOPE_WORDS.filter(s => matchWord(lower, s)).length;
  score += scopeCount * 2;

  // Multiple domain keywords (cross-domain work)
  const domainCount = DOMAIN_KEYWORDS.filter(d => matchWord(lower, d)).length;
  if (domainCount >= 3) score += 3;
  else if (domainCount >= 2) score += 2;

  // Multiple action verbs (multi-step work)
  const actionCount = ACTION_VERBS.filter(v => matchWord(lower, v)).length;
  if (actionCount >= 3) score += 2;
  else if (actionCount >= 2) score += 1;

  // Explicit multi-step language
  const multiStepPhrases = [
    "and then", "after that", "also need", "plus",
    "e poi", "dopo", "inoltre", "anche"
  ];
  if (multiStepPhrases.some(p => matchWord(lower, p))) score += 2;

  // Listing patterns (1., 2., bullet points, commas separating tasks)
  if (/\d\.\s/.test(prompt)) score += 2;
  if ((prompt.match(/,/g) || []).length >= 3) score += 1;

  // Questions are less likely to need teams
  if (prompt.trimEnd().endsWith("?")) score -= 2;

  // Threshold: need score >= 3 to suggest a custom team
  return score >= 3;
}

// --- Main ---

let input = "";
const MAX_INPUT = 1024 * 64; // 64 KB
const stdinTimeout = setTimeout(() => process.exit(0), 3000);
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  input += chunk;
  if (input.length > MAX_INPUT) process.exit(0);
});
process.stdin.on("end", () => {
  clearTimeout(stdinTimeout);
  try {
    const event = JSON.parse(input);
    const prompt = (event.prompt || "").trim();

    // Bypass: empty, slash commands, hash prefix, asterisk prefix
    if (!prompt || prompt.startsWith("/") || prompt.startsWith("#") || prompt.startsWith("*")) {
      process.exit(0);
    }

    // Bypass: single-word prompts
    if (!prompt.includes(" ")) process.exit(0);

    // Bypass: explicit --no-team flag
    if (prompt.includes("--no-team")) process.exit(0);

    const matched = matchPreset(prompt);
    let context;

    if (matched) {
      // Tier 1/2: preset matched -- use the predefined team
      context = [
        `<IMPORTANT>`,
        `[Team Spawn Gate] This prompt matches the "${matched.name}" team preset.`,
        ``,
        `This request benefits from a multi-agent team. Use the team unless the user explicitly asked for a single-agent approach.`,
        ``,
        `Command: ${matched.command}`,
        `What it does: ${matched.desc}`,
        ``,
        `Action:`,
        `1. Tell the user you're launching the "${matched.name}" team (one sentence)`,
        `2. Invoke the skill: ${matched.command}`,
        ``,
        `Do NOT ask for confirmation -- just launch the team. The user expects proactive team usage.`,
        `</IMPORTANT>`
      ].join("\n");
    } else if (detectComplexity(prompt)) {
      // Tier 3: no preset matched, but the request is complex enough for a custom team
      context = [
        `<IMPORTANT>`,
        `[Team Spawn Gate] No preset matched, but this request is complex enough for a multi-agent team.`,
        ``,
        `You have freedom to compose a custom team. Analyze the request and select 2-5 agents from the catalog below.`,
        `Use the Agent tool to spawn each teammate with the appropriate subagent_type.`,
        ``,
        `Available specialist agents:`,
        `  ${AGENT_CATALOG}`,
        ``,
        `Guidelines:`,
        `- Pick only agents relevant to the actual task (don't over-staff)`,
        `- If the task spans multiple domains (e.g. frontend + backend), pick one agent per domain`,
        `- Always include a team-lead if spawning 3+ agents`,
        `- Launch independent agents in parallel for speed`,
        `- Give each agent a clear, scoped task description`,
        ``,
        `Action:`,
        `1. Tell the user you're assembling a custom team and list the agents you chose (2-3 sentences max)`,
        `2. Spawn the agents using the Agent tool with the chosen subagent_type values`,
        ``,
        `Do NOT ask for confirmation -- compose and launch the team directly.`,
        `</IMPORTANT>`
      ].join("\n");
    } else {
      process.exit(0);
    }

    const output = {
      hookSpecificOutput: {
        hookEventName: "UserPromptSubmit",
        additionalContext: context
      }
    };

    process.stdout.write(JSON.stringify(output));
  } catch {
    process.exit(0);
  }
});
