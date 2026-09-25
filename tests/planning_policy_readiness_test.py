import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).parents[1]
    / "souroldgeezer-policy/skills/planning-policy/references/scripts/validate_plan_contract.py"
)
SPEC = importlib.util.spec_from_file_location("plan_contract", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def leaf(identifier, unit, *, reads=None, writes=None, dependencies=None, owner=None):
    return {
        "id": identifier,
        "dependencies": dependencies or [],
        "task": "Implement one bounded concern",
        "boundary": "Do not edit other concerns",
        "read_set": ["inputs/source.py"] if reads is None else reads,
        "write_set": [f"outputs/{identifier}.py"] if writes is None else writes,
        "settled_decisions": {"shape": "chosen"},
        "size": "medium",
        "portable_tier": "standard",
        "worktree_owner": owner or f"task/{identifier}",
        "acceptance_command": "uv run python -m unittest tests.example",
        "return_contract": "bounded-step-return-v1",
        "stop_conditions": ["missing_load_bearing_information"],
        "work_unit_id": unit,
        "max_attempts": 2,
        "capability_requirements": {"baseline": "plan-step-base-v1", "additional": []},
    }


def plan(*leaves):
    return {
        "contract_version": 5,
        "objective": "Implement the approved bounded change",
        "scope_summary": "Only the assigned source and focused tests are in scope.",
        "approved_decisions": ["Use the settled contract shape."],
        "work_units": [
            {
                "id": item["work_unit_id"],
                "original_size": "medium",
                "cohesive_outcome": f"Deliver {item['work_unit_id']} as one reviewable outcome",
                "decomposition": {"shape": "single"},
            }
            for item in leaves
        ],
        "leaves": list(leaves),
    }


class ReadinessAdmissionTest(unittest.TestCase):
    def test_rejects_unsafe_duplicate_and_empty_io_sets(self):
        subject = leaf("one", "u1", reads=["input.py", "input.py"], writes=[])
        result = MODULE.validate(plan(subject))
        self.assertFalse(result["valid"])
        self.assertTrue(any("read_set" in error and "unique" in error for error in result["errors"]))

        subject = leaf("one", "u1", reads=[], writes=[])
        result = MODULE.validate(plan(subject))
        self.assertFalse(result["valid"])
        self.assertTrue(any("both be empty" in error for error in result["errors"]))

        subject = leaf("one", "u1", reads=["../outside.py"], writes=["output.py"])
        result = MODULE.validate(plan(subject))
        self.assertFalse(result["valid"])
        self.assertTrue(any("safe repository-relative" in error for error in result["errors"]))

        for path in (17, {}, "", "/absolute", "a/../b", "a\\b", "x" * 241):
            with self.subTest(path=path):
                self.assertFalse(MODULE.validate(plan(leaf("one", "u1", reads=[path])))["valid"])
        read_only = leaf("one", "u1", reads=["x" * 240], writes=[])
        self.assertTrue(MODULE.validate(plan(read_only))["valid"])

    def test_rejects_placeholder_decisions_and_noop_acceptance(self):
        subject = leaf("one", "u1")
        subject["settled_decisions"] = {"shape": "TBD"}
        subject["acceptance_command"] = "true"
        result = MODULE.validate(plan(subject))
        self.assertFalse(result["valid"])
        self.assertTrue(any("placeholder" in error for error in result["errors"]))
        self.assertTrue(any("no-op" in error for error in result["errors"]))

        shared = plan(leaf("one", "u1"))
        shared["approved_decisions"] = ["TBD"]
        self.assertFalse(MODULE.validate(shared)["valid"])

    def test_requires_order_for_overlapping_write_coverage_and_shared_worktrees(self):
        first = leaf("one", "u1", writes=["src/package"])
        second = leaf("two", "u2", writes=["src/package/module.py"])
        result = MODULE.validate(plan(first, second))
        self.assertFalse(result["valid"])
        self.assertTrue(any("overlapping write coverage" in error for error in result["errors"]))

        second["dependencies"] = ["one"]
        result = MODULE.validate(plan(first, second))
        self.assertTrue(result["valid"], result["errors"])

        second = leaf("two", "u2", writes=["other/module.py"], owner="task/one")
        first["worktree_owner"] = "task/one"
        result = MODULE.validate(plan(first, second))
        self.assertFalse(result["valid"])
        self.assertTrue(any("shared worktree_owner" in error for error in result["errors"]))

        middle = leaf("middle", "u3", dependencies=["one"])
        second["dependencies"] = ["middle"]
        self.assertTrue(MODULE.validate(plan(first, middle, second))["valid"])
        shared_reads = plan(leaf("a", "ua"), leaf("b", "ub"))
        self.assertTrue(MODULE.validate(shared_reads)["valid"])

    def test_conservative_globs_and_retained_admission_mode(self):
        first = leaf("one", "u1", writes=["src/*.py"])
        second = leaf("two", "u2", writes=["src/module.py"])
        result = MODULE.validate(plan(first, second))
        self.assertFalse(result["valid"])
        self.assertTrue(any("overlapping write coverage" in error for error in result["errors"]))

        retained = leaf("one", "u1", reads=[], writes=[])
        retained["acceptance_command"] = ":"
        self.assertFalse(MODULE.validate(plan(retained))["valid"])
        self.assertTrue(MODULE.validate(plan(retained), admission=False)["valid"])
