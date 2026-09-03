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
        live_next = self.measure("planning-policy-approved-v5-live-next")
        fallback = self.measure("planning-policy-ledger-diagnostic-fallback")
        self.assertLessEqual(lookup["load_total"], 900)
        self.assertLessEqual(direct["load_total"], 750)
        self.assertLessEqual(agent_lookup["total"], 900)
        # claude and codex were re-baselined together, from 4000/4200, to carry the
        # downward tier test. The contract gated only escalation: analytical/deep had
        # to name an irreducible unknown, while nothing had to be argued to pick
        # standard, so standard absorbed settled work and mechanical rarely fired.
        # The added tokens state the mirror (a leaf whose settled decisions and
        # enumerated write set leave no open choice is mechanical), the optional
        # open_implementation_choice that names a real remaining judgment, and the
        # tier_mix the plan discloses. Both adapters load the same two references.
        # New v4 authoring adds the canonical capability-requirement scaffold,
        # approval/dispatch distinction, exact host binding, and pre-dispatch
        # blocker. The increase is charged only to executable-plan authoring and
        # dispatch, not lookup or legacy resume.
        # Live-next authoring adds the bounded lifecycle/restart contract to the
        # shared plan surface and the host notification rule to each adapter.
        # This is not the repeated execution route measured separately below.
        # claude and codex were re-baselined again, from 5700/5850, to carry the
        # batch dispatch lane: core-workflow.md's advisory-fed grooming (act on
        # PLANCOST-UNBATCHED-CHAIN/-TIER-OVER-ASSIGNED/-PLAN-SCALE before
        # approval), its fifth inline-departure case (dispatch overhead
        # evidenced by the cost advisory), its batch/acceptance-scoping
        # grooming rule, and its verification-economy paragraph
        # (rebased_tree_changed decides whether a leaf's scoped acceptance
        # re-runs); plan-contract.md's `batch` leaf field and its
        # PLANCOST-UNBATCHED-CHAIN/PLANCOST-PLAN-SCALE advisory coverage; and
        # each adapter's one-dispatch-per-batch paragraph. Every added
        # sentence states a contract fact steps 1-4 already implemented and
        # validated in the batch-aware validator, ledger, and worktree helper.
        # claude and codex were re-baselined once more, from 6250/6350, to carry
        # the plan-series pointers: core-workflow.md's PLANCOST-PLAN-SCALE
        # remediation sentence and plan-contract.md's advisory-cost sentence
        # each now point at the new on-demand references/plan-series.md, which
        # documents series fields, grooming inheritance, close/handoff
        # mechanics, the init-v4 predecessor cross-check, and the parent's
        # series-end obligation already implemented and tested in
        # planning_ledger.py. Neither adapter loads plan-series.md itself.
        # V5 is re-baselined from 6,280/6,380 to carry outcome-first grooming,
        # exact single/parallel/checkpointed evidence, the microleaf-risk
        # disposition, v1-v4 resume-only guidance, and the larger v5 scaffold.
        # The lookup and repeated live-next paths retain their existing bounds.
        self.assertLessEqual(claude["load_total"], 6850)
        # codex.md and ledger-contract.md were re-baselined once, from 4100/4200,
        # to carry the bounded-step-return-v1 corrections: the optional blocker
        # evidence pair, `oversized` as a status rather than a `blocked:` code,
        # and the commit-or-revert rule for a stop that already edited files.
        # codex.md had 12 tokens of headroom, so the corrections could not fit.
        # Every added token states a contract fact a live dispatch got wrong.
        # codex.md was re-baselined again, from 5850, to carry its matching
        # one-dispatch-per-batch paragraph alongside the same shared
        # core-workflow.md/plan-contract.md batch additions as claude above.
        # codex was re-baselined once more, from 6350, alongside claude above
        # for the same shared plan-series pointers.
        self.assertLessEqual(codex["load_total"], 6950)
        # Normal v4 execution now drives every lifecycle edge through live bounded
        # results, so the 2,476-token runtime reference is exceptional rather than
        # repeated context. The fallback remains separately measurable and routed.
        self.assertLessEqual(live_next["load_total"], 2200)
        self.assertFalse(
            any(row["file"].endswith("ledger-contract.md") for row in live_next["rows"])
        )
        self.assertTrue(
            any(row["file"].endswith("ledger-contract.md") for row in fallback["rows"])
        )
        self.assertEqual(1, len(lookup["rows"]), "lookup must load only the entry surface")
        self.assertEqual("load-map", direct["rows"][0]["anchor"])
        self.assertEqual("load-map", agent_lookup["rows"][0]["anchor"])
        for result, adapter in ((claude, "claude-code.md"), (codex, "codex.md")):
            files = [row["file"] for row in result["rows"]]
            self.assertTrue(any(file.endswith("SKILL.md") for file in files))
            self.assertTrue(any(file.endswith("core-workflow.md") for file in files))
            self.assertTrue(any(file.endswith("plan-contract.md") for file in files))
            self.assertTrue(any(file.endswith("templates/plan-v5.json") for file in files))
            self.assertEqual(1, sum(file.endswith(adapter) for file in files))

    def test_series_successor_scenario_is_bounded_and_isolated(self):
        # Slicing an oversized plan into a series loads the new on-demand
        # references/plan-series.md alongside the same enforcement/executable-plan
        # surface as active-claude/active-codex, minus any host adapter (the
        # series contract is runtime-neutral). V5 adds the same outcome-first
        # contract and scaffold charged above; measured at 6,840 tokens.
        series = self.measure("planning-policy-series-successor")
        self.assertLessEqual(series["load_total"], 6875)
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

    def test_unknown_predicate_is_charged_and_scenario_has_provenance(self):
        unknown = self.measure("planning-policy-unknown-host")
        self.assertGreater(unknown["load_total"], self.measure("planning-policy-lookup")["load_total"])
        adapter = next(row for row in unknown["rows"] if row["file"].endswith("codex.md"))
        self.assertEqual([{"entry": "planning-policy", "predicate": "unknown"}], adapter["routes"])
        self.assertTrue(all(item.get("provenance") for item in self.scenarios.values()))

    def test_legacy_v4_scaffold_remains_outside_declared_load_routes(self):
        for scenario_id in self.scenarios:
            measured = self.measure(scenario_id)
            self.assertFalse(
                any(row["file"].endswith("templates/plan-v4.json") for row in measured["rows"]),
                f"{scenario_id} must not load the legacy v4 scaffold for new authoring",
            )

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
