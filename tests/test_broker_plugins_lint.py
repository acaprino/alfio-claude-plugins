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
{scope_line}
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
          scope="single-broker", per_broker_section=False,
          refs=("orders.md",), listed=("orders.md",), agent=True, command=True,
          register=True, verify=False, probe=False, register_verify=False,
          category="algotrading", sections=None):
    """Write one plugin plus a marketplace.json describing it.

    scope=None omits the **Scope:** line entirely (for the missing-declaration
    test). per_broker_section=True appends a '## What varies per broker'
    heading, which a multi-broker-platform plugin needs to pass.
    """
    broker = name[:-len("-trading")] if name.endswith("-trading") else name
    plugin = root / "plugins" / name
    skill = plugin / "skills" / name
    (skill / "references").mkdir(parents=True)
    scope_line = f"**Scope:** {scope}\n" if scope is not None else ""
    body = SKILL_TEMPLATE.format(skill=name, broker=broker, level=level,
                                 archetype=archetype, scope_line=scope_line)
    if sections is not None:
        body = sections
    listing = "\n".join(f"- `{r}` - description" for r in listed)
    body = body.replace("- `orders.md` - how orders behave", listing)
    if per_broker_section:
        body += "\n## What varies per broker\n\nFill mode and account mode vary by broker.\n"
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

    def test_empty_references_directory_fails(self):
        """references/ exists (build() always creates it) but holds no .md
        file: base level requires at least one, not just the directory."""
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), refs=(), listed=())
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("references/ directory", result.stdout + result.stderr)

    def test_missing_references_directory_fails(self):
        """references/ does not exist at all, the harder case: on_disk must
        come back empty rather than error, and still fail the same way as
        the empty-directory case above."""
        with tempfile.TemporaryDirectory() as tmp:
            root = build(Path(tmp), refs=(), listed=())
            ref_dir = (root / "plugins" / "acme-trading" / "skills" / "acme-trading"
                       / "references")
            ref_dir.rmdir()
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("references/ directory", result.stdout + result.stderr)

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
            # probe=True writes references/open-questions.md on disk (see build()
            # above); a plugin is not fully conformant unless that file is also
            # listed in the Reference materials section, same as any other
            # reference, so it must be added to `listed` here too.
            build(Path(tmp), level="verified", verify=True, probe=True,
                  register_verify=True, listed=("orders.md", "open-questions.md"))
            result = run(Path(tmp))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_scope_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), scope=None)
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Scope", result.stdout + result.stderr)

    def test_unknown_scope_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), scope="some-other-thing")
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("some-other-thing", result.stdout + result.stderr)

    def test_multi_broker_platform_without_variation_section_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), scope="multi-broker-platform", per_broker_section=False)
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("varies per broker", result.stdout + result.stderr)

    def test_multi_broker_platform_with_variation_section_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), scope="multi-broker-platform", per_broker_section=True)
            result = run(Path(tmp))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_single_broker_needs_no_variation_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), scope="single-broker", per_broker_section=False)
            result = run(Path(tmp))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_two_archetypes_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), archetype="local-terminal, direct-api")
            result = run(Path(tmp))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_archetype_list_with_bad_token_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(Path(tmp), archetype="local-terminal, socket-thing")
            result = run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("socket-thing", result.stdout + result.stderr)

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
