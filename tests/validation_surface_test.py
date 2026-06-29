import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


class ValidationSurfaceTest(unittest.TestCase):
    def test_default_validation_runs_stop_hook_regression_script(self) -> None:
        validation_script = read("scripts/validate-fragmentation.sh")
        readme = read("README.md")

        self.assertIn("bash scripts/test-stop-hooks.sh", validation_script)
        self.assertIn("scripts/test-stop-hooks.sh", readme)

    def test_readme_documents_optional_dediren_release_smoke_lane(self) -> None:
        readme = read("README.md")

        self.assertIn("DEDIREN_RELEASE_SMOKE=1", readme)
        self.assertIn(
            "uv run python -m unittest tests.architecture_dediren_release_test",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
