import unittest

from tests.surface_test_lib import read, read_jsonl


class ApiDesignArchitectureScopeTest(unittest.TestCase):
    def test_trigger_metadata_names_portfolio_scope_and_matches_claude_agent(self) -> None:
        skill = read("souroldgeezer-design/skills/api-design/SKILL.md")
        agent = read("souroldgeezer-design/agents/api-design.md")
        skill_description = next(
            line for line in skill.split("---", 2)[1].splitlines()
            if line.startswith("description:")
        )
        agent_description = next(
            line for line in agent.split("---", 2)[1].splitlines()
            if line.startswith("description:")
        )

        self.assertEqual(skill_description, agent_description)
        for phrase in (
            "API architecture",
            "portfolio cohesion",
            "fragmentation",
            "sprawl",
            "consolidation",
            "overlap",
            "consumer chattiness",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill_description)

    def test_router_keeps_architecture_invariant_compact_and_conditional(self) -> None:
        skill = read("souroldgeezer-design/skills/api-design/SKILL.md")

        self.assertIn("one canonical HTTP contract per capability", skill)
        self.assertIn("references/procedures/surface-architecture.md", skill)
        self.assertIn("when API surface architecture, overlap, consolidation", skill)

    def test_reference_defines_evidence_bound_architecture_decisions(self) -> None:
        reference = read("souroldgeezer-design/docs/api-reference/api-design.md")

        self.assertIn("API surface architecture", reference)
        self.assertIn("one canonical HTTP contract per capability", reference)
        self.assertIn("Never infer traffic, latency, organizational ownership, or runtime benefit", reference)
        self.assertIn("Keep architecture-model changes delegated through the existing pairing procedure", reference)

    def test_procedure_has_taxonomy_evidence_and_mode_slicing(self) -> None:
        procedure = read(
            "souroldgeezer-design/skills/api-design/references/procedures/surface-architecture.md"
        )

        for code in (
            "SAD-A-capability-overlap",
            "SAD-A-policy-drift",
            "SAD-A-consumer-chattiness",
            "SAD-A-internal-boundary-leak",
            "SAD-A-lifecycle-sprawl",
            "SAD-A-duplicated-aggregation",
        ):
            with self.subTest(code=code):
                self.assertIn(code, procedure)
        for decision in (
            "keep",
            "separate",
            "standardize",
            "aggregate",
            "consolidate",
            "deprecate",
        ):
            with self.subTest(decision=decision):
                self.assertIn(decision, procedure)
        self.assertIn("contract inventories", procedure)
        self.assertIn("consumer journeys", procedure)
        self.assertIn("versions", procedure)
        self.assertIn("gateway/client wiring", procedure)
        self.assertIn("usage/deprecation evidence", procedure)
        self.assertIn("Build", procedure)
        self.assertIn("Extract", procedure)
        self.assertIn("Review", procedure)
        self.assertIn("Lookup", procedure)

    def test_evidence_is_source_grounded_and_covers_trigger_and_behavior(self) -> None:
        source_grounding = read(
            "souroldgeezer-design/skills/api-design/references/source-grounding.md"
        )
        triggers = {
            case["id"]
            for case in read_jsonl(
                "souroldgeezer-design/skills/api-design/references/evals/trigger-cases.jsonl"
            )
        }
        behaviors = {
            case["id"]: case
            for case in read_jsonl(
                "souroldgeezer-design/skills/api-design/references/evals/behavior-cases.jsonl"
            )
        }

        self.assertIn("surface-architecture.md", source_grounding)
        self.assertIn("api-design-trigger-yes-surface-architecture", triggers)
        self.assertIn("api-design-trigger-no-organization-design", triggers)
        self.assertIn("api-design-behavior-build-surface-architecture", behaviors)
        self.assertIn("api-design-behavior-extract-surface-architecture", behaviors)
        self.assertIn("api-design-behavior-review-surface-architecture", behaviors)
        self.assertIn("api-design-behavior-lookup-surface-architecture", behaviors)


if __name__ == "__main__":
    unittest.main()
