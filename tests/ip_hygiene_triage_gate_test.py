import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, assert_phrases, compact, read, section


GATE = "### Triage Gate"
SKILL_PATH = "souroldgeezer-audit/skills/ip-hygiene/SKILL.md"
IN_DEPTH_PATH = "souroldgeezer-audit/skills/ip-hygiene/references/procedures/in-depth-review.md"
CORPUS = REPO_ROOT / "souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus"


class IpHygieneTriageGateTest(unittest.TestCase):
    def test_triage_gate_is_scoped_and_has_ip_specific_blockers(self) -> None:
        gate = section(read(SKILL_PATH), GATE)
        assert_phrases(self, gate, (
            "triage gate: <fail | not-evaluated | pass-limited>",
            "Do not emit this line in in-depth mode.",
            "misleading mark claims or branding",
            "unauthorized logos or endorsement implications",
            "unlicensed copied expression",
            "missing operative copyright or licence notices",
            "incompatible or restricted bundled content",
        ))

    def test_triage_procedure_answers_all_six_questions_including_the_notice_question(self) -> None:
        skill = read(SKILL_PATH)
        normalized = " ".join(skill.split())
        self.assertIn("Answer all six questions by judgment", normalized)
        self.assertIn("All six no: emit `nothing to check`", normalized)
        in_depth = " ".join(read(IN_DEPTH_PATH).split())
        self.assertIn("apply all six triage questions per surface", in_depth)
        self.assertIn(
            "Does a touched source file carry, need, lose, or transform a copyright or licence notice, "
            "attribution comment, or generated-code banner?",
            normalized,
        )
        self.assertIn(
            "Does a surface a reader sees — public or code-visible — mention or brand with",
            normalized,
        )
        self.assertIn("Identifiers, string literals, package/module names, User-Agent strings", normalized)

    def test_notice_classification_boundaries_are_explicit(self) -> None:
        skill = read(SKILL_PATH)
        normalized = " ".join(skill.split())
        self.assertIn(
            "A missing operative copyright or licence notice on material actually distributed is a "
            "`block` and `fail`",
            normalized,
        )
        self.assertIn(
            "A notice that survived a transformation but was relocated or reformatted, where the "
            "operative licence does not specify required location or form, is `warn` or `info` and "
            "`pass-limited`",
            normalized,
        )
        self.assertIn(
            "Notice survival through a build, bundle, or minification step that cannot be checked "
            "because the built artifact is unavailable is `not-evaluated`, not `pass-limited`",
            normalized,
        )
        self.assertIn(
            "An attribution comment naming a source whose terms are unresolved is an evidence gap "
            "under `IP-SRC-2`: `not-evaluated`",
            normalized,
        )
        self.assertIn(
            "A generated-code banner alone is `IP-SRC-5` provenance evidence, not a finding",
            normalized,
        )

    def test_ambiguity_and_nonblocking_semantics_are_explicit(self) -> None:
        gate = section(read(SKILL_PATH), GATE)
        assert_phrases(self, gate, (
            "unclear source authority, holder policy, or redistribution terms",
            "unless a confirmed blocker already makes the gate `fail`",
            "Ordinary mark-symbol, grammar, or optional-attribution convention issues are nonblocking",
            "preserve their underlying `warn` or `info` severity",
            "clean triage rerun before `pass-limited`",
        ))

    def test_gate_outcomes_are_defined_in_precedence_order(self) -> None:
        gate = compact(section(read(SKILL_PATH), GATE))
        positions = [gate.index(f"- `{status}`") for status in ("fail", "not-evaluated", "pass-limited")]
        self.assertEqual(positions, sorted(positions))

    def test_synthetic_corpus_covers_each_triage_gate_outcome(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        cases = [json.loads(line) for line in (CORPUS / "cases.jsonl").read_text().splitlines()]
        by_case = {case["case"]: case for case in expected}
        self.assertEqual(
            {by_case[case_id]["outcome"] for case_id in (
                "case-001", "case-002", "case-003", "case-005"
            )},
            {"fail"},
        )
        self.assertEqual(by_case["case-004"]["outcome"], "not-evaluated")
        self.assertEqual(by_case["case-006"]["outcome"], "pass-limited")
        self.assertEqual(by_case["case-007"]["outcome"], "not-evaluated")
        self.assertEqual(by_case["case-008"]["outcome"], "pass-limited")
        self.assertEqual(by_case["case-011"]["outcome"], "not-evaluated")
        self.assertEqual(by_case["case-014"]["outcome"], "not-evaluated")
        case_ids = {case["case"] for case in cases}
        self.assertEqual(case_ids, set(by_case))
        fixture_dirs = [path for path in (CORPUS / "cases").iterdir() if path.is_dir()]
        self.assertEqual(len(fixture_dirs), 8)

    def test_accuracy_corpus_has_complete_adversarial_contract_records(self) -> None:
        expected = [json.loads(line) for line in (CORPUS / "expected.jsonl").read_text().splitlines()]
        self.assertGreaterEqual(len(expected), 32)
        families = {case["family"] for case in expected}
        self.assertEqual(families, {"IP-SRC", "IP-COPY", "IP-DB", "IP-LIC", "IP-MARK"})
        for case in expected:
            with self.subTest(case=case["case"]):
                for key in ("required_code_groups", "allowed_codes", "allowed_classifications", "lane",
                            "outcome", "counsel_outcome", "designated_blocker_criterion"):
                    self.assertIn(key, case)
        self.assertTrue(any(case["counsel_outcome"] == "required" for case in expected))
        self.assertTrue(any(case["expect"] == "no-finding" for case in expected))


if __name__ == "__main__":
    unittest.main()
