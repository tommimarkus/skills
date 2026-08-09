import unittest

from tests.surface_test_lib import compact, read, read_jsonl


SOFTWARE_SKILL = "souroldgeezer-design/skills/software-design"


class SoftwareDesignToolSelectionSurfaceTest(unittest.TestCase):
    def test_skill_selects_tools_by_capability_with_bounded_discovery(self) -> None:
        skill = compact(read(f"{SOFTWARE_SKILL}/SKILL.md"))

        for marker in (
            "bounded discovery",
            "repository-configured commands",
            "host-exposed integrations",
            "task fit",
            "authoritative data",
            "structured output",
            "failure and side-effect behavior",
            "maintainability",
            "no universal MCP, CLI, or script ranking",
            "existing suitable tool",
            "human-oriented output",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, skill)

    def test_context7_is_optional_mcp_documentation_evidence(self) -> None:
        skill = compact(read(f"{SOFTWARE_SKILL}/SKILL.md"))

        for marker in (
            "Context7 MCP",
            "resolve the library",
            "query its documentation",
            "local project configuration, installed versions, and actual tool output",
            "project documentation, local help, official sources",
            "Do not install Context7, invoke its CLI, or alter MCP configuration",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, skill)

    def test_craft_standard_preserves_justified_tool_contracts(self) -> None:
        standard = compact(read("docs/skill-architecture.md"))

        for marker in (
            "capabilities and selection criteria",
            "optional MCP documentation services",
            "repository policy, authoritative-state access, compatibility, or operation fragility",
            "Dediren MCP routing",
            "provider lifecycle tooling order",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, standard)

    def test_grounding_and_behavior_evidence_cover_tool_selection_paths(self) -> None:
        grounding = read(f"{SOFTWARE_SKILL}/references/source-grounding.md")
        pressure = read(f"{SOFTWARE_SKILL}/references/evals/model-pressure.md")
        behaviors = {
            record["id"]: record
            for record in read_jsonl(f"{SOFTWARE_SKILL}/references/evals/behavior-cases.jsonl")
        }

        self.assertIn("https://github.com/upstash/context7", grounding)
        self.assertIn("resolve-library-id", grounding)
        self.assertIn("query-docs", grounding)
        self.assertIn("capability-based tool-selection expansion", pressure)

        expected = {
            "software-design-behavior-tool-selection-existing-structured":
                ("use the existing structured-output tool", "draft an ad hoc parser"),
            "software-design-behavior-tool-selection-context7-available":
                ("resolve the library and query relevant documentation", "treat Context7 as runtime authority"),
            "software-design-behavior-tool-selection-context7-absent":
                ("continue through project documentation", "install Context7"),
            "software-design-behavior-tool-selection-bounded-fallback":
                ("smallest validated fallback", "crawl the machine"),
            "software-design-behavior-tool-selection-repository-contract":
                ("preserve the repository-required tool", "replace the named contract"),
        }
        for case_id, (required, forbidden) in expected.items():
            with self.subTest(case_id=case_id):
                self.assertIn(case_id, behaviors)
                checks = " ".join(behaviors[case_id]["required_checks"])
                forbidden_behaviors = " ".join(behaviors[case_id]["forbidden_behaviors"])
                self.assertIn(required, checks)
                self.assertIn(forbidden, forbidden_behaviors)

    def test_readme_explains_optional_context7_path(self) -> None:
        readme = compact(read("README.md"))

        self.assertIn("capability-based tool selection", readme)
        self.assertIn("Context7 MCP is already exposed", readme)
        self.assertIn("does not install or configure Context7", readme)


if __name__ == "__main__":
    unittest.main()
