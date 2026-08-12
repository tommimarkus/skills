"""Keep RED-test selection explicit in the public TDD policy contract."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TDD_ROOT = ROOT / "souroldgeezer-policy/skills/tdd-policy"


class TddPolicyContractTest(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def behavior_cases(self) -> dict[str, dict[str, object]]:
        path = TDD_ROOT / "references/evals/behavior-cases.jsonl"
        return {
            case["id"]: case
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
            for case in (json.loads(line),)
        }

    def test_core_selects_red_from_existing_tests_first(self) -> None:
        core = (TDD_ROOT / "references/core-workflow.md").read_text(encoding="utf-8")
        for phrase in (
            "## Selecting the RED test",
            "Inspect the existing tests before choosing",
            "Minimally extend a suitable existing test",
            "without removing or weakening its coverage",
            "Create a new test when the behavior is distinct",
            "reuse would make the test unclear",
            "precisely represents the intended behavior",
            "Unrelated failures do not establish RED",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, core)

    def test_synthetic_cases_cover_reuse_and_new_test_branches(self) -> None:
        cases = self.behavior_cases()
        reuse = cases["tdd-policy-behavior-reuse-cohesive-test"]
        create = cases["tdd-policy-behavior-create-distinct-test"]

        self.assertEqual(reuse["source_kind"], "synthetic")
        self.assertEqual(create["source_kind"], "synthetic")
        self.assertTrue(
            any("inspect existing tests" in check.lower() for check in reuse["required_checks"])
        )
        self.assertTrue(
            any("preserve" in check.lower() for check in reuse["required_checks"])
        )
        self.assertTrue(
            any("distinct" in check.lower() for check in create["required_checks"])
        )
        self.assertTrue(
            any("rationale" in artifact.lower() for artifact in create["expected_artifacts"])
        )

    def test_source_grounding_records_selection_rationale(self) -> None:
        grounding = (TDD_ROOT / "references/source-grounding.md").read_text(encoding="utf-8")
        self.assertIn("cohesive existing scenario", grounding)
        self.assertIn("distinct scenario", grounding)
        self.assertIn("clarity or regression coverage", grounding)

    def test_public_guidance_summarizes_existing_test_inspection(self) -> None:
        for relative in ("AGENTS.md", "CLAUDE.md", "README.md"):
            with self.subTest(relative=relative):
                guidance = self.text(relative)
                self.assertIn("Inspect existing tests before selecting the RED test", guidance)


if __name__ == "__main__":
    unittest.main()
