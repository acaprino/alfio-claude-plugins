"""Version-bump check for plugin changes, over a git commit range.

Stdlib only, runs from the repository root:

    python scripts/check_version_bumps.py <base-rev> [<head-rev>]

head-rev defaults to HEAD. Enforces steps 1 and 2 of the marketplace update
workflow in CLAUDE.md: when a commit range touches files under
plugins/<name>/, that plugin's version in .claude-plugin/marketplace.json must
change across the range, and so must metadata.version. Exits non-zero on
violations.

Cases handled per changed plugin directory:

  - registered at both ends      version must differ between base and head
  - registered only at head      new plugin, ok
  - unregistered at head, dir    error: plugin files exist but the plugin is
    still present                not in marketplace.json
  - unregistered at head, dir    plugin removal, ok
    gone

CI derives the range from github.event.before (push) or the PR base sha and
skips gracefully when the base commit is unknown (branch creation, force
push with pruned history).
"""
import json
import subprocess
import sys
from collections import defaultdict

MANIFEST = ".claude-plugin/marketplace.json"


def git(*args):
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def manifest_at(rev):
    result = subprocess.run(
        ["git", "show", f"{rev}:{MANIFEST}"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        return {"metadata": {}, "plugins": []}
    return json.loads(result.stdout)


def versions_of(manifest):
    return {p["name"]: p.get("version") for p in manifest.get("plugins", [])}


def dir_exists_at(rev, name):
    result = subprocess.run(
        ["git", "ls-tree", "-d", rev, f"plugins/{name}"],
        capture_output=True, text=True, encoding="utf-8",
    )
    return result.returncode == 0 and result.stdout.strip() != ""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip().splitlines()[2].strip())
    base = sys.argv[1]
    head = sys.argv[2] if len(sys.argv) > 2 else "HEAD"

    changed = git("diff", "--name-only", base, head, "--", "plugins/").splitlines()
    plugins_touched = defaultdict(list)
    for path in changed:
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == "plugins":
            plugins_touched[parts[1]].append(path)

    if not plugins_touched:
        print(f"no plugin changes in {base}..{head}")
        return

    base_versions = versions_of(manifest_at(base))
    head_manifest = manifest_at(head)
    head_versions = versions_of(head_manifest)

    problems = []
    for name in sorted(plugins_touched):
        n_files = len(plugins_touched[name])
        if name in head_versions:
            if name in base_versions and base_versions[name] == head_versions[name]:
                problems.append(
                    f"plugins/{name}: {n_files} file(s) changed but version stayed "
                    f"at {head_versions[name]}; bump it in {MANIFEST}")
        elif dir_exists_at(head, name):
            problems.append(
                f"plugins/{name}: {n_files} file(s) changed but the plugin is not "
                f"registered in {MANIFEST}")
        # dir gone at head: plugin removal, nothing to check

    base_meta = manifest_at(base).get("metadata", {}).get("version")
    head_meta = head_manifest.get("metadata", {}).get("version")
    if base_meta == head_meta:
        problems.append(
            f"metadata.version stayed at {head_meta} despite plugin changes "
            f"({', '.join(sorted(plugins_touched))}); bump it in {MANIFEST}")

    if problems:
        print(f"FAIL  version bumps ({base}..{head}):")
        for p in problems:
            print("        ", p)
        sys.exit(1)
    print(f"ok    version bumps: {', '.join(sorted(plugins_touched))} all bumped, "
          f"metadata {base_meta} -> {head_meta}")


if __name__ == "__main__":
    main()
