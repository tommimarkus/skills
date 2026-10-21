import unittest

from tests.planning_policy_shared_contract_test import MODULE, leaf, v5_plan


def plan_with(precision=None, **leaf_fields):
    item = leaf("a", "u1")
    item.update(leaf_fields)
    plan = v5_plan(item)
    if precision is not None:
        plan["precision"] = precision
    return plan


def errors_of(plan):
    return MODULE.validate(plan)["errors"]


class PrecisionFieldTest(unittest.TestCase):
    def test_absent_and_known_modes_are_valid(self):
        for precision in (None, "standard", "strict"):
            self.assertEqual([], errors_of(plan_with(precision)), precision)

    def test_other_values_are_contract_errors(self):
        for value in ("loose", "", None, ["strict"], 1):
            plan = plan_with()
            plan["precision"] = value
            self.assertTrue(any("precision" in error for error in errors_of(plan)), value)

    def test_standard_allows_absent_read_set_and_areas(self):
        plan = plan_with(write_set=["outputs", "src/**/*.py"], read_set=["docs"])
        self.assertEqual([], errors_of(plan))
        plan = plan_with()
        del plan["leaves"][0]["read_set"]
        self.assertEqual([], errors_of(plan))

    def test_standard_keeps_write_set_required_and_both_empty_rule(self):
        plan = plan_with()
        del plan["leaves"][0]["read_set"]
        plan["leaves"][0]["write_set"] = []
        self.assertTrue(errors_of(plan))
        self.assertEqual([], [e for e in errors_of(plan_with(read_set=[], write_set=["x.py"]))])
        self.assertTrue(any("cannot both be empty" in e for e in errors_of(plan_with(read_set=[], write_set=[]))))

    def test_strict_requires_exact_write_and_nonempty_exact_read(self):
        for fields in (
            {"write_set": ["outputs/*.py"], "read_set": ["a.py"]},
            {"write_set": ["outputs/a.py"], "read_set": []},
            {"write_set": ["outputs/a.py"], "read_set": ["docs/**"]},
            {"write_set": [], "read_set": ["a.py"]},
        ):
            self.assertTrue(errors_of(plan_with("strict", **fields)), fields)
        plan = plan_with("strict")
        del plan["leaves"][0]["read_set"]
        self.assertTrue(any("read_set" in e for e in errors_of(plan)))

    def test_strict_accepts_exact_sets(self):
        plan = plan_with("strict", write_set=["outputs/a.py"], read_set=["a.py", "docs"])
        self.assertEqual([], errors_of(plan))


if __name__ == "__main__":
    unittest.main()
