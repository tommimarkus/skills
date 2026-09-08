import json
import unittest

from tests.surface_test_lib import REPO_ROOT, read, read_jsonl


class ApiDesignDataEfficiencyTest(unittest.TestCase):
    def test_reference_owns_api_access_amplification_and_scoped_lifetimes(self) -> None:
        reference = read("souroldgeezer-design/docs/api-reference/api-design.md")
        self.assertIn("SAD-G-data-access-amplification", reference)
        self.assertIn("Distinct from `SAD-A-consumer-chattiness`", reference)
        self.assertIn("never share `DbContext` concurrently", reference)
        self.assertIn("`IHttpClientFactory` may create a short-lived client", reference)

    def test_routes_charge_shared_procedure_only_for_relevant_access_work(self) -> None:
        scenarios = json.loads(read("tests/skill_load_cost/scenarios.json"))
        by_id = {item["id"]: item for item in scenarios}
        target = "souroldgeezer-design/docs/design-reference/data-efficiency.md"
        relevant = ("review-api-data-access", "build-api-data-access", "extract-api-data-access-debt", "review-api-software-composed")
        for scenario_id in relevant:
            targets = [route["target"] for route in by_id[scenario_id]["load_routes"]]
            self.assertEqual(targets.count(target), 1, scenario_id)
        for scenario_id in ("lookup-api-data-access", "extract-functions-cosmos-factual"):
            targets = [route["target"] for route in by_id[scenario_id]["load_routes"]]
            self.assertNotIn(target, targets)

    def test_data_evals_are_unique_and_keep_the_existing_sentinel_last(self) -> None:
        cases = list(read_jsonl("souroldgeezer-design/skills/api-design/references/evals/behavior-cases.jsonl"))
        ids = [case["id"] for case in cases]
        expected = {"api-design-behavior-data-nplus-review", "api-design-behavior-data-query-build", "api-design-behavior-data-buffer-review", "api-design-behavior-data-sql-control", "api-design-behavior-data-http-control", "api-design-behavior-data-lifetime-review"}
        self.assertTrue(expected <= set(ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("api-design-behavior-review-extension-highrisk-gates", ids)


if __name__ == "__main__":
    unittest.main()
