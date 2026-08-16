import json
import re
import unittest

from tests.surface_test_lib import REPO_ROOT, load_script_module, read, read_jsonl

API_SKILL = REPO_ROOT / "souroldgeezer-design" / "skills" / "api-design"
API_REFERENCE = REPO_ROOT / "souroldgeezer-design" / "docs" / "api-reference" / "api-design.md"
# api-design's Load Map also cites the shared design core, which lives outside the
# skill dir, so an rglob of the skill dir alone understates the real closure.
PAIRING_CORE = (
    REPO_ROOT / "souroldgeezer-design" / "docs" / "design-reference"
    / "architecture-pairing-core.md"
)
LOAD_COST_SCRIPT = (
    REPO_ROOT
    / "souroldgeezer-audit"
    / "skills"
    / "lean-audit"
    / "references"
    / "scripts"
    / "skill_load_cost.py"
)
STACKS = (
    "azure-functions-dotnet",
    "nodejs",
    "nextjs",
    "azure-cosmosdb",
    "azure-blob-storage",
    "python",
)
CONCRETE_CODE = re.compile(
    r"(?:afdotnet|nodejs|nextjs|cosmos|blob|pyapi)\.(?:PAT|HC|LC|POS)-[a-z0-9-]+"
)
PATTERN_CODE = re.compile(r"(?:afdotnet|nodejs|nextjs|cosmos|blob|pyapi)\.PAT-[a-z0-9-]+")
REVIEW_CODE = re.compile(r"(?:afdotnet|nodejs|nextjs|cosmos|blob|pyapi)\.(?:HC|LC|POS)-\d+")


class ApiDesignModeSlicingTest(unittest.TestCase):
    def test_stack_cores_and_lanes_have_disjoint_code_ownership(self) -> None:
        for stack in STACKS:
            with self.subTest(stack=stack):
                core_path = API_SKILL / "extensions" / f"{stack}.md"
                build_path = API_SKILL / "extensions" / stack / "build.md"
                review_path = API_SKILL / "extensions" / stack / "review.md"
                core = core_path.read_text(encoding="utf-8")
                build = build_path.read_text(encoding="utf-8")
                review = review_path.read_text(encoding="utf-8")

                self.assertEqual(CONCRETE_CODE.findall(core), [])
                self.assertTrue(PATTERN_CODE.search(build), stack)
                self.assertFalse(REVIEW_CODE.search(build), stack)
                self.assertTrue(REVIEW_CODE.search(review), stack)
                self.assertFalse(PATTERN_CODE.search(review), stack)
                self.assertIn(f"{stack}/build.md", core)
                self.assertIn(f"{stack}/review.md", core)

    def test_router_declares_each_mode_and_bounded_lookup(self) -> None:
        skill = read("souroldgeezer-design/skills/api-design/SKILL.md")

        self.assertLessEqual(len(skill.splitlines()), 150)
        required_route_phrases = (
            "Build:** load every matching core",
            "Review:** load every matching core",
            "Extract:** load matching cores only",
            "Node.js followed by Next.js counts as one composed base",
            "at most its one relevant",
            "escalate to Review or Build",
        )
        self.assertTrue(all(phrase in skill for phrase in required_route_phrases))

    def test_declared_cost_routes_encode_mode_exclusions(self) -> None:
        scenarios = json.loads(read("tests/skill_load_cost/scenarios.json"))
        by_id = {scenario["id"]: scenario for scenario in scenarios}

        def targets(scenario_id: str) -> set[str]:
            scenario = by_id[scenario_id]
            self.assertNotIn("files", scenario)
            return {route["target"] for route in scenario["load_routes"]}

        lookup = targets("lookup-functions")
        build = targets("build-functions-cosmos")
        review = targets("review-functions-cosmos-blob")
        factual = targets("extract-functions-cosmos-factual")
        debt = targets("extract-functions-cosmos-debt")
        surface = targets("review-surface-architecture")

        self.assertTrue(
            any("api-design.md#" in target for target in lookup),
            "Lookup must charge an anchored reference subtree",
        )
        self.assertFalse(any("/build.md" in target or "/review.md" in target for target in lookup))
        self.assertTrue(any("/build.md" in target for target in build))
        self.assertFalse(any("/review.md" in target for target in build))
        self.assertTrue(any("/review.md" in target for target in review))
        self.assertFalse(any("/build.md" in target for target in review))
        self.assertFalse(any("/build.md" in target or "/review.md" in target for target in factual))
        self.assertTrue(any("/review.md" in target for target in debt))
        self.assertFalse(any("/build.md" in target for target in debt))
        self.assertIn(
            "souroldgeezer-design/skills/api-design/references/procedures/surface-architecture.md",
            surface,
        )
        self.assertFalse(any("/build.md" in target or "/review.md" in target for target in surface))

    def test_full_api_closure_preserves_fidelity_baseline(self) -> None:
        slc = load_script_module("api_design_mode_slicing_load_cost", LOAD_COST_SCRIPT)
        patterns = json.loads(read("tests/skill_load_cost/code_patterns.json"))
        baseline = json.loads(read("tests/skill_load_cost/baselines/api-design.json"))
        paths = [API_REFERENCE, PAIRING_CORE, *sorted(API_SKILL.rglob("*.md"))]
        current = slc.union_inventory(
            [slc.extract_inventory(path.read_text(encoding="utf-8"), patterns) for path in paths]
        )

        missing_codes = sorted(set(baseline["codes"]) - set(current["codes"]))
        missing_sections = sorted(set(baseline["sections"]) - set(current["sections"]))
        self.assertEqual(missing_codes, [])
        self.assertEqual(missing_sections, [])
        self.assertGreaterEqual(len(current["codes"]), 218)
        self.assertGreaterEqual(len(current["sections"]), 210)

    def test_mode_routing_has_behavior_eval_coverage(self) -> None:
        cases = {
            case["id"]: case
            for case in read_jsonl(
                "souroldgeezer-design/skills/api-design/references/evals/behavior-cases.jsonl"
            )
        }
        self.assertIn("api-design-behavior-extract-factual-core-only", cases)
        self.assertIn("api-design-behavior-extract-explicit-debt", cases)
        self.assertIn(
            "exclude both Build and Review lanes",
            cases["api-design-behavior-extract-factual-core-only"]["required_checks"],
        )
        self.assertIn(
            "exclude Build lanes",
            cases["api-design-behavior-extract-explicit-debt"]["required_checks"],
        )


if __name__ == "__main__":
    unittest.main()
