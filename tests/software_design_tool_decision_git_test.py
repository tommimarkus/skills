import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import compact, read


PROCEDURE = (
    "souroldgeezer-design/skills/software-design/references/procedures/"
    "native-tool-evidence.md"
)
KEY = "softwaredesign.tool-decision-typescript-unchecked-index-evidence"
VALUE = "defer-until:2026-09-08"


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    )


class SoftwareDesignToolDecisionGitTest(unittest.TestCase):
    def test_documented_commands_keep_decisions_in_git_local_scope(self) -> None:
        procedure = compact(read(PROCEDURE))

        self.assertIn(f"git config --local {KEY} {VALUE}", procedure)
        self.assertIn(f"git config --local --get {KEY}", procedure)
        self.assertIn("git config --local --get-regexp '^softwaredesign\\.tool-decision-'", procedure)
        self.assertIn(f"git config --local --unset-all {KEY}", procedure)
        self.assertIn("`softwaredesign.tool-decision-*`", procedure)
        self.assertIn("Never use global or worktree configuration, raw `.git` writes", procedure)
        self.assertIn("https://git-scm.com/docs/git-config/2.51.2.html", procedure)
        self.assertIn("https://git-scm.com/docs/git-worktree.html", procedure)

    def test_local_decision_is_visible_from_a_linked_worktree_and_can_be_cleared(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "clone"
            linked = Path(temporary) / "linked"
            root.mkdir()
            git(root, "init")
            git(root, "config", "user.email", "test@example.invalid")
            git(root, "config", "user.name", "Test User")
            (root / "README.md").write_text("fixture\n", encoding="utf-8")
            git(root, "add", "README.md")
            git(root, "commit", "-m", "fixture")
            git(root, "branch", "linked-branch")
            git(root, "worktree", "add", str(linked), "linked-branch")

            git(root, "config", "--local", KEY, VALUE)
            observed = git(linked, "config", "--local", "--get", KEY).stdout.strip()
            self.assertEqual(VALUE, observed)

            git(linked, "config", "--local", "--unset-all", KEY)
            absent = subprocess.run(
                ["git", "-C", str(root), "config", "--local", "--get", KEY],
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, absent.returncode)


if __name__ == "__main__":
    unittest.main()
