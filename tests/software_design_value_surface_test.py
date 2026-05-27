import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOFTWARE_SKILL = "souroldgeezer-design/skills/software-design"


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def read_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


class SoftwareDesignValueSurfaceTest(unittest.TestCase):
    def test_skill_guides_design_into_implementation_loop(self) -> None:
        skill = read(f"{SOFTWARE_SKILL}/SKILL.md")
        compact = " ".join(skill.split())

        self.assertIn("design decision", compact)
        self.assertIn("implement the smallest coherent move", compact)
        self.assertIn("review diff against the design decision", compact)
        self.assertIn("validate", compact)

    def test_extensions_define_concrete_smell_codes(self) -> None:
        expected_codes = {
            "dotnet": ["dotnet.SD-C-1", "dotnet.SD-W-1", "dotnet.SD-Q-1"],
            "java": ["java.SD-B-1", "java.SD-C-2", "java.SD-W-1"],
            "python": ["python.SD-B-4", "python.SD-C-1", "python.SD-S-2"],
            "rust": ["rust.SD-B-3", "rust.SD-C-2", "rust.SD-Q-1"],
            "shell-script": ["shell.SD-B-1", "shell.SD-C-1", "shell.SD-S-4"],
            "typescript": ["typescript.SD-B-2", "typescript.SD-C-2", "typescript.SD-S-1"],
        }

        for extension, codes in expected_codes.items():
            content = read(f"{SOFTWARE_SKILL}/extensions/{extension}.md")
            with self.subTest(extension=extension):
                for code in codes:
                    self.assertIn(code, content)
                concrete_codes = set(re.findall(rf"`?{re.escape(codes[0].split('.')[0])}\.SD-[A-Z]-\d`?", content))
                self.assertGreaterEqual(len(concrete_codes), 4)

    def test_eval_pack_covers_development_value_and_delegation_boundaries(self) -> None:
        triggers = {
            record["id"]: record
            for record in read_jsonl(f"{SOFTWARE_SKILL}/references/evals/trigger-cases.jsonl")
        }
        behaviors = {
            record["id"]: record
            for record in read_jsonl(f"{SOFTWARE_SKILL}/references/evals/behavior-cases.jsonl")
        }

        for case_id in (
            "software-design-trigger-no-typescript-ui",
            "software-design-trigger-no-java-dependency-security",
            "software-design-trigger-no-rust-unsafe-audit",
            "software-design-trigger-no-python-api-route",
            "software-design-trigger-no-terraform-module",
        ):
            self.assertIn(case_id, triggers)
            self.assertFalse(triggers[case_id]["expected_activation"])

        behavior = behaviors["software-design-behavior-typescript-build-implementation"]
        checks = " ".join(behavior["required_checks"])
        forbidden = " ".join(behavior["forbidden_behaviors"])
        self.assertIn("design decision", checks)
        self.assertIn("review the diff", checks)
        self.assertIn("jump straight to code", forbidden)

    def test_model_pressure_justifies_stack_extensions(self) -> None:
        pressure = read(f"{SOFTWARE_SKILL}/references/evals/model-pressure.md")

        for case_id in ("SD-MP-TS-1", "SD-MP-RS-1", "SD-MP-JAVA-1", "SD-MP-DOTNET-1"):
            self.assertIn(case_id, pressure)

        for phrase in ("baseline failure", "accepted extension rule", "retest", "merge-back condition"):
            self.assertIn(phrase, pressure)

    def test_source_grounding_covers_all_extension_families(self) -> None:
        grounding = read(f"{SOFTWARE_SKILL}/references/source-grounding.md")

        for heading in (".NET facts", "Shell facts", "Python facts", "Rust facts", "Java facts", "TypeScript facts"):
            self.assertIn(heading, grounding)

    def test_pattern_catalog_has_high_impact_shortlist_with_guardrails(self) -> None:
        catalog = read(f"{SOFTWARE_SKILL}/references/pattern-catalog.md")

        for pattern in (
            "Anti-Corruption Layer / Adapter",
            "Strategy / Policy Object",
            "Composition Root / Dependency Injection / Factory",
            "Facade",
            "State Machine",
            "Pipes and Filters / Pipeline",
            "Publish-Subscribe / Observer / Domain Events",
            "Domain Model / Aggregate",
            "Repository + Unit of Work",
            "Strangler Fig / Branch by Abstraction",
        ):
            self.assertIn(pattern, catalog)

        for phrase in (
            "Track record",
            "Current force",
            "Sustainable lift",
            "Misuse guardrail",
            "Exit condition",
        ):
            self.assertIn(phrase, catalog)

    def test_pattern_value_is_covered_by_evals_and_grounding(self) -> None:
        behaviors = {
            record["id"]: record
            for record in read_jsonl(f"{SOFTWARE_SKILL}/references/evals/behavior-cases.jsonl")
        }
        pressure = read(f"{SOFTWARE_SKILL}/references/evals/model-pressure.md")
        grounding = read(f"{SOFTWARE_SKILL}/references/source-grounding.md")

        self.assertIn("software-design-behavior-pattern-high-impact-selection", behaviors)
        behavior = behaviors["software-design-behavior-pattern-high-impact-selection"]
        checks = " ".join(behavior["required_checks"])
        forbidden = " ".join(behavior["forbidden_behaviors"])
        self.assertIn("current force", checks)
        self.assertIn("track record", checks)
        self.assertIn("pattern shopping", forbidden)

        self.assertIn("SD-MP-PAT-1", pressure)
        self.assertIn("Pattern sources", grounding)
        self.assertIn("martinfowler.com/eaaCatalog", grounding)
        self.assertIn("enterpriseintegrationpatterns.com", grounding)


if __name__ == "__main__":
    unittest.main()
