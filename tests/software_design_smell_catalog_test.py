import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOFTWARE_SKILL = "souroldgeezer-design/skills/software-design"
SMELL_CATALOG = f"{SOFTWARE_SKILL}/references/smell-catalog.md"
BEHAVIOR_CASES = f"{SOFTWARE_SKILL}/references/evals/behavior-cases.jsonl"
MODEL_PRESSURE = f"{SOFTWARE_SKILL}/references/evals/model-pressure.md"
SOURCE_GROUNDING = f"{SOFTWARE_SKILL}/references/source-grounding.md"


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def read_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


def section_for(content: str, heading: str) -> str:
    start = content.index(heading)
    next_heading = re.search(r"\n### `SD-[A-Z]-\d+`", content[start + 1 :])
    if next_heading is None:
        return content[start:]
    return content[start : start + 1 + next_heading.start()]


class SoftwareDesignSmellCatalogTest(unittest.TestCase):
    def test_core_smell_catalog_has_actionable_cards(self) -> None:
        catalog = read(SMELL_CATALOG)
        expected_cards = {
            "SD-W-1": "Speculative abstraction",
            "SD-W-2": "Pass-through layer",
            "SD-B-1": "Responsibility drift",
            "SD-B-3": "Internals leakage",
            "SD-C-1": "Dependency cycle",
            "SD-C-3": "Shared-core gravity",
            "SD-S-1": "Vocabulary split",
            "SD-S-4": "External model collapse",
            "SD-E-1": "Shotgun change",
            "SD-E-3": "Flag pile-up",
            "SD-Q-1": "Unstated quality tradeoff",
            "SD-T-1": "Ownership mismatch",
        }

        for code, title in expected_cards.items():
            with self.subTest(code=code):
                heading = f"### `{code}` - {title}"
                self.assertIn(heading, catalog)
                card = section_for(catalog, heading)
                for field in (
                    "**Signal:**",
                    "**Evidence layer:**",
                    "**False-positive guard:**",
                    "**Smallest action:**",
                    "**Default severity:**",
                ):
                    self.assertIn(field, card)

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
            "software-design-behavior-core-smell-coupling": ("SD-C-1", "SD-C-3"),
            "software-design-behavior-core-smell-semantics": ("SD-S-1", "SD-S-4"),
            "software-design-behavior-core-smell-evolution": ("SD-E-1", "SD-E-3"),
            "software-design-behavior-core-smell-socio-technical": ("SD-Q-1", "SD-T-1"),
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
