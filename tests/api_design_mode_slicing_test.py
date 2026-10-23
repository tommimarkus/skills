import json
import re
import unittest

from tests.surface_test_lib import REPO_ROOT, read, read_jsonl

API_SKILL = REPO_ROOT / "souroldgeezer-design" / "skills" / "api-design"
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

    def test_router_keeps_stack_reference_targets_available(self) -> None:
        skill = read("souroldgeezer-design/skills/api-design/SKILL.md")

        self.assertLessEqual(len(skill.splitlines()), 150)
        for stack in STACKS:
            with self.subTest(stack=stack):
                for relative in (f"extensions/{stack}.md", f"extensions/{stack}/build.md", f"extensions/{stack}/review.md"):
                    self.assertIn(relative, skill)
                    self.assertTrue((API_SKILL / relative).is_file())

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
            "avoid unrelated Build and Review detail for a factual baseline",
            cases["api-design-behavior-extract-factual-core-only"]["required_checks"],
        )
        self.assertIn(
            "avoid unrelated Build detail for the requested judgment",
            cases["api-design-behavior-extract-explicit-debt"]["required_checks"],
        )
        for case_id in (
            "api-design-behavior-project-compatible-contract",
            "api-design-behavior-contract-exception-safety-control",
            "api-design-behavior-lookup-composed-excerpts",
        ):
            with self.subTest(case_id=case_id):
                self.assertIn(case_id, cases)
                self.assertTrue(cases[case_id]["required_checks"])
                self.assertTrue(cases[case_id]["forbidden_behaviors"])



if __name__ == "__main__":
    unittest.main()
