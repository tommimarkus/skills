import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, read


CORPUS = REPO_ROOT / "souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus"
SCORER = REPO_ROOT / "souroldgeezer-audit/skills/ip-hygiene/references/scripts/score_ip_hygiene_eval.py"


class IpHygieneEvalContractTest(unittest.TestCase):
    def test_blind_cases_have_distinct_substantive_synthetic_facts(self) -> None:
        cases = [json.loads(line) for line in (CORPUS / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(cases), 32)
        prompts = [case["prompt"] for case in cases]
        self.assertEqual(len(prompts), len(set(prompts)))
        self.assertNotIn("Synthetic FictionalCloud scenario; assess only the stated publication act.", prompts)
        for case in cases:
            self.assertTrue(case["synthetic"], case["case"])
            for fact_heading in ("Material:", "Provenance:", "Act and distribution:", "Decision context:"):
                self.assertIn(fact_heading, case["prompt"], case["case"])
            self.assertGreaterEqual(len(case["prompt"]), 420, case["case"])

    def test_readme_documents_blind_actual_result_schema_and_limits(self) -> None:
        text = read("souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus/README.md")
        self.assertIn("actual result schema", text.lower())
        self.assertIn("required_codes", text)
        self.assertIn("structural validation is not model recall", text.lower())

    def test_scorer_accepts_expected_actual_and_family_filters(self) -> None:
        self.assertTrue(SCORER.is_file())
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [dict(case) for case in expected]
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(case) + "\n" for case in actual), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCORER), "--expected", str(CORPUS / "expected.jsonl"),
                                     "--actual", str(actual_path), "--families", "IP-MARK,IP-COPY,IP-DB"],
                                    text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_scorer_rejects_blocker_miss_clean_false_positive_and_clearance_overclaim(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [dict(case) for case in expected]
        blocker = next(case for case in actual if case["triage_gate"] == "fail")
        blocker["required_codes"] = []
        clean = next(case for case in actual if case["expect"] == "no-finding")
        clean["required_codes"] = ["IP-COPY-1"]
        actual[0]["legal_clearance"] = True
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(case) + "\n" for case in actual), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCORER), "--expected", str(CORPUS / "expected.jsonl"),
                                     "--actual", str(actual_path)], text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missed designated blocker", result.stdout)
        self.assertIn("forbidden clean-control finding", result.stdout)
        self.assertIn("legal-clearance overclaim", result.stdout)
