"""What the publication workflow must and must not do.

The mirror workflow it replaces wrote one host's export. This one writes all
three or none, because a marketplace where one host is a commit ahead of the
others is the drift the whole compiler exists to prevent.

Its release step is pinned here for the same reason the guard above it is. A
release keyed on the push instead of on `metadata.version` would publish a tag
per commit and make the Releases page a commit log, and a release carrying an
asset would resurrect the download-and-install path the universal cutover
removed. Both are one careless edit away, and neither shows up as a build
failure.
"""

import shlex
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO_ROOT / ".github/workflows"

PUBLISH = WORKFLOWS / "publish-marketplaces.yml"
CONSISTENCY = WORKFLOWS / "consistency.yml"

STAGED_PATHS = (
    "exports/claude",
    "exports/copilot",
    "exports/codex",
    ".claude-plugin/marketplace.json",
    ".github/plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
)

FORBIDDEN = ("vsce", "exports/vscode", "gen_extension_manifest.py", "mirror_export.py")

# `gh release create` flags that consume the token after them. Anything else that
# is not a flag is a positional, and a positional after the tag is an upload.
VALUE_FLAGS = frozenset(
    {
        "--target",
        "--title",
        "--notes",
        "--notes-file",
        "--notes-start-tag",
        "--discussion-category",
    }
)


def workflow_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class PublishWorkflowContractTests(unittest.TestCase):
    def test_the_publication_workflow_exists(self):
        self.assertTrue(PUBLISH.is_file(), f"missing: {PUBLISH}")

    def test_the_mirror_workflow_is_gone(self):
        self.assertFalse((WORKFLOWS / "mirror-export.yml").exists())

    def test_publication_runs_the_universal_check(self):
        text = workflow_text(PUBLISH)
        self.assertIn("scripts/daodan_build.py --check", text)
        self.assertIn("scripts/daodan_build.py", text)

    def test_publication_stages_every_host(self):
        text = workflow_text(PUBLISH)
        for path in STAGED_PATHS:
            with self.subTest(path=path):
                self.assertIn(path, text)

    def test_publication_guards_against_answering_itself(self):
        text = workflow_text(PUBLISH)
        self.assertIn("github-actions[bot]", text)
        self.assertIn("concurrency", text)

    def test_publication_commit_message_is_fixed(self):
        self.assertIn("Publish native Daodan marketplaces", workflow_text(PUBLISH))

    def test_consistency_runs_the_drift_gate(self):
        self.assertIn("scripts/daodan_build.py --check", workflow_text(CONSISTENCY))

    def test_consistency_pins_python_311_or_later(self):
        text = workflow_text(CONSISTENCY)
        self.assertNotIn("python-version: '3.10'", text)
        self.assertIn("python-version:", text)

    def test_no_workflow_mentions_the_extension_surface(self):
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = workflow_text(path)
            for token in FORBIDDEN:
                with self.subTest(workflow=path.name, token=token):
                    self.assertNotIn(token, text)


class ReleaseStepContractTests(unittest.TestCase):
    """The Releases page carries one assetless tag per published version."""

    def setUp(self):
        self.text = workflow_text(PUBLISH)

    def release_create_arguments(self) -> list[str]:
        """The `gh release create` invocation, flattened across its continuations."""
        lines = self.text.splitlines()
        start = next(
            index
            for index, line in enumerate(lines)
            if line.strip().startswith("gh release create")
        )
        collected = []
        for line in lines[start:]:
            stripped = line.strip()
            collected.append(stripped.removesuffix("\\").strip())
            if not stripped.endswith("\\"):
                break
        return shlex.split(" ".join(collected))

    def test_publication_creates_a_release_for_the_marketplace_version(self):
        self.assertIn("gh release create", self.text)
        self.assertIn(".claude-plugin/marketplace.json", self.text)
        self.assertIn("['metadata']['version']", self.text)
        self.assertIn('tag="v${version}"', self.text)

    def test_the_release_is_keyed_on_the_version_not_on_the_push(self):
        """A second push at the same version must find its release and stop."""
        self.assertIn('gh release view "$tag"', self.text)
        view = self.text.index('gh release view "$tag"')
        create = self.text.index("gh release create")
        self.assertLess(view, create)
        self.assertIn("already published", self.text)

    def test_the_release_carries_no_asset(self):
        arguments = self.release_create_arguments()
        self.assertEqual(arguments[:3], ["gh", "release", "create"])
        rest = arguments[3:]
        self.assertEqual(rest[0], "$tag")

        positionals = []
        index = 1
        while index < len(rest):
            token = rest[index]
            if token in VALUE_FLAGS:
                index += 2
            elif token.startswith("--"):
                index += 1
            else:
                positionals.append(token)
                index += 1

        self.assertEqual(
            positionals,
            [],
            f"gh release create uploads asset(s): {positionals}",
        )

    def test_the_release_targets_the_commit_it_published(self):
        self.assertIn('--target "$(git rev-parse HEAD)"', self.text)

    def test_the_release_runs_after_the_publication_commit(self):
        self.assertLess(self.text.index("git push"), self.text.index("gh release create"))

    def test_the_release_does_not_revive_the_extension_tag_scheme(self):
        self.assertNotIn("vscode-v", self.text)


if __name__ == "__main__":
    unittest.main()
