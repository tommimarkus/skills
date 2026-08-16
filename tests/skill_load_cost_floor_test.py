# tests/skill_load_cost_floor_test.py
"""Every committed fidelity baseline must remain a valid floor for its skill.

The floor invariant is `baseline ⊆ current closure`: a code, section, or pointer
recorded in the baseline must still be reachable. Losing one is the silent
fidelity regression `load_cost_guard.py` exists to stop.

Why a suite test and not the runtime guard — the same reasoning
`skill_load_cost_freshness_test.py` gives for the cost snapshot. The guard's Stop
path enumerates only the `.md` files changed *that session* and maps each to its
owning skill, so it is structurally incapable of noticing that an untouched
skill's floor has been breached. A loss in a skill nobody edited this session
stays invisible until someone happens to edit it. Re-checking every committed
baseline each suite run closes that hole.

Deliberately a **subset** assertion, not equality. Equality would force a
baseline regeneration on every content addition — churn that fights the floor
semantics, since gaining sections never weakens protection. Staleness (a floor
lower than achievable) is reported by `test_floors_are_not_drifting_far` as a
soft signal, and refreshed deliberately with `skill_load_cost.py baseline`.

Compare inventories as **sets**. An ordered diff of the `sections` arrays reports
pure reordering as add/remove pairs, which once produced a false "section has gone
unreachable" report; `diff_inventory` below is set-based and is the same function
the guard uses.
"""
import json
import unittest

from tests.surface_test_lib import REPO_ROOT, load_script_module

SCRIPT = (REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit"
          / "references" / "scripts" / "skill_load_cost.py")
slc = load_script_module("skill_load_cost_floor", SCRIPT)

COST_DIR = REPO_ROOT / "tests" / "skill_load_cost"
BASELINES = COST_DIR / "baselines"
CODE_PATTERNS = COST_DIR / "code_patterns.json"

# A floor this far below its closure is stale enough to be worth refreshing.
# Not a correctness bound — protection is still valid, just lower than achievable.
STALENESS_ALLOWANCE = 24


def skill_md_for(name: str):
    """Locate a published SKILL.md by directory name, as the guard does."""
    matches = [
        p for p in REPO_ROOT.glob("souroldgeezer-*/skills/*/SKILL.md")
        if p.parent.name == name
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one SKILL.md for {name!r}, found {matches}")
    return matches[0]


def current_inventory(name: str):
    patterns = json.loads(CODE_PATTERNS.read_text(encoding="utf-8"))
    files = slc.resolve_closure(skill_md_for(name))
    return slc.union_inventory(
        [slc.extract_inventory(f.read_text(encoding="utf-8"), patterns) for f in files]
    )


def committed_baselines() -> list[str]:
    return sorted(p.stem for p in BASELINES.glob("*.json"))


class SkillLoadCostFloorTest(unittest.TestCase):
    def test_there_are_committed_baselines_to_check(self) -> None:
        """Guards the loops below from passing vacuously if the directory empties."""
        self.assertGreaterEqual(len(committed_baselines()), 9)

    def test_every_committed_baseline_is_still_a_valid_floor(self) -> None:
        for name in committed_baselines():
            baseline = json.loads((BASELINES / f"{name}.json").read_text(encoding="utf-8"))
            with self.subTest(skill=name):
                problems = slc.diff_inventory(baseline, current_inventory(name))
                self.assertEqual(
                    problems,
                    [],
                    f"{name}: fidelity floor breached — "
                    f"{len(problems)} item(s) recorded in the baseline are no longer "
                    f"reachable from the skill's closure. Restore them, or lower the "
                    f"floor deliberately by regenerating the baseline.",
                )

    def test_floors_are_not_drifting_far(self) -> None:
        """Soft staleness signal: a floor far below its closure protects less than it could."""
        for name in committed_baselines():
            baseline = json.loads((BASELINES / f"{name}.json").read_text(encoding="utf-8"))
            current = current_inventory(name)
            gained = len(set(current["sections"]) - set(baseline["sections"]))
            with self.subTest(skill=name):
                self.assertLessEqual(
                    gained,
                    STALENESS_ALLOWANCE,
                    f"{name}: closure has {gained} sections the committed floor omits. "
                    f"Refresh it in the change that added them: "
                    f"skill_load_cost.py baseline --files $(resolve_closure ...) "
                    f"--code-patterns {CODE_PATTERNS.name} --out baselines/{name}.json",
                )


if __name__ == "__main__":
    unittest.main()
