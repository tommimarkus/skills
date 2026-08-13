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
        self.assertEqual(len(cases), 40)
        prompts = [case["prompt"] for case in cases]
        self.assertEqual(len(prompts), len(set(prompts)))
        self.assertNotIn("Synthetic FictionalCloud scenario; assess only the stated publication act.", prompts)
        for case in cases:
            self.assertEqual(set(case), {"case", "prompt", "synthetic"})
            self.assertRegex(case["case"], r"^case-[0-9]{3}$")
            self.assertTrue(case["synthetic"], case["case"])
            for fact_heading in ("Material:", "Provenance:", "Act and distribution:", "Decision context:"):
                self.assertIn(fact_heading, case["prompt"], case["case"])
            self.assertRegex(
                case["prompt"],
                r"Requested lane: (prospective decision|limited-assurance triage|reasonable-hygiene in-depth review)\.",
            )
            self.assertGreaterEqual(len(case["prompt"]), 420, case["case"])

    def test_expected_records_encode_reviewed_authority_and_merits_boundaries(self) -> None:
        expected = {
            item["case"]: item
            for item in map(json.loads, (CORPUS / "expected.jsonl").read_text().splitlines())
        }
        self.assertEqual(
            {frozenset(group) for group in expected["case-001"]["required_code_groups"]},
            {frozenset({"IP-MARK-2"}), frozenset({"IP-MARK-3"})},
        )
        self.assertEqual(
            expected["case-002"]["allowed_classifications"]["IP-MARK-4"][0]["authority_class"],
            "conservative repository policy",
        )
        self.assertEqual(expected["case-017"]["expect"], "stopped")
        self.assertEqual(expected["case-017"]["outcome"], "not-evaluated")
        self.assertIsNone(expected["case-017"]["designated_blocker_criterion"])
        self.assertEqual(expected["case-018"]["expect"], "stopped")
        self.assertEqual(expected["case-018"]["outcome"], "not-evaluated")
        self.assertIsNone(expected["case-018"]["designated_blocker_criterion"])
        for case_id in ("case-017", "case-018", "case-019"):
            for classifications in expected[case_id]["allowed_classifications"].values():
                self.assertEqual(
                    classifications[0]["authority_class"],
                    "binding-law harmonization source",
                    case_id,
                )
        for case_id in ("case-005", "case-013", "case-014", "case-024",
                        "case-027", "case-028"):
            for classifications in expected[case_id]["allowed_classifications"].values():
                self.assertNotEqual(classifications[0]["authority_class"], "binding law", case_id)
        self.assertEqual(expected["case-015"]["family"], "IP-LIC")
        self.assertEqual(
            expected["case-022"]["allowed_classifications"]["IP-LIC-4"][0]["authority_class"],
            "conservative repository policy",
        )
        prospective = [case for case in expected.values() if case["lane"] == "prospective"]
        self.assertEqual(
            {case["outcome"] for case in prospective},
            {"proceed-with-stated-controls", "do-not-proceed", "insufficient-evidence", "counsel-required"},
        )
        self.assertEqual(
            {case["outcome"] for case in expected.values() if case["lane"] == "in-depth"},
            {"blocked", "qualified", "no-blocker-identified"},
        )
        covered = {code for case in expected.values() for group in case["required_code_groups"] for code in group}
        self.assertIn("IP-COPY-4", covered)
        self.assertIn("IP-MARK-5", covered)
        self.assertEqual(expected["case-009"]["required_code_groups"], [["IP-SRC-1", "IP-LIC-1"]])
        self.assertIn("IP-COPY-1", expected["case-039"]["allowed_codes"])
        self.assertIn("IP-MARK-3", expected["case-040"]["allowed_codes"])

    def test_readme_documents_blind_actual_result_schema_and_limits(self) -> None:
        text = read("souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus/README.md")
        self.assertIn("actual result schema", text.lower())
        self.assertIn("required_code_groups", text)
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
        next(case for case in actual if case["case"] == "case-002")["findings"] = []
        next(case for case in actual if case["case"] == "case-001")["findings"].append({
            "code": "IP-MARK-5", "severity": "block", "authority_class": "binding law", "fact_status": "fact"})
        next(case for case in actual if case["case"] == "case-006")["findings"] = [{
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
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--cases", str(CORPUS / "cases.jsonl"),
                 "--actual", str(actual_path)],
                text=True, capture_output=True, check=False,
            )
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

    def test_validator_requires_coverage_aware_invocation_and_rejects_coverage_drift(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(case) + "\n" for case in actual), encoding="utf-8")
            positional = subprocess.run(
                [sys.executable, str(VALIDATOR), str(actual_path)], text=True,
                capture_output=True, check=False,
            )
            actual.append({**actual[-1], "case": "case-999"})
            actual_path.write_text("".join(json.dumps(case) + "\n" for case in actual), encoding="utf-8")
            unexpected = subprocess.run(
                [sys.executable, str(VALIDATOR), "--cases", str(CORPUS / "cases.jsonl"),
                 "--actual", str(actual_path)], text=True, capture_output=True, check=False,
            )
        self.assertNotEqual(positional.returncode, 0)
        self.assertIn("--cases", positional.stderr)
        self.assertNotEqual(unexpected.returncode, 0)
        self.assertIn("unexpected actual case: case-999", unexpected.stdout)

    def test_scorer_rejects_unexpected_case_even_with_family_filter(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        actual.append({**actual[0], "case": "case-999"})
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(case) + "\n" for case in actual), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCORER), "--expected", str(CORPUS / "expected.jsonl"),
                 "--actual", str(actual_path), "--families", "IP-MARK"],
                text=True, capture_output=True, check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected actual case: case-999", result.stdout)

    def test_scorer_rejects_unknown_and_zero_coverage_family_selectors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCORER), "--expected", str(CORPUS / "expected.jsonl"),
                 "--actual", str(actual_path), "--families", "IP-NOPE"],
                text=True, capture_output=True, check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown family selector: IP-NOPE", result.stdout)

    def test_validator_accepts_harmonization_source_authority_class(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        finding = next(case for case in actual if case["case"] == "case-017")["findings"][0]
        self.assertEqual(finding["authority_class"], "binding-law harmonization source")
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(case) + "\n" for case in actual), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--cases", str(CORPUS / "cases.jsonl"),
                 "--actual", str(actual_path)], text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_scorer_accepts_supported_alternative_criterion_group(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        case = next(item for item in actual if item["case"] == "case-035")
        case["findings"] = [{"code": "IP-SRC-1", "severity": "warn",
                             "authority_class": "conservative repository policy", "fact_status": "fact"}]
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(item) + "\n" for item in actual), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCORER), "--expected", str(CORPUS / "expected.jsonl"),
                 "--actual", str(actual_path)], text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_requires_lane_evidence_contracts(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        prospective = next(case for case in actual if case["lane"] == "prospective")
        prospective.pop("decision_controls")
        qualified = next(case for case in actual if case.get("in_depth_verdict") == "qualified")
        qualified["limits"] = []
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(item) + "\n" for item in actual), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--cases", str(CORPUS / "cases.jsonl"),
                 "--actual", str(actual_path)], text=True, capture_output=True, check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("decision_controls", result.stdout)
        self.assertIn("limits must be a nonempty array", result.stdout)

    def test_expected_contract_has_per_code_classification_and_supported_authority(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        self.assertEqual(len(expected), 40)
        for case in expected:
            with self.subTest(case=case["case"]):
                self.assertEqual(set(case), {
                    "case", "family", "expect", "required_code_groups", "allowed_codes", "allowed_classifications",
                    "lane", "outcome", "counsel_outcome", "designated_blocker_criterion"})
                required = {code for group in case["required_code_groups"] for code in group}
                self.assertTrue(required.issubset(case["allowed_codes"]))
                self.assertEqual(set(case["allowed_codes"]), set(case["allowed_classifications"]))
                if case["expect"] == "no-finding":
                    self.assertEqual(case["required_code_groups"], [])
                    self.assertEqual(case["allowed_codes"], [])
                    self.assertEqual(case["allowed_classifications"], {})
                for classifications in case["allowed_classifications"].values():
                    self.assertTrue(classifications)
                    for item in classifications:
                        self.assertEqual(set(item), {"severity", "authority_class", "fact_status"})
                        self.assertNotEqual(item["authority_class"], "not-applicable")


def actual_from_expected(case: dict) -> dict:
    findings = []
    for group in case["required_code_groups"]:
        code = group[0]
        findings.append({"code": code, **case["allowed_classifications"][code][0]})
    result = {"case": case["case"], "lane": case["lane"], "findings": findings,
              "counsel_outcome": case["counsel_outcome"], "legal_clearance": False}
    outcome_field = {"triage": "triage_gate", "in-depth": "in_depth_verdict",
                     "prospective": "prospective_decision"}[case["lane"]]
    result[outcome_field] = case["outcome"]
    if case["lane"] == "prospective":
        result.update({"decision_controls": ["bounded control"], "evidence": ["synthetic facts"],
                       "limits": ["bounded prospective decision"]})
    elif case["lane"] == "in-depth":
        result.update({"reviewed_surface": ["whole synthetic plugin"], "exclusions": ["none"],
                       "evidence": ["synthetic enumeration"], "limits": ["reasonable-hygiene only"]})
    return result
