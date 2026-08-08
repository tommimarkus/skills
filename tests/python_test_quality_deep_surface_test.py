import json
import unittest

from tests.surface_test_lib import REPO_ROOT, compact, read

SKILL = "souroldgeezer-audit/skills/test-quality-audit/SKILL.md"
INDEX = "souroldgeezer-audit/skills/test-quality-audit/extensions/index.md"
PYTHON_CORE = "souroldgeezer-audit/skills/test-quality-audit/references/extensions/python/core.md"
PYTHON_DEEP = "souroldgeezer-audit/skills/test-quality-audit/references/extensions/python/deep.md"
SCENARIOS = REPO_ROOT / "tests" / "skill_load_cost" / "scenarios.json"


class PythonTestQualityDeepSurfaceTest(unittest.TestCase):
    def test_deep_guidance_is_split_from_quick_python_core(self) -> None:
        core = read(PYTHON_CORE)
        deep = read(PYTHON_DEEP)

        self.assertIn("Deep-mode procedures", core)
        self.assertIn("[`deep.md`](deep.md)", core)
        for heading in (
            "## SUT Surface Enumeration",
            "## Determinism Verification",
            "## Mutation Tool",
        ):
            self.assertNotIn(heading, core)

        self.assertIn("# Extension: Python — deep (Deep mode only)", deep)
        for marker in (
            "## SUT surface enumeration",
            "Gap-API",
            "Gap-Route",
            "Gap-Migration",
            "Gap-Throw",
            "Gap-Validate",
            "## Determinism verification",
            "pytest -q --maxfail=1",
            "## Mutation tool",
            "Mutmut",
            "mutmut run",
        ):
            self.assertIn(marker, deep)

    def test_routing_keeps_deep_opt_in_and_preserves_project_runner_posture(self) -> None:
        skill = read(SKILL)
        index = read(INDEX)
        deep = read(PYTHON_DEEP)

        self.assertIn("core.md`](references/extensions/python/core.md) + selected addon", skill)
        self.assertIn("In Deep mode only, also load the matched stack's `deep.md`", skill)
        self.assertIn("references/extensions/python/deep.md", index)
        self.assertIn("Quick mode never loads it", index)
        deep_compact = compact(deep)
        self.assertIn("project's documented test runner", deep_compact)
        self.assertIn("instead of introducing pytest", deep_compact)

        mutation = deep_compact[deep_compact.index("## Mutation tool") :]
        self.assertIn("project-configured mutation tool", mutation)
        self.assertIn("Preferred", mutation)
        self.assertIn("Mutmut fallback", mutation)
        self.assertIn("only after the user accepts the fallback path", mutation)
        self.assertIn("documented development-dependency mechanism", mutation)
        self.assertLess(
            mutation.index("project-configured mutation tool"),
            mutation.index("Mutmut fallback"),
        )
        self.assertNotIn("uv add --dev mutmut", mutation)
        self.assertNotIn("python -m pip install mutmut", mutation)
        self.assertNotIn("extract pure logic into import-safe modules", mutation)
        self.assertIn("skip the affected target and disclose the limitation", mutation)
        parser = mutation[mutation.index("### Output parser notes") :]
        self.assertIn("project-configured tool", parser)
        self.assertIn("Only for the accepted Mutmut fallback", parser)
        self.assertLess(parser.index("project-configured tool"), parser.index("mutmut results"))

    def test_load_cost_scenarios_are_bounded_quick_vs_deep(self) -> None:
        scenarios = {
            scenario["id"]: scenario
            for scenario in json.loads(SCENARIOS.read_text(encoding="utf-8"))
        }
        quick = scenarios["quick-python-unit"]["files"]
        deep = scenarios["deep-python-suite"]["files"]
        core = PYTHON_CORE
        addon = (
            "souroldgeezer-audit/skills/test-quality-audit/"
            "references/extensions/python/unit.md"
        )
        integration = (
            "souroldgeezer-audit/skills/test-quality-audit/"
            "references/extensions/python/integration.md"
        )

        self.assertEqual(
            quick,
            [
                SKILL,
                "souroldgeezer-audit/docs/audit-reference/audit-craft.md",
                "souroldgeezer-audit/docs/quality-reference/unit-testing.md",
                core,
                addon,
            ],
        )
        self.assertNotIn(PYTHON_DEEP, quick)
        self.assertIn(PYTHON_DEEP, deep)
        self.assertIn(core, deep)
        self.assertIn(integration, deep)
        self.assertEqual(
            [path for path in deep if "/extensions/python/" in path and path.endswith(".md")],
            [
                core,
                PYTHON_DEEP,
                integration,
            ],
        )
        self.assertEqual(len(quick), 5)
        self.assertEqual(len(deep), 8)


if __name__ == "__main__":
    unittest.main()
