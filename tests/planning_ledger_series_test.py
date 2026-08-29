import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).parents[1]
    / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py"
)
SPEC = importlib.util.spec_from_file_location("planning_ledger_series", SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(ledger)


class PlanningLedgerSeriesTest(unittest.TestCase):
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

    def plan(self, plan_id="plan", count=1, series=None):
        path = self.root / f"{plan_id}-plan.json"
        leaves = []
        for number in range(count):
            step_id = f"step{number}"
            leaves.append(
                {
                    "id": step_id,
                    "dependencies": [],
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
                    "capability_requirements": {
                        "baseline": "plan-step-base-v1",
                        "additional": [],
                    },
                }
            )
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
        if series is not None:
            plan["series"] = series
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

    def assignments(self, plan_id="plan", count=1):
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

    def init4(self, plan_id="plan", count=1, series=None):
        selected_plan = self.plan(plan_id, count, series)
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

    def checkpoint_path(self, plan_id, run_id):
        return self.root / "planning-policy/ledgers" / plan_id / run_id / "checkpoint.json"

    def checkpoint(self, plan_id, run_id):
        return json.loads(self.checkpoint_path(plan_id, run_id).read_text())

    def run_dir(self, plan_id, run_id):
        return self.root / "planning-policy/ledgers" / plan_id / run_id

    def default_series(self):
        return {
            "series_id": "plan-series",
            "slice": 1,
            "final": False,
            "end_verification_commands": ["uv run python -m unittest tests.example"],
        }

    def handoff(self, plan_id, run_id, series_id="plan-series", slice_number=1, **overrides):
        value = {
            "schema": "planning-series-handoff-v1",
            "plan_id": plan_id,
            "run_id": run_id,
            "series_id": series_id,
            "slice": slice_number,
            "landed": ["shipped feature A"],
            "decisions": ["chose approach X"],
            "assumptions_to_revalidate": ["upstream API stays stable"],
            "remaining_scope": ["slice 2 continues cleanup"],
        }
        value.update(overrides)
        return value

    def stamp(self, plan_id, run_id, handoff_value):
        directory = self.run_dir(plan_id, run_id)
        artifact_path = directory / "series-handoff.json"
        artifact_path.write_text(json.dumps(handoff_value))
        checkpoint = self.checkpoint(plan_id, run_id)
        checkpoint["series_handoff_path"] = "series-handoff.json"
        checkpoint["series_handoff_sha256"] = ledger.digest(handoff_value)
        checkpoint["event_sequence"] += 1
        checkpoint["updated_at"] = ledger.now()
        (directory / "checkpoint.json").write_text(
            json.dumps(checkpoint, sort_keys=True, separators=(",", ":")) + "\n"
        )

    def show(self, plan_id, run_id):
        return self.call(*self.common(plan_id), "show", "--run-id", run_id)

    # -- plumbing coverage --------------------------------------------------

    def test_series_handoff_round_trips_through_show(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("plan", run_id))
        code, result = self.show("plan", run_id)
        self.assertEqual(0, code, result)

    def test_plain_non_series_run_has_no_series_keys_in_checkpoint(self):
        run_id = self.init4(series=None)
        checkpoint = self.checkpoint("plan", run_id)
        self.assertNotIn("series_handoff_path", checkpoint)
        self.assertNotIn("series_handoff_sha256", checkpoint)
        code, result = self.show("plan", run_id)
        self.assertEqual(0, code, result)

    def test_rejects_artifact_edited_after_stamping(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("plan", run_id))
        artifact = self.run_dir("plan", run_id) / "series-handoff.json"
        tampered = self.handoff("plan", run_id, landed=["tampered"])
        artifact.write_text(json.dumps(tampered))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_stamp_without_file(self):
        run_id = self.init4(series=self.default_series())
        directory = self.run_dir("plan", run_id)
        checkpoint = self.checkpoint("plan", run_id)
        checkpoint["series_handoff_path"] = "series-handoff.json"
        checkpoint["series_handoff_sha256"] = "a" * 64
        (directory / "checkpoint.json").write_text(
            json.dumps(checkpoint, sort_keys=True, separators=(",", ":")) + "\n"
        )
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_file_without_stamp(self):
        run_id = self.init4(series=self.default_series())
        directory = self.run_dir("plan", run_id)
        (directory / "series-handoff.json").write_text(
            json.dumps(self.handoff("plan", run_id))
        )
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_artifact_on_non_series_run(self):
        run_id = self.init4(series=None)
        self.stamp("plan", run_id, self.handoff("plan", run_id))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_identity_mismatch_slice(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("plan", run_id, slice_number=2))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_identity_mismatch_series_id(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("plan", run_id, series_id="other-series"))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_identity_mismatch_run_id(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("plan", "11111111-1111-4111-8111-111111111111"))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_identity_mismatch_plan_id(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("other-plan", run_id))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_oversized_artifact(self):
        run_id = self.init4(series=self.default_series())
        oversized = self.handoff(
            "plan",
            run_id,
            landed=["x" * 480] * 16,
            decisions=["x" * 480] * 16,
            assumptions_to_revalidate=["x" * 480] * 16,
            remaining_scope=["x" * 480] * 16,
        )
        self.assertGreater(len(ledger.canon(oversized)), ledger.MAX_SERIES_HANDOFF)
        self.stamp("plan", run_id, oversized)
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_malformed_schema_unknown_key(self):
        run_id = self.init4(series=self.default_series())
        malformed = self.handoff("plan", run_id)
        malformed["extra"] = "nope"
        self.stamp("plan", run_id, malformed)
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_malformed_schema_overlong_string(self):
        run_id = self.init4(series=self.default_series())
        malformed = self.handoff("plan", run_id, landed=["x" * 481])
        self.stamp("plan", run_id, malformed)
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_malformed_schema_over_sixteen_entries(self):
        run_id = self.init4(series=self.default_series())
        malformed = self.handoff("plan", run_id, decisions=["entry"] * 17)
        self.stamp("plan", run_id, malformed)
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)


if __name__ == "__main__":
    unittest.main()
