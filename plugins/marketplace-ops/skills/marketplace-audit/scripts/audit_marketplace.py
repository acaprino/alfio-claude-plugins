#!/usr/bin/env python3
"""
Marketplace Audit Script for anvil-toolset.

Validates marketplace.json consistency, checks file references,
validates frontmatter, detects orphaned files, and reports issues.

Usage:
    python plugins/marketplace-ops/skills/marketplace-audit/scripts/audit_marketplace.py [--fix]
"""

import json
import re
import subprocess
import sys
from pathlib import Path

# Resolve project root (4 levels up from this script)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[4]
MARKETPLACE_JSON = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = PROJECT_ROOT / "plugins"

REQUIRED_PLUGIN_FIELDS = [
    "name", "source", "description", "version",
    "author", "license", "keywords", "category", "strict"
]

REQUIRED_AGENT_FRONTMATTER = ["name", "description", "model", "color"]
REQUIRED_SKILL_FRONTMATTER = ["name", "description"]
REQUIRED_COMMAND_FRONTMATTER = ["description"]

VALID_COLORS = [
    "red", "blue", "green", "yellow", "purple", "orange", "cyan",
    "magenta", "violet", "teal", "indigo", "gold", "rust", "pink"
]

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
KEBAB_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


class AuditReport:
    def __init__(self):
        self.critical = []
        self.warning = []
        self.info = []
        self.stats = {
            "plugins": 0,
            "agents": 0,
            "skills": 0,
            "commands": 0,
            "plugins_with_agents": 0,
            "plugins_with_skills": 0,
            "plugins_with_commands": 0,
        }

    def add(self, severity, message):
        getattr(self, severity).append(message)

    def print_report(self):
        print("=" * 60)
        print("MARKETPLACE AUDIT REPORT")
        print("=" * 60)
        print()

        # Stats
        print(f"Plugins: {self.stats['plugins']}")
        print(f"  Agents:   {self.stats['agents']} across {self.stats['plugins_with_agents']} plugins")
        print(f"  Skills:   {self.stats['skills']} across {self.stats['plugins_with_skills']} plugins")
        print(f"  Commands: {self.stats['commands']} across {self.stats['plugins_with_commands']} plugins")
        print()

        # Issues
        total_issues = len(self.critical) + len(self.warning)
        print(f"Issues: {total_issues} ({len(self.critical)} critical, {len(self.warning)} warnings)")
        print("-" * 60)

        if self.critical:
            print("\n[CRITICAL]")
            for msg in self.critical:
                print(f"  - {msg}")

        if self.warning:
            print("\n[WARNING]")
            for msg in self.warning:
                print(f"  - {msg}")

        if self.info:
            print("\n[INFO]")
            for msg in self.info:
                print(f"  - {msg}")

        print()
        if self.critical:
            print("Status: BROKEN")
        elif self.warning:
            print("Status: NEEDS ATTENTION")
        else:
            print("Status: HEALTHY")


def parse_frontmatter(filepath):
    """Extract YAML frontmatter from a markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return None, str(e)

    if not content.startswith("---"):
        return {}, None

    end = content.find("---", 3)
    if end == -1:
        return {}, None

    fm_text = content[3:end].strip()
    result = {}
    current_key = None
    current_value_lines = []

    for line in fm_text.split("\n"):
        # Handle multiline values with >
        if current_key and (line.startswith("  ") or line.startswith("\t")):
            current_value_lines.append(line.strip())
            continue

        if current_key and current_value_lines:
            result[current_key] = " ".join(current_value_lines)
            current_key = None
            current_value_lines = []

        match = re.match(r"^(\w[\w-]*):\s*(.*)", line)
        if match:
            key = match.group(1)
            value = match.group(2).strip().strip('"').strip("'")
            if value == ">" or value == "|":
                current_key = key
                current_value_lines = []
            else:
                result[key] = value

    if current_key and current_value_lines:
        result[current_key] = " ".join(current_value_lines)

    return result, None


def set_frontmatter_field(filepath, field, value):
    """Set or replace a frontmatter field in a markdown file."""
    content = filepath.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False

    end = content.find("---", 3)
    if end == -1:
        return False

    fm_block = content[3:end]
    body = content[end:]

    # Replace existing field or add before closing ---
    field_pattern = re.compile(rf"^{re.escape(field)}:\s*.*$", re.MULTILINE)
    if field_pattern.search(fm_block):
        fm_block = field_pattern.sub(f"{field}: {value}", fm_block)
    else:
        fm_block = fm_block.rstrip("\n") + f"\n{field}: {value}\n"

    filepath.write_text("---" + fm_block + body, encoding="utf-8")
    return True


def audit(fix=False):
    report = AuditReport()

    # Load marketplace.json
    if not MARKETPLACE_JSON.exists():
        report.add("critical", f"marketplace.json not found at {MARKETPLACE_JSON}")
        report.print_report()
        return 1

    with open(MARKETPLACE_JSON, encoding="utf-8") as f:
        marketplace = json.load(f)

    # Check metadata
    metadata = marketplace.get("metadata", {})
    version = metadata.get("version")
    if not version:
        report.add("critical", "metadata.version is missing")
    elif not SEMVER_PATTERN.match(str(version)):
        report.add("warning", f"metadata.version '{version}' is not valid semver")

    plugins = marketplace.get("plugins", [])
    report.stats["plugins"] = len(plugins)

    # Track registered paths for orphan detection
    registered_agent_files = set()
    registered_skill_dirs = set()
    registered_command_files = set()
    seen_names = set()

    for plugin in plugins:
        pname = plugin.get("name", "<unnamed>")

        # Check duplicate names
        if pname in seen_names:
            report.add("critical", f"Duplicate plugin name: {pname}")
        seen_names.add(pname)

        # Check required fields
        for field in REQUIRED_PLUGIN_FIELDS:
            if field not in plugin:
                report.add("critical", f"Plugin '{pname}': missing required field '{field}'")

        # Check naming convention
        if not KEBAB_CASE_PATTERN.match(pname):
            report.add("warning", f"Plugin '{pname}': name is not kebab-case")

        # Check version
        pversion = plugin.get("version", "")
        if not SEMVER_PATTERN.match(str(pversion)):
            report.add("warning", f"Plugin '{pname}': version '{pversion}' is not valid semver")

        # Check source directory exists
        source = plugin.get("source", "")
        source_path = PROJECT_ROOT / source.lstrip("./")
        if not source_path.is_dir():
            report.add("critical", f"Plugin '{pname}': source directory missing: {source}")

        # Check agents
        agents = plugin.get("agents", [])
        if agents:
            report.stats["plugins_with_agents"] += 1
        for agent_path in agents:
            report.stats["agents"] += 1
            full_path = source_path / agent_path.lstrip("./")
            registered_agent_files.add(full_path.resolve())

            if not full_path.exists():
                report.add("critical", f"Plugin '{pname}': agent file missing: {agent_path}")
                continue

            fm, err = parse_frontmatter(full_path)
            if err:
                report.add("critical", f"Plugin '{pname}': cannot read agent {agent_path}: {err}")
                continue
            if fm is None:
                report.add("warning", f"Plugin '{pname}': agent {agent_path} has no frontmatter")
                continue

            for field in REQUIRED_AGENT_FRONTMATTER:
                if field not in fm:
                    if fix and field == "color":
                        fallback = "blue"
                        for other_path in agents:
                            ofp = source_path / other_path.lstrip("./")
                            if ofp == full_path or not ofp.exists():
                                continue
                            ofm, _ = parse_frontmatter(ofp)
                            if ofm and ofm.get("color") in VALID_COLORS:
                                fallback = ofm["color"]
                                break
                        if set_frontmatter_field(full_path, "color", fallback):
                            report.add(
                                "info",
                                f"[FIXED] Plugin '{pname}': agent {agent_path} "
                                f"added missing color '{fallback}'",
                            )
                            continue
                    report.add("warning", f"Plugin '{pname}': agent {agent_path} missing frontmatter '{field}'")

            # Check name matches filename
            fm_name = fm.get("name", "")
            expected_name = full_path.stem
            if fm_name and fm_name != expected_name:
                report.add("warning", f"Plugin '{pname}': agent name '{fm_name}' != filename '{expected_name}'")

            # Check color validity
            color = fm.get("color", "")
            if color and color not in VALID_COLORS:
                if fix:
                    # Pick the first valid color used by other agents in this plugin,
                    # or fall back to "blue"
                    fallback = "blue"
                    for other_path in agents:
                        ofp = source_path / other_path.lstrip("./")
                        if ofp == full_path or not ofp.exists():
                            continue
                        ofm, _ = parse_frontmatter(ofp)
                        if ofm and ofm.get("color") in VALID_COLORS:
                            fallback = ofm["color"]
                            break
                    if set_frontmatter_field(full_path, "color", fallback):
                        report.add(
                            "info",
                            f"[FIXED] Plugin '{pname}': agent {agent_path} "
                            f"color '{color}' -> '{fallback}'",
                        )
                    else:
                        report.add(
                            "warning",
                            f"Plugin '{pname}': agent {agent_path} has invalid "
                            f"color '{color}' (auto-fix failed)",
                        )
                else:
                    report.add("warning", f"Plugin '{pname}': agent {agent_path} has invalid color '{color}'")

        # Check skills
        skills = plugin.get("skills", [])
        if skills:
            report.stats["plugins_with_skills"] += 1
        for skill_path in skills:
            report.stats["skills"] += 1
            full_path = source_path / skill_path.lstrip("./")
            registered_skill_dirs.add(full_path.resolve())

            if not full_path.is_dir():
                report.add("critical", f"Plugin '{pname}': skill directory missing: {skill_path}")
                continue

            skill_md = full_path / "SKILL.md"
            if not skill_md.exists():
                report.add("critical", f"Plugin '{pname}': SKILL.md missing in {skill_path}")
                continue

            fm, err = parse_frontmatter(skill_md)
            if err:
                report.add("critical", f"Plugin '{pname}': cannot read {skill_path}/SKILL.md: {err}")
                continue
            if fm is None:
                report.add("warning", f"Plugin '{pname}': {skill_path}/SKILL.md has no frontmatter")
                continue

            for field in REQUIRED_SKILL_FRONTMATTER:
                if field not in fm:
                    report.add("warning", f"Plugin '{pname}': {skill_path}/SKILL.md missing frontmatter '{field}'")

        # Check commands
        commands = plugin.get("commands", [])
        if commands:
            report.stats["plugins_with_commands"] += 1
        for cmd_path in commands:
            report.stats["commands"] += 1
            full_path = source_path / cmd_path.lstrip("./")
            registered_command_files.add(full_path.resolve())

            if not full_path.exists():
                report.add("critical", f"Plugin '{pname}': command file missing: {cmd_path}")
                continue

            fm, err = parse_frontmatter(full_path)
            if err:
                report.add("critical", f"Plugin '{pname}': cannot read command {cmd_path}: {err}")
                continue
            if fm is None:
                report.add("warning", f"Plugin '{pname}': command {cmd_path} has no frontmatter")
                continue

            for field in REQUIRED_COMMAND_FRONTMATTER:
                if field not in fm:
                    report.add("warning", f"Plugin '{pname}': command {cmd_path} missing frontmatter '{field}'")

    # Orphan detection - scan filesystem
    if PLUGINS_DIR.is_dir():
        for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
            if not plugin_dir.is_dir():
                continue

            dir_name = plugin_dir.name
            if dir_name not in seen_names:
                report.add("warning", f"Orphaned plugin directory: plugins/{dir_name}/ (not in marketplace.json)")

            # Check for unregistered agents
            agents_dir = plugin_dir / "agents"
            if agents_dir.is_dir():
                for agent_file in sorted(agents_dir.glob("*.md")):
                    if agent_file.resolve() not in registered_agent_files:
                        report.add("warning", f"Orphaned agent: {agent_file.relative_to(PROJECT_ROOT)}")

            # Check for unregistered skills
            skills_dir = plugin_dir / "skills"
            if skills_dir.is_dir():
                for skill_dir in sorted(skills_dir.iterdir()):
                    if skill_dir.is_dir() and skill_dir.resolve() not in registered_skill_dirs:
                        if (skill_dir / "SKILL.md").exists():
                            report.add("warning", f"Orphaned skill: {skill_dir.relative_to(PROJECT_ROOT)}")

            # Check for unregistered commands
            commands_dir = plugin_dir / "commands"
            if commands_dir.is_dir():
                for cmd_file in sorted(commands_dir.glob("*.md")):
                    if cmd_file.resolve() not in registered_command_files:
                        report.add("warning", f"Orphaned command: {cmd_file.relative_to(PROJECT_ROOT)}")

    # Cross-reference consistency checks
    marketplace_name = marketplace.get("name", "")

    # Check 1: marketplace name vs git remote repo name
    try:
        remote_url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            cwd=str(PROJECT_ROOT),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        # Extract repo name from URL (handles https and ssh formats)
        repo_name = remote_url.rstrip("/").rsplit("/", 1)[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        if marketplace_name and repo_name and marketplace_name != repo_name:
            report.add(
                "warning",
                f"Marketplace name '{marketplace_name}' does not match "
                f"git repo name '{repo_name}'",
            )
    except (subprocess.CalledProcessError, FileNotFoundError):
        report.add("info", "Could not determine git remote - skipping repo name check")

    # Check 2: plugin name vs source directory name
    for plugin in plugins:
        pname = plugin.get("name", "")
        source = plugin.get("source", "")
        if source:
            dir_name = source.rstrip("/").rsplit("/", 1)[-1]
            if pname and dir_name and pname != dir_name:
                report.add(
                    "warning",
                    f"Plugin '{pname}': name does not match source "
                    f"directory '{dir_name}'",
                )

    # Check 3: marketplace name vs CLAUDE.md project reference
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    if claude_md.exists():
        try:
            claude_content = claude_md.read_text(encoding="utf-8")
            # Look for "# <project-name>" header
            header_match = re.search(r"^#\s+(\S+)", claude_content, re.MULTILINE)
            if header_match:
                claude_project_name = header_match.group(1)
                if marketplace_name and claude_project_name != marketplace_name:
                    report.add(
                        "warning",
                        f"Marketplace name '{marketplace_name}' does not match "
                        f"CLAUDE.md project header '{claude_project_name}'",
                    )
        except Exception:
            pass

    # Color consistency checks
    plugin_colors = {}  # plugin_name -> set of colors used by its agents
    color_to_plugins = {}  # color -> list of plugin names
    for plugin in plugins:
        pname = plugin.get("name", "<unnamed>")
        source = plugin.get("source", "")
        source_path = PROJECT_ROOT / source.lstrip("./")
        colors_in_plugin = set()
        for agent_path in plugin.get("agents", []):
            full_path = source_path / agent_path.lstrip("./")
            if not full_path.exists():
                continue
            fm, _ = parse_frontmatter(full_path)
            if fm and "color" in fm:
                colors_in_plugin.add(fm["color"])
        if colors_in_plugin:
            plugin_colors[pname] = colors_in_plugin
            for c in colors_in_plugin:
                color_to_plugins.setdefault(c, []).append(pname)

    # Warn if agents within the same plugin use different colors
    for pname, colors in plugin_colors.items():
        if len(colors) > 1:
            report.add(
                "warning",
                f"Plugin '{pname}': agents use inconsistent colors: "
                f"{', '.join(sorted(colors))} (expected one color per plugin)",
            )

    # Report color distribution across plugins
    color_summary = []
    for color, pnames in sorted(color_to_plugins.items()):
        color_summary.append(f"{color} ({', '.join(sorted(pnames))})")
    if color_summary:
        report.add("info", f"Color distribution: {'; '.join(color_summary)}")

    # Warn about colors shared by many plugins (potential confusion)
    for color, pnames in sorted(color_to_plugins.items()):
        if len(pnames) > 3:
            report.add(
                "warning",
                f"Color '{color}' is overused ({len(pnames)} plugins): "
                f"{', '.join(sorted(pnames))} - consider diversifying",
            )

    # Category analysis
    categories = {}
    for plugin in plugins:
        cat = plugin.get("category", "uncategorized")
        categories.setdefault(cat, []).append(plugin.get("name"))

    report.add("info", f"Categories: {', '.join(f'{k} ({len(v)})' for k, v in sorted(categories.items()))}")

    # Keyword overlap analysis
    keyword_map = {}
    for plugin in plugins:
        for kw in plugin.get("keywords", []):
            keyword_map.setdefault(kw, []).append(plugin.get("name"))
    shared_kw = {k: v for k, v in keyword_map.items() if len(v) > 1}
    if shared_kw:
        for kw, pnames in sorted(shared_kw.items()):
            report.add("info", f"Shared keyword '{kw}': {', '.join(pnames)}")

    # Dependency validation
    plugin_names = {p.get("name") for p in plugins}
    for plugin in plugins:
        pname = plugin.get("name", "")
        for dep in plugin.get("dependencies", []):
            if dep not in plugin_names:
                report.add(
                    "critical",
                    f"Plugin '{pname}': dependency '{dep}' not found in marketplace",
                )
        for dep in plugin.get("optionalDependencies", []):
            if dep not in plugin_names:
                report.add(
                    "warning",
                    f"Plugin '{pname}': optional dependency '{dep}' not found in marketplace",
                )

    report.print_report()
    return 1 if report.critical else 0


if __name__ == "__main__":
    fix_mode = "--fix" in sys.argv
    sys.exit(audit(fix=fix_mode))
