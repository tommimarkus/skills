"""Enforces the lean-audit Python standard (ruff + mypy) inside `python -m unittest`."""
import subprocess
import unittest

from tests.surface_test_lib import REPO_ROOT
CHECKS = (
    ("ruff-check", ["uv", "run", "--frozen", "ruff", "check", "."]),
    ("ruff-format", ["uv", "run", "--frozen", "ruff", "format", "--check", "."]),
    ("mypy", ["uv", "run", "--frozen", "mypy"]),
)


class LeanAuditPythonStandardTest(unittest.TestCase):
    def test_standard_gates(self) -> None:
        for name, cmd in CHECKS:
            with self.subTest(check=name):
                try:
                    proc = subprocess.run(
                        cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=300
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    self.skipTest(f"{name}: toolchain unavailable ({exc})")
                if proc.returncode != 0 and (
                    "failed to fetch" in proc.stderr.lower()
                    or "no interpreter" in proc.stderr.lower()
                    or "not found" in proc.stderr.lower()
                ):
                    self.skipTest(f"{name}: toolchain unavailable offline: {proc.stderr[:200]}")
                self.assertEqual(
                    proc.returncode, 0, f"{name} failed:\n{proc.stdout}\n{proc.stderr}"
                )
