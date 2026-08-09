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

    def test_declared_load_budgets_and_routes(self):
        lookup = self.measure("planning-policy-lookup")
        direct = self.measure("planning-policy-direct-lookup")
        agent_lookup = self.measure("planning-policy-claude-agent-lookup")
        claude = self.measure("planning-policy-active-claude")
        codex = self.measure("planning-policy-active-codex")
        ledger = self.measure("planning-policy-approved-multi-agent-ledger")
        self.assertLessEqual(lookup["load_total"], 900)
        self.assertLessEqual(direct["load_total"], 750)
        self.assertLessEqual(agent_lookup["total"], 900)
        self.assertLessEqual(claude["load_total"], 4000)
        self.assertLessEqual(codex["load_total"], 4100)
        self.assertLessEqual(ledger["load_total"], 4200)
        self.assertEqual(1, len(lookup["rows"]), "lookup must load only the entry surface")
        self.assertEqual("load-map", direct["rows"][0]["anchor"])
        self.assertEqual("load-map", agent_lookup["rows"][0]["anchor"])
        for result, adapter in ((claude, "claude-code.md"), (codex, "codex.md")):
            files = [row["file"] for row in result["rows"]]
            self.assertTrue(any(file.endswith("SKILL.md") for file in files))
            self.assertTrue(any(file.endswith("core-workflow.md") for file in files))
            self.assertTrue(any(file.endswith("plan-contract.md") for file in files))
            self.assertEqual(1, sum(file.endswith(adapter) for file in files))

    def test_unknown_predicate_is_charged_and_scenario_has_provenance(self):
        unknown = self.measure("planning-policy-unknown-host")
        self.assertGreater(unknown["load_total"], self.measure("planning-policy-lookup")["load_total"])
        adapter = next(row for row in unknown["rows"] if row["file"].endswith("codex.md"))
        self.assertEqual([{"entry": "planning-policy", "predicate": "unknown"}], adapter["routes"])
        self.assertTrue(all(item.get("provenance") for item in self.scenarios.values()))

    def test_representative_delegated_checkpoint_is_bounded_and_rehydratable(self):
        assignment = {"harness": "codex", "tier": "standard", "model_or_alias": "gpt-5.6-terra", "effort": "medium", "worktree": ".worktrees/cost-run"}
        steps = json.dumps([
            {"id": "prepare", "summary": "Prepare bounded handoff", **assignment},
            {"id": "implement", "dependencies": ["prepare"], "summary": "Implement one concern", **assignment},
            {"id": "verify", "dependencies": ["implement"], "summary": "Run focused acceptance", **assignment},
        ])
        with tempfile.TemporaryDirectory() as temporary:
            common = ["--ledger-root", temporary, "--plan-id", "cost-run"]
            def call(*args):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(0, ledger.main([*common, *args]))
                return json.loads(output.getvalue())
            call("init", "--actor", "parent", "--approved", "--steps-json", steps)
            for step in ("prepare", "implement"):
                call("transition", "--actor", "parent", "--step-id", step, "--to", "ready")
                call("transition", "--actor", "parent", "--step-id", step, "--to", "in_progress")
                call("transition", "--actor", "parent", "--step-id", step, "--to", "completed")
                call("transition", "--actor", "parent", "--step-id", step, "--to", "integrated", "--summary", "focused acceptance passed", "--evidence-path", "evidence/focused.json")
            shown = call("show")
            checkpoint = Path(temporary) / "planning-policy/ledgers/cost-run/checkpoint.json"
            self.assertLessEqual(checkpoint.stat().st_size, 16 * 1024)
            self.assertLessEqual(shown["summary_proxy_tokens"], 1200)
            self.assertEqual(shown["summary_proxy_tokens"], len(ledger.PROXY_TOKEN_RE.findall(json.dumps({key: value for key, value in shown.items() if key != "summary_proxy_tokens"}, sort_keys=True, separators=(",", ":")))))


if __name__ == "__main__":
    unittest.main()
