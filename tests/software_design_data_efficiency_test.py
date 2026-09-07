import json
import re
import unittest

from tests.surface_test_lib import REPO_ROOT, compact, load_script_module, read, read_jsonl


ROOT = "souroldgeezer-design/skills/software-design"
LOAD_COST = REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/references/scripts/skill_load_cost.py"
slc = load_script_module("software_design_data_efficiency_cost", LOAD_COST)


class SoftwareDesignDataEfficiencyTest(unittest.TestCase):
    def test_conditional_route_and_shared_procedure_cover_data_paths(self) -> None:
        skill = compact(read(f"{ROOT}/SKILL.md"))
        procedure = read("souroldgeezer-design/docs/design-reference/data-efficiency.md")
        self.assertIn("data-efficiency.md", skill)
        self.assertIn("Build/Review", skill)
        self.assertIn("File Edit", skill)
        for marker in ("construction", "mutation", "lookup frequency", "unknown scale", "cleanup", "factory-managed HTTP", "matched section"):
            self.assertIn(marker, procedure)

    def test_q5_card_and_synthetic_evals_cover_positive_and_guards(self) -> None:
        card_rows = read_jsonl(f"{ROOT}/references/smell-cards.jsonl")
        card_ids = [row["id"] for row in card_rows]
        self.assertEqual(len(card_ids), len(set(card_ids)))
        for code in card_ids:
            self.assertRegex(code, r"^SD-[A-Z]-\d+$")
        cards = {row["id"]: row for row in card_rows}
        self.assertEqual("Workload-mismatched data path", cards["SD-Q-5"]["title"])
        self.assertIn("warn", cards["SD-Q-5"]["default_severity"])
        self.assertIn("correctness/resource-budget", cards["SD-Q-5"]["default_severity"])
        behaviors = {row["id"]: row for row in read_jsonl(f"{ROOT}/references/evals/behavior-cases.jsonl")}
        required_text = []
        for identifier in (
            "software-design-behavior-data-repeated-key-build",
            "software-design-behavior-data-quadratic-review",
            "software-design-behavior-data-storage-buffering-review",
            "software-design-behavior-data-tiny-bounded-control",
            "software-design-behavior-data-semantics-control",
            "software-design-behavior-data-speculative-cache-rejection",
        ):
            self.assertIn(identifier, behaviors)
            required_text.extend(behaviors[identifier]["required_checks"])
            references = set(re.findall(r"(?<![\w.])SD-[A-Z]-\d+\b", json.dumps(behaviors[identifier])))
            self.assertLessEqual(references, set(card_ids), identifier)
        self.assertIn("SD-Q-5", " ".join(required_text))
        self.assertIn("data-efficiency.md", " ".join(required_text))
        cases = read_jsonl(f"{ROOT}/references/evals/accuracy-corpus/expected.jsonl")
        selected = {row["id"]: row for row in cases if row["id"] in {"sd-acc-116", "sd-acc-117", "sd-acc-118", "sd-acc-119"}}
        self.assertEqual({"sd-acc-116", "sd-acc-117", "sd-acc-118", "sd-acc-119"}, set(selected))
        self.assertEqual(["positive", "positive", "fp-bait", "clean"], [selected[f"sd-acc-{n}"]["kind"] for n in range(116, 120)])

    def test_routes_and_evidence_contract_are_conditional(self) -> None:
        skill = read(f"{ROOT}/SKILL.md")
        cards = {row["id"]: row for row in read_jsonl(f"{ROOT}/references/smell-cards.jsonl")}
        self.assertIn("Build/Review data", skill)
        self.assertIn("debt Extract", skill)
        self.assertIn("Lookup reads", skill)
        self.assertIn("File Edit returns", skill)
        triggers = {row["id"]: row for row in read_jsonl(f"{ROOT}/references/evals/trigger-cases.jsonl")}
        self.assertTrue(triggers["software-design-trigger-yes-data-collections"]["expected_activation"])
        self.assertTrue(triggers["software-design-trigger-yes-data-batch-cli"]["expected_activation"])
        self.assertFalse(triggers["software-design-trigger-no-data-http-contract"]["expected_activation"])
        self.assertFalse(triggers["software-design-trigger-no-data-ui"]["expected_activation"])
        for extension in ("python", "typescript"):
            content = read(f"{ROOT}/extensions/{extension}.md")
            self.assertIn("structural", content)
            self.assertIn("data-efficiency.md", content)
        self.assertIn("structural operation/size/semantic decision", cards["SD-Q-2"]["false_positive_guard"])

    def test_cost_routes_measure_conditional_inclusion_and_exclusion(self) -> None:
        scenarios = json.loads(read("tests/skill_load_cost/scenarios.json"))
        by_id = {scenario["id"]: scenario for scenario in scenarios}
        procedure = "souroldgeezer-design/docs/design-reference/data-efficiency.md"
        self.assertIn(procedure, by_id["sd-build-data-efficiency"]["files"])
        self.assertIn(procedure, by_id["sd-review-data-efficiency"]["files"])
        self.assertIn(procedure, by_id["sd-lookup-data-efficiency"]["files"])
        self.assertNotIn(procedure, by_id["sd-file-edit-data-excluded"]["files"])
        self.assertNotIn(procedure, by_id["sd-lookup-principle"]["files"])
        snapshot = json.loads(read("tests/skill_load_cost/cost-snapshot.json"))
        for scenario_id, scenario in by_id.items():
            if scenario["skill"] != "software-design":
                continue
            self.assertEqual(snapshot[scenario_id], slc.measure_scenario(by_id[scenario_id], REPO_ROOT)["total"])
        # Exact committed counts at 40a7be15237fc190d6ed611593fb84cedb04268d.
        baseline = {"sd-lookup-principle": 2228, "sd-build-csharp": 8083, "sd-review-typescript": 11420, "sd-review-fragility": 10448}
        for scenario_id, before in baseline.items():
            self.assertLessEqual(snapshot[scenario_id] - before, 250)
        self.assertLessEqual(slc.estimate_tokens(read(procedure)), 1400)

    def test_stack_extensions_keep_core_rules_and_csharp_adds_ef_cues(self) -> None:
        for extension in ("python", "typescript"):
            self.assertIn("data-efficiency.md", read(f"{ROOT}/extensions/{extension}.md"))
        csharp = read(f"{ROOT}/extensions/csharp.md")
        self.assertIn("efficient-querying", csharp)
        self.assertIn("dbcontext-configuration", csharp)
        self.assertIn("scoped", csharp)


if __name__ == "__main__":
    unittest.main()
