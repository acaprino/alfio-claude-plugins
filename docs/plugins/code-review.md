# Code Review Plugin

> Catch bugs before they ship. Three specialized agents review architecture, security, and code patterns in parallel -- like having a senior architect, security auditor, and quality engineer on every PR.

## Agents

### `architect-review`

Master software architect specializing in modern architecture patterns, clean architecture, microservices, event-driven systems, and DDD.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Architecture integrity, scalability review, design pattern assessment |

**Invocation:**
```
Use the architect-review agent to review [system/design]
```

---

### `security-auditor`

Expert security auditor specializing in DevSecOps, comprehensive cybersecurity, and compliance frameworks.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Security audits, DevSecOps, compliance (GDPR/HIPAA/SOC2), threat modeling |

**Invocation:**
```
Use the security-auditor agent to audit [system/codebase]
```

**Expertise:**
- Vulnerability assessment and threat modeling
- OAuth2/OIDC secure authentication
- OWASP standards and cloud security
- Security automation and incident response

---

### `pattern-quality-scorer`

Pattern consistency analyzer and quantitative code quality scorer.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Pattern deviation detection, anti-pattern checklists, quality scoring |

**Invocation:**
```
Use the pattern-quality-scorer agent to analyze [codebase]
```

**Methodology:**
- 16-item anti-pattern checklist
- 6 mental models (security engineer, performance engineer, team lead, systems architect, SRE, pattern detective)
- 1-10 Code Quality Score per category

---

## Commands

### `/full-review`

Orchestrate comprehensive multi-dimensional code review using all specialized review agents.

```
/full-review src/features/auth/ --security-focus
```

**Options:**
| Flag | Effect |
|------|--------|
| `--security-focus` | Prioritize security analysis |
| `--performance-critical` | Deep performance review |
| `--strict-mode` | Strictest quality standards |
| `--framework react\|django` | Framework-specific checks |

---

### `/code-review`

Unified code review -- auto-detects scope: uncommitted/staged changes, recent commits, PR number, or branch diff. Runs architecture, security, and pattern analysis agents in parallel with confidence scoring.

```
/code-review                    # auto-detect: uncommitted changes or branch diff
/code-review 42                 # review PR #42
/code-review --commits 3        # review last 3 commits
/code-review --branch feature   # review branch diff
/code-review --auto-comment     # post findings as PR comments
```

---

### `/pr-enhance`

Analyze current branch changes, generate comprehensive PR description with risk assessment and review checklist, and optionally create the PR via `gh`.

```
/pr-enhance --create
```
