# Alfio Claude Plugins

Custom Claude Code plugin marketplace with development workflow agents and skills for code quality, Tauri/Rust development, frontend optimization, and AI tooling.

## Installation

### From GitHub (Recommended)

```bash
claude plugins:add acaprino/alfio-claude-plugins
```

### From Local Path

```bash
claude plugins:add C:\Users\alfio\Desktop\agents
```

### Verify Installation

```bash
claude plugins:list
```

## Plugins Overview

| Plugin | Description | Agents | Skills |
|--------|-------------|--------|--------|
| **code-quality** | Code review, analysis, and Python refactoring | 1 | 2 |
| **tauri-development** | Tauri 2 mobile/desktop and Rust engineering | 2 | 1 |
| **frontend-optimization** | React performance, UI polish, and UX design | 3 | - |
| **ai-tooling** | Prompt engineering and LLM optimization | 1 | - |

---

## Code Quality Plugin

Tools for systematic code review, deep analysis, and Python refactoring.

### Agents

#### `senior-code-reviewer`
Expert code review agent providing systematic analysis of code quality, security, performance, and architecture.

**Model:** `claude-opus-4-5-20251101`

**Use for:**
- Comprehensive feature reviews
- Pre-deployment validation
- Security audits
- Performance optimization
- Architectural assessments
- Critical code path reviews

**Invocation:**
```
Use the senior-code-reviewer agent to review [file/feature]
```

**Output includes:**
- Executive summary with deploy/fix-first/redesign recommendation
- Findings by severity (CRITICAL, HIGH, MEDIUM, LOW)
- Code quality scores (Security, Performance, Maintainability, Testing)
- Prioritized action plan with time estimates

### Skills

#### `deep-dive-analysis`
AI-powered systematic codebase analysis combining mechanical structure extraction with semantic understanding.

**Use for:**
- Codebase analysis and documentation
- Architecture understanding
- Pattern recognition and red flag detection
- Code review with semantic understanding
- Onboarding to new projects

**Invocation:**
```
/deep-dive-analysis
```

**Capabilities:**
- Extract code structure (classes, functions, imports)
- Map dependencies (internal/external)
- Recognize architectural patterns
- Identify anti-patterns and red flags
- Trace data and control flows
- Assess quality and maintainability

#### `python-refactor-skill`
Systematic code refactoring that transforms complex code into clean, maintainable code.

**Use for:**
- Legacy code modernization
- Spaghetti code cleanup
- Complexity reduction
- OOP transformation
- Code review improvements

**Invocation:**
```
/python-refactor
```

**Key principles:**
- Class-based architecture (mandatory)
- Flake8 compliance
- Cognitive complexity reduction
- Proper dependency injection
- Clear module organization

---

## Tauri Development Plugin

Specialized tools for Tauri 2 cross-platform development and Rust engineering.

### Agents

#### `tauri-optimizer`
Expert in Tauri v2 + React desktop application optimization for trading and high-frequency data scenarios.

**Model:** `claude-opus-4-5-20251101`

**Use for:**
- Performance reviews
- IPC architecture optimization
- State management patterns
- Memory leak detection
- Rust backend optimization
- WebView tuning

**Invocation:**
```
Use the tauri-optimizer agent to analyze [project/file]
```

**Performance targets:**
| Metric | Target | Critical |
|--------|--------|----------|
| Startup time | < 1s | < 2s |
| Memory baseline | < 100MB | < 150MB |
| IPC latency | < 0.5ms | < 1ms |
| Frame rate | 60 FPS | > 30 FPS |

#### `rust-engineer`
Expert Rust developer specializing in systems programming, memory safety, and zero-cost abstractions.

**Model:** `claude-opus-4-5-20251101`

**Use for:**
- Ownership pattern design
- Async programming (tokio)
- Performance optimization
- FFI and unsafe code
- Memory management
- Embedded development

**Invocation:**
```
Use the rust-engineer agent to implement [feature]
```

**Checklist enforced:**
- Zero unsafe code outside core abstractions
- clippy::pedantic compliance
- Complete documentation with examples
- MIRI verification for unsafe blocks
- Benchmark performance-critical code

### Skills

#### `tauri2-mobile`
Expert guidance for developing, testing, and deploying mobile applications with Tauri 2.

**Use for:**
- Android/iOS project setup
- Rust backend patterns
- Plugin integration (biometric, geolocation, notifications, IAP)
- Emulator/ADB testing
- Code signing and store deployment

**Invocation:**
```
/tauri2-mobile
```

**Quick commands:**
| Task | Command |
|------|---------|
| Init Android | `npm run tauri android init` |
| Dev Android | `npm run tauri android dev` |
| Build APK | `npm run tauri android build --apk` |
| Build iOS | `npm run tauri ios build` |

---

## Frontend Optimization Plugin

React performance optimization, UI polish, and UX design tools.

### Agents

#### `react-performance-optimizer`
Expert in React 19 performance optimization including React Compiler, Server Components, and bundle optimization.

**Model:** `claude-opus-4-5-20251101`

**Use for:**
- React performance reviews
- Bundle analysis and reduction
- State management decisions
- Re-render optimization
- Virtualization setup

**Invocation:**
```
Use the react-performance-optimizer agent to analyze [component/app]
```

**Key optimizations:**
- React Compiler (Babel plugin) configuration
- Zustand/Jotai atomic selectors
- useDeferredValue for non-critical updates
- TanStack Virtual for large datasets
- Code splitting and lazy loading

**Performance targets:**
| Metric | Web | Desktop |
|--------|-----|---------|
| Bundle (initial) | < 200KB | < 3MB |
| Frame rate | 60 FPS | 60 FPS |
| Render time | < 16ms | < 16ms |

#### `ui-polisher`
Senior UI polish specialist and motion designer for creating premium interfaces.

**Model:** `sonnet`

**Use for:**
- Micro-interactions and animations
- Page transitions
- Button/input states
- Loading states and skeletons
- Premium feel and polish

**Invocation:**
```
Use the ui-polisher agent to improve [component/page]
```

**Focus areas:**
- Hover/press states with transitions
- Spring physics for toggles
- Coordinated enter/exit animations
- 60fps smooth animations

#### `ui-ux-designer`
Elite UI/UX designer for beautiful, accessible interfaces and design systems.

**Model:** `claude-opus-4-5-20251101`

**Use for:**
- Design systems creation
- User flow optimization
- Wireframes and prototypes
- Accessibility compliance
- Component architecture

**Invocation:**
```
Use the ui-ux-designer agent to design [feature/system]
```

**Expertise:**
- Visual design and interaction patterns
- User-centered research
- Design tokenization
- Cross-platform consistency
- WCAG accessibility

---

## AI Tooling Plugin

Prompt engineering and LLM optimization tools.

### Agents

#### `prompt-engineer`
Expert prompt engineer specializing in designing, optimizing, and managing prompts for LLMs.

**Model:** `claude-opus-4-5-20251101`

**Use for:**
- Prompt design and optimization
- Token usage reduction
- A/B testing prompts
- Production prompt systems
- Multi-model strategies

**Invocation:**
```
Use the prompt-engineer agent to optimize [prompt/system]
```

**Prompt patterns:**
- Zero-shot / Few-shot prompting
- Chain-of-thought / Tree-of-thought
- ReAct pattern
- Constitutional AI
- Role-based prompting

**Targets:**
- Accuracy > 90%
- Latency < 2s
- Token usage optimized
- Cost per query tracked

---

## Usage Examples

### Code Review Workflow
```
1. Use the senior-code-reviewer agent to review src/features/trading
2. Address CRITICAL issues first
3. Use react-performance-optimizer for React-specific optimizations
```

### Tauri App Optimization
```
1. Use tauri-optimizer for IPC and Rust backend
2. Use react-performance-optimizer for React frontend
3. Use ui-polisher for animations and polish
```

### New Feature Development
```
1. Use ui-ux-designer to design the feature
2. Use rust-engineer for backend implementation
3. Use senior-code-reviewer before merge
```

### Prompt System Development
```
1. Use prompt-engineer to design prompts
2. Test variations and measure accuracy
3. Optimize token usage and costs
```

---

## Project Structure

```
alfio-claude-plugins/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── code-quality/
│   │   ├── agents/
│   │   │   └── senior-code-reviewer.md
│   │   └── skills/
│   │       ├── deep-dive-analysis/
│   │       └── python-refactor-skill/
│   ├── tauri-development/
│   │   ├── agents/
│   │   │   ├── tauri-optimizer.md
│   │   │   └── rust-engineer.md
│   │   └── skills/
│   │       └── tauri2-mobile/
│   ├── frontend-optimization/
│   │   └── agents/
│   │       ├── react-performance-optimizer.md
│   │       ├── ui-polisher.md
│   │       └── ui-ux-designer.md
│   └── ai-tooling/
│       └── agents/
│           └── prompt-engineer.md
├── LICENSE
├── README.md
└── .gitignore
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your agent/skill following the existing structure
4. Update `marketplace.json` with your additions
5. Submit a pull request

### Agent Template

```markdown
---
name: agent-name
description: Brief description of the agent's purpose
model: claude-opus-4-5-20251101
tools: Read, Write, Edit, Bash, Glob, Grep
---

Agent instructions and expertise...
```

### Skill Template

```markdown
---
name: skill-name
description: Brief description of the skill's purpose
---

# Skill Name

## Overview
...

## When to Use
...

## How to Use
...
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
