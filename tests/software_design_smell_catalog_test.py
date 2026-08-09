# lean-audit:dup-intentional — parallel per-case test bodies kept literal for readability
import re
import unittest

from tests.surface_test_lib import read, read_jsonl

SOFTWARE_SKILL = "souroldgeezer-design/skills/software-design"
SMELL_CATALOG = f"{SOFTWARE_SKILL}/references/smell-catalog.md"
SMELL_CARDS = f"{SOFTWARE_SKILL}/references/smell-cards.jsonl"
BEHAVIOR_CASES = f"{SOFTWARE_SKILL}/references/evals/behavior-cases.jsonl"
MODEL_PRESSURE = f"{SOFTWARE_SKILL}/references/evals/model-pressure.md"
SOURCE_GROUNDING = f"{SOFTWARE_SKILL}/references/source-grounding.md"


class SoftwareDesignSmellCatalogTest(unittest.TestCase):
    def test_smell_catalog_family_table_only_advertises_defined_core_cards(self) -> None:
        catalog = read(SMELL_CATALOG)
        cards = {record["id"] for record in read_jsonl(SMELL_CARDS)}
        table_rows = [line for line in catalog.splitlines() if line.startswith("|")]
        advertised_codes = set(re.findall(r"`(SD-[A-Z]-\d+)`", "\n".join(table_rows)))

        self.assertEqual(cards, advertised_codes)

    def test_smell_catalog_reserves_retired_core_code(self) -> None:
        catalog = read(SMELL_CATALOG)
        cards = {record["id"] for record in read_jsonl(SMELL_CARDS)}

        self.assertIn("Core `SD-S-3` is intentionally retired", catalog)
        self.assertNotIn("SD-S-3", cards)

    def test_core_smell_catalog_has_actionable_cards(self) -> None:
        catalog = read(SMELL_CATALOG)
        cards = {record["id"]: record for record in read_jsonl(SMELL_CARDS)}
        expected_cards = {
            "SD-W-1": "Speculative abstraction",
            "SD-W-2": "Pass-through layer",
            "SD-B-1": "Responsibility drift",
            "SD-B-2": "State owner blur",
            "SD-B-3": "Internals leakage",
            "SD-B-4": "Adapter owns policy",
            "SD-C-1": "Dependency cycle",
            "SD-C-2": "Policy-to-adapter dependency",
            "SD-C-3": "Shared-core gravity",
            "SD-C-4": "Hidden mutable state",
            "SD-C-6": "Unowned concurrency",
            "SD-S-1": "Vocabulary split",
            "SD-S-2": "Duplicate concept drift",
            "SD-S-4": "External model collapse",
            "SD-S-5": "Error-contract collapse",
            "SD-E-1": "Shotgun change",
            "SD-E-2": "Migration without exit",
            "SD-E-3": "Flag pile-up",
            "SD-E-6": "Latent precondition",
            "SD-Q-1": "Unstated quality tradeoff",
            "SD-Q-2": "Unmeasured quality tactic",
            "SD-Q-4": "Stacked failure handling",
            "SD-T-1": "Ownership mismatch",
        }

        for code, title in expected_cards.items():
            with self.subTest(code=code):
                self.assertIn(f"`{code}`", catalog)
                self.assertIn(code, cards)
                card = cards[code]
                self.assertEqual(title, card["title"])
                for field in ("signal", "evidence_layers", "false_positive_guard", "smallest_action", "default_severity"):
                    self.assertIn(field, card)
                    self.assertTrue(card[field])

    def test_smell_catalog_preserves_family_contract_and_default_blocks(self) -> None:
        catalog = read(SMELL_CATALOG)

        for family in ("Waste", "Boundary", "Coupling", "Semantics", "Evolution", "Tradeoff", "Socio-technical"):
            self.assertIn(f"| {family} |", catalog)

        for phrase in (
            "Default blocks",
            "dependency cycles/inversions",
            "hidden mutable state",
            "specialist-scope absorption",
        ):
            self.assertIn(phrase, catalog)

    def test_behavior_evals_cover_core_smell_clusters(self) -> None:
        behaviors = {record["id"]: record for record in read_jsonl(BEHAVIOR_CASES)}
        expected = {
            "software-design-behavior-core-smell-waste-vs-force": ("SD-W-1", "SD-W-2"),
            "software-design-behavior-core-smell-boundary-policy": ("SD-B-1", "SD-B-3"),
            "software-design-behavior-core-smell-state-policy": ("SD-B-2", "SD-B-4"),
            "software-design-behavior-core-smell-coupling": ("SD-C-1", "SD-C-3"),
            "software-design-behavior-core-smell-adapter-global-coupling": ("SD-C-2", "SD-C-4"),
            "software-design-behavior-core-smell-semantics": ("SD-S-1", "SD-S-4"),
            "software-design-behavior-core-smell-duplicate-semantics": ("SD-S-2",),
            "software-design-behavior-core-smell-evolution": ("SD-E-1", "SD-E-3"),
            "software-design-behavior-core-smell-migration-quality": ("SD-E-2", "SD-Q-2"),
            "software-design-behavior-core-smell-socio-technical": ("SD-Q-1", "SD-T-1"),
            "software-design-behavior-core-smell-unowned-concurrency": ("SD-C-6",),
            "software-design-behavior-core-smell-error-contract-collapse": ("SD-S-5",),
            "software-design-behavior-core-smell-stacked-retries": ("SD-Q-4",),
            "software-design-behavior-csharp-ef-repository-smells": ("csharp.SD-S-1", "csharp.SD-W-1"),
            "software-design-behavior-python-tooling-contract-smells": (
                "python.SD-B-4",
                "python.SD-S-2",
                "python.SD-S-3",
            ),
        }

        for case_id, required_codes in expected.items():
            with self.subTest(case_id=case_id):
                self.assertIn(case_id, behaviors)
                joined_checks = " ".join(behaviors[case_id]["required_checks"])
                joined_forbidden = " ".join(behaviors[case_id]["forbidden_behaviors"])
                for code in required_codes:
                    self.assertIn(code, joined_checks)
                self.assertIn("false positive", joined_forbidden.lower())

    def test_model_pressure_records_smell_catalog_expansion_gate(self) -> None:
        pressure = read(MODEL_PRESSURE)

        self.assertIn("SD-MP-SMELL-1", pressure)
        self.assertIn("accepted smell-catalog rule", pressure)
        self.assertIn("merge-back condition", pressure)

    def test_source_grounding_links_research_without_copying_it(self) -> None:
        grounding = read(SOURCE_GROUNDING)

        for phrase in (
            "Code smells and refactoring",
            "A survey on software smells",
            "Refactoring for Software Design Smells",
            "refactoring.com/catalog",
            "External links ground source roles only",
        ):
            self.assertIn(phrase, grounding)

        for source_link in (
            "sciencedirect.com/science/article/pii/S0164121220300881",
            "spinellis.gr/pubs/jrnl/2018-JSS-smells-survey",
            "oreilly.com/library/view/refactoring-for-software/9780128013977",
            "refactoring.com/catalog",
            "sei.cmu.edu/library/the-architecture-tradeoff-analysis-method-2",
            "dora.dev/capabilities/code-maintainability",
            "dora.dev/capabilities/loosely-coupled-teams",
        ):
            self.assertIn(source_link, grounding)


if __name__ == "__main__":
    unittest.main()
