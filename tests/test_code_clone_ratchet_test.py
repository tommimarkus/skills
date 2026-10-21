"""Ratchet: blocking source clones (`LA-CODE-DUP-1`) never grow.

One whole-repo scan, split into two ceilings: clones with both sides under
tests/ (nothing else gates that tree, which is how its count climbed after the
July dedupe) and clones with either side elsewhere. Git-aware path discovery
keeps ignored trees such as .worktrees/ out. Each ceiling only moves down."""
import unittest

from tests.surface_test_lib import LEAN_AUDIT_SCRIPTS, REPO_ROOT, load_leanaudit_module

TESTS_CEILING = 156
SOURCE_CEILING = 13


def _in_tests(path: str) -> bool:
    return path.startswith("tests/")


class TestCodeCloneRatchetTest(unittest.TestCase):
    def test_blocking_clones_do_not_grow(self) -> None:
        clones = load_leanaudit_module(
            "test_code_clone_ratchet_clones", LEAN_AUDIT_SCRIPTS / "leanaudit" / "clones.py"
        )
        found = clones.scan_dir(
            REPO_ROOT, clones.DEFAULT_MIN_CLONE_TOKENS, REPO_ROOT / ".lean-audit.toml"
        )
        blocking = [clone for clone in found if clone.severity == "block"]
        in_tests = sum(_in_tests(c.path) and _in_tests(c.matched_path) for c in blocking)
        in_source = len(blocking) - in_tests
        with self.subTest(scope="tests"):
            self.assertLessEqual(
                in_tests,
                TESTS_CEILING,
                f"{in_tests} blocking clones within tests/ exceed the ceiling {TESTS_CEILING}: "
                "fold the new duplicate into tests/surface_test_lib.py. When a cleanup lowers "
                "the count, lower TESTS_CEILING to match.",
            )
        with self.subTest(scope="source"):
            self.assertLessEqual(
                in_source,
                SOURCE_CEILING,
                f"{in_source} blocking clones outside tests/ exceed the ceiling "
                f"{SOURCE_CEILING}: extract the shared code or declare it intentional with "
                "`lean-audit:dup-intentional`. When a cleanup lowers the count, lower "
                "SOURCE_CEILING to match.",
            )


if __name__ == "__main__":
    unittest.main()
