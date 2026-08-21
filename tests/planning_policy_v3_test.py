"""Current-contract cost advisory and opt-in usage tracing regression tests."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


contract = load("planning_policy_v3_contract", POLICY / "validate_plan_contract.py")
ledger = load("planning_policy_v3_ledger", POLICY / "planning_ledger.py")


def plan(version: int = 4, cost: object = None, include_cost: bool = False) -> dict:
    value = {
        "contract_version": version,
        "objective": "Ship one bounded change",
        "scope_summary": "One source file and its focused test",
        "approved_decisions": ["Keep cost data advisory"],
        "work_units": [{"id": "build", "original_size": "small"}],
        "leaves": [
            {
                "id": "build",
                "dependencies": [],
                "task": "Implement the bounded change",
                "boundary": "Do not edit adjacent modules",
                "read_set": ["src/input.py"],
                "write_set": ["src/output.py"],
                "settled_decisions": {"shape": "settled"},
                "size": "small",
                "portable_tier": "standard",
                "worktree_owner": "task/build",
                "acceptance_command": "uv run python -m unittest tests.focused_test",
                "return_contract": "bounded-step-return-v1",
                "stop_conditions": ["missing_load_bearing_information"],
                "work_unit_id": "build",
                "max_attempts": 3,
            }
        ],
    }
    if include_cost:
        value["execution_cost"] = cost
    if version == 4:
        value["leaves"][0]["capability_requirements"] = {
            "baseline": "plan-step-base-v1",
            "additional": [],
        }
    return value


def binding(value: dict) -> dict:
    plan_sha256 = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
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
            for leaf in value["leaves"]
        ],
    }


def validate_current(value: dict) -> dict:
    return contract.validate(value, capability_binding=binding(value))


def token_range(low: int, expected: int, high: int) -> dict[str, int]:
    return {"low": low, "expected": expected, "high": high}


class PlanningPolicyV3ContractTest(unittest.TestCase):
    def test_missing_and_malformed_cost_profiles_never_change_dispatch(self) -> None:
        missing_plan = plan()
        malformed_plan = plan(cost={"schema": "wrong"}, include_cost=True)
        missing = validate_current(missing_plan)
        malformed = validate_current(malformed_plan)
        self.assertTrue(missing["valid"] and missing["dispatch_ready"])
        self.assertTrue(malformed["valid"] and malformed["dispatch_ready"])
        self.assertIn("PLANCOST-MISSING-PROFILE", missing["cost_advisory"]["codes"])
        self.assertIn("PLANCOST-INVALID-PROFILE", malformed["cost_advisory"]["codes"])

    def test_v2_and_v3_are_resume_only_and_v4_is_forward_dispatch_contract(self) -> None:
        old = contract.validate(plan(version=2))
        prior = contract.validate(plan(version=3))
        current_plan = plan()
        current = validate_current(current_plan)
        self.assertTrue(old["valid"])
        self.assertFalse(old["dispatch_ready"])
        self.assertTrue(old["resume_ready"])
        self.assertIn("blocked:contract_migration_required", old["warnings"])
        self.assertTrue(prior["valid"])
        self.assertFalse(prior["dispatch_ready"])
        self.assertTrue(prior["resume_ready"])
        self.assertTrue(current["dispatch_ready"])
        self.assertTrue(current["approval_ready"])

    def test_known_lanes_compute_expected_and_high_without_mixing_units(self) -> None:
        profile = {
            "schema": "planning-execution-cost-v1",
            "mode": "advisory",
            "expected_attempts": 1,
            "leaf_attempt_overrides": {"build": 2},
            "declared_model_tokens": {
                "parent_baseline": token_range(10, 20, 30),
                "worker_attempts": {"build": token_range(100, 120, 150)},
                "parent_turns": token_range(5, 10, 20),
                "retained_return_context": token_range(2, 4, 8),
                "final_verification": token_range(20, 30, 40),
            },
            "final_verification_commands": ["uv run python -m unittest tests.focused_test"],
            "assumptions": ["One parent turn after each attempt"],
            "unknowns": [],
        }
        result = contract.validate(plan(cost=profile, include_cost=True))
        advisory = result["cost_advisory"]
        self.assertEqual({"low": 237, "expected": 304, "high": 398}, advisory["declared_total_run"])
        self.assertEqual({"expected": 2, "maximum": 3}, advisory["attempts"]["build"])
        self.assertEqual("known", advisory["final_verification_reserve"])
        self.assertIn("stable_proxy", advisory)
        self.assertNotIn("provider_measured_tokens", advisory["declared_total_run"])

    def test_unknowns_stay_unknown_and_advisory_is_bounded(self) -> None:
        result = contract.validate(plan())
        advisory = result["cost_advisory"]
        self.assertIsNone(advisory["declared_total_run"])
        self.assertEqual("indeterminate", advisory["final_verification_reserve"])
        self.assertLessEqual(contract.proxy_tokens(advisory), 600)

        many = plan()
        template = many["leaves"][0]
        many["leaves"] = []
        many["work_units"] = []
        for number in range(80):
            leaf = dict(template, id=f"build-{number}", work_unit_id=f"unit-{number}")
            many["leaves"].append(leaf)
            many["work_units"].append({"id": f"unit-{number}", "original_size": "small"})
        bounded = contract.validate(many)["cost_advisory"]
        self.assertGreater(bounded["attempts_omitted"], 0)
        self.assertLessEqual(contract.proxy_tokens(bounded), 600)

    def test_settled_leaf_tiered_standard_is_advisory_not_an_error(self) -> None:
        current = plan()
        over = validate_current(current)
        self.assertTrue(over["valid"] and over["dispatch_ready"])
        self.assertIn("PLANCOST-TIER-OVER-ASSIGNED", over["cost_advisory"]["codes"])
        self.assertEqual(1, over["cost_advisory"]["tier_mix"]["over_assigned"])

        named = plan()
        named["leaves"][0]["open_implementation_choice"] = "Pick the retry boundary"
        silenced = contract.validate(named)["cost_advisory"]
        self.assertNotIn("PLANCOST-TIER-OVER-ASSIGNED", silenced["codes"])
        self.assertEqual(0, silenced["tier_mix"]["over_assigned"])

    def test_tier_mix_reports_the_share_and_spares_unsettled_shapes(self) -> None:
        routed = plan()
        routed["leaves"][0]["portable_tier"] = "mechanical"
        mix = contract.validate(routed)["cost_advisory"]["tier_mix"]
        self.assertEqual(1.0, mix["mechanical_share"])
        self.assertEqual(0, mix["over_assigned"])
        self.assertEqual(1, mix["counts"]["mechanical"])

        for field, value in (
            ("write_set", ["src/**/*.py"]),
            ("size", "medium"),
            ("settled_decisions", {}),
        ):
            unsettled = plan()
            unsettled["leaves"][0][field] = value
            advisory = contract.validate(unsettled)["cost_advisory"]
            self.assertEqual(
                0, advisory["tier_mix"]["over_assigned"], f"{field}={value!r} is not settled work"
            )


class PlanningPolicyV3LedgerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.common = ["--ledger-root", str(self.root), "--plan-id", "plan"]
        self.plan_file = self.root / "plan.json"
        self.plan_file.write_text(json.dumps(plan()), encoding="utf-8")
        self.assignments_file = self.root / "assignments.json"
        self.assignments_file.write_text(
            json.dumps(
                [
                    {
                        "id": "build",
                        "harness": "codex",
                        "model_or_alias": "gpt-5.6-terra",
                        "effort": "medium",
                        "worktree": ".worktrees/build",
                    }
                ]
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def call(self, *args: str):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = ledger.main(args)
        return code, json.loads(stream.getvalue())

    def init3(self) -> str:
        selected_plan = json.loads(self.plan_file.read_text(encoding="utf-8"))
        binding_file = self.root / "capability-binding.json"
        binding_file.write_text(json.dumps(binding(selected_plan)), encoding="utf-8")
        code, result = self.call(
            *self.common,
            "init-v4",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(self.plan_file),
            "--assignments-file",
            str(self.assignments_file),
            "--capability-binding-file",
            str(binding_file),
        )
        self.assertEqual(0, code, result)
        return result["run_id"]

    def test_v2_and_v3_init_refuse_new_run_and_v4_has_no_trace_state_by_default(self) -> None:
        for command in ("init-v2", "init-v3"):
            code, result = self.call(
                *self.common,
                command,
                "--actor",
                "parent",
                "--approved",
                "--plan-file",
                str(self.plan_file),
                "--assignments-file",
                str(self.assignments_file),
            )
            self.assertEqual(3, code)
            self.assertEqual("blocked:contract_migration_required", result["error"])
        run_id = self.init3()
        run = self.root / "planning-policy/ledgers/plan" / run_id
        checkpoint = json.loads((run / "checkpoint.json").read_text(encoding="utf-8"))
        self.assertEqual(4, checkpoint["schema"])
        self.assertFalse((run / "usage").exists())
        show_code, shown = self.call(*self.common, "show", "--run-id", run_id)
        self.assertEqual(0, show_code)
        self.assertNotIn("trace", shown)

    def test_trace_is_explicit_rejects_raw_content_and_bounds_summary(self) -> None:
        run_id = self.init3()
        code, initialized = self.call(
            *self.common, "trace-init", "--actor", "parent", "--run-id", run_id
        )
        self.assertEqual(0, code, initialized)
        bad = self.root / "bad-usage.json"
        bad.write_text(
            json.dumps(
                {
                    "schema": "planning-usage-summary-v1",
                    "run_id": run_id,
                    "step_id": "parent",
                    "attempt_id": "run",
                    "actor": "parent",
                    "stage": "final_verify",
                    "harness": "codex",
                    "model": "gpt-5.6-sol",
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "total_tokens": 15,
                    "prompt": "must never be stored",
                }
            ),
            encoding="utf-8",
        )
        code, rejected = self.call(
            *self.common,
            "trace-record",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--usage-file",
            str(bad),
        )
        self.assertEqual(3, code)
        self.assertIn("raw-content", rejected["error"])
        good = json.loads(bad.read_text(encoding="utf-8"))
        del good["prompt"]
        good_path = self.root / "good-usage.json"
        good_path.write_text(json.dumps(good), encoding="utf-8")
        code, recorded = self.call(
            *self.common,
            "trace-record",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--usage-file",
            str(good_path),
        )
        self.assertEqual(0, code, recorded)
        code, shown = self.call(*self.common, "trace-show", "--actor", "parent", "--run-id", run_id)
        self.assertEqual(0, code, shown)
        self.assertEqual("planning-usage-advisory-v1", shown["schema"])
        self.assertEqual(15, shown["provider_measured"]["total_tokens"])
        self.assertLessEqual(shown["summary_proxy_tokens"], 600)
        code, closed = self.call(
            *self.common, "trace-close", "--actor", "parent", "--run-id", run_id
        )
        self.assertEqual(0, code, closed)

    def test_existing_v2_run_resumes_without_rewriting_checkpoint(self) -> None:
        run_id = self.init3()
        run = self.root / "planning-policy/ledgers/plan" / run_id
        old_plan = json.loads((run / "plan.json").read_text(encoding="utf-8"))
        old_plan["contract_version"] = 2
        for leaf in old_plan["leaves"]:
            leaf.pop("capability_requirements")
        checkpoint = json.loads((run / "checkpoint.json").read_text(encoding="utf-8"))
        checkpoint["schema"] = 2
        checkpoint["plan_hash"] = ledger.digest(old_plan)
        for step in checkpoint["steps"].values():
            step.pop("capability_binding")
            step.pop("capability_binding_sha256")
            step["current_assignment"].pop("model_or_alias")
        event = json.loads((run / "events.jsonl").read_text(encoding="utf-8"))
        event["action"] = "init-v2"
        event["plan_hash"] = checkpoint["plan_hash"]
        ledger.write(run / "plan.json", old_plan, 64 * 1024)
        ledger.write(run / "checkpoint.json", checkpoint)
        (run / "events.jsonl").write_bytes(ledger.canon(event) + b"\n")
        before = (run / "checkpoint.json").read_bytes()
        code, shown = self.call(*self.common, "show", "--run-id", run_id)
        self.assertEqual(0, code, shown)
        self.assertEqual(2, shown["contract_version"])
        self.assertEqual(before, (run / "checkpoint.json").read_bytes())

    def test_trace_validates_stage_identity_and_follows_run_purge(self) -> None:
        run_id = self.init3()
        self.assertEqual(
            0,
            self.call(*self.common, "trace-init", "--actor", "parent", "--run-id", run_id)[0],
        )
        invalid = self.root / "invalid-stage.json"
        invalid.write_text(
            json.dumps(
                {
                    "schema": "planning-usage-summary-v1",
                    "run_id": run_id,
                    "step_id": "build",
                    "attempt_id": "not-current",
                    "actor": "worker",
                    "stage": "secret_stage",
                    "harness": "codex",
                    "model": "gpt-5.6-terra",
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "total_tokens": 2,
                }
            ),
            encoding="utf-8",
        )
        code, result = self.call(
            *self.common,
            "trace-record",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--usage-file",
            str(invalid),
        )
        self.assertEqual(3, code)
        self.assertIn("stage", result["error"])
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "close",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--outcome",
                "abandoned",
                "--reason",
                "test retention",
            )[0],
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "purge",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--before-retention",
                "--reason",
                "test exact purge",
            )[0],
        )
        self.assertFalse((self.root / "planning-policy/ledgers/plan" / run_id).exists())

    def test_trace_reports_drift_only_for_compatible_worker_provenance(self) -> None:
        value = plan(
            cost={
                "schema": "planning-execution-cost-v1",
                "mode": "advisory",
                "final_verification_commands": ["uv run test"],
                "assumptions": [],
                "unknowns": [],
                "declared_model_tokens": {
                    "parent_baseline": token_range(1, 1, 1),
                    "worker_attempts": {"build": token_range(5, 10, 15)},
                    "parent_turns": token_range(1, 1, 1),
                    "retained_return_context": token_range(1, 1, 1),
                    "final_verification": token_range(1, 1, 1),
                },
            },
            include_cost=True,
        )
        self.plan_file.write_text(json.dumps(value), encoding="utf-8")
        run_id = self.init3()
        for target in ("ready", "in_progress"):
            args = [
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--step-id",
                "build",
                "--to",
                target,
            ]
            if target == "ready":
                args += ["--agent-id", "worker-build"]
            self.assertEqual(0, self.call(*args)[0])
        checkpoint = json.loads(
            (self.root / "planning-policy/ledgers/plan" / run_id / "checkpoint.json").read_text(
                encoding="utf-8"
            )
        )
        attempt_id = checkpoint["steps"]["build"]["attempt_id"]
        self.assertEqual(
            0,
            self.call(*self.common, "trace-init", "--actor", "parent", "--run-id", run_id)[0],
        )
        usage = self.root / "worker-usage.json"
        usage.write_text(
            json.dumps(
                {
                    "schema": "planning-usage-summary-v1",
                    "run_id": run_id,
                    "step_id": "build",
                    "attempt_id": attempt_id,
                    "actor": "worker",
                    "stage": "implement",
                    "harness": "codex",
                    "model": "gpt-5.6-terra",
                    "input_tokens": 20,
                    "output_tokens": 10,
                    "total_tokens": 30,
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "trace-record",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--usage-file",
                str(usage),
            )[0],
        )
        code, shown = self.call(*self.common, "trace-show", "--actor", "parent", "--run-id", run_id)
        self.assertEqual(0, code, shown)
        self.assertIn("PLANCOST-COMPARABLE-OBSERVED-DRIFT", shown["findings"])


if __name__ == "__main__":
    unittest.main()
