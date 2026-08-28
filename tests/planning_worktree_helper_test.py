import json
import shutil
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

    def test_cleanup_removes_registered_worktree_and_branch(self) -> None:
        leaf = self.add_worktree("ordinary-cleanup")
        source = self.commit(leaf, "ordinary.txt", "ordinary\n")
        result, integrated = self.integrate("ordinary-cleanup", leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)

        result, cleaned = self.cleanup("ordinary-cleanup", leaf, integrated)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("cleanup", cleaned["action"])
        self.assertFalse(leaf.exists())
        self.assertNotIn("task/ordinary-cleanup", git(self.root, "branch", "--list").stdout)

    def test_cleanup_retry_after_worktree_removal_deletes_branch(self) -> None:
        leaf = self.add_worktree("worktree-removed")
        source = self.commit(leaf, "work.txt", "work\n")
        result, integrated = self.integrate("worktree-removed", leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)
        git(self.root, "worktree", "remove", str(leaf))

        result, cleaned = self.cleanup("worktree-removed", leaf, integrated)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("cleanup", cleaned["action"])
        self.assertNotIn("task/worktree-removed", git(self.root, "branch", "--list").stdout)

    def test_cleanup_retry_after_worktree_and_branch_removal_is_idempotent(self) -> None:
        leaf = self.add_worktree("fully-removed")
        source = self.commit(leaf, "work.txt", "work\n")
        result, integrated = self.integrate("fully-removed", leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)
        git(self.root, "worktree", "remove", str(leaf))
        git(self.root, "branch", "-d", "task/fully-removed")

        result, cleaned = self.cleanup("fully-removed", leaf, integrated)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("cleanup", cleaned["action"])
        self.assertEqual(integrated["parent_after"], cleaned["parent_commit"])

    def test_cleanup_refuses_dirty_registered_worktree(self) -> None:
        leaf = self.add_worktree("dirty-cleanup")
        source = self.commit(leaf, "work.txt", "work\n")
        result, integrated = self.integrate("dirty-cleanup", leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)
        self.write(leaf / "dirty.txt", "dirty\n")

        result, value = self.cleanup("dirty-cleanup", leaf, integrated)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("clean", value["error"])
        self.assertTrue(leaf.exists())
        self.assertIn("task/dirty-cleanup", git(self.root, "branch", "--list").stdout)

    def test_cleanup_refuses_integrated_result_identity_mismatch(self) -> None:
        leaf = self.add_worktree("identity-mismatch")
        source = self.commit(leaf, "work.txt", "work\n")
        result, integrated = self.integrate("identity-mismatch", leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)
        mismatched = {**integrated, "worktree": str(leaf.parent / "other")}

        result, value = self.cleanup("identity-mismatch", leaf, mismatched)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("does not own", value["error"])
        self.assertTrue(leaf.exists())
        self.assertIn("task/identity-mismatch", git(self.root, "branch", "--list").stdout)

    def test_missing_worktree_recovery_refuses_stale_registration(self) -> None:
        leaf = self.add_worktree("stale-registration")
        source = self.commit(leaf, "work.txt", "work\n")
        result, integrated = self.integrate("stale-registration", leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)
        shutil.rmtree(leaf)

        result, value = self.cleanup("stale-registration", leaf, integrated)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("stale", value["error"])
        self.assertIn("task/stale-registration", git(self.root, "branch", "--list").stdout)

    def test_missing_worktree_recovery_refuses_unregistered_filesystem_entry(self) -> None:
        leaf = self.add_worktree("unexpected-entry")
        source = self.commit(leaf, "work.txt", "work\n")
        result, integrated = self.integrate("unexpected-entry", leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)
        git(self.root, "worktree", "remove", str(leaf))
        self.write(leaf / "unowned.txt", "unowned\n")

        result, value = self.cleanup("unexpected-entry", leaf, integrated)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("unexpected filesystem entry", value["error"])
        self.assertIn("task/unexpected-entry", git(self.root, "branch", "--list").stdout)

    def test_missing_worktree_recovery_refuses_changed_branch_tip(self) -> None:
        leaf = self.add_worktree("changed-tip")
        source = self.commit(leaf, "work.txt", "work\n")
        result, integrated = self.integrate("changed-tip", leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)
        git(self.root, "worktree", "remove", str(leaf))
        git(self.root, "branch", "-f", "task/changed-tip", integrated["parent_before"])

        result, value = self.cleanup("changed-tip", leaf, integrated)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("integrated commit", value["error"])
        self.assertIn("task/changed-tip", git(self.root, "branch", "--list").stdout)

    def test_missing_worktree_recovery_refuses_branch_upstream(self) -> None:
        leaf = self.add_worktree("upstream-recovery")
        source = self.commit(leaf, "work.txt", "work\n")
        result, integrated = self.integrate("upstream-recovery", leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)
        git(self.root, "worktree", "remove", str(leaf))
        git(
            self.root,
            "branch",
            "--set-upstream-to",
            "main",
            "task/upstream-recovery",
        )

        result, value = self.cleanup("upstream-recovery", leaf, integrated)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("upstream", value["error"])
        self.assertIn("task/upstream-recovery", git(self.root, "branch", "--list").stdout)

    def test_missing_worktree_recovery_refuses_unmerged_branch(self) -> None:
        leaf = self.add_worktree("unmerged-recovery")
        source = self.commit(leaf, "work.txt", "work\n")
        result, integrated = self.integrate("unmerged-recovery", leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)
        git(self.root, "worktree", "remove", str(leaf))
        git(self.root, "reset", "--hard", integrated["parent_before"])

        result, value = self.cleanup("unmerged-recovery", leaf, integrated)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("merged", value["error"])
        self.assertIn("task/unmerged-recovery", git(self.root, "branch", "--list").stdout)

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
            "rebased_tree_changed": False,
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

    def test_batch_commit_ancestry_records_all_members(self) -> None:
        leaf = self.add_worktree("batch-happy")
        first = self.commit(leaf, "m1.txt", "m1\n")
        second = self.commit(leaf, "m2.txt", "m2\n")
        third = self.commit(leaf, "m3.txt", "m3\n")

        result, integrated = self.integrate(
            "batch-happy",
            leaf,
            third,
            "--batch-commit",
            f"step-one={first}",
            "--batch-commit",
            f"step-two={second}",
            "--batch-commit",
            f"step-three={third}",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            {"step-one": first, "step-two": second, "step-three": third},
            integrated["batch_source_commits"],
        )
        self.assertIn("rebased_tree_changed", integrated)
        self.assertIsInstance(integrated["rebased_tree_changed"], bool)

    def test_batch_commit_non_ancestor_fails_before_rebase(self) -> None:
        leaf = self.add_worktree("batch-bad")
        source = self.commit(leaf, "bad.txt", "bad\n")
        other = self.add_worktree("batch-unrelated")
        unrelated = self.commit(other, "unrelated.txt", "unrelated\n")
        before = git(self.root, "rev-parse", "main").stdout.strip()

        result, value = self.integrate(
            "batch-bad", leaf, source, "--batch-commit", f"stepX={unrelated}"
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("not an ancestor", value["error"])
        self.assertIn("stepX", value["error"])
        self.assertEqual(source, git(leaf, "rev-parse", "HEAD").stdout.strip())
        self.assertFalse((leaf / ".git" / "rebase-merge").exists())
        self.assertEqual(before, git(self.root, "rev-parse", "main").stdout.strip())
        self.assertEqual(source, git(self.root, "rev-parse", "task/batch-bad").stdout.strip())

    def test_batch_commit_survives_member_emptied_by_rebase(self) -> None:
        leaf = self.add_worktree("batch-emptied")
        emptied = self.commit(leaf, "shared.txt", "shared\n")
        final = self.commit(leaf, "final.txt", "final\n")
        self.write(self.root / "shared.txt", "shared\n")
        git(self.root, "add", "shared.txt")
        git(self.root, "commit", "-m", "parent already has the shared change")

        result, integrated = self.integrate(
            "batch-emptied",
            leaf,
            final,
            "--batch-commit",
            f"step-emptied={emptied}",
            "--batch-commit",
            f"step-final={final}",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            {"step-emptied": emptied, "step-final": final},
            integrated["batch_source_commits"],
        )

    def test_batch_commit_malformed_values_fail_cleanly(self) -> None:
        leaf = self.add_worktree("batch-malformed")
        source = self.commit(leaf, "work.txt", "work\n")

        result, value = self.integrate(
            "batch-malformed", leaf, source, "--batch-commit", "no-equals-sign"
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("invalid --batch-commit value", value["error"])

        result, value = self.integrate(
            "batch-malformed", leaf, source, "--batch-commit", "step1=short"
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("invalid --batch-commit value", value["error"])

        filler = "a" * 40
        result, value = self.integrate(
            "batch-malformed",
            leaf,
            source,
            "--batch-commit",
            f"dup={filler}",
            "--batch-commit",
            f"dup={filler}",
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("duplicate --batch-commit step id", value["error"])

    def test_rebased_tree_changed_false_when_parent_untouched(self) -> None:
        leaf = self.add_worktree("tree-unchanged")
        source = self.commit(leaf, "unchanged.txt", "unchanged\n")

        result, integrated = self.integrate("tree-unchanged", leaf, source)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(integrated["rebased_tree_changed"])
        self.assertNotIn("batch_source_commits", integrated)

    def test_rebased_tree_changed_true_when_parent_moved(self) -> None:
        leaf = self.add_worktree("tree-changed")
        source = self.commit(leaf, "leaf-only.txt", "leaf\n")
        self.write(self.root / "parent-only.txt", "parent\n")
        git(self.root, "add", "parent-only.txt")
        git(self.root, "commit", "-m", "parent moved")

        result, integrated = self.integrate("tree-changed", leaf, source)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(integrated["rebased_tree_changed"])

    def test_no_batch_commit_omits_batch_source_commits_key(self) -> None:
        leaf = self.add_worktree("no-batch")
        source = self.commit(leaf, "solo.txt", "solo\n")

        result, integrated = self.integrate("no-batch", leaf, source)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("batch_source_commits", integrated)
        self.assertEqual(
            {
                "schema",
                "ok",
                "action",
                "repo_root",
                "target",
                "branch",
                "worktree",
                "source_commit",
                "rebased_commit",
                "parent_before",
                "parent_after",
                "rebased_tree_changed",
            },
            set(integrated),
        )


if __name__ == "__main__":
    unittest.main()
