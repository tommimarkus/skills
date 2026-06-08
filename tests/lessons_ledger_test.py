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


class CandidateTest(unittest.TestCase):
    def _valid_kwargs(self):
        return dict(
            trigger="user-edited-claude-output",
            summary="manifest version triplet left out of sync",
            proposed_rule="report rule: plugin.json/codex/marketplace versions must match",
            substrate="deterministic",
        )

    def test_build_sets_schema_and_no_sac_id(self):
        ledger = load_ledger()
        rec = ledger.build_candidate(**self._valid_kwargs())
        self.assertEqual(rec["schema_version"], ledger.SCHEMA_VERSION)
        self.assertEqual(rec["layer"], 2)
        self.assertEqual(rec["decision"], "review")
        self.assertNotIn("sac_id", rec)
        self.assertTrue(rec["candidate_id"])
        ledger.validate_candidate(rec)  # must not raise

    def test_auto_approved_requires_deterministic_substrate(self):
        ledger = load_ledger()
        kw = self._valid_kwargs()
        kw.update(decision="auto-approved", substrate="prose")
        with self.assertRaises(ledger.LedgerError):
            ledger.build_candidate(**kw)

    def test_invalid_enums_and_empty_fields_raise(self):
        ledger = load_ledger()
        kw = self._valid_kwargs()
        with self.assertRaises(ledger.LedgerError):
            ledger.build_candidate(**{**kw, "substrate": "bogus"})
        with self.assertRaises(ledger.LedgerError):
            ledger.build_candidate(**{**kw, "trigger": "  "})

    def test_validate_rejects_record_with_sac_id(self):
        ledger = load_ledger()
        rec = ledger.build_candidate(**self._valid_kwargs())
        rec["sac_id"] = "SAC-T00600"
        with self.assertRaises(ledger.LedgerError):
            ledger.validate_candidate(rec)


class AppendTest(unittest.TestCase):
    def test_append_then_read_round_trips(self):
        ledger = load_ledger()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "pending.jsonl"
            rec = ledger.build_candidate(
                trigger="t", summary="s", proposed_rule="r", substrate="policy")
            ledger.append_candidate(rec, path=path)
            rows = ledger.read_candidates(path=path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["candidate_id"], rec["candidate_id"])

    def test_read_missing_file_returns_empty(self):
        ledger = load_ledger()
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ledger.read_candidates(path=Path(tmp) / "none.jsonl"), [])


class ConcurrencyTest(unittest.TestCase):
    def test_parallel_appends_are_not_torn_or_lost(self):
        procs, per = 20, 10
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pending.jsonl"
            worker = Path(tmp) / "worker.py"
            worker.write_text(
                "import importlib.util, sys\n"
                f"spec = importlib.util.spec_from_file_location('l', {str(MODULE)!r})\n"
                "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
                "path, tag, n = sys.argv[1], sys.argv[2], int(sys.argv[3])\n"
                "from pathlib import Path\n"
                "for i in range(n):\n"
                "    rec = m.build_candidate(trigger='t', summary='s',\n"
                "        proposed_rule=f'{tag}-{i}', substrate='policy')\n"
                "    m.append_candidate(rec, path=Path(path))\n",
                encoding="utf-8",
            )
            running = [
                subprocess.Popen([sys.executable, str(worker), str(path), f"p{p}", str(per)])
                for p in range(procs)
            ]
            for proc in running:
                self.assertEqual(proc.wait(), 0)

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), procs * per)          # nothing lost
            parsed = [json.loads(line) for line in lines]      # nothing torn
            self.assertEqual(len({r["proposed_rule"] for r in parsed}), procs * per)


class CliTest(unittest.TestCase):
    def _run(self, *args, cwd):
        return subprocess.run(
            [sys.executable, str(MODULE), *args],
            cwd=str(cwd), capture_output=True, text=True)

    def test_append_then_list_reports_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pending.jsonl"
            out = self._run(
                "append", "--path", str(path),
                "--trigger", "failed-then-passed",
                "--summary", "missing version sync test",
                "--proposed-rule", "report rule: version triplet must match",
                "--substrate", "deterministic",
                cwd=tmp)
            self.assertEqual(out.returncode, 0, out.stderr)

            listed = self._run("list", "--path", str(path), cwd=tmp)
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertIn("1 candidate", listed.stdout)

    def test_append_rejects_bad_substrate_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self._run(
                "append", "--path", str(Path(tmp) / "p.jsonl"),
                "--trigger", "t", "--summary", "s",
                "--proposed-rule", "r", "--substrate", "bogus", cwd=tmp)
            self.assertNotEqual(out.returncode, 0)


if __name__ == "__main__":
    unittest.main()
