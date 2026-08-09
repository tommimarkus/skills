import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "souroldgeezer-policy/skills/planning-policy/references/scripts/validate_plan_contract.py"
LEDGER_CONTRACT = Path(__file__).parents[1] / "souroldgeezer-policy/skills/planning-policy/references/ledger-contract.md"
SPEC = importlib.util.spec_from_file_location("plan_contract", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def leaf(identifier, unit, tier="standard", dependencies=None):
    result = {
        "id": identifier, "dependencies": dependencies or [], "task": "Implement one bounded concern",
        "boundary": "Do not edit other concerns", "read_set": ["a.py"], "write_set": ["b.py"],
        "settled_decisions": {"shape": "chosen"}, "size": "medium", "portable_tier": tier,
        "worktree_owner": "task/example", "acceptance_command": "uv run python -m unittest tests.example",
        "return_contract": "commit and focused output", "stop_conditions": ["missing_load_bearing_information"], "work_unit_id": unit,
    }
    if tier in {"analytical", "deep"}:
        result["irreducible_unknown_or_risk"] = "A bounded compatibility question remains"
    return result


def v2_plan(*leaves, work_units=None, **overrides):
    plan = {
        "contract_version": 2,
        "objective": "Implement the approved bounded change",
        "scope_summary": "Only the assigned files and acceptance command are in scope.",
        "approved_decisions": ["Use the settled shared contract shape."],
        "work_units": work_units or [{"id": "u1", "original_size": "medium"}],
        "leaves": list(leaves),
    }
    for item in plan["leaves"]:
        item["max_attempts"] = 2
        item["return_contract"] = "bounded-step-return-v1"
    plan.update(overrides)
    return plan


class SharedContractTest(unittest.TestCase):
    def test_accepts_weighted_medium_ready_plan(self):
        plan = {"work_units": [{"id": "u1", "original_size": "medium"}, {"id": "u2", "original_size": "small"}], "leaves": [leaf("one", "u1"), leaf("two", "u2", "analytical")]}
        result = MODULE.validate(plan)
        self.assertTrue(result["valid"])
        self.assertEqual(result["standard_ready_ratio"], 2 / 3)

    def test_rejects_artificial_split_and_missing_risk(self):
        plan = {"work_units": [{"id": "u1", "original_size": "small"}], "leaves": [leaf("one", "u1", "analytical"), leaf("two", "u1")]}
        del plan["leaves"][0]["irreducible_unknown_or_risk"]
        result = MODULE.validate(plan)
        self.assertFalse(result["valid"])
        self.assertTrue(any("irreducible" in error for error in result["errors"]))
        self.assertTrue(any("standard_ready_ratio" in error for error in result["errors"]))

    def test_rejects_cycles_and_unjustified_audit(self):
        first, second = leaf("one", "u1", dependencies=["two"]), leaf("two", "u1", dependencies=["one"])
        first["selective_audit"] = {"owner": "test-quality-audit", "question": "review risks", "evidence_surface": "tests/", "domain_match": True}
        result = MODULE.validate({"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [first, second]})
        self.assertFalse(result["valid"])
        self.assertTrue(any("cyclic" in error for error in result["errors"]))
        self.assertTrue(any("must be true" in error or "bounded" in error for error in result["errors"]))

    def test_exception_waives_only_ratio(self):
        plan = {"work_units": [{"id": "u1", "original_size": "large"}], "leaves": [leaf("one", "u1", "deep")], "analytical_heavy_exception": {"rationale": "The chosen approach is research-first", "user_approved_by": "user"}}
        result = MODULE.validate(plan)
        self.assertTrue(result["valid"])
        self.assertEqual(result["standard_ready_ratio"], 0.0)

    def test_accepts_bounded_audit_routed_to_owning_audit(self):
        audited_leaf = leaf("inspect-pagination-tests", "u1")
        audited_leaf["selective_audit"] = {
            "owner": "test-quality-audit",
            "initial_inspection": True,
            "domain_match": True,
            "materially_changes_approach_or_acceptance": True,
            "targeted_inspection_or_focused_tests_cannot_resolve": True,
            "question": "Do parameterized pagination tests conceal a fixture-coupling failure?",
            "evidence_surface": "tests/pagination_test.py",
        }
        result = MODULE.validate({"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [audited_leaf]})
        self.assertTrue(result["valid"])

    def test_rejects_malformed_dependency_ids_without_crashing(self):
        malformed = leaf("one", "u1", dependencies=[None, {}, "Not-Stable"])
        result = MODULE.validate({"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [malformed]})
        self.assertFalse(result["valid"])
        self.assertEqual(sum("dependencies[" in error for error in result["errors"]), 3)

    def test_rejects_unstable_leaf_and_work_unit_ids(self):
        result = MODULE.validate({"work_units": [{"id": "unit 1", "original_size": "medium"}], "leaves": [leaf("Leaf-1", "unit 1")]})
        self.assertFalse(result["valid"])
        self.assertTrue(any("stable bounded identifier" in error for error in result["errors"]))

    def test_rejects_per_leaf_runtime_tuning(self):
        tuned = leaf("one", "u1")
        tuned["model_override"] = "expensive-model"
        result = MODULE.validate({"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [tuned]})
        self.assertFalse(result["valid"])
        self.assertTrue(any("host-adapter controlled" in error for error in result["errors"]))

    def test_rejects_ordinary_and_vague_audit_routing(self):
        ordinary = leaf("one", "u1")
        ordinary["selective_audit"] = {
            "owner": "software-design", "initial_inspection": True, "domain_match": True,
            "materially_changes_approach_or_acceptance": True,
            "targeted_inspection_or_focused_tests_cannot_resolve": True,
            "question": "Which module should own pagination state?", "evidence_surface": "src/",
        }
        vague = leaf("two", "u2")
        vague["selective_audit"] = {
            "owner": "lean-audit", "initial_inspection": True, "domain_match": True,
            "materially_changes_approach_or_acceptance": True,
            "targeted_inspection_or_focused_tests_cannot_resolve": True,
            "question": "review for risks", "evidence_surface": "skills/",
        }
        ordinary_result = MODULE.validate({"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [ordinary]})
        vague_result = MODULE.validate({"work_units": [{"id": "u2", "original_size": "medium"}], "leaves": [vague]})
        self.assertFalse(ordinary_result["valid"])
        self.assertTrue(any("owner" in error for error in ordinary_result["errors"]))
        self.assertFalse(vague_result["valid"])
        self.assertTrue(any("bounded" in error for error in vague_result["errors"]))

    def test_cli_emits_machine_safe_ratio(self):
        plan = {"work_units": [{"id": "u1", "original_size": "small"}], "leaves": [leaf("one", "u1")]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
            json.dump(plan, handle)
            handle.flush()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = MODULE.main(["validate", handle.name])
        result = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["valid"])
        self.assertEqual(result["standard_ready_ratio"], 1.0)

    def test_accepts_dispatch_ready_version_two_plan(self):
        result = MODULE.validate(v2_plan(leaf("one", "u1")))
        self.assertTrue(result["valid"])
        self.assertEqual(result["contract_version"], 2)
        self.assertTrue(result["dispatch_ready"])
        self.assertEqual(result["warnings"], [])

    def test_legacy_unversioned_plan_is_valid_but_not_dispatch_ready(self):
        result = MODULE.validate({"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [leaf("one", "u1")]})
        self.assertTrue(result["valid"])
        self.assertEqual(result["contract_version"], 1)
        self.assertFalse(result["dispatch_ready"])
        self.assertTrue(any("legacy" in warning for warning in result["warnings"]))

    def test_version_two_requires_bounded_fields_and_leaf_retry_contract(self):
        invalid = v2_plan(leaf("one", "u1"), objective="", approved_decisions=[])
        invalid["leaves"][0]["max_attempts"] = 6
        invalid["leaves"][0]["return_contract"] = "commit and focused output"
        result = MODULE.validate(invalid)
        self.assertFalse(result["valid"])
        self.assertFalse(result["dispatch_ready"])
        self.assertTrue(any("objective" in error for error in result["errors"]))
        self.assertTrue(any("approved_decisions" in error for error in result["errors"]))
        self.assertTrue(any("max_attempts" in error for error in result["errors"]))
        self.assertTrue(any("return_contract" in error for error in result["errors"]))

    def test_rejects_unsupported_explicit_contract_version(self):
        result = MODULE.validate({"contract_version": 1, "work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [leaf("one", "u1")]})
        self.assertFalse(result["valid"])
        self.assertIsNone(result["contract_version"])
        self.assertFalse(result["dispatch_ready"])

    def test_ledger_contract_has_required_v2_lifecycle_and_return_anchors(self):
        contract = LEDGER_CONTRACT.read_text(encoding="utf-8")
        required = (
            "<plan-id>/<run-id>", "UUID4", "init-v2", "assignment set",
            "exactly one current attempt", "--run-id", "max_attempts",
            "bounded-step-return-v1", "changed_paths", "commit_hash",
            "progress fingerprint", "blocked:no_progress", "blocked:retry_exhausted",
            "oversized", "SHA-256", "blocked:plan_tampered", "--step-id",
            "truncated: true", "contract_version: 1", "dispatch_ready: false",
            "no active version-1 ledger remains", "at most 8 KiB",
            "1 through 128 characters", "integer or `null` `exit_code`",
            "at most 32 unique", "at most 8 objects, each with `code`",
            "summary` of at most 240", "optional paired `evidence_path`/`sha256`",
            "`finding`", "`decision_needed`", "`residual_risk`", "`untouched`",
            "`verification_limit`",
            "The return does not list `run_id`", "40 or 64 lowercase",
            "only when `changed_paths` is non-empty", "oversized` also requires",
            "helper-generated bounded opaque `attempt_id`", "attempt count starts at 1",
            "canonical lowercase UUID4",
            "`completed` → `integrated` → `cleaned`",
            "planning-worktree-result-v1", "validate --closeout",
            "planning worktree closeout",
            "terminal `integrated` state is unchanged",
        )
        for anchor in required:
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, contract)


if __name__ == "__main__":
    unittest.main()
