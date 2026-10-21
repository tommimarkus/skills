import unittest

from tests.planning_policy_shared_contract_test import ABSENT, MODULE, assert_mode_field, leaf, v5_plan


def plan_with(**leaf_fields):
    item = leaf("a", "u1")
    item.update(leaf_fields)
    return v5_plan(item)


def errors_of(plan):
    return MODULE.validate(plan)["errors"]


class VerificationFieldTest(unittest.TestCase):
    def test_absent_and_known_modes_are_valid_and_others_are_contract_errors(self):
        assert_mode_field(self, "verification", (ABSENT, "per-leaf", "closeout-only"),
                          ("never", "", None, ["per-leaf"], 1), plan_with)


class ChangesetBudgetTest(unittest.TestCase):
    def test_defaults_follow_size_band(self):
        for size, lines, files in (("small", 150, 6), ("medium", 400, 15), ("large", 400, 15)):
            budget = MODULE.changeset_budget({"size": size, "write_set": ["x.py"]})
            self.assertEqual(
                {"max_changed_lines": lines, "max_files": files, "exempt_paths": []}, budget
            )

    def test_declared_limits_and_exemptions_are_returned(self):
        item = {
            "size": "small",
            "write_set": ["docs/"],
            "changeset_budget": {
                "max_changed_lines": 300,
                "exempt_paths": ["docs/generated.md"],
                "reason": "generated index",
            },
        }
        self.assertEqual(
            {"max_changed_lines": 300, "max_files": 6, "exempt_paths": ["docs/generated.md"]},
            MODULE.changeset_budget(item),
        )

    def test_valid_budget_is_admitted(self):
        plan = plan_with(
            size="small",
            write_set=["outputs/a.py", "docs/*.md"],
            changeset_budget={
                "max_changed_lines": 300,
                "max_files": 12,
                "exempt_paths": ["outputs/a.py/extra", "docs/gen.md"],
                "reason": "needs a wider migration",
            },
        )
        plan["work_units"][0]["original_size"] = "small"
        self.assertEqual([], errors_of(plan))

    def test_invalid_budgets_are_rejected(self):
        cases = {
            "not an object": [],
            "unknown key": {"max_files": 3, "extra": 1},
            "zero": {"max_files": 0},
            "bool": {"max_files": True},
            "above 2x": {"max_changed_lines": 801, "reason": "r"},
            "raise without reason": {"max_changed_lines": 500},
            "empty reason": {"max_changed_lines": 500, "reason": ""},
            "long reason": {"max_changed_lines": 500, "reason": "x" * 241},
            "exempt without reason": {"exempt_paths": ["outputs/a.py"]},
            "uncovered exempt": {"exempt_paths": ["other/b.py"], "reason": "r"},
            "unsafe exempt": {"exempt_paths": ["../outputs/a.py"], "reason": "r"},
            "too many exempt": {
                "exempt_paths": [f"outputs/a.py/{n}" for n in range(9)],
                "reason": "r",
            },
        }
        for name, budget in cases.items():
            with self.subTest(name):
                self.assertTrue(
                    any("changeset_budget" in error for error in errors_of(plan_with(changeset_budget=budget)))
                )

    def test_lowering_a_limit_needs_no_reason(self):
        self.assertEqual([], errors_of(plan_with(changeset_budget={"max_files": 3})))


class VerifyDispatchesTest(unittest.TestCase):
    def advisory(self, plan):
        return MODULE.validate(plan)["cost_advisory"]

    def test_counts_dispatch_groups_or_zero_for_closeout_only(self):
        plan = v5_plan(leaf("a", "u1"), leaf("b", "u2"))
        self.assertEqual(2, self.advisory(plan)["verify_dispatches"])
        plan["leaves"][0]["batch"] = plan["leaves"][1]["batch"] = "pair"
        self.assertEqual(1, self.advisory(plan)["verify_dispatches"])
        plan["verification"] = "closeout-only"
        self.assertEqual(0, self.advisory(plan)["verify_dispatches"])


if __name__ == "__main__":
    unittest.main()
