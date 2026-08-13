import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, read


CORPUS = REPO_ROOT / "souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus"
SCORER = REPO_ROOT / "souroldgeezer-audit/skills/ip-hygiene/references/scripts/score_ip_hygiene_eval.py"
VALIDATOR = REPO_ROOT / "souroldgeezer-audit/skills/ip-hygiene/references/scripts/validate_ip_hygiene_actual.py"


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

    def test_scorer_accepts_contract_actual_and_family_filters(self) -> None:
        self.assertTrue(SCORER.is_file())
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(case) + "\n" for case in actual), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCORER), "--expected", str(CORPUS / "expected.jsonl"),
                                     "--actual", str(actual_path), "--families", "IP-MARK,IP-COPY,IP-DB"],
                                    text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_scorer_rejects_missing_required_unsupported_clean_and_clearance_findings(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        next(case for case in actual if case["case"] == "c2-false-registration")["findings"] = []
        next(case for case in actual if case["case"] == "c1-mark-led-name")["findings"].append({
            "code": "IP-MARK-5", "severity": "block", "authority_class": "binding law", "fact_status": "fact"})
        next(case for case in actual if case["case"] == "c6-clean-control")["findings"] = [{
            "code": "IP-COPY-1", "severity": "block", "authority_class": "binding law", "fact_status": "fact"}]
        actual[0]["legal_clearance"] = "approved"
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(case) + "\n" for case in actual), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCORER), "--expected", str(CORPUS / "expected.jsonl"),
                                     "--actual", str(actual_path)], text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required finding code", result.stdout)
        self.assertIn("undeclared finding code", result.stdout)
        self.assertIn("forbidden clean-control finding", result.stdout)
        self.assertIn("legal-clearance overclaim", result.stdout)

    def test_validator_rejects_open_schema_aliases_and_nonliteral_false_clearance(self) -> None:
        self.assertTrue(VALIDATOR.is_file())
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = actual_from_expected(expected[0])
        actual["clearance"] = False
        actual["legal_clearance"] = "false"
        actual["extra"] = "not allowed"
        actual["findings"][0]["code"] = "IP-BOGUS-9"
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text(json.dumps(actual) + "\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(VALIDATOR), str(actual_path)], text=True,
                                    capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("undeclared field", result.stdout)
        self.assertIn("clearance alias", result.stdout)
        self.assertIn("legal_clearance must be literal false", result.stdout)
        self.assertIn("invalid code", result.stdout)

    def test_validator_accepts_blind_bundle_cases_and_actual_flags(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text(
                "".join(json.dumps(case) + "\n" for case in actual), encoding="utf-8"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--cases",
                    str(CORPUS / "cases.jsonl"),
                    "--actual",
                    str(actual_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_expected_contract_has_per_code_classification_and_supported_authority(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        self.assertEqual(len(expected), 32)
        for case in expected:
            with self.subTest(case=case["case"]):
                self.assertEqual(set(case), {
                    "case", "family", "expect", "required_codes", "allowed_codes", "allowed_classifications",
                    "lane", "outcome", "counsel_outcome", "designated_blocker_criterion"})
                self.assertTrue(set(case["required_codes"]).issubset(case["allowed_codes"]))
                self.assertEqual(set(case["required_codes"]), set(case["allowed_classifications"]))
                if case["expect"] == "no-finding":
                    self.assertEqual(case["required_codes"], [])
                    self.assertEqual(case["allowed_codes"], [])
                    self.assertEqual(case["allowed_classifications"], {})
                for classifications in case["allowed_classifications"].values():
                    self.assertTrue(classifications)
                    for item in classifications:
                        self.assertEqual(set(item), {"severity", "authority_class", "fact_status"})
                        self.assertNotEqual(item["authority_class"], "not-applicable")


def actual_from_expected(case: dict) -> dict:
    findings = []
    for code in case["required_codes"]:
        findings.append({"code": code, **case["allowed_classifications"][code][0]})
    result = {"case": case["case"], "lane": case["lane"], "findings": findings,
              "counsel_outcome": case["counsel_outcome"], "legal_clearance": False}
    outcome_field = {"triage": "triage_gate", "in-depth": "in_depth_verdict",
                     "prospective": "prospective_decision"}[case["lane"]]
    result[outcome_field] = case["outcome"]
    return result
