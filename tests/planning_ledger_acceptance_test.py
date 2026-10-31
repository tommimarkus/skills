"""run-acceptance: bounded acceptance execution with parent-visible evidence."""

import hashlib
import json
import os
import unittest
from pathlib import Path

from tests.planning_ledger_changeset_test import ChangesetHarness
from tests.planning_ledger_dispatch_test import bare, batch_leaves, leaf, ledger

NOISY_FAIL = (
    'for i in $(seq 1 2000); do echo "head-marker line $i"; done; '
    "echo tail-one; echo tail-two; exit 7"
)


class AcceptanceHarness(ChangesetHarness):
    def prepared(self, command):
        """Dispatch one alpha step whose acceptance command is `command`."""
        step = leaf("alpha", "leaf-alpha")
        step["acceptance_command"] = command
        self.entry = self.started([step])
        self.packet = bare(self.entry)
        self.stored = self.entry["packet_path"]
        return self.entry

    def worker(self, path=None):
        return self.call("run-acceptance", "--handoff-file", path or self.stored)

    def parent(self, worktree=None):
        return self.call("run-acceptance", "--run-id", self.run_id, "--step-id", "alpha",
                         "--worktree", str(worktree or self.worktree))

    def run_dir(self):
        return self.checkpoint_path().parent

    def evidence(self, result):
        return self.run_dir() / result["acceptance"]["evidence_path"]


class RunAcceptanceTest(AcceptanceHarness):
    def test_passing_command_records_full_output_and_a_matching_digest(self):
        self.prepared("echo first; echo done-line")
        code, result = self.worker()
        self.assertEqual((0, 0), (code, result["exit_code"]), result)
        self.assertEqual(("run-acceptance", "worker"), (result["action"], result["mode"]))
        self.assertEqual(self.packet["attempt_id"], result["attempt_id"])
        acceptance = result["acceptance"]
        self.assertEqual("echo first; echo done-line", acceptance["command"])
        self.assertEqual("done-line", acceptance["summary"])
        log = self.evidence(result)
        self.assertEqual(
            f"acceptance/alpha/{self.packet['attempt_id']}/worker-1.log",
            acceptance["evidence_path"])
        self.assertEqual(b"first\ndone-line\n", log.read_bytes())
        self.assertEqual(hashlib.sha256(log.read_bytes()).hexdigest(), acceptance["sha256"])
        self.assertEqual(len(log.read_bytes()), result["output_bytes"])
        self.assertNotIn("excerpt", result)
        self.assertEqual(acceptance["evidence_path"], ledger.rel(acceptance["evidence_path"]))

    def test_failing_noisy_command_keeps_its_status_and_bounds_the_excerpt(self):
        self.prepared(NOISY_FAIL)
        code, result = self.worker()
        self.assertEqual((7, 7), (code, result["exit_code"]), result)
        self.assertEqual("tail-two", result["acceptance"]["summary"])
        excerpt = result["excerpt"]
        self.assertLessEqual(len(excerpt), ledger.MAX_ACCEPTANCE_EXCERPT)
        self.assertTrue(result["excerpt_truncated"])
        self.assertTrue(excerpt.endswith("tail-one\ntail-two\n"))
        self.assertNotIn("head-marker line 1\n", excerpt)
        self.assertTrue(excerpt.startswith("head-marker line "))
        log = self.evidence(result).read_text()
        self.assertTrue(log.startswith("head-marker line 1\n"))
        self.assertEqual(result["output_bytes"], len(log.encode()))

    def test_short_failure_excerpt_is_whole_and_untruncated(self):
        self.prepared("echo oops; exit 3")
        code, result = self.worker()
        self.assertEqual(3, code)
        self.assertEqual(("oops\n", False), (result["excerpt"], result["excerpt_truncated"]))

    def test_silent_command_summarises_its_exit(self):
        self.prepared("printf %s \"\"")
        code, result = self.worker()
        self.assertEqual(0, code)
        self.assertEqual("exit 0, no output", result["acceptance"]["summary"])

    def test_signal_death_maps_to_128_plus_signal(self):
        self.prepared("kill -TERM $$")
        code, result = self.worker()
        self.assertEqual((143, 143), (code, result["exit_code"]), result)

    def test_emitted_acceptance_object_passes_validate_return(self):
        self.prepared(NOISY_FAIL)
        _code, result = self.worker()
        path = self.return_file(self.packet, "failed",
                                [{"code": "failed:acceptance", "summary": "red"}],
                                acceptance=result["acceptance"])
        code, checked = self.call("validate-return", "--handoff-file", self.stored,
                                  "--return-file", str(path))
        self.assertEqual(0, code, checked)

    def test_malformed_or_foreign_packets_refuse_without_running_the_command(self):
        marker = self.scratch / "marker"
        self.prepared(f"touch {marker}")
        forged = json.loads(Path(self.stored).read_text())
        forged["schema"] = "other"
        bad = self.scratch / "bad.json"
        bad.write_text(json.dumps(forged))
        for path in (str(bad), str(self.scratch / "missing.json")):
            code, result = self.worker(path)
            self.assertFalse(result["ok"])
            self.assertIn(code, (2, 3, 4))
        self.assertEqual(2, self.call("run-acceptance")[0])
        self.assertEqual(2, self.call("run-acceptance", "--handoff-file", self.stored,
                                      "--run-id", self.run_id, "--step-id", "alpha")[0])
        self.assertEqual(2, self.call("run-acceptance", "--run-id", self.run_id,
                                      "--step-id", "alpha")[0])
        self.assertEqual(2, self.call("run-acceptance", "--run-id", self.run_id, "--step-id",
                                      "alpha", "--worktree", str(self.scratch / "none"))[0])
        self.assertFalse(marker.exists())

    def test_packet_outside_its_run_still_runs_but_reports_no_evidence(self):
        self.prepared(NOISY_FAIL)
        code, result = self.worker(str(self.handoff_file(self.packet)))
        self.assertEqual((7, 7), (code, result["exit_code"]), result)
        self.assertIn("evidence_error", result)
        self.assertNotIn("evidence_path", result["acceptance"])
        self.assertNotIn("sha256", result["acceptance"])
        self.assertEqual("tail-two", result["acceptance"]["summary"])
        self.assertTrue(result["excerpt"].endswith("tail-two\n"))
        self.assertFalse((self.run_dir() / "acceptance").exists())

    @unittest.skipIf(os.geteuid() == 0, "root ignores directory permissions")
    def test_unwritable_run_directory_reports_an_evidence_error(self):
        self.prepared("echo ok; exit 5")
        self.run_dir().chmod(0o500)
        self.addCleanup(self.run_dir().chmod, 0o700)
        code, result = self.worker()
        self.assertEqual(5, code, result)
        self.assertIn("evidence_error", result)
        self.assertNotIn("evidence_path", result["acceptance"])

    def test_repeated_runs_never_overwrite_evidence(self):
        self.prepared("echo again")
        paths = [self.worker()[1]["acceptance"]["evidence_path"] for _ in range(2)]
        self.assertEqual([f"acceptance/alpha/{self.packet['attempt_id']}/worker-{n}.log"
                          for n in (1, 2)], paths)
        self.assertTrue(all((self.run_dir() / path).is_file() for path in paths))

    def test_parent_mode_runs_the_amended_command_and_leaves_the_checkpoint_alone(self):
        self.prepared("echo original")
        self.returned(self.packet, "failed", [{"code": "failed:acceptance", "summary": "red"}],
                      acceptance={"command": "echo original", "exit_code": 1, "summary": "red"})
        code, amended = self.call("amend", "--actor", "parent", "--run-id", self.run_id,
                                  "--step-id", "alpha", "--reason", "narrow",
                                  "--acceptance-command", "echo amended-line")
        self.assertEqual(0, code, amended)
        before = self.checkpoint_path().read_bytes()
        entries = {p.name for p in self.run_dir().iterdir()}
        code, result = self.parent()
        self.assertEqual(0, code, result)
        self.assertEqual("parent", result["mode"])
        self.assertEqual("echo amended-line", result["acceptance"]["command"])
        self.assertEqual("amended-line", result["acceptance"]["summary"])
        self.assertEqual(f"acceptance/alpha/{self.packet['attempt_id']}/parent-1.log",
                         result["acceptance"]["evidence_path"])
        self.assertEqual(before, self.checkpoint_path().read_bytes())
        self.assertEqual(entries | {"acceptance"}, {p.name for p in self.run_dir().iterdir()})


class AcceptanceEvidenceLoadingTest(AcceptanceHarness):
    """Evidence under <run>/acceptance never blocks loading, retention or later commands."""

    def shown(self):
        return self.call("show", "--run-id", self.run_id)

    def test_the_run_still_loads_and_accepts_a_return_after_worker_evidence(self):
        self.prepared("echo ok")
        self.assertEqual(0, self.worker()[0])
        self.assertEqual(0, self.shown()[0])
        self.commit_file("src/alpha/a.txt", "one\n")
        acceptance = {"command": "echo ok", "exit_code": 0, "summary": "ok"}
        self.returned(self.packet, acceptance=acceptance)

    def test_consecutive_parent_runs_number_their_evidence(self):
        self.prepared("echo ok")
        paths = [self.parent()[1]["acceptance"]["evidence_path"] for _ in range(2)]
        self.assertEqual([f"acceptance/alpha/{self.packet['attempt_id']}/parent-{n}.log"
                          for n in (1, 2)], paths)

    def test_a_run_holding_evidence_can_still_be_purged(self):
        self.prepared("echo ok")
        self.assertEqual(0, self.worker()[0])
        self.returned(self.packet, "failed", [{"code": "failed:acceptance", "summary": "red"}],
                      acceptance={"command": "echo ok", "exit_code": 1, "summary": "red"})
        code, closed = self.call("close", "--actor", "parent", "--run-id", self.run_id,
                                 "--outcome", "abandoned", "--reason", "test")
        self.assertEqual(0, code, closed)
        code, purged = self.call("purge", "--actor", "parent", "--run-id", self.run_id,
                                 "--before-retention", "--reason", "test cleanup")
        self.assertEqual(0, code, purged)
        self.assertFalse(self.run_dir().exists())

    def test_malformed_evidence_trees_refuse_to_load(self):
        self.prepared("echo ok")
        self.assertEqual(0, self.worker()[0])
        root = self.run_dir() / "acceptance"
        attempt = root / "alpha" / self.packet["attempt_id"]
        outside = self.scratch / "outside"
        outside.write_text("x")
        cases = {
            "symlink": (attempt / "worker-9.log", lambda p: p.symlink_to(outside)),
            "not a log": (attempt / "worker-9.txt", lambda p: p.write_text("x")),
            "zero index": (attempt / "worker-0.log", lambda p: p.write_text("x")),
            "bad mode": (attempt / "other-1.log", lambda p: p.write_text("x")),
            "bad index": (attempt / "worker-x.log", lambda p: p.write_text("x")),
            "file in root": (root / "stray.log", lambda p: p.write_text("x")),
            "file in step dir": (root / "alpha" / "stray.log", lambda p: p.write_text("x")),
            "bad step id": (root / "bad id", lambda p: p.mkdir()),
            "bad attempt id": (root / "alpha" / "nope", lambda p: p.mkdir()),
            "dir as log": (attempt / "worker-9.log", lambda p: p.mkdir()),
            "symlinked step": (root / "beta", lambda p: p.symlink_to(root / "alpha")),
        }
        for label, (path, damage) in cases.items():
            with self.subTest(label):
                damage(path)
                code, result = self.shown()
                if path.is_dir() and not path.is_symlink():
                    path.rmdir()
                else:
                    path.unlink()
                self.assertEqual(3, code, result)
                self.assertIn("unexpected acceptance contents", result["error"])
                self.assertEqual(0, self.shown()[0])


class PromptAndNoteTypeTest(AcceptanceHarness):
    def test_dispatch_prompt_names_run_acceptance_within_the_fixed_bound(self):
        entry = self.prepared("uv run test")
        self.assertIn("run-acceptance --handoff-file " + entry["packet_path"], entry["prompt"])
        self.assertLessEqual(len(ledger.worker_prompt_fixed_text(bare(entry))), 1200)

    def test_batch_prompts_name_run_acceptance_within_the_fixed_bound(self):
        self.init(*batch_leaves())
        handoffs = self.dispatch("first", "--create-from", "main")[1]["handoffs"]
        for index, item in enumerate(handoffs, 1):
            self.assertIn("run-acceptance --handoff-file " + item["packet_path"], item["prompt"])
            fixed = ledger.worker_prompt_fixed_text(bare(item), (index, 2, "group"))
            self.assertLessEqual(len(fixed), 1200)

    def test_extra_read_notes_validate_and_the_schema_lists_them(self):
        entry = self.started()
        self.assertIn("extra_read", entry["return_schema"]["properties"]["notes"]["items"]
                      ["properties"]["type"]["enum"])
        path = self.return_file(bare(entry), notes=[{"type": "extra_read", "message": "docs/x.md"}])
        code, checked = self.call("validate-return", "--handoff-file", entry["packet_path"],
                                  "--return-file", str(path))
        self.assertEqual(0, code, checked)


if __name__ == "__main__":
    unittest.main()
