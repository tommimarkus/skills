import contextlib
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

    def plan(self, plan_id="plan", count=2, dependent=False):
        path = self.root / f"{plan_id}-plan.json"
        leaves = []
        for number in range(count):
            step_id = f"step{number}"
            leaves.append(
                {
                    "id": step_id,
                    "dependencies": ["step0"] if dependent and number == 1 else [],
                    "task": "task",
                    "boundary": "boundary",
                    "read_set": ["src"],
                    "write_set": ["src"],
                    "settled_decisions": "settled",
                    "size": "small",
                    "portable_tier": "standard",
                    "worktree_owner": "owner",
                    "acceptance_command": "uv run test",
                    "return_contract": "bounded-step-return-v1",
                    "stop_conditions": ["missing_load_bearing_information"],
                    "work_unit_id": step_id,
                    "max_attempts": 2,
                }
            )
        path.write_text(
            json.dumps(
                {
                    "contract_version": 2,
                    "objective": "objective",
                    "scope_summary": "scope",
                    "approved_decisions": ["settled"],
                    "leaves": leaves,
                    "work_units": [
                        {"id": f"step{number}", "original_size": "small"} for number in range(count)
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

    def init2(self, plan_id="plan", count=2, dependent=False):
        code, result = self.call(
            *self.common(plan_id),
            "init-v2",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(self.plan(plan_id, count, dependent)),
            "--assignments-file",
            str(self.assignments(plan_id, count)),
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
        code, _ = self.call(
            *self.common("linked"),
            "init-v2",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(self.plan("linked")),
            "--assignments-file",
            str(self.assignments("linked")),
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


if __name__ == "__main__":
    unittest.main()
