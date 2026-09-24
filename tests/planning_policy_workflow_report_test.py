import hashlib
import copy
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
REVISIONS = {"baseline": "a" * 40, "candidate": "b" * 40}


def trial(identifier: str, variant: str, sequence: int, *, usage=True, outcome="completed", conditions=None):
    worker = {
        "actor_id": f"{identifier}-worker",
        "step_id": "evaluation",
        "attempt_id": f"{identifier}-attempt",
        "role": "worker",
        "model": "gpt-5.6-terra", "effort": "medium", "tier": "standard", "coverage_complete": True,
        "usage": {"input_tokens": 10, "output_tokens": 5, "cached_input_tokens": 2, "total_tokens": 15}
        if usage
        else None,
    }
    return {
        "trial_id": identifier,
        "variant": variant,
        "sequence": sequence,
        "policy_revision": REVISIONS[variant],
        "roster_complete": True,
        "conditions": conditions or CONDITIONS,
        "limits": {"worker_leaves": 2, "worker_attempts": 4, "minutes": 15},
        "counts": {"worker_leaves": 1, "worker_attempts": 1, "failed_attempts": 0, "retries": 0, "escalations": 0, "dispatches": 1},
        "sources": [{"path": "usage/summary.json", "sha256": digest(identifier)}],
        "actors": [
            {"actor_id": f"{identifier}-parent", "step_id": "parent", "attempt_id": "run", "role": "coordinator", "model": "gpt-5.6-sol", "effort": "high", "tier": None, "coverage_complete": True, "usage": {"input_tokens": 20, "output_tokens": 10, "cached_input_tokens": 0, "total_tokens": 30}},
            worker,
        ],
        "execution": {"outcome": outcome, "lifecycle": "cleaned", "oracle": "passed", "elapsed_seconds": 12},
    }


class WorkflowReportTest(unittest.TestCase):
    def setUp(self):
        self.reporter = load_reporter()

    def report(self, records):
        return self.reporter.build_report({"schema": "planning-policy-workflow-manifest/v1", "revisions": REVISIONS, "trials": records})

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
            manifest.write_text(json.dumps({"schema": "planning-policy-workflow-manifest/v1", "revisions": REVISIONS, "trials": [record]}), encoding="utf-8")
            self.assertEqual(self.reporter.main(["--manifest", str(manifest), "--output", str(output)]), 0)
            self.assertLessEqual(output.stat().st_size, 16 * 1024)

    def test_maximum_trial_count_still_has_a_bounded_report(self):
        records = [trial(f"trial-{index}", "baseline" if index % 2 else "candidate", index) for index in range(1, 17)]
        report = self.report(records)
        self.assertLessEqual(len(json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")), 16 * 1024)

    def test_oracle_failure_is_retained_without_economy_claims(self):
        oracle_failed = trial("candidate-1", "candidate", 2, outcome="failed")
        oracle_failed["execution"]["oracle"] = "failed"
        result = self.report([trial("baseline-1", "baseline", 1), oracle_failed])
        self.assertEqual(result["trials"][1]["execution"]["oracle"], "failed")
        self.assertFalse(result["comparison"]["comparable"])
        self.assertIsNone(result["variants"]["candidate"]["median_total_tokens"])

    def test_rejects_excessive_limits(self):
        out_of_bounds = trial("baseline-2", "baseline", 2)
        out_of_bounds["limits"]["worker_attempts"] = 5
        with self.assertRaisesRegex(ValueError, "worker_attempts"):
            self.report([out_of_bounds])

    def test_missing_actor_and_partial_coverage_invalidate_totals(self):
        for change in ("missing_actor", "partial_usage", "unreconciled_roster"):
            record = trial("baseline-1", "baseline", 1)
            if change == "missing_actor":
                record["counts"]["worker_attempts"] = 2
            elif change == "partial_usage":
                record["actors"][1]["coverage_complete"] = False
            else:
                record["roster_complete"] = False
            with self.subTest(change=change):
                result = self.report([record])
                self.assertIsNone(result["trials"][0]["usage"]["total_tokens"])
                self.assertFalse(result["comparison"]["comparable"])

    def test_blocked_before_dispatch_and_unknown_counts_are_retained(self):
        record = trial("baseline-1", "baseline", 1, outcome="blocked")
        record["actors"] = record["actors"][:1]
        record["counts"] = {key: None for key in record["counts"]}
        record["execution"].update(oracle="not_run", lifecycle="not_cleaned", elapsed_seconds=None)
        result = self.report([record])
        self.assertIsNone(result["trials"][0]["counts"]["worker_attempts"])
        self.assertFalse(result["comparison"]["comparable"])

    def test_actor_mapping_drift_is_incomparable(self):
        record = trial("candidate-1", "candidate", 2)
        record["actors"][1]["model"] = "unexpected-model"
        result = self.report([trial("baseline-1", "baseline", 1), record])
        self.assertFalse(result["comparison"]["comparable"])
        self.assertIn("actor_mapping_mismatch", result["comparison"]["reasons"])

    def test_reused_worker_is_counted_once_across_recorded_retry_attempts(self):
        baseline = trial("baseline-1", "baseline", 1)
        candidate = trial("candidate-1", "candidate", 2)
        candidate["actors"][1]["additional_attempt_ids"] = ["candidate-retry"]
        candidate["counts"].update(worker_attempts=2, failed_attempts=1, retries=1, dispatches=2)
        result = self.report([baseline, candidate])
        self.assertTrue(result["comparison"]["comparable"])
        self.assertEqual(result["trials"][1]["usage"]["total_tokens"], 45)
        candidate["actors"][1]["additional_attempt_ids"] = [candidate["actors"][1]["attempt_id"]]
        with self.assertRaisesRegex(ValueError, "duplicate attempt"):
            self.report([candidate])

    def test_conflicting_identifiers_and_nonfinite_evidence_are_rejected(self):
        base = trial("baseline-1", "baseline", 1)
        candidate = trial("candidate-1", "candidate", 2)
        for change in ("sequence", "actor", "revision", "nan", "content"):
            row = copy.deepcopy(candidate)
            if change == "sequence": row["sequence"] = 1
            if change == "actor": row["actors"][0]["actor_id"] = base["actors"][0]["actor_id"]
            if change == "revision": row["policy_revision"] = "c" * 40
            if change == "nan": row["execution"]["elapsed_seconds"] = float("nan")
            if change == "content": row["actors"][0]["completions"] = ["private text"]
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.report([base, row])

    def test_cli_bounds_input_before_parsing_and_refuses_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "manifest.json"
            output = Path(temporary) / "report.json"
            for contents in ('{"schema":"x","schema":"y"}', " " * (16 * 64 * 1024 + 4097), "[" * 1500 + "0" + "]" * 1500):
                manifest.write_text(contents)
                self.assertEqual(self.reporter.main(["--manifest", str(manifest), "--output", str(output)]), 2)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
