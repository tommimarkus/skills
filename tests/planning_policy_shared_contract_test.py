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
    / "souroldgeezer-policy/skills/planning-policy/references/scripts/validate_plan_contract.py"
)
LEDGER_CONTRACT = (
    Path(__file__).parents[1]
    / "souroldgeezer-policy/skills/planning-policy/references/ledger-contract.md"
)
LEDGER_COMPATIBILITY = LEDGER_CONTRACT.with_name("ledger-compatibility.md")
TEMPLATE = (
    Path(__file__).parents[1]
    / "souroldgeezer-policy/skills/planning-policy/references/templates/plan-v4.json"
)
SPEC = importlib.util.spec_from_file_location("plan_contract", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def leaf(identifier, unit, tier="standard", dependencies=None):
    result = {
        "id": identifier,
        "dependencies": dependencies or [],
        "task": "Implement one bounded concern",
        "boundary": "Do not edit other concerns",
        "read_set": ["a.py"],
        "write_set": ["b.py"],
        "settled_decisions": {"shape": "chosen"},
        "size": "medium",
        "portable_tier": tier,
        "worktree_owner": "task/example",
        "acceptance_command": "uv run python -m unittest tests.example",
        "return_contract": "commit and focused output",
        "stop_conditions": ["missing_load_bearing_information"],
        "work_unit_id": unit,
    }
    if tier in {"analytical", "deep"}:
        result["irreducible_unknown_or_risk"] = "A bounded compatibility question remains"
    return result


def v3_plan(*leaves, work_units=None, **overrides):
    plan = {
        "contract_version": 3,
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


def v4_plan(*leaves, work_units=None, **overrides):
    plan = v3_plan(*leaves, work_units=work_units, **overrides)
    plan["contract_version"] = 4
    for item in plan["leaves"]:
        item["capability_requirements"] = {
            "baseline": "plan-step-base-v1",
            "additional": [],
        }
    return plan


def capability_binding(plan):
    plan_sha256 = hashlib.sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "schema": "planning-capability-binding-v1",
        "plan_sha256": plan_sha256,
        "bindings": [
            {
                "step_id": item["id"],
                "host": "codex",
                "executor": "gpt-5.6-terra",
                "requirements": item["capability_requirements"],
                "evidence": ["test fixture capability inventory"],
            }
            for item in plan["leaves"]
        ],
    }


class SharedContractTest(unittest.TestCase):
    def test_v4_template_is_canonical_blank_scaffold_and_populates_to_dispatch(self):
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual("contract_version", next(iter(template)))
        self.assertEqual(4, template["contract_version"])
        self.assertNotIn("version", template)
        self.assertTrue(
            {
                "contract_version",
                "objective",
                "scope_summary",
                "approved_decisions",
                "work_units",
                "leaves",
                "execution_cost",
            }.issubset(template)
        )
        self.assertTrue({"id", "original_size"}.issubset(template["work_units"][0]))
        self.assertTrue(set(MODULE.REQUIRED).issubset(template["leaves"][0]))
        self.assertIn("max_attempts", template["leaves"][0])
        self.assertEqual("bounded-step-return-v1", template["leaves"][0]["return_contract"])
        self.assertIn(
            "missing_load_bearing_information", template["leaves"][0]["stop_conditions"]
        )
        self.assertTrue(
            {
                "schema",
                "mode",
                "expected_attempts",
                "leaf_attempt_overrides",
                "declared_model_tokens",
                "final_verification_commands",
                "assumptions",
                "unknowns",
            }.issubset(template["execution_cost"])
        )

        blank = MODULE.validate(template)
        self.assertFalse(blank["valid"])
        self.assertFalse(blank["dispatch_ready"])

        template["objective"] = "Implement one approved bounded change"
        template["scope_summary"] = "Edit only the named source and focused test."
        template["approved_decisions"] = ["Use the settled contract shape."]
        template["work_units"][0].update(id="build", original_size="small")
        template["leaves"][0].update(
            id="build",
            task="Implement the approved change",
            boundary="Do not edit adjacent modules",
            read_set=["src/input.py", "tests/input_test.py"],
            write_set=["src/input.py", "tests/input_test.py"],
            settled_decisions={"shape": "settled"},
            size="small",
            portable_tier="mechanical",
            worktree_owner="task/build",
            acceptance_command="uv run python -m unittest tests.input_test",
            work_unit_id="build",
            max_attempts=2,
        )
        populated = MODULE.validate(template)
        self.assertTrue(populated["valid"], populated["errors"])
        self.assertTrue(populated["approval_ready"])
        self.assertFalse(populated["dispatch_ready"])
        bound = MODULE.validate(template, capability_binding=capability_binding(template))
        self.assertTrue(bound["dispatch_ready"])

    def test_accepts_weighted_medium_ready_plan(self):
        plan = {
            "work_units": [
                {"id": "u1", "original_size": "medium"},
                {"id": "u2", "original_size": "small"},
            ],
            "leaves": [leaf("one", "u1"), leaf("two", "u2", "analytical")],
        }
        result = MODULE.validate(plan)
        self.assertTrue(result["valid"])
        self.assertEqual(result["standard_ready_ratio"], 2 / 3)

    def test_rejects_artificial_split_and_missing_risk(self):
        plan = {
            "work_units": [{"id": "u1", "original_size": "small"}],
            "leaves": [leaf("one", "u1", "analytical"), leaf("two", "u1")],
        }
        del plan["leaves"][0]["irreducible_unknown_or_risk"]
        result = MODULE.validate(plan)
        self.assertFalse(result["valid"])
        self.assertTrue(any("irreducible" in error for error in result["errors"]))
        self.assertTrue(any("standard_ready_ratio" in error for error in result["errors"]))

    def test_rejects_cycles_and_unjustified_audit(self):
        first, second = (
            leaf("one", "u1", dependencies=["two"]),
            leaf("two", "u1", dependencies=["one"]),
        )
        first["selective_audit"] = {
            "owner": "test-quality-audit",
            "question": "review risks",
            "evidence_surface": "tests/",
            "domain_match": True,
        }
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [first, second]}
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("cyclic" in error for error in result["errors"]))
        self.assertTrue(
            any("must be true" in error or "bounded" in error for error in result["errors"])
        )

    def test_exception_waives_only_ratio(self):
        plan = {
            "work_units": [{"id": "u1", "original_size": "large"}],
            "leaves": [leaf("one", "u1", "deep")],
            "analytical_heavy_exception": {
                "rationale": "The chosen approach is research-first",
                "user_approved_by": "user",
            },
        }
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
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [audited_leaf]}
        )
        self.assertTrue(result["valid"])

    def test_rejects_malformed_dependency_ids_without_crashing(self):
        malformed = leaf("one", "u1", dependencies=[None, {}, "Not-Stable"])
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [malformed]}
        )
        self.assertFalse(result["valid"])
        self.assertEqual(sum("dependencies[" in error for error in result["errors"]), 3)

    def test_rejects_unstable_leaf_and_work_unit_ids(self):
        result = MODULE.validate(
            {
                "work_units": [{"id": "unit 1", "original_size": "medium"}],
                "leaves": [leaf("Leaf-1", "unit 1")],
            }
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("stable bounded identifier" in error for error in result["errors"]))

    def test_rejects_per_leaf_runtime_tuning(self):
        tuned = leaf("one", "u1")
        tuned["model_override"] = "expensive-model"
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [tuned]}
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("host-adapter controlled" in error for error in result["errors"]))

    def test_rejects_ordinary_and_vague_audit_routing(self):
        ordinary = leaf("one", "u1")
        ordinary["selective_audit"] = {
            "owner": "software-design",
            "initial_inspection": True,
            "domain_match": True,
            "materially_changes_approach_or_acceptance": True,
            "targeted_inspection_or_focused_tests_cannot_resolve": True,
            "question": "Which module should own pagination state?",
            "evidence_surface": "src/",
        }
        vague = leaf("two", "u2")
        vague["selective_audit"] = {
            "owner": "lean-audit",
            "initial_inspection": True,
            "domain_match": True,
            "materially_changes_approach_or_acceptance": True,
            "targeted_inspection_or_focused_tests_cannot_resolve": True,
            "question": "review for risks",
            "evidence_surface": "skills/",
        }
        ordinary_result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [ordinary]}
        )
        vague_result = MODULE.validate(
            {"work_units": [{"id": "u2", "original_size": "medium"}], "leaves": [vague]}
        )
        self.assertFalse(ordinary_result["valid"])
        self.assertTrue(any("owner" in error for error in ordinary_result["errors"]))
        self.assertFalse(vague_result["valid"])
        self.assertTrue(any("bounded" in error for error in vague_result["errors"]))

    def test_cli_emits_machine_safe_ratio(self):
        plan = {
            "work_units": [{"id": "u1", "original_size": "small"}],
            "leaves": [leaf("one", "u1")],
        }
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

    def test_version_three_is_resume_only_and_bound_version_four_dispatches(self):
        prior = MODULE.validate(v3_plan(leaf("one", "u1")))
        self.assertTrue(prior["valid"])
        self.assertEqual(prior["contract_version"], 3)
        self.assertFalse(prior["dispatch_ready"])
        self.assertTrue(prior["resume_ready"])
        self.assertIn("blocked:contract_migration_required", prior["warnings"])

        current = v4_plan(leaf("one", "u1"))
        result = MODULE.validate(current, capability_binding=capability_binding(current))
        self.assertTrue(result["valid"])
        self.assertEqual(result["contract_version"], 4)
        self.assertTrue(result["dispatch_ready"])

    def test_version_two_plan_is_resume_only(self):
        old = v3_plan(leaf("one", "u1"))
        old["contract_version"] = 2
        result = MODULE.validate(old)
        self.assertTrue(result["valid"])
        self.assertFalse(result["dispatch_ready"])
        self.assertTrue(result["resume_ready"])
        self.assertIn("blocked:contract_migration_required", result["warnings"])

    def test_legacy_unversioned_plan_is_valid_but_not_dispatch_ready(self):
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [leaf("one", "u1")]}
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["contract_version"], 1)
        self.assertFalse(result["dispatch_ready"])
        self.assertTrue(any("legacy" in warning for warning in result["warnings"]))

    def test_rejects_version_alias_without_classifying_it_as_legacy(self):
        aliased = v3_plan(leaf("one", "u1"))
        aliased["version"] = aliased.pop("contract_version")
        result = MODULE.validate(aliased)
        self.assertFalse(result["valid"])
        self.assertIsNone(result["contract_version"])
        self.assertEqual(
            ["version is not a valid plan discriminator; use `contract_version`"],
            result["errors"],
        )
        self.assertFalse(any("legacy" in warning for warning in result["warnings"]))

    def test_rejects_version_alias_even_with_contract_version(self):
        both = v3_plan(leaf("one", "u1"))
        both["version"] = 3
        result = MODULE.validate(both)
        self.assertFalse(result["valid"])
        self.assertEqual(3, result["contract_version"])
        self.assertIn(
            "version is not a valid plan discriminator; use `contract_version`",
            result["errors"],
        )

    def test_version_two_requires_bounded_fields_and_leaf_retry_contract(self):
        invalid = v3_plan(leaf("one", "u1"), objective="", approved_decisions=[])
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
        result = MODULE.validate(
            {
                "contract_version": 1,
                "work_units": [{"id": "u1", "original_size": "medium"}],
                "leaves": [leaf("one", "u1")],
            }
        )
        self.assertFalse(result["valid"])
        self.assertIsNone(result["contract_version"])
        self.assertFalse(result["dispatch_ready"])

    def test_batch_of_two_same_tier_and_owner_passes(self):
        first = leaf("one", "u1", "standard")
        second = leaf("two", "u1", "standard", dependencies=["one"])
        first["batch"] = "batch-a"
        second["batch"] = "batch-a"
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [first, second]}
        )
        self.assertTrue(result["valid"], result["errors"])

    def test_singleton_batch_fails(self):
        solo = leaf("one", "u1", "standard")
        solo["batch"] = "batch-a"
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "small"}], "leaves": [solo]}
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("2 to 8 members" in error for error in result["errors"]))

    def test_nine_member_batch_fails(self):
        members = [leaf(f"m{index}", "u1", "standard") for index in range(9)]
        for member in members:
            member["batch"] = "batch-a"
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "large"}], "leaves": members}
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("2 to 8 members" in error for error in result["errors"]))

    def test_batch_member_with_analytical_tier_fails(self):
        first = leaf("one", "u1", "standard")
        second = leaf("two", "u1", "analytical", dependencies=["one"])
        first["batch"] = "batch-a"
        second["batch"] = "batch-a"
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [first, second]}
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("mechanical or standard" in error for error in result["errors"]))

    def test_batch_members_must_share_worktree_owner(self):
        first = leaf("one", "u1", "standard")
        second = leaf("two", "u1", "standard", dependencies=["one"])
        first["batch"] = "batch-a"
        second["batch"] = "batch-a"
        second["worktree_owner"] = "task/other"
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [first, second]}
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("worktree_owner" in error for error in result["errors"]))

    def test_batch_dependency_on_later_listed_member_fails(self):
        first = leaf("one", "u1", "standard", dependencies=["two"])
        second = leaf("two", "u1", "standard")
        first["batch"] = "batch-a"
        second["batch"] = "batch-a"
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [first, second]}
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("later-listed batch member" in error for error in result["errors"]))

    def test_batch_member_external_dependency_is_unrestricted(self):
        outside = leaf("outside", "u1", "standard")
        first = leaf("one", "u1", "standard", dependencies=["outside"])
        second = leaf("two", "u1", "standard", dependencies=["one", "outside"])
        first["batch"] = "batch-a"
        second["batch"] = "batch-a"
        result = MODULE.validate(
            {
                "work_units": [{"id": "u1", "original_size": "large"}],
                "leaves": [outside, first, second],
            }
        )
        self.assertTrue(result["valid"], result["errors"])

    def test_invalid_batch_id_format_fails(self):
        malformed = leaf("one", "u1", "standard")
        malformed["batch"] = "Not Stable!"
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "small"}], "leaves": [malformed]}
        )
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("batch must be a stable bounded identifier" in error for error in result["errors"])
        )

    def test_plan_without_batch_field_is_unaffected(self):
        plan = {
            "work_units": [{"id": "u1", "original_size": "medium"}],
            "leaves": [leaf("one", "u1"), leaf("two", "u1", dependencies=["one"])],
        }
        result = MODULE.validate(plan)
        self.assertTrue(result["valid"], result["errors"])

    def test_stable_proxy_reports_leaf_count_and_handoff_total(self):
        plan = {
            "work_units": [{"id": "u1", "original_size": "medium"}],
            "leaves": [leaf("one", "u1"), leaf("two", "u1", dependencies=["one"])],
        }
        advisory = MODULE.validate(plan)["cost_advisory"]
        stable = advisory["stable_proxy"]
        self.assertEqual(2, stable["leaf_count"])
        expected_total = sum(
            MODULE.proxy_tokens({key: item.get(key) for key in MODULE.REQUIRED if key in item})
            for item in plan["leaves"]
        )
        self.assertEqual(expected_total, stable["handoff_total"])
        self.assertGreater(stable["handoff_total"], 0)

    def test_batched_dispatch_lowers_prefix_multiplication_while_handoff_total_matches(self):
        def build(batched):
            first = leaf("one", "u1", "mechanical")
            second = leaf("two", "u1", "mechanical", dependencies=["one"])
            first["max_attempts"] = 3
            second["max_attempts"] = 3
            if batched:
                first["batch"] = "batch-a"
                second["batch"] = "batch-a"
            plan = {
                "work_units": [{"id": "u1", "original_size": "medium"}],
                "leaves": [first, second],
                "execution_cost": {
                    "schema": "planning-execution-cost-v1",
                    "mode": "advisory",
                    "expected_attempts": 1,
                    "leaf_attempt_overrides": {"one": 2, "two": 2},
                    "final_verification_commands": ["uv run python -m unittest tests.example"],
                    "assumptions": [],
                    "unknowns": [],
                },
            }
            return MODULE.validate(plan)["cost_advisory"]

        unbatched = build(False)
        batched = build(True)
        self.assertEqual(
            unbatched["stable_proxy"]["handoff_total"], batched["stable_proxy"]["handoff_total"]
        )
        self.assertEqual(unbatched["stable_proxy"]["leaf_count"], batched["stable_proxy"]["leaf_count"])
        self.assertLess(
            batched["repeated_shared_prefix_proxy"], unbatched["repeated_shared_prefix_proxy"]
        )

    def test_unbatched_chain_fires_between_mechanical_leaves_even_without_profile(self):
        first = leaf("one", "u1", "mechanical")
        second = leaf("two", "u1", "mechanical", dependencies=["one"])
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [first, second]}
        )
        self.assertIn("PLANCOST-UNBATCHED-CHAIN", result["cost_advisory"]["codes"])
        self.assertIn("PLANCOST-MISSING-PROFILE", result["cost_advisory"]["codes"])
        self.assertTrue(result["valid"], result["errors"])

    def test_unbatched_chain_silenced_by_shared_batch(self):
        first = leaf("one", "u1", "mechanical")
        second = leaf("two", "u1", "mechanical", dependencies=["one"])
        first["batch"] = "batch-a"
        second["batch"] = "batch-a"
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [first, second]}
        )
        self.assertNotIn("PLANCOST-UNBATCHED-CHAIN", result["cost_advisory"]["codes"])
        self.assertTrue(result["valid"], result["errors"])

    def test_unbatched_chain_not_flagged_for_analytical_tiers(self):
        first = leaf("one", "u1", "analytical")
        second = leaf("two", "u1", "analytical", dependencies=["one"])
        result = MODULE.validate(
            {
                "work_units": [{"id": "u1", "original_size": "medium"}],
                "leaves": [first, second],
                "analytical_heavy_exception": {
                    "rationale": "Both steps need investigation",
                    "user_approved_by": "user",
                },
            }
        )
        self.assertNotIn("PLANCOST-UNBATCHED-CHAIN", result["cost_advisory"]["codes"])

    def test_unbatched_chain_not_flagged_across_worktree_owners(self):
        first = leaf("one", "u1", "mechanical")
        second = leaf("two", "u1", "mechanical", dependencies=["one"])
        second["worktree_owner"] = "task/other"
        result = MODULE.validate(
            {"work_units": [{"id": "u1", "original_size": "medium"}], "leaves": [first, second]}
        )
        self.assertNotIn("PLANCOST-UNBATCHED-CHAIN", result["cost_advisory"]["codes"])

    def test_plan_scale_fires_over_twelve_leaves_and_not_at_twelve(self):
        def build(count):
            leaves = [leaf(f"leaf{index}", f"u{index}") for index in range(count)]
            units = [{"id": f"u{index}", "original_size": "small"} for index in range(count)]
            return MODULE.validate({"work_units": units, "leaves": leaves})

        over = build(13)
        at_limit = build(12)
        self.assertIn("PLANCOST-PLAN-SCALE", over["cost_advisory"]["codes"])
        self.assertTrue(over["valid"], over["errors"])
        self.assertNotIn("PLANCOST-PLAN-SCALE", at_limit["cost_advisory"]["codes"])

    def test_plan_scale_fires_on_declared_weight_over_twenty_with_few_leaves(self):
        leaves = [leaf(f"leaf{index}", f"u{index}") for index in range(7)]
        units = [{"id": f"u{index}", "original_size": "large"} for index in range(7)]
        result = MODULE.validate({"work_units": units, "leaves": leaves})
        self.assertLessEqual(len(leaves), 12)
        self.assertIn("PLANCOST-PLAN-SCALE", result["cost_advisory"]["codes"])
        self.assertIn("PLANCOST-MISSING-PROFILE", result["cost_advisory"]["codes"])
        self.assertTrue(result["valid"], result["errors"])

    def test_ledger_contract_has_required_v2_lifecycle_and_return_anchors(self):
        contract = LEDGER_CONTRACT.read_text(encoding="utf-8") + LEDGER_COMPATIBILITY.read_text(
            encoding="utf-8"
        )
        required = (
            "<plan-id>/<run-id>",
            "UUID4",
            "init-v2",
            "assignment set",
            "exactly one current attempt",
            "--run-id",
            "max_attempts",
            "bounded-step-return-v1",
            "changed_paths",
            "commit_hash",
            "progress fingerprint",
            "blocked:no_progress",
            "blocked:retry_exhausted",
            "oversized",
            "SHA-256",
            "blocked:plan_tampered",
            "--step-id",
            "truncated: true",
            "contract_version: 1",
            "dispatch_ready: false",
            "no active version-1 ledger remains",
            "at most 8 KiB",
            "1 through 128 characters",
            "integer or `null` `exit_code`",
            "at most 32 unique",
            "at most 8 objects, each with `code`",
            "summary` of at most 240",
            "optional paired `evidence_path`/`sha256`",
            "`finding`",
            "`decision_needed`",
            "`residual_risk`",
            "`untouched`",
            "`verification_limit`",
            "The return does not list `run_id`",
            "40 or 64 lowercase",
            "only when `changed_paths` is non-empty",
            "oversized` also requires",
            "helper-generated bounded opaque `attempt_id`",
            "attempt count starts at 1",
            "canonical lowercase UUID4",
            "`completed` → `integrated` → `cleaned`",
            "planning-worktree-result-v1",
            "validate --closeout",
            "planning worktree closeout",
            "terminal `integrated` state is unchanged",
            "escalating_remediation_v1",
            "retry-remediation-v1",
            "exact `failed:acceptance`",
            "`blocked:needs_higher_tier`",
            "same-tier retry",
            "same-tier-used",
            "prior-return digest",
            "reuse or fresh",
            "target tier",
            "terminal precedence",
        )
        for anchor in required:
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, contract)


def series_plan(series):
    plan = {
        "work_units": [{"id": "u1", "original_size": "medium"}],
        "leaves": [leaf("one", "u1")],
    }
    if series is not None:
        plan["series"] = series
    return plan


def slice_one_series(**overrides):
    series = {
        "series_id": "plan-series",
        "slice": 1,
        "final": False,
        "end_verification_commands": ["uv run python -m unittest tests.example"],
    }
    series.update(overrides)
    return series


def predecessor_block(**overrides):
    predecessor = {
        "plan_id": "plan-series",
        "plan_sha256": "a" * 64,
        "run_id": "11111111-1111-4111-8111-111111111111",
        "outcome": "completed",
        "handoff_sha256": "b" * 64,
    }
    predecessor.update(overrides)
    return predecessor


def slice_two_series(**overrides):
    series = slice_one_series(slice=2, predecessor=predecessor_block())
    series.update(overrides)
    return series


class SeriesContractTest(unittest.TestCase):
    def test_absent_series_leaves_result_unchanged(self):
        plan = series_plan(None)
        self.assertNotIn("series", plan)
        result = MODULE.validate(plan)
        self.assertEqual(result, MODULE.validate(dict(plan)))
        self.assertTrue(result["valid"])
        self.assertFalse(any("series" in error for error in result["errors"]))

    def test_valid_slice_one_series_without_final(self):
        result = MODULE.validate(series_plan(slice_one_series()))
        self.assertTrue(result["valid"], result["errors"])

    def test_valid_slice_one_series_with_final_true(self):
        result = MODULE.validate(series_plan(slice_one_series(final=True)))
        self.assertTrue(result["valid"], result["errors"])

    def test_valid_slice_two_series_with_predecessor(self):
        result = MODULE.validate(series_plan(slice_two_series()))
        self.assertTrue(result["valid"], result["errors"])

    def test_predecessor_handoff_sha256_empty_string_accepted(self):
        series = slice_two_series(predecessor=predecessor_block(handoff_sha256=""))
        result = MODULE.validate(series_plan(series))
        self.assertTrue(result["valid"], result["errors"])

    def test_rejects_bad_series_id(self):
        result = MODULE.validate(series_plan(slice_one_series(series_id="Not-Stable")))
        self.assertFalse(result["valid"])
        self.assertTrue(any("series.series_id" in error for error in result["errors"]))

    def test_rejects_slice_zero(self):
        result = MODULE.validate(series_plan(slice_one_series(slice=0)))
        self.assertFalse(result["valid"])
        self.assertTrue(any("series.slice" in error for error in result["errors"]))

    def test_rejects_bool_slice(self):
        result = MODULE.validate(series_plan(slice_one_series(slice=True)))
        self.assertFalse(result["valid"])
        self.assertTrue(any("series.slice" in error for error in result["errors"]))

    def test_rejects_non_bool_final(self):
        result = MODULE.validate(series_plan(slice_one_series(final="no")))
        self.assertFalse(result["valid"])
        self.assertTrue(any("series.final" in error for error in result["errors"]))

    def test_rejects_empty_end_verification_commands(self):
        result = MODULE.validate(series_plan(slice_one_series(end_verification_commands=[])))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("series.end_verification_commands" in error for error in result["errors"])
        )

    def test_rejects_oversized_end_verification_command_string(self):
        series = slice_one_series(end_verification_commands=["x" * 481])
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("series.end_verification_commands" in error for error in result["errors"])
        )

    def test_rejects_five_end_verification_commands(self):
        series = slice_one_series(end_verification_commands=["uv run x"] * 5)
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("series.end_verification_commands" in error for error in result["errors"])
        )

    def test_rejects_missing_predecessor_at_slice_two(self):
        series = slice_one_series(slice=2)
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("predecessor is required" in error for error in result["errors"])
        )

    def test_rejects_predecessor_present_at_slice_one(self):
        series = slice_one_series(predecessor=predecessor_block())
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("predecessor is forbidden" in error for error in result["errors"])
        )

    def test_rejects_malformed_predecessor_plan_id(self):
        series = slice_two_series(predecessor=predecessor_block(plan_id="Not Stable"))
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("series.predecessor.plan_id" in error for error in result["errors"])
        )

    def test_rejects_malformed_predecessor_plan_sha256(self):
        series = slice_two_series(predecessor=predecessor_block(plan_sha256="not-hex"))
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("series.predecessor.plan_sha256" in error for error in result["errors"])
        )

    def test_rejects_malformed_predecessor_run_id(self):
        series = slice_two_series(predecessor=predecessor_block(run_id="not-a-uuid"))
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("series.predecessor.run_id" in error for error in result["errors"])
        )

    def test_rejects_predecessor_outcome_outside_set(self):
        series = slice_two_series(predecessor=predecessor_block(outcome="cancelled"))
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("series.predecessor.outcome" in error for error in result["errors"])
        )

    def test_rejects_malformed_predecessor_handoff_sha256(self):
        series = slice_two_series(predecessor=predecessor_block(handoff_sha256="short"))
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("series.predecessor.handoff_sha256" in error for error in result["errors"])
        )

    def test_rejects_unknown_key_in_series(self):
        series = slice_one_series()
        series["extra"] = "nope"
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(any("series has unknown keys" in error for error in result["errors"]))

    def test_rejects_unknown_key_in_predecessor(self):
        series = slice_two_series(predecessor=predecessor_block(extra="nope"))
        result = MODULE.validate(series_plan(series))
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("series.predecessor must have exactly the keys" in error for error in result["errors"])
        )


if __name__ == "__main__":
    unittest.main()
