import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "planning_policy_workflow_report.py"


def load_reporter():
    spec = importlib.util.spec_from_file_location("planning_policy_workflow_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


CONDITIONS = {
    "fixture_sha256": digest("fixture"),
    "oracle_sha256": digest("oracle"),
    "host": {"name": "codex", "version": "test", "profile": "workspace-write"},
    "coordinator": {"model": "gpt-5.6-sol", "effort": "high"},
    "worker_mapping": {"standard": {"model": "gpt-5.6-terra", "effort": "medium"}},
}


def trial(identifier: str, variant: str, sequence: int, *, usage=True, outcome="completed", conditions=None):
    worker = {
        "actor_id": f"{identifier}-worker",
        "step_id": "evaluation",
        "attempt_id": f"{identifier}-attempt",
        "role": "worker",
        "usage": {"input_tokens": 10, "output_tokens": 5, "cached_input_tokens": 2, "total_tokens": 15}
        if usage
        else None,
    }
    return {
        "trial_id": identifier,
        "variant": variant,
        "sequence": sequence,
        "conditions": conditions or CONDITIONS,
        "limits": {"worker_leaves": 2, "worker_attempts": 4, "minutes": 15},
        "counts": {"worker_leaves": 1, "worker_attempts": 1, "failed_attempts": 0, "retries": 0, "escalations": 0, "dispatches": 1},
        "sources": [{"path": "usage/summary.json", "sha256": digest(identifier)}],
        "actors": [
            {"actor_id": f"{identifier}-parent", "step_id": "parent", "attempt_id": "run", "role": "coordinator", "usage": {"input_tokens": 20, "output_tokens": 10, "cached_input_tokens": 0, "total_tokens": 30}},
            worker,
        ],
        "execution": {"outcome": outcome, "lifecycle": "cleaned", "oracle": "passed", "elapsed_seconds": 12},
    }


class WorkflowReportTest(unittest.TestCase):
    def setUp(self):
        self.reporter = load_reporter()

    def report(self, records):
        return self.reporter.build_report({"schema": "planning-policy-workflow-manifest/v1", "trials": records})

    def test_missing_worker_usage_is_visible_but_blocks_comparison(self):
        report = self.report([trial("baseline-1", "baseline", 1, usage=False)])
        self.assertEqual(report["trials"][0]["usage"]["total_tokens"], None)
        self.assertFalse(report["comparison"]["comparable"])
        self.assertIn("missing_complete_usage", report["comparison"]["reasons"])

    def test_duplicate_actor_identity_is_rejected(self):
        record = trial("baseline-1", "baseline", 1)
        record["actors"].append(dict(record["actors"][1]))
        with self.assertRaisesRegex(ValueError, "duplicate actor identity"):
            self.report([record])

    def test_mismatched_conditions_are_incomparable(self):
        changed = json.loads(json.dumps(CONDITIONS))
        changed["coordinator"]["model"] = "another-model"
        report = self.report([trial("baseline-1", "baseline", 1), trial("candidate-1", "candidate", 2, conditions=changed)])
        self.assertFalse(report["comparison"]["comparable"])
        self.assertIn("mismatched_conditions", report["comparison"]["reasons"])

    def test_cheaper_failed_trial_never_claims_improvement(self):
        failed = trial("candidate-1", "candidate", 2, outcome="failed")
        failed["actors"][0]["usage"] = {"input_tokens": 1, "output_tokens": 1, "cached_input_tokens": 0, "total_tokens": 2}
        failed["actors"][1]["usage"] = {"input_tokens": 1, "output_tokens": 1, "cached_input_tokens": 0, "total_tokens": 2}
        report = self.report([trial("baseline-1", "baseline", 1), failed])
        self.assertFalse(report["comparison"]["comparable"])
        self.assertIn("non_successful_trial", report["comparison"]["reasons"])
        self.assertNotIn("improved", report["comparison"])

    def test_complete_matched_trials_report_medians_ranges_and_paired_delta(self):
        records = [
            trial("baseline-1", "baseline", 1),
            trial("candidate-1", "candidate", 2),
            trial("candidate-2", "candidate", 3),
            trial("baseline-2", "baseline", 4),
        ]
        records[1]["actors"][0]["usage"].update({"input_tokens": 10, "output_tokens": 10, "total_tokens": 20})
        records[1]["actors"][1]["usage"].update({"input_tokens": 5, "output_tokens": 5, "total_tokens": 10})
        report = self.report(records)
        self.assertTrue(report["comparison"]["comparable"])
        self.assertIn("median_total_tokens", report["variants"]["baseline"])
        self.assertIn("repeat_range_total_tokens", report["variants"]["baseline"])
        self.assertEqual(len(report["comparison"]["paired_deltas"]), 2)

    def test_unknown_counters_stay_null_and_output_is_bounded(self):
        record = trial("baseline-1", "baseline", 1)
        record["actors"][0]["usage"] = {"input_tokens": None, "output_tokens": None, "cached_input_tokens": None, "total_tokens": None}
        report = self.report([record])
        self.assertIsNone(report["trials"][0]["usage"]["total_tokens"])
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "manifest.json"
            output = Path(temporary) / "report.json"
            manifest.write_text(json.dumps({"schema": "planning-policy-workflow-manifest/v1", "trials": [record]}), encoding="utf-8")
            self.assertEqual(self.reporter.main(["--manifest", str(manifest), "--output", str(output)]), 0)
            self.assertLessEqual(output.stat().st_size, 16 * 1024)

    def test_maximum_trial_count_still_has_a_bounded_report(self):
        records = [trial(f"trial-{index}", "baseline" if index % 2 else "candidate", index) for index in range(1, 17)]
        report = self.report(records)
        self.assertLessEqual(len(json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")), 16 * 1024)

    def test_rejects_oracle_failure_and_excessive_limits(self):
        oracle_failed = trial("baseline-1", "baseline", 1)
        oracle_failed["execution"]["oracle"] = "failed"
        with self.assertRaisesRegex(ValueError, "oracle"):
            self.report([oracle_failed])
        out_of_bounds = trial("baseline-2", "baseline", 2)
        out_of_bounds["limits"]["worker_attempts"] = 5
        with self.assertRaisesRegex(ValueError, "worker_attempts"):
            self.report([out_of_bounds])


if __name__ == "__main__":
    unittest.main()
