"""Regression budgets for planning-policy's declared load and rehydration paths."""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, load_script_module


SCENARIOS = REPO_ROOT / "tests/planning_policy_cost/scenarios.json"
LOAD_COST = REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/references/scripts/skill_load_cost.py"
LEDGER = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py"
slc = load_script_module("planning_policy_load_cost", LOAD_COST)
spec = importlib.util.spec_from_file_location("planning_policy_cost_ledger", LEDGER)
ledger = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(ledger)


class PlanningPolicyCostTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenarios = {item["id"]: item for item in json.loads(SCENARIOS.read_text(encoding="utf-8"))}

    def measure(self, scenario_id):
        return slc.measure_scenario(self.scenarios[scenario_id], REPO_ROOT)

    def assert_within_budget(self, route, measured, budget):
        # One subTest per budget, so a run reports every overrun, not just the first.
        with self.subTest(budget=route):
            self.assertLessEqual(measured, budget)

    def test_declared_load_budgets_and_routes(self):
        # Standard gets a distinct 3k proxy ceiling; managed budgets charge its
        # selection/readability slices, strict workflow and native-route guard.
        budgets = {
            "lookup": 1120, "claude-agent-lookup": 1130,
            "active-claude": 9500, "active-codex": 9400,
            "approved-v5-live-next": 2800, "ledger-diagnostic-fallback": 3300,
            "standard-claude": 3000, "standard-codex": 3000,
            "standard-worker": 400, "standard-reviewer": 200,
        }
        for name, budget in budgets.items():
            self.assert_within_budget(name, self.measure(f"planning-policy-{name}")["total"], budget)
        lookup = self.measure("planning-policy-lookup")
        self.assertEqual(1, len(lookup["rows"]))
        self.assertIsNone(lookup["rows"][0].get("anchor"))
        self.assertGreater(self.measure("planning-policy-claude-agent-lookup")["selection_metadata_total"], 0)
        for host, adapter in (("claude", "claude-code.md"), ("codex", "codex.md")):
            with self.subTest(host=host):
                standard = self.measure(f"planning-policy-standard-{host}")
                self.assertEqual(3, len(standard["rows"]))
                self.assertEqual(["whole-file", "whole-file", "heading-subtree"],
                                 [row["resolution"] for row in standard["rows"]])
                self.assertEqual("standard-workflow", standard["rows"][-1]["anchor"])
                self.assertTrue(standard["rows"][-1]["file"].endswith(adapter))
                self.assertLess(standard["load_total"], self.measure("planning-policy-approval-handoff")["load_total"] / 2)
                managed = self.measure(f"planning-policy-active-{host}")
                files = [row["file"] for row in managed["rows"]]
                for suffix in ("strict-workflow.md", "plan-contract.md", "templates/plan-v5.json", adapter):
                    self.assertTrue(any(file.endswith(suffix) for file in files), suffix)
                self.assertEqual(1, sum(file.endswith(adapter) for file in files))
        for name, anchor in (("worker", "standard-assignment-and-return"), ("reviewer", "independent-review")):
            result = self.measure(f"planning-policy-standard-{name}")
            self.assertEqual(1, len(result["rows"]))
            self.assertEqual(anchor, result["rows"][0]["anchor"])
            self.assertEqual("heading-subtree", result["rows"][0]["resolution"])
        live = self.measure("planning-policy-approved-v5-live-next")
        self.assertEqual([None, "approval-and-output", "parent-ledger-helper", None],
                         [row["anchor"] for row in live["rows"]])
        self.assertTrue(live["rows"][1]["file"].endswith("strict-workflow.md"))

    def test_worker_and_verifier_routes_charge_their_agent_and_handoff(self):
        for name, agent, handoff, budget in (
            # Managed-only guard text remains charged to each managed agent.
            ("worker", "step", "worker", 2540), ("verifier", "verify", "verify", 1260),
        ):
            with self.subTest(route=name):
                result = self.measure(f"planning-policy-{name}")
                files = [row["file"] for row in result["rows"]]
                self.assertLessEqual(result["load_total"], budget)
                self.assertTrue(files[0].endswith(f"agents/plan-{agent}-standard.md"), files)
                self.assertTrue(files[1].endswith(f"references/{handoff}-handoff.md"), files)

    def test_series_successor_scenario_is_bounded_and_isolated(self):
        # Only an explicitly selected managed series loads this reference.
        series = self.measure("planning-policy-series-successor")
        self.assertLessEqual(series["load_total"], 8800)
        files = [row["file"] for row in series["rows"]]
        self.assertTrue(any(file.endswith("plan-series.md") for file in files))
        self.assertTrue(any(file.endswith("SKILL.md") for file in files))
        self.assertTrue(any(file.endswith("core-workflow.md") for file in files))
        self.assertTrue(any(file.endswith("plan-contract.md") for file in files))
        self.assertFalse(any(file.endswith("claude-code.md") for file in files))
        self.assertFalse(any(file.endswith("codex.md") for file in files))
        for scenario_id in self.scenarios:
            if scenario_id == "planning-policy-series-successor":
                continue
            other = self.measure(scenario_id)
            self.assertFalse(
                any(row["file"].endswith("plan-series.md") for row in other["rows"]),
                f"{scenario_id} must not load plan-series.md",
            )

    def test_approval_handoff_route_is_bounded_and_conditional(self):
        result = self.measure("planning-policy-approval-handoff")
        # Strict approval still transports exact JSON; standard never loads it.
        self.assertLessEqual(result["load_total"], 10300)
        self.assertTrue(any(row["file"].endswith("approval-handoff.md") for row in result["rows"]))
        for name in ("planning-policy-lookup", "planning-policy-approved-v5-live-next"):
            self.assertFalse(any(row["file"].endswith("approval-handoff.md") for row in self.measure(name)["rows"]))

    def test_unknown_predicate_is_charged_and_scenario_has_provenance(self):
        unknown = self.measure("planning-policy-unknown-host")
        self.assertGreater(unknown["load_total"], self.measure("planning-policy-lookup")["load_total"])
        adapter = next(row for row in unknown["rows"] if row["file"].endswith("codex.md"))
        self.assertEqual([{"entry": "planning-policy", "predicate": "unknown"}], adapter["routes"])
        self.assertTrue(all(item.get("provenance") for item in self.scenarios.values()))

    def test_representative_delegated_checkpoint_is_bounded_and_rehydratable(self):
        ids = ("prepare", "implement", "verify")
        plan = {
            "contract_version": 5,
            "verification": "closeout-only",
            "objective": "Ship one bounded change through three delegated steps",
            "scope_summary": "One source file per step and its focused test",
            "approved_decisions": ["Keep each step to one concern"],
            "work_units": [
                {"id": sid, "original_size": "small", "cohesive_outcome": f"Complete {sid}",
                 "decomposition": {"shape": "single"}}
                for sid in ids
            ],
            "leaves": [
                {
                    "id": sid, "dependencies": ids[:number][-1:], "task": f"{sid.title()} one concern",
                    "boundary": "Only the named file", "read_set": ["src/input.py"],
                    "write_set": [f"src/{sid}.py"], "settled_decisions": {"shape": "settled"},
                    "size": "small", "portable_tier": "standard", "worktree_owner": f"task/{sid}",
                    "acceptance_command": "uv run python -m unittest tests.focused_test",
                    "return_contract": "bounded-step-return-v1",
                    "stop_conditions": ["missing_load_bearing_information"],
                    "work_unit_id": sid, "max_attempts": 2,
                    "capability_requirements": {"baseline": "plan-step-base-v1", "additional": []},
                }
                for number, sid in enumerate(ids)
            ],
        }
        with tempfile.TemporaryDirectory() as temporary:
            common = ["--ledger-root", temporary, "--plan-id", "cost-run"]
            def call(*args):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(0, ledger.main([*common, *args]))
                return json.loads(output.getvalue())
            plan_file = Path(temporary) / "plan.json"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")
            run_id = call(
                "init-v5", "--actor", "parent", "--approved", "--plan-file", str(plan_file),
                "--host", "codex", "--evidence", "test fixture capability inventory",
            )["run_id"]
            scope = ("--actor", "parent", "--run-id", run_id, "--step-id", "prepare")
            call("transition", *scope, "--to", "ready", "--agent-id", "prepare-worker")
            call("transition", *scope, "--to", "in_progress")
            checkpoint = Path(temporary) / "planning-policy/ledgers/cost-run" / run_id / "checkpoint.json"
            step = json.loads(checkpoint.read_text(encoding="utf-8"))["steps"]["prepare"]
            returned = Path(temporary) / "return.json"
            returned.write_text(json.dumps({
                "schema": "bounded-step-return-v1", "step_id": "prepare",
                "attempt_id": step["attempt_id"], "agent_id": step["agent_id"], "status": "completed",
                "changed_paths": [], "commit_hash": "", "blockers": [], "unstarted_remainder": [],
                "acceptance": {"command": plan["leaves"][0]["acceptance_command"], "exit_code": 0,
                               "summary": "focused acceptance passed"},
                "notes": [{"type": "finding", "message": "bounded handoff prepared"}],
            }), encoding="utf-8")
            call("record-return", "--actor", "parent", "--run-id", run_id, "--return-file", str(returned))
            shown = call("show", "--run-id", run_id)
            self.assertLessEqual(checkpoint.stat().st_size, ledger.MAX_CHECKPOINT)
            self.assertLessEqual(shown["summary_proxy_tokens"], 1200)
            self.assertEqual(shown["summary_proxy_tokens"], len(ledger.PROXY_TOKEN_RE.findall(json.dumps({key: value for key, value in shown.items() if key != "summary_proxy_tokens"}, sort_keys=True, separators=(",", ":")))))

if __name__ == "__main__":
    unittest.main()
