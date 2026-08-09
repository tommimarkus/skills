import json
import unittest

from tests.surface_test_lib import read, read_jsonl


class SoftwareDesignFragilityEvalTest(unittest.TestCase):
    def test_behavior_cases_cover_fragility_native_evidence_and_quieting(self) -> None:
        cases = {case["id"]: case for case in read_jsonl("souroldgeezer-design/skills/software-design/references/evals/behavior-cases.jsonl")}
        expected = {
            "software-design-behavior-fragility-review-calibration": ["hidden assumptions", "style review", "indexed, first/last, lookup, and cast", "multiple files alone", "pass, warn, block, or not-assessed"],
            "software-design-behavior-fragility-supported-and-blocked": ["fixed/non-empty type", "partial-application consequence", "optional tooling"],
            "software-design-behavior-native-evidence-comprehension": ["project-owned invocation", "detected-not-run", "at most one optional suggestion", "capability key"],
            "software-design-behavior-native-evidence-quieting": ["defer-until:2026-09-08", "stored date", "exact list and clear commands", "do not escalate, retry", "fragility findings active"],
        }
        for identifier, markers in expected.items():
            with self.subTest(identifier=identifier):
                body = json.dumps(cases[identifier])
                for marker in markers:
                    self.assertIn(marker, body)

    def test_accuracy_corpus_is_contiguous_and_calibrated(self) -> None:
        cases = read_jsonl("souroldgeezer-design/skills/software-design/references/evals/accuracy-corpus/expected.jsonl")
        self.assertEqual([f"sd-acc-{number:03d}" for number in range(1, 116)], [case["id"] for case in cases])
        self.assertEqual(["positive", "positive", "fp-bait", "clean"], [case["kind"] for case in cases[-4:]])
        self.assertEqual(["SD-E-6"] * 4, [case["target"] for case in cases[-4:]])
        self.assertEqual({"positive": 64, "fp-bait": 40, "clean": 11}, {kind: sum(case["kind"] == kind for case in cases) for kind in ("positive", "fp-bait", "clean")})
        for case in cases[-4:]:
            self.assertEqual("synthetic", case["source_kind"])
            self.assertFalse(case["contains_third_party_text"])

    def test_pressure_grounding_readme_and_cost_contract(self) -> None:
        pressure = read("souroldgeezer-design/skills/software-design/references/evals/model-pressure.md")
        for marker in ("baseline", "Accepted rules", "Behavior evals:", "Retest:", "Merge back:"):
            self.assertIn(marker, pressure)
        grounding = read("souroldgeezer-design/skills/software-design/references/source-grounding.md")
        self.assertIn("https://git-scm.com/docs/git-config/2.51.2.html", grounding)
        self.assertIn("https://git-scm.com/docs/git-worktree.html", grounding)
        self.assertIn("URL-only, paraphrased grounding", grounding)
        self.assertIn("fragility/native-evidence evals are repo-authored", grounding)
        self.assertIn("additive fragility check", read("README.md"))
        scenarios = {item["id"] for item in json.loads(read("tests/skill_load_cost/scenarios.json"))}
        self.assertTrue({"sd-review-fragility", "sd-native-evidence-procedure", "sd-fragility-final-reporting"} <= scenarios)
        snapshot = json.loads(read("tests/skill_load_cost/cost-snapshot.json"))
        for identifier, ceiling in {"sd-lookup-principle": 2266, "sd-build-csharp": 8121, "sd-review-typescript": 11423, "sd-review-fragility": 12628, "sd-native-evidence-procedure": 1200}.items():
            self.assertLessEqual(snapshot[identifier], ceiling)
        self.assertGreaterEqual(snapshot["sd-fragility-final-reporting"], 500)
        self.assertLessEqual(snapshot["sd-fragility-final-reporting"], 1000)


if __name__ == "__main__":
    unittest.main()
