"""Worker handoff packets are self-validating, bounded, and read-only."""

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

from tests.planning_policy_v4_capability_test import binding, plan


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py"
SPEC = importlib.util.spec_from_file_location("planning_policy_worker_handoff_ledger", SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ledger)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class PlanningPolicyWorkerHandoffTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.common = ["--ledger-root", str(self.root), "--plan-id", "handoff-plan"]
        self.plan = plan()
        self.plan_file = self.root / "plan.json"
        self.plan_file.write_text(json.dumps(self.plan), encoding="utf-8")
        self.binding_file = self.root / "binding.json"
        self.binding_file.write_text(json.dumps(binding(self.plan)), encoding="utf-8")
        self.worktree = self.root / "worker-worktree"
        self.assignment_file = self.root / "assignments.json"
        self.assignment_file.write_text(
            json.dumps(
                [{
                    "id": "build", "harness": "codex",
                    "model_or_alias": "gpt-5.6-terra", "effort": "medium",
                    "worktree": str(self.worktree),
                }]
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def call(self, *args: str):
        with contextlib.redirect_stdout(io.StringIO()) as stream, contextlib.redirect_stderr(io.StringIO()):
            code = ledger.main(args)
        return code, json.loads(stream.getvalue())

    def started_run(self) -> str:
        code, init = self.call(
            *self.common, "init-v5", "--actor", "parent", "--approved",
            "--plan-file", str(self.plan_file), "--assignments-file", str(self.assignment_file),
            "--capability-binding-file", str(self.binding_file),
        )
        self.assertEqual(0, code, init)
        run_id = init["run_id"]
        for target in ("ready", "in_progress"):
            args = [*self.common, "transition", "--actor", "parent", "--run-id", run_id,
                    "--step-id", "build", "--to", target]
            if target == "ready":
                args.extend(["--agent-id", "worker-1"])
            code, result = self.call(*args)
            self.assertEqual(0, code, result)
        return run_id

    def handoff(self, run_id: str) -> dict:
        code, result = self.call(*self.common, "handoff", "--run-id", run_id, "--step-id", "build")
        self.assertEqual(0, code, result)
        return result["handoff"]

    def completed_return(self, handoff: dict) -> dict:
        return {
            "schema": "bounded-step-return-v1",
            "step_id": handoff["step_id"], "attempt_id": handoff["attempt_id"],
            "agent_id": handoff["agent_id"], "status": "completed", "changed_paths": [],
            "acceptance": {"command": handoff["leaf"]["acceptance_command"], "exit_code": 0,
                           "summary": "focused check passed"},
            "blockers": [], "notes": [], "unstarted_remainder": [], "commit_hash": "",
        }

    def test_handoff_contains_exact_worker_context_and_is_read_only(self) -> None:
        run_id = self.started_run()
        checkpoint = self.root / "planning-policy/ledgers/handoff-plan" / run_id / "checkpoint.json"
        before = checkpoint.read_bytes()

        packet = self.handoff(run_id)

        self.assertEqual("planning-worker-handoff-v1", packet["schema"])
        self.assertEqual("handoff-plan", packet["plan_id"])
        self.assertEqual(run_id, packet["run_id"])
        self.assertEqual(canonical_sha256(self.plan), packet["plan_sha256"])
        self.assertEqual("build", packet["step_id"])
        self.assertEqual("worker-1", packet["agent_id"])
        self.assertEqual(str(self.worktree), packet["worktree"])
        self.assertEqual(self.plan["leaves"][0], packet["leaf"])
        self.assertEqual(self.plan["work_units"][0], packet["work_unit"])
        self.assertEqual("codex", packet["host"])
        self.assertEqual("gpt-5.6-terra", packet["executor"])
        self.assertEqual("planning-capability-binding-v1", packet["capability_binding"]["schema"])
        self.assertIsNone(packet["retry_remediation"])
        self.assertEqual("bounded-step-return-v1", packet["return_schema"]["properties"]["schema"]["const"])
        self.assertEqual(before, checkpoint.read_bytes())

    def test_validate_return_needs_only_the_packet_and_return_files(self) -> None:
        packet = self.handoff(self.started_run())
        handoff_file = self.root / "handoff.json"
        return_file = self.root / "return.json"
        handoff_file.write_text(json.dumps(packet), encoding="utf-8")
        return_file.write_text(json.dumps(self.completed_return(packet)), encoding="utf-8")

        code, result = self.call("--ledger-root", str(self.root / "does-not-exist"),
                                 "validate-return", "--handoff-file", str(handoff_file),
                                 "--return-file", str(return_file))

        self.assertEqual(0, code, result)
        self.assertEqual({"ok", "action", "plan_id", "run_id", "step_id", "agent_id",
                          "attempt_id", "status", "handoff_sha256", "return_sha256"}, set(result))
        self.assertEqual("completed", result["status"])

    def test_packet_and_return_tampering_are_rejected_without_ledger_mutation(self) -> None:
        packet = self.handoff(self.started_run())
        handoff_file = self.root / "handoff.json"
        return_file = self.root / "return.json"
        return_file.write_text(json.dumps(self.completed_return(packet)), encoding="utf-8")
        packet["agent_id"] = "foreign-worker"
        handoff_file.write_text(json.dumps(packet), encoding="utf-8")
        code, result = self.call("validate-return", "--handoff-file", str(handoff_file),
                                 "--return-file", str(return_file))
        self.assertNotEqual(0, code, result)
        self.assertIn("handoff", result["error"])

        packet = self.handoff(self.started_run())
        handoff_file.write_text(json.dumps(packet), encoding="utf-8")
        invalid = self.completed_return(packet)
        invalid["notes"] = [{"type": "unknown", "message": "bad"}]
        return_file.write_text(json.dumps(invalid), encoding="utf-8")
        code, result = self.call("validate-return", "--handoff-file", str(handoff_file),
                                 "--return-file", str(return_file))
        self.assertNotEqual(0, code, result)
        self.assertEqual("invalid typed notes", result["error"])

    def test_builder_rejects_incomplete_or_oversized_packets(self) -> None:
        packet = self.handoff(self.started_run())
        self.assertEqual(packet["handoff_sha256"], canonical_sha256(
            {key: value for key, value in packet.items() if key != "handoff_sha256"}
        ))
        bad_step = copy.deepcopy({"id": "build"})
        with self.assertRaisesRegex(ledger.Error, "in_progress"):
            ledger.build_worker_handoff(self.plan, bad_step, "handoff-plan", packet["run_id"])

        oversized = copy.deepcopy(self.plan)
        oversized["leaves"][0]["settled_decisions"]["padding"] = "x" * (33 * 1024)
        oversized_step = self._step_for(packet["run_id"])
        oversized_binding = binding(oversized)
        oversized_step["capability_binding"] = {
            "schema": oversized_binding["schema"],
            "plan_sha256": oversized_binding["plan_sha256"],
            "bindings": oversized_binding["bindings"],
        }
        oversized_step["capability_binding_sha256"] = canonical_sha256(
            oversized_step["capability_binding"]
        )
        with self.assertRaisesRegex(ledger.Error, "exceeds 32 KiB"):
            ledger.build_worker_handoff(
                oversized,
                oversized_step,
                "handoff-plan",
                packet["run_id"],
            )

    def _step_for(self, run_id: str) -> dict:
        checkpoint = self.root / "planning-policy/ledgers/handoff-plan" / run_id / "checkpoint.json"
        return json.loads(checkpoint.read_text(encoding="utf-8"))["steps"]["build"]

    def rebuilt_packet(self, candidate: dict) -> dict:
        run_id = self.started_run()
        step = self._step_for(run_id)
        resolved = binding(candidate)
        step["capability_binding"] = {
            "schema": resolved["schema"], "plan_sha256": resolved["plan_sha256"],
            "bindings": resolved["bindings"],
        }
        step["capability_binding_sha256"] = canonical_sha256(step["capability_binding"])
        step["current_tier"] = candidate["leaves"][0]["portable_tier"]
        return ledger.build_worker_handoff(candidate, step, "handoff-plan", run_id)

    def test_packet_keeps_dependent_and_non_single_work_unit_context(self) -> None:
        dependent = copy.deepcopy(self.plan)
        other = copy.deepcopy(dependent["leaves"][0])
        other.update(id="other", dependencies=[], work_unit_id="other")
        dependent["leaves"].append(other)
        dependent["leaves"][0]["dependencies"] = ["other"]
        dependent["work_units"].append({
            "id": "other", "original_size": "small", "cohesive_outcome": "Other prerequisite",
            "decomposition": {"shape": "single"},
        })
        packet = self.rebuilt_packet(dependent)
        self.assertEqual(["other"], packet["leaf"]["dependencies"])
        self.assertEqual("build", ledger.valid_worker_handoff(packet)["step_id"])

        for shape, basis in (("parallel", "parallel_independence"), ("checkpointed", "failure_isolation")):
            with self.subTest(shape=shape):
                candidate = copy.deepcopy(self.plan)
                candidate["work_units"][0]["decomposition"] = {
                    "shape": shape, "basis": basis, "rationale": "The assigned member retains this context.",
                }
                packet = self.rebuilt_packet(candidate)
                self.assertEqual(shape, packet["work_unit"]["decomposition"]["shape"])
                self.assertEqual(shape, ledger.valid_worker_handoff(packet)["work_unit"]["decomposition"]["shape"])

        analytical = copy.deepcopy(self.plan)
        analytical["leaves"][0].update(
            portable_tier="analytical", irreducible_unknown_or_risk="Requires bounded analysis.",
        )
        analytical["analytical_heavy_exception"] = {
            "rationale": "One analytical fixture exercises packet transport.", "user_approved_by": "test",
        }
        packet = self.rebuilt_packet(analytical)
        self.assertEqual("analytical", ledger.valid_worker_handoff(packet)["portable_tier"])

    def test_return_schema_is_a_complete_nested_json_schema(self) -> None:
        schema = ledger.bounded_return_schema()
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual("object", schema["properties"]["acceptance"]["type"])
        self.assertIn("dependentRequired", schema["properties"]["acceptance"])
        self.assertEqual(ledger.MAX_NOTE_MESSAGE, schema["properties"]["notes"]["items"]["properties"]["message"]["maxLength"])
        self.assertEqual(ledger.COMMIT.pattern[:-1] + "?$", schema["properties"]["commit_hash"]["pattern"])

    def test_malformed_files_and_events_fail_without_tracebacks(self) -> None:
        run_id = self.started_run()
        packet = self.handoff(run_id)
        handoff_file = self.root / "handoff.json"
        return_file = self.root / "return.json"
        packet["plan_context"] = []
        packet["handoff_sha256"] = canonical_sha256(
            {key: value for key, value in packet.items() if key != "handoff_sha256"}
        )
        handoff_file.write_text(json.dumps(packet), encoding="utf-8")
        return_file.write_text(json.dumps(self.completed_return(packet)), encoding="utf-8")
        code, result = self.call("validate-return", "--handoff-file", str(handoff_file),
                                 "--return-file", str(return_file))
        self.assertNotEqual(0, code, result)
        self.assertNotIn("Traceback", result["error"])

        packet = self.handoff(run_id)
        handoff_file.write_text(json.dumps(packet), encoding="utf-8")
        malformed = self.completed_return(packet)
        malformed["changed_paths"] = [{}]
        return_file.write_text(json.dumps(malformed), encoding="utf-8")
        code, result = self.call("validate-return", "--handoff-file", str(handoff_file),
                                 "--return-file", str(return_file))
        self.assertNotEqual(0, code, result)
        self.assertEqual("invalid changed_paths", result["error"])

        handoff_file.write_bytes(b" " * (ledger.MAX_WORKER_HANDOFF_RAW + 1))
        code, result = self.call("validate-return", "--handoff-file", str(handoff_file),
                                 "--return-file", str(return_file))
        self.assertNotEqual(0, code, result)
        self.assertEqual("worker handoff exceeds byte limit", result["error"])

        packet = self.handoff(run_id)
        handoff_file.write_text(json.dumps(packet), encoding="utf-8")
        return_file.write_bytes(b" " * (ledger.MAX_RETURN + 1))
        code, result = self.call("validate-return", "--handoff-file", str(handoff_file),
                                 "--return-file", str(return_file))
        self.assertNotEqual(0, code, result)
        self.assertEqual("step return exceeds byte limit", result["error"])

        events = self.root / "planning-policy/ledgers/handoff-plan" / run_id / "events.jsonl"
        checkpoint = self.root / "planning-policy/ledgers/handoff-plan" / run_id / "checkpoint.json"
        before = checkpoint.read_bytes()
        events.write_text("{}\n", encoding="utf-8")
        code, result = self.call(*self.common, "handoff", "--run-id", run_id, "--step-id", "build")
        self.assertNotEqual(0, code, result)
        self.assertEqual(before, checkpoint.read_bytes())


if __name__ == "__main__":
    unittest.main()
