# lean-audit:dup-intentional — surface-verification bodies whose entire content is literal paths and strings the tokenizer normalizes to STR; the shared read/read_jsonl helpers are already imported from surface_test_lib, so remaining matches are read()+assert scaffolds around distinct literals
import unittest

from tests.surface_test_lib import assert_phrases, read, read_jsonl, section


class SkillLeanRemediationTest(unittest.TestCase):
    def test_api_design_router_is_compact_and_procedure_driven(self) -> None:
        skill = read("souroldgeezer-design/skills/api-design/SKILL.md")

        self.assertLessEqual(len(skill.splitlines()), 150)
        self.assertIn("references/procedures/preflight.md", skill)
        self.assertIn("references/procedures/project-assimilation.md", skill)
        self.assertIn("references/procedures/architecture-pairing.md", skill)
        self.assertIn("references/procedures/red-flags.md", skill)
        self.assertEqual(skill.count("docs/architecture/<feature>.dediren/"), 2)
        self.assertIn("Existing API with no requested change", skill)
        self.assertIn("defaults to Extract", skill)
        self.assertIn("New endpoint or feature defaults to Build", skill)
        self.assertIn("they never weaken the core reference", skill)

        procedures = "souroldgeezer-design/skills/api-design/references/procedures/"
        assimilation = read(procedures + "project-assimilation.md")
        red_flags = read(procedures + "red-flags.md")
        moved_sections = {
            "### Framework-agnostic discovery": (assimilation, "## Discovery"),
            "### Stack-specific discovery": (assimilation, "## Discovery"),
            "### Mapping existing infrastructure to reference rules": (assimilation, "## Reuse Or Replace"),
            "### Conflict handling": (assimilation, "## Conflict Handling"),
            "## Red flags": (red_flags, "# API Design Red Flags"),
        }
        for moved, (destination, heading) in moved_sections.items():
            with self.subTest(section=moved):
                self.assertNotIn(moved, skill)
                section(destination, heading)

    def test_api_design_preflight_defaults_continue_without_forced_questions(
        self,
    ) -> None:
        preflight = read(
            "souroldgeezer-design/skills/api-design/references/procedures/preflight.md"
        )
        behavior_cases = read_jsonl(
            "souroldgeezer-design/skills/api-design/references/evals/behavior-cases.jsonl"
        )
        case = next(
            record
            for record in behavior_cases
            if record["id"] == "api-design-behavior-greenfield-defaults"
        )

        assert_phrases(
            self,
            preflight.split("\n## ", 1)[0],
            (
                "Apply the listed defaults when the user has not supplied an answer.",
                "Ask only when a default would be unsafe",
            ),
        )
        self.assertIn(
            "apply safe defaults instead of asking unnecessary preflight questions",
            case["required_checks"],
        )

    def test_pr_ops_uses_reference_core_workflow(self) -> None:
        skill = read("souroldgeezer-ops/skills/pr-ops/SKILL.md")
        core = read("souroldgeezer-ops/skills/pr-ops/references/core-workflow.md")

        self.assertLessEqual(len(skill.splitlines()), 125)
        self.assertIn("references/core-workflow.md", skill)
        self.assertIn("A single pending-check retry is never completion", skill)

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
        dotnet_deep = read(
            "souroldgeezer-audit/skills/test-quality-audit/references/extensions/dotnet/deep.md"
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
        # The .NET mutation-tool declaration lives in the Deep-only pack, so the
        # procedure link is reached from there rather than from the always-loaded core.
        self.assertIn("../../procedures/mutation-dotnet.md", dotnet_deep)
        self.assertNotIn("../../procedures/mutation-dotnet.md", dotnet_core)
        self.assertNotIn("Stryker JS cannot mutate every", node_core)
        self.assertNotIn("Stryker.NET cannot mutate every", dotnet_core)
        self.assertIn("Stryker JS cannot mutate every", node_mutation)
        self.assertIn("Stryker.NET cannot mutate every", dotnet_mutation)

    def test_github_issue_lifecycle_points_to_repo_guidance_for_sync_surfaces(
        self,
    ) -> None:
        overlay = read("internal-skills/github-issue-lifecycle/SKILL.md")

        self.assertNotIn("AGENTS.md", overlay)
        assert_phrases(
            self,
            overlay,
            (
                "For sync-surface decisions, follow `CLAUDE.md` and "
                "`docs/skill-architecture.md` instead of duplicating the repo-wide list here.",
            ),
            heading="## Repo-Specific Gates",
        )
        repeated_surface_names = [
            "skills/<skill>/agents/openai.yaml",
            "both plugin manifests",
            ".claude-plugin/marketplace.json",
            ".codex/agents",
        ]
        for text in repeated_surface_names:
            with self.subTest(text=text):
                self.assertNotIn(text, overlay)


if __name__ == "__main__":
    unittest.main()
