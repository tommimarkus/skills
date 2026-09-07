import unittest

from tests.surface_test_lib import REPO_ROOT


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


class ValidationSurfaceTest(unittest.TestCase):
    def test_contributor_guide_links_the_maintainer_documentation(self) -> None:
        contributing = read("docs/contributing.md")

        for guide in (
            "skill-architecture.md",
            "skill-evaluation.md",
            "maintenance-procedures.md",
            "release-checklist.md",
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

    def test_readme_documents_optional_dediren_runtime_smoke_lane(self) -> None:
        readme = read("README.md")

        self.assertIn("DEDIREN_RUNTIME_SMOKE=1", readme)
        # The lane no longer presumes an operator-installed runtime: it goes
        # through the launcher's own resolution, so the README has to say which
        # variable pins the executable under test.
        self.assertIn("resolves Dediren through the launcher", readme)
        self.assertIn("DEDIREN_COMMAND", readme)
        self.assertIn(
            "uv run python -m unittest tests.architecture_dediren_release_test",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
