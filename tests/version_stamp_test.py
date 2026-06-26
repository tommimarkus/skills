import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "scripts" / "version_stamp.py"


def load_module():
    spec = importlib.util.spec_from_file_location("version_stamp", MODULE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["version_stamp"] = module
    spec.loader.exec_module(module)
    return module


vs = load_module()


class ComputeNextTest(unittest.TestCase):
    def test_increments_micro_within_same_month(self):
        self.assertEqual(vs.compute_next("2026.06.3", "2026.06"), "2026.06.4")

    def test_resets_micro_for_new_month(self):
        self.assertEqual(vs.compute_next("2026.05.2", "2026.06"), "2026.06.0")

    def test_resets_for_pre_calver_semver(self):
        self.assertEqual(vs.compute_next("2.8.1", "2026.06"), "2026.06.0")

    def test_first_bump_in_month_from_zero(self):
        self.assertEqual(vs.compute_next("2026.06.0", "2026.06"), "2026.06.1")

    def test_rejects_month_older_than_current(self):
        with self.assertRaises(ValueError):
            vs.compute_next("2026.07.0", "2026.06")


class VersionDiffTest(unittest.TestCase):
    def test_no_change(self):
        a = {"x": "2026.06.0"}
        self.assertEqual(vs.version_diff(a, dict(a)), [])

    def test_detects_bumped_cell(self):
        base = {"x": "2026.06.3"}
        head = {"x": "2026.06.4"}
        self.assertEqual(vs.version_diff(base, head), [("x", "2026.06.3", "2026.06.4")])

    def test_ignores_keys_absent_in_base(self):
        self.assertEqual(vs.version_diff({}, {"new": "2026.06.0"}), [])


class CurrentMonthTest(unittest.TestCase):
    def test_format(self):
        self.assertRegex(vs.current_month(), r"^\d{4}\.\d{2}$")


if __name__ == "__main__":
    unittest.main()
