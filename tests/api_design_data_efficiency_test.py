import json
import unittest

from tests.surface_test_lib import REPO_ROOT, load_script_module, read, read_jsonl

LOAD_COST = load_script_module(
    "api_data_efficiency_load_cost",
    REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit" / "references" / "scripts" / "skill_load_cost.py",
)
API_BASELINES = {
    "lookup-functions": 4020, "build-functions-cosmos": 24411,
    "review-functions-cosmos-blob": 24147, "extract-functions-cosmos-factual": 17239,
    "extract-functions-cosmos-debt": 20394, "review-surface-architecture": 13659,
    "extract-python-factual": 15496, "extract-python-debt": 16631,
    "lookup-python-lifecycle": 5383, "build-python-asgi": 17110,
    "review-python-wsgi-clean": 16952, "review-python-serverless": 16952,
}


class ApiDesignDataEfficiencyTest(unittest.TestCase):
    def test_reference_owns_api_access_amplification_and_scoped_lifetimes(self) -> None:
        reference = read("souroldgeezer-design/docs/api-reference/api-design.md")
        self.assertIn("SAD-G-data-access-amplification", reference)
        self.assertIn("Distinct from `SAD-A-consumer-chattiness`", reference)
        self.assertIn("never share `DbContext` concurrently", reference)
        self.assertIn("Factory short-lived and configured long-lived `HttpClient` are valid", reference)

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

    def test_data_evals_are_unique_and_keep_the_existing_highrisk_sentinel(self) -> None:
        cases = list(read_jsonl("souroldgeezer-design/skills/api-design/references/evals/behavior-cases.jsonl"))
        ids = [case["id"] for case in cases]
        expected = {"api-design-behavior-data-nplus-review", "api-design-behavior-data-query-build", "api-design-behavior-data-buffer-review", "api-design-behavior-data-sql-control", "api-design-behavior-data-http-control", "api-design-behavior-data-lifetime-review"}
        self.assertTrue(expected <= set(ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("api-design-behavior-review-extension-highrisk-gates", ids)

    def test_new_finding_and_eval_references_are_defined_once(self) -> None:
        reference = read("souroldgeezer-design/docs/api-reference/api-design.md")
        self.assertEqual(reference.count("**SAD-G-data-access-amplification**"), 1)
        cases = list(read_jsonl("souroldgeezer-design/skills/api-design/references/evals/behavior-cases.jsonl"))
        nplus = next(case for case in cases if case["id"] == "api-design-behavior-data-nplus-review")
        self.assertTrue(any("SAD-G-data-access-amplification" in item for item in nplus["required_checks"]))

    def test_existing_api_routes_stay_within_the_approved_content_allowance(self) -> None:
        scenarios = {item["id"]: item for item in json.loads(read("tests/skill_load_cost/scenarios.json"))}
        for scenario_id, baseline in API_BASELINES.items():
            with self.subTest(scenario_id=scenario_id):
                current = LOAD_COST.measure_scenario(scenarios[scenario_id], REPO_ROOT)["total"]
                self.assertLessEqual(current, baseline + 250)

    def test_snapshot_is_exactly_fresh_for_api_routes(self) -> None:
        snapshot = json.loads(read("tests/skill_load_cost/cost-snapshot.json"))
        scenarios = {item["id"]: item for item in json.loads(read("tests/skill_load_cost/scenarios.json"))}
        for scenario_id in (*API_BASELINES, "review-api-data-access", "build-api-data-access", "extract-api-data-access-debt"):
            with self.subTest(scenario_id=scenario_id):
                self.assertEqual(snapshot[scenario_id], LOAD_COST.measure_scenario(scenarios[scenario_id], REPO_ROOT)["total"])

    def test_load_cost_engine_deduplicates_shared_procedure_across_entries(self) -> None:
        scenario = {
            "id": "dedup", "skill": "api-design", "load_routes": [
                {"entry": "api-design-skill", "target": "souroldgeezer-design/docs/design-reference/data-efficiency.md", "predicate": "conditional:data"},
                {"entry": "software-design-skill", "target": "souroldgeezer-design/docs/design-reference/data-efficiency.md", "predicate": "conditional:data"},
            ],
        }
        measured = LOAD_COST.measure_scenario(scenario, REPO_ROOT)
        self.assertEqual(len(measured["rows"]), 1)
        self.assertEqual(len(measured["rows"][0]["routes"]), 2)


if __name__ == "__main__":
    unittest.main()
