import unittest

from tests.surface_test_lib import read, read_jsonl


SKILL = "souroldgeezer-design/skills/software-design/SKILL.md"
REFERENCE = "souroldgeezer-design/docs/software-reference/software-design.md"
CATALOG = "souroldgeezer-design/skills/software-design/references/smell-catalog.md"
CARDS = "souroldgeezer-design/skills/software-design/references/smell-cards.jsonl"
PROCEDURE = "souroldgeezer-design/skills/software-design/references/procedures/fragility-review.md"


class SoftwareDesignFragilitySurfaceTest(unittest.TestCase):
    def test_public_contract_and_load_conditions_are_explicit(self) -> None:
        skill = read(SKILL)

        self.assertIn("Fragility review checks whether code that", skill)
        self.assertIn("not style review, speculative abstraction, analyzer", skill)
        self.assertIn("references/procedures/fragility-review.md", skill)
        self.assertIn("references/procedures/native-tool-evidence.md", skill)
        for condition in (
            "repository-configured native tool supplied evidence",
            "detected without a repository-owned invocation",
            "evidence gap makes one optional suggestion relevant",
        ):
            self.assertIn(condition, skill)

    def test_latent_precondition_card_requires_real_safety_evidence(self) -> None:
        catalog = read(CATALOG)
        cards = {record["id"]: record for record in read_jsonl(CARDS)}
        card = cards["SD-E-6"]

        self.assertIn("`SD-E-6`", catalog)
        self.assertEqual("Latent precondition", card["title"])
        for phrase in (
            "indexed access",
            "first/last",
            "lookup",
            "cast",
            "fixed-shape or non-empty type",
            "validated boundary",
            "dominating guard",
            "deliberate fail-fast contract",
            "tests, comments, and sample data alone are not proof",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, " ".join(str(value) for value in card.values()))

    def test_adjacent_change_probe_calibrates_structural_findings(self) -> None:
        procedure = read(PROCEDURE)

        for phrase in (
            "volatile decision",
            "intended owner",
            "every site that must change together",
            "Multiple files alone are not a finding",
            "accidental duplication, divergent ownership, or unrelated coordinated edits",
            "coupling, ownership, boundary, or semantic `SD-*` code",
            "future change is merely imaginable",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, procedure)

    def test_completion_gate_is_calibrated_and_tool_absence_is_safe(self) -> None:
        reference = read(REFERENCE)
        procedure = read(PROCEDURE)

        for state in ("`pass`", "`warn`", "`block`", "`not-assessed`"):
            self.assertIn(state, procedure)
        self.assertIn("high-confidence fragility", procedure)
        self.assertIn("crash, corruption, partial-application, or silent-divergence", procedure)
        self.assertIn("optional tooling", procedure)
        self.assertIn("not a finding", reference)
        self.assertIn("Tool findings are evidence\ncandidates, not conclusions", reference)
        self.assertIn("plain-language title beside its internal `SD-*` code", procedure)


if __name__ == "__main__":
    unittest.main()
