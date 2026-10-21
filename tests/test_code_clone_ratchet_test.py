"""Ratchet: blocking source clones (`LA-CODE-DUP-1`) in tests/ never grow.

No other gate scans tests/, which is how its clone count climbed after the
July dedupe. The ceiling only moves down."""
import unittest

from tests.surface_test_lib import LEAN_AUDIT_SCRIPTS, REPO_ROOT, load_leanaudit_module

CEILING = 161


class TestCodeCloneRatchetTest(unittest.TestCase):
    def test_blocking_clones_in_tests_do_not_grow(self) -> None:
        clones = load_leanaudit_module(
            "test_code_clone_ratchet_clones", LEAN_AUDIT_SCRIPTS / "leanaudit" / "clones.py"
        )
        found = clones.scan_dir(
            REPO_ROOT / "tests", clones.DEFAULT_MIN_CLONE_TOKENS, REPO_ROOT / ".lean-audit.toml"
        )
        blocking = sum(clone.severity == "block" for clone in found)
        self.assertLessEqual(
            blocking,
            CEILING,
            f"{blocking} blocking clones in tests/ exceed the ceiling {CEILING}: fold the new "
            "duplicate into tests/surface_test_lib.py. When a cleanup lowers the count, lower "
            "CEILING to match.",
        )


if __name__ == "__main__":
    unittest.main()
