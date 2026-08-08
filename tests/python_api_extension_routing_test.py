import json
import unittest

from tests.surface_test_lib import REPO_ROOT, read, read_jsonl

API_SKILL = "souroldgeezer-design/skills/api-design"
SCENARIOS = REPO_ROOT / "tests" / "skill_load_cost" / "scenarios.json"


class PythonApiExtensionRoutingTest(unittest.TestCase):
    def test_router_and_claude_agent_advertise_python_without_owning_internals(self) -> None:
        skill = read(f"{API_SKILL}/SKILL.md")
        agent = read("souroldgeezer-design/agents/api-design.md")
        inventory = read(f"{API_SKILL}/extensions/README.md")

        self.assertIn("extensions/python.md", skill)
        self.assertIn("Python ASGI / WSGI", skill)
        self.assertIn("Python", agent)
        self.assertIn("python.md", inventory)
        self.assertIn("python/build.md", inventory)
        self.assertIn("python/review.md", inventory)
        self.assertIn("software-design", skill)
        self.assertIn("not general Python design", read(f"{API_SKILL}/extensions/python.md"))

    def test_python_routes_keep_extract_build_review_and_lookup_slices_disjoint(self) -> None:
        scenarios = {
            scenario["id"]: scenario
            for scenario in json.loads(SCENARIOS.read_text(encoding="utf-8"))
            if scenario.get("skill") == "api-design"
        }

        expected = {
            "extract-python-factual": "factual",
            "extract-python-debt": "debt",
            "lookup-python-lifecycle": "lookup",
            "build-python-asgi": "build",
            "review-python-wsgi-clean": "review",
            "review-python-serverless": "review",
        }
        self.assertTrue(set(expected).issubset(scenarios))

        def targets(scenario_id: str) -> set[str]:
            return {route["target"] for route in scenarios[scenario_id]["load_routes"]}

        factual = targets("extract-python-factual")
        debt = targets("extract-python-debt")
        lookup = targets("lookup-python-lifecycle")
        build = targets("build-python-asgi")
        wsgi = targets("review-python-wsgi-clean")
        serverless = targets("review-python-serverless")

        self.assertIn("extensions/python.md", " ".join(factual))
        self.assertFalse(
            any(
                "python/build.md" in target or "python/review.md" in target
                for target in factual
            )
        )
        self.assertIn("extensions/python/review.md", " ".join(debt))
        self.assertFalse(any("extensions/python/build.md" in target for target in debt))
        self.assertLessEqual(sum("extensions/python/" in target for target in lookup), 1)
        self.assertIn("extensions/python/build.md", " ".join(lookup))
        self.assertIn("extensions/python/build.md", " ".join(build))
        self.assertFalse(any("extensions/python/review.md" in target for target in build))
        for review in (wsgi, serverless):
            with self.subTest(review=review):
                self.assertIn("extensions/python/review.md", " ".join(review))
                self.assertFalse(any("extensions/python/build.md" in target for target in review))

    def test_python_eval_cases_cover_mode_routing_and_false_positive_controls(self) -> None:
        triggers = {
            case["id"]: case
            for case in read_jsonl(f"{API_SKILL}/references/evals/trigger-cases.jsonl")
        }
        behavior = {
            case["id"]: case
            for case in read_jsonl(f"{API_SKILL}/references/evals/behavior-cases.jsonl")
        }
        self.assertTrue(triggers["api-design-trigger-yes-python-asgi-build"]["expected_activation"])
        self.assertTrue(triggers["api-design-trigger-yes-python-serverless-review"]["expected_activation"])
        self.assertFalse(triggers["api-design-trigger-no-python-internals"]["expected_activation"])

        required = {
            "api-design-behavior-python-extract-factual",
            "api-design-behavior-python-extract-explicit-debt",
            "api-design-behavior-python-lookup-bounded",
            "api-design-behavior-python-build-hosted-asgi",
            "api-design-behavior-python-review-wsgi-clean",
            "api-design-behavior-python-review-serverless",
        }
        self.assertTrue(required.issubset(behavior))
        factual = behavior["api-design-behavior-python-extract-factual"]
        debt = behavior["api-design-behavior-python-extract-explicit-debt"]
        lookup = behavior["api-design-behavior-python-lookup-bounded"]
        build = behavior["api-design-behavior-python-build-hosted-asgi"]
        wsgi = behavior["api-design-behavior-python-review-wsgi-clean"]
        serverless = behavior["api-design-behavior-python-review-serverless"]
        self.assertIn("exclude both Build and Review lanes", factual["required_checks"])
        self.assertIn("load the Python core and Review lane", debt["required_checks"])
        self.assertIn(
            "load the matched core reference plus at most one Python lane",
            lookup["required_checks"],
        )
        self.assertIn("exclude the Review lane", build["required_checks"])
        self.assertIn(
            "apply the WSGI close carve-out and withhold pyapi.HC-5",
            wsgi["required_checks"],
        )
        self.assertIn("cite pyapi.HC-2, pyapi.HC-4, and pyapi.HC-6", serverless["required_checks"])


if __name__ == "__main__":
    unittest.main()
