"""Mirror plugins/ into exports/vscode/, and report what a machine cannot mirror.

Stdlib only, runs from the repository root:

    python scripts/mirror_export.py            # fix in place, always exits 0
    python scripts/mirror_export.py --check    # report, change nothing, exit non-zero
    python scripts/mirror_export.py --check --since <rev>   # also flag stale adapted files

Fixing and gating are separate on purpose. Fix mode reports what it cannot fix and
still succeeds, because a missing changelog entry is no reason to withhold a mirror
that is already computed and correct. `--check` is the gate, and in CI it runs after
the mirror is committed.

The mirror obligation has been global since the 2026-07-30 catalog build: every
plugin feeds a bundle, so every plugin change is a candidate mirror. Doing that by
hand is what let `marketplace-ops/skills-creator/references/conventions.md` sit at a
superseded version of its source, in a bundle nothing adapts, for as long as nobody
happened to diff it.

Only half the export is mechanical, and the split is the whole design here.

  BYTE-COPY   Reference files, scripts and assets under a skill directory. They name
              no tool and no agent, so the port never rewrote them. This script owns
              them: it copies, and drift is a bug it fixes rather than reports.

  ADAPTED     Agents, prompts, every SKILL.md, and the handful of reference files
              carrying a tool rename or a vendoring header. Porting these means
              rewriting frontmatter, renaming tools, stripping plugin namespaces and
              rerouting dispatch. This script never writes them. What it can do is
              notice that a source moved while its export twin did not, which is the
              failure a green structural check has always been compatible with.

`_pipelines` is excluded wholesale. It carries three plugins plus 14 vendored
superpowers skills whose upstream is not `plugins/` at all, so no path rule maps it.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

EXPORT = Path("exports/vscode")
PLUGINS = Path("plugins")
MARKETPLACE = Path(".claude-plugin/marketplace.json")
CHANGELOG = EXPORT / "CHANGELOG.md"
PACKAGE = EXPORT / "package.json"

# Bundles this script does not map. `_pipelines` carries three plugins and vendored
# upstream content; its layout is a decision, not a derivation.
SKIP_BUNDLES = {"_pipelines"}

# Reference files that are adapted despite living beside byte-copies. Each was
# verified by reading the diff: a tool rename, a stripped plugin namespace, or the
# vendoring header the port adds. Copying over one would silently un-port it.
ADAPTED_REFERENCES = {
    "browser-extensions/firefox-extension-dev/references/mdn-api-urls.md",
    "trading-broker-integration/ibkr/references/gateway-verification.md",
    "digital-marketing/ga4-implementation/references/diagnostics-troubleshooting.md",
    "pwa-expert/pwa-development/references/production-checklist.md",
    "testing/test-hygiene/references/prevention-rules.md",
    "testing/test-hygiene/references/remediation-workflow.md",
    "testing/test-hygiene/references/runner-playbook.md",
}


def is_build_artifact(path: Path) -> bool:
    """Compiled bytecode and its directory. A `__pycache__/` was copied into a bundle
    once during the catalog build; a source-side one has no business having a twin."""
    return "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}


def source_candidates(bundle: str, subpath: str) -> list[Path]:
    """Where a skill-directory file could come from upstream.

    Most sit under `plugins/<bundle>/skills/`. A few live at the plugin root in a
    directory named for what they are rather than for the skill that consumes them:
    `research/scripts/webfetch.py`, `peer-review/mcp/server.py`, the peer-review
    protocol documents, `ai-tooling/references/reasoning-patterns.md`.
    """
    name = Path(subpath).name
    return [
        PLUGINS / bundle / "skills" / subpath,
        PLUGINS / bundle / "scripts" / name,
        PLUGINS / bundle / "mcp" / name,
        PLUGINS / bundle / "protocol" / name,
        PLUGINS / bundle / "references" / name,
    ]


def classify(path: Path):
    """(kind, source) for an export file, or (None, None) when it has no upstream.

    Orchestrator agents, the bundle READMEs and the catalog README are export-only:
    they exist to satisfy constraints the host imposes and have nothing to mirror.
    """
    rel = path.relative_to(EXPORT)
    if len(rel.parts) < 2 or rel.parts[0] in SKIP_BUNDLES or ".github" not in rel.parts:
        return None, None
    bundle, tail = rel.parts[0], "/".join(rel.parts[1:])

    if tail.startswith(".github/agents/") and path.name.endswith(".agent.md"):
        src = PLUGINS / bundle / "agents" / (path.name[: -len(".agent.md")] + ".md")
        return ("adapted", src) if src.exists() else (None, None)

    if tail.startswith(".github/prompts/") and path.name.endswith(".prompt.md"):
        src = PLUGINS / bundle / "commands" / (path.name[: -len(".prompt.md")] + ".md")
        return ("adapted", src) if src.exists() else (None, None)

    if ".github/skills/" in tail:
        subpath = tail.split(".github/skills/", 1)[1]
        for candidate in source_candidates(bundle, subpath):
            if candidate.exists():
                if path.name == "SKILL.md" or f"{bundle}/{subpath}" in ADAPTED_REFERENCES:
                    return "adapted", candidate
                return "byte-copy", candidate
        return None, None

    return None, None


def marketplace_version() -> str:
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))["metadata"]["version"]


def set_package_version(version: str) -> bool:
    """Rewrite only the version line. json.dump would reformat the whole manifest and
    bury the change in noise, and this file is read by humans reviewing a bot commit."""
    raw = PACKAGE.read_bytes()
    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.split(newline)
    for i, line in enumerate(lines):
        text = line.decode("utf-8")
        if re.match(r'\s*"version"\s*:', text):
            updated = re.sub(r'("version"\s*:\s*")[^"]*(")', rf"\g<1>{version}\g<2>", text)
            if updated == text:
                return False
            lines[i] = updated.encode("utf-8")
            PACKAGE.write_bytes(newline.join(lines))
            return True
    raise SystemExit("exports/vscode/package.json has no version field")


def changelog_has(version: str) -> bool:
    pattern = re.compile(rf"^##\s+{re.escape(version)}\s*$", re.MULTILINE)
    match = pattern.search(CHANGELOG.read_text(encoding="utf-8"))
    if not match:
        return False
    rest = CHANGELOG.read_text(encoding="utf-8")[match.end():]
    body = rest.split("\n## ", 1)[0]
    return bool(body.strip())


def changed_since(rev: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{rev}..HEAD"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"git diff against '{rev}' failed: {result.stderr.strip()}")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="report without writing; exit non-zero on any finding")
    parser.add_argument("--since", metavar="REV",
                        help="flag adapted files whose source changed in REV..HEAD "
                             "while the export twin did not")
    args = parser.parse_args()

    if not EXPORT.is_dir():
        print(f"run from the repository root: {EXPORT} not found")
        return 2

    copied, adapted, orphans = [], [], []
    for path in sorted(EXPORT.rglob("*")):
        if not path.is_file() or is_build_artifact(path):
            continue
        kind, source = classify(path)
        if kind == "byte-copy":
            if source.read_bytes() != path.read_bytes():
                copied.append((path, source))
        elif kind == "adapted":
            adapted.append((path, source))

    # A source file with no export twin is a bundle that was never generated for it.
    # Only skills are checked: agents and prompts are deliberately not all exported.
    for source in sorted(PLUGINS.glob("*/skills/*/**/*")):
        if not source.is_file() or is_build_artifact(source):
            continue
        bundle = source.parts[1]
        if bundle in SKIP_BUNDLES or not (EXPORT / bundle).is_dir():
            continue
        subpath = "/".join(source.parts[3:])
        twin = EXPORT / bundle / ".github/skills" / subpath
        if not twin.exists():
            orphans.append(source)

    stale = []
    if args.since:
        touched = changed_since(args.since)
        for path, source in adapted:
            if str(source).replace("\\", "/") in touched:
                if str(path).replace("\\", "/") not in touched:
                    stale.append((path, source))

    version = marketplace_version()
    version_stale = json.loads(PACKAGE.read_text(encoding="utf-8"))["version"] != version

    print(f"byte-copy files out of date : {len(copied)}")
    print(f"adapted files tracked        : {len(adapted)}")
    print(f"source files with no twin    : {len(orphans)}")
    print(f"extension version            : {'stale' if version_stale else 'current'} "
          f"(marketplace {version})")
    if args.since:
        print(f"adapted files left behind    : {len(stale)}")
    print()

    for path, source in copied:
        print(f"  {'would copy' if args.check else 'copied'}  {source} -> {path}")
    for source in orphans:
        print(f"  no export twin  {source}")
    for path, source in stale:
        print(f"  STALE  {source} changed, {path} did not")

    if args.check:
        problems = len(copied) + len(orphans) + len(stale) + (1 if version_stale else 0)
        if not changelog_has(version):
            print(f"  CHANGELOG.md has no non-empty '## {version}' section")
            problems += 1
        print()
        print("mirror is current" if not problems else f"{problems} finding(s)")
        return 1 if problems else 0

    for path, source in copied:
        path.write_bytes(source.read_bytes())
    if version_stale:
        set_package_version(version)
        print(f"  extension version -> {version}")

    # Fix mode reports what it cannot fix and still succeeds. Failing here would
    # block the mirror it just computed from being committed, over a defect the
    # mirror is not the remedy for. `--check` is the gate; run it afterwards.
    if stale:
        print()
        print("Adapted files whose source moved. Re-port them by hand; this script "
              "will not guess at an adaptation.")
    if orphans:
        print()
        print("Source files with no export twin. A bundle is missing content.")
    if not changelog_has(version):
        print()
        print(f"exports/vscode/CHANGELOG.md needs a '## {version}' section describing "
              f"this release. The version is computed; the prose is not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
