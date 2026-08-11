import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT


SKILL_ROOT = REPO_ROOT / "souroldgeezer-audit/skills/test-quality-audit"
SKILL = SKILL_ROOT / "SKILL.md"
CORPUS = SKILL_ROOT / "references/golden-corpus/test-quality-audit-cases.jsonl"
SCENARIOS = REPO_ROOT / "tests/skill_load_cost/scenarios.json"

BLOCKERS = {
    "HC-1", "HC-2", "HC-4", "I-HC-A1", "I-HC-A10", "I-HC-B2",
    "I-HC-B5", "E-HC-F10", "E-HC-S1", "E-HC-S5",
}
DEEP_CASES = {
    "TQA-GOLD-0005", "TQA-GOLD-0006", "TQA-GOLD-0010", "TQA-GOLD-0012",
    "TQA-GOLD-0013", "TQA-GOLD-0014", "TQA-GOLD-0017", "TQA-GOLD-0019",
}


def corpus() -> dict[str, dict]:
    return {
        row["id"]: row
        for row in (
            json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


class TestQualityQuickGateTest(unittest.TestCase):
    def test_quick_loads_materiality_and_emits_the_shared_gate(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        compact = " ".join(skill.split())
        self.assertIn("materiality.md`](../../docs/audit-reference/materiality.md) in all modes", compact)
        self.assertIn("Quick gate: <status>", skill)
        self.assertLess(skill.index("per-test findings"), skill.index("Quick gate: <status>"))
        self.assertIn("fail if any substantiated in-scope `block`", compact)
        self.assertIn("not-evaluated", compact)
        self.assertIn("pass-limited", compact)
        self.assertIn("remediated block needs a clean rerun", compact)
        self.assertIn("risk is orthogonal", compact)
        self.assertIn("never emits `Gap-*` findings or a remediation worklist", compact)

    def test_quick_scenarios_load_materiality_but_not_deep_only_output(self) -> None:
        scenarios = {row["id"]: row for row in json.loads(SCENARIOS.read_text(encoding="utf-8"))}
        materiality = "souroldgeezer-audit/docs/audit-reference/materiality.md"
        deep_output = (
            "souroldgeezer-audit/skills/test-quality-audit/"
            "references/procedures/deep-mode-output-format.md"
        )
        for scenario_id in ("quick-node-unit", "quick-python-unit"):
            with self.subTest(scenario_id=scenario_id):
                self.assertIn(materiality, scenarios[scenario_id]["files"])
                self.assertNotIn(deep_output, scenarios[scenario_id]["files"])

    def test_corpus_pins_gate_precedence_blockers_and_false_positive_controls(self) -> None:
        cases = corpus()
        observed = {
            smell
            for case in cases.values()
            if case["mode"] == "quick" and case["expected_gate"] == "fail"
            for smell in case["expected_smells"]
        }
        self.assertTrue(BLOCKERS.issubset(observed))

        false_positive_controls = [
            case for case in cases.values()
            if case["mode"] == "quick" and case["expected_gate"] == "pass-limited"
            and case["expected_severity"] in {"warn", "info"}
            and case.get("forbidden_smells")
        ]
        self.assertTrue(false_positive_controls)

    def test_corpus_marks_modes_and_requires_sut_context_for_deep_gap_cases(self) -> None:
        cases = corpus()
        for case_id, case in cases.items():
            with self.subTest(case_id=case_id):
                self.assertIn(case["mode"], {"quick", "deep"})
                self.assertIn(case["expected_gate"], {"fail", "pass-limited", None})
                if case["mode"] == "quick":
                    self.assertIsNotNone(case["expected_gate"])
                    self.assertNotIn("Gap-", " ".join(case["expected_smells"]))
        for case_id in DEEP_CASES:
            with self.subTest(case_id=case_id):
                self.assertEqual("deep", cases[case_id]["mode"])
                self.assertIsNone(cases[case_id]["expected_gate"])
                self.assertTrue(cases[case_id].get("sut_snippet") or cases[case_id].get("deep_mode_context"))


if __name__ == "__main__":
    unittest.main()
