import json
import subprocess
import unittest
from pathlib import Path

from tests.surface_test_lib import read_jsonl


ROOT = Path("souroldgeezer-design/skills/software-design")
TRIGGERS = ROOT / "references/evals/trigger-cases.jsonl"
BEHAVIORS = ROOT / "references/evals/behavior-cases.jsonl"


class SoftwareDesignFileLaneEvalTest(unittest.TestCase):
    def test_trigger_cases_cover_file_families_and_source_exclusions(self):
        cases = {row["id"]: row for row in read_jsonl(str(TRIGGERS))}
        for family in ("markdown", "json", "jsonl", "yaml", "toml", "xml", "csv", "ini"):
            with self.subTest(family=family):
                case = cases[f"software-design-trigger-file-edit-{family}"]
                self.assertTrue(case["expected_activation"])
                self.assertIn("File Edit", case["reason"])
        for case_id in ("software-design-trigger-file-edit-source-python", "software-design-trigger-file-edit-source-typescript"):
            with self.subTest(case_id=case_id):
                self.assertTrue(cases[case_id]["expected_activation"])
                self.assertIn("Normal", cases[case_id]["reason"])
                self.assertIn("not select File Edit", cases[case_id]["reason"])

    def test_behavior_cases_cover_dispatch_selection_lifecycle_and_fidelity(self):
        cases = {row["id"]: row for row in read_jsonl(str(BEHAVIORS))}
        expected = {
            "software-design-behavior-file-edit-dispatch": ("early-return", "core reference"),
            "software-design-behavior-file-edit-selection": ("repository-required", "target-specific authority"),
            "software-design-behavior-file-edit-lifecycle": ("fresh cache hit", "expiry boundary"),
            "software-design-behavior-file-edit-fidelity": ("forced refresh", "validated fallback"),
        }
        for case_id, markers in expected.items():
            with self.subTest(case_id=case_id):
                case = cases[case_id]
                checks = " ".join(case["required_checks"])
                forbidden = " ".join(case["forbidden_behaviors"])
                self.assertTrue(case["expected_artifacts"])
                self.assertIn(markers[0], checks)
                self.assertIn(markers[1], checks + forbidden)

    def test_eval_files_are_jsonl_and_ids_are_unique(self):
        for path in (TRIGGERS, BEHAVIORS):
            rows = read_jsonl(str(path))
            self.assertTrue(rows)
            ids = [row["id"] for row in rows]
            self.assertEqual(len(ids), len(set(ids)), path)


class FileLaneStateBoundaryTest(unittest.TestCase):
    script = ROOT / "references/scripts/tool_state.py"

    def _run(self, repo: Path, *args: str) -> dict:
        result = subprocess.run(
            ["python3", str(self.script), "--repo-root", str(repo), *args],
            check=True, text=True, capture_output=True,
        )
        return json.loads(result.stdout)

    def test_cache_lifecycle_exact_boundaries_and_forced_refresh(self):
        with self.subTest("boundary states"):
            import tempfile
            with tempfile.TemporaryDirectory() as directory:
                repo = Path(directory)
                subprocess.run(["git", "init", "-q", str(repo)], check=True)
                from datetime import date, timedelta
                import importlib.util
                spec = importlib.util.spec_from_file_location("tool_state_boundary", self.script)
                module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
                base = date(2026, 1, 1)
                record = {"schema-version":"1", "tool":"jq", "reported-version":"1", "source":"x", "validated-on":base.isoformat(), "refresh-after":(base+timedelta(days=30)).isoformat(), "purge-after":(base+timedelta(days=60)).isoformat(), "state":"valid"}
                self.assertEqual("valid", module.assess("json", {k:[v] for k,v in record.items()}, base+timedelta(days=29))[0])
                self.assertEqual("refresh_due", module.assess("json", {k:[v] for k,v in record.items()}, base+timedelta(days=30))[0])
                self.assertEqual("expired", module.assess("json", {k:[v] for k,v in record.items()}, base+timedelta(days=60))[0])
                stale = dict(record, state="stale", **{"stale-on":(base+timedelta(days=60)).isoformat(), "purge-after":(base+timedelta(days=67)).isoformat()})
                self.assertEqual("stale", module.assess("json", {k:[v] for k,v in stale.items()}, base+timedelta(days=66))[0])
                self.assertEqual("expired", module.assess("json", {k:[v] for k,v in stale.items()}, base+timedelta(days=67))[0])


if __name__ == "__main__":
    unittest.main()
