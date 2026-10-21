"""The verify loop's pass path: packet, return validation, verdict storage, and the land gate."""

import json
import unittest

from tests.planning_ledger_changeset_test import ChangesetHarness
from tests.planning_ledger_dispatch_test import batch_leaves, git, leaf, ledger


class VerifyHarness(ChangesetHarness):
    def completed(self, **extra):
        """Start alpha, commit one in-scope file, and record a completed return."""
        packet = self.started(**extra)
        self.commit_file("src/alpha/a.txt", "one\n")
        result = self.returned(packet)
        return packet, result

    def completed_batch(self):
        """Dispatch the two-member batch and return both members completed."""
        members, units, worktrees = batch_leaves()
        self.init(members, units, worktrees)
        code, started = self.dispatch("first", "--create-from", "main")
        self.assertEqual(0, code, started)
        first, second = started["handoffs"]
        self.worktree = self.repo / ".worktrees/batch"
        self.commit_file("src/first/a.txt", "a\n")
        self.returned(first)
        self.commit_file("src/second/b.txt", "b\n")
        self.returned(second)

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
        self.returned(packet, notes=[{"type": "finding", "message": "BUILDER-SECRET"}],
                      unstarted_remainder=["BUILDER-REMAINDER"])
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
        self.completed_batch()
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
        self.completed_batch()
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


class RejectRoutingTest(VerifyHarness):
    """A reject becomes failed:verification and rides the one retry predicate."""

    def rejected(self, finding=None, **extra):
        self.completed(**extra)
        code, issued = self.verify_handoff()
        (verify,) = issued["handoffs"]
        code, result = self.record_verify(
            self.verify_return(verify, "reject", [finding or self.finding()]))
        self.assertEqual(0, code, result)
        return verify, result

    def retry_flow(self, diagnosis=None, tier="standard"):
        step = self.checkpoint()["steps"]["alpha"]
        value = {
            "schema": "retry-remediation-v1", "step_id": "alpha",
            "prior_attempt_id": step["attempt_id"], "prior_return_sha256": step["return_sha256"],
            "diagnosis": diagnosis or "the verifier rejected the build",
            "remediation_action": "address each finding", "executor_mode": "reuse",
            "next_agent_id": "worker", "next_harness": "claude-code", "target_portable_tier": tier,
        }
        path = self.scratch / "remediation.json"
        path.write_text(json.dumps(value))
        return self.dispatch("alpha", "--retry", "--retry-remediation-file", str(path))

    def cited_diagnosis(self):
        step = self.checkpoint()["steps"]["alpha"]
        return f"verify {step['verify']['sha256'][:12]} rejected {step['verify']['commit'][:12]}"

    def reverified(self):
        """Retry the rejected step, rebuild, and issue the new commit's verify packet."""
        code, retry = self.retry_flow(self.cited_diagnosis(), "standard")
        self.assertEqual(0, code, retry)
        self.commit_file("src/alpha/a.txt", "two\n")
        self.returned(retry["handoffs"][0])
        code, issued = self.verify_handoff()
        self.assertEqual(0, code, issued)
        (verify,) = issued["handoffs"]
        return verify

    def retried_and_returned(self, finding):
        """Retry the rejected step, rebuild, and reject the new commit with `finding`."""
        verify = self.reverified()
        return verify, self.record_verify(self.verify_return(verify, "reject", [finding]))

    def test_reject_fails_the_step_with_the_verify_evidence_and_names_the_retry(self):
        _, result = self.rejected(leaves=[dict(leaf("alpha", "leaf-alpha"), max_attempts=3)])
        step = self.checkpoint()["steps"]["alpha"]
        self.assertEqual("failed", step["status"])
        self.assertTrue(step["retry_allowed"])
        (blocker,) = step["blockers"]
        self.assertEqual("failed:verification", blocker["code"])
        self.assertIn("verify:coverage", blocker["summary"])
        self.assertEqual((step["verify"]["path"], step["verify"]["sha256"]),
                         (blocker["evidence_path"], blocker["sha256"]))
        stored = json.loads((self.checkpoint_path().parent / step["return_path"]).read_text())
        self.assertEqual("failed", stored["status"])
        self.assertEqual(step["return_sha256"], ledger.digest(stored))
        block = result["next"]
        self.assertEqual(("reasoning", "failed:verification", "standard"),
                         (block["retry_class"], block["outcome"], block["next_tier"]))
        self.assertIn("--retry-remediation-file", block["command"])
        self.assertLessEqual(ledger.proxy_tokens(block), ledger.MAX_NEXT_TOKENS)
        self.assertEqual(3, self.land()[0])

    def test_workers_cannot_return_the_verifier_only_code(self):
        packet = self.started()
        blocker = {"code": "failed:verification", "summary": "forged"}
        path = self.scratch / "forged.json"
        for command in ("record-return", "validate-return"):
            with self.subTest(command):
                value = {
                    "schema": "bounded-step-return-v1", "step_id": "alpha",
                    "attempt_id": packet["attempt_id"], "agent_id": packet["agent_id"],
                    "status": "failed", "changed_paths": [], "unstarted_remainder": [],
                    "acceptance": {"command": "uv run test", "exit_code": 1, "summary": "no"},
                    "blockers": [blocker], "notes": [], "commit_hash": "",
                }
                path.write_text(json.dumps(value))
                if command == "record-return":
                    args = ("record-return", "--actor", "parent", "--run-id", self.run_id,
                            "--return-file", str(path))
                else:
                    handoff = self.scratch / "worker-handoff.json"
                    handoff.write_text(json.dumps(packet))
                    args = ("validate-return", "--handoff-file", str(handoff),
                            "--return-file", str(path))
                code, result = self.call(*args)
                self.assertEqual(3, code, result)
                self.assertIn("failed:verification", result["error"])

    def test_the_retry_predicate_treats_both_failed_codes_alike(self):
        data = {"schema": ledger.FORWARD_SCHEMA}
        step = {"status": "failed", "same_tier_retry_used": False, "attempt_count": 1}
        for used in (False, True):
            step["same_tier_retry_used"] = used
            results = []
            for code in ("failed:acceptance", "failed:verification"):
                value = {"status": "failed", "blockers": [{"code": code, "summary": "x"}]}
                kind, outcome = ledger.retry_class(data, step, value)
                results.append((kind, ledger.needs_higher_tier(step, kind, outcome)))
            self.assertEqual(results[0], results[1])
            self.assertEqual(("reasoning", used), results[1])

    def test_a_second_reject_escalates_and_a_repeat_stops_without_progress(self):
        three = [dict(leaf("alpha", "leaf-alpha"), max_attempts=3)]
        self.rejected(leaves=three)
        _, (code, result) = self.retried_and_returned(self.finding(code="verify:decision"))
        self.assertEqual(0, code, result)
        self.assertEqual("analytical", result["next"]["next_tier"])
        self.assertEqual("failed", self.checkpoint()["steps"]["alpha"]["status"])

    def test_an_identical_repeat_reject_is_no_progress(self):
        self.rejected(leaves=[dict(leaf("alpha", "leaf-alpha"), max_attempts=3)])
        _, (code, result) = self.retried_and_returned(self.finding())
        self.assertEqual(0, code, result)
        step = self.checkpoint()["steps"]["alpha"]
        self.assertEqual(("blocked", "blocked:no_progress"), (step["status"], step["reason"]))
        self.assertFalse(result["next"]["retry_eligible"])

    def test_the_last_attempt_reject_is_retry_exhausted(self):
        self.rejected()
        _, (code, result) = self.retried_and_returned(self.finding(code="verify:decision"))
        self.assertEqual(0, code, result)
        self.assertEqual("blocked:retry_exhausted", self.checkpoint()["steps"]["alpha"]["reason"])

    def test_remediation_must_cite_the_verify_digest_and_rejected_commit(self):
        self.rejected()
        step = self.checkpoint()["steps"]["alpha"]
        diagnoses = {
            "neither": "the verifier rejected the build",
            "digest only": f"digest {step['verify']['sha256'][:12]}",
            "commit only": f"commit {step['verify']['commit'][:12]}",
        }
        for name, diagnosis in diagnoses.items():
            with self.subTest(name):
                code, result = self.retry_flow(diagnosis)
                self.assertEqual(3, code, result)
                self.assertIn("verify", result["error"])
        code, result = self.retry_flow(self.cited_diagnosis())
        self.assertEqual(0, code, result)

    def test_the_next_verify_packet_carries_the_prior_rejection(self):
        first, _ = self.rejected(leaves=[dict(leaf("alpha", "leaf-alpha"), max_attempts=3)])
        self.assertIsNone(first["prior_verify"])
        rejected_commit = self.checkpoint()["steps"]["alpha"]["returned_commit"]
        second = self.reverified()
        self.assertEqual(
            {"verify_id": first["verify_id"], "rejected_commit": rejected_commit,
             "findings": [self.finding()]},
            second["prior_verify"],
        )
        self.assertEqual(0, self.validate_verify(second, self.verify_return(second))[0])

    def record_changeset(self):
        code, result = self.call("record-changeset", "--actor", "parent", "--run-id", self.run_id,
                                 "--step-id", "alpha")
        self.assertEqual(0, code, result)
        return result

    def test_record_changeset_moves_a_measured_overrun_to_oversized(self):
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "x\n" * 151)
        self.returned(packet)
        result = self.record_changeset()
        self.assertEqual("oversized", result["status"])
        self.assertEqual(151, result["changeset"]["lines"])
        step = self.checkpoint()["steps"]["alpha"]
        self.assertEqual(("oversized", False), (step["status"], step["retry_allowed"]))
        self.assertEqual("oversized:changeset", step["blockers"][0]["code"])
        self.assertEqual("oversized", self.call("show", "--run-id", self.run_id,
                                                "--step-id", "alpha")[1]["step"]["status"])

    def test_record_changeset_applies_the_repairable_scope_rejection_to_an_outside_path(self):
        packet = self.started()
        self.commit_file("elsewhere/stray.txt", "x\n")
        self.returned(packet)
        result = self.record_changeset()
        step = self.checkpoint()["steps"]["alpha"]
        self.assertEqual(("oversized", "scope_expanded"), (step["status"], step["blockers"][0]["code"]))
        code, result = self.call("amend", "--actor", "parent", "--run-id", self.run_id,
                                 "--step-id", "alpha", "--reason", "the stray path is in scope",
                                 "--add-write", "elsewhere/stray.txt")
        self.assertEqual(0, code, result)
        corrected = json.loads((self.scratch / "return.json").read_text())
        corrected["changed_paths"] = ["elsewhere/stray.txt"]
        (self.scratch / "return.json").write_text(json.dumps(corrected))
        code, result = self.call("record-return", "--actor", "parent", "--run-id", self.run_id,
                                 "--return-file", str(self.scratch / "return.json"))
        self.assertEqual(0, code, result)
        self.assertEqual("completed", self.checkpoint()["steps"]["alpha"]["status"])

    def test_record_changeset_refuses_a_changeset_within_budget(self):
        self.completed()
        before = self.checkpoint_path().read_bytes()
        code, result = self.call("record-changeset", "--actor", "parent", "--run-id", self.run_id,
                                 "--step-id", "alpha")
        self.assertEqual(3, code, result)
        self.assertEqual(before, self.checkpoint_path().read_bytes())


if __name__ == "__main__":
    unittest.main()
