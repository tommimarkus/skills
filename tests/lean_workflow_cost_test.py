# lean-audit:dup-intentional — detector fixture bodies deliberately repeat one-factor workflow/scenario shapes; shared loaders and ledger calibration are already extracted
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

    def test_workflow_intentional_marker_is_exact_and_outside_fences(self) -> None:
        mod = load_workflow_cost()
        path = "plugin/agents/coordinator.md"
        workflow = (
            "The coordinator performs preflight, discovery, plan, build, and verify. "
            "Delegate worker output and retry until tests pass."
        )

        unmarked = mod.analyze_sources({path: workflow})
        marked = mod.analyze_sources(
            {
                path: (
                    "<!-- lean-audit:workflow-intentional — synthetic detector catalog -->\n"
                    + workflow
                )
            }
        )
        plain_text = mod.analyze_sources(
            {path: "The string lean-audit:workflow-intentional is documentation.\n" + workflow}
        )
        fenced = mod.analyze_sources(
            {
                path: (
                    "```markdown\n"
                    "<!-- lean-audit:workflow-intentional — example only -->\n"
                    "```\n"
                    + workflow
                )
            }
        )
        near_match = mod.analyze_sources(
            {path: "<!-- lean-audit:workflow-intentionality -->\n" + workflow}
        )
        missing_rationale = mod.analyze_sources(
            {path: "<!-- lean-audit:workflow-intentional -->\n" + workflow}
        )

        self.assertTrue(unmarked["findings"])
        self.assertEqual(marked["findings"], [])
        self.assertEqual(marked["intentional_workflow_paths"], [path])
        for report in (plain_text, fenced, near_match, missing_rationale):
            self.assertTrue(report["findings"])
            self.assertEqual(report["intentional_workflow_paths"], [])

    def test_retry_contract_routes_bounds_terminals_and_progress_separately(self) -> None:
        mod = load_workflow_cost()

        def codes(content: str) -> set[str]:
            report = mod.analyze_sources({"plugin/agents/lead.md": content})
            return {row["code"] for row in report["findings"]}

        capped_only = codes(
            "Preflight, discover, plan, build, and verify. Retry at most 3 times and "
            "checkpoint after each attempt."
        )
        terminal_without_progress = codes(
            "Preflight, discover, plan, build, and verify. Retry at most 3 times. "
            "Stop successfully when tests pass; after the final failure, report the "
            "failure summary and escalate to the owner."
        )
        convergence_aware = codes(
            "Preflight, discover, plan, build, and verify. Retry at most 3 times. "
            "Stop successfully when tests pass; after the final failure, report the "
            "failure summary and escalate to the owner. If the failing-check set is "
            "unchanged after an attempt, stop and escalate with the evidence path."
        )
        unbounded = codes("Preflight, discover, plan, build, and verify. Retry until tests pass.")

        self.assertIn("LA-RUN-4", capped_only)
        self.assertNotIn("LA-RUN-6", capped_only)
        self.assertNotIn("LA-RUN-4", terminal_without_progress)
        self.assertIn("LA-RUN-6", terminal_without_progress)
        self.assertNotIn("LA-RUN-4", convergence_aware)
        self.assertNotIn("LA-RUN-6", convergence_aware)
        self.assertIn("LA-RUN-1", unbounded)
        self.assertIn("LA-RUN-4", unbounded)
        self.assertNotIn("LA-RUN-6", unbounded)

    def test_checkpoint_requires_a_bounded_structural_state_contract(self) -> None:
        mod = load_workflow_cost()

        def codes(content: str) -> set[str]:
            report = mod.analyze_sources({"plugin/agents/lead.md": content})
            return {row["code"] for row in report["findings"]}

        incomplete = codes(
            "Preflight, discover, plan, build, and verify. Iterate at most 2 times; "
            "checkpoint and summarize after each iteration."
        )
        complete = codes(
            "Preflight, discover, plan, build, and verify. Iterate at most 2 times. "
            "After each iteration checkpoint a bounded summary schema containing objective "
            "and scope, approved decisions, progress, blockers and open choices, obligation "
            "IDs and evidence paths, plus the next decision."
        )
        unapproved_decisions = codes(
            "Preflight, discover, plan, build, and verify. Iterate at most 2 times. "
            "After each iteration checkpoint a bounded summary schema containing objective "
            "and scope, decisions, progress, blockers and open choices, obligation IDs and "
            "evidence paths, plus the next decision."
        )

        self.assertIn("LA-ORCH-5", incomplete)
        self.assertNotIn("LA-ORCH-5", complete)
        self.assertIn("LA-ORCH-5", unapproved_decisions)

        report = mod.analyze_sources(
            {
                "plugin/agents/lead.md": (
                    "Preflight, discover, plan, build, and verify. Iterate over an enumerated "
                    "matrix and note that this is not a repair retry. Checkpoint each pass."
                )
            }
        )
        signals = report["artifacts"][0]["signals"]
        self.assertTrue(signals["loop"])
        self.assertTrue(signals["retry"])
        self.assertTrue(signals["checkpoint"])
        self.assertFalse(signals["effective_loop"])
        self.assertFalse(signals["effective_retry"])
        self.assertFalse(signals["checkpoint_complete"])

    def test_deferred_scope_requires_explicit_broad_implementation(self) -> None:
        mod = load_workflow_cost()

        def codes(content: str) -> set[str]:
            report = mod.analyze_sources({"plugin/agents/lead.md": content})
            return {row["code"] for row in report["findings"]}

        absent_only = codes(
            "Preflight, discover, plan, build, and verify the requested narrow change."
        )
        broad_tbd = codes(
            "Preflight, discover, plan, build, and verify. Proceed with broad implementation "
            "across the repository while the implementation scope and acceptance criteria "
            "remain TBD."
        )
        resolved_packet = codes(
            "Preflight, discover, and plan. Classify requirements as must, out of scope, or "
            "unknown. Give every unknown an owner, default, and acceptance check; implement "
            "only the must items, then verify."
        )
        discovery_spike = codes(
            "Preflight and discover. Scope is TBD, so before implementation run a bounded "
            "2-pass discovery spike with a named question, owner, and exit criterion; then "
            "plan, build, and verify only the resolved scope."
        )
        broad_resolved_packet = codes(
            "Preflight, discover, and plan. Proceed with broad implementation only from the "
            "resolved packet while initial scope and acceptance remain TBD: classify every "
            "requirement as must, out of scope, or unknown, and give each unknown an owner, "
            "default, and acceptance check. Then build and verify only must items."
        )
        broad_bounded_spike = codes(
            "Preflight and discover. Proceed with broad implementation only after scope TBD "
            "is resolved by a bounded 2-pass discovery spike with a named question, owner, "
            "and exit criterion; then plan, build, and verify the resolved scope."
        )

        self.assertNotIn("LA-RUN-7", absent_only)
        self.assertIn("LA-RUN-7", broad_tbd)
        self.assertNotIn("LA-RUN-7", resolved_packet)
        self.assertNotIn("LA-RUN-7", discovery_spike)
        self.assertNotIn("LA-RUN-7", broad_resolved_packet)
        self.assertNotIn("LA-RUN-7", broad_bounded_spike)

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

    def test_hook_inventory_is_additive_and_uses_content_free_fixture_metadata(self) -> None:
        mod = load_workflow_cost()
        secret = "DO-NOT-EMIT-WORKFLOW-HOOK-COMMAND"
        hook_path = ".codex/hooks.json"
        report = mod.analyze_sources(
            {
                hook_path: json.dumps(
                    {
                        "hooks": {
                            "Stop": [
                                {"hooks": [{"type": "command", "command": f"printf {secret}"}]}
                            ]
                        }
                    }
                )
            },
            hook_fixture_metadata=[
                {
                    "path": hook_path,
                    "event": "Stop",
                    "registration_index": 0,
                    "hook_index": 0,
                    "enabled": True,
                    "visibility": "out-of-band",
                    "frequency": 1,
                    "proxy_tokens": 21,
                }
            ],
        )

        ledger = report["hook_cost"]
        self.assertEqual(len(ledger["registrations"]), 1)
        self.assertEqual(ledger["fixture_metadata"][0]["proxy_tokens"], 21)
        self.assertNotIn(secret, json.dumps(ledger))

    def test_workflow_source_reader_includes_recognized_hook_configs(self) -> None:
        mod = load_workflow_cost()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".codex").mkdir()
            (root / ".claude").mkdir()
            (root / ".codex/hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
            (root / ".claude/settings.json").write_text('{"hooks": {}}', encoding="utf-8")

            files = mod.read_workflow_sources(root)

        self.assertIn(".codex/hooks.json", files)
        self.assertIn(".claude/settings.json", files)


class ForecastTest(unittest.TestCase):
    def test_declared_output_cardinality_multiplies_lanes_iterations_and_waterfall(
        self,
    ) -> None:
        mod = load_workflow_cost()
        scenario = mod.load_scenario_data(
            {
                "id": "output-contract",
                "context_window": 1000,
                "orchestrator": {"base_tokens": 100},
                "stages": [
                    {
                        "id": "report",
                        "role": "verify",
                        "iterations": 2,
                        "output_tokens": 5,
                        "fixed_output_tokens": 10,
                        "per_item_output_tokens": 3,
                        "item_count": {"low": 1, "expected": 2, "high": 4},
                        "retained_tokens": 0,
                    }
                ],
            }
        )

        forecast = mod.forecast_scenario(scenario)

        self.assertEqual(
            forecast["cost_waterfall"]["output_tokens"],
            {
                "low": 36,
                "expected": 42,
                "high": 54,
            },
        )
        self.assertEqual(
            forecast["total_run_tokens"],
            {
                "low": 236,
                "expected": 242,
                "high": 254,
            },
        )
        model_keys = set(forecast["cost_waterfall"]) - {"out_of_band_result_tokens"}
        for lane in ("low", "expected", "high"):
            self.assertEqual(
                sum(forecast["cost_waterfall"][key][lane] for key in model_keys),
                forecast["total_run_tokens"][lane],
            )

    def test_output_components_without_cardinality_preserve_legacy_output_and_disclose_limit(
        self,
    ) -> None:
        mod = load_workflow_cost()
        scenario = mod.load_scenario_data(
            {
                "id": "output-cardinality-unknown",
                "context_window": 1000,
                "orchestrator": {"base_tokens": 100},
                "stages": [
                    {
                        "id": "report",
                        "role": "verify",
                        "output_tokens": 5,
                        "fixed_output_tokens": 10,
                        "per_item_output_tokens": 3,
                        "retained_tokens": 0,
                    }
                ],
            }
        )

        forecast = mod.forecast_scenario(scenario)

        self.assertEqual(forecast["cost_waterfall"]["output_tokens"]["expected"], 5)
        self.assertTrue(
            any("report" in limit and "item_count" in limit for limit in forecast["limits"])
        )

    def test_item_count_without_output_components_is_inert(self) -> None:
        mod = load_workflow_cost()
        base = {
            "id": "item-count-inert",
            "context_window": 1000,
            "orchestrator": {"base_tokens": 100},
            "stages": [
                {
                    "id": "report",
                    "role": "verify",
                    "output_tokens": 5,
                    "retained_tokens": 0,
                }
            ],
        }
        with_count = json.loads(json.dumps(base))
        with_count["stages"][0]["item_count"] = {
            "low": 1,
            "expected": 10,
            "high": 100,
        }

        plain = mod.forecast_scenario(mod.load_scenario_data(base))
        counted = mod.forecast_scenario(mod.load_scenario_data(with_count))

        self.assertEqual(counted["total_run_tokens"], plain["total_run_tokens"])
        self.assertEqual(counted["cost_waterfall"], plain["cost_waterfall"])

    def test_output_cardinality_overflow_reuses_existing_run_codes(self) -> None:
        mod = load_workflow_cost()
        scenario = mod.load_scenario_data(
            {
                "id": "output-overflow",
                "context_window": 150,
                "orchestrator": {"base_tokens": 100},
                "stages": [
                    {
                        "id": "verify",
                        "role": "verify",
                        "fixed_output_tokens": 20,
                        "per_item_output_tokens": 50,
                        "item_count": 2,
                    }
                ],
            }
        )

        forecast = mod.forecast_scenario(scenario)
        codes = {finding["code"] for finding in forecast["findings"]}

        self.assertEqual(forecast["verdict"], "infeasible")
        self.assertEqual(codes, {"LA-RUN-2", "LA-RUN-3"})

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
    def test_trace_reader_accepts_nested_event_lists_and_preserves_scalar_error(self) -> None:
        mod = load_workflow_cost()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.json"
            path.write_text(
                json.dumps({"events": [{"usage": {"input_tokens": 3}}]}),
                encoding="utf-8",
            )
            self.assertEqual(len(mod.read_trace_file(path)), 1)
            path.write_text("1", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "trace must contain JSON objects"):
                mod.read_trace_file(path)

    def test_jsonl_trace_reader_streams_records(self) -> None:
        mod = load_workflow_cost()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.jsonl"
            path.write_text(
                "\n".join(
                    json.dumps({"usage": {"input_tokens": value, "output_tokens": 1}})
                    for value in (3, 5)
                )
                + "\n",
                encoding="utf-8",
            )
            rows = mod.read_trace_file(path)

            self.assertNotIsInstance(rows, list)
            self.assertEqual(
                [row["usage"]["input_tokens"] for row in rows],
                [3, 5],
            )

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

    def test_native_codex_rollout_uses_last_usage_not_cumulative_usage(self) -> None:
        mod = load_workflow_cost()
        records = [
            {
                "ordinal": "10",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "last_token_usage": {
                            "input_tokens": 10,
                            "cached_input_tokens": 4,
                            "cache_write_input_tokens": 2,
                            "output_tokens": 3,
                            "reasoning_output_tokens": 1,
                            "total_tokens": 13,
                        },
                        "total_token_usage": {
                            "input_tokens": 1000,
                            "cached_input_tokens": 400,
                            "cache_write_input_tokens": 200,
                            "output_tokens": 300,
                            "reasoning_output_tokens": 100,
                            "total_tokens": 1300,
                        },
                    },
                },
            },
            {
                "ordinal": "11",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "last_token_usage": {
                            "input_tokens": 20,
                            "cached_input_tokens": 8,
                            "cache_write_input_tokens": 0,
                            "output_tokens": 5,
                            "reasoning_output_tokens": 2,
                            "total_tokens": 25,
                        },
                        "total_token_usage": {
                            "input_tokens": 1020,
                            "cached_input_tokens": 408,
                            "cache_write_input_tokens": 200,
                            "output_tokens": 305,
                            "reasoning_output_tokens": 102,
                            "total_tokens": 1325,
                        },
                    },
                },
            },
        ]

        summary = mod.summarize_trace_records(iter(records))

        self.assertEqual(summary["input_tokens"], 30)
        self.assertEqual(summary["output_tokens"], 8)
        self.assertEqual(summary["cached_input_tokens"], 12)
        self.assertEqual(summary["cache_write_tokens"], 2)
        self.assertEqual(summary["reasoning_tokens"], 3)
        self.assertEqual(summary["total_tokens"], 38)
        self.assertEqual(summary["by_adapter"], {"codex": 38})
        self.assertEqual(
            summary["coverage"],
            {
                "source_records": 2,
                "recognized_usage_events": 2,
                "unsupported_usage_records": 0,
                "calibration_eligible": True,
                "limit_codes": [],
            },
        )

    def test_native_codex_rollout_reports_bounded_lifecycle_counters_only(self) -> None:
        mod = load_workflow_cost()
        secret = "DO-NOT-ECHO-CODEX-ROLLOUT-CONTENT"
        records = [
            {"type": "compacted", "payload": {"summary": secret}},
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "call_id": "exec-1",
                    "input": secret,
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call_output",
                    "call_id": "exec-1",
                    "output": "é",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "wait_agent",
                    "call_id": "wait-1",
                    "arguments": json.dumps({"timeout_ms": 60_000, "message": secret}),
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "wait-1",
                    "output": "done",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "wait_agent",
                    "call_id": "wait-2",
                    "arguments": json.dumps({"timeout_ms": 90_000}),
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "wait_agent",
                    "call_id": "wait-3",
                    "arguments": "{}",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "list_agents",
                    "call_id": "list-1",
                    "arguments": "{}",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "list-1",
                    "output": secret,
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "spawn_agent",
                    "call_id": "spawn-1",
                    "arguments": json.dumps({"message": secret}),
                },
            },
        ]

        summary = mod.summarize_trace_records(iter(records))
        rollout = summary["codex_rollout"]

        self.assertEqual(rollout["compaction_count"], 1)
        self.assertEqual(
            rollout["collaboration_calls"],
            {
                "spawn_agent": 1,
                "send_message": 0,
                "followup_task": 0,
                "wait_agent": 3,
                "list_agents": 1,
                "interrupt_agent": 0,
            },
        )
        self.assertEqual(
            rollout["waits"],
            {
                "count": 3,
                "declared_timeout_ms_total": 150_000,
                "at_or_below_60000_ms": 1,
                "unknown_timeouts": 1,
            },
        )
        self.assertEqual(
            rollout["tool_output_utf8_bytes"],
            {
                "exec": {"count": 1, "total": 2, "maximum": 2},
                "wait_agent": {"count": 1, "total": 4, "maximum": 4},
                "list_agents": {
                    "count": 1,
                    "total": len(secret.encode("utf-8")),
                    "maximum": len(secret.encode("utf-8")),
                },
            },
        )
        self.assertNotIn(secret, json.dumps(summary))

    def test_missing_and_partial_usage_are_not_calibration_eligible(self) -> None:
        mod = load_workflow_cost()
        empty = mod.summarize_trace_records(iter(()))
        self.assertEqual(empty["total_tokens"], 0)
        self.assertFalse(empty["coverage"]["calibration_eligible"])
        self.assertIn("TRACE-USAGE-MISSING", empty["coverage"]["limit_codes"])

        partial = mod.summarize_trace_records(
            iter(
                [
                    {
                        "type": "event_msg",
                        "payload": {
                            "type": "token_count",
                            "info": {
                                "last_token_usage": {
                                    "input_tokens": 1000,
                                    "output_tokens": 200,
                                }
                            },
                        },
                    }
                ]
            )
        )
        self.assertEqual(partial["coverage"]["recognized_usage_events"], 0)
        self.assertEqual(partial["coverage"]["unsupported_usage_records"], 1)
        self.assertFalse(partial["coverage"]["calibration_eligible"])
        self.assertIn("TRACE-USAGE-INCOMPLETE", partial["coverage"]["limit_codes"])

        unsupported = mod.summarize_trace_records(iter([{"usage": {"vendor_units": 9}}]))
        self.assertEqual(unsupported["coverage"]["unsupported_usage_records"], 1)
        self.assertFalse(unsupported["coverage"]["calibration_eligible"])
        self.assertIn("TRACE-USAGE-UNSUPPORTED", unsupported["coverage"]["limit_codes"])

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
    def test_json_cli_attaches_hook_config_and_fixture_ledgers_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".codex").mkdir()
            secret = "DO-NOT-EMIT-CLI-HOOK-COMMAND"
            (root / ".codex/hooks.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "Stop": [
                                {"hooks": [{"type": "command", "command": f"printf {secret}"}]}
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            fixture = root / "hook-fixture.json"
            fixture.write_text(
                json.dumps(
                    [
                        {
                            "path": ".codex/hooks.json",
                            "event": "Stop",
                            "registration_index": 0,
                            "hook_index": 0,
                            "enabled": True,
                            "visibility": "model",
                            "frequency": 1,
                            "proxy_tokens": 8,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(root),
                    "--hook-fixture",
                    str(fixture),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        hook_cost = payload["static"]["hook_cost"]
        self.assertEqual(len(hook_cost["registrations"]), 1)
        self.assertEqual(hook_cost["fixture_metadata"][0]["proxy_tokens"], 8)
        self.assertNotIn(secret, proc.stdout)

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

    def test_incomplete_trace_cannot_emit_calibration_drift(self) -> None:
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
            trace = root / "trace.jsonl"
            trace.write_text(
                json.dumps(
                    {
                        "type": "event_msg",
                        "payload": {
                            "type": "token_count",
                            "info": {
                                "last_token_usage": {
                                    "input_tokens": 1000,
                                    "output_tokens": 200,
                                }
                            },
                        },
                    }
                )
                + "\n",
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
        payload = json.loads(proc.stdout)
        self.assertNotIn("LA-RUN-5", {row["code"] for row in payload["findings"]})
        self.assertFalse(payload["trace"]["coverage"]["calibration_eligible"])


if __name__ == "__main__":
    unittest.main()
