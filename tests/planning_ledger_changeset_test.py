"""The changeset gate: verify_policy stamp, base_commit, budgeted packet, and check-changeset."""

import json
import unittest

from tests.planning_ledger_dispatch_test import DispatchHarness, bare, batch_leaves, git, leaf


class ChangesetHarness(DispatchHarness):
    def call(self, *arguments):
        """Every init-v5 names an empty pin root, which strict plans require."""
        if arguments[:1] == ("init-v5",):
            (self.repo / "pins").mkdir(exist_ok=True)
            arguments += ("--pin-roots", "pins")
        return super().call(*arguments)

    def checkpoint(self):
        return json.loads(self.checkpoint_path().read_text())

    def started(self, leaves=None, **extra):
        self.init(leaves or [leaf("alpha", "leaf-alpha")], **extra)
        code, result = self.dispatch("alpha", "--create-from", "main")
        self.assertEqual(0, code, result)
        self.worktree = self.repo / ".worktrees/alpha"
        return result["handoffs"][0]

    def commit_file(self, relative, content, message="work"):
        path = self.worktree / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())
        git(self.worktree, "add", "-A")
        git(self.worktree, "commit", "-m", message)

    def returned(self, packet, status="completed", blockers=(), commit=None, **fields):
        value = {
            "schema": "bounded-step-return-v1", "step_id": packet["step_id"],
            "attempt_id": packet["attempt_id"], "agent_id": packet["agent_id"],
            "status": status, "changed_paths": [],
            "acceptance": {"command": "uv run test", "exit_code": 0 if status == "completed" else 1,
                           "summary": status},
            "blockers": list(blockers), "notes": [], "unstarted_remainder": [],
            "commit_hash": commit or git(self.worktree, "rev-parse", "HEAD").stdout.strip(),
            **fields,
        }
        path = self.scratch / "return.json"
        path.write_text(json.dumps(value))
        code, result = self.call("record-return", "--actor", "parent", "--run-id", self.run_id,
                                 "--return-file", str(path))
        self.assertEqual(0, code, result)
        return result

    def check(self, packet, *extra):
        handoff = self.scratch / "handoff.json"
        handoff.write_text(json.dumps(packet))
        return self.call("check-changeset", "--handoff-file", str(handoff),
                         "--worktree", str(self.worktree), *extra)


class VerifyPolicyAndPacketTest(ChangesetHarness):
    def test_init_stamps_leaf_verify_by_default_and_closeout_only_when_declared(self):
        self.init([leaf("alpha", "leaf-alpha")])
        self.assertEqual("leaf_verify_v1", self.checkpoint()["verify_policy"])
        self.init([leaf("alpha", "leaf-alpha")], verification="closeout-only")
        self.assertEqual("closeout_only", self.checkpoint()["verify_policy"])

    def test_unknown_verify_policy_fails_ledger_load(self):
        self.init([leaf("alpha", "leaf-alpha")])
        data = self.checkpoint()
        data["verify_policy"] = "mystery"
        self.checkpoint_path().write_text(json.dumps(data))
        code, result = self.call("show", "--run-id", self.run_id)
        self.assertNotEqual(0, code, result)

    def test_dispatch_records_base_commit_and_packet_carries_the_budget(self):
        packet = self.started()
        head = git(self.repo / ".worktrees/alpha", "rev-parse", "HEAD").stdout.strip()
        self.assertEqual(head, self.checkpoint()["steps"]["alpha"]["base_commit"])
        self.assertEqual(
            {"max_changed_lines": 150, "max_files": 6, "exempt_paths": [], "base_commit": head},
            packet["changeset_budget"],
        )
        code, granular = self.call("handoff", "--run-id", self.run_id, "--step-id", "alpha")
        self.assertEqual(bare(packet), granular["handoff"])

    def test_retry_dispatch_keeps_the_first_base_commit(self):
        packet = self.started()
        base = self.checkpoint()["steps"]["alpha"]["base_commit"]
        self.commit_file("src/alpha/a.txt", "one\n")
        self.returned(packet, "failed", [{"code": "failed:acceptance", "summary": "red"}])
        step = self.checkpoint()["steps"]["alpha"]
        remediation = self.scratch / "remediation.json"
        remediation.write_text(json.dumps({
            "schema": "retry-remediation-v1", "step_id": "alpha",
            "prior_attempt_id": step["attempt_id"], "prior_return_sha256": step["return_sha256"],
            "diagnosis": "acceptance failed", "remediation_action": "fix the case",
            "executor_mode": "reuse", "next_agent_id": "worker",
            "next_harness": "claude-code", "target_portable_tier": "standard",
        }))
        code, result = self.dispatch("alpha", "--retry", "--retry-remediation-file", str(remediation))
        self.assertEqual(0, code, result)
        self.assertEqual(base, self.checkpoint()["steps"]["alpha"]["base_commit"])
        self.assertEqual(base, result["handoffs"][0]["changeset_budget"]["base_commit"])

    def test_batch_follower_measures_from_the_previous_member_commit(self):
        members, units, worktrees = batch_leaves()
        members[1]["write_set"] = ["src"]
        self.init(members, units, worktrees)
        code, result = self.dispatch("first", "--create-from", "main")
        self.assertEqual(0, code, result)
        first, second = result["handoffs"]
        self.assertEqual("", second["changeset_budget"]["base_commit"])
        self.worktree = self.repo / ".worktrees/batch"
        self.commit_file("src/first/a.txt", "x\n" * 100)
        self.returned(first)
        self.commit_file("src/second/b.txt", "y\n" * 3)
        self.returned(second)
        code, result = self.call("check-changeset", "--run-id", self.run_id, "--step-id", "second")
        self.assertEqual(0, code, result)
        self.assertEqual((3, 1), (result["lines"], result["files"]))

    def test_closeout_only_packet_and_step_stay_unchanged(self):
        packet = self.started(verification="closeout-only")
        self.assertNotIn("changeset_budget", packet)
        self.assertNotIn("base_commit", self.checkpoint()["steps"]["alpha"])

    def test_oversized_changeset_is_registered_and_never_retryable(self):
        packet = self.started()
        self.assertIn(
            "oversized:changeset",
            packet["return_schema"]["properties"]["blockers"]["items"]["properties"]["code"]["enum"],
        )
        self.returned(
            packet, "oversized", [{"code": "oversized:changeset", "summary": "diff over budget"}],
            acceptance={"command": "uv run test", "exit_code": None, "summary": "stopped"},
            unstarted_remainder=["rest"], commit_hash="",
        )
        step = self.checkpoint()["steps"]["alpha"]
        self.assertEqual(("oversized", False), (step["status"], step["retry_allowed"]))


class CheckChangesetTest(ChangesetHarness):
    def test_in_budget_change_inside_write_set_passes(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "one\ntwo\n")
        code, result = self.check(packet)
        self.assertEqual(0, code, result)
        self.assertEqual(
            {"ok": True, "verdict": "pass", "lines": 2, "files": 1,
             "limits": {"max_changed_lines": 150, "max_files": 6}, "outside": []},
            result,
        )

    def test_over_budget_is_oversized_changeset(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "x\n" * 151)
        code, result = self.check(packet)
        self.assertEqual(1, code, result)
        self.assertEqual(("oversized:changeset", 151), (result["verdict"], result["lines"]))
        self.assertFalse(result["ok"])

    def test_declared_exempt_path_is_dropped_before_counting(self):
        declared = leaf("alpha", "leaf-alpha")
        declared["changeset_budget"] = {"exempt_paths": ["src/alpha/lock.txt"], "reason": "lockfile"}
        packet = self.started([declared])
        self.commit_file("src/alpha/lock.txt", "x\n" * 300)
        code, result = self.check(packet)
        self.assertEqual(0, code, result)
        self.assertEqual((0, 0), (result["lines"], result["files"]))

    def test_outside_write_set_lists_at_most_eight_paths(self):
        packet = self.started(precision="strict")
        for index in range(10):
            self.commit_file(f"elsewhere/f{index}.txt", "x\n", f"c{index}")
        code, result = self.check(packet)
        self.assertEqual(1, code, result)
        self.assertEqual("outside_write_set", result["verdict"])
        self.assertEqual(8, len(result["outside"]))

    def test_binary_counts_one_file_zero_lines_and_pure_rename_one_file(self):
        packet = self.started()
        self.commit_file("src/alpha/old.txt", "a\nb\nc\n", "seed")
        base = git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        git(self.worktree, "mv", "src/alpha/old.txt", "src/alpha/new.txt")
        self.commit_file("src/alpha/blob.bin", b"\x00\x01\x02\xff", "move")
        code, result = self.check(packet, "--base", base)
        self.assertEqual(0, code, result)
        self.assertEqual((0, 2), (result["lines"], result["files"]))

    def test_dirty_worktree_fails_the_gate(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "one\n")
        (self.worktree / "src/alpha/stray.txt").write_text("uncommitted\n")
        code, result = self.check(packet)
        self.assertEqual(1, code, result)
        self.assertFalse(result["ok"])
        self.assertEqual(["src/alpha/stray.txt"], result["outside"])

    def test_gate_is_read_only(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "one\n")
        before = self.checkpoint_path().read_bytes()
        head = git(self.worktree, "rev-parse", "HEAD").stdout
        self.check(packet)
        self.assertEqual(before, self.checkpoint_path().read_bytes())
        self.assertEqual(head, git(self.worktree, "rev-parse", "HEAD").stdout)

    def test_parent_mode_measures_the_returned_commit(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "x\n" * 151)
        self.returned(packet, changed_paths=["src/alpha/a.txt"])
        code, result = self.call("check-changeset", "--run-id", self.run_id, "--step-id", "alpha")
        self.assertEqual(1, code, result)
        self.assertEqual("oversized:changeset", result["verdict"])

    def test_usage_errors_exit_two(self):
        packet = self.started(verification="closeout-only")
        code, result = self.check(packet)
        self.assertEqual(2, code, result)
        self.assertFalse(result["ok"])
        code, result = self.call("check-changeset")
        self.assertEqual(2, code, result)


if __name__ == "__main__":
    unittest.main()
