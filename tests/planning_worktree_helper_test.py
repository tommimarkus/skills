import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "souroldgeezer-policy/skills/git-workflow-policy/references/scripts/planning_worktree.py"
)


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=check,
        text=True,
        capture_output=True,
    )


class PlanningWorktreeHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        git(self.root.parent, "init", "-b", "main", str(self.root))
        git(self.root, "config", "user.name", "Test User")
        git(self.root, "config", "user.email", "test@example.invalid")
        self.write(self.root / "base.txt", "base\n")
        self.write(self.root / ".gitignore", ".worktrees/\n")
        git(self.root, "add", "base.txt", ".gitignore")
        git(self.root, "commit", "-m", "base")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def write(path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def add_worktree(self, name: str) -> Path:
        path = self.root / ".worktrees" / name
        git(self.root, "worktree", "add", "-b", f"task/{name}", str(path), "main")
        return path

    def commit(self, worktree: Path, relative: str, value: str) -> str:
        self.write(worktree / relative, value)
        git(worktree, "add", relative)
        git(worktree, "commit", "-m", relative)
        return git(worktree, "rev-parse", "HEAD").stdout.strip()

    def invoke(self, command: str, worktree: Path, branch: str, *extra: str):
        result = subprocess.run(
            [
                "python",
                str(SCRIPT),
                command,
                "--repo-root",
                str(self.root),
                "--target",
                "main",
                "--branch",
                branch,
                "--worktree",
                str(worktree),
                *extra,
            ],
            text=True,
            capture_output=True,
        )
        return result, json.loads(result.stdout)

    def integrate(self, name: str, worktree: Path, source: str, *extra: str):
        return self.invoke("integrate", worktree, f"task/{name}", "--source-commit", source, *extra)

    def cleanup(self, name: str, worktree: Path, integrated: dict):
        result_path = Path(self.temporary.name) / f"{name}-integrated.json"
        result_path.write_text(json.dumps(integrated), encoding="utf-8")
        return self.invoke(
            "cleanup", worktree, f"task/{name}", "--integrated-result", str(result_path)
        )

    def test_sequential_siblings_rebase_and_fast_forward_with_ancestry(self) -> None:
        first = self.add_worktree("first")
        second = self.add_worktree("second")
        first_source = self.commit(first, "first.txt", "first\n")
        second_source = self.commit(second, "second.txt", "second\n")

        result, one = self.integrate("first", first, first_source)
        self.assertEqual(0, result.returncode, result.stderr)
        result, two = self.integrate("second", second, second_source)
        self.assertEqual(0, result.returncode, result.stderr)

        self.assertEqual("planning-worktree-result-v1", one["schema"])
        self.assertEqual(first_source, one["source_commit"])
        self.assertEqual(second_source, two["source_commit"])
        self.assertNotEqual(second_source, two["rebased_commit"])
        self.assertEqual(one["parent_after"], two["parent_before"])
        self.assertEqual(two["rebased_commit"], two["parent_after"])
        self.assertEqual(
            0, git(self.root, "merge-base", "--is-ancestor", "task/first", "main").returncode
        )
        self.assertEqual(
            0, git(self.root, "merge-base", "--is-ancestor", "task/second", "main").returncode
        )

    def test_patch_equivalent_retirement_introduces_no_content(self) -> None:
        leaf = self.add_worktree("equivalent")
        source = self.commit(leaf, "same.txt", "same\n")
        self.write(self.root / "same.txt", "same\n")
        git(self.root, "add", "same.txt")
        git(self.root, "commit", "-m", "equivalent landing")
        parent = git(self.root, "rev-parse", "HEAD").stdout.strip()

        result, integrated = self.integrate(
            "equivalent", leaf, source, "--require-patch-equivalent"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(parent, integrated["rebased_commit"])
        self.assertEqual(parent, integrated["parent_after"])
        result, cleaned = self.cleanup("equivalent", leaf, integrated)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("cleanup", cleaned["action"])
        self.assertFalse(leaf.exists())
        self.assertNotIn("task/equivalent", git(self.root, "branch", "--list").stdout)

    def test_refuses_dirty_unowned_and_upstream_worktrees(self) -> None:
        leaf = self.add_worktree("refuse")
        source = self.commit(leaf, "work.txt", "work\n")
        self.write(leaf / "dirty.txt", "dirty\n")
        result, value = self.integrate("refuse", leaf, source)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("clean", value["error"])
        (leaf / "dirty.txt").unlink()

        result, value = self.invoke("integrate", leaf, "task/not-refuse", "--source-commit", source)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("registered", value["error"])

        git(leaf, "branch", "--set-upstream-to", "main", "task/refuse")
        result, value = self.integrate("refuse", leaf, source)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("upstream", value["error"])

    def test_conflict_aborts_and_preserves_source_branch(self) -> None:
        leaf = self.add_worktree("conflict")
        source = self.commit(leaf, "base.txt", "leaf\n")
        self.write(self.root / "base.txt", "parent\n")
        git(self.root, "add", "base.txt")
        git(self.root, "commit", "-m", "parent conflict")
        parent = git(self.root, "rev-parse", "HEAD").stdout.strip()

        result, value = self.integrate("conflict", leaf, source)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("conflict", value["error"])
        self.assertEqual(source, git(leaf, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual(parent, git(self.root, "rev-parse", "main").stdout.strip())
        self.assertFalse((leaf / ".git" / "rebase-merge").exists())

    def test_cleanup_requires_integration_and_never_force_deletes(self) -> None:
        leaf = self.add_worktree("ordered")
        source = self.commit(leaf, "ordered.txt", "ordered\n")
        fake = {
            "schema": "planning-worktree-result-v1",
            "ok": True,
            "action": "integrate",
            "repo_root": str(self.root.resolve()),
            "target": "main",
            "branch": "task/ordered",
            "worktree": str(leaf.resolve()),
            "source_commit": source,
            "rebased_commit": source,
            "parent_before": git(self.root, "rev-parse", "main").stdout.strip(),
            "parent_after": source,
        }
        result, value = self.cleanup("ordered", leaf, fake)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("merged", value["error"])
        self.assertTrue(leaf.exists())
        self.assertIn("task/ordered", git(self.root, "branch", "--list").stdout)

        helper = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('branch", "-D', helper)
        self.assertNotIn("--force", helper)
        self.assertNotIn("cherry-pick", helper)


if __name__ == "__main__":
    unittest.main()
