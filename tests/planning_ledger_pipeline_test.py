"""Retained provisional_v1 runs after the provisional-start pipeline's removal, and the concurrent list."""

import contextlib
import io
import json
import unittest

from tests.planning_ledger_dispatch_test import leaf, ledger
from tests.planning_ledger_verify_test import VerifyHarness

MIGRATION = "blocked:contract_migration_required"


class RetainedRunHarness(VerifyHarness):
    def finished(self, step_id):
        """Dispatch a step, commit one in-scope file in its worktree, and record a completed return."""
        code, started = self.dispatch(step_id, "--create-from", "main")
        self.assertEqual(0, code, started)
        self.worktree = self.repo / ".worktrees" / step_id
        self.commit_file(f"src/{step_id}/f.txt", f"{step_id}\n")
        self.returned(started["handoffs"][0])

    def alpha_in_review(self):
        """A retained provisional_v1 pair: alpha completed with its verify packet issued, no verdict."""
        self.init([leaf("alpha", "leaf-alpha"), leaf("beta", "leaf-beta", ["alpha"])])
        self.finished("alpha")
        code, issued = self.verify_handoff("alpha")
        self.assertEqual(0, code, issued)
        self.rewrite(lambda data: data.update(pipeline_policy="provisional_v1"))
        return issued["handoffs"][0]

    def rewrite(self, change):
        data = self.checkpoint()
        change(data)
        self.checkpoint_path().write_text(json.dumps(data))

    def next_only(self):
        code, shown = self.call("show", "--run-id", self.run_id, "--next-only")
        self.assertEqual(0, code, shown)
        return shown["next"]


class RetainedRunTest(RetainedRunHarness):
    def test_new_runs_never_stamp_the_pipeline_policy_and_restack_is_gone(self):
        self.init([leaf("alpha", "leaf-alpha")])
        self.assertNotIn("pipeline_policy", self.checkpoint())
        self.assertNotIn("blocked:upstream_changed", ledger.RETURN_CODES["blocked"])
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            self.call("restack", "--actor", "parent", "--run-id", self.run_id, "--step-id", "alpha")

    def test_a_run_without_stacked_state_resumes_under_integrated_readiness(self):
        packet = self.alpha_in_review()
        code, refused = self.dispatch("beta", "--create-from", "main")
        self.assertEqual(3, code, refused)
        self.assertIn("dependencies", refused["error"])
        self.assertEqual("await_verify", self.next_only()["category"])
        self.assertEqual(0, self.record_verify(self.verify_return(packet))[0])
        self.assertEqual(0, self.land("alpha")[0])
        code, started = self.dispatch("beta", "--create-from", "main")
        self.assertEqual(0, code, started)
        self.assertNotIn("provisional_base", started["handoffs"][0])
        self.assertEqual("provisional_v1", self.checkpoint()["pipeline_policy"])

    def test_stacked_state_refuses_mutation_while_read_only_commands_work(self):
        commit = "a" * 40
        stacked = {
            "provisional_base": {"step_id": "alpha", "commit": commit},
            "upstream_stale": {"step_id": "alpha", "commit": commit},
            "upstream_change": {"old": commit, "new": commit},
            "pending_acceptance": {"old": commit, "new": commit},
            "blockers": [{"code": "blocked:upstream_changed", "summary": "restack failed"}],
        }
        self.alpha_in_review()
        retained = self.checkpoint_path().read_bytes()
        for field, value in stacked.items():
            with self.subTest(field=field):
                self.checkpoint_path().write_bytes(retained)
                self.rewrite(lambda data: data["steps"]["beta"].update({field: value}))
                before = self.checkpoint_path().read_bytes()
                for code, refused in (
                    self.dispatch("beta", "--create-from", "main"),
                    self.land("alpha"),
                    self.verify_handoff("alpha"),
                    self.call("amend", "--actor", "parent", "--run-id", self.run_id,
                              "--step-id", "beta", "--reason", "widen", "--add-write", "docs"),
                    self.call("close", "--actor", "parent", "--run-id", self.run_id,
                              "--outcome", "abandoned"),
                ):
                    self.assertEqual(3, code, refused)
                    self.assertIn(MIGRATION, refused["error"])
                    self.assertIn("beta", refused["error"])
                self.assertEqual(before, self.checkpoint_path().read_bytes())
                block = self.next_only()
                self.assertEqual(("contract_migration_required", ["beta"]),
                                 (block["category"], block["step_ids"]))
                self.assertNotIn("concurrent", block)
                for arguments in (
                    ("show", "--run-id", self.run_id),
                    ("show", "--run-id", self.run_id, "--step-id", "beta"),
                    ("list",),
                    ("gc", "--dry-run"),
                ):
                    code, shown = self.call(*arguments)
                    self.assertEqual(0, code, shown)


class ConcurrentActionsTest(RetainedRunHarness):
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
        self.assertLessEqual(ledger.next_tokens(block), ledger.MAX_NEXT_TOKENS)

    def test_a_block_that_already_names_every_startable_step_adds_nothing(self):
        self.init([leaf("alpha", "leaf-alpha"), leaf("gamma", "leaf-gamma")])
        self.assertNotIn("concurrent", self.next_only())


if __name__ == "__main__":
    unittest.main()
