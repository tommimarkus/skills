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

    def test_test_quality_mutation_guidance_is_deep_only(self) -> None:
        skill = read("souroldgeezer-audit/skills/test-quality-audit/SKILL.md")
        node_core = read(
            "souroldgeezer-audit/skills/test-quality-audit/references/extensions/nodejs/core.md"
        )
        dotnet_core = read(
            "souroldgeezer-audit/skills/test-quality-audit/references/extensions/dotnet/core.md"
        )
        node_mutation = read(
            "souroldgeezer-audit/skills/test-quality-audit/references/procedures/mutation-nodejs.md"
        )
        dotnet_mutation = read(
            "souroldgeezer-audit/skills/test-quality-audit/references/procedures/mutation-dotnet.md"
        )

        self.assertIn("mutation-nodejs.md", skill)
        self.assertIn("mutation-dotnet.md", skill)
        self.assertIn("../../procedures/mutation-nodejs.md", node_core)
        self.assertIn("../../procedures/mutation-dotnet.md", dotnet_core)
        self.assertNotIn("Stryker JS cannot mutate every", node_core)
        self.assertNotIn("Stryker.NET cannot mutate every", dotnet_core)
        self.assertIn("Stryker JS cannot mutate every", node_mutation)
        self.assertIn("Stryker.NET cannot mutate every", dotnet_mutation)

    def test_github_issue_lifecycle_points_to_repo_guidance_for_sync_surfaces(
        self,
    ) -> None:
        overlay = read(".claude/skills/github-issue-lifecycle/SKILL.md")

        self.assertIn("AGENTS.md", overlay)
        self.assertIn("CLAUDE.md", overlay)
        self.assertIn("docs/skill-architecture.md", overlay)
        repeated_surface_names = [
            "skills/<skill>/agents/openai.yaml",
            "both plugin manifests",
            ".claude-plugin/marketplace.json",
            "AGENTS.md when Codex entry rules change",
        ]
        for text in repeated_surface_names:
            with self.subTest(text=text):
                self.assertNotIn(text, overlay)


if __name__ == "__main__":
    unittest.main()
