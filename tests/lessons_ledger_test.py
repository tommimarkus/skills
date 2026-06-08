import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "scripts" / "lessons_ledger.py"


def load_ledger():
    spec = importlib.util.spec_from_file_location("lessons_ledger", MODULE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["lessons_ledger"] = module
    spec.loader.exec_module(module)
    return module


def _git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True,
                   capture_output=True, text=True)


def _init_repo(root: Path):
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    (root / "f.txt").write_text("x", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")


class PathResolutionTest(unittest.TestCase):
    def test_main_and_worktree_share_one_ledger_file(self):
        ledger = load_ledger()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            main = tmp / "main"
            main.mkdir()
            _init_repo(main)
            wt = tmp / "wt"
            _git(main, "worktree", "add", "-q", str(wt))

            from_main = ledger.resolve_ledger_path(main)
            from_wt = ledger.resolve_ledger_path(wt)

            self.assertEqual(from_main, from_wt)
            self.assertEqual(from_main, main / ".cache" / "lessons" / "pending.jsonl")

    def test_non_git_dir_raises(self):
        ledger = load_ledger()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ledger.LedgerError):
                ledger.resolve_ledger_path(Path(tmp))


if __name__ == "__main__":
    unittest.main()
