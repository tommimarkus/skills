import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.planning_policy_shared_contract_test import MODULE, leaf, v5_plan

SCRIPT = Path(MODULE.__file__)


def plan_for(write_set, precision=None):
    item = leaf("a", "u1")
    item["write_set"] = write_set
    plan = v5_plan(item)
    if precision:
        plan["precision"] = precision
    return plan


class PinScanTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def write(self, relative, text="x"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def scan(self, plan, roots=("tests",)):
        return MODULE.validate(plan, pin_roots=list(roots), repo_root=self.root)

    def test_no_scan_without_roots(self):
        self.write("tests/t_test.py", "src/mod.py")
        self.assertNotIn("pin_scan", MODULE.validate(plan_for(["src/mod.py"])))

    def test_exact_path_and_unique_basename_pins_warn_under_standard(self):
        self.write("src/mod.py")
        self.write("tests/path_test.py", "open('src/mod.py')")
        self.write("tests/base_test.py", "import mod.py")
        self.write("tests/other_test.py", "nothing")
        result = self.scan(plan_for(["src/mod.py"]))
        self.assertEqual(
            ["tests/base_test.py", "tests/path_test.py"], result["pin_scan"]["leaves"]["a"]
        )
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(2, sum("PLANSCOPE-UNOWNED-PIN" in w for w in result["warnings"]))

    def test_ambiguous_basename_does_not_pin(self):
        self.write("src/mod.py")
        self.write("lib/mod.py")
        self.write("tests/base_test.py", "mod.py")
        self.assertEqual({}, self.scan(plan_for(["src/mod.py"]))["pin_scan"]["leaves"])

    def test_area_prefix_pins_and_owned_files_do_not(self):
        self.write("tests/area_test.py", "see src/pkg/x")
        self.write("tests/mine_test.py", "src/pkg/x")
        plan = plan_for(["src/pkg/**", "tests/mine_test.py"])
        self.assertEqual(["tests/area_test.py"], self.scan(plan)["pin_scan"]["leaves"]["a"])

    def test_strict_makes_unowned_pin_an_approval_error(self):
        self.write("tests/t_test.py", "src/mod.py")
        result = self.scan(plan_for(["src/mod.py"], "strict"))
        self.assertFalse(result["valid"])
        self.assertFalse(result["approval_ready"])
        self.assertTrue(any("PLANSCOPE-UNOWNED-PIN" in e for e in result["errors"]))

    def test_missing_roots_skips_hidden_oversize_and_truncation(self):
        self.write("tests/.hidden/h_test.py", "src/mod.py")
        self.write("tests/node_modules/n.py", "src/mod.py")
        self.write("tests/big_test.py", "src/mod.py" + " " * (1 << 20))
        for index in range(10):
            self.write(f"tests/t{index}_test.py", "src/mod.py")
        scan = self.scan(plan_for(["src/mod.py"]), roots=("tests", "absent", "../out"))["pin_scan"]
        self.assertEqual(["tests"], scan["roots"])
        self.assertEqual(["absent", "../out"], scan["roots_missing"])
        self.assertEqual(8, len(scan["leaves"]["a"]))
        self.assertTrue(scan["truncated"])
        self.assertTrue(all(p.startswith("tests/t") for p in scan["leaves"]["a"]))

    def test_cli_flags(self):
        self.write("tests/t_test.py", "src/mod.py")
        plan_path = self.root / "plan.json"
        plan_path.write_text(json.dumps(plan_for(["src/mod.py"])), encoding="utf-8")
        done = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "validate", str(plan_path), "--pin-roots", "tests",
             "--repo-root", str(self.root)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(["tests/t_test.py"], json.loads(done.stdout)["pin_scan"]["leaves"]["a"])


if __name__ == "__main__":
    unittest.main()
