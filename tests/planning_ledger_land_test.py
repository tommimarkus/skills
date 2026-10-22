import json
import unittest
from unittest.mock import patch

from tests import planning_ledger_dispatch_test as base
from planningledger import gitops  # noqa: E402

ledger = base.ledger
git = base.git
leaf = base.leaf


class LandCommandTest(base.DispatchHarness):
    def init(self, leaves, units=None, worktrees=None, **plan_fields):
        plan_fields.setdefault("verification", "closeout-only")
        return super().init(leaves, units, worktrees, **plan_fields)

    def work(self, packet, relative):
        """Commit one file in the packet's worktree and return its commit."""
        tree = packet["worktree"]
        path = f"{tree}/{relative}"
        base.Path(path).parent.mkdir(parents=True, exist_ok=True)
        base.Path(path).write_text(f"{relative}\n")
        git(tree, "add", relative)
        git(tree, "commit", "-m", relative)
        return git(tree, "rev-parse", "HEAD").stdout.strip()

    def finish(self, packet, relative):
        commit = self.work(packet, relative)
        path = self.scratch / f"{packet['step_id']}-return.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "bounded-step-return-v1",
                    "step_id": packet["step_id"],
                    "attempt_id": packet["attempt_id"],
                    "agent_id": packet["agent_id"],
                    "status": "completed",
                    "changed_paths": [relative],
                    "acceptance": {"command": "uv run test", "exit_code": 0, "summary": "ok"},
                    "blockers": [],
                    "notes": [],
                    "unstarted_remainder": [],
                    "commit_hash": commit,
                }
            )
        )
        code, result = self.call(
            "record-return", "--actor", "parent", "--run-id", self.run_id,
            "--return-file", str(path),
        )
        self.assertEqual(0, code, result)
        return result, commit

    def land(self, step_id, target="main"):
        return self.call(
            "land", "--actor", "parent", "--run-id", self.run_id,
            "--step-id", step_id, "--target", target,
        )

    def steps(self):
        return json.loads(self.checkpoint_path().read_text())["steps"]

    def test_a_dependent_pair_flows_from_init_through_land_to_closeout(self):
        self.init([leaf("alpha", "leaf-alpha"), leaf("beta", "leaf-beta", ["alpha"])])
        code, started = self.dispatch("alpha", "--create-from", "main")
        self.assertEqual(0, code, started)
        returned, commit = self.finish(started["handoffs"][0], "src/alpha")
        self.assertIn(" land ", returned["next"]["command"])
        self.assertIn("--step-id alpha", returned["next"]["command"])

        code, landed = self.land("alpha")
        self.assertEqual(0, code, landed)
        self.assertEqual("cleaned", landed["status"])
        self.assertEqual(["alpha"], landed["integrated"])
        self.assertEqual(["alpha"], landed["cleaned"])
        self.assertEqual(["beta"], landed["next"]["ready_step_ids"])
        self.assertIn(" dispatch ", landed["next"]["command"])
        self.assertLessEqual(ledger.next_tokens(landed["next"]), ledger.MAX_NEXT_TOKENS)
        state = self.steps()["alpha"]
        self.assertTrue(state["integrated_commit"])
        self.assertTrue(state["integration_result_path"].startswith("worktree-results/alpha/"))
        self.assertTrue(state["cleanup_result_path"].startswith("worktree-results/alpha/"))
        self.assertTrue((self.repo / "src/alpha").exists())
        self.assertFalse((self.repo / ".worktrees/alpha").exists())
        self.assertEqual("", git(self.repo, "branch", "--list", "leaf-alpha").stdout.strip())

        code, started = self.dispatch("beta", "--create-from", "main")
        self.assertEqual(0, code, started)
        # The dependent's worktree starts from the integrated parent tip.
        self.assertTrue((self.repo / ".worktrees/beta/src/alpha").exists())
        self.finish(started["handoffs"][0], "src/beta")
        code, landed = self.land("beta")
        self.assertEqual(0, code, landed)
        self.assertIn("validate", landed["next"]["command"])
        code, checked = self.call("validate", "--run-id", self.run_id, "--closeout")
        self.assertEqual(0, code, checked)

    def test_a_settled_batch_integrates_once_then_cleans_every_member(self):
        members = [
            leaf("first", "batch-owner", batch="group"),
            leaf("second", "batch-owner", ["first"], batch="group"),
        ]
        units = [
            {
                "id": "unit",
                "original_size": "medium",
                "cohesive_outcome": "One batch outcome",
                "decomposition": {
                    "basis": "failure_isolation",
                    "rationale": "Separate failure surfaces",
                    "shape": "checkpointed",
                },
            }
        ]
        self.init(members, units, {"first": ".worktrees/batch", "second": ".worktrees/batch"})
        code, started = self.dispatch("first", "--create-from", "main")
        self.assertEqual(0, code, started)
        first, second = started["handoffs"]
        self.finish(first, "src/first")
        code, early = self.land("first")
        self.assertEqual(3, code)
        self.assertIn("not settled", early["error"])
        self.finish(second, "src/second")
        code, landed = self.land("second")
        self.assertEqual(0, code, landed)
        self.assertEqual(["first", "second"], landed["integrated"])
        self.assertEqual(["first", "second"], landed["cleaned"])
        steps = self.steps()
        self.assertEqual({"cleaned"}, {item["status"] for item in steps.values()})
        self.assertEqual(1, len({item["integration_result_sha256"] for item in steps.values()}))
        self.assertEqual(1, len({item["cleanup_result_sha256"] for item in steps.values()}))
        self.assertTrue((self.repo / "src/first").exists() and (self.repo / "src/second").exists())

    def test_an_environment_stop_lets_the_next_member_return_but_blocks_the_landing(self):
        members = [
            leaf("first", "batch-owner", batch="group"),
            leaf("second", "batch-owner", ["first"], batch="group"),
        ]
        units = [
            {
                "id": "unit",
                "original_size": "medium",
                "cohesive_outcome": "One batch outcome",
                "decomposition": {
                    "basis": "failure_isolation",
                    "rationale": "Separate failure surfaces",
                    "shape": "checkpointed",
                },
            }
        ]
        self.init(members, units, {"first": ".worktrees/batch", "second": ".worktrees/batch"})
        code, started = self.dispatch("first", "--create-from", "main")
        self.assertEqual(0, code, started)
        first, second = started["handoffs"]
        commit = self.work(first, "src/first")
        stop = self.scratch / "first-return.json"
        stop.write_text(
            json.dumps(
                {
                    "schema": "bounded-step-return-v1",
                    "step_id": "first",
                    "attempt_id": first["attempt_id"],
                    "agent_id": first["agent_id"],
                    "status": "blocked",
                    "changed_paths": ["src/first"],
                    "acceptance": {"command": "uv run test", "exit_code": 1, "summary": "sandbox"},
                    "blockers": [{"code": "blocked:environment", "summary": "sandbox denied a test"}],
                    "notes": [],
                    "unstarted_remainder": [],
                    "commit_hash": commit,
                }
            )
        )
        code, result = self.call(
            "record-return", "--actor", "parent", "--run-id", self.run_id,
            "--return-file", str(stop),
        )
        self.assertEqual(0, code, result)
        self.assertEqual("in_progress", self.steps()["second"]["status"])
        self.finish(second, "src/second")
        steps = self.steps()
        self.assertEqual("blocked", steps["first"]["status"])
        self.assertEqual("completed", steps["second"]["status"])
        code, refused = self.land("second")
        self.assertEqual(3, code)
        self.assertIn("not settled", refused["error"])

    def test_an_integrate_failure_exits_nonzero_and_leaves_state_unchanged(self):
        self.init([leaf("alpha", "leaf-alpha")])
        _code, started = self.dispatch("alpha", "--create-from", "main")
        self.finish(started["handoffs"][0], "src/alpha")
        (self.repo / "dirty.txt").write_text("dirty\n")
        before = self.checkpoint_path().read_bytes()
        code, failed = self.land("alpha")
        self.assertEqual(3, code)
        self.assertIn("integrate failed", failed["error"])
        self.assertIn("parent", failed["error"])
        self.assertEqual(before, self.checkpoint_path().read_bytes())

    def test_a_completed_step_without_a_returned_commit_is_refused_before_integration(self):
        self.init([leaf("alpha", "leaf-alpha")])
        _code, started = self.dispatch("alpha", "--create-from", "main")
        self.finish(started["handoffs"][0], "src/alpha")
        checkpoint = json.loads(self.checkpoint_path().read_text())
        checkpoint["steps"]["alpha"]["returned_commit"] = ""
        self.checkpoint_path().write_text(json.dumps(checkpoint))
        before = self.checkpoint_path().read_bytes()
        main_before = git(self.repo, "rev-parse", "main").stdout
        with patch.object(gitops, "run_worktree_helper") as helper:
            code, refused = self.land("alpha")
        self.assertEqual(3, code)
        self.assertIn("completed step has no returned commit to integrate", refused["error"])
        helper.assert_not_called()
        self.assertEqual(before, self.checkpoint_path().read_bytes())
        self.assertEqual(main_before, git(self.repo, "rev-parse", "main").stdout)

    def test_a_target_other_than_the_checked_out_branch_is_refused_and_leaves_state_unchanged(self):
        self.init([leaf("alpha", "leaf-alpha")])
        _code, started = self.dispatch("alpha", "--create-from", "main")
        self.finish(started["handoffs"][0], "src/alpha")
        git(self.repo, "branch", "elsewhere")
        before = self.checkpoint_path().read_bytes()
        main_before = git(self.repo, "rev-parse", "main").stdout
        code, refused = self.land("alpha", target="elsewhere")
        self.assertEqual(3, code, refused)
        self.assertIn("integrate failed", refused["error"])
        self.assertEqual(before, self.checkpoint_path().read_bytes())
        self.assertEqual(main_before, git(self.repo, "rev-parse", "main").stdout)
        self.assertFalse((self.repo / "src/alpha").exists())

    def test_a_batch_member_with_an_invalid_artifact_mid_batch_leaves_every_member_completed(self):
        members = [
            leaf("first", "batch-owner", batch="group"),
            leaf("second", "batch-owner", ["first"], batch="group"),
        ]
        units = [
            {
                "id": "unit",
                "original_size": "medium",
                "cohesive_outcome": "One batch outcome",
                "decomposition": {
                    "basis": "failure_isolation",
                    "rationale": "Separate failure surfaces",
                    "shape": "checkpointed",
                },
            }
        ]
        self.init(members, units, {"first": ".worktrees/batch", "second": ".worktrees/batch"})
        _code, started = self.dispatch("first", "--create-from", "main")
        first, second = started["handoffs"]
        self.finish(first, "src/first")
        self.finish(second, "src/second")
        real = gitops.run_worktree_helper

        def stale_second(*arguments):
            value, ok = real(*arguments)
            if arguments[0] == "integrate":
                # The first member matches the artifact's source; the second, applied after it,
                # names a different commit.
                value["source_commit"] = value["batch_source_commits"]["first"]
                value["batch_source_commits"]["second"] = "0" * 40
            return value, ok

        before = self.checkpoint_path().read_bytes()
        with patch.object(gitops, "run_worktree_helper", side_effect=stale_second):
            code, refused = self.land("second")
        self.assertEqual(3, code, refused)
        self.assertIn("integrated source does not match returned commit", refused["error"])
        self.assertEqual(before, self.checkpoint_path().read_bytes())
        self.assertEqual({"completed"}, {item["status"] for item in self.steps().values()})

    def test_a_cleanup_failure_stays_integrated_and_a_retry_only_cleans(self):
        self.init([leaf("alpha", "leaf-alpha"), leaf("beta", "leaf-beta", ["alpha"])])
        _code, started = self.dispatch("alpha", "--create-from", "main")
        self.finish(started["handoffs"][0], "src/alpha")
        real = gitops.run_worktree_helper

        def failing_cleanup(*arguments):
            if arguments[0] == "cleanup":
                return {"ok": False, "error": "cleanup refused"}, False
            return real(*arguments)

        with patch.object(gitops, "run_worktree_helper", side_effect=failing_cleanup):
            code, landed = self.land("alpha")
        self.assertEqual(0, code, landed)
        self.assertTrue(landed["ok"])
        self.assertEqual("integrated", landed["status"])
        self.assertEqual("cleanup refused", landed["cleanup_error"])
        self.assertIn(" land ", landed["retry_command"])
        self.assertIn("--target main", landed["retry_command"])
        self.assertEqual("integrated", self.steps()["alpha"]["status"])
        # An integrated step unblocks its dependent before cleanup finishes.
        self.assertEqual(["beta"], landed["next"]["ready_step_ids"])

        code, retried = self.land("alpha")
        self.assertEqual(0, code, retried)
        self.assertEqual([], retried["integrated"])
        self.assertEqual(["alpha"], retried["cleaned"])
        self.assertEqual("cleaned", self.steps()["alpha"]["status"])

    def test_next_only_cleanup_category_names_land(self):
        self.init([leaf("alpha", "leaf-alpha")])
        _code, started = self.dispatch("alpha", "--create-from", "main")
        self.finish(started["handoffs"][0], "src/alpha")
        real = gitops.run_worktree_helper
        with patch.object(
            gitops,
            "run_worktree_helper",
            side_effect=lambda *a: ({"ok": False, "error": "no"}, False)
            if a[0] == "cleanup"
            else real(*a),
        ):
            self.land("alpha")
        code, shown = self.call("show", "--run-id", self.run_id, "--next-only")
        self.assertEqual(0, code, shown)
        self.assertEqual("cleanup_integrated", shown["next"]["category"])
        self.assertIn(" land ", shown["next"]["command"])

    def test_land_refuses_steps_that_are_not_completed_or_integrated(self):
        self.init([leaf("alpha", "leaf-alpha")])
        code, failed = self.land("alpha")
        self.assertEqual(3, code)
        self.assertIn("only completed or integrated", failed["error"])


if __name__ == "__main__":
    unittest.main()
