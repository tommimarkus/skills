import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT


SKILL = REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/SKILL.md"
BEHAVIOR_CASES = (
    REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/references/evals/behavior-cases.jsonl"
)
ENGINE_LEDGER = REPO_ROOT / "tests/lean_engine_ledger.jsonl"
CODE_LEDGER = REPO_ROOT / "tests/lean_code_ledger.jsonl"
WORKFLOW_LEDGER = REPO_ROOT / "tests/lean_workflow_ledger.jsonl"


def rows(path: Path) -> dict[str, dict]:
    return {
        row["id"]: row
        for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
        if row
    }


class LeanAuditLimitedGateTest(unittest.TestCase):
    def test_limited_scope_gate_derives_only_after_filtering_and_carve_outs(self) -> None:
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.assertIn("limited-scope gate: <status>", skill)
        self.assertIn("only for a file, named-file, or diff coverage", skill)
        self.assertIn("filter findings to the requested paths and apply declared carve-outs before", skill)
        self.assertIn("never derive it from a directory-wide engine exit alone", skill)
        self.assertIn("`LA-DUP-1`, `LA-DUP-2`, `LA-CODE-DUP-1`, `LA-RUN-2`, or `LA-RUN-3`", skill)
        self.assertIn("expected lane exceeds declared capacity", skill)

    def test_gate_precedence_and_not_evaluated_evidence_rules_are_explicit(self) -> None:
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.assertIn("confirmed in-scope block exists, `fail` wins", skill)
        self.assertIn("`not-evaluated`", skill)
        self.assertIn("Python ≥3.11 floor is unmet", skill)
        self.assertIn("required deterministic engine is unavailable", skill)
        self.assertIn("cannot rule out overflow", skill)
        self.assertIn("Otherwise emit `pass-limited`", skill)
        self.assertIn("judgment-only findings are warn/info and nonblocking", skill)

    def test_behavior_cases_cover_block_clean_and_not_evaluated_paths(self) -> None:
        cases = rows(BEHAVIOR_CASES)
        for case_id, status in {
            "lean-audit-limited-gate-block": "fail",
            "lean-audit-limited-gate-clean": "pass-limited",
            "lean-audit-limited-gate-not-evaluated": "not-evaluated",
        }.items():
            with self.subTest(case_id=case_id):
                self.assertEqual(cases[case_id]["expected_gate"], status)
                self.assertEqual(cases[case_id]["source_kind"], "synthetic")

    def test_existing_detector_ledgers_supply_block_and_clean_controls(self) -> None:
        engine = rows(ENGINE_LEDGER)
        code = rows(CODE_LEDGER)
        workflow = rows(WORKFLOW_LEDGER)
        self.assertTrue(engine["LAD-T0001"]["expect_block"])
        self.assertFalse(engine["LAD-T0007"]["expect_block"])
        self.assertTrue(code["LCD-T0001"]["expect_block"])
        self.assertFalse(code["LCD-T0004"]["expect_block"])
        self.assertIn("LA-RUN-1", workflow["workflow-unbounded-raw"]["expected_codes"])
        self.assertEqual(workflow["workflow-bounded-compact"]["expected_codes"], [])


if __name__ == "__main__":
    unittest.main()
