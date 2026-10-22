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
        agent_lookup = self.measure("planning-policy-claude-agent-lookup")
        claude = self.measure("planning-policy-active-claude")
        codex = self.measure("planning-policy-active-codex")
        live_next = self.measure("planning-policy-approved-v5-live-next")
        fallback = self.measure("planning-policy-ledger-diagnostic-fallback")
        # Budgets below the history are the measured values rounded up to the next
        # multiple of 10, with the whole SKILL.md charged (the host loads the full
        # file, docs/skill-architecture.md), superseding the earlier slack-5 figures.
        # Every SKILL.md route then gained +14 for the planningledger/ package pointer
        # that SAC-REF-UNADVERTISED-SUPPORT requires once the ledger became a shim.
        self.assertLessEqual(lookup["load_total"], 1190)
        self.assertLessEqual(agent_lookup["total"], 1200)
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
        # Parent-orchestrator refinement adds 227 measured proxy tokens to the
        # shared core workflow. Charge 230 only to its authoring routes: active
        # Claude/Codex, series authoring, and approval handoff. Lookup and normal
        # live-next execution retain their existing loads and budgets.
        # Live-run repair: one over-long approval-envelope plan line made Claude
        # Code withhold approval, and a rejected ExitPlanMode was read as
        # approval. The adapter now states plan-mode persistence, display limits,
        # and the rejection rule (+113 measured, 7,189); the block-format
        # handoff adds 51 (8,274) on its route. Each budget carries 5 slack.
        # tdd-policy suite-step handoff: one sentence in the verification-economy
        # paragraph states the parent-owned suite step planning-policy hands to
        # tdd-policy at integration (+13 claude / +21 codex / +21 approval
        # measured), charged to every route that loads core-workflow.md; series
        # keeps its headroom. Each budget still carries 5 slack.
        # verify-loop: plan-contract.md gains the verification / changeset_budget
        # section (+196 measured claude; slack 5 kept).
        # verify-loop contract docs: verifier procedure, Verify footer/option and
        # adapter dispatch (+314 measured claude; slack 5 kept).
        # v1-v4 retirement and the batch environment-stop rule: every route re-measured
        # and ratcheted down to its measured value rounded up to 10.
        # #143 verify-packet decisions: plan-contract.md says verifiers see both
        # decision lists and independent evidence belongs in acceptance (+35 measured
        # on every route loading it; rounded up to 10).
        # #135/#137 write-set closure: core-workflow.md names the pins the literal
        # pin scan cannot see (+52 measured on every route loading it; rounded up to 10).
        self.assertLessEqual(claude["load_total"], 8840)
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
        # verify-loop contract docs: same shared additions plus codex verifier dispatch
        # (+287 measured; slack 5 kept). #143: same plan-contract.md sentence (+35).
        # #135/#137: same core-workflow.md write-set closure sentence (+52).
        self.assertLessEqual(codex["load_total"], 8720)
        # Normal v4 execution now drives every lifecycle edge through live bounded
        # results, so the 2,476-token runtime reference is exceptional rather than
        # repeated context. The fallback remains separately measurable and routed.
        # verify-loop contract docs: SKILL.md pointer and worker-handoff
        # budget/preflight (+70 measured; slack 5 kept).
        self.assertLessEqual(live_next["load_total"], 2700)
        base = "souroldgeezer-policy/skills/"
        self.assertEqual(
            [
                base + "planning-policy/SKILL.md",
                base + "planning-policy/references/core-workflow.md",
                base + "planning-policy/references/plan-contract.md",
                base + "git-workflow-policy/references/planning-worktree-closeout.md",
            ],
            [row["file"] for row in live_next["rows"]],
        )
        self.assertEqual(
            ["whole-file", "heading-subtree", "heading-subtree", "whole-file"],
            [row["resolution"] for row in live_next["rows"]],
        )
        self.assertEqual(
            [None, "approval-and-output", "parent-ledger-helper", None],
            [row["anchor"] for row in live_next["rows"]],
        )
        self.assertEqual(
            [
                base + "planning-policy/SKILL.md",
                base + "planning-policy/references/ledger-contract.md",
            ],
            [row["file"] for row in fallback["rows"]],
        )
        self.assertEqual(
            [(None, "whole-file"), ("authoring-and-audit-reference", "heading-subtree")],
            [(row["anchor"], row["resolution"]) for row in fallback["rows"]],
        )
        self.assertGreater(agent_lookup["selection_metadata_total"], 0)
        self.assertEqual(1, len(lookup["rows"]), "lookup must load only the entry surface")
        self.assertIsNone(lookup["rows"][0].get("anchor"), "the whole entry file is charged")
        for result, adapter in ((claude, "claude-code.md"), (codex, "codex.md")):
            files = [row["file"] for row in result["rows"]]
            self.assertTrue(any(file.endswith("SKILL.md") for file in files))
            self.assertTrue(any(file.endswith("core-workflow.md") for file in files))
            self.assertTrue(any(file.endswith("plan-contract.md") for file in files))
            self.assertTrue(any(file.endswith("templates/plan-v5.json") for file in files))
            self.assertEqual(1, sum(file.endswith(adapter) for file in files))

    def test_worker_and_verifier_routes_charge_their_agent_and_handoff(self):
        for name, agent, handoff, budget in (
            # #143: verify-handoff.md names approved_decisions, widens check 2, and
            # states the builder-notes evidence limit (+87 measured; rounded up to 10).
            ("worker", "step", "worker", 2450), ("verifier", "verify", "verify", 1190),
        ):
            result = self.measure(f"planning-policy-{name}")
            files = [row["file"] for row in result["rows"]]
            self.assertLessEqual(result["load_total"], budget)
            self.assertTrue(files[0].endswith(f"agents/plan-{agent}-standard.md"), files)
            self.assertTrue(files[1].endswith(f"references/{handoff}-handoff.md"), files)

    def test_series_successor_scenario_is_bounded_and_isolated(self):
        # Slicing an oversized plan into a series loads the new on-demand
        # references/plan-series.md alongside the same enforcement/executable-plan
        # surface as active-claude/active-codex, minus any host adapter (the
        # series contract is runtime-neutral). V5 adds the same outcome-first
        # contract and scaffold charged above. Including the orchestrator prose
        # charged above, this route measures 7,038 proxy tokens.
        series = self.measure("planning-policy-series-successor")
        # verify-loop contract docs: SKILL.md pointer and core-workflow verifier
        # paragraph (+206 measured; slack 5 kept). #143: plan-contract.md sentence (+35).
        # #135/#137: core-workflow.md write-set closure sentence (+52).
        self.assertLessEqual(series["load_total"], 8460)
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
        # Block-format envelope emission and the 4,096-character line limit
        # answer the same live failure: an over-long envelope line withheld
        # approval and a rejected ExitPlanMode was mistaken for approval.
        # verify-loop contract docs: same shared core-workflow/SKILL.md additions (+287
        # measured; slack 5 kept). #143: plan-contract.md sentence (+35).
        # #135/#137: core-workflow.md write-set closure sentence (+52).
        self.assertLessEqual(result["load_total"], 9830)
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
