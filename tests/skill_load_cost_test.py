# tests/skill_load_cost_test.py
import importlib.util
import json
import unittest
from pathlib import Path

# Load the script by path — repo convention (no `scripts/__init__.py`), matching
# tests/skill_architecture_report_test.py and tests/lessons_ledger_test.py.
REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "skill_load_cost", REPO_ROOT / "scripts" / "skill_load_cost.py"
)
slc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(slc)


class EstimateTokensTest(unittest.TestCase):
    def test_counts_words_and_punctuation_separately(self):
        # "a, b c." -> a , b c .  == 5 tokens
        self.assertEqual(slc.estimate_tokens("a, b c."), 5)

    def test_is_deterministic_and_empty_safe(self):
        self.assertEqual(slc.estimate_tokens(""), 0)
        self.assertEqual(slc.estimate_tokens("word"), slc.estimate_tokens("word"))


class MeasureScenarioTest(unittest.TestCase):
    def test_sums_tokens_across_declared_files(self):
        root = Path(__file__).parent / "skill_load_cost" / "fixtures"
        scenario = {"id": "t", "files": ["alpha.md", "beta.md"]}
        result = slc.measure_scenario(scenario, root)
        self.assertEqual(result["id"], "t")
        self.assertEqual(len(result["rows"]), 2)
        self.assertEqual(
            result["total"],
            result["rows"][0]["tokens"] + result["rows"][1]["tokens"],
        )


if __name__ == "__main__":
    unittest.main()
