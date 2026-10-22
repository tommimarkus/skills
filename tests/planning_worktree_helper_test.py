import json
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "souroldgeezer-policy/skills/git-workflow-policy/references/scripts/planning_worktree.py"
)
SPEC = importlib.util.spec_from_file_location("planning_worktree", SCRIPT)
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


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
        self.process_env = None
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

    def invoke(
        self,
        command: str,
        worktree: Path,
        branch: str,
        *extra: str,
        repo_root: Path | None = None,
        target: str = "main",
    ):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                command,
                "--repo-root",
                str(repo_root or self.root),
                "--target",
                target,
                "--branch",
                branch,
                "--worktree",
                str(worktree),
                *extra,
            ],
            text=True,
            capture_output=True,
            env=self.process_env,
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

        # Record every git invocation the helper makes while it refuses and then
        # succeeds at cleanup, so a force delete cannot hide in an unexecuted branch.
        shim_dir = Path(self.temporary.name) / "shim"
        shim_dir.mkdir()
        log = Path(self.temporary.name) / "git-argv.log"
        real_git = shutil.which("git")
        shim = shim_dir / "git"
        shim.write_text(
            f'#!/bin/sh\nprintf \'%s\\n\' "$*" >> "{log}"\nexec "{real_git}" "$@"\n',
            encoding="utf-8",
        )
        shim.chmod(0o755)
        self.process_env = {**os.environ, "PATH": f"{shim_dir}{os.pathsep}{os.environ['PATH']}"}

        refused, _ = self.cleanup("ordered", leaf, fake)
        self.assertNotEqual(0, refused.returncode)

        done = self.add_worktree("landed")
        landed_source = self.commit(done, "landed.txt", "landed\n")
        result, integrated = self.integrate("landed", done, landed_source)
        self.assertEqual(0, result.returncode, result.stderr)
        result, cleaned = self.cleanup("landed", done, integrated)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(done.exists())

        calls = log.read_text(encoding="utf-8").splitlines()
        self.assertTrue(any("branch" in call and "--merged" in call for call in calls), calls)
        for call in calls:
            self.assertNotIn(" -D", call)
            self.assertNotIn("--force", call)
            self.assertNotIn("cherry-pick", call)

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

    def test_batch_commit_accepts_both_supported_object_id_lengths(self) -> None:
        sha1 = "a" * 40
        sha256 = "b" * 64
        self.assertEqual(
            {"sha1": sha1, "sha256": sha256},
            HELPER.parse_batch_commits([f"sha1={sha1}", f"sha256={sha256}"]),
        )
        for malformed in ("a" * 39, "a" * 41, "a" * 63, "a" * 64 + "g", "a" * 65):
            with self.assertRaises(HELPER.Error):
                HELPER.parse_batch_commits([f"member={malformed}"])

    def test_batch_evidence_accepts_sha256_ids_and_rejects_malformed_ids(self) -> None:
        leaf = self.add_worktree("batch-evidence-format")
        source = self.commit(leaf, "work.txt", "work\n")
        result_path = Path(self.temporary.name) / "integrated.json"
        integrated = {
            "schema": "planning-worktree-result-v1",
            "ok": True,
            "action": "integrate",
            "repo_root": str(self.root),
            "target": "main",
            "branch": "task/batch-evidence-format",
            "worktree": str(leaf),
            "source_commit": source,
            "rebased_commit": source,
            "parent_before": git(self.root, "rev-parse", "main").stdout.strip(),
            "parent_after": source,
            "rebased_tree_changed": False,
            "batch_source_commits": {"member": "c" * 64},
        }
        result_path.write_text(json.dumps(integrated), encoding="utf-8")
        self.assertEqual(integrated, HELPER.read_integrated(str(result_path)))

        integrated["batch_source_commits"]["member"] = "c" * 63 + "Z"
        result_path.write_text(json.dumps(integrated), encoding="utf-8")
        with self.assertRaisesRegex(HELPER.Error, "invalid integrated batch source commits"):
            HELPER.read_integrated(str(result_path))

    def test_sha256_git_batch_integration_and_cleanup_retry(self) -> None:
        root = Path(self.temporary.name) / "sha256-repo"
        initialized = subprocess.run(
            ["git", "init", "--object-format=sha256", "-b", "main", str(root)],
            text=True,
            capture_output=True,
        )
        if initialized.returncode:
            self.skipTest("installed Git does not support SHA-256 repositories")
        git(root, "config", "user.name", "Test User")
        git(root, "config", "user.email", "test@example.invalid")
        self.write(root / "base.txt", "base\n")
        self.write(root / ".gitignore", ".worktrees/\n")
        git(root, "add", "base.txt", ".gitignore")
        git(root, "commit", "-m", "base")
        leaf = root / ".worktrees" / "sha256-batch"
        git(root, "worktree", "add", "-b", "task/sha256-batch", str(leaf), "main")
        first = self.commit(leaf, "first.txt", "first\n")
        second = self.commit(leaf, "second.txt", "second\n")

        def invoke(command: str, *extra: str):
            return subprocess.run(
                [
                    sys.executable, str(SCRIPT), command,
                    "--repo-root", str(root), "--target", "main",
                    "--branch", "task/sha256-batch", "--worktree", str(leaf), *extra,
                ],
                text=True,
                capture_output=True,
            )

        integrated_result = invoke(
            "integrate", "--source-commit", second,
            "--batch-commit", f"first={first}", "--batch-commit", f"second={second}",
        )
        self.assertEqual(0, integrated_result.returncode, integrated_result.stderr)
        integrated = json.loads(integrated_result.stdout)
        self.assertEqual(64, len(second))
        self.assertEqual({"first": first, "second": second}, integrated["batch_source_commits"])

        evidence = Path(self.temporary.name) / "sha256-integrated.json"
        evidence.write_text(json.dumps(integrated), encoding="utf-8")
        git(root, "worktree", "remove", str(leaf))
        cleanup_result = invoke("cleanup", "--integrated-result", str(evidence))
        self.assertEqual(0, cleanup_result.returncode, cleanup_result.stderr)
        self.assertEqual("cleanup", json.loads(cleanup_result.stdout)["action"])

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

    def install_git_shim(self, *rules: tuple[str, str]) -> None:
        """Front PATH with a git that delegates to the real git except where a rule matches.

        Each rule is (argv fragment, shell action). The action runs before delegating, so
        `exit N` injects a failing or no-op git call and a plain command stages a race.
        """
        shim_dir = Path(self.temporary.name) / "fault-shim"
        shim_dir.mkdir()
        real_git = shutil.which("git")
        cases = "".join(f'  *" {fragment} "*) {action} ;;\n' for fragment, action in rules)
        shim = shim_dir / "git"
        shim.write_text(
            f'#!/bin/sh\ncase " $* " in\n{cases}esac\nexec "{real_git}" "$@"\n',
            encoding="utf-8",
        )
        shim.chmod(0o755)
        self.process_env = {**os.environ, "PATH": f"{shim_dir}{os.pathsep}{os.environ['PATH']}"}

    def integrated_leaf(self, name: str) -> tuple[Path, dict]:
        leaf = self.add_worktree(name)
        source = self.commit(leaf, "work.txt", "work\n")
        result, integrated = self.integrate(name, leaf, source)
        self.assertEqual(0, result.returncode, result.stderr)
        return leaf, integrated

    def branches(self) -> str:
        return git(self.root, "branch", "--list").stdout

    def test_refuses_active_git_operation_in_parent_and_leaf(self) -> None:
        leaf = self.add_worktree("active-op")
        source = self.commit(leaf, "work.txt", "work\n")
        for label, marker in (
            ("parent", self.root / ".git" / "BISECT_LOG"),
            ("leaf", Path(git(leaf, "rev-parse", "--git-path", "BISECT_LOG").stdout.strip())),
        ):
            marker = marker if marker.is_absolute() else leaf / marker
            marker.write_text("", encoding="utf-8")
            result, value = self.integrate("active-op", leaf, source)
            self.assertEqual(3, result.returncode)
            self.assertEqual(f"{label} worktree has an active Git operation", value["error"])
            marker.unlink()
        self.assertEqual(0, self.integrate("active-op", leaf, source)[0].returncode)

    def assert_both_commands_refuse(self, name: str, expected: str, **overrides) -> None:
        leaf, integrated = self.integrated_leaf(name)
        absent = str(Path(self.temporary.name) / "absent.json")
        for command, flag, argument in (
            ("integrate", "--source-commit", integrated["source_commit"]),
            ("cleanup", "--integrated-result", absent),
        ):
            result, value = self.invoke(command, leaf, f"task/{name}", flag, argument, **overrides)
            self.assertEqual(3, result.returncode)
            self.assertEqual(expected, value["error"])

    def test_refuses_repo_root_that_is_not_the_parent_toplevel(self) -> None:
        self.assert_both_commands_refuse(
            "subdir-root",
            "--repo-root must be the parent worktree root",
            repo_root=self.root / ".worktrees",
        )

    def test_refuses_parent_not_checked_out_on_the_target(self) -> None:
        git(self.root, "branch", "release", "main")
        self.assert_both_commands_refuse(
            "wrong-target",
            "parent worktree must be checked out on the exact target",
            target="release",
        )

    def test_batch_commit_count_is_capped_at_eight(self) -> None:
        eight = [f"step{i}={'a' * 40}" for i in range(8)]
        self.assertEqual(8, len(HELPER.parse_batch_commits(eight)))
        leaf = self.add_worktree("batch-cap")
        source = self.commit(leaf, "work.txt", "work\n")
        extra = [arg for i in range(9) for arg in ("--batch-commit", f"step{i}={'a' * 40}")]

        result, value = self.integrate("batch-cap", leaf, source, *extra)

        self.assertEqual(3, result.returncode)
        self.assertEqual("--batch-commit may not appear more than 8 times", value["error"])

    def test_refuses_source_commit_that_is_not_the_branch_tip(self) -> None:
        leaf = self.add_worktree("stale-source")
        earlier = self.commit(leaf, "one.txt", "one\n")
        self.commit(leaf, "two.txt", "two\n")
        before = git(self.root, "rev-parse", "main").stdout.strip()

        result, value = self.integrate("stale-source", leaf, earlier)

        self.assertEqual(3, result.returncode)
        self.assertEqual("returned source commit is not the exact branch tip", value["error"])
        self.assertEqual(before, git(self.root, "rev-parse", "main").stdout.strip())

    def assert_integrate_refused(self, name: str, expected: str, *rules: tuple[str, str]) -> None:
        leaf = self.add_worktree(name)
        source = self.commit(leaf, "work.txt", "work\n")
        self.install_git_shim(*rules)

        result, value = self.integrate(name, leaf, source)

        self.assertEqual(3, result.returncode)
        self.assertEqual(expected, value["error"])
        self.assertIn(f"task/{name}", self.branches())

    def assert_cleanup_refused(self, name: str, expected: str, arrange, leaf_remains=True) -> None:
        leaf, integrated = self.integrated_leaf(name)
        arrange(leaf)

        result, value = self.cleanup(name, leaf, integrated)

        self.assertEqual(3, result.returncode)
        self.assertEqual(expected, value["error"])
        self.assertEqual(leaf_remains, leaf.exists())
        self.assertIn(f"task/{name}", self.branches())

    def test_refuses_when_target_moves_during_rebase(self) -> None:
        moved = f'"{shutil.which("git")}" -C "{self.root}" commit --allow-empty -q -m moved'
        self.assert_integrate_refused(
            "moving-target",
            "parent target moved during rebase; rebased branch retained",
            ("rebase main", moved),
        )
        self.assertEqual("moved", git(self.root, "log", "-1", "--format=%s").stdout.strip())

    def test_refuses_when_fast_forward_merge_fails(self) -> None:
        before = git(self.root, "rev-parse", "main").stdout.strip()
        self.assert_integrate_refused(
            "ff-fails",
            "fast-forward-only merge failed; rebased branch retained",
            ("merge --ff-only", "exit 1"),
        )
        self.assertEqual(before, git(self.root, "rev-parse", "main").stdout.strip())

    def test_refuses_when_fast_forward_does_not_land_the_rebased_commit(self) -> None:
        self.assert_integrate_refused(
            "ff-noop",
            "fast-forward target does not equal rebased branch",
            ("merge --ff-only", "exit 0"),
        )

    def test_cleanup_refuses_branch_registered_at_an_unexpected_worktree(self) -> None:
        def arrange(leaf: Path) -> None:
            git(self.root, "worktree", "remove", str(leaf))
            other = self.root / ".worktrees" / "somewhere-else"
            git(self.root, "worktree", "add", str(other), "task/elsewhere")

        self.assert_cleanup_refused(
            "elsewhere",
            "delegated branch is registered at an unexpected worktree",
            arrange,
            leaf_remains=False,
        )

    def test_cleanup_refuses_when_branch_merged_listing_omits_the_branch(self) -> None:
        self.assert_cleanup_refused(
            "unlisted",
            "git branch --merged did not confirm the exact branch",
            lambda leaf: self.install_git_shim(("branch --merged", "exit 0")),
        )

    def test_cleanup_retains_branch_when_worktree_removal_fails(self) -> None:
        self.assert_cleanup_refused(
            "locked",
            "clean worktree removal failed; branch retained",
            lambda leaf: git(self.root, "worktree", "lock", str(leaf)),
        )

    def test_cleanup_reports_failed_non_force_branch_deletion(self) -> None:
        lock = self.root / ".git" / "refs" / "heads" / "task" / "delete-fails.lock"
        self.assert_cleanup_refused(
            "delete-fails",
            "non-force branch deletion failed; branch retained",
            lambda leaf: lock.write_text("", encoding="utf-8"),
            leaf_remains=False,
        )

    def test_cleanup_refuses_when_branch_survives_a_reported_deletion(self) -> None:
        self.assert_cleanup_refused(
            "delete-noop",
            "branch still exists after non-force deletion",
            lambda leaf: self.install_git_shim(("branch -d", "exit 0")),
            leaf_remains=False,
        )


if __name__ == "__main__":
    unittest.main()
