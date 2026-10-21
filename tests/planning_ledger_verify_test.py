"""The verify loop's pass path: packet, return validation, verdict storage, and the land gate."""

import json
import unittest

from tests.planning_ledger_changeset_test import ChangesetHarness
from tests.planning_ledger_dispatch_test import git, leaf, ledger


def batch_leaves():
    members = [
        leaf("first", "batch-owner", batch="group"),
        leaf("second", "batch-owner", ["first"], batch="group"),
    ]
    units = [{
        "id": "unit", "original_size": "medium", "cohesive_outcome": "One batch outcome",
        "decomposition": {"basis": "failure_isolation", "rationale": "Separate failure surfaces",
                          "shape": "checkpointed"},
    }]
    return members, units, {"first": ".worktrees/batch", "second": ".worktrees/batch"}


class VerifyHarness(ChangesetHarness):
    def completed(self, **extra):
        """Start alpha, commit one in-scope file, and record a completed return."""
        packet = self.started(**extra)
        self.commit_file("src/alpha/a.txt", "one\n")
        result = self.returned(packet)
        return packet, result

    def verify_handoff(self, step_id="alpha"):
        return self.call("verify-handoff", "--actor", "parent", "--run-id", self.run_id,
                         "--step-id", step_id)

    def verify_return(self, packet, verdict="pass", findings=(), notes=(), **override):
        value = {
            "schema": "bounded-verify-return-v1", "step_id": packet["step_id"],
            "verify_id": packet["verify_id"], "verdict": verdict,
            "findings": list(findings), "notes": list(notes), **override,
        }
        path = self.scratch / f"verify-{packet['step_id']}.json"
        path.write_text(json.dumps(value))
        return path

    def finding(self, **override):
        return {"code": "verify:coverage", "path": "src/alpha/a.txt", "line": 1,
                "clause": "task", "summary": "the task is not covered", **override}

    def validate_verify(self, packet, path):
        handoff = self.scratch / f"verify-handoff-{packet['step_id']}.json"
        handoff.write_text(json.dumps(packet))
        return self.call("validate-verify-return", "--handoff-file", str(handoff),
                         "--return-file", str(path))

    def record_verify(self, path):
        return self.call("record-verify", "--actor", "parent", "--run-id", self.run_id,
                         "--return-file", str(path))

    def land(self, step_id="alpha"):
        return self.call("land", "--actor", "parent", "--run-id", self.run_id,
                         "--step-id", step_id, "--target", "main")

    def verified(self, verdict="pass", findings=()):
        packet, _ = self.completed()
        code, issued = self.verify_handoff()
        self.assertEqual(0, code, issued)
        (verify,) = issued["handoffs"]
        code, result = self.record_verify(self.verify_return(verify, verdict, findings))
        return verify, code, result


class VerifyHandoffTest(VerifyHarness):
    def test_completed_return_names_the_gate_then_verify_handoff_instead_of_land(self):
        _, result = self.completed()
        command = result["next"]["command"]
        self.assertIn(" check-changeset ", command)
        self.assertIn(" verify-handoff ", result["next"]["then"])
        self.assertNotIn(" land ", json.dumps(result["next"]))
        self.assertLessEqual(ledger.proxy_tokens(result["next"]), ledger.MAX_NEXT_TOKENS)

    def test_closeout_only_completed_return_still_names_land(self):
        _, result = self.completed(verification="closeout-only")
        self.assertIn(" land ", result["next"]["command"])

    def test_packet_carries_the_bounded_contract_and_a_fresh_verify_id(self):
        packet, _ = self.completed()
        step = self.checkpoint()["steps"]["alpha"]
        code, issued = self.verify_handoff()
        self.assertEqual(0, code, issued)
        (verify,) = issued["handoffs"]
        self.assertEqual("planning-verify-handoff-v1", verify["schema"])
        self.assertEqual(
            (self.plan_digest(), "alpha", packet["attempt_id"], packet["agent_id"]),
            (verify["plan_sha256"], verify["step_id"], verify["attempt_id"], verify["agent_id"]),
        )
        self.assertEqual("plan-verify-standard", verify["verifier_tier"])
        self.assertEqual(["src/alpha"], verify["write_set"])
        self.assertEqual("uv run test", verify["acceptance_command"])
        self.assertEqual("Complete alpha", verify["cohesive_outcome"])
        self.assertEqual(0, verify["acceptance_exit_code"])
        self.assertEqual(step["returned_commit"], verify["returned_commit"])
        self.assertEqual(step["base_commit"], verify["base_commit"])
        self.assertEqual(150, verify["budget"]["max_changed_lines"])
        self.assertEqual("pass", verify["changeset"]["verdict"])
        self.assertIn("verdict", verify["return_schema"]["properties"])
        self.assertLessEqual(len(ledger.canon(verify)), 16 * 1024)
        code, again = self.verify_handoff()
        self.assertNotEqual(verify["verify_id"], again["handoffs"][0]["verify_id"])

    def test_packet_never_carries_builder_notes_blockers_or_remainder(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "one\n")
        value = {
            "schema": "bounded-step-return-v1", "step_id": "alpha",
            "attempt_id": packet["attempt_id"], "agent_id": packet["agent_id"],
            "status": "completed", "changed_paths": [],
            "acceptance": {"command": "uv run test", "exit_code": 0, "summary": "ok"},
            "blockers": [], "notes": [{"type": "finding", "message": "BUILDER-SECRET"}],
            "unstarted_remainder": ["BUILDER-REMAINDER"],
            "commit_hash": git(self.worktree, "rev-parse", "HEAD").stdout.strip(),
        }
        path = self.scratch / "return.json"
        path.write_text(json.dumps(value))
        code, result = self.call("record-return", "--actor", "parent", "--run-id", self.run_id,
                                 "--return-file", str(path))
        self.assertEqual(0, code, result)
        code, issued = self.verify_handoff()
        self.assertEqual(0, code, issued)
        text = json.dumps(issued)
        self.assertNotIn("BUILDER-SECRET", text)
        self.assertNotIn("BUILDER-REMAINDER", text)

    def test_escalated_builds_get_the_analytical_verifier(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "one\n")
        self.returned(packet)
        data = self.checkpoint()
        data["steps"]["alpha"]["current_tier"] = "analytical"
        self.checkpoint_path().write_text(json.dumps(data))
        code, issued = self.verify_handoff()
        self.assertEqual(0, code, issued)
        self.assertEqual("plan-verify-analytical", issued["handoffs"][0]["verifier_tier"])

    def test_changeset_failure_refuses_the_handoff_and_names_the_verdict(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "x\n" * 151)
        self.returned(packet)
        code, result = self.verify_handoff()
        self.assertEqual(3, code, result)
        self.assertIn("oversized:changeset", result["error"])

    def test_dirty_worktree_refuses_the_handoff(self):
        self.completed()
        (self.worktree / "src/alpha/stray.txt").write_text("uncommitted\n")
        code, result = self.verify_handoff()
        self.assertEqual(3, code, result)
        self.assertIn("outside_write_set", result["error"])

    def test_incomplete_step_and_closeout_only_run_are_refused(self):
        self.started()
        code, result = self.verify_handoff()
        self.assertEqual(3, code, result)
        self.completed(verification="closeout-only")
        code, result = self.verify_handoff()
        self.assertEqual(3, code, result)
        self.assertIn("leaf verification", result["error"])

    def test_batch_emits_one_packet_per_completed_member(self):
        members, units, worktrees = batch_leaves()
        self.init(members, units, worktrees)
        code, started = self.dispatch("first", "--create-from", "main")
        first, second = started["handoffs"]
        self.worktree = self.repo / ".worktrees/batch"
        self.commit_file("src/first/a.txt", "a\n")
        self.returned(first)
        self.commit_file("src/second/b.txt", "b\n")
        self.returned(second)
        code, issued = self.verify_handoff("first")
        self.assertEqual(0, code, issued)
        self.assertEqual(["first", "second"], [item["step_id"] for item in issued["handoffs"]])
        self.assertEqual(
            self.checkpoint()["steps"]["first"]["returned_commit"],
            issued["handoffs"][1]["base_commit"],
        )

    def plan_digest(self):
        return self.checkpoint()["plan_hash"]


class VerifyReturnTest(VerifyHarness):
    def packet(self):
        self.completed()
        return self.verify_handoff()[1]["handoffs"][0]

    def test_valid_pass_and_reject_returns_validate_read_only(self):
        packet = self.packet()
        before = self.checkpoint_path().read_bytes()
        code, result = self.validate_verify(packet, self.verify_return(packet))
        self.assertEqual(0, code, result)
        self.assertEqual("pass", result["verdict"])
        code, result = self.validate_verify(
            packet, self.verify_return(packet, "reject", [self.finding(line=None)]))
        self.assertEqual(0, code, result)
        self.assertEqual(before, self.checkpoint_path().read_bytes())

    def test_malformed_returns_are_refused(self):
        packet = self.packet()
        too_many = [self.finding() for _ in range(9)]
        cases = {
            "reject without a finding": self.verify_return(packet, "reject"),
            "pass with a finding": self.verify_return(packet, "pass", [self.finding()]),
            "unknown code": self.verify_return(packet, "reject", [self.finding(code="verify:style")]),
            "too many findings": self.verify_return(packet, "reject", too_many),
            "long summary": self.verify_return(packet, "reject", [self.finding(summary="x" * 241)]),
            "unknown verdict": self.verify_return(packet, "maybe"),
            "too many notes": self.verify_return(packet, notes=["n"] * 9),
            "extra field": self.verify_return(packet, extra="x"),
            "stale verify id": self.verify_return(packet, verify_id="0" * 8 + packet["verify_id"][8:]),
            "foreign step": self.verify_return(packet, step_id="beta"),
            "oversized": self.verify_return(packet, "inconclusive", notes=["x" * 240] * 8,
                                            findings=[self.finding(summary="y" * 240)] * 8),
        }
        for name, path in cases.items():
            with self.subTest(name):
                code, result = self.validate_verify(packet, path)
                self.assertNotEqual(0, code, result)

    def test_inconclusive_needs_no_finding(self):
        packet = self.packet()
        code, result = self.validate_verify(packet, self.verify_return(packet, "inconclusive"))
        self.assertEqual(0, code, result)


class RecordVerifyTest(VerifyHarness):
    def test_pass_stores_the_return_and_names_land(self):
        verify, code, result = self.verified()
        self.assertEqual(0, code, result)
        self.assertIn(" land ", result["next"]["command"])
        step = self.checkpoint()["steps"]["alpha"]
        self.assertEqual("pass", step["verify"]["verdict"])
        self.assertEqual(step["returned_commit"], step["verify"]["commit"])
        stored = self.checkpoint_path().parent / step["verify"]["path"]
        self.assertTrue(stored.is_file())
        self.assertEqual(step["verify"]["sha256"], ledger.digest(json.loads(stored.read_text())))
        self.assertEqual("completed", step["status"])

    def test_a_replayed_or_stale_verify_id_is_refused(self):
        verify, code, _ = self.verified()
        code, result = self.record_verify(self.verify_return(verify))
        self.assertEqual(3, code, result)
        self.verify_handoff()
        code, result = self.record_verify(self.verify_return(verify))
        self.assertEqual(3, code, result)

    def test_verifier_mutation_is_refused(self):
        self.completed()
        code, issued = self.verify_handoff()
        (verify,) = issued["handoffs"]
        (self.worktree / "src/alpha/a.txt").write_text("mutated\n")
        code, result = self.record_verify(self.verify_return(verify))
        self.assertEqual(3, code, result)
        self.assertIn("mutation", result["error"])
        git(self.worktree, "commit", "-am", "verifier commit")
        code, result = self.record_verify(self.verify_return(verify))
        self.assertEqual(3, code, result)
        self.assertIn("mutation", result["error"])
        self.assertNotIn("verify", self.checkpoint()["steps"]["alpha"])

    def test_requires_the_parent_actor(self):
        self.completed()
        verify = self.verify_handoff()[1]["handoffs"][0]
        code, result = self.call("record-verify", "--actor", "worker", "--run-id", self.run_id,
                                 "--return-file", str(self.verify_return(verify)))
        self.assertNotEqual(0, code, result)


class LandGateTest(VerifyHarness):
    def test_land_and_integrated_transition_refuse_an_unverified_step(self):
        self.completed()
        code, result = self.land()
        self.assertEqual(3, code, result)
        self.assertIn("verif", result["error"])
        code, result = self.call("transition", "--actor", "parent", "--run-id", self.run_id,
                                 "--step-id", "alpha", "--to", "integrated",
                                 "--worktree-result", str(self.scratch / "missing.json"))
        self.assertEqual(3, code, result)
        self.assertIn("verif", result["error"])
        self.assertEqual("completed", self.checkpoint()["steps"]["alpha"]["status"])

    def assert_verdict_opens_the_gate(self, verdict):
        verify, code, result = self.verified(verdict)
        self.assertEqual(0, code, result)
        code, landed = self.land()
        self.assertEqual(0, code, landed)
        self.assertEqual("cleaned", landed["status"])

    def test_pass_verdict_opens_the_gate(self):
        self.assert_verdict_opens_the_gate("pass")

    def test_inconclusive_verdict_opens_the_gate(self):
        self.assert_verdict_opens_the_gate("inconclusive")

    def test_reject_keeps_the_gate_closed(self):
        verify, code, result = self.verified("reject", [self.finding()])
        self.assertEqual(0, code, result)
        self.assertNotIn("next", result)
        code, landed = self.land()
        self.assertEqual(3, code, landed)

    def test_a_verdict_for_an_earlier_commit_does_not_open_the_gate(self):
        self.verified()
        data = self.checkpoint()
        data["steps"]["alpha"]["verify"]["commit"] = "0" * 40
        self.checkpoint_path().write_text(json.dumps(data))
        code, landed = self.land()
        self.assertEqual(3, code, landed)

    def test_closeout_only_run_lands_without_a_verdict(self):
        self.completed(verification="closeout-only")
        code, landed = self.land()
        self.assertEqual(0, code, landed)

    def test_batch_land_waits_for_every_completed_member_verdict(self):
        members, units, worktrees = batch_leaves()
        self.init(members, units, worktrees)
        code, started = self.dispatch("first", "--create-from", "main")
        first, second = started["handoffs"]
        self.worktree = self.repo / ".worktrees/batch"
        self.commit_file("src/first/a.txt", "a\n")
        self.returned(first)
        self.commit_file("src/second/b.txt", "b\n")
        self.returned(second)
        code, issued = self.verify_handoff("first")
        one, two = issued["handoffs"]
        code, result = self.record_verify(self.verify_return(one))
        self.assertEqual(0, code, result)
        self.assertEqual(["second"], result["next"]["step_ids"])
        self.assertEqual(3, self.land("second")[0])
        self.assertEqual(0, self.record_verify(self.verify_return(two))[0])
        code, landed = self.land("second")
        self.assertEqual(0, code, landed)
        self.assertEqual(["first", "second"], landed["integrated"])


if __name__ == "__main__":
    unittest.main()
