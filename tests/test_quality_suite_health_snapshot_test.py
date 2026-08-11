import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, load_script_module, write_fixture


SCRIPT = (
    REPO_ROOT
    / "souroldgeezer-audit/skills/test-quality-audit/references/scripts/suite_health_snapshot.py"
)


class SuiteHealthSnapshotTest(unittest.TestCase):
    def run_snapshot(self, content: str) -> dict:
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = Path(temporary_directory) / "results.xml"
            write_fixture(report, content)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--junit", str(report)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def test_snapshot_aggregates_testsuites_statuses_times_and_slow_cases(self) -> None:
        snapshot = self.run_snapshot(
            """
            <testsuites>
              <testsuite name="unit" time="10">
                <testcase classname="alpha" name="fast" time="1" />
                <testcase classname="alpha" name="skip" time="2"><skipped /></testcase>
                <testcase classname="beta" name="failure" time="3"><failure>secret failure body</failure></testcase>
              </testsuite>
              <testsuite name="integration" time="20">
                <testcase classname="beta" name="error" time="4"><error>secret error body</error></testcase>
                <testcase classname="gamma" name="negative" time="-5" />
              </testsuite>
            </testsuites>
            """
        )

        self.assertEqual("suite-health-snapshot-v1", snapshot["schema"])
        self.assertEqual(
            {"total": 5, "passed": 2, "skipped": 1, "failed": 1, "error": 1},
            snapshot["testcase_statuses"],
        )
        self.assertEqual(30.0, snapshot["reported_suite_time_seconds"])
        self.assertEqual(10.0, snapshot["testcase_time_seconds"])
        self.assertEqual(
            {"p50": 2.0, "p90": 4.0, "p95": 4.0, "p99": 4.0, "max": 4.0},
            snapshot["testcase_duration_percentiles_seconds"],
        )
        self.assertEqual(
            {"top_1_percent": 0.4, "top_5_percent": 0.4, "top_10_percent": 0.4},
            snapshot["testcase_runtime_shares"],
        )
        self.assertEqual(
            [
                {"classname": "beta", "name": "error", "time_seconds": 4.0},
                {"classname": "beta", "name": "failure", "time_seconds": 3.0},
                {"classname": "alpha", "name": "skip", "time_seconds": 2.0},
                {"classname": "alpha", "name": "fast", "time_seconds": 1.0},
                {"classname": "gamma", "name": "negative", "time_seconds": 0.0},
            ],
            snapshot["slow_testcases"],
        )
        self.assertNotIn("secret failure body", json.dumps(snapshot))
        self.assertNotIn("secret error body", json.dumps(snapshot))

    def test_snapshot_accepts_a_single_testsuite_and_bounds_slow_identities(self) -> None:
        cases = "\n".join(
            f'<testcase classname="suite" name="case-{number}" time="{number}" />'
            for number in range(25)
        )
        snapshot = self.run_snapshot(f'<testsuite name="suite" time="99">{cases}</testsuite>')

        self.assertEqual(25, snapshot["testcase_statuses"]["total"])
        self.assertEqual(99.0, snapshot["reported_suite_time_seconds"])
        self.assertEqual(300.0, snapshot["testcase_time_seconds"])
        self.assertEqual(20, len(snapshot["slow_testcases"]))
        self.assertEqual("case-24", snapshot["slow_testcases"][0]["name"])
        self.assertEqual("case-5", snapshot["slow_testcases"][-1]["name"])

    def test_usage_malformed_and_empty_documents_exit_two(self) -> None:
        module = load_script_module("suite_health_snapshot", SCRIPT)
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = Path(temporary_directory) / "bad.xml"
            report.write_text("<testsuite>", encoding="utf-8")
            self.assertEqual(2, module.main(["--junit", str(report)]))
            report.write_text("<testsuites />", encoding="utf-8")
            self.assertEqual(2, module.main(["--junit", str(report)]))
            report.write_text("<testsuite><testcase /></testsuite>", encoding="utf-8")
            self.assertEqual(2, module.main(["--junit", str(report), "--junit", str(report)]))
        self.assertEqual(2, module.main([]))

    def test_output_is_capped_at_sixteen_kib(self) -> None:
        module = load_script_module("suite_health_snapshot_cap", SCRIPT)
        root = module.parse_junit(
            "<testsuite time=\"1\">"
            + "".join(
                f'<testcase classname="{number * "x"}" name="{number * "y"}" time="1" />'
                for number in range(1, 40)
            )
            + "</testsuite>"
        )
        self.assertLessEqual(len(module.render_snapshot(root).encode("utf-8")), 16 * 1024)


if __name__ == "__main__":
    unittest.main()
