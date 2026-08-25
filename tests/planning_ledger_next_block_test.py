"""Coverage for the bounded `next` block ledger results emit at the point of use.

The block must be derived from state the module already owns. `TRANS` is the
version-1 table and governs only `transition1()`, so no v2-v4 successor list is
emitted here; these cases pin the two commands that can state their own outcome
soundly, and pin the silence everywhere else.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ledger = load("planning_ledger_next_block", SCRIPTS / "planning_ledger.py")

FAIL = {"code": "failed:acceptance", "summary": "acceptance exited 1"}
HIGHER = {"code": "blocked:needs_higher_tier", "summary": "needs deeper reasoning"}
OTHER = {"code": "blocked:missing_input", "summary": "missing a load-bearing input"}


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def leaf(sid: str, dependencies: list[str], attempts: int = 3) -> dict:
    return {
        "id": sid,
        "dependencies": dependencies,
        "task": "Implement the bounded change",
        "boundary": "Do not edit adjacent modules",
        "read_set": ["src/input.py"],
        "write_set": [f"src/{sid}.py"],
        "settled_decisions": {"shape": "settled"},
        "size": "small",
        "portable_tier": "standard",
        "worktree_owner": f"task/{sid}",
        "acceptance_command": "uv run python -m unittest tests.focused_test",
        "return_contract": "bounded-step-return-v1",
        "stop_conditions": ["missing_load_bearing_information"],
        "work_unit_id": sid,
        "max_attempts": attempts,
        "capability_requirements": {
            "baseline": "plan-step-base-v1",
            "additional": [
                {
                    "kind": "skill",
                    "name": "repository-policy",
                    "reason": "The approved task requires its workflow.",
                }
            ],
        },
    }


def make_plan(leaves: list[dict]) -> dict:
    return {
        "contract_version": 4,
        "objective": "Emit a bounded next block at the point of use",
        "scope_summary": "Only the declared steps are in scope.",
        "approved_decisions": ["The ledger states its own next action."],
        "work_units": [{"id": x["id"], "original_size": "small"} for x in leaves],
        "leaves": leaves,
    }


class LedgerHarness(unittest.TestCase):
    plan_id = "next-plan"

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.common = ["--ledger-root", str(self.root), "--plan-id", self.plan_id]

    def build(self, leaves: list[dict]) -> None:
        self.plan = make_plan(leaves)
        (self.root / "plan.json").write_text(json.dumps(self.plan), encoding="utf-8")
        (self.root / "binding.json").write_text(
            json.dumps(
                {
                    "schema": "planning-capability-binding-v1",
                    "plan_sha256": canonical_sha256(self.plan),
                    "bindings": [
                        {
                            "step_id": x["id"],
                            "host": "codex",
                            "executor": "gpt-5.6-terra",
                            "requirements": copy.deepcopy(x["capability_requirements"]),
                            "evidence": ["host capability inventory"],
                        }
                        for x in leaves
                    ],
                }
            ),
            encoding="utf-8",
        )
        (self.root / "assignments.json").write_text(
            json.dumps(
                [
                    {
                        "id": x["id"],
                        "harness": "codex",
                        "model_or_alias": "gpt-5.6-terra",
                        "effort": "medium",
                        "worktree": f".worktrees/{x['id']}",
                    }
                    for x in leaves
                ]
            ),
            encoding="utf-8",
        )

    def call(self, *args: str):
        with (
            contextlib.redirect_stdout(io.StringIO()) as stream,
            contextlib.redirect_stderr(io.StringIO()),
        ):
            code = ledger.main(args)
        return code, json.loads(stream.getvalue())

    def init(self, leaves: list[dict] | None = None) -> dict:
        self.build(leaves or [leaf("build", [])])
        code, result = self.call(
            *self.common,
            "init-v4",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(self.root / "plan.json"),
            "--assignments-file",
            str(self.root / "assignments.json"),
            "--capability-binding-file",
            str(self.root / "binding.json"),
        )
        self.assertEqual(0, code, result)
        self.run_id = result["run_id"]
        return result

    def checkpoint(self) -> dict:
        path = (
            self.root
            / "planning-policy/ledgers"
            / self.plan_id
            / self.run_id
            / "checkpoint.json"
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def transition(self, sid: str, target: str, *extra: str):
        return self.call(
            *self.common,
            "transition",
            "--actor",
            "parent",
            "--run-id",
            self.run_id,
            "--step-id",
            sid,
            "--to",
            target,
            *extra,
        )

    def start(self, sid: str = "build", agent: str = "agent-1") -> None:
        code, result = self.transition(sid, "ready", "--agent-id", agent)
        self.assertEqual(0, code, result)
        code, result = self.transition(sid, "in_progress")
        self.assertEqual(0, code, result)

    def give(self, status: str, blocker: dict | None = None, marker: str = "x",
             sid: str = "build"):
        step = self.checkpoint()["steps"][sid]
        value = {
            "schema": "bounded-step-return-v1",
            "step_id": sid,
            "agent_id": step["agent_id"],
            "attempt_id": step["attempt_id"],
            "status": status,
            "changed_paths": [],
            "acceptance": {
                "command": "uv run python -m unittest tests.focused_test",
                "exit_code": 0 if status == "completed" else 1,
                "summary": f"attempt {marker}",
            },
            "blockers": [] if blocker is None else [blocker],
            "notes": [],
            "commit_hash": "",
            "unstarted_remainder": ["remaining work"] if status == "oversized" else [],
        }
        path = self.root / "return.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        code, result = self.call(
            *self.common,
            "record-return",
            "--actor",
            "parent",
            "--run-id",
            self.run_id,
            "--return-file",
            str(path),
        )
        self.assertEqual(0, code, result)
        return result

    def retry(self, tier: str, agent: str, sid: str = "build") -> None:
        step = self.checkpoint()["steps"][sid]
        remediation = {
            "schema": "retry-remediation-v1",
            "step_id": sid,
            "prior_attempt_id": step["attempt_id"],
            "prior_return_sha256": step["return_sha256"],
            "diagnosis": "acceptance failed on the bounded case",
            "remediation_action": "retry with a sharper reproduction",
            "executor_mode": "fresh",
            "next_agent_id": agent,
            "next_harness": "codex",
            "target_portable_tier": tier,
        }
        path = self.root / "remediation.json"
        path.write_text(json.dumps(remediation), encoding="utf-8")
        code, result = self.transition(
            sid, "ready", "--retry", "--retry-remediation-file", str(path)
        )
        self.assertEqual(0, code, result)
        code, result = self.transition(sid, "in_progress")
        self.assertEqual(0, code, result)

    def assertBounded(self, block: dict) -> None:
        self.assertLessEqual(ledger.proxy_tokens(block), ledger.MAX_NEXT_TOKENS)


class InitNextBlockTest(LedgerHarness):
    def test_init_v4_names_only_dependency_free_steps_and_the_ready_command(self):
        result = self.init([leaf("build", []), leaf("later", ["build"])])
        block = result["next"]
        # `ready()` admits a pending step only once each dependency is cleaned.
        self.assertEqual(["build"], block["ready_step_ids"])
        self.assertIn(f"--run-id {self.run_id}", block["command"])
        self.assertIn("--step-id build", block["command"])
        self.assertIn("--to ready", block["command"])
        self.assertBounded(block)

    def test_init_v4_lists_every_independent_step_in_stable_order(self):
        result = self.init([leaf("gamma", ["alpha"]), leaf("beta", []), leaf("alpha", [])])
        self.assertEqual(["alpha", "beta"], result["next"]["ready_step_ids"])

    def test_a_wide_plan_sheds_the_command_then_trims_within_the_cap(self):
        result = self.init([leaf(f"step{n:02d}", []) for n in range(30)])
        block = result["next"]
        self.assertBounded(block)
        self.assertNotIn("command", block)
        self.assertTrue(block["truncated"])
        self.assertLess(len(block["ready_step_ids"]), 30)
        self.assertEqual("step00", block["ready_step_ids"][0])


class TransitionSilenceTest(LedgerHarness):
    def test_transition_results_carry_no_next_block(self):
        self.init()
        code, result = self.transition("build", "ready", "--agent-id", "agent-1")
        self.assertEqual(0, code, result)
        self.assertNotIn("next", result)
        code, result = self.transition("build", "in_progress")
        self.assertEqual(0, code, result)
        self.assertNotIn("next", result)

    def test_validate_closeout_carries_no_next_block(self):
        self.init()
        code, result = self.call(
            *self.common, "validate", "--run-id", self.run_id, "--closeout"
        )
        self.assertEqual(0, code, result)
        self.assertNotIn("next", result)


class RecordReturnNextBlockTest(LedgerHarness):
    def test_completed_offers_the_integrate_command_and_no_retry(self):
        self.init()
        self.start()
        block = self.give("completed")["next"]
        self.assertFalse(block["retry_eligible"])
        self.assertEqual("completed", block["outcome"])
        self.assertIn("--to integrated", block["command"])
        self.assertBounded(block)

    def test_first_acceptance_failure_keeps_the_same_tier(self):
        self.init()
        self.start()
        block = self.give("failed", FAIL, marker="a")["next"]
        self.assertTrue(block["retry_eligible"])
        self.assertEqual("failed:acceptance", block["outcome"])
        self.assertEqual("standard", block["next_tier"])
        self.assertIn("--retry-remediation-file", block["command"])
        self.assertBounded(block)

    def test_a_used_same_tier_retry_escalates_the_next_tier(self):
        self.init()
        self.start()
        self.give("failed", FAIL, marker="a")
        self.retry("standard", "agent-2")
        block = self.give("failed", FAIL, marker="b")["next"]
        self.assertTrue(block["retry_eligible"])
        self.assertEqual("analytical", block["next_tier"])

    def test_needs_higher_tier_escalates_immediately(self):
        self.init()
        self.start()
        block = self.give("blocked", HIGHER, marker="a")["next"]
        self.assertTrue(block["retry_eligible"])
        self.assertEqual("blocked:needs_higher_tier", block["outcome"])
        self.assertEqual("analytical", block["next_tier"])

    def test_an_ineligible_outcome_reports_no_retry(self):
        self.init()
        self.start()
        block = self.give("blocked", OTHER, marker="a")["next"]
        self.assertFalse(block["retry_eligible"])
        self.assertEqual("ineligible_outcome", block["outcome"])
        self.assertNotIn("command", block)

    def test_oversized_reports_no_retry(self):
        self.init()
        self.start()
        block = self.give("oversized", OTHER, marker="a")["next"]
        self.assertFalse(block["retry_eligible"])
        self.assertEqual("oversized", block["outcome"])

    def test_exhaustion_names_the_precedence_rule_that_fired(self):
        self.init([leaf("build", [], attempts=1)])
        self.start()
        block = self.give("failed", FAIL, marker="a")["next"]
        self.assertFalse(block["retry_eligible"])
        self.assertEqual("blocked:retry_exhausted", block["outcome"])

    def test_a_repeated_fingerprint_names_no_progress(self):
        self.init()
        self.start()
        self.give("failed", FAIL, marker="same")
        self.retry("standard", "agent-2")
        block = self.give("failed", FAIL, marker="same")["next"]
        self.assertFalse(block["retry_eligible"])
        self.assertEqual("blocked:no_progress", block["outcome"])

    def test_the_tier_ceiling_stops_an_otherwise_eligible_retry(self):
        self.init([leaf("build", [], attempts=5)])
        self.start()
        self.give("blocked", HIGHER, marker="a")
        self.retry("analytical", "agent-2")
        self.give("blocked", HIGHER, marker="b")
        self.retry("deep", "agent-3")
        self.assertEqual("deep", self.checkpoint()["steps"]["build"]["current_tier"])
        block = self.give("blocked", HIGHER, marker="c")["next"]
        self.assertFalse(block["retry_eligible"])
        self.assertEqual("blocked:retry_ceiling_reached", block["outcome"])


class LegacySilenceTest(LedgerHarness):
    def downgrade_to_policyless_v2(self) -> None:
        directory = self.root / "planning-policy/ledgers" / self.plan_id / self.run_id
        plan_path = directory / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["contract_version"] = 2
        for entry in plan["leaves"]:
            entry.pop("capability_requirements")
        plan_path.write_text(json.dumps(plan), encoding="utf-8")

        checkpoint_path = directory / "checkpoint.json"
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        checkpoint["schema"] = 2
        checkpoint["plan_hash"] = ledger.digest(plan)
        checkpoint.pop("retry_policy")
        for step in checkpoint["steps"].values():
            step.pop("capability_binding")
            step.pop("capability_binding_sha256")
            for field in (
                "current_tier",
                "same_tier_retry_used",
                "current_assignment",
                "retry_remediation_path",
                "retry_remediation_sha256",
            ):
                step.pop(field)
        checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")

        events_path = directory / "events.jsonl"
        events = [json.loads(line) for line in events_path.read_text().splitlines()]
        for entry in events:
            entry["action"] = entry["action"].replace("-v4", "-v2")
            if "plan_hash" in entry:
                entry["plan_hash"] = checkpoint["plan_hash"]
        events_path.write_text(
            "".join(json.dumps(entry) + "\n" for entry in events), encoding="utf-8"
        )

    def test_a_policyless_v2_run_records_a_return_without_a_next_block(self):
        self.init([leaf("build", []), leaf("later", ["build"])])
        self.downgrade_to_policyless_v2()
        self.start()
        result = self.give("blocked", OTHER, marker="a")
        self.assertNotIn("next", result)
        self.assertNotIn("retry_policy", self.checkpoint())

    def test_a_version_one_ledger_stays_silent(self):
        steps = json.dumps(
            [
                {
                    "id": name,
                    "dependencies": [],
                    "harness": "codex",
                    "tier": "standard",
                    "model_or_alias": "gpt-5.6-terra",
                    "effort": "medium",
                    "worktree": f".worktrees/{name}",
                }
                for name in ("one", "two")
            ]
        )
        legacy = ["--ledger-root", str(self.root), "--plan-id", "legacy-plan"]
        code, result = self.call(
            *legacy, "init", "--actor", "parent", "--approved", "--steps-json", steps
        )
        self.assertEqual(0, code, result)
        self.assertNotIn("next", result)
        self.assertEqual("legacy_unbounded", result["retry_policy"])

        code, result = self.call(
            *legacy, "transition", "--actor", "parent", "--step-id", "one", "--to", "ready"
        )
        self.assertEqual(0, code, result)
        self.assertNotIn("next", result)


if __name__ == "__main__":
    unittest.main()
