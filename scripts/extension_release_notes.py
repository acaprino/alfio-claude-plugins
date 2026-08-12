"""Version guard and release-notes extraction for the VS Code extension.

Stdlib only, runs from the repository root:

    python scripts/extension_release_notes.py <tag-or-version>

Accepts vscode-v20.0.0, v20.0.0 or 20.0.0 and normalizes to the bare
version. Two things must agree before a release is cut:

  - exports/vscode/package.json "version" equals the tag's version, so a
    tag can never ship a .vsix carrying a number different from its name.
    The version is also what extension.js compares against the recorded
    manifest to decide whether to re-copy the skills, so a wrong one
    leaves installed skills stale with no visible symptom.
  - exports/vscode/CHANGELOG.md carries a "## <version>" section with
    content, so notes exist before the tag is pushed rather than after.
    The CHANGELOG had drifted seven versions behind package.json before
    this check existed.

On success the CHANGELOG section is printed to stdout, which is what the
release workflow feeds to "gh release create --notes-file". Failures name
the file to fix and exit non-zero.
"""
import io
import json
import re
import sys

MANIFEST = "exports/vscode/package.json"
CHANGELOG = "exports/vscode/CHANGELOG.md"
TAG_PREFIX = re.compile(r"^(?:vscode-)?v?")


def normalize(raw):
    version = TAG_PREFIX.sub("", raw.strip(), count=1)
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        sys.exit(
            f"'{raw}' is not a release tag: expected vscode-vX.Y.Z, vX.Y.Z or X.Y.Z"
        )
    return version


def manifest_version():
    try:
        with io.open(MANIFEST, encoding="utf-8") as handle:
            return json.load(handle)["version"]
    except OSError as err:
        sys.exit(f"cannot read {MANIFEST}: {err}")
    except (ValueError, KeyError) as err:
        sys.exit(f"{MANIFEST} has no readable version: {err}")


def changelog_section(version):
    try:
        with io.open(CHANGELOG, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as err:
        sys.exit(f"cannot read {CHANGELOG}: {err}")

    heading = f"## {version}"
    try:
        start = lines.index(heading) + 1
    except ValueError:
        sys.exit(
            f"{CHANGELOG} has no '{heading}' section; write the release notes "
            f"before tagging"
        )

    end = start
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1

    body = "\n".join(lines[start:end]).strip()
    if not body:
        sys.exit(f"{CHANGELOG} section '{heading}' is empty; write the release notes")
    return body


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/extension_release_notes.py <tag-or-version>")

    version = normalize(sys.argv[1])
    declared = manifest_version()
    if declared != version:
        sys.exit(
            f"tag says {version} but {MANIFEST} says {declared}; bump the manifest "
            f"or retag"
        )

    print(changelog_section(version))


if __name__ == "__main__":
    main()
