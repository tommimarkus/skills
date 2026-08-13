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
        self.assertEqual(len(cases), 42)
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
            db_code = "IP-DB-1" if case_id == "case-017" else "IP-DB-2"
            self.assertEqual(
                expected[case_id]["allowed_classifications"][db_code][0]["authority_class"],
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
        complete_codes = {
            *(f"IP-SRC-{number}" for number in range(1, 5)),
            *(f"IP-COPY-{number}" for number in range(1, 5)),
            *(f"IP-DB-{number}" for number in range(1, 3)),
            *(f"IP-LIC-{number}" for number in range(1, 5)),
            *(f"IP-MARK-{number}" for number in range(1, 6)),
        }
        self.assertEqual(covered, complete_codes)
        self.assertEqual(expected["case-009"]["required_code_groups"], [["IP-SRC-1", "IP-LIC-1"]])
        self.assertIn("IP-COPY-1", expected["case-039"]["allowed_codes"])
        self.assertIn("IP-MARK-3", expected["case-040"]["allowed_codes"])
        self.assertEqual(
            expected["case-040"]["allowed_classifications"]["IP-MARK-5"],
            [{"severity": "block", "authority_class": "binding-law harmonization source",
              "fact_status": "inference"}],
        )
        self.assertEqual(
            {case["counsel_outcome"] for case in expected.values()},
            {"not-triggered", "recommended", "required"},
        )
        authorities = {
            classification["authority_class"]
            for case in expected.values()
            for classifications in case["allowed_classifications"].values()
            for classification in classifications
        }
        self.assertEqual(authorities, {
            "binding law", "binding-law harmonization source", "operative licence term",
            "holder policy", "project convention", "conservative repository policy",
        })
        self.assertEqual(expected["case-030"]["expect"], "no-finding")
        self.assertEqual(expected["case-041"]["required_code_groups"], [["IP-MARK-1"]])
        self.assertIn("rejects every", cases_by_id()["case-041"]["prompt"])

    def test_blind_prompts_do_not_disclose_gate_verdict_or_counsel_conclusions(self) -> None:
        prompts = "\n".join(case["prompt"] for case in case_records())
        for leaked in (
            "load-bearing", "nonblocking", "no blocker", "counsel trigger",
            "evidence is sufficient", "prudent non-mandatory", "not-evaluated",
            "pass-limited", "no-blocker-identified", "counsel-required",
        ):
            self.assertNotIn(leaked, prompts.lower())

    def test_behavior_cases_use_current_finding_verdict_and_assurance_language(self) -> None:
        behavior_path = CORPUS.parent / "behavior-cases.jsonl"
        text = behavior_path.read_text(encoding="utf-8")
        for stale in (
            "check-bucket result",
            "cite the relevant ip-hygiene check bucket",
            "bucket counts",
            "footer at reasonable assurance",
            "reasonable-assurance footer",
        ):
            self.assertNotIn(stale, text)
        self.assertIn("criterion code", text)
        self.assertIn("reasonable-hygiene in-depth", text)

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
            result = subprocess.run([sys.executable, str(SCORER), "--cases", str(CORPUS / "cases.jsonl"),
                                     "--expected", str(CORPUS / "expected.jsonl"),
                                     "--actual", str(actual_path), "--families", "IP-MARK,IP-COPY,IP-DB"],
                                    text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_scorer_rejects_missing_required_unsupported_clean_and_clearance_findings(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        next(case for case in actual if case["case"] == "case-002")["findings"] = []
        case_001 = next(case for case in expected if case["case"] == "case-001")
        unsupported = finding_from_expected(case_001, "IP-MARK-2")
        unsupported.update({"code": "IP-MARK-5", "severity": "block",
                            "authority_class": "binding law", "fact_status": "fact"})
        next(case for case in actual if case["case"] == "case-001")["findings"].append(unsupported)
        clean_case = next(case for case in expected if case["case"] == "case-006")
        clean_finding = finding_from_expected(clean_case, "IP-COPY-1", {
            "severity": "block", "authority_class": "binding law", "fact_status": "fact"})
        next(case for case in actual if case["case"] == "case-006")["findings"] = [clean_finding]
        actual[0]["legal_clearance"] = "approved"
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(case) + "\n" for case in actual), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCORER), "--cases", str(CORPUS / "cases.jsonl"),
                                     "--expected", str(CORPUS / "expected.jsonl"),
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
        actual["findings"][0]["severity"] = ["block"]
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
        self.assertIn("invalid severity", result.stdout)

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
                [sys.executable, str(SCORER), "--cases", str(CORPUS / "cases.jsonl"),
                 "--expected", str(CORPUS / "expected.jsonl"),
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
                [sys.executable, str(SCORER), "--cases", str(CORPUS / "cases.jsonl"),
                 "--expected", str(CORPUS / "expected.jsonl"),
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
        expected_case = next(item for item in expected if item["case"] == "case-035")
        case["findings"] = [finding_from_expected(expected_case, "IP-SRC-1")]
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(item) + "\n" for item in actual), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCORER), "--cases", str(CORPUS / "cases.jsonl"),
                 "--expected", str(CORPUS / "expected.jsonl"),
                 "--actual", str(actual_path)], text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_scorer_accepts_reviewed_correlated_and_alternative_criteria(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        replacements = {
            "case-004": "IP-SRC-1",
            "case-013": "IP-SRC-2",
            "case-021": "IP-LIC-3",
        }
        by_expected = {case["case"]: case for case in expected}
        for case_id, code in replacements.items():
            actual_case = next(case for case in actual if case["case"] == case_id)
            actual_case["findings"] = [
                finding_from_expected(by_expected[case_id], code)
            ]
        case_017 = next(case for case in actual if case["case"] == "case-017")
        case_017["findings"].append(finding_from_expected(by_expected["case-017"], "IP-COPY-1"))
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text("".join(json.dumps(item) + "\n" for item in actual), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCORER), "--cases", str(CORPUS / "cases.jsonl"),
                 "--expected", str(CORPUS / "expected.jsonl"),
                 "--actual", str(actual_path)], text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_every_declared_alternative_and_correlated_code_is_scorable(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        by_expected = {case["case"]: case for case in expected}
        alternatives = [
            (case, group_index, code)
            for case in expected
            for group_index, group in enumerate(case["required_code_groups"])
            for code in group[1:]
        ]
        for expected_case, group_index, code in alternatives:
            with self.subTest(case=expected_case["case"], code=code):
                actual = [actual_from_expected(case) for case in expected]
                actual_case = next(item for item in actual if item["case"] == expected_case["case"])
                canonical = expected_case["required_code_groups"][group_index][0]
                actual_case["findings"] = [
                    finding for finding in actual_case["findings"] if finding["code"] != canonical
                ]
                actual_case["findings"].append(finding_from_expected(expected_case, code))
                result = self.run_scorer(actual)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        actual = [actual_from_expected(case) for case in expected]
        for actual_case in actual:
            expected_case = by_expected[actual_case["case"]]
            present = {finding["code"] for finding in actual_case["findings"]}
            for code in set(expected_case["allowed_codes"]) - present:
                actual_case["findings"].append(finding_from_expected(expected_case, code))
        result = self.run_scorer(actual)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_scorer_requires_case_grounded_evidence_anchors(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        case = next(item for item in actual if item["case"] == "case-001")
        for field in ("reviewed_surface", "exclusions", "evidence", "limits"):
            case[field] = ["generic placeholder"]
        for finding in case["findings"]:
            finding["evidence"] = ["generic placeholder"]
            for field in (
                "condition", "location", "source_provenance", "distribution_audience",
                "jurisdiction_applicability", "cause", "consequence", "recommendation",
            ):
                finding[field] = "generic placeholder"
        result = self.run_scorer(actual)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing evidence anchor: Blue Harbor", result.stdout)

    def test_scorer_fails_closed_on_malformed_or_incoherent_expected_records(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        mutations = []

        invalid_family = [dict(case) for case in expected]
        invalid_family[0] = {**invalid_family[0], "family": "IP-NOPE"}
        mutations.append((invalid_family, "invalid family"))

        empty_finding = [dict(case) for case in expected]
        empty_finding[0] = {**empty_finding[0], "required_code_groups": [], "allowed_codes": [],
                            "allowed_classifications": {}, "designated_blocker_criterion": None}
        mutations.append((empty_finding, "finding or stopped record must require a code group"))

        counsel_drift = [dict(case) for case in expected]
        index = next(i for i, case in enumerate(counsel_drift) if case["case"] == "case-023")
        counsel_drift[index] = {**counsel_drift[index], "outcome": "no-blocker-identified"}
        mutations.append((counsel_drift, "required counsel must stop the lane"))

        blocker_drift = json.loads(json.dumps(expected))
        blocker_drift[0]["allowed_classifications"]["IP-MARK-2"][0]["severity"] = "warn"
        mutations.append((blocker_drift, "designated blocker must allow block severity"))

        authority_drift = json.loads(json.dumps(expected))
        authority_drift[0]["allowed_classifications"]["IP-MARK-2"][0]["authority_class"] = "directive"
        mutations.append((authority_drift, "invalid classification authority"))

        type_drift = json.loads(json.dumps(expected))
        type_drift[0]["allowed_classifications"]["IP-MARK-2"][0]["severity"] = ["block"]
        mutations.append((type_drift, "invalid classification severity"))

        mutations.append((expected[:-1], "missing expected case: case-042"))

        for records, message in mutations:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                expected_path = root / "expected.jsonl"
                actual_path = root / "actual.jsonl"
                expected_path.write_text(
                    "".join(json.dumps(item) + "\n" for item in records), encoding="utf-8"
                )
                actual_path.write_text(
                    "".join(json.dumps(item) + "\n" for item in actual), encoding="utf-8"
                )
                result = subprocess.run(
                    [sys.executable, str(SCORER), "--cases", str(CORPUS / "cases.jsonl"),
                     "--expected", str(expected_path), "--actual", str(actual_path)],
                    text=True, capture_output=True, check=False,
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(message, result.stdout)

    def run_scorer(self, actual: list[dict]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "actual.jsonl"
            actual_path.write_text(
                "".join(json.dumps(item) + "\n" for item in actual), encoding="utf-8"
            )
            return subprocess.run(
                [sys.executable, str(SCORER), "--cases", str(CORPUS / "cases.jsonl"),
                 "--expected", str(CORPUS / "expected.jsonl"), "--actual", str(actual_path)],
                text=True, capture_output=True, check=False,
            )

    def test_validator_requires_lane_evidence_contracts(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        actual = [actual_from_expected(case) for case in expected]
        prospective = next(case for case in actual if case["lane"] == "prospective")
        prospective.pop("decision_controls")
        triage = next(case for case in actual if case["lane"] == "triage")
        triage.pop("reviewed_surface")
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
        self.assertIn("reviewed_surface", result.stdout)
        self.assertIn("limits must be a nonempty array", result.stdout)

    def test_expected_contract_has_per_code_classification_and_supported_authority(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        self.assertEqual(len(expected), 42)
        for case in expected:
            with self.subTest(case=case["case"]):
                self.assertEqual(set(case), {
                    "case", "family", "expect", "required_code_groups", "allowed_codes", "allowed_classifications",
                    "lane", "outcome", "counsel_outcome", "designated_blocker_criterion",
                    "evidence_anchors"})
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


def case_records() -> list[dict]:
    return [json.loads(line) for line in (CORPUS / "cases.jsonl").read_text().splitlines()]


def cases_by_id() -> dict[str, dict]:
    return {case["case"]: case for case in case_records()}


def finding_from_expected(case: dict, code: str, classification: dict | None = None) -> dict:
    anchors = case["evidence_anchors"]
    classification = classification or case["allowed_classifications"][code][0]
    grounding = " and ".join(anchors)
    return {
        "code": code,
        **classification,
        "condition": f"Condition established by {grounding}",
        "location": f"{case['case']} material describing {anchors[0]}",
        "source_provenance": f"Synthetic source record for {grounding}",
        "intended_act": "redistribute",
        "distribution_audience": f"Publication audience for {anchors[0]}",
        "jurisdiction_applicability": f"Stated applicability facts for {anchors[1]}",
        "confidence": "high",
        "evidence": list(anchors),
        "cause": f"Cause shown by {anchors[0]}",
        "consequence": f"Publication consequence for {anchors[1]}",
        "recommendation": f"Address the condition evidenced by {grounding}",
        "risk_tier": "high" if classification["severity"] == "block" else "unknown",
        "counsel_outcome": case["counsel_outcome"],
    }


def actual_from_expected(case: dict) -> dict:
    findings = []
    for group in case["required_code_groups"]:
        code = group[0]
        findings.append(finding_from_expected(case, code))
    anchors = case["evidence_anchors"]
    result = {"case": case["case"], "lane": case["lane"], "findings": findings,
              "counsel_outcome": case["counsel_outcome"], "legal_clearance": False,
              "reviewed_surface": [f"Reviewed {anchors[0]} and {anchors[1]}"],
              "exclusions": ["none stated in the synthetic case"],
              "evidence": list(anchors),
              "limits": [f"Bounded to the facts about {anchors[0]}"],
              "independence": "independent"}
    outcome_field = {"triage": "triage_gate", "in-depth": "in_depth_verdict",
                     "prospective": "prospective_decision"}[case["lane"]]
    result[outcome_field] = case["outcome"]
    result["assurance_level"] = {
        "triage": "limited triage",
        "in-depth": "reasonable-hygiene in-depth",
        "prospective": "prospective bounded decision",
    }[case["lane"]]
    if case["lane"] == "prospective":
        result["decision_controls"] = [f"Control publication of {anchors[0]}"]
    return result
