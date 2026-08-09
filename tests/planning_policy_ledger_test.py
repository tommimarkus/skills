import contextlib, importlib.util, io, json, tempfile, unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).parents[1]
    / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py"
)
SPEC = importlib.util.spec_from_file_location("ledger", SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(ledger)


class PlanningLedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.common = ["--ledger-root", str(self.root), "--plan-id", "plan"]
        self.assignment = {
            "harness": "codex",
            "tier": "standard",
            "model_or_alias": "inherit",
            "effort": "inherit",
            "worktree": ".worktrees/a",
        }

    def tearDown(self):
        self.temp.cleanup()

    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = ledger.main(args)
        return code, json.loads(stream.getvalue())

    def v1(self):
        return json.dumps(
            [
                {"id": "build", **self.assignment},
                {"id": "verify", "dependencies": ["build"], **self.assignment},
            ]
        )

    def plan(self, count=2, max_attempts=2):
        leaves = []
        units = []
        for n in range(count):
            sid = f"step{n}"
            leaves.append(
                {
                    "id": sid,
                    "dependencies": [],
                    "task": "task",
                    "boundary": "boundary",
                    "read_set": ["src"],
                    "write_set": ["src"],
                    "settled_decisions": "decision",
                    "size": "small",
                    "portable_tier": "standard",
                    "worktree_owner": "owner",
                    "acceptance_command": "uv run test",
                    "return_contract": "bounded-step-return-v1",
                    "stop_conditions": ["missing_load_bearing_information"],
                    "work_unit_id": sid,
                    "max_attempts": max_attempts,
                }
            )
            units.append({"id": sid, "original_size": "small"})
        path = self.root / "plan.json"
        path.write_text(
            json.dumps(
                {
                    "contract_version": 2,
                    "objective": "objective",
                    "scope_summary": "scope",
                    "approved_decisions": ["decision"],
                    "leaves": leaves,
                    "work_units": units,
                }
            )
        )
        return path

    def assignments(self, count=2):
        path = self.root / "assign.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "id": f"step{n}",
                        "harness": "codex",
                        "model_or_alias": "inherit",
                        "effort": "medium",
                        "worktree": f".worktrees/{n}",
                    }
                    for n in range(count)
                ]
            )
        )
        return path

    def init2(self, count=2, max_attempts=2):
        code, data = self.call(
            *self.common,
            "init-v2",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(self.plan(count, max_attempts)),
            "--assignments-file",
            str(self.assignments(count)),
        )
        self.assertEqual(0, code)
        return data["run_id"]

    def checkpoint(self, run):
        return json.loads(
            (self.root / "planning-policy/ledgers/plan" / run / "checkpoint.json").read_text()
        )

    def start(self, run, sid="step0", agent="agent"):
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                sid,
                "--to",
                "ready",
                "--agent-id",
                agent,
            )[0],
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                sid,
                "--to",
                "in_progress",
            )[0],
        )
        return self.checkpoint(run)["steps"][sid]

    def blocker(self, code="blocked_reason", summary="reason"):
        return {"code": code, "summary": summary}

    def returned(
        self, step, status="completed", changed=None, code=0, blockers=None, remainder=None
    ):
        return {
            "schema": "bounded-step-return-v1",
            "step_id": step["id"],
            "attempt_id": step["attempt_id"],
            "agent_id": step["agent_id"],
            "status": status,
            "changed_paths": changed or [],
            "acceptance": {"command": "uv run test", "exit_code": code, "summary": "summary"},
            "blockers": blockers or [],
            "notes": [{"type": "finding", "message": "ok"}],
            "unstarted_remainder": remainder or [],
            "commit_hash": "a" * 40 if status == "completed" and changed else "",
        }

    def record(self, run, value):
        path = self.root / "return.json"
        path.write_text(json.dumps(value))
        return self.call(
            *self.common,
            "record-return",
            "--actor",
            "parent",
            "--run-id",
            run,
            "--return-file",
            str(path),
        )

    def test_v1_lifecycle_byte_shape_and_disclosure(self):
        self.assertEqual(
            0,
            self.call(
                *self.common, "init", "--actor", "parent", "--approved", "--steps-json", self.v1()
            )[0],
        )
        original = json.loads(
            (self.root / "planning-policy/ledgers/plan/checkpoint.json").read_text()
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--step-id",
                "build",
                "--to",
                "ready",
            )[0],
        )
        code, shown = self.call(*self.common, "show")
        self.assertEqual(0, code)
        self.assertEqual(1, shown["legacy_schema"])
        self.assertTrue(shown["rehydration_incomplete"])
        self.assertEqual("legacy_unbounded", shown["retry_policy"])
        current = json.loads(
            (self.root / "planning-policy/ledgers/plan/checkpoint.json").read_text()
        )
        self.assertEqual(set(original), set(current))
        self.assertEqual(1, current["schema_version"])

    def test_twenty_isolated_generated_uuid_runs_and_assignment_join(self):
        runs = [self.init2() for _ in range(20)]
        self.assertEqual(20, len(set(runs)))
        base = self.root / "planning-policy/ledgers/plan"
        self.assertEqual(20, len([p for p in base.iterdir() if p.is_dir()]))
        self.assertTrue(all(len(x) == 36 for x in runs))
        bad = self.assignments()
        bad.write_text("[]")
        self.assertEqual(
            3,
            self.call(
                *self.common,
                "init-v2",
                "--actor",
                "parent",
                "--approved",
                "--plan-file",
                str(self.plan()),
                "--assignments-file",
                str(bad),
            )[0],
        )

    def test_run_isolation_independent_steps_and_identity(self):
        one, two = self.init2(), self.init2()
        first = self.start(one, "step0", "agent-one")
        self.start(one, "step1", "agent-two")
        self.assertEqual("pending", self.checkpoint(two)["steps"]["step0"]["status"])
        self.assertEqual(
            3,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                two,
                "--step-id",
                "missing",
                "--to",
                "ready",
                "--agent-id",
                "x",
            )[0],
        )
        stale = self.returned(first)
        stale["agent_id"] = "other"
        self.assertEqual(3, self.record(one, stale)[0])

    def test_return_limits_paths_copy_completion_and_tamper(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, changed=["src/file.py"])
        code, result = self.record(run, value)
        self.assertEqual(0, code)
        self.assertEqual("completed", result["status"])
        self.assertTrue(
            (
                self.root
                / "planning-policy/ledgers/plan"
                / run
                / "returns"
                / "step0"
                / f"{step['attempt_id']}.json"
            ).is_file()
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                "step0",
                "--to",
                "integrated",
            )[0],
        )
        plan = self.root / "planning-policy/ledgers/plan" / run / "plan.json"
        plan.write_text("{}")
        self.assertEqual(3, self.call(*self.common, "show", "--run-id", run)[0])

    def test_retry_fingerprints_exhaustion_and_oversized(self):
        run = self.init2(max_attempts=2)
        step = self.start(run)
        failed = self.returned(step, "failed", code=1, blockers=[self.blocker("failed_acceptance")])
        self.assertEqual(0, self.record(run, failed)[0])
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                "step0",
                "--to",
                "ready",
                "--agent-id",
                "again",
                "--retry",
                "--summary",
                "changed evidence",
            )[0],
        )
        step = self.start_after_ready(run)
        self.assertEqual(
            0,
            self.record(
                run,
                self.returned(step, "failed", code=1, blockers=[self.blocker("failed_acceptance")]),
            )[0],
        )
        self.assertEqual("blocked", self.checkpoint(run)["steps"]["step0"]["status"])
        run = self.init2()
        step = self.start(run)
        huge = self.returned(step, "blocked", blockers=[self.blocker("x")])
        huge["notes"] = [{"type": "verification_limit", "message": "x" * 9000}]
        self.assertEqual(3, self.record(run, huge)[0])
        self.assertEqual("oversized", self.checkpoint(run)["steps"]["step0"]["status"])

    def start_after_ready(self, run):
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                "step0",
                "--to",
                "in_progress",
            )[0],
        )
        return self.checkpoint(run)["steps"]["step0"]

    def test_summary_truncation_and_step_detail(self):
        run = self.init2(count=40)
        code, shown = self.call(*self.common, "show", "--run-id", run)
        self.assertEqual(0, code)
        self.assertLessEqual(shown["summary_proxy_tokens"], 1200)
        self.assertIn("omitted_count", shown)
        code, detail = self.call(*self.common, "show", "--run-id", run, "--step-id", "step0")
        self.assertEqual(0, code)
        self.assertEqual("step0", detail["step"]["id"])

    def test_repeated_noncompleted_fingerprint_stops_progress(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "blocked", blockers=[self.blocker("missing_input")])
        self.assertEqual(0, self.record(run, value)[0])
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                "step0",
                "--to",
                "ready",
                "--agent-id",
                "second",
                "--retry",
                "--summary",
                "evidence",
            )[0],
        )
        step = self.start_after_ready(run)
        value["attempt_id"] = step["attempt_id"]
        value["agent_id"] = step["agent_id"]
        self.assertEqual(0, self.record(run, value)[0])
        state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual("blocked", state["status"])
        self.assertEqual("blocked:no_progress", state["reason"])
        self.assertFalse(state["retry_allowed"])

    def test_reassignment_increments_once_and_requires_retry_reason(self):
        run = self.init2()
        step = self.start(run)
        self.assertEqual(
            0,
            self.record(
                run,
                self.returned(step, "failed", code=1, blockers=[self.blocker("failed_acceptance")]),
            )[0],
        )
        self.assertEqual(
            3,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                "step0",
                "--to",
                "ready",
                "--agent-id",
                "second",
            )[0],
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                "step0",
                "--to",
                "ready",
                "--agent-id",
                "second",
                "--retry",
                "--summary",
                "new evidence",
            )[0],
        )
        state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(2, state["attempt_count"])
        self.assertNotEqual(step["attempt_id"], state["attempt_id"])

    def test_return_status_and_field_invariants(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "completed", changed=["src/a"])
        value["commit_hash"] = ""
        self.assertEqual(3, self.record(run, value)[0])
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "failed", code=None, blockers=[self.blocker()])
        self.assertEqual(0, self.record(run, value)[0])
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "blocked", blockers=[])
        self.assertEqual(3, self.record(run, value)[0])
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, changed=["other/file"])
        self.assertEqual(3, self.record(run, value)[0])
        self.assertEqual("oversized", self.checkpoint(run)["steps"]["step0"]["status"])

    def test_return_evidence_digest_notes_and_bounded_arrays(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step)
        value["acceptance"]["evidence_path"] = "evidence/x.json"
        self.assertEqual(3, self.record(run, value)[0])
        value = self.returned(step)
        value["notes"] = [{"type": "not-enum", "message": "x"}]
        self.assertEqual(3, self.record(run, value)[0])
        value = self.returned(step)
        value["changed_paths"] = [f"src/{n}" for n in range(33)]
        self.assertEqual(3, self.record(run, value)[0])

    def test_valid_oversized_and_blocker_evidence_contract(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(
            step, "oversized", blockers=[self.blocker("scope", "outside")], remainder=["step1"]
        )
        self.assertEqual(0, self.record(run, value)[0])
        self.assertEqual("oversized", self.checkpoint(run)["steps"]["step0"]["status"])
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "oversized", blockers=[self.blocker()], remainder=[])
        self.assertEqual(3, self.record(run, value)[0])
        run = self.init2()
        step = self.start(run)
        value = self.returned(
            step,
            "blocked",
            blockers=[{"code": "x", "summary": "y", "evidence_path": "../bad", "sha256": "a" * 64}],
        )
        self.assertEqual(3, self.record(run, value)[0])

    def test_completed_without_changes_does_not_need_commit(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "completed")
        self.assertEqual("", value["commit_hash"])
        self.assertEqual(0, self.record(run, value)[0])

    def test_validate_unknown_run_and_cross_run_return(self):
        one, two = self.init2(), self.init2()
        step = self.start(one)
        self.assertEqual(
            3,
            self.call(*self.common, "validate", "--run-id", "00000000-0000-4000-8000-000000000000")[
                0
            ],
        )
        self.assertEqual(3, self.record(two, self.returned(step))[0])


if __name__ == "__main__":
    unittest.main()
