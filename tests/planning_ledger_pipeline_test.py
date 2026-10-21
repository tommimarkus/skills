"""Provisional start: a dependent builds on a completed prerequisite while its verifier runs."""

import json
import unittest

from tests.planning_ledger_dispatch_test import bare, git, leaf, ledger
from tests.planning_ledger_verify_test import VerifyHarness


class PipelineHarness(VerifyHarness):
    def pair(self, **extra):
        self.init([leaf("alpha", "leaf-alpha"), leaf("beta", "leaf-beta", ["alpha"])], **extra)

    def build(self, step_id, create_from="main"):
        """Dispatch a step and commit one in-scope file in its worktree."""
        code, started = self.dispatch(step_id, "--create-from", create_from)
        self.assertEqual(0, code, started)
        self.worktree = self.repo / ".worktrees" / step_id
        self.commit_file(f"src/{step_id}/f.txt", f"{step_id}\n")
        return started["handoffs"][0]

    def finished(self, step_id, create_from="main"):
        packet = self.build(step_id, create_from)
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
        code, refused = self.land("beta")
        self.assertEqual(3, code, refused)
        self.assertIn("land the prerequisite first", refused["error"])
        code, refused = self.call(
            "transition", "--actor", "parent", "--run-id", self.run_id, "--step-id", "beta",
            "--to", "integrated", "--worktree-result", str(self.scratch / "none.json"),
        )
        self.assertEqual(3, code, refused)
        self.assertIn("land the prerequisite first", refused["error"])
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
