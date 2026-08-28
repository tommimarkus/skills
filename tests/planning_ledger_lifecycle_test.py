import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = (
    Path(__file__).parents[1]
    / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py"
)
SPEC = importlib.util.spec_from_file_location("planning_ledger_lifecycle", SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(ledger)


class PlanningLedgerLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def common(self, plan_id="plan"):
        return ["--ledger-root", str(self.root), "--plan-id", plan_id]

    def call(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = ledger.main(arguments)
        return code, json.loads(stream.getvalue())

    def plan(
        self,
        plan_id="plan",
        count=2,
        dependent=False,
        max_attempts=2,
        portable_tier="standard",
    ):
        path = self.root / f"{plan_id}-plan.json"
        leaves = []
        for number in range(count):
            step_id = f"step{number}"
            leaf = {
                "id": step_id,
                "dependencies": ["step0"] if dependent and number == 1 else [],
                "task": "task",
                "boundary": "boundary",
                "read_set": ["src"],
                "write_set": ["src"],
                "settled_decisions": "settled",
                "size": "small",
                "portable_tier": portable_tier,
                "worktree_owner": "owner",
                "acceptance_command": "uv run test",
                "return_contract": "bounded-step-return-v1",
                "stop_conditions": ["missing_load_bearing_information"],
                "work_unit_id": step_id,
                "max_attempts": max_attempts,
                "capability_requirements": {
                    "baseline": "plan-step-base-v1",
                    "additional": [],
                },
            }
            if portable_tier in {"analytical", "deep"}:
                leaf["irreducible_unknown_or_risk"] = "retry terminal precedence"
            leaves.append(leaf)
        plan = {
            "contract_version": 4,
            "objective": "objective",
            "scope_summary": "scope",
            "approved_decisions": ["settled"],
            "leaves": leaves,
            "work_units": [
                {"id": f"step{number}", "original_size": "small"} for number in range(count)
            ],
        }
        if portable_tier in {"analytical", "deep"}:
            plan["analytical_heavy_exception"] = {
                "rationale": "exercise retry terminal precedence",
                "user_approved_by": "test fixture",
            }
        path.write_text(json.dumps(plan))
        return path

    def capability_binding(self, plan_path):
        plan = json.loads(Path(plan_path).read_text())
        plan_sha256 = hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        path = self.root / f"{plan_path.stem}-capability-binding.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "planning-capability-binding-v1",
                    "plan_sha256": plan_sha256,
                    "bindings": [
                        {
                            "step_id": leaf["id"],
                            "host": "codex",
                            "executor": "gpt-5.6-terra",
                            "requirements": leaf["capability_requirements"],
                            "evidence": ["test fixture capability inventory"],
                        }
                        for leaf in plan["leaves"]
                    ],
                }
            )
        )
        return path

    def assignments(self, plan_id="plan", count=2):
        path = self.root / f"{plan_id}-assignments.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "id": f"step{number}",
                        "harness": "codex",
                        "model_or_alias": "gpt-5.6-terra",
                        "effort": "medium",
                        "worktree": f".worktrees/{plan_id}-{number}",
                    }
                    for number in range(count)
                ]
            )
        )
        return path

    def init2(
        self,
        plan_id="plan",
        count=2,
        dependent=False,
        max_attempts=2,
        portable_tier="standard",
    ):
        selected_plan = self.plan(plan_id, count, dependent, max_attempts, portable_tier)
        code, result = self.call(
            *self.common(plan_id),
            "init-v4",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(selected_plan),
            "--assignments-file",
            str(self.assignments(plan_id, count)),
            "--capability-binding-file",
            str(self.capability_binding(selected_plan)),
        )
        self.assertEqual(0, code, result)
        return result["run_id"]

    def checkpoint(self, plan_id, run_id):
        return json.loads(
            (
                self.root / "planning-policy/ledgers" / plan_id / run_id / "checkpoint.json"
            ).read_text()
        )

    def start(self, plan_id, run_id, step_id):
        for target in ("ready", "in_progress"):
            arguments = [
                *self.common(plan_id),
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--step-id",
                step_id,
                "--to",
                target,
            ]
            if target == "ready":
                arguments += ["--agent-id", f"agent-{step_id}"]
            code, result = self.call(*arguments)
            self.assertEqual(0, code, result)
        return self.checkpoint(plan_id, run_id)["steps"][step_id]

    def returned(self, step, status="completed"):
        return {
            "schema": "bounded-step-return-v1",
            "step_id": step["id"],
            "attempt_id": step["attempt_id"],
            "agent_id": step["agent_id"],
            "status": status,
            "changed_paths": [],
            "acceptance": {
                "command": "uv run test",
                "exit_code": 0 if status == "completed" else None,
                "summary": status,
            },
            "blockers": []
            if status == "completed"
            else [{"code": "waiting", "summary": "waiting"}],
            "notes": [],
            "unstarted_remainder": [],
            "commit_hash": "",
        }

    def record(self, plan_id, run_id, value):
        path = self.root / f"{plan_id}-{value['step_id']}-return.json"
        path.write_text(json.dumps(value))
        return self.call(
            *self.common(plan_id),
            "record-return",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--return-file",
            str(path),
        )

    def eligible_return(self, step, outcome="failed:acceptance", summary="eligible"):
        status = "failed" if outcome == "failed:acceptance" else "blocked"
        value = self.returned(step, status)
        value["acceptance"]["exit_code"] = 1 if status == "failed" else None
        value["acceptance"]["summary"] = summary
        value["blockers"] = [{"code": outcome, "summary": summary}]
        return value

    def retry(self, plan_id, run_id, step, target_tier, next_agent="next-agent"):
        remediation = {
            "schema": "retry-remediation-v1",
            "step_id": step["id"],
            "prior_attempt_id": step["attempt_id"],
            "prior_return_sha256": step["return_sha256"],
            "diagnosis": "bounded retry diagnosis",
            "remediation_action": "bounded retry action",
            "executor_mode": "fresh",
            "next_agent_id": next_agent,
            "next_harness": "codex",
            "target_portable_tier": target_tier,
        }
        path = self.root / f"{plan_id}-retry-remediation.json"
        path.write_text(json.dumps(remediation))
        return self.call(
            *self.common(plan_id),
            "transition",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--step-id",
            step["id"],
            "--to",
            "ready",
            "--retry",
            "--retry-remediation-file",
            str(path),
        )

    def continue_ready(self, plan_id, run_id, step_id="step0"):
        code, result = self.call(
            *self.common(plan_id),
            "transition",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--step-id",
            step_id,
            "--to",
            "in_progress",
        )
        self.assertEqual(0, code, result)
        return self.checkpoint(plan_id, run_id)["steps"][step_id]

    def test_repeated_result_precedes_exhaustion_and_ceiling(self):
        repeated_run = self.init2("repeated", max_attempts=2, portable_tier="deep")
        first = self.start("repeated", repeated_run, "step0")
        repeated = self.eligible_return(first, summary="same failure")
        self.assertEqual(0, self.record("repeated", repeated_run, repeated)[0])
        failed = self.checkpoint("repeated", repeated_run)["steps"]["step0"]
        self.assertEqual(0, self.retry("repeated", repeated_run, failed, "deep")[0])
        second = self.continue_ready("repeated", repeated_run)
        repeated["attempt_id"] = second["attempt_id"]
        repeated["agent_id"] = second["agent_id"]
        self.assertEqual(0, self.record("repeated", repeated_run, repeated)[0])
        state = self.checkpoint("repeated", repeated_run)["steps"]["step0"]
        self.assertEqual("blocked:no_progress", state["reason"])

    def test_ineligible_outcome_precedes_exhaustion(self):
        ineligible_run = self.init2("ineligible", max_attempts=1)
        step = self.start("ineligible", ineligible_run, "step0")
        arbitrary = self.returned(step, "blocked")
        arbitrary["blockers"] = [{"code": "blocked:missing_input", "summary": "missing"}]
        self.assertEqual(0, self.record("ineligible", ineligible_run, arbitrary)[0])
        state = self.checkpoint("ineligible", ineligible_run)["steps"]["step0"]
        self.assertFalse(state["retry_allowed"])
        self.assertEqual("blocked:missing_input", state["blockers"][0]["code"])

    def test_attempt_exhaustion_precedes_tier_ceiling(self):
        exhausted_run = self.init2("exhausted", max_attempts=2, portable_tier="deep")
        first = self.start("exhausted", exhausted_run, "step0")
        self.assertEqual(
            0,
            self.record("exhausted", exhausted_run, self.eligible_return(first))[0],
        )
        failed = self.checkpoint("exhausted", exhausted_run)["steps"]["step0"]
        self.assertEqual(0, self.retry("exhausted", exhausted_run, failed, "deep")[0])
        second = self.continue_ready("exhausted", exhausted_run)
        self.assertEqual(
            0,
            self.record(
                "exhausted",
                exhausted_run,
                self.eligible_return(second, "blocked:needs_higher_tier", "higher needed"),
            )[0],
        )
        state = self.checkpoint("exhausted", exhausted_run)["steps"]["step0"]
        self.assertEqual("blocked:retry_exhausted", state["reason"])

    def test_deep_retry_that_requires_escalation_reaches_ceiling(self):
        ceiling_run = self.init2("ceiling", max_attempts=3, portable_tier="deep")
        step = self.start("ceiling", ceiling_run, "step0")
        self.assertEqual(
            0,
            self.record(
                "ceiling",
                ceiling_run,
                self.eligible_return(step, "blocked:needs_higher_tier", "higher needed"),
            )[0],
        )
        state = self.checkpoint("ceiling", ceiling_run)["steps"]["step0"]
        self.assertEqual("blocked:retry_ceiling_reached", state["reason"])

    def test_retry_remediation_is_bounded_and_exact(self):
        run_id = self.init2("bounded", max_attempts=3)
        step = self.start("bounded", run_id, "step0")
        self.assertEqual(0, self.record("bounded", run_id, self.eligible_return(step))[0])
        failed = self.checkpoint("bounded", run_id)["steps"]["step0"]
        base = {
            "schema": "retry-remediation-v1",
            "step_id": failed["id"],
            "prior_attempt_id": failed["attempt_id"],
            "prior_return_sha256": failed["return_sha256"],
            "diagnosis": "diagnosis",
            "remediation_action": "action",
            "executor_mode": "fresh",
            "next_agent_id": "next-agent",
            "next_harness": "codex",
            "target_portable_tier": "standard",
        }
        invalid = (
            {**base, "diagnosis": "x" * 481},
            {**base, "unexpected": True},
            {**base, "evidence_path": "evidence/retry.json"},
            {**base, "evidence_path": "../escape", "sha256": "a" * 64},
        )
        path = self.root / "bounded-invalid-remediation.json"
        for value in invalid:
            with self.subTest(value=value):
                path.write_text(json.dumps(value))
                code, _ = self.call(
                    *self.common("bounded"),
                    "transition",
                    "--actor",
                    "parent",
                    "--run-id",
                    run_id,
                    "--step-id",
                    "step0",
                    "--to",
                    "ready",
                    "--retry",
                    "--retry-remediation-file",
                    str(path),
                )
                self.assertEqual(3, code)

    def worktree_result(self, plan_id, step_id, action="integrate"):
        integrated = "b" * 40
        value = {
            "schema": "planning-worktree-result-v1",
            "ok": True,
            "action": action,
            "repo_root": str(self.root),
            "target": "main",
            "branch": "owner",
            "worktree": str(self.root / f".worktrees/{plan_id}-{step_id.removeprefix('step')}"),
            "source_commit": "a" * 40,
            "rebased_commit": integrated,
            "parent_before": "c" * 40,
            "parent_after": integrated,
        }
        if action == "cleanup":
            value["parent_commit"] = integrated
        path = self.root / f"{plan_id}-{step_id}-{action}.json"
        path.write_text(json.dumps(value))
        return path

    def closeout(self, plan_id, run_id, step_id):
        for target, action in (("integrated", "integrate"), ("cleaned", "cleanup")):
            code, result = self.call(
                *self.common(plan_id),
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--step-id",
                step_id,
                "--to",
                target,
                "--worktree-result",
                str(self.worktree_result(plan_id, step_id, action)),
            )
            self.assertEqual(0, code, result)

    def integrate_all(self, plan_id, run_id, count=2):
        for number in range(count):
            step_id = f"step{number}"
            step = self.start(plan_id, run_id, step_id)
            self.assertEqual(0, self.record(plan_id, run_id, self.returned(step))[0])
            self.closeout(plan_id, run_id, step_id)

    def test_close_blocked_reopen_and_completed_require_terminal_invariants(self):
        run_id = self.init2()
        step = self.start("plan", run_id, "step0")
        self.assertEqual(
            3,
            self.call(
                *self.common(),
                "close",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--outcome",
                "blocked",
                "--reason",
                "live work remains",
            )[0],
        )
        self.assertEqual(0, self.record("plan", run_id, self.returned(step, "blocked"))[0])
        code, closed = self.call(
            *self.common(),
            "close",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--outcome",
            "blocked",
            "--reason",
            "waiting for an approved decision",
        )
        self.assertEqual(0, code, closed)
        self.assertEqual("closed", closed["run_status"])
        self.assertEqual("blocked", closed["outcome"])
        self.assertEqual(
            90,
            (ledger.timestamp(closed["purge_after"]) - ledger.timestamp(closed["closed_at"])).days,
        )
        self.assertEqual(
            3,
            self.call(
                *self.common(),
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--step-id",
                "step0",
                "--to",
                "ready",
                "--agent-id",
                "agent-new",
            )[0],
        )
        code, reopened = self.call(
            *self.common(),
            "reopen",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--reason",
            "decision supplied",
        )
        self.assertEqual(0, code, reopened)
        self.assertEqual("active", reopened["run_status"])
        state = self.checkpoint("plan", run_id)
        self.assertIsNone(state["outcome"])
        self.assertEqual(
            3,
            self.call(
                *self.common(),
                "close",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--outcome",
                "completed",
            )[0],
        )

    def test_cleaned_dependency_is_ready_compatible(self):
        run_id = self.init2("dependent", dependent=True)
        first = self.start("dependent", run_id, "step0")
        self.assertEqual(0, self.record("dependent", run_id, self.returned(first))[0])
        self.closeout("dependent", run_id, "step0")
        code, ready = self.call(
            *self.common("dependent"),
            "transition",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--step-id",
            "step1",
            "--to",
            "ready",
            "--agent-id",
            "agent-step1",
        )
        self.assertEqual(0, code, ready)
        self.assertEqual("ready", ready["status"])

    def test_abandoned_refuses_in_progress_and_discards_unstarted_work(self):
        live = self.init2("live")
        self.start("live", live, "step0")
        self.assertEqual(
            3,
            self.call(
                *self.common("live"),
                "close",
                "--actor",
                "parent",
                "--run-id",
                live,
                "--outcome",
                "abandoned",
                "--reason",
                "cancelled",
            )[0],
        )
        run_id = self.init2("abandoned")
        self.assertEqual(
            0,
            self.call(
                *self.common("abandoned"),
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--step-id",
                "step0",
                "--to",
                "ready",
                "--agent-id",
                "agent",
            )[0],
        )
        code, closed = self.call(
            *self.common("abandoned"),
            "close",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--outcome",
            "abandoned",
            "--reason",
            "work no longer needed",
        )
        self.assertEqual(0, code, closed)
        self.assertEqual(
            {"discarded"},
            {step["status"] for step in self.checkpoint("abandoned", run_id)["steps"].values()},
        )
        self.assertEqual(
            7,
            (ledger.timestamp(closed["purge_after"]) - ledger.timestamp(closed["closed_at"])).days,
        )

    def test_gc_retention_boundary_and_active_protection(self):
        with patch.object(ledger, "now", return_value="2026-01-01T00:00:00Z"):
            active = self.init2("active")
            closed = self.init2("done")
            self.integrate_all("done", closed)
            self.assertEqual(
                0,
                self.call(
                    *self.common("done"),
                    "close",
                    "--actor",
                    "parent",
                    "--run-id",
                    closed,
                    "--outcome",
                    "completed",
                )[0],
            )
        with patch.object(ledger, "now", return_value="2026-01-30T23:59:59Z"):
            code, before = self.call("--ledger-root", str(self.root), "gc", "--actor", "parent")
            self.assertEqual(0, code, before)
            self.assertEqual(0, before["counts"]["removed"])
        with patch.object(ledger, "now", return_value="2026-01-31T00:00:00Z"):
            code, dry = self.call("--ledger-root", str(self.root), "gc", "--dry-run")
            self.assertEqual(0, code, dry)
            self.assertEqual(1, dry["counts"]["eligible"])
            self.assertEqual(0, dry["counts"]["removed"])
            code, boundary = self.call("--ledger-root", str(self.root), "gc", "--actor", "parent")
            self.assertEqual(0, code, boundary)
            self.assertEqual(1, boundary["counts"]["removed"])
        base = self.root / "planning-policy/ledgers"
        self.assertTrue((base / "active" / active).is_dir())
        self.assertFalse((base / "done" / closed).exists())

    def test_early_purge_requires_explicit_flag_and_reason(self):
        with patch.object(ledger, "now", return_value="2026-02-01T00:00:00Z"):
            run_id = self.init2("early")
            self.integrate_all("early", run_id)
            self.assertEqual(
                0,
                self.call(
                    *self.common("early"),
                    "close",
                    "--actor",
                    "parent",
                    "--run-id",
                    run_id,
                    "--outcome",
                    "completed",
                )[0],
            )
            base = [*self.common("early"), "purge", "--actor", "parent", "--run-id", run_id]
            self.assertEqual(3, self.call(*base)[0])
            self.assertEqual(3, self.call(*base, "--before-retention")[0])
            code, purged = self.call(
                *base, "--before-retention", "--reason", "explicit test cleanup"
            )
        self.assertEqual(0, code, purged)
        self.assertTrue(purged["early"])
        self.assertFalse((self.root / "planning-policy/ledgers/early" / run_id).exists())

    def v1_steps(self, count):
        return json.dumps(
            [
                {
                    "id": f"step{number}",
                    "harness": "codex",
                    "tier": "standard",
                    "model_or_alias": "gpt-5.6-terra",
                    "effort": "medium",
                    "worktree": f".worktrees/{number}",
                }
                for number in range(count)
            ]
        )

    def complete_v1(self, plan_id, count):
        self.assertEqual(
            0,
            self.call(
                *self.common(plan_id),
                "init",
                "--actor",
                "parent",
                "--approved",
                "--steps-json",
                self.v1_steps(count),
            )[0],
        )
        for number in range(count):
            for target in ("ready", "in_progress", "completed", "integrated"):
                arguments = [
                    *self.common(plan_id),
                    "transition",
                    "--actor",
                    "parent",
                    "--step-id",
                    f"step{number}",
                    "--to",
                    target,
                ]
                if target == "integrated":
                    arguments += ["--summary", "integrated"]
                self.assertEqual(0, self.call(*arguments)[0])

    def test_current_completed_v1_shapes_list_without_byte_mutation(self):
        shapes = {
            "planning-policy-lean-remediation-20260809": 5,
            "planning-policy-medium-majority-20260809": 7,
            "software-design-fragility-20260809": 3,
        }
        with patch.object(ledger, "now", return_value="2026-08-09T16:00:00Z"):
            for plan_id, count in shapes.items():
                self.complete_v1(plan_id, count)
            base = self.root / "planning-policy/ledgers"
            before = {
                plan_id: (
                    (base / plan_id / "checkpoint.json").read_bytes(),
                    (base / plan_id / "events.jsonl").read_bytes(),
                )
                for plan_id in shapes
            }
            code, listed = self.call("--ledger-root", str(self.root), "list")
            self.assertEqual(0, code, listed)
            self.assertEqual(set(shapes), {run["plan_id"] for run in listed["runs"]})
            self.assertEqual({"completed"}, {run["outcome"] for run in listed["runs"]})
            self.call("--ledger-root", str(self.root), "gc", "--dry-run")
        after = {
            plan_id: (
                (base / plan_id / "checkpoint.json").read_bytes(),
                (base / plan_id / "events.jsonl").read_bytes(),
            )
            for plan_id in shapes
        }
        self.assertEqual(before, after)

    def test_legacy_short_retention_and_ambiguous_terminal_state_are_conservative(self):
        with patch.object(ledger, "now", return_value="2026-03-01T00:00:00Z"):
            self.assertEqual(
                0,
                self.call(
                    *self.common("discarded"),
                    "init",
                    "--actor",
                    "parent",
                    "--approved",
                    "--steps-json",
                    self.v1_steps(2),
                )[0],
            )
            for number in range(2):
                self.assertEqual(
                    0,
                    self.call(
                        *self.common("discarded"),
                        "transition",
                        "--actor",
                        "parent",
                        "--step-id",
                        f"step{number}",
                        "--to",
                        "discarded",
                    )[0],
                )
            self.assertEqual(
                0,
                self.call(
                    *self.common("ambiguous"),
                    "init",
                    "--actor",
                    "parent",
                    "--approved",
                    "--steps-json",
                    self.v1_steps(2),
                )[0],
            )
            for target in ("ready", "in_progress", "completed", "integrated"):
                arguments = [
                    *self.common("ambiguous"),
                    "transition",
                    "--actor",
                    "parent",
                    "--step-id",
                    "step0",
                    "--to",
                    target,
                ]
                if target == "integrated":
                    arguments += ["--summary", "integrated"]
                self.assertEqual(0, self.call(*arguments)[0])
            self.assertEqual(
                0,
                self.call(
                    *self.common("ambiguous"),
                    "transition",
                    "--actor",
                    "parent",
                    "--step-id",
                    "step1",
                    "--to",
                    "discarded",
                )[0],
            )
        with patch.object(ledger, "now", return_value="2026-03-08T00:00:00Z"):
            code, report = self.call("--ledger-root", str(self.root), "gc", "--actor", "parent")
        self.assertEqual(0, code, report)
        self.assertEqual(1, report["counts"]["removed"])
        self.assertTrue(any(item["code"] == "ambiguous_legacy" for item in report["invalid"]))
        self.assertTrue((self.root / "planning-policy/ledgers/ambiguous").is_dir())

    def test_invalid_shapes_are_bounded_reported_and_preserved(self):
        base = self.root / "planning-policy/ledgers"
        unknown = base / "unknown"
        unknown.mkdir(parents=True)
        (unknown / "checkpoint.json").write_text('{"schema_version":9}')
        (unknown / "events.jsonl").write_text("")
        malformed = base / "malformed"
        malformed.mkdir()
        (malformed / "checkpoint.json").write_text("{")
        (malformed / "events.jsonl").write_text("")
        unexpected = base / "unexpected"
        unexpected.mkdir()
        (unexpected / "note.txt").write_text("preserve")
        (base / "linked").symlink_to(unexpected, target_is_directory=True)
        code, listed = self.call("--ledger-root", str(self.root), "list")
        self.assertEqual(0, code, listed)
        self.assertEqual(4, listed["counts"]["invalid"])
        self.assertEqual(
            {"unknown_schema", "malformed_checkpoint", "unexpected_contents", "symlink"},
            {item["code"] for item in listed["invalid"]},
        )
        self.assertLessEqual(listed["summary_proxy_tokens"], 1200)
        linked_plan = self.plan("linked")
        code, _ = self.call(
            *self.common("linked"),
            "init-v4",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(linked_plan),
            "--assignments-file",
            str(self.assignments("linked")),
            "--capability-binding-file",
            str(self.capability_binding(linked_plan)),
        )
        self.assertEqual(3, code)
        self.assertEqual("preserve", (unexpected / "note.txt").read_text())
        code, garbage = self.call("--ledger-root", str(self.root), "gc", "--actor", "parent")
        self.assertEqual(0, code, garbage)
        self.assertEqual(4, garbage["counts"]["invalid"])
        self.assertTrue(
            all(
                path.exists() or path.is_symlink()
                for path in (unknown, malformed, unexpected, base / "linked")
            )
        )


MEMBER_COMMITS = {"b0": "1" * 40, "b1": "2" * 40, "b2": "3" * 40}
BATCH_TIP = MEMBER_COMMITS["b2"]
BATCH_INTEGRATED = "9" * 40


class PlanningLedgerBatchTest(unittest.TestCase):
    """A batch is one dispatch in one worktree that integrates its tip once."""

    members = ("b0", "b1", "b2")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def common(self, plan_id):
        return ["--ledger-root", str(self.root), "--plan-id", plan_id]

    def call(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = ledger.main(arguments)
        return code, json.loads(stream.getvalue())

    def leaf(self, sid, dependencies, batched, max_attempts):
        value = {
            "id": sid,
            "dependencies": dependencies,
            "task": "task",
            "boundary": "boundary",
            "read_set": ["src"],
            "write_set": ["src"],
            "settled_decisions": "settled",
            "size": "small",
            "portable_tier": "standard",
            "worktree_owner": "batch/owner" if batched else f"solo/{sid}",
            "acceptance_command": "uv run test",
            "return_contract": "bounded-step-return-v1",
            "stop_conditions": ["missing_load_bearing_information"],
            "work_unit_id": sid,
            "max_attempts": max_attempts,
            "capability_requirements": {"baseline": "plan-step-base-v1", "additional": []},
        }
        if batched:
            value["batch"] = "edits"
        return value

    def plan(self, plan_id, ids, batched, max_attempts):
        leaves = [
            self.leaf(sid, [ids[index - 1]] if index else [], batched, max_attempts)
            for index, sid in enumerate(ids)
        ]
        path = self.root / f"{plan_id}-plan.json"
        path.write_text(
            json.dumps(
                {
                    "contract_version": 4,
                    "objective": "objective",
                    "scope_summary": "scope",
                    "approved_decisions": ["settled"],
                    "leaves": leaves,
                    "work_units": [{"id": sid, "original_size": "small"} for sid in ids],
                }
            )
        )
        return path

    def capability_binding(self, plan_path):
        plan = json.loads(Path(plan_path).read_text())
        path = self.root / f"{plan_path.stem}-binding.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "planning-capability-binding-v1",
                    "plan_sha256": hashlib.sha256(
                        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
                    ).hexdigest(),
                    "bindings": [
                        {
                            "step_id": leaf["id"],
                            "host": "codex",
                            "executor": "gpt-5.6-terra",
                            "requirements": leaf["capability_requirements"],
                            "evidence": ["test fixture capability inventory"],
                        }
                        for leaf in plan["leaves"]
                    ],
                }
            )
        )
        return path

    def assignments(self, plan_id, ids, batched):
        path = self.root / f"{plan_id}-assignments.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "id": sid,
                        "harness": "codex",
                        "model_or_alias": "gpt-5.6-terra",
                        "effort": "medium",
                        "worktree": ".worktrees/batch" if batched else f".worktrees/{sid}",
                    }
                    for sid in ids
                ]
            )
        )
        return path

    def init(self, plan_id, ids, batched=True, max_attempts=2):
        selected = self.plan(plan_id, ids, batched, max_attempts)
        code, result = self.call(
            *self.common(plan_id),
            "init-v4",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(selected),
            "--assignments-file",
            str(self.assignments(plan_id, ids, batched)),
            "--capability-binding-file",
            str(self.capability_binding(selected)),
        )
        self.assertEqual(0, code, result)
        return result["run_id"]

    def checkpoint(self, plan_id, run_id):
        return json.loads(
            (
                self.root / "planning-policy/ledgers" / plan_id / run_id / "checkpoint.json"
            ).read_text()
        )

    def transition(self, plan_id, run_id, sid, target, *extra):
        return self.call(
            *self.common(plan_id),
            "transition",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--step-id",
            sid,
            "--to",
            target,
            *extra,
        )

    def start(self, plan_id, run_id, sid, agent="batch-worker"):
        code, result = self.transition(plan_id, run_id, sid, "ready", "--agent-id", agent)
        self.assertEqual(0, code, result)
        code, result = self.transition(plan_id, run_id, sid, "in_progress")
        self.assertEqual(0, code, result)
        return self.checkpoint(plan_id, run_id)["steps"][sid]

    def returned(self, step, status="completed", blocker=""):
        sid = step["id"]
        return {
            "schema": "bounded-step-return-v1",
            "step_id": sid,
            "attempt_id": step["attempt_id"],
            "agent_id": step["agent_id"],
            "status": status,
            "changed_paths": [f"src/{sid}.py"],
            "acceptance": {
                "command": "uv run test",
                "exit_code": 0 if status == "completed" else 1,
                "summary": blocker or status,
            },
            "blockers": [] if status == "completed" else [{"code": blocker, "summary": blocker}],
            "notes": [],
            "unstarted_remainder": [],
            "commit_hash": MEMBER_COMMITS[sid],
        }

    def record(self, plan_id, run_id, value):
        path = self.root / f"{plan_id}-{value['step_id']}-return.json"
        path.write_text(json.dumps(value))
        return self.call(
            *self.common(plan_id),
            "record-return",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--return-file",
            str(path),
        )

    def complete(self, plan_id, run_id, sid):
        step = self.checkpoint(plan_id, run_id)["steps"][sid]
        code, result = self.record(plan_id, run_id, self.returned(step))
        self.assertEqual(0, code, result)
        return result

    def retry(self, plan_id, run_id, step):
        path = self.root / f"{plan_id}-remediation.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "retry-remediation-v1",
                    "step_id": step["id"],
                    "prior_attempt_id": step["attempt_id"],
                    "prior_return_sha256": step["return_sha256"],
                    "diagnosis": "acceptance failed inside the shared batch worktree",
                    "remediation_action": "rerun the member alone in the same worktree",
                    "executor_mode": "fresh",
                    "next_agent_id": "remediation-worker",
                    "next_harness": "codex",
                    "target_portable_tier": "standard",
                }
            )
        )
        return self.transition(
            plan_id, run_id, step["id"], "ready", "--retry", "--retry-remediation-file", str(path)
        )

    def artifact(self, plan_id, action="integrate", commits=None, source=BATCH_TIP):
        value = {
            "schema": "planning-worktree-result-v1",
            "ok": True,
            "action": action,
            "repo_root": str(self.root),
            "target": "main",
            "branch": "batch/owner",
            "worktree": str(self.root / ".worktrees/batch"),
            "source_commit": source,
            "rebased_commit": BATCH_INTEGRATED,
            "parent_before": "c" * 40,
            "parent_after": BATCH_INTEGRATED,
            "rebased_tree_changed": False,
        }
        if commits:
            value["batch_source_commits"] = commits
        if action == "cleanup":
            value["parent_commit"] = BATCH_INTEGRATED
        path = self.root / f"{plan_id}-{action}.json"
        path.write_text(json.dumps(value))
        return str(path)

    def close_out_batch(self, plan_id, run_id):
        """One integrate artifact and one cleanup artifact serve every member."""
        integrate = self.artifact(plan_id, commits=MEMBER_COMMITS)
        for sid in self.members:
            code, result = self.transition(
                plan_id, run_id, sid, "integrated", "--worktree-result", integrate
            )
            self.assertEqual(0, code, result)
        cleanup = self.artifact(plan_id, action="cleanup", commits=MEMBER_COMMITS)
        for sid in self.members:
            code, result = self.transition(
                plan_id, run_id, sid, "cleaned", "--worktree-result", cleanup
            )
            self.assertEqual(0, code, result)

    def test_a_batch_dispatches_in_order_and_integrates_its_shared_tip_once(self):
        run = self.init("batch", self.members)
        steps = self.checkpoint("batch", run)["steps"]
        self.assertEqual(
            {".worktrees/batch"}, {step["assignment"]["worktree"] for step in steps.values()}
        )
        for sid in self.members:
            self.start("batch", run, sid)
        self.assertEqual(
            {"in_progress"},
            {self.checkpoint("batch", run)["steps"][sid]["status"] for sid in self.members},
        )
        for sid in self.members[:-1]:
            self.assertEqual("await_return", self.complete("batch", run, sid)["next"]["category"])
        self.assertIn("--to integrated", self.complete("batch", run, "b2")["next"]["command"])

        self.close_out_batch("batch", run)
        state = self.checkpoint("batch", run)["steps"]
        self.assertEqual({"cleaned"}, {step["status"] for step in state.values()})
        self.assertEqual(
            {BATCH_INTEGRATED}, {step["integrated_commit"] for step in state.values()}
        )
        self.assertEqual(1, len({step["integration_result_sha256"] for step in state.values()}))
        self.assertEqual(1, len({step["cleanup_result_sha256"] for step in state.values()}))
        code, validated = self.call(
            *self.common("batch"), "validate", "--run-id", run, "--closeout"
        )
        self.assertEqual(0, code, validated)

    def test_a_stopped_member_unwinds_its_followers_before_one_shared_integrate(self):
        run = self.init("unwind", self.members)
        for sid in self.members:
            self.start("unwind", run, sid)
        self.complete("unwind", run, "b0")
        running = self.checkpoint("unwind", run)["steps"]["b1"]
        code, result = self.record(
            "unwind", run, self.returned(running, "failed", "failed:acceptance")
        )
        self.assertEqual(0, code, result)

        code, unwound = self.transition("unwind", run, "b2", "pending")
        self.assertEqual(0, code, unwound)
        follower = self.checkpoint("unwind", run)["steps"]["b2"]
        self.assertEqual("pending", follower["status"])
        self.assertEqual(0, follower["attempt_count"])
        self.assertEqual("", follower["agent_id"])
        self.assertEqual("", follower["attempt_id"])
        self.assertEqual("", follower["current_assignment"]["agent_id"])

        stopped = self.checkpoint("unwind", run)["steps"]["b1"]
        code, retried = self.retry("unwind", run, stopped)
        self.assertEqual(0, code, retried)
        code, result = self.transition("unwind", run, "b1", "in_progress")
        self.assertEqual(0, code, result)
        self.complete("unwind", run, "b1")
        remediated = self.checkpoint("unwind", run)["steps"]["b1"]
        self.assertEqual("standard", remediated["current_tier"])
        self.assertEqual(".worktrees/batch", remediated["assignment"]["worktree"])

        self.start("unwind", run, "b2", agent="redispatched-worker")
        self.complete("unwind", run, "b2")
        self.close_out_batch("unwind", run)
        code, validated = self.call(
            *self.common("unwind"), "validate", "--run-id", run, "--closeout"
        )
        self.assertEqual(0, code, validated)

    def test_pending_unwind_is_refused_outside_a_stopped_batch(self):
        early = self.init("early", self.members)
        code, result = self.transition("early", early, "b0", "ready", "--agent-id", "worker")
        self.assertEqual(0, code, result)
        self.assertEqual(3, self.transition("early", early, "b0", "pending")[0])

        solo = self.init("solo", ("b0", "b1"), batched=False)
        self.start("solo", solo, "b0")
        self.assertEqual(3, self.transition("solo", solo, "b0", "pending")[0])

        running = self.init("running", self.members)
        self.start("running", running, "b0")
        self.start("running", running, "b1")
        self.assertEqual(3, self.transition("running", running, "b1", "pending")[0])
        self.assertEqual(
            "in_progress", self.checkpoint("running", running)["steps"]["b1"]["status"]
        )


if __name__ == "__main__":
    unittest.main()
