"""Run-viability and orchestrator-survivability tests for lean-audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, assert_precision_recall_at_least, load_script_module

SCRIPT = REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/references/scripts/workflow_cost.py"
LEDGER = REPO_ROOT / "tests/lean_workflow_ledger.jsonl"
FIXTURES = REPO_ROOT / "tests/lean_workflow_cost"


def load_workflow_cost():
    return load_script_module("workflow_cost", SCRIPT)


class StaticWorkflowLedgerTest(unittest.TestCase):
    def test_precision_and_recall(self) -> None:
        mod = load_workflow_cost()
        cases = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines()]
        self.assertGreaterEqual(len(cases), 12)
        tp = fp = fn = 0
        for case in cases:
            files = {row["path"]: row["content"] for row in case["files"]}
            found = {finding["code"] for finding in mod.analyze_sources(files)["findings"]}
            expected = set(case["expected_codes"])
            tp += len(found & expected)
            fp += len(found - expected)
            fn += len(expected - found)
        assert_precision_recall_at_least(self, tp, fp, fn)

    def test_orchestrator_evidence_names_phases_and_path(self) -> None:
        mod = load_workflow_cost()
        files = {
            "plugin/agents/coordinator.md": (
                "# Coordinator\nPreflight, discover, plan, build, and verify. "
                "Delegate workers and iterate until complete.\n"
            )
        }
        report = mod.analyze_sources(files)
        candidate = report["orchestrators"][0]
        self.assertEqual(candidate["path"], "plugin/agents/coordinator.md")
        self.assertEqual(candidate["phases"], ["preflight", "discovery", "plan", "build", "verify"])
        self.assertGreaterEqual(candidate["score"], 45)

    def test_named_single_agent_control_plane_is_detected(self) -> None:
        mod = load_workflow_cost()
        report = mod.analyze_sources(
            {
                "plugin/agents/coordinator.md": (
                    "# Coordinator\nThe coordinator performs preflight, discovery, planning, "
                    "build, and verification. Repeat build and verification until complete."
                )
            }
        )
        self.assertEqual(report["orchestrators"][0]["path"], "plugin/agents/coordinator.md")
        self.assertTrue(report["orchestrators"][0]["signals"]["named_control_plane"])
        self.assertIn("LA-RUN-1", {row["code"] for row in report["findings"]})

    def test_local_tool_schema_inventory_sizes_declared_schema_only(self) -> None:
        mod = load_workflow_cost()
        report = mod.analyze_sources(
            {
                "plugin/tools.json": json.dumps(
                    {
                        "tools": [
                            {
                                "name": "search",
                                "description": "Search the local index",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"query": {"type": "string"}},
                                },
                            }
                        ],
                        "unrelated": {"large_output": "not a tool schema"},
                    }
                )
            }
        )
        inventory = report["tool_schema_inventory"]
        self.assertEqual(len(inventory["tools"]), 1)
        self.assertEqual(inventory["tools"][0]["name"], "search")
        self.assertGreater(inventory["proxy_tokens"], 0)


class ForecastTest(unittest.TestCase):
    def test_unsafe_run_exhausts_before_verification(self) -> None:
        mod = load_workflow_cost()
        scenario = mod.load_scenario_data(
            json.loads((FIXTURES / "unsafe-run.json").read_text(encoding="utf-8"))
        )
        forecast = mod.forecast_scenario(scenario)
        self.assertEqual(forecast["verdict"], "infeasible")
        self.assertEqual(forecast["earliest_expected_overflow"], "build-loop")
        self.assertGreater(
            forecast["total_run_tokens"]["expected"],
            forecast["peak_context"]["expected"],
        )
        self.assertLess(forecast["verification_reserve_remaining"]["expected"], 0)
        self.assertIn("LA-RUN-2", {f["code"] for f in forecast["findings"]})
        self.assertIn("LA-RUN-3", {f["code"] for f in forecast["findings"]})

    def test_compact_handoffs_leave_verification_reserve(self) -> None:
        mod = load_workflow_cost()
        scenario = mod.load_scenario_data(
            json.loads((FIXTURES / "safe-run.json").read_text(encoding="utf-8"))
        )
        forecast = mod.forecast_scenario(scenario)
        self.assertEqual(forecast["verdict"], "feasible")
        self.assertIsNone(forecast["earliest_upper_overflow"])
        self.assertGreaterEqual(forecast["verification_reserve_remaining"]["high"], 0)
        self.assertNotIn("LA-RUN-3", {finding["code"] for finding in forecast["findings"]})

    def test_unknown_capacity_is_indeterminate_not_guessed(self) -> None:
        mod = load_workflow_cost()
        scenario = mod.load_scenario_data(
            {
                "id": "unknown",
                "orchestrator": {"base_tokens": 1000},
                "stages": [{"id": "verify", "role": "verify", "prompt_tokens": 100}],
            }
        )
        forecast = mod.forecast_scenario(scenario)
        self.assertEqual(forecast["verdict"], "indeterminate")
        self.assertIn("context_window", " ".join(forecast["limits"]))

    def test_fanout_accounts_for_worker_and_handoff_cost(self) -> None:
        mod = load_workflow_cost()
        scenario = mod.load_scenario_data(
            {
                "id": "workers",
                "context_window": 20000,
                "verification_reserve": 1000,
                "orchestrator": {"base_tokens": 1000},
                "stages": [
                    {
                        "id": "discover",
                        "role": "discovery",
                        "prompt_tokens": 100,
                        "workers": {
                            "count": 3,
                            "shared_prefix_tokens": 500,
                            "local_tokens": 200,
                            "output_tokens": 300,
                            "handoff_tokens": 250,
                        },
                    },
                    {"id": "verify", "role": "verify", "prompt_tokens": 100},
                ],
            }
        )
        forecast = mod.forecast_scenario(scenario)
        discover = forecast["stages"][0]
        self.assertEqual(discover["worker_total_tokens"]["expected"], 3000)
        self.assertEqual(discover["handoff_tokens"]["expected"], 750)

    def test_cost_waterfall_balances_and_excludes_out_of_band_logs(self) -> None:
        mod = load_workflow_cost()
        scenario = mod.load_scenario_data(
            {
                "id": "waterfall",
                "context_window": 10000,
                "orchestrator": {"base_tokens": 100},
                "stages": [
                    {
                        "id": "verify",
                        "role": "verify",
                        "prompt_tokens": 10,
                        "tool_schema_tokens": 20,
                        "hook_tokens": 30,
                        "tool_result_tokens": 40,
                        "out_of_band_result_tokens": 9000,
                        "output_tokens": 50,
                        "workers": {
                            "count": 2,
                            "shared_prefix_tokens": 5,
                            "local_tokens": 6,
                            "tool_result_tokens": 7,
                            "out_of_band_result_tokens": 8000,
                            "output_tokens": 8,
                            "handoff_tokens": 9,
                        },
                    }
                ],
            }
        )
        forecast = mod.forecast_scenario(scenario)
        waterfall = forecast["cost_waterfall"]
        model_keys = set(waterfall) - {"out_of_band_result_tokens"}
        self.assertEqual(
            sum(waterfall[key]["expected"] for key in model_keys),
            forecast["total_run_tokens"]["expected"],
        )
        self.assertEqual(waterfall["out_of_band_result_tokens"]["expected"], 25000)


class TraceAdapterTest(unittest.TestCase):
    def test_provider_and_otel_shapes_normalize(self) -> None:
        mod = load_workflow_cost()
        records = [
            {
                "id": "openai",
                "stage": "plan",
                "usage": {
                    "input_tokens": 100,
                    "input_tokens_details": {"cached_tokens": 40},
                    "output_tokens": 20,
                    "output_tokens_details": {"reasoning_tokens": 5},
                    "total_tokens": 120,
                },
            },
            {
                "id": "anthropic",
                "stage": "build",
                "usage": {
                    "input_tokens": 80,
                    "cache_read_input_tokens": 30,
                    "cache_creation_input_tokens": 10,
                    "output_tokens": 25,
                },
            },
            {
                "name": "gen_ai.client.operation.duration",
                "attributes": {
                    "gen_ai.usage.input_tokens": 60,
                    "gen_ai.usage.output_tokens": 15,
                    "lean_audit.stage": "verify",
                },
            },
        ]
        events = mod.normalize_trace_records(records)
        self.assertEqual([event.adapter for event in events], ["openai", "anthropic", "otel"])
        summary = mod.summarize_trace(events)
        self.assertEqual(summary["input_tokens"], 240)
        self.assertEqual(summary["output_tokens"], 60)
        self.assertEqual(summary["cached_input_tokens"], 70)
        self.assertEqual(summary["reasoning_tokens"], 5)

    def test_codex_and_claude_host_records_normalize(self) -> None:
        mod = load_workflow_cost()
        events = mod.normalize_trace_records(
            [
                {
                    "method": "thread/tokenUsage/updated",
                    "params": {
                        "tokenUsage": {
                            "inputTokens": 33,
                            "outputTokens": 7,
                            "totalTokens": 40,
                        }
                    },
                },
                {
                    "name": "claude_code.tool",
                    "attributes": {
                        "gen_ai.usage.input_tokens": 22,
                        "gen_ai.usage.output_tokens": 6,
                        "claude_code.tool.result_tokens": 12,
                    },
                    "visibility": "model",
                },
            ]
        )
        self.assertEqual([event.adapter for event in events], ["codex", "claude-code"])
        self.assertEqual(sum(event.total_tokens for event in events), 68)
        self.assertEqual(events[1].tool_result_tokens, 12)

    def test_trace_report_is_metadata_only(self) -> None:
        mod = load_workflow_cost()
        secret = "DO-NOT-ECHO-RAW-PROMPT"
        events = mod.normalize_trace_records(
            [
                {
                    "message": secret,
                    "tool_output": secret,
                    "usage": {"input_tokens": 10, "output_tokens": 3},
                }
            ]
        )
        rendered = json.dumps(mod.summarize_trace(events))
        self.assertNotIn(secret, rendered)

    def test_out_of_band_tool_result_is_not_model_visible_cost(self) -> None:
        mod = load_workflow_cost()
        events = mod.normalize_trace_records(
            [
                {
                    "id": "log",
                    "visibility": "out-of-band",
                    "tool_result_tokens": 9000,
                    "usage": {"input_tokens": 5, "output_tokens": 1},
                },
                {
                    "id": "hook",
                    "visibility": "model",
                    "tool_result_tokens": 200,
                    "usage": {"input_tokens": 8, "output_tokens": 2},
                },
            ]
        )
        summary = mod.summarize_trace(events)
        self.assertEqual(summary["model_visible_tool_result_tokens"], 200)
        self.assertEqual(summary["out_of_band_tool_result_tokens"], 9000)


class CliTest(unittest.TestCase):
    def test_json_cli_combines_static_forecast_and_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "agents/coordinator.md"
            agent.parent.mkdir()
            agent.write_text(
                "Preflight, discover, plan, build, verify; delegate workers. "
                "Return a compact summary. Iterate at most 2 times with a checkpoint.\n",
                encoding="utf-8",
            )
            trace = root / "trace.jsonl"
            trace.write_text(
                json.dumps({"usage": {"input_tokens": 10, "output_tokens": 2}}) + "\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(root),
                    "--scenario",
                    str(FIXTURES / "safe-run.json"),
                    "--trace",
                    str(trace),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["forecast"]["verdict"], "feasible")
            self.assertEqual(payload["trace"]["total_tokens"], 12)

    def test_calibration_drift_requires_declared_tolerance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario = root / "scenario.json"
            scenario.write_text(
                json.dumps(
                    {
                        "id": "calibration",
                        "context_window": 5000,
                        "verification_reserve": 500,
                        "calibration_tolerance": 0.1,
                        "orchestrator": {"base_tokens": 100},
                        "stages": [
                            {
                                "id": "verify",
                                "role": "verify",
                                "prompt_tokens": 100,
                                "output_tokens": 20,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps({"usage": {"input_tokens": 1000, "output_tokens": 200}}),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(root),
                    "--scenario",
                    str(scenario),
                    "--trace",
                    str(trace),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("LA-RUN-5", {row["code"] for row in json.loads(proc.stdout)["findings"]})


if __name__ == "__main__":
    unittest.main()
