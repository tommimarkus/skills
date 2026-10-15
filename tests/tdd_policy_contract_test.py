"""Keep RED-test selection, refactor classification, execution scope, suite
maintenance, and the feedback budget explicit in the public TDD policy contract."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TDD_ROOT = ROOT / "souroldgeezer-policy/skills/tdd-policy"
AGENT = ROOT / "souroldgeezer-policy/agents/tdd-policy.md"
PLANNING_CORE = ROOT / "souroldgeezer-policy/skills/planning-policy/references/core-workflow.md"
TEST_QUALITY_SKILL = ROOT / "souroldgeezer-audit/skills/test-quality-audit/SKILL.md"

NEW_BEHAVIOR_CASES = {
    "tdd-policy-behavior-covered-refactor-no-red": "existing passing tests",
    "tdd-policy-behavior-characterize-before-refactor": "characterization",
    "tdd-policy-behavior-requirement-change-updates-expectation": "rationale",
    "tdd-policy-behavior-red-level-cheapest": "cheapest",
    "tdd-policy-behavior-integration-seam-retained": "seam",
    "tdd-policy-behavior-parameter-partitions": "partition",
    "tdd-policy-behavior-focused-execution-scope": "focused",
    "tdd-policy-behavior-budget-breach-consolidate": "budget",
    "tdd-policy-behavior-budget-inherited-or-absent": "inherit",
    "tdd-policy-behavior-refactor-retires-superseded": "successor",
    "tdd-policy-behavior-retirement-evidence-insufficient": "retain",
    "tdd-policy-behavior-delegated-parent-consolidation": "integration",
    "tdd-policy-behavior-reuse-shared-helper": "shared",
    "tdd-policy-behavior-setup-lifetime-immutable-only": "immutable",
    "tdd-policy-behavior-no-fixed-sleep": "condition",
    "tdd-policy-behavior-machine-format-hostile-locale": "locale",
    "tdd-policy-behavior-human-format-explicit-locale": "explicit",
    "tdd-policy-behavior-env-locale-assert-applied": "took effect",
    "tdd-policy-behavior-minimal-input": "smallest",
    "tdd-policy-behavior-lane-marker": "lane",
    "tdd-policy-behavior-green-duration-slow-tail": "duration",
    "tdd-policy-behavior-stack-idioms-fallback": "software-design",
}


def flat(text: str) -> str:
    """Collapse wrapping so multi-word phrases can be asserted across line breaks."""
    return " ".join(text.split())


def description(path: Path) -> str:
    """Read the single-line quoted `description:` from a Markdown frontmatter block."""
    text = path.read_text(encoding="utf-8")
    _, block, _ = text.split("---\n", 2)
    match = re.search(r'^description:\s*"(.*)"\s*$', block, re.M)
    assert match, f"{path} has no single-line quoted description"
    return match.group(1)


class TddPolicyContractTest(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def core(self) -> str:
        return (TDD_ROOT / "references/core-workflow.md").read_text(encoding="utf-8")

    def skill(self) -> str:
        return (TDD_ROOT / "SKILL.md").read_text(encoding="utf-8")

    def jsonl_cases(self, relative: str) -> dict[str, dict[str, object]]:
        path = TDD_ROOT / relative
        return {
            case["id"]: case
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
            for case in (json.loads(line),)
        }

    def behavior_cases(self) -> dict[str, dict[str, object]]:
        return self.jsonl_cases("references/evals/behavior-cases.jsonl")

    def test_core_selects_red_from_existing_tests_first(self) -> None:
        core = self.core()
        for phrase in (
            "## Selecting the RED test",
            "Inspect the existing tests before choosing",
            "Minimally extend a suitable existing test",
            "without removing or weakening its coverage",
            "Create a new test when the behavior is distinct",
            "reuse would make the test unclear",
            "precisely represents the intended behavior",
            "Unrelated failures do not establish RED",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, core)

    def test_core_adds_value_and_cost_axes_to_red_selection(self) -> None:
        core = flat(self.core())
        for phrase in (
            "already detects the regression",
            "distinct behavioral obligation or failure mode",
            "cheapest level that proves",
            "in-process unit",
            "child process / CLI",
            "equivalence-partition representatives and boundaries, not combinatorial products",
            "existing fixtures and helpers",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, core)

    def test_core_invariant_distinguishes_refactor_and_keeps_one_covering_test(self) -> None:
        core = flat(self.core())
        for phrase in (
            "## Invariant",
            "New or changed observable behavior is preceded by a focused failing test",
            "Behavior-preserving refactors run under existing passing tests",
            "bounded characterization coverage only where protection is missing",
            "a failure is never manufactured to satisfy TDD",
            "REFACTOR consolidates or retires superseded coverage",
            "at least one test that would fail if it regressed",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, core)

    def test_core_has_the_new_sections(self) -> None:
        core = self.core()
        for heading in (
            "## Behavioral change or refactor",
            "## Execution scope",
            "## REFACTOR includes the suite",
            "## Delegated work",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, core)
        flat_core = flat(core)
        self.assertIn("never per RED/GREEN step", flat_core)
        self.assertIn("name the successor", flat_core)
        self.assertIn("verify-then-retire", flat_core)
        self.assertIn("parent runs the suite step once", flat_core)

    def test_core_states_stack_neutral_test_authoring_rules(self) -> None:
        core = flat(self.core())
        for phrase in (
            "## Writing the test",
            "Reuse before define",
            "shared test-support surface",
            "defaulted parameter",
            "moves into the shared surface in the same cycle",
            "immutable or safely resettable",
            "cleanup that runs even when the test fails",
            "No fixed sleeps or real clocks",
            "observable condition with a bounded timeout",
            "must not depend on the runner's locale",
            "assert it took effect",
            "Expected values never come from the authoring environment",
            "smallest fixture that exhibits the behavior",
            "no order dependence",
            "lane marker, tag, or location",
            "loaded once per task",
            "`stack idioms: n/a`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, core)

    def test_core_red_can_fail_where_it_runs_and_green_reads_duration(self) -> None:
        core = flat(self.core())
        for phrase in (
            "must be able to fail where it runs",
            "comma-decimal locale",
            "For machine-facing output",
            "the locale is an explicit test input",
            "read the new test's duration",
            "slow tail",
            "record the duration only",
            "duplication detector",
            "names the shared test-support paths in each worker's reads",
            "Language-specific test-code idioms → `software-design`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, core)

    def test_standing_block_and_footer_carry_test_authoring(self) -> None:
        core = flat(re.sub(r"(?m)^> ", "", self.core()))  # the template wraps as a blockquote
        for phrase in (
            "Tests reuse the suite's shared fixtures and helpers, share only immutable setup, "
            "and never depend on real sleeps, clocks, or the machine's locale or timezone.",
            "cost <duration|unknown>[: reason]",
            "stack idioms <software-design:<stack>|n/a>",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, core)
        skill = flat(self.skill())
        for phrase in ("Writing the test", "test-code idioms", "duration", "stack idioms"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill)

    def test_software_design_is_referenced_by_name_never_by_path(self) -> None:
        for path in sorted(TDD_ROOT.rglob("*")):
            if path.is_file():
                with self.subTest(path=path.relative_to(TDD_ROOT).as_posix()):
                    text = path.read_text(encoding="utf-8")
                    self.assertNotIn("souroldgeezer-design", text)
                    self.assertNotRegex(text, r"extensions/\S*test-code")

    def test_standing_block_carries_level_retirement_and_budget(self) -> None:
        core = flat(self.core())
        for phrase in (
            "cheapest level that proves it; refactors run under existing passing tests",
            "REFACTOR retires or consolidates superseded coverage",
            "at least one test that fails on regression",
            "Budget <lane: value|inherited|none>",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, core)

    def test_feedback_budget_option_has_both_loop_ends(self) -> None:
        core = flat(self.core())
        self.assertIn("`feedback-budget`", core)
        for phrase in (
            "`feedback-budget` none",
            "inherited",
            "declared budget",
            "never new telemetry",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, core)

    def test_footer_discloses_change_level_scope_delta_and_retirement(self) -> None:
        core = self.core()
        for field in (
            "change <behavioral|refactor|requirement-change>",
            "level <unit|in-process|child-process|e2e>",
            "ran <focused|affected|full>",
            "suite delta <+n/−m tests",
            "retired: <list|none>",
        ):
            with self.subTest(field=field):
                self.assertIn(field, core)

    def test_skill_stop_rules_exempt_refactors_and_hold_green_over_budget(self) -> None:
        skill = flat(self.skill())
        for phrase in (
            "Stop before letting new or changed behavior land with no failing test first",
            "a behavior-preserving refactor under existing passing tests is not a breach",
            "Stop before GREEN lands in a lane at or over its budget",
            "parent runs the suite step once",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill)

    def test_skill_and_agent_descriptions_match_and_name_the_budget(self) -> None:
        skill_description = description(TDD_ROOT / "SKILL.md")
        agent_description = description(AGENT)
        self.assertEqual(skill_description, agent_description)
        for phrase in (
            "behavioral-change vs refactor classification",
            "RED test level and placement",
            "execution scope",
            "suite feedback budget",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill_description)
        self.assertLessEqual(len(skill_description), 1024)

    def test_synthetic_cases_cover_reuse_and_new_test_branches(self) -> None:
        cases = self.behavior_cases()
        reuse = cases["tdd-policy-behavior-reuse-cohesive-test"]
        create = cases["tdd-policy-behavior-create-distinct-test"]

        self.assertEqual(reuse["source_kind"], "synthetic")
        self.assertEqual(create["source_kind"], "synthetic")
        self.assertTrue(
            any("inspect existing tests" in check.lower() for check in reuse["required_checks"])
        )
        self.assertTrue(
            any("preserve" in check.lower() for check in reuse["required_checks"])
        )
        self.assertTrue(
            any("distinct" in check.lower() for check in create["required_checks"])
        )
        self.assertTrue(
            any("rationale" in artifact.lower() for artifact in create["expected_artifacts"])
        )

    def test_synthetic_cases_cover_each_cost_aware_rule(self) -> None:
        cases = self.behavior_cases()
        for case_id, keyword in NEW_BEHAVIOR_CASES.items():
            with self.subTest(case=case_id):
                self.assertIn(case_id, cases)
                case = cases[case_id]
                self.assertEqual(case["source_kind"], "synthetic")
                self.assertTrue(case.get("ip_handling"))
                self.assertTrue(
                    any(keyword in check.lower() for check in case["required_checks"]),
                    f"{case_id} needs a required check mentioning {keyword!r}",
                )
                self.assertTrue(case["forbidden_behaviors"])

    def test_trigger_cases_split_budgeted_tdd_from_suite_runtime_audit(self) -> None:
        triggers = self.jsonl_cases("references/evals/trigger-cases.jsonl")
        self.assertTrue(triggers["tdd-policy-trigger-yes-initialized-budget"]["expected_activation"])
        self.assertFalse(triggers["tdd-policy-trigger-no-suite-runtime-audit"]["expected_activation"])

    def test_source_grounding_records_selection_rationale(self) -> None:
        grounding = flat((TDD_ROOT / "references/source-grounding.md").read_text(encoding="utf-8"))
        for phrase in (
            "cohesive existing scenario",
            "distinct scenario",
            "clarity or regression coverage",
            "characterization",
            "slow tail",
            "feedback budget",
            "inherited",
            "verify-then-retire",
            "Test Desiderata",
            "testing.googleblog.com",
            "decimal separator",
            "by skill name",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, grounding)

    def test_sibling_boundaries_name_the_handoff(self) -> None:
        planning = flat(PLANNING_CORE.read_text(encoding="utf-8"))
        self.assertIn(
            "When tdd-policy is in force, the parent runs its suite step once", planning
        )
        audit = flat(TEST_QUALITY_SKILL.read_text(encoding="utf-8"))
        self.assertIn("in-cycle retirement", audit)
        self.assertIn("informational alone", audit)

    def test_public_guidance_summarizes_existing_test_inspection(self) -> None:
        for relative in ("AGENTS.md", "CLAUDE.md"):
            with self.subTest(relative=relative):
                guidance = flat(self.text(relative))
                self.assertIn("Inspect existing tests before selecting the RED test", guidance)
                self.assertIn("cheapest level", guidance)
                self.assertIn("REFACTOR includes the suite", guidance)
                self.assertIn("`tests/surface_test_lib.py` helpers before defining new ones", guidance)
                self.assertIn("share only immutable setup", guidance)


if __name__ == "__main__":
    unittest.main()
