#!/usr/bin/env python3
"""
Skill & Agent Description Validator for Claude Code plugin marketplaces.

Checks activation quality, description patterns, token budget,
and body size against skills-creator conventions.

Usage:
    python plugins/marketplace-ops/skills/skills-creator/scripts/validate_skills.py [plugin-name]
    python plugins/marketplace-ops/skills/skills-creator/scripts/validate_skills.py --all
"""

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[4]
MARKETPLACE_JSON = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = PROJECT_ROOT / "plugins"

DESCRIPTION_HARD_LIMIT = 1024
DESCRIPTION_RECOMMENDED_LIMIT = 300
TOTAL_DESCRIPTION_BUDGET = 15000
SKILL_BODY_WARN_LINES = 300
SKILL_BODY_MAX_LINES = 500
SKILL_BODY_TOKEN_TARGET = 5000
SKILL_BODY_TOKEN_WARN = 4000
EXAMPLE_TAG_MIN = 3
EXAMPLE_TAG_MAX = 5

# Passive patterns that indicate low activation descriptions
PASSIVE_PATTERNS = [
    (r"(?i)^\"?helps?\s+with\b", "passive: 'Helps with...'"),
    (r"(?i)^\"?can\s+be\s+used\b", "passive: 'Can be used...'"),
    (r"(?i)^\"?use\s+when\b", "passive: 'Use when...' (prefer 'TRIGGER WHEN')"),
    (r"(?i)^\"?useful\s+for\b", "passive: 'Useful for...'"),
    (r"(?i)^\"?a\s+tool\s+for\b", "passive: 'A tool for...'"),
    (r"(?i)^\"?provides?\b", "passive: 'Provides...'"),
]

# Directive patterns that indicate high activation
DIRECTIVE_PATTERNS = [
    r"(?i)\bALWAYS\s+invoke\b",
    r"(?i)\bMUST\s+use\b",
    r"(?i)\buse\s+PROACTIVELY\b",
    r"(?i)\bTRIGGER\s+WHEN\b",
]

NEGATIVE_CONSTRAINT_PATTERNS = [
    r"(?i)\bDo\s+not\b.*\bdirectly\b",
    r"(?i)\bDO\s+NOT\s+TRIGGER\b",
    r"(?i)\bnever\b.*\bdirectly\b",
]

EM_DASH = "\u2014"


def parse_frontmatter(text):
    """Extract YAML frontmatter from markdown text."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 3:].strip()
    fm = {}
    current_key = None
    current_val = []
    for line in fm_text.split("\n"):
        if re.match(r"^\w[\w-]*:", line):
            if current_key:
                fm[current_key] = "\n".join(current_val).strip()
            parts = line.split(":", 1)
            current_key = parts[0].strip()
            current_val = [parts[1].strip()] if len(parts) > 1 else []
        else:
            current_val.append(line.strip())
    if current_key:
        fm[current_key] = "\n".join(current_val).strip()
    return fm, body


def check_description(desc, component_type, name):
    """Validate a description against activation quality rules."""
    issues = []
    # Strip YAML multiline indicator
    clean = desc.strip().lstrip(">").strip()

    # Length checks
    if len(clean) > DESCRIPTION_HARD_LIMIT:
        issues.append(("CRITICAL", f"Description exceeds {DESCRIPTION_HARD_LIMIT} char limit ({len(clean)} chars)"))
    elif len(clean) > DESCRIPTION_RECOMMENDED_LIMIT:
        issues.append(("INFO", f"Description is {len(clean)} chars (recommended: under {DESCRIPTION_RECOMMENDED_LIMIT})"))

    # Em dash
    if EM_DASH in clean:
        issues.append(("WARNING", "Description contains em dash -- use hyphen or double hyphen"))

    # Passive patterns
    for pattern, label in PASSIVE_PATTERNS:
        if re.search(pattern, clean):
            issues.append(("WARNING", f"Low-activation description pattern: {label}"))
            break

    # Directive check
    has_directive = any(re.search(p, clean) for p in DIRECTIVE_PATTERNS)
    if not has_directive:
        issues.append(("WARNING", "No directive activation phrase found (ALWAYS invoke, MUST use, TRIGGER WHEN, use PROACTIVELY)"))

    # TRIGGER WHEN check
    has_trigger_when = bool(re.search(r"(?i)TRIGGER\s+WHEN\b", clean))
    if not has_trigger_when:
        issues.append(("WARNING", "Missing TRIGGER WHEN clause"))

    # DO NOT TRIGGER WHEN check
    has_no_trigger = bool(re.search(r"(?i)DO\s+NOT\s+TRIGGER\s+WHEN\b", clean))
    if not has_no_trigger:
        issues.append(("WARNING", "Missing DO NOT TRIGGER WHEN clause"))

    # Negative constraint check
    has_negative = any(re.search(p, clean) for p in NEGATIVE_CONSTRAINT_PATTERNS)
    if not has_negative and component_type == "skill":
        issues.append(("INFO", "No negative constraint ('Do not X directly') -- consider adding one for higher activation"))

    return issues, len(clean)


def check_skill_body(skill_dir):
    """Validate SKILL.md body size and references usage."""
    issues = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        issues.append(("CRITICAL", f"Missing SKILL.md in {skill_dir.name}"))
        return issues

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    _, body = parse_frontmatter(text)
    line_count = len(body.split("\n"))

    if line_count > SKILL_BODY_MAX_LINES:
        issues.append(("WARNING", f"SKILL.md body is {line_count} lines (max: {SKILL_BODY_MAX_LINES}) -- split into references/"))
    elif line_count > SKILL_BODY_WARN_LINES:
        has_refs = (skill_dir / "references").exists() and any((skill_dir / "references").iterdir())
        if not has_refs:
            issues.append(("INFO", f"SKILL.md body is {line_count} lines (threshold: {SKILL_BODY_WARN_LINES}) -- consider splitting into references/"))

    if EM_DASH in text:
        issues.append(("WARNING", "SKILL.md contains em dash character -- use hyphen or double hyphen"))

    return issues


def check_skill_body_extended(skill_dir):
    """Extended body checks: tokens, examples, frontmatter fields, preprocessor."""
    issues = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return issues, 0

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)

    # Token estimate (chars / 4)
    est_tokens = len(body) // 4
    if est_tokens > SKILL_BODY_TOKEN_TARGET:
        issues.append(("WARNING", f"SKILL.md body is ~{est_tokens:,} tokens (target: <{SKILL_BODY_TOKEN_TARGET:,}) -- split into references/"))
    elif est_tokens > SKILL_BODY_TOKEN_WARN:
        issues.append(("INFO", f"SKILL.md body is ~{est_tokens:,} tokens (approaching {SKILL_BODY_TOKEN_TARGET:,} target)"))

    # Example tags
    example_count = len(re.findall(r"<example>", body, re.IGNORECASE))
    if example_count == 0:
        issues.append(("INFO", f"No <example> tags -- guide recommends {EXAMPLE_TAG_MIN}-{EXAMPLE_TAG_MAX}"))
    elif example_count < EXAMPLE_TAG_MIN:
        issues.append(("INFO", f"Only {example_count} <example> tag(s) -- guide recommends {EXAMPLE_TAG_MIN}-{EXAMPLE_TAG_MAX}"))

    # context: fork detection
    if fm.get("context", "").strip() == "fork":
        issues.append(("INFO", "Uses context: fork (isolated subagent)"))

    # disable-model-invocation detection
    if fm.get("disable-model-invocation", "").strip().lower() == "true":
        issues.append(("INFO", "Has disable-model-invocation: true (slash-command only)"))

    # !command preprocessor syntax (backtick-wrapped shell commands)
    preproc_count = len(re.findall(r"!`[^`]+`", body))
    if preproc_count > 0:
        issues.append(("INFO", f"Uses {preproc_count} !`command` preprocessor injection(s)"))

    return issues, est_tokens


def check_agent_body(agent_path):
    """Validate agent body size and em dash."""
    issues = []
    text = agent_path.read_text(encoding="utf-8", errors="replace")
    _, body = parse_frontmatter(text)
    line_count = len(body.split("\n"))

    if line_count > 800:
        issues.append(("WARNING", f"Agent body is {line_count} lines (max recommended: 800)"))

    if EM_DASH in text:
        issues.append(("WARNING", "Agent file contains em dash character -- use hyphen or double hyphen"))

    return issues


def check_agent_frontmatter_extended(agent_path):
    """Check agent-specific frontmatter: tools field presence."""
    issues = []
    text = agent_path.read_text(encoding="utf-8", errors="replace")
    fm, _ = parse_frontmatter(text)

    if "tools" not in fm:
        issues.append(("INFO", "No tools field -- all tools allowed (consider restricting)"))

    return issues


def score_description(issues):
    """Calculate activation score 1-5 from issues."""
    score = 5
    for severity, _ in issues:
        if severity == "CRITICAL":
            score -= 2
        elif severity == "WARNING":
            score -= 1
        elif severity == "INFO":
            score -= 0.25
    return max(1, min(5, round(score, 1)))


def main():
    target_plugin = None
    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        target_plugin = sys.argv[1]

    if not MARKETPLACE_JSON.exists():
        print(f"ERROR: {MARKETPLACE_JSON} not found")
        sys.exit(1)

    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    plugins = data.get("plugins", [])

    total_desc_chars = 0
    total_body_tokens = 0
    all_results = []
    total_skills = 0
    total_agents = 0
    total_issues = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}

    for plugin in plugins:
        pname = plugin["name"]
        if target_plugin and pname != target_plugin:
            continue

        psource = plugin.get("source", f"./plugins/{pname}")
        pdir = PROJECT_ROOT / psource.lstrip("./")

        plugin_results = {"name": pname, "version": plugin.get("version", "?"), "skills": [], "agents": []}

        # Check skills
        for skill_ref in plugin.get("skills", []):
            skill_dir = pdir / skill_ref.lstrip("./")
            if not skill_dir.exists():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            total_skills += 1
            text = skill_md.read_text(encoding="utf-8", errors="replace")
            fm, _ = parse_frontmatter(text)
            desc = fm.get("description", "")
            sname = fm.get("name", skill_dir.name)

            desc_issues, desc_len = check_description(desc, "skill", sname)
            body_issues = check_skill_body(skill_dir)
            extended_issues, est_tokens = check_skill_body_extended(skill_dir)
            all_issues = desc_issues + body_issues + extended_issues
            total_desc_chars += desc_len
            total_body_tokens += est_tokens

            for severity, _ in all_issues:
                total_issues[severity] = total_issues.get(severity, 0) + 1

            plugin_results["skills"].append({
                "name": sname,
                "score": score_description(desc_issues),
                "desc_len": desc_len,
                "issues": all_issues,
            })

        # Check agents
        for agent_ref in plugin.get("agents", []):
            agent_path = pdir / agent_ref.lstrip("./")
            if not agent_path.exists():
                continue

            total_agents += 1
            text = agent_path.read_text(encoding="utf-8", errors="replace")
            fm, _ = parse_frontmatter(text)
            desc = fm.get("description", "")
            aname = fm.get("name", agent_path.stem)

            desc_issues, desc_len = check_description(desc, "agent", aname)
            body_issues = check_agent_body(agent_path)
            extended_issues = check_agent_frontmatter_extended(agent_path)
            all_issues = desc_issues + body_issues + extended_issues
            total_desc_chars += desc_len

            for severity, _ in all_issues:
                total_issues[severity] = total_issues.get(severity, 0) + 1

            plugin_results["agents"].append({
                "name": aname,
                "score": score_description(desc_issues),
                "desc_len": desc_len,
                "issues": all_issues,
            })

        if plugin_results["skills"] or plugin_results["agents"]:
            all_results.append(plugin_results)

    # Output report
    print("=" * 60)
    print("SKILL & AGENT DESCRIPTION VALIDATION REPORT")
    print("=" * 60)
    print()
    print(f"Scanned: {total_skills} skills, {total_agents} agents across {len(all_results)} plugins")
    print(f"Total description chars: {total_desc_chars:,} / {TOTAL_DESCRIPTION_BUDGET:,} budget ({total_desc_chars * 100 // TOTAL_DESCRIPTION_BUDGET}%)")
    if total_desc_chars > TOTAL_DESCRIPTION_BUDGET:
        print(f"  ** OVER BUDGET by {total_desc_chars - TOTAL_DESCRIPTION_BUDGET:,} chars -- skills may be silently dropped!")
    elif total_desc_chars > TOTAL_DESCRIPTION_BUDGET * 0.8:
        print(f"  ** Approaching budget limit ({TOTAL_DESCRIPTION_BUDGET - total_desc_chars:,} chars remaining)")
    print(f"Total skill body tokens (est.): {total_body_tokens:,}")
    print(f"Issues: {total_issues.get('CRITICAL', 0)} critical, {total_issues.get('WARNING', 0)} warnings, {total_issues.get('INFO', 0)} info")
    print("-" * 60)

    for pr in all_results:
        has_issues = any(
            item["issues"]
            for item in pr["skills"] + pr["agents"]
        )
        if not has_issues:
            continue

        print(f"\n## {pr['name']} (v{pr['version']})")

        for skill in pr["skills"]:
            if not skill["issues"]:
                continue
            print(f"\n  Skill: {skill['name']}  (score: {skill['score']}/5, {skill['desc_len']} chars)")
            for severity, msg in skill["issues"]:
                print(f"    [{severity}] {msg}")

        for agent in pr["agents"]:
            if not agent["issues"]:
                continue
            print(f"\n  Agent: {agent['name']}  (score: {agent['score']}/5, {agent['desc_len']} chars)")
            for severity, msg in agent["issues"]:
                print(f"    [{severity}] {msg}")

    # Summary table
    print("\n" + "=" * 60)
    print("ACTIVATION SCORE SUMMARY")
    print("=" * 60)
    print(f"{'Component':<40} {'Type':<7} {'Score':<6} {'Chars':<6}")
    print("-" * 60)

    low_scores = []
    for pr in all_results:
        for skill in pr["skills"]:
            label = f"{pr['name']}/{skill['name']}"
            print(f"{label:<40} {'skill':<7} {skill['score']:<6} {skill['desc_len']:<6}")
            if skill["score"] < 3:
                low_scores.append(label)
        for agent in pr["agents"]:
            label = f"{pr['name']}/{agent['name']}"
            print(f"{label:<40} {'agent':<7} {agent['score']:<6} {agent['desc_len']:<6}")
            if agent["score"] < 3:
                low_scores.append(label)

    if low_scores:
        print(f"\n** {len(low_scores)} components scored below 3/5 (need attention):")
        for ls in low_scores:
            print(f"   - {ls}")

    # Status
    crit = total_issues.get("CRITICAL", 0)
    warn = total_issues.get("WARNING", 0)
    if crit > 0:
        status = "BROKEN"
    elif warn > 5:
        status = "NEEDS ATTENTION"
    elif warn > 0:
        status = "OK (minor issues)"
    else:
        status = "EXCELLENT"

    print(f"\nStatus: {status}")


if __name__ == "__main__":
    main()
