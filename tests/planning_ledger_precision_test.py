"""Ledger precision: the init stamp, the packet field, and advisory out-of-write-set paths."""

import json
import unittest

from tests.planning_ledger_dispatch_test import git, leaf, ledger
from tests.planning_ledger_verify_test import VerifyHarness

OUTSIDE = "elsewhere/stray.txt"


class PrecisionHarness(VerifyHarness):
    def stamp(self, value):
        data = self.checkpoint()
        if value is None:
            data.pop("precision_policy", None)
        else:
            data["precision_policy"] = value
        self.checkpoint_path().write_text(json.dumps(data))

    def started_unstamped(self):
        """A retained run: initialised, its stamp removed, then dispatched."""
        self.init([leaf("alpha", "leaf-alpha")])
        self.stamp(None)
        code, result = self.dispatch("alpha", "--create-from", "main")
        self.assertEqual(0, code, result)
        self.worktree = self.repo / ".worktrees/alpha"
        return result["handoffs"][0]

    def return_file(self, packet, paths):
        value = {
            "schema": "bounded-step-return-v1", "step_id": packet["step_id"],
            "attempt_id": packet["attempt_id"], "agent_id": packet["agent_id"],
            "status": "completed", "changed_paths": paths,
            "acceptance": {"command": "uv run test", "exit_code": 0, "summary": "ok"},
            "blockers": [], "notes": [], "unstarted_remainder": [],
            "commit_hash": git(self.worktree, "rev-parse", "HEAD").stdout.strip(),
        }
        path = self.scratch / "return.json"
        path.write_text(json.dumps(value))
        return path

    def validate_return(self, packet, paths):
        handoff = self.scratch / "handoff.json"
        handoff.write_text(json.dumps(packet))
        return self.call("validate-return", "--handoff-file", str(handoff),
                         "--return-file", str(self.return_file(packet, paths)))

    def record_return(self, packet, paths):
        return self.call("record-return", "--actor", "parent", "--run-id", self.run_id,
                         "--return-file", str(self.return_file(packet, paths)))


class PrecisionStampTest(PrecisionHarness):
    def test_init_stamps_standard_by_default_and_strict_when_declared(self):
        self.init([leaf("alpha", "leaf-alpha")])
        self.assertEqual("standard_v1", self.checkpoint()["precision_policy"])
        self.init([leaf("alpha", "leaf-alpha")], precision="strict")
        self.assertEqual("strict_v1", self.checkpoint()["precision_policy"])

    def test_unknown_precision_policy_fails_ledger_load(self):
        self.init([leaf("alpha", "leaf-alpha")])
        self.stamp("mystery")
        code, result = self.call("show", "--run-id", self.run_id)
        self.assertNotEqual(0, code, result)

    def test_packet_carries_precision_only_for_a_stamped_run(self):
        self.assertEqual("standard", self.started()["precision"])
        self.assertEqual("strict", self.started(precision="strict")["precision"])
        self.assertNotIn("precision", self.started_unstamped())

    def test_unknown_packet_precision_is_refused(self):
        packet = self.started()
        packet["precision"] = "lax"
        packet["handoff_sha256"] = ledger.worker_handoff_digest(packet)
        code, result = self.validate_return(packet, [])
        self.assertNotEqual(0, code, result)


class PrecisionReturnTest(PrecisionHarness):
    def test_standard_accepts_and_records_paths_outside_the_write_set(self):
        packet = self.started()
        code, result = self.validate_return(packet, ["src/alpha/a.txt", OUTSIDE])
        self.assertEqual(0, code, result)
        code, result = self.record_return(packet, ["src/alpha/a.txt", OUTSIDE])
        self.assertEqual(0, code, result)
        self.assertEqual([OUTSIDE], self.checkpoint()["steps"]["alpha"]["scope_notes"])
        self.assertEqual([OUTSIDE], result["next"]["outside_paths"])

    def test_in_scope_return_records_no_scope_notes(self):
        packet = self.started()
        code, result = self.record_return(packet, ["src/alpha/a.txt"])
        self.assertEqual(0, code, result)
        self.assertNotIn("scope_notes", self.checkpoint()["steps"]["alpha"])
        self.assertNotIn("outside_paths", result["next"])

    def test_scope_notes_keep_at_most_eight_paths(self):
        packet = self.started()
        paths = [f"elsewhere/f{index}.txt" for index in range(12)]
        code, result = self.record_return(packet, paths)
        self.assertEqual(0, code, result)
        self.assertEqual(8, len(self.checkpoint()["steps"]["alpha"]["scope_notes"]))
        self.assertLessEqual(ledger.proxy_tokens(result["next"]), 120)

    def test_strict_and_unstamped_runs_keep_the_hard_scope_rejection(self):
        for start in (lambda: self.started(precision="strict"), self.started_unstamped):
            packet = start()
            code, result = self.validate_return(packet, [OUTSIDE])
            self.assertNotEqual(0, code, result)
            code, result = self.record_return(packet, [OUTSIDE])
            self.assertEqual(3, code, result)
            self.assertEqual("oversized", self.checkpoint()["steps"]["alpha"]["status"])


class PrecisionChangesetTest(PrecisionHarness):
    def test_standard_lists_committed_outside_paths_without_failing(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "one\n")
        self.commit_file(OUTSIDE, "x\n")
        code, result = self.check(packet)
        self.assertEqual(0, code, result)
        self.assertEqual(("pass", True, [OUTSIDE]), (result["verdict"], result["ok"], result["outside"]))

    def test_standard_still_fails_a_dirty_worktree(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "one\n")
        (self.worktree / "src/alpha/stray.txt").write_text("uncommitted\n")
        code, result = self.check(packet)
        self.assertEqual(1, code, result)
        self.assertEqual("outside_write_set", result["verdict"])

    def test_standard_still_fails_an_overrun(self):
        packet = self.started()
        self.commit_file(OUTSIDE, "x\n" * 151)
        code, result = self.check(packet)
        self.assertEqual(1, code, result)
        self.assertEqual("oversized:changeset", result["verdict"])

    def test_record_changeset_refuses_an_outside_only_result_as_nothing_to_record(self):
        packet = self.started()
        self.commit_file(OUTSIDE, "x\n")
        self.returned(packet)
        before = self.checkpoint_path().read_bytes()
        code, result = self.call("record-changeset", "--actor", "parent", "--run-id", self.run_id,
                                 "--step-id", "alpha")
        self.assertEqual(3, code, result)
        self.assertEqual(before, self.checkpoint_path().read_bytes())

    def test_verify_packet_names_the_committed_outside_paths(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "one\n")
        self.commit_file(OUTSIDE, "x\n")
        self.returned(packet)
        code, issued = self.verify_handoff()
        self.assertEqual(0, code, issued)
        verify = issued["handoffs"][0]
        self.assertEqual([OUTSIDE], verify["outside_write_set"])
        self.assertEqual(0, self.validate_verify(verify, self.verify_return(verify))[0])

    def test_verify_packet_outside_list_is_empty_when_none(self):
        self.completed()
        code, issued = self.verify_handoff()
        self.assertEqual(0, code, issued)
        self.assertEqual([], issued["handoffs"][0]["outside_write_set"])


if __name__ == "__main__":
    unittest.main()
