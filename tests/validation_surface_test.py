import json
import re
import unittest

from tests.surface_test_lib import REPO_ROOT


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


class ValidationSurfaceTest(unittest.TestCase):
    def test_contributor_guide_links_the_maintainer_documentation(self) -> None:
        contributing = read("docs/contributing.md")

        for guide in (
            "[skill architecture standard](skill-architecture.md)",
            "[evaluation evidence guide](skill-evaluation.md)",
            "[maintenance procedures](maintenance-procedures.md)",
            "[release checklist](release-checklist.md)",
        ):
            with self.subTest(guide=guide):
                self.assertIn(guide, contributing)

        release = read("docs/release-checklist.md")
        self.assertIn("all 16 shared public skills", release)
        self.assertNotIn("docs/refactor/fragmentation-execplan.md", release)

    def test_default_validation_runs_stop_hook_regression_script(self) -> None:
        validation_script = read("scripts/validate-fragmentation.sh")
        readme = read("README.md")

        self.assertIn("bash scripts/test-stop-hooks.sh", validation_script)
        self.assertIn("scripts/test-stop-hooks.sh", readme)

    def test_runtime_guide_links_to_the_operator_dediren_procedure(self) -> None:
        runtime = read("docs/runtime-support.md")

        self.assertIn("[dediren-install.md](../souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md)", runtime)
        self.assertIn("DEDIREN_COMMAND", runtime)
        maintenance = read("docs/maintenance-procedures.md")
        self.assertIn("DEDIREN_RUNTIME_SMOKE=1", maintenance)
        self.assertIn("DEDIREN_COMMAND", maintenance)
        self.assertIn("uv run python -m unittest tests.architecture_dediren_release_test", maintenance)

    def test_readme_guide_links_and_skill_inventory_are_reachable(self) -> None:
        readme = read("README.md")
        for link in ("[using skills](docs/using-skills.md)", "[runtime support](docs/runtime-support.md)", "[contributor guide](docs/contributing.md)"):
            with self.subTest(link=link):
                self.assertIn(link, readme)
        inventory = read("docs/using-skills.md")
        marketplace = json.loads(read(".claude-plugin/marketplace.json"))
        skill_paths = []
        for plugin in marketplace["plugins"]:
            skill_root = "skills"
            skill_paths.extend(str(path.relative_to(REPO_ROOT)) for path in (REPO_ROOT / plugin["name"] / skill_root).glob("*/SKILL.md"))
        self.assertEqual(16, len(skill_paths))
        for path in skill_paths:
            with self.subTest(path=path):
                self.assertIn(f"](../{path})", inventory)
                self.assertTrue((REPO_ROOT / path).is_file())

    def test_readme_local_guides_have_targets_and_requested_anchors(self) -> None:
        readme = read("README.md")
        for target, anchor in (("docs/using-skills.md", "# Using skills"), ("docs/runtime-support.md", "# Runtime support"), ("docs/contributing.md", "# Contributing")):
            with self.subTest(target=target):
                self.assertRegex(readme, rf"\[[^]]+\]\({re.escape(target)}\)")
                self.assertIn(anchor, read(target))


if __name__ == "__main__":
    unittest.main()
