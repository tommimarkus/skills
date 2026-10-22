"""Keep RED-test selection, the declared seam, change classification, execution
scope, suite maintenance and retention, and the feedback budget explicit in the
public TDD policy contract."""

import json
from pathlib import Path
import re
import unittest

from tests.surface_test_lib import assert_phrases


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
    "tdd-policy-behavior-seam-internal-change-is-refactor": "seam",
    "tdd-policy-behavior-structure-coupled-test-rewritten-at-seam": "at the seam",
    "tdd-policy-behavior-scaffold-resolved-before-green": "before green",
    "tdd-policy-behavior-trivial-code-no-red": "trivial",
    "tdd-policy-behavior-controller-short-integration": "integration",
    "tdd-policy-behavior-overcomplicated-split-first": "split",
    "tdd-policy-behavior-behavior-removal-deletes-tests": "delete",
    "tdd-policy-behavior-characterization-expires": "below the seam",
    "tdd-policy-behavior-examples-per-rule": "per rule",
    "tdd-policy-behavior-mutation-unique-kill": "mutant",
    "tdd-policy-behavior-refactor-edits-listed-structure-coupled": "structure-coupled",
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

    def standing_block(self) -> str:
        """The template section, with its blockquote markers stripped."""
        core = self.core()
        section = core.split("## Standing block template", 1)[1].split("\n## ", 1)[0]
        return flat(re.sub(r"(?m)^> ", "", section))

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
        block = self.standing_block()
        for phrase in (
            "new or changed behavior at the seam gets a focused failing test first",
            "at the cheapest level that proves it through the seam",
            "a change with no effect at the seam is a refactor and runs under existing passing tests",
            "trivial wiring, delegation, accessors, and declarative config get no RED of their own",
            "REFACTOR retires or consolidates superseded coverage and resolves scaffold tests "
            "before GREEN lands",
            "removing a behavior removes its tests",
            "at least one test that fails on regression",
            "Seam <rule|public API of each module>.",
            "Budget <lane: value|inherited|none>",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, block)

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
            "seam <declared rule|public API>",
            "change <behavioral|refactor|trivial|requirement-change|behavior-removal>",
            "level <unit|in-process|child-process|e2e>",
            "ran <focused|affected|full>",
            "suite delta <+n/−m tests",
            "mutation <n unique kills|n/a>",
            "scaffold: <name: rewritten|deleted|none>",
            "structure-coupled: <list|none>",
            "retired: <list|none>",
        ):
            with self.subTest(field=field):
                self.assertIn(field, core)
        flat_core = flat(core)
        for marker in ("`behavior removed`", "`characterization expired`"):
            with self.subTest(marker=marker):
                self.assertIn(marker, flat_core)

    def test_skill_stop_rules_exempt_refactors_and_hold_green_over_budget(self) -> None:
        skill = flat(self.skill())
        for phrase in (
            "Stop before letting new or changed behavior at the seam land with no failing test first",
            "a behavior-preserving refactor under existing passing tests is not a breach",
            "neither is trivial code",
            "Stop before GREEN lands in a lane at or over its budget",
            "Stop before GREEN lands with an unresolved scaffold test",
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
            "seam",
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
            "Cooper",
            "public API",
            "Khorikov",
            "resistance to refactoring",
            "private method",
            "sunk cost",
            "cucumber.io",
            "Canon TDD",
            "mutation",
            "Noemmer",
            "structure-coupled",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, grounding)

    def test_core_measures_observable_behavior_at_a_declared_seam(self) -> None:
        core = flat(self.core())
        for phrase in (
            "cheapest level that proves it through the declared seam",
            "A change with no effect visible at the seam is a refactor",
            "cheapest level that proves the behavior through the seam",
            "- `seam` —",
            "public API of each module or package",
            "not individual functions or classes",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, core)

    def test_invariant_coverage_clause_survives_removal_and_scaffold_deletion(self) -> None:
        invariant = flat(self.core().split("## Invariant", 1)[1].split("\n## ", 1)[0])
        for phrase in (
            "Behavior removal and scaffold deletion keep this clause",
            "no longer shipped",
            "never pinned seam behavior",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, invariant)

    def test_core_classifies_trivial_code_and_behavior_removal(self) -> None:
        assert_phrases(self, self.core(), (
            "**Trivial code**",
            "no RED of its own",
            "a classification, not an exception",
            "domain logic and algorithms",
            "controllers",
            "split it first",
            "**Behavior removal**",
            "delete the removed behavior's tests in the same change",
            "no successor",
        ), heading="## Behavioral change or refactor")

    def test_core_retention_check_scaffolds_and_characterization_expiry(self) -> None:
        assert_phrases(self, self.core(), (
            "Would a behavior-preserving refactor force this test to change?",
        ), heading="## Selecting the RED test")
        assert_phrases(self, self.core(), (
            "scaffold test",
            "Resolve every scaffold test",
            "no supersession proof",
            "GREEN does not land with an unresolved scaffold test",
            "characterization tests it added below the seam",
            "at the seam stay",
        ), heading="## REFACTOR includes the suite")
        assert_phrases(self, self.core(), (
            "resolves its own scaffold tests",
        ), heading="## Delegated work")

    def test_core_bounds_examples_per_rule_and_uses_mutation_evidence(self) -> None:
        assert_phrases(self, self.core(), (
            "a few key examples per rule",
            "property-based test",
            "stay declarative",
            "kills a mutant no existing test kills",
        ), heading="## Selecting the RED test")

    def test_core_records_structure_coupled_tests_for_the_audit(self) -> None:
        refactor = flat(self.core().split("## REFACTOR includes the suite", 1)[1].split("\n## ", 1)[0])
        for phrase in ("structure-coupled", "verify-then-retire"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, refactor)

    def test_skill_rules_carry_the_seam_invariant_and_evidence(self) -> None:
        skill = flat(self.skill())
        for phrase in (
            "at the cheapest level that proves it through the seam",
            "a change with no effect at the seam is a refactor",
            "trivial wiring, delegation, accessors, and declarative config get no RED of their own",
            "resolves scaffold tests before GREEN lands",
            "removing a behavior removes its tests",
            "the seam in force",
            "structure-coupled",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill)

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
