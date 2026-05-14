import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def read_jsonl(relative_path: str) -> list[dict]:
    records = []
    for line in read(relative_path).splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


class SkillLeanRemediationTest(unittest.TestCase):
    def test_api_design_router_is_compact_and_procedure_driven(self) -> None:
        skill = read("souroldgeezer-design/skills/api-design/SKILL.md")

        self.assertLessEqual(len(skill.splitlines()), 150)
        self.assertIn("references/procedures/preflight.md", skill)
        self.assertIn("references/procedures/project-assimilation.md", skill)
        self.assertIn("references/procedures/architecture-pairing.md", skill)
        self.assertIn("references/procedures/red-flags.md", skill)
        self.assertEqual(skill.count("docs/architecture/<feature>.dediren/"), 2)

        moved_sections = [
            "### Framework-agnostic discovery",
            "### Stack-specific discovery",
            "### Mapping existing infrastructure to reference rules",
            "### Conflict handling",
            "## Red flags",
        ]
        for section in moved_sections:
            with self.subTest(section=section):
                self.assertNotIn(section, skill)

    def test_api_design_preflight_defaults_continue_without_forced_questions(
        self,
    ) -> None:
        preflight = read(
            "souroldgeezer-design/skills/api-design/references/procedures/preflight.md"
        )
        behavior_cases = read_jsonl(
            "souroldgeezer-design/skills/api-design/references/evals/behavior-cases.jsonl"
        )
        case_ids = {record["id"] for record in behavior_cases}

        self.assertIn(
            "Apply the listed defaults when the user has not supplied an answer.",
            preflight,
        )
        self.assertIn("Ask only when a default would be unsafe", preflight)
        self.assertIn("api-design-behavior-greenfield-defaults", case_ids)

    def test_pr_ops_uses_reference_core_workflow(self) -> None:
        skill = read("souroldgeezer-ops/skills/pr-ops/SKILL.md")
        core = read("souroldgeezer-ops/skills/pr-ops/references/core-workflow.md")

        self.assertLessEqual(len(skill.splitlines()), 125)
        self.assertIn("references/core-workflow.md", skill)

        moved_headings = [
            "## Evidence Contract",
            "## Queue Limits",
            "## Authority And Ledger",
            "## Normal Flow",
            "## Ask Vs Continue",
            "## Escalation Gates",
            "## Output",
        ]
        for heading in moved_headings:
            with self.subTest(heading=heading):
                self.assertNotIn(heading, skill)
                self.assertIn(heading, core)


if __name__ == "__main__":
    unittest.main()
