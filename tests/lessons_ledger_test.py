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


class StatusTest(unittest.TestCase):
    def _candidate(self, ledger, path, rule="r"):
        rec = ledger.build_candidate(trigger="t", summary="s",
                                     proposed_rule=rule, substrate="policy")
        ledger.append_candidate(rec, path=path)
        return rec

    def test_build_defaults_status_pending(self):
        ledger = load_ledger()
        rec = ledger.build_candidate(trigger="t", summary="s",
                                     proposed_rule="r", substrate="policy")
        self.assertEqual(rec["status"], "pending")
        ledger.validate_candidate(rec)  # status is part of the schema now

    def test_set_status_applies_and_filters_pending(self):
        ledger = load_ledger()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pending.jsonl"
            rec = self._candidate(ledger, path)
            self.assertEqual(len(ledger.pending_candidates(path=path)), 1)

            found = ledger.set_status(rec["candidate_id"], "applied", path=path, note="placed in CLAUDE.md")
            self.assertTrue(found)
            self.assertEqual(ledger.pending_candidates(path=path), [])
            rows = ledger.read_candidates(path=path)
            self.assertEqual(rows[0]["status"], "applied")
            self.assertEqual(rows[0]["resolve_note"], "placed in CLAUDE.md")

    def test_set_status_unknown_id_returns_false(self):
        ledger = load_ledger()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pending.jsonl"
            self._candidate(ledger, path)
            self.assertFalse(ledger.set_status("deadbeef", "applied", path=path))

    def test_set_status_invalid_status_raises(self):
        ledger = load_ledger()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pending.jsonl"
            rec = self._candidate(ledger, path)
            with self.assertRaises(ledger.LedgerError):
                ledger.set_status(rec["candidate_id"], "bogus", path=path)


class ResolveCliTest(unittest.TestCase):
    def _run(self, *args, cwd):
        return subprocess.run([sys.executable, str(MODULE), *args],
                              cwd=str(cwd), capture_output=True, text=True)

    def test_append_list_resolve_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pending.jsonl"
            self._run("append", "--path", str(path), "--trigger", "revert",
                      "--summary", "s", "--proposed-rule", "rule one",
                      "--substrate", "policy", cwd=tmp)
            pending = self._run("list", "--path", str(path), "--pending", cwd=tmp)
            self.assertIn("[policy]", pending.stdout)
            cid = pending.stdout.split()[0]

            resolved = self._run("resolve", "--path", str(path), "--id", cid,
                                 "--status", "applied", cwd=tmp)
            self.assertEqual(resolved.returncode, 0, resolved.stderr)

            summary = self._run("list", "--path", str(path), cwd=tmp)
            self.assertIn("0 pending", summary.stdout)
            self.assertIn("1 applied", summary.stdout)


class AutoApproveTest(unittest.TestCase):
    def _auto_record(self, ledger, change_class="add-fixture-existing-smell"):
        rec = ledger.build_candidate(trigger="t", summary="s", proposed_rule="r",
                                     substrate="deterministic", decision="auto-approved",
                                     change_class=change_class)
        return rec

    def test_build_sets_change_class(self):
        ledger = load_ledger()
        rec = self._auto_record(ledger)
        self.assertEqual(rec["change_class"], "add-fixture-existing-smell")

    def test_default_allowlist_denies_everything(self):
        ledger = load_ledger()
        self.assertEqual(ledger.AUTO_APPROVE_CHANGE_CLASSES, ())
        ok, reason = ledger.auto_approve_eligible(self._auto_record(ledger))
        self.assertFalse(ok)
        self.assertIn("allowlist", reason)

    def test_eligible_with_explicit_allowlist(self):
        ledger = load_ledger()
        rec = self._auto_record(ledger)
        ok, reason = ledger.auto_approve_eligible(
            rec, allowlist=("add-fixture-existing-smell",))
        self.assertTrue(ok, reason)

    def test_review_candidate_is_not_eligible(self):
        ledger = load_ledger()
        rec = ledger.build_candidate(trigger="t", summary="s", proposed_rule="r",
                                     substrate="deterministic")  # decision defaults to review
        ok, reason = ledger.auto_approve_eligible(rec, allowlist=("x",))
        self.assertFalse(ok)
        self.assertIn("auto-approved", reason)

    def test_already_graduated_is_not_eligible(self):
        ledger = load_ledger()
        rec = self._auto_record(ledger)
        ok, reason = ledger.auto_approve_eligible(
            rec, allowlist=("add-fixture-existing-smell",),
            graduated_ids=(rec["candidate_id"],))
        self.assertFalse(ok)
        self.assertIn("graduated", reason)


if __name__ == "__main__":
    unittest.main()
