"""Enforces the bundled-scripts Python standard (ruff + mypy) inside `python -m unittest`.

It covers the lean-audit, test-quality-audit, and planning-policy scripts that
`pyproject.toml` scopes ruff and mypy to.
"""
import shutil
import subprocess
import unittest

from tests.surface_test_lib import REPO_ROOT
CHECKS = (
    ("ruff-check", ["uv", "run", "--frozen", "ruff", "check", "."]),
    ("ruff-format", ["uv", "run", "--frozen", "ruff", "format", "--check", "."]),
    ("mypy", ["uv", "run", "--frozen", "mypy"]),
)


class LeanAuditPythonStandardTest(unittest.TestCase):
    @unittest.skipIf(shutil.which("uv") is None, "uv is not installed")
    def test_standard_gates(self) -> None:
        for name, cmd in CHECKS:
            with self.subTest(check=name):
                # Only a missing `uv` skips; a fetch failure, timeout or any
                # non-zero exit is a real gate failure and surfaces the output.
                try:
                    proc = subprocess.run(
                        cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=300
                    )
                except subprocess.TimeoutExpired as exc:
                    self.fail(f"{name} timed out after {exc.timeout}s")
                self.assertEqual(
                    proc.returncode, 0, f"{name} failed:\n{proc.stdout}\n{proc.stderr}"
                )
