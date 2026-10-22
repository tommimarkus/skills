"""Coverage for the bounded live-next chain and restart rehydration.

Guidance must be derived from the validated forward checkpoint and the predicates
that enforce lifecycle legality. `TRANS` remains version-1-only; these cases do
not permit a second v2-v5 transition table.
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

from tests.planning_ledger_dispatch_test import leaf as git_leaf
from tests.planning_ledger_verify_test import (
    MAX_AGENT_ID,
    MAX_PLAN_ID,
    MAX_STEP_ID,
    VerifyHarness,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ledger = load("planning_ledger_next_block", SCRIPTS / "planning_ledger.py")

ENV = {"code": "blocked:environment", "summary": "sandbox denied a required write"}
EXEC = {"code": "failed:execution", "summary": "the tool crashed"}
FAIL = {"code": "failed:acceptance", "summary": "acceptance exited 1"}
HIGHER = {"code": "blocked:needs_higher_tier", "summary": "needs deeper reasoning"}
OTHER = {"code": "blocked:missing_input", "summary": "missing a load-bearing input"}
SCOPE = {"code": "oversized:scope", "summary": "work outgrew its size band"}
RUN_ID = "7d6c608b-0925-47cf-9c31-cc5867295b0e"


def long_ids(count: int) -> list[str]:
    """Distinct 64-character step ids, the grammar's maximum, with 63 proxy tokens each."""
    return [f"{chr(97 + n // 10)}{n % 10}" + "-a" * 30 + "-b" for n in range(count)]


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


def batch_leaf(sid: str, dependencies: list[str], attempts: int = 3) -> dict:
    """A batchable leaf: one shared worktree owner, one batch id."""
    return {
        **leaf(sid, dependencies, attempts),
        "batch": "edits",
        "worktree_owner": "task/batch",
    }


def make_plan(leaves: list[dict], series: dict | None = None) -> dict:
    plan = {
        "contract_version": 5,
        "verification": "closeout-only",
        "objective": "Emit a bounded next block at the point of use",
        "scope_summary": "Only the declared steps are in scope.",
        "approved_decisions": ["The ledger states its own next action."],
        "work_units": [
            {
                "id": x["id"],
                "original_size": "small",
                "cohesive_outcome": f"Complete {x['id']}",
                "decomposition": {"shape": "single"},
            }
            for x in leaves
        ],
        "leaves": leaves,
    }
    if series is not None:
        plan["series"] = series
    return plan


def series_block(final: bool = False, commands: list[str] | None = None) -> dict:
    return {
        "series_id": "next-series",
        "slice": 1,
        "final": final,
        "end_verification_commands": commands or ["uv run python -m unittest tests.example"],
    }


class LedgerHarness(unittest.TestCase):
    plan_id = "next-plan"

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.common = [
            "--ledger-root", str(self.root), "--repo-root", str(self.root),
            "--plan-id", self.plan_id,
        ]

    def build(self, leaves: list[dict], series: dict | None = None) -> None:
        self.plan = make_plan(leaves, series)
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

    def init(self, leaves: list[dict] | None = None, series: dict | None = None) -> dict:
        self.build(leaves or [leaf("build", [])], series)
        code, result = self.call(
            *self.common,
            "init-v5",
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

    def give(self, status: str, blocker: dict | list | None = None, marker: str = "x",
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
            "blockers": (
                [] if blocker is None else blocker if isinstance(blocker, list) else [blocker]
            ),
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

    def worktree_transition(self, sid: str, target: str) -> dict:
        action = "integrate" if target == "integrated" else "cleanup"
        value = {
            "schema": "planning-worktree-result-v1",
            "ok": True,
            "action": action,
            "repo_root": str(self.root),
            "target": "main",
            "branch": f"task/{sid}",
            "worktree": str(self.root / ".worktrees" / sid),
            "source_commit": "a" * 40,
            "rebased_commit": "b" * 40,
            "parent_before": "c" * 40,
            "parent_after": "b" * 40,
        }
        path = self.root / f"{sid}-{target}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        code, result = self.transition(
            sid, target, "--worktree-result", str(path)
        )
        self.assertEqual(0, code, result)
        return result

    def show_next(self):
        return self.call(
            *self.common, "show", "--run-id", self.run_id, "--next-only"
        )

    def assertBounded(self, block: dict) -> None:
        self.assertLessEqual(ledger.next_tokens(block), ledger.MAX_NEXT_TOKENS)


class InitNextBlockTest(LedgerHarness):
    def test_init_v4_names_only_dependency_free_steps_and_the_ready_command(self):
        result = self.init([leaf("build", []), leaf("later", ["build"])])
        block = result["next"]
        # `ready()` admits a pending step only once each dependency is integrated or cleaned.
        self.assertEqual(["build"], block["ready_step_ids"])
        self.assertIn(f"--run-id {self.run_id}", block["command"])
        self.assertIn("--step-id build", block["command"])
        self.assertIn(" dispatch ", block["command"])
        self.assertNotIn("--to ready", block["command"])
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


class LifecycleNextBlockTest(LedgerHarness):
    def test_ready_names_the_dispatch_command_and_in_progress_names_await_identity(self):
        self.init()
        code, result = self.transition("build", "ready", "--agent-id", "agent-1")
        self.assertEqual(0, code, result)
        block = result["next"]
        self.assertIn("--step-id build", block["command"])
        self.assertIn("--to in_progress", block["command"])
        self.assertBounded(block)

        code, result = self.transition("build", "in_progress")
        self.assertEqual(0, code, result)
        block = result["next"]
        self.assertEqual("build", block["await_step_id"])
        self.assertEqual("agent-1", block["agent_id"])
        self.assertEqual(self.checkpoint()["steps"]["build"]["attempt_id"], block["attempt_id"])
        self.assertBounded(block)

    def test_integrated_names_cleanup_and_newly_unblocked_work_and_cleaned_names_it_again(self):
        self.init([leaf("build", []), leaf("later", ["build"])])
        self.start("build")
        self.give("completed", sid="build")
        integrated = self.worktree_transition("build", "integrated")["next"]
        # Dispatching the unblocked dependent outranks cleanup on the critical path.
        self.assertIn("--step-id later", integrated["command"])
        self.assertIn(" dispatch ", integrated["command"])
        self.assertEqual(["later"], integrated["ready_step_ids"])
        # The integrated step's own cleanup stays named, just behind the dispatch.
        self.assertEqual("build", integrated["cleanup_step_id"])
        self.assertBounded(integrated)

        cleaned = self.worktree_transition("build", "cleaned")["next"]
        self.assertEqual(["later"], cleaned["ready_step_ids"])
        self.assertIn("--step-id later", cleaned["command"])
        self.assertIn(" dispatch ", cleaned["command"])
        self.assertBounded(cleaned)

    def test_cleaning_the_last_step_names_closeout_validation(self):
        self.init()
        self.start()
        self.give("completed")
        self.worktree_transition("build", "integrated")
        block = self.worktree_transition("build", "cleaned")["next"]
        self.assertIn("validate", block["command"])
        self.assertIn("--closeout", block["command"])
        self.assertBounded(block)

    def test_validate_closeout_names_the_completed_run_close_command(self):
        self.init()
        self.start()
        self.give("completed")
        self.worktree_transition("build", "integrated")
        self.worktree_transition("build", "cleaned")
        code, result = self.call(
            *self.common, "validate", "--run-id", self.run_id, "--closeout"
        )
        self.assertEqual(0, code, result)
        block = result["next"]
        self.assertIn("close --actor parent", block["command"])
        self.assertIn("--outcome completed", block["command"])
        self.assertBounded(block)

    def test_reopen_names_retryable_steps_and_the_first_remediation_command(self):
        self.init([leaf("alpha", []), leaf("beta", [])])
        for sid in ("alpha", "beta"):
            self.start(sid, f"agent-{sid}")
            self.give("failed", FAIL, marker=sid, sid=sid)
        code, closed = self.call(
            *self.common,
            "close", "--actor", "parent", "--run-id", self.run_id,
            "--outcome", "blocked", "--reason", "retry after external recovery",
        )
        self.assertEqual(0, code, closed)
        code, reopened = self.call(
            *self.common,
            "reopen", "--actor", "parent", "--run-id", self.run_id,
            "--reason", "dependency is available",
        )
        self.assertEqual(0, code, reopened)
        block = reopened["next"]
        self.assertEqual(["alpha", "beta"], block["retryable_step_ids"])
        self.assertIn("--step-id alpha", block["command"])
        self.assertIn("--retry-remediation-file", block["command"])
        self.assertBounded(block)


class ExternalDependencyGateTest(unittest.TestCase):
    def data(self, status: str) -> dict:
        return {
            "schema": 5,
            "steps": {
                "a": {"id": "a", "status": status, "dependencies": []},
                "b": {"id": "b", "status": "pending", "dependencies": ["a"]},
            },
        }

    def test_externals_unblock_at_integrated_or_cleaned(self):
        for status, expected in (("integrated", True), ("cleaned", True), ("completed", False)):
            with self.subTest(status=status):
                data = self.data(status)
                self.assertEqual(
                    expected, ledger.dependencies_clean(data, data["steps"]["b"], {})
                )


class NextOnlyRehydrationTest(LedgerHarness):
    def assertEnvelopeBounded(self, result: dict) -> None:
        self.assertLessEqual(ledger.next_tokens(result), ledger.MAX_NEXT_ONLY_TOKENS)
        self.assertBounded(result["next"])

    def assertCategory(self, expected: str) -> dict:
        code, result = self.show_next()
        self.assertEqual(0, code, result)
        self.assertEqual(expected, result["next"]["category"])
        self.assertEnvelopeBounded(result)
        return result["next"]

    def test_priority_and_commands_follow_the_live_checkpoint(self):
        self.init([leaf("clean", []), leaf("integrate", []), leaf("retry", []),
                   leaf("pending", []), leaf("ready", []), leaf("active", [])])
        self.start("clean", "agent-clean")
        self.give("completed", sid="clean")
        self.worktree_transition("clean", "integrated")
        self.start("integrate", "agent-integrate")
        self.give("completed", sid="integrate")
        self.start("retry", "agent-retry")
        self.give("failed", FAIL, sid="retry")
        code, _ = self.transition("ready", "ready", "--agent-id", "agent-ready")
        self.assertEqual(0, code)
        self.start("active", "agent-active")

        # Schema 5 puts cleanup behind every dispatch-side action, so the chain
        # walks integrate, remediate, dispatch, await, then cleanup and closeout.
        block = self.assertCategory("integrate_completed")
        self.assertEqual(["integrate"], block["step_ids"])
        self.assertIn(" land --actor parent ", block["command"])
        self.assertIn("--step-id integrate --target", block["command"])
        self.worktree_transition("integrate", "integrated")

        block = self.assertCategory("remediate_failure")
        self.assertEqual(["retry"], block["retryable_step_ids"])
        self.assertIn("--step-id retry --to ready --retry --retry-remediation-file", block["command"])
        self.retry("standard", "agent-retry-2", sid="retry")

        block = self.assertCategory("ready_pending")
        self.assertEqual(["pending"], block["ready_step_ids"])
        self.assertIn(" dispatch --actor parent ", block["command"])
        self.assertIn("--step-id pending ", block["command"])
        code, _ = self.transition("pending", "ready", "--agent-id", "agent-pending")
        self.assertEqual(0, code)

        block = self.assertCategory("dispatch_ready")
        self.assertEqual(["pending", "ready"], block["ready_step_ids"])
        self.assertTrue(block["command"].endswith("--step-id pending --to in_progress"))
        for sid in ("pending", "ready"):
            code, _ = self.transition(sid, "in_progress")
            self.assertEqual(0, code)

        block = self.assertCategory("await_return")
        # Steps are ordered by id, so the first in-progress step is `active`.
        self.assertEqual("active", block["await_step_id"])
        self.assertEqual("agent-active", block["agent_id"])
        self.assertEqual(self.checkpoint()["steps"]["active"]["attempt_id"], block["attempt_id"])
        for sid in ("retry", "pending", "ready", "active"):
            self.give("completed", sid=sid)
            self.worktree_transition(sid, "integrated")

        block = self.assertCategory("cleanup_integrated")
        self.assertEqual(
            ["active", "clean", "integrate", "pending", "ready", "retry"], block["step_ids"]
        )
        self.assertIn("--step-id active --target", block["command"])
        for sid in ("clean", "integrate", "retry", "pending", "ready", "active"):
            self.worktree_transition(sid, "cleaned")

        block = self.assertCategory("validate_closeout")
        self.assertIn(" validate --run-id ", block["command"])
        self.assertTrue(block["command"].endswith("--closeout"))

    def test_cleanup_waits_behind_ready_dispatch_and_await_then_leads_to_closeout(self):
        self.init([leaf("clean", []), leaf("pending", []), leaf("ready", []), leaf("active", [])])
        self.start("clean", "agent-clean")
        self.give("completed", sid="clean")
        self.worktree_transition("clean", "integrated")
        self.assertCategory("ready_pending")
        for sid in ("pending", "ready", "active"):
            code, _ = self.transition(sid, "ready", "--agent-id", f"agent-{sid}")
            self.assertEqual(0, code)
        self.assertCategory("dispatch_ready")
        for sid in ("pending", "ready", "active"):
            code, _ = self.transition(sid, "in_progress")
            self.assertEqual(0, code)
        self.assertCategory("await_return")
        for sid in ("pending", "ready", "active"):
            self.give("completed", sid=sid)
            self.worktree_transition(sid, "integrated")
        block = self.assertCategory("cleanup_integrated")
        self.assertIn("--step-id active", block["command"])
        for sid in ("clean", "pending", "ready", "active"):
            self.worktree_transition(sid, "cleaned")
        self.assertCategory("validate_closeout")

    def test_pending_dispatch_await_closeout_and_terminal_categories(self):
        self.init()
        self.assertCategory("ready_pending")
        code, _ = self.transition("build", "ready", "--agent-id", "agent-1")
        self.assertEqual(0, code)
        self.assertCategory("dispatch_ready")
        code, _ = self.transition("build", "in_progress")
        self.assertEqual(0, code)
        self.assertCategory("await_return")
        self.give("completed")
        self.worktree_transition("build", "integrated")
        self.worktree_transition("build", "cleaned")
        self.assertCategory("validate_closeout")
        code, result = self.call(
            *self.common, "close", "--actor", "parent", "--run-id", self.run_id,
            "--outcome", "completed",
        )
        self.assertEqual(0, code, result)
        terminal = self.assertCategory("terminal_closed")
        self.assertEqual("completed", terminal["outcome"])
        self.assertNotIn("command", terminal)

    def test_terminal_blockage_is_reported_when_no_legal_action_remains(self):
        self.init([leaf("build", [], attempts=1)])
        self.start()
        self.give("failed", FAIL)
        block = self.assertCategory("terminal_blocked")
        self.assertEqual(["build"], block["blocked_step_ids"])
        self.assertNotIn("command", block)

    def test_next_only_is_read_only_and_full_show_remains_the_diagnostic_fallback(self):
        self.init([leaf(f"step{n:02d}", []) for n in range(40)])
        directory = self.root / "planning-policy/ledgers" / self.plan_id / self.run_id
        before = {
            name: (directory / name).read_bytes()
            for name in ("checkpoint.json", "events.jsonl", "plan.json")
        }
        code, result = self.show_next()
        self.assertEqual(0, code, result)
        self.assertEnvelopeBounded(result)
        self.assertTrue(result["next"]["truncated"])
        self.assertIn("command", result["next"])
        self.assertEqual(
            before,
            {name: (directory / name).read_bytes() for name in before},
        )

        code, full = self.call(*self.common, "show", "--run-id", self.run_id)
        self.assertEqual(0, code, full)
        self.assertTrue(full["truncated"])
        self.assertLessEqual(full["summary_proxy_tokens"], ledger.MAX_TOKENS)
        self.assertNotIn("next", full)


class RecordReturnNextBlockTest(LedgerHarness):
    def test_completed_offers_the_integrate_command_and_no_retry(self):
        self.init()
        self.start()
        block = self.give("completed")["next"]
        self.assertFalse(block["retry_eligible"])
        self.assertEqual("completed", block["outcome"])
        self.assertIn(" land ", block["command"])
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
        block = self.give("oversized", SCOPE, marker="a")["next"]
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


class RepairableRetryTest(LedgerHarness):
    """Reasoning stops escalate; repairable stops retry at the same tier."""

    def amend(self, *extra: str, sid: str = "build"):
        return self.call(
            *self.common, "amend", "--actor", "parent", "--run-id", self.run_id,
            "--step-id", sid, "--reason", "repair execution metadata", *extra,
        )

    def step(self, sid: str = "build") -> dict:
        return self.checkpoint()["steps"][sid]

    def test_environment_stops_retry_at_the_same_tier_without_spending_it(self):
        self.init([leaf("build", [], attempts=4)])
        self.start()
        block = self.give("blocked", ENV, marker="a")["next"]
        self.assertTrue(block["retry_eligible"])
        self.assertEqual("repairable", block["retry_class"])
        self.assertEqual("blocked:environment", block["outcome"])
        self.assertEqual("standard", block["next_tier"])
        self.assertBounded(block)
        self.retry("standard", "agent-2")
        self.assertFalse(self.step()["same_tier_retry_used"])
        block = self.give("blocked", ENV, marker="b")["next"]
        self.assertEqual("standard", block["next_tier"])
        self.retry("standard", "agent-3")
        self.assertEqual("standard", self.step()["current_tier"])

    def test_a_repairable_stop_after_a_spent_same_tier_retry_is_not_forced_upward(self):
        self.init()
        self.start()
        self.give("failed", FAIL, marker="a")
        self.retry("standard", "agent-2")
        self.assertTrue(self.step()["same_tier_retry_used"])
        block = self.give("blocked", ENV, marker="b")["next"]
        self.assertEqual("repairable", block["retry_class"])
        self.assertEqual("standard", block["next_tier"])
        self.retry("standard", "agent-3")

    def test_reasoning_stops_keep_their_rules_and_class(self):
        self.init()
        self.start()
        block = self.give("failed", FAIL, marker="a")["next"]
        self.assertEqual("reasoning", block["retry_class"])
        self.retry("standard", "agent-2")
        block = self.give("failed", FAIL, marker="b")["next"]
        self.assertEqual("analytical", block["next_tier"])

    def test_the_first_family_blocker_classifies_the_return(self):
        for blockers, eligible in (
            ([FAIL, EXEC], True),
            ([EXEC, FAIL], False),
            ([{"code": "failed:acceptance", "summary": "again"}, FAIL], True),
        ):
            with self.subTest(blockers=[b["code"] for b in blockers]):
                self.init()
                self.start()
                block = self.give("failed", blockers)["next"]
                self.assertEqual(eligible, block["retry_eligible"])
        self.init()
        self.start()
        block = self.give("blocked", [OTHER, ENV])["next"]
        self.assertFalse(block["retry_eligible"])
        self.assertEqual("ineligible_outcome", block["outcome"])

    def test_the_predicate_is_one_function_for_every_consumer(self):
        self.init()
        self.start()
        self.give("blocked", ENV, marker="a")
        data = self.checkpoint()
        step = data["steps"]["build"]
        directory = self.root / "planning-policy/ledgers" / self.plan_id / self.run_id
        value = ledger.current_return(directory, step)
        self.assertEqual(("repairable", "blocked:environment"), ledger.retry_class(data, step, value))
        retryable = ledger.retryable_steps(directory, data, {})
        self.assertEqual([("build", "blocked:environment", "repairable")], [(s["id"], o, k) for s, o, k in retryable])
        code, result = self.show_next()
        self.assertEqual("remediate_failure", result["next"]["category"])
        self.assertEqual("repairable", result["next"]["retry_class"])

    def test_an_amendment_after_the_return_makes_other_stops_repairable(self):
        for status, blocker in (("blocked", OTHER), ("failed", EXEC)):
            with self.subTest(code=blocker["code"]):
                self.init()
                self.start()
                block = self.give(status, blocker, marker="a")["next"]
                self.assertFalse(block["retry_eligible"])
                self.assertEqual("terminal_blocked", self.show_next()[1]["next"]["category"])
                code, result = self.amend("--add-read", "docs")
                self.assertEqual(0, code, result)
                code, result = self.show_next()
                self.assertEqual("remediate_failure", result["next"]["category"])
                self.assertEqual("repairable", result["next"]["retry_class"])
                self.retry("standard", "agent-2")
                self.assertFalse(self.step()["same_tier_retry_used"])
                self.assertEqual("standard", self.step()["current_tier"])

    def test_an_amendment_before_the_return_does_not_make_the_stop_repairable(self):
        self.init()
        code, result = self.transition("build", "ready", "--agent-id", "agent-1")
        self.assertEqual(0, code, result)
        self.assertEqual(0, self.amend("--add-read", "docs")[0])
        self.assertEqual(0, self.transition("build", "in_progress")[0])
        block = self.give("blocked", OTHER, marker="a")["next"]
        self.assertFalse(block["retry_eligible"])
        self.assertEqual("terminal_blocked", self.show_next()[1]["next"]["category"])

    def test_an_amendment_does_not_reopen_other_terminal_stops(self):
        self.init([leaf("build", [], attempts=1)])
        self.start()
        block = self.give("blocked", ENV, marker="a")["next"]
        self.assertEqual("blocked:retry_exhausted", block["outcome"])
        self.assertEqual(0, self.amend("--add-read", "docs")[0])
        self.assertEqual("terminal_blocked", self.show_next()[1]["next"]["category"])
        code, _ = self.transition("build", "ready", "--retry")
        self.assertEqual(3, code)
        self.init()
        self.start()
        self.give("oversized", SCOPE, marker="a")
        self.assertEqual(0, self.amend("--add-read", "docs")[0])
        self.assertEqual("terminal_blocked", self.show_next()[1]["next"]["category"])

    def test_a_repairable_retry_is_still_bounded_by_attempts_and_progress(self):
        self.init([leaf("build", [], attempts=2)])
        self.start()
        self.give("blocked", ENV, marker="same")
        self.retry("standard", "agent-2")
        block = self.give("blocked", ENV, marker="same")["next"]
        self.assertEqual("blocked:no_progress", block["outcome"])
        self.init([leaf("build", [], attempts=2)])
        self.start()
        self.give("blocked", ENV, marker="a")
        self.retry("standard", "agent-2")
        block = self.give("blocked", ENV, marker="b")["next"]
        self.assertEqual("blocked:retry_exhausted", block["outcome"])


class BatchNextBlockTest(LedgerHarness):
    """A batch integrates its shared tip once, so a completed member waits.

    Suggesting the integrate while a sibling still holds the shared worktree
    would rebase a tip the batch has not finished writing, and the cleanup that
    follows would remove the worktree the sibling is still working in.
    """

    def dispatch(self, *ids: str) -> None:
        for sid in ids:
            self.start(sid, "batch-worker")

    def test_a_completed_member_waits_for_a_sibling_that_can_still_commit(self):
        self.init([batch_leaf("b0", []), batch_leaf("b1", ["b0"])])
        self.dispatch("b0", "b1")
        block = self.give("completed", sid="b0")["next"]
        self.assertEqual("await_return", block["category"])
        self.assertEqual("b1", block["await_step_id"])
        self.assertNotIn("command", block)
        self.assertBounded(block)

        code, held = self.show_next()
        self.assertEqual(0, code, held)
        self.assertEqual("await_return", held["next"]["category"])

        settled = self.give("completed", sid="b1")["next"]
        self.assertFalse(settled["retry_eligible"])
        self.assertEqual("completed", settled["outcome"])
        self.assertIn(" land ", settled["command"])
        self.assertBounded(settled)

        code, ready_to_integrate = self.show_next()
        self.assertEqual(0, code, ready_to_integrate)
        self.assertEqual("integrate_completed", ready_to_integrate["next"]["category"])
        self.assertEqual(["b0", "b1"], ready_to_integrate["next"]["step_ids"])

    def test_an_unwound_follower_still_holds_back_the_shared_integrate(self):
        self.init([batch_leaf("b0", []), batch_leaf("b1", ["b0"]), batch_leaf("b2", ["b1"])])
        self.dispatch("b0", "b1", "b2")
        self.give("completed", sid="b0")
        self.give("failed", FAIL, sid="b1")
        code, unwound = self.transition("b2", "pending")
        self.assertEqual(0, code, unwound)
        # `b1` is retryable and `b2` will be redispatched, so `b0` keeps waiting.
        self.assertEqual("remediate_failure", self.show_next()[1]["next"]["category"])


class SeriesOverlayNextBlockTest(LedgerHarness):
    """The series overlay never inlines end_verification_commands, so a
    worst-case series still fits the same bounds a plain run does.
    """

    def drive_to_cleaned(self) -> dict:
        self.start()
        self.give("completed")
        self.worktree_transition("build", "integrated")
        return self.worktree_transition("build", "cleaned")

    def closeout_validate(self) -> dict:
        code, result = self.call(*self.common, "validate", "--run-id", self.run_id, "--closeout")
        self.assertEqual(0, code, result)
        return result

    def test_final_series_closeout_marker_stays_bounded_at_worst_case(self):
        # Token-dense worst case: a long run of one word character is a single
        # proxy token, so an "x" * 480 command could be inlined without moving
        # the measured bound at all. Realistic command text is what blows it.
        commands = [("uv run python -m unittest tests.suite -k case " * 11)[:480]] * 4
        self.assertGreater(ledger.proxy_tokens(commands), ledger.MAX_NEXT_ONLY_TOKENS)
        self.init(series=series_block(final=True, commands=commands))
        cleaned = self.drive_to_cleaned()
        block = cleaned["next"]
        self.assertIn("--closeout", block["command"])
        self.assertTrue(block["series_end"])
        self.assertBounded(block)

        code, next_only = self.show_next()
        self.assertEqual(0, code, next_only)
        self.assertTrue(next_only["next"]["series_end"])
        self.assertBounded(next_only["next"])
        self.assertLessEqual(ledger.next_tokens(next_only), ledger.MAX_NEXT_ONLY_TOKENS)

    def test_final_series_close_command_carries_the_marker_not_the_flag(self):
        self.init(series=series_block(final=True))
        self.drive_to_cleaned()
        block = self.closeout_validate()["next"]
        self.assertTrue(block["series_end"])
        self.assertNotIn("--series-handoff-file", block["command"])
        self.assertBounded(block)

    def test_non_final_series_close_command_carries_the_handoff_hint(self):
        self.init(series=series_block(final=False))
        self.drive_to_cleaned()
        block = self.closeout_validate()["next"]
        self.assertNotIn("series_end", block)
        self.assertIn("--series-handoff-file", block["command"])
        self.assertBounded(block)

    def test_non_series_close_command_carries_neither_flag_nor_marker(self):
        self.init()
        self.drive_to_cleaned()
        block = self.closeout_validate()["next"]
        self.assertNotIn("series_end", block)
        self.assertNotIn("--series-handoff-file", block["command"])
        self.assertBounded(block)


class VerifyNextBlockTest(VerifyHarness):
    """verify_pending sits before land and after the failure-retry route."""

    def two_steps(self):
        self.init([git_leaf("alpha", "leaf-alpha"), git_leaf("beta", "leaf-beta")])
        packets = {}
        for sid in ("alpha", "beta"):
            code, result = self.dispatch(sid, "--create-from", "main")
            self.assertEqual(0, code, result)
            packets[sid] = result["handoffs"][0]
        self.worktree = self.repo / ".worktrees/beta"
        failure = {"code": "failed:acceptance", "summary": "acceptance exited 1"}
        self.returned(packets["beta"], "failed", [failure])
        self.worktree = self.repo / ".worktrees/alpha"
        self.commit_file("src/alpha/a.txt", "one\n")
        self.returned(packets["alpha"])

    def category(self):
        code, result = self.call("show", "--run-id", self.run_id, "--next-only")
        self.assertEqual(0, code, result)
        self.assertLessEqual(ledger.next_tokens(result), ledger.MAX_NEXT_ONLY_TOKENS)
        self.assertLessEqual(ledger.next_tokens(result["next"]), ledger.MAX_NEXT_TOKENS)
        return result["next"]["category"]

    def test_verify_pending_precedes_land_and_land_precedes_retry(self):
        self.two_steps()
        self.assertEqual("verify_pending", self.category())
        code, issued = self.verify_handoff()
        (verify,) = issued["handoffs"]
        self.assertEqual(0, self.record_verify(self.verify_return(verify))[0])
        self.assertEqual("integrate_completed", self.category())
        self.assertEqual(0, self.land()[0])
        self.assertEqual("remediate_failure", self.category())

    def test_a_rejected_step_routes_to_the_retry_not_to_land(self):
        self.two_steps()
        code, issued = self.verify_handoff()
        (verify,) = issued["handoffs"]
        verdict = self.verify_return(verify, "reject", [self.finding()])
        self.assertEqual(0, self.record_verify(verdict)[0])
        code, result = self.call("show", "--run-id", self.run_id, "--next-only")
        self.assertEqual("remediate_failure", result["next"]["category"])
        self.assertEqual(["alpha", "beta"], result["next"]["retryable_step_ids"])



class IdNeutralCapLedgerTest(LedgerHarness):
    """#144: the full block fits for every admissible id; collections still trim by count."""

    plan_id = MAX_PLAN_ID

    def test_maximal_ids_keep_the_full_init_and_transition_next(self):
        sid = MAX_STEP_ID
        result = self.init([leaf(sid, [])])
        scope = f"--plan-id {self.plan_id}"
        self.assertEqual(
            {"ready_step_ids": [sid], "command": (
                f"{scope} dispatch --actor parent --run-id {self.run_id} "
                f"--step-id {sid} --agent-id <agent-id>")},
            result["next"],
        )
        code, readied = self.transition(sid, "ready", "--agent-id", MAX_AGENT_ID)
        command = (f"{scope} transition --actor parent --run-id {self.run_id} "
                   f"--step-id {sid} --to in_progress")
        self.assertEqual((0, {"command": command}), (code, readied.get("next")))
        code, started = self.transition(sid, "in_progress")
        attempt = self.checkpoint()["steps"][sid]["attempt_id"]
        self.assertEqual(
            (0, {"await_step_id": sid, "agent_id": MAX_AGENT_ID, "attempt_id": attempt}),
            (code, started.get("next")),
        )

    def test_long_ids_still_cap_the_concurrent_list_by_count(self):
        names = long_ids(8)
        self.init([leaf(name, []) for name in names])
        self.start(names[0])
        self.give("completed", sid=names[0])
        code, shown = self.show_next()
        land = (f"--plan-id {self.plan_id} land --actor parent --run-id {self.run_id} "
                f"--step-id {names[0]} --target <target-branch>")
        self.assertEqual(
            (0, {"category": "integrate_completed", "step_ids": names[:1], "command": land,
                 "concurrent": names[1:1 + ledger.MAX_CONCURRENT]}),
            (code, shown.get("next")),
        )


class IdNeutralMeasureTest(unittest.TestCase):
    """The one measure every next cap uses counts each identifier as one placeholder."""

    def test_every_identifier_becomes_the_placeholder_and_structure_stays(self):
        block = {
            "category": "remediate_failure",
            "retry_class": "reasoning",
            "retryable_step_ids": [MAX_STEP_ID, "b"],
            "agent_id": MAX_AGENT_ID,
            "command": ledger.dispatch_command(MAX_PLAN_ID, RUN_ID, MAX_STEP_ID),
        }
        self.assertEqual(
            {
                "category": "remediate_failure",
                "retry_class": "reasoning",
                "retryable_step_ids": ["ID", "ID"],
                "agent_id": "ID",
                "command": "--plan-id ID dispatch --actor parent --run-id ID --step-id ID "
                "--agent-id ID",
            },
            ledger.id_neutral(block),
        )

    def test_the_same_structure_measures_equal_for_short_and_maximal_ids(self):
        def blocks(plan_id: str, step_id: str, agent_id: str) -> list[dict]:
            data = {"plan_id": plan_id, "run_id": RUN_ID}
            return [
                {"retry_eligible": False, "outcome": "completed",
                 **ledger.verify_commands(data, step_id)},
                {"category": "integrate_completed", "step_ids": [step_id],
                 "command": ledger.land_command(data, step_id), "concurrent": [step_id] * 4},
                {"category": "remediate_failure", "retryable_step_ids": [step_id],
                 "command": ledger.retry_command(plan_id, RUN_ID, step_id)},
                {"await_step_id": step_id, "agent_id": agent_id, "attempt_id": RUN_ID},
                {"category": "rerecord_return", "step_id": step_id},
                {"category": "terminal_blocked", "blocked_step_ids": [step_id] * 3},
                {"ok": True, "action": "show-next", "plan_id": plan_id, "run_id": RUN_ID,
                 "next": {"ready_step_ids": [step_id], "cleanup_step_id": step_id,
                          "command": ledger.dispatch_command(plan_id, RUN_ID, step_id)}},
            ]

        short = blocks("p", "s", "w")
        maximal = blocks(MAX_PLAN_ID, MAX_STEP_ID, MAX_AGENT_ID)
        self.assertEqual([ledger.next_tokens(block) for block in short],
                         [ledger.next_tokens(block) for block in maximal])
        self.assertGreater(ledger.proxy_tokens(maximal[0]), ledger.MAX_NEXT_TOKENS)

    def test_a_collection_trims_to_the_same_count_for_short_and_maximal_ids(self):
        def trimmed(plan_id: str, ids: list[str]) -> dict:
            return ledger.bounded_action_next(
                {"category": "ready_pending", "ready_step_ids": ids,
                 "command": ledger.dispatch_command(plan_id, RUN_ID, ids[0])},
                "ready_step_ids",
            )

        short_ids = [f"s{n}" for n in range(30)]
        short, maximal = trimmed("p", short_ids), trimmed(MAX_PLAN_ID, long_ids(30))
        kept = len(short["ready_step_ids"])
        self.assertLess(kept, 30)
        self.assertEqual((True, short_ids[:kept]), (short["truncated"], short["ready_step_ids"]))
        self.assertEqual((True, long_ids(30)[:kept]),
                         (maximal["truncated"], maximal["ready_step_ids"]))


if __name__ == "__main__":
    unittest.main()
