import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, read


SKILL_PATH = "souroldgeezer-audit/skills/ip-hygiene/SKILL.md"
CORPUS = REPO_ROOT / "souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus"


class IpHygieneTriageGateTest(unittest.TestCase):
    def test_triage_gate_is_scoped_and_has_ip_specific_blockers(self) -> None:
        skill = read(SKILL_PATH)
        self.assertIn("triage gate: <fail | not-evaluated |\npass-limited>", skill)
        self.assertIn("Do not emit this line in in-depth mode.", skill)
        for blocker in (
            "misleading mark claims or branding",
            "unauthorized logos or endorsement implications",
            "unlicensed copied expression",
            "missing operative copyright or licence notices",
            "incompatible or restricted bundled content",
        ):
            with self.subTest(blocker=blocker):
                self.assertIn(blocker, skill)

    def test_ambiguity_and_nonblocking_semantics_are_explicit(self) -> None:
        skill = read(SKILL_PATH)
        self.assertIn("unclear source authority, holder policy, or redistribution terms", skill)
        self.assertIn("unless a confirmed blocker already makes the gate `fail`", skill)
        self.assertIn("Ordinary mark-symbol, grammar, or optional-attribution convention issues are\nnonblocking", skill)
        self.assertIn("preserve\ntheir underlying `warn` or `info` severity", skill)
        self.assertIn("clean triage rerun before `pass-limited`", skill)

    def test_synthetic_corpus_covers_each_triage_gate_outcome(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        cases = [json.loads(line) for line in (CORPUS / "cases.jsonl").read_text().splitlines()]
        by_case = {case["case"]: case for case in expected}
        self.assertEqual({by_case[f"c{number}-{name}"]["triage_gate"] for number, name in (
            (1, "mark-led-name"), (2, "false-registration"), (3, "dropped-notice"),
            (4, "vendored-no-license"), (5, "near-verbatim"),
        )}, {"fail"})
        self.assertEqual(by_case["c6-clean-control"]["triage_gate"], "pass-limited")
        self.assertEqual(by_case["c7-unclear-redistribution"]["triage_gate"], "not-evaluated")
        self.assertEqual(by_case["c8-symbol-convention"]["triage_gate"], "pass-limited")
        case_ids = {case["case"] for case in cases}
        self.assertEqual(case_ids, set(by_case))
        for case in expected[:8]:
            with self.subTest(case=case["case"]):
                self.assertTrue((CORPUS / "cases" / case["case"]).is_dir())

    def test_accuracy_corpus_has_complete_adversarial_contract_records(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        self.assertGreaterEqual(len(expected), 32)
        families = {case["family"] for case in expected}
        self.assertEqual(families, {"IP-SRC", "IP-COPY", "IP-DB", "IP-LIC", "IP-MARK"})
        for case in expected:
            with self.subTest(case=case["case"]):
                for key in ("required_codes", "forbidden_codes", "severity", "triage_gate",
                            "in_depth_verdict", "authority_class", "fact_status", "counsel_outcome"):
                    self.assertIn(key, case)
        self.assertTrue(any(case["counsel_outcome"] == "required" for case in expected))
        self.assertTrue(any(case["expect"] == "no-finding" for case in expected))


if __name__ == "__main__":
    unittest.main()
