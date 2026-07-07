import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, write_fixture as write

CHECKER = REPO_ROOT / "scripts" / "check-runtime-metadata-parity.py"


def run_checker(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--check", str(repo)],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class RuntimeMetadataParityTest(unittest.TestCase):
    def _run_with_broken_fixture(self, rel_path: str, content: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            write(repo / rel_path, content)
            return run_checker(repo)

    def _assert_broken_fixture_flags(self, rel_path: str, content: str, *expect_in_stdout: str
                                      ) -> subprocess.CompletedProcess[str]:
        result = self._run_with_broken_fixture(rel_path, content)
        self.assertNotEqual(result.returncode, 0)
        for substring in expect_in_stdout:
            self.assertIn(substring, result.stdout)
        return result

    def test_clean_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)

            result = run_checker(repo)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Runtime metadata parity OK", result.stdout)

    def test_skill_description_drift_is_detected(self) -> None:
        self._assert_broken_fixture_flags(
            "souroldgeezer-example/agents/example-skill.md",
            """
            ---
            name: example-skill
            description: Use when this Claude agent has drifted away.
            ---

            Use the matching skill as source of truth.
            """,
            "Runtime metadata parity failed",
            "souroldgeezer-example/agents/example-skill.md",
            "description",
        )

    def test_plugin_manifest_missing_version_is_detected(self) -> None:
        self._assert_broken_fixture_flags(
            "souroldgeezer-example/.claude-plugin/plugin.json",
            """
            {
              "name": "souroldgeezer-example",
              "description": "Example plugin for runtime metadata parity tests.",
              "author": {"name": "Sour Old Geezer", "email": "test@example.invalid"},
              "license": "MIT"
            }
            """,
            "souroldgeezer-example/.claude-plugin/plugin.json",
            "version",
        )

    def test_marketplace_entry_with_version_key_is_detected(self) -> None:
        # plugin.json#version is the sole authority (Claude Code always resolves
        # it over a marketplace-entry copy without warning); a marketplace entry
        # carrying a version key is flagged even when the value matches.
        self._assert_broken_fixture_flags(
            ".claude-plugin/marketplace.json",
            """
            {
              "name": "souroldgeezer",
              "plugins": [
                {
                  "name": "souroldgeezer-example",
                  "source": "./souroldgeezer-example",
                  "version": "0.1.0",
                  "description": "Example plugin for runtime metadata parity tests."
                }
              ]
            }
            """,
            ".claude-plugin/marketplace.json",
            "version",
        )

    def test_docs_plugin_links_must_be_relative_to_doc(self) -> None:
        self._assert_broken_fixture_flags(
            "docs/plugins/example.md",
            """
            # `souroldgeezer-example`

            | Skill | Summary |
            |---|---|
            | [example-skill](souroldgeezer-example/skills/example-skill/SKILL.md) | Broken from docs/plugins |
            """,
            "docs/plugins/example.md",
            "[example-skill](../../souroldgeezer-example/skills/example-skill/SKILL.md)",
        )

    def test_shared_internal_skill_without_claude_wrapper_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            (repo / ".claude" / "skills" / "internal-review" / "SKILL.md").unlink()

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".claude/skills/internal-review/SKILL.md", result.stdout)
        self.assertIn("exists", result.stdout)
        self.assertIn("present", result.stdout)
        self.assertIn("missing", result.stdout)

    def test_orphan_claude_wrapper_without_shared_skill_is_detected(self) -> None:
        self._assert_broken_fixture_flags(
            ".claude/skills/orphan-review/SKILL.md",
            """
            ---
            name: orphan-review
            description: No shared internal skill owns this Claude wrapper.
            ---

            # Orphan Review
            """,
            ".claude/skills/orphan-review/SKILL.md",
            "source-of-truth",
            "internal-skills/orphan-review/SKILL.md",
        )

    def test_internal_claude_wrapper_must_point_to_shared_skill(self) -> None:
        self._assert_broken_fixture_flags(
            ".claude/skills/internal-review/SKILL.md",
            """
            ---
            name: internal-review
            description: Use when reviewing the internal authoring workflow.
            ---

            # Internal Review

            This wrapper accidentally duplicates workflow text instead of
            delegating to the neutral shared source.
            """,
            ".claude/skills/internal-review/SKILL.md",
            "source-of-truth",
            "internal-skills/internal-review/SKILL.md",
        )

    def test_internal_skill_wrapper_is_keyed_by_directory_when_frontmatter_name_drifts(self) -> None:
        result = self._assert_broken_fixture_flags(
            "internal-skills/internal-review/SKILL.md",
            """
            ---
            name: drifted-internal
            description: Use when reviewing the internal authoring workflow.
            ---

            # Internal Review
            """,
            "internal-skills/internal-review/SKILL.md",
            "name",
        )
        self.assertNotIn(".claude/skills/internal-review/SKILL.md :: source-of-truth", result.stdout)

    def make_clean_fixture(self, repo: Path) -> None:
        plugin_description = "Example plugin for runtime metadata parity tests."
        skill_description = "Use when checking runtime metadata parity for an example skill."
        internal_description = "Use when reviewing the internal authoring workflow."
        write(
            repo / ".claude-plugin/marketplace.json",
            f"""
            {{
              "name": "souroldgeezer",
              "plugins": [
                {{
                  "name": "souroldgeezer-example",
                  "source": "./souroldgeezer-example",
                  "description": "{plugin_description}"
                }}
              ]
            }}
            """,
        )
        write(
            repo / "souroldgeezer-example/.claude-plugin/plugin.json",
            f"""
            {{
              "name": "souroldgeezer-example",
              "version": "0.1.0",
              "description": "{plugin_description}",
              "author": {{"name": "Sour Old Geezer", "email": "test@example.invalid"}},
              "license": "MIT"
            }}
            """,
        )
        write(
            repo / "souroldgeezer-example/skills/example-skill/SKILL.md",
            f"""
            ---
            name: example-skill
            description: {skill_description}
            ---

            # Example Skill
            """,
        )
        write(
            repo / "souroldgeezer-example/agents/example-skill.md",
            f"""
            ---
            name: example-skill
            description: {skill_description}
            ---

            Use the matching skill as source of truth.
            """,
        )
        write(
            repo / "README.md",
            """
            # Example Marketplace

            ## What's in `souroldgeezer-example`

            | Skill | Summary | Extensions |
            |---|---|---|
            | [example-skill](souroldgeezer-example/skills/example-skill/SKILL.md) | Example parity checks | none |
            """,
        )
        write(
            repo / "docs/plugins/example.md",
            """
            # `souroldgeezer-example`

            | Skill | Summary |
            |---|---|
            | [example-skill](../../souroldgeezer-example/skills/example-skill/SKILL.md) | Example parity checks |
            """,
        )
        write(
            repo / "internal-skills/internal-review/SKILL.md",
            f"""
            ---
            name: internal-review
            description: {internal_description}
            ---

            # Internal Review
            """,
        )
        write(
            repo / ".claude/skills/internal-review/SKILL.md",
            f"""
            ---
            name: internal-review
            description: {internal_description}
            ---

            # Internal Review

            Read `internal-skills/internal-review/SKILL.md` and follow it as the
            source of truth.
            """,
        )


if __name__ == "__main__":
    unittest.main()
