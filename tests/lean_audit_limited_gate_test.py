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
PROCEDURE = REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/references/procedures/code-adjudication.md"


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
        self.assertIn(
            "filter findings to the requested paths and apply declared carve-outs before", skill
        )
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

    def test_scan_coverage_and_indeterminate_forecast_contracts_are_explicit(self) -> None:
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.assertIn("Normal scans report `coverage`", skill)
        self.assertIn("empty in-scope Markdown set is an input/coverage error", skill)
        self.assertIn("verification reserve, orchestrator base tokens", skill)
        self.assertIn("Treat missing bounds as `indeterminate`", skill)

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

    def test_directory_scope_is_limited_and_mixed_scope_emits_no_gate(self) -> None:
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.assertIn(
            "any scope short of a full-repo enumeration (a file, named files, a diff, a directory,"
            " or a mix) derives `limited`",
            skill,
        )
        self.assertIn("only a full-repo enumeration derives `reasonable`", skill)
        self.assertIn(
            "any scope that contains a directory is a rollup and emits no gate, even when it also"
            " names files; its scope line lists the named files",
            skill,
        )

    def test_carve_out_disclosure_lists_suppressed_pairs_never_a_bare_zero(self) -> None:
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.assertIn(
            "a carve-out disclosure names its rule and lists the engine's `coverage.suppressed`"
            " in-scope pairs, or the `by_rule` counts when truncated",
            skill,
        )
        self.assertIn("a zero is never reported bare while `suppressed.count` is nonzero", skill)

    def test_code_adjudication_procedure_is_linked_and_states_its_four_rules(self) -> None:
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.assertIn("](references/procedures/code-adjudication.md)", skill)
        text = " ".join(PROCEDURE.read_text(encoding="utf-8").split())
        self.assertIn("LA-CODE-DUP-", text)
        self.assertIn("messages, limits, names and constants are parameters", text)
        self.assertIn("Clear a candidate only for genuinely different contracts", text)
        self.assertIn("compare the copies with any canonical sibling they cite", text)
        self.assertIn("Apply one criterion to every candidate", text)

    def test_new_behavior_cases_exist(self) -> None:
        cases = rows(BEHAVIOR_CASES)
        for case_id in (
            "lean-audit-behavior-mixed-scope-limited",
            "lean-audit-behavior-carve-out-disclosure",
            "lean-audit-behavior-clone-adjudication",
        ):
            with self.subTest(case_id=case_id):
                self.assertEqual(cases[case_id]["source_kind"], "synthetic")


if __name__ == "__main__":
    unittest.main()
