"""Provisional start: a dependent builds on a completed prerequisite while its verifier runs."""

import json
import unittest

from tests.planning_ledger_dispatch_test import bare, git, leaf, ledger
from tests.planning_ledger_verify_test import VerifyHarness


class PipelineHarness(VerifyHarness):
    def pair(self, **extra):
        self.init([leaf("alpha", "leaf-alpha"), leaf("beta", "leaf-beta", ["alpha"])], **extra)

    def build(self, step_id, create_from="main", files=None):
        """Dispatch a step and commit its files (default: one in-scope file) in its worktree."""
        code, started = self.dispatch(step_id, "--create-from", create_from)
        self.assertEqual(0, code, started)
        self.worktree = self.repo / ".worktrees" / step_id
        for path, text in (files or {f"src/{step_id}/f.txt": f"{step_id}\n"}).items():
            self.commit_file(path, text)
        return started["handoffs"][0]

    def finished(self, step_id, create_from="main", files=None):
        packet = self.build(step_id, create_from, files)
        self.returned(packet)
        return packet

    def issued(self, step_id):
        code, issued = self.verify_handoff(step_id)
        self.assertEqual(0, code, issued)
        return issued["handoffs"][0]

    def passed(self, step_id):
        self.record_verify(self.verify_return(self.issued(step_id)))

    def alpha_in_review(self):
        """alpha is completed with its verify packet issued but no verdict."""
        self.pair()
        self.finished("alpha")
        return self.issued("alpha")

    def step(self, step_id):
        return self.checkpoint()["steps"][step_id]

    def assert_landing_refused(self, step_id, reason):
        """Both `land` and the granular integrated transition refuse with `reason`."""
        refusals = (
            self.land(step_id),
            self.call(
                "transition", "--actor", "parent", "--run-id", self.run_id, "--step-id", step_id,
                "--to", "integrated", "--worktree-result", str(self.scratch / "none.json"),
            ),
        )
        for code, refused in refusals:
            self.assertEqual(3, code, refused)
            self.assertIn(reason, refused["error"])

    def next_only(self):
        code, shown = self.call("show", "--run-id", self.run_id, "--next-only")
        self.assertEqual(0, code, shown)
        return shown["next"]


class ProvisionalStartTest(PipelineHarness):
    def test_init_stamps_the_pipeline_policy_only_for_leaf_verification(self):
        self.pair()
        self.assertEqual("provisional_v1", self.checkpoint()["pipeline_policy"])
        self.pair(verification="closeout-only")
        self.assertNotIn("pipeline_policy", self.checkpoint())

    def test_a_dependent_waits_until_the_prerequisite_verify_packet_is_issued(self):
        self.pair()
        self.finished("alpha")
        code, refused = self.dispatch("beta", "--create-from", "main")
        self.assertEqual(3, code, refused)
        self.assertIn("dependencies", refused["error"])
        self.issued("alpha")
        code, started = self.dispatch("beta", "--create-from", "main")
        self.assertEqual(0, code, started)

    def test_dispatch_stacks_the_worktree_on_the_prerequisite_commit(self):
        self.alpha_in_review()
        commit = self.step("alpha")["returned_commit"]
        packet = self.build("beta", create_from="main")
        self.assertEqual(
            commit, git(self.repo / ".worktrees/beta", "merge-base", "HEAD~1", commit).stdout.strip()
        )
        beta = self.step("beta")
        self.assertEqual({"step_id": "alpha", "commit": commit}, beta["provisional_base"])
        self.assertEqual(commit, beta["base_commit"])
        self.assertEqual({"step_id": "alpha", "commit": commit}, packet["provisional_base"])
        self.assertEqual(commit, packet["changeset_budget"]["base_commit"])
        self.assertEqual(bare(packet), ledger.valid_worker_handoff(bare(packet)))

    def test_a_malformed_packet_provisional_base_is_rejected(self):
        self.alpha_in_review()
        packet = bare(self.build("beta"))
        packet["provisional_base"] = {"step_id": "alpha", "commit": "nope"}
        packet["handoff_sha256"] = ledger.worker_handoff_digest(packet)
        with self.assertRaisesRegex(ledger.Error, "provisional base"):
            ledger.valid_worker_handoff(packet)

    def test_an_existing_worktree_must_already_contain_the_prerequisite_commit(self):
        self.alpha_in_review()
        git(self.repo, "worktree", "add", "-b", "leaf-beta", str(self.repo / ".worktrees/beta"), "main")
        before = self.checkpoint_path().read_bytes()
        code, refused = self.dispatch("beta")
        self.assertEqual(3, code, refused)
        self.assertIn("does not contain provisional base", refused["error"])
        self.assertEqual(before, self.checkpoint_path().read_bytes())

    def test_two_unintegrated_prerequisites_wait(self):
        self.init([
            leaf("alpha", "leaf-alpha"), leaf("beta", "leaf-beta"),
            leaf("gamma", "leaf-gamma", ["alpha", "beta"]),
        ])
        self.finished("alpha")
        self.issued("alpha")
        code, refused = self.dispatch("gamma", "--create-from", "main")
        self.assertEqual(3, code, refused)
        self.finished("beta")
        self.issued("beta")
        code, refused = self.dispatch("gamma", "--create-from", "main")
        self.assertEqual(3, code, refused)
        self.assertIn("dependencies", refused["error"])

    def test_closeout_only_runs_keep_integrated_readiness(self):
        self.pair(verification="closeout-only")
        self.finished("alpha")
        code, refused = self.dispatch("beta", "--create-from", "main")
        self.assertEqual(3, code, refused)

    def test_land_keeps_dependency_order_for_a_stacked_step(self):
        self.alpha_in_review()
        self.finished("beta", create_from="main")
        self.passed("beta")
        self.assert_landing_refused("beta", "land the prerequisite first")
        self.record_verify(self.verify_return(self.issued("alpha")))
        self.assertEqual(0, self.land("alpha")[0])
        code, landed = self.land("beta")
        self.assertEqual(0, code, landed)
        self.assertEqual("cleaned", landed["status"])

    def test_next_blocks_withhold_land_for_a_stacked_step(self):
        self.alpha_in_review()
        self.finished("beta", create_from="main")
        self.passed("beta")
        block = self.next_only()
        self.assertNotEqual("integrate_completed", block["category"])


SHARED = "src/shared.txt"


class UpstreamHarness(PipelineHarness):
    """alpha and beta both own src; beta is stacked on alpha's unverified commit."""

    def stacked(self, beta_files, verified=True):
        (self.repo / "src").mkdir()
        (self.repo / SHARED).write_text("one\ntwo\nthree\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "shared")
        alpha, beta = leaf("alpha", "leaf-alpha"), leaf("beta", "leaf-beta", ["alpha"])
        alpha["write_set"] = beta["write_set"] = ["src"]
        self.init([alpha, beta])
        self.finished("alpha")
        self.alpha_old = self.issued("alpha")
        self.finished("beta", files=beta_files)
        if verified:
            self.passed("beta")
        return self.step("alpha")["returned_commit"]

    def reject_alpha(self):
        code, result = self.record_verify(
            self.verify_return(self.alpha_old, "reject", [self.finding()]))
        self.assertEqual(0, code, result)

    def retry(self, step_id, diagnosis, files):
        """Retry a stopped step with a remediation citing `diagnosis` and commit `files`."""
        step = self.step(step_id)
        path = self.scratch / "remediation.json"
        path.write_text(json.dumps({
            "schema": "retry-remediation-v1", "step_id": step_id,
            "prior_attempt_id": step["attempt_id"], "prior_return_sha256": step["return_sha256"],
            "diagnosis": diagnosis, "remediation_action": "repair", "executor_mode": "reuse",
            "next_agent_id": "worker", "next_harness": "claude-code",
            "target_portable_tier": "standard",
        }))
        code, retry = self.dispatch(step_id, "--retry", "--retry-remediation-file", str(path))
        self.assertEqual(0, code, retry)
        self.worktree = self.repo / ".worktrees" / step_id
        for name, text in files.items():
            self.commit_file(name, text)
        return retry["handoffs"][0]

    def alpha_fixed(self, files):
        """Reject alpha, retry it, and return its new commit."""
        self.reject_alpha()
        verify = self.step("alpha")["verify"]
        self.returned(self.retry(
            "alpha", f"verify {verify['sha256'][:12]} rejected {verify['commit'][:12]}", files,
        ))
        return self.step("alpha")["returned_commit"]

    def restack(self, *extra):
        return self.call("restack", "--actor", "parent", "--run-id", self.run_id,
                         "--step-id", "beta", *extra)

    def head(self, step_id):
        return git(self.repo / ".worktrees" / step_id, "rev-parse", "HEAD").stdout.strip()


class StaleMarkingTest(UpstreamHarness):
    def test_a_rejected_prerequisite_marks_its_stacked_dependent_stale_and_gates_it(self):
        old = self.stacked({"src/beta.txt": "b\n"})
        self.reject_alpha()
        self.assertEqual({"step_id": "alpha", "commit": old}, self.step("beta")["upstream_stale"])
        code, refused = self.verify_handoff("beta")
        self.assertEqual(3, code, refused)
        self.assertIn("restack", refused["error"])
        self.assert_landing_refused("beta", "stale")

    def test_an_in_progress_dependent_keeps_working_and_its_return_records(self):
        self.pair()
        self.finished("alpha")
        self.alpha_old = self.issued("alpha")
        packet = self.build("beta")
        self.reject_alpha()
        self.assertEqual("in_progress", self.step("beta")["status"])
        self.assertIn("upstream_stale", self.step("beta"))
        self.returned(packet)
        self.assertEqual("completed", self.step("beta")["status"])
        self.assertIn("upstream_stale", self.step("beta"))

    def test_a_dependent_stacked_on_a_still_standing_prerequisite_stays_fresh(self):
        self.stacked({"src/beta.txt": "b\n"})
        self.assertNotIn("upstream_stale", self.step("beta"))

    def test_the_ledger_only_code_is_registered_but_never_returnable(self):
        self.assertIn("blocked:upstream_changed", ledger.RETURN_CODES["blocked"])
        enum = ledger.bounded_return_schema(True)["properties"]["blockers"]["items"]["properties"]["code"]["enum"]
        self.assertNotIn("blocked:upstream_changed", enum)


class RestackTest(UpstreamHarness):
    def test_restack_rebases_and_keeps_a_verdict_for_an_unchanged_patch(self):
        self.stacked({"src/beta.txt": "b\n"})
        fixed = self.alpha_fixed({"src/alpha/g.txt": "g\n"})
        code, pending = self.restack()
        self.assertEqual(0, code, pending)
        self.assertEqual("acceptance_pending", pending["outcome"])
        self.assertIn("--acceptance-exit-code", pending["next"]["command"])
        self.assertEqual("restack_acceptance", pending["next"]["category"])
        beta = self.step("beta")
        self.assertIn("upstream_stale", beta)
        self.assertEqual(fixed, beta["pending_acceptance"]["new"])
        self.assertEqual("restack_acceptance", self.next_only()["category"])
        code, result = self.restack("--acceptance-exit-code", "0")
        self.assertEqual(0, code, result)
        self.assertEqual(("restacked", True), (result["outcome"], result["verdict_carried"]))
        beta = self.step("beta")
        self.assertEqual(self.head("beta"), beta["returned_commit"])
        self.assertEqual(fixed, beta["base_commit"])
        self.assertEqual(fixed, beta["provisional_base"]["commit"])
        self.assertNotIn("upstream_stale", beta)
        self.assertNotIn("pending_acceptance", beta)
        self.assertTrue(ledger.commit_verified(beta))
        self.assertEqual(0, git(self.repo / ".worktrees/beta", "merge-base", "--is-ancestor",
                                fixed, "HEAD").returncode)

    def test_a_changed_patch_needs_verification_again(self):
        self.stacked({SHARED: "one\ntwo\nTHREE\n"})
        self.alpha_fixed({SHARED: "ONE\ntwo\nthree\n"})
        code, result = self.restack("--acceptance-exit-code", "0")
        self.assertEqual(0, code, result)
        self.assertEqual(("restacked", False), (result["outcome"], result["verdict_carried"]))
        self.assertNotIn("verify", self.step("beta"))
        self.assertEqual(0, self.verify_handoff("beta")[0])

    def test_a_rebase_conflict_aborts_cleanly_and_routes_to_a_repairable_retry(self):
        self.stacked({SHARED: "one\nBETA\nthree\n"})
        before = self.head("beta")
        self.alpha_fixed({SHARED: "one\nALPHA\nthree\n"})
        code, result = self.restack()
        self.assertEqual(0, code, result)
        self.assertEqual("retry_eligible", result["outcome"])
        self.assertEqual(before, self.head("beta"))
        self.assertEqual("", git(self.repo / ".worktrees/beta", "status", "--porcelain").stdout)
        self.assertFalse((self.repo / ".git/worktrees/beta/rebase-merge").exists())
        beta = self.step("beta")
        self.assertEqual("blocked", beta["status"])
        self.assertEqual("blocked:upstream_changed", beta["blockers"][0]["code"])
        stored = json.loads((self.checkpoint_path().parent / beta["return_path"]).read_text())
        self.assertEqual(("repairable", "blocked:upstream_changed"),
                         ledger.retry_class(self.checkpoint(), beta, stored))
        old, new = beta["upstream_change"]["old"][:12], beta["upstream_change"]["new"][:12]
        self.assertIn(old, beta["blockers"][0]["summary"])
        # The remediation must cite both commits, and the retry spends no same-tier retry.
        with self.assertRaises(AssertionError):
            self.retry("beta", "the base moved", {})
        self.retry("beta", f"alpha moved {old} to {new}", {})
        retried = self.step("beta")
        self.assertEqual((False, "in_progress"), (retried["same_tier_retry_used"], retried["status"]))
        self.assertIn("upstream_stale", retried)

    def test_a_failed_reacceptance_blocks_and_keeps_the_rebased_worktree(self):
        self.stacked({"src/beta.txt": "b\n"})
        fixed = self.alpha_fixed({"src/alpha/g.txt": "g\n"})
        code, result = self.restack("--acceptance-exit-code", "1")
        self.assertEqual(0, code, result)
        self.assertEqual("retry_eligible", result["outcome"])
        beta = self.step("beta")
        self.assertEqual("blocked:upstream_changed", beta["blockers"][0]["code"])
        self.assertIn("acceptance exit 1", beta["blockers"][0]["summary"])
        self.assertEqual(fixed, beta["base_commit"])
        self.assertIn("upstream_stale", beta)

    def test_restack_waits_for_a_new_prerequisite_commit(self):
        self.stacked({"src/beta.txt": "b\n"})
        self.reject_alpha()
        code, refused = self.restack("--acceptance-exit-code", "0")
        self.assertEqual(3, code, refused)
        self.assertIn("no new completed commit", refused["error"])

    def test_a_fresh_step_cannot_be_restacked(self):
        self.stacked({"src/beta.txt": "b\n"})
        code, refused = self.restack()
        self.assertEqual(3, code, refused)
        self.assertIn("only a completed stale step", refused["error"])

    def test_an_integrated_prerequisite_restacks_onto_the_parent_tip(self):
        self.stacked({"src/beta.txt": "b\n"})
        self.alpha_fixed({"src/alpha/g.txt": "g\n"})
        self.passed("alpha")
        self.assertEqual(0, self.land("alpha")[0])
        tip = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        code, result = self.restack("--acceptance-exit-code", "0")
        self.assertEqual(0, code, result)
        self.assertEqual(tip, self.step("beta")["base_commit"])
        code, landed = self.land("beta")
        self.assertEqual(0, code, landed)

    def test_next_names_the_restack_once_the_prerequisite_has_moved_on(self):
        self.stacked({"src/beta.txt": "b\n"})
        self.alpha_fixed({"src/alpha/g.txt": "g\n"})
        block = self.next_only()
        self.assertEqual("restack_stale", block["category"])
        self.assertEqual(["beta"], block["step_ids"])
        self.assertIn(" restack ", block["command"])
        self.assertLessEqual(ledger.proxy_tokens(block), ledger.MAX_NEXT_TOKENS)


class ConcurrentActionsTest(PipelineHarness):
    def test_a_provisionally_ready_step_is_listed_beside_the_verify_action(self):
        self.alpha_in_review()
        block = self.next_only()
        self.assertEqual("verify_pending", block["category"])
        self.assertEqual(["alpha"], block["step_ids"])
        self.assertEqual(["beta"], block["concurrent"])
        self.assertLessEqual(ledger.proxy_tokens(block), ledger.MAX_NEXT_TOKENS)

    def test_a_dispatch_ready_step_is_listed_beside_an_unverified_step(self):
        self.init([leaf("alpha", "leaf-alpha"), leaf("gamma", "leaf-gamma")])
        self.finished("alpha")
        block = self.next_only()
        self.assertEqual("verify_pending", block["category"])
        self.assertEqual(["gamma"], block["concurrent"])

    def test_the_list_is_capped_and_stays_inside_the_token_bound(self):
        names = [f"extra{index}" for index in range(7)]
        self.init([leaf("alpha", "leaf-alpha"), *[leaf(name, f"leaf-{name}") for name in names]])
        self.finished("alpha")
        block = self.next_only()
        self.assertEqual(names[:ledger.MAX_CONCURRENT], block["concurrent"])
        self.assertLessEqual(ledger.proxy_tokens(block), ledger.MAX_NEXT_TOKENS)

    def test_a_block_that_already_names_every_startable_step_adds_nothing(self):
        self.init([leaf("alpha", "leaf-alpha"), leaf("gamma", "leaf-gamma")])
        self.assertNotIn("concurrent", self.next_only())


if __name__ == "__main__":
    unittest.main()
