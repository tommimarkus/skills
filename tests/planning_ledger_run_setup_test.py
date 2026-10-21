"""Derived run setup: the host tier map, init-v5 --host, dispatch alias defaults, strict pin refusal."""

import json
import unittest
from pathlib import Path

from tests.planning_ledger_dispatch_test import DispatchHarness, git, ledger, leaf

MAP_PATH = Path(__file__).resolve().parents[1] / "souroldgeezer-policy/skills/planning-policy/references/host-tiers.json"
EVIDENCE = "host inventory line"


def skill_leaf(sid, tier):
    value = leaf(sid, f"owner-{sid}")
    value["portable_tier"] = tier
    if tier in {"analytical", "deep"}:
        value["irreducible_unknown_or_risk"] = "an open design choice"
    value["capability_requirements"]["additional"] = [
        {"kind": "skill", "name": "software-design", "reason": "domain rules"}
    ]
    return value


class DerivedHarness(DispatchHarness):
    def init_derived(self, leaves, *extra, **plan_fields):
        plan = {
            "contract_version": 5, "objective": "objective", "scope_summary": "scope",
            "approved_decisions": ["settled"], "leaves": leaves,
            "work_units": [
                {"id": item["id"], "original_size": "small",
                 "cohesive_outcome": f"Complete {item['id']}", "decomposition": {"shape": "single"}}
                for item in leaves
            ],
            **plan_fields,
        }
        path = self.scratch / "plan.json"
        path.write_text(json.dumps(plan))
        code, result = self.call("init-v5", "--actor", "parent", "--approved",
                                 "--plan-file", str(path), *extra)
        if code == 0:
            self.run_id = result["run_id"]
        return code, result

    def checkpoint(self):
        return json.loads(self.checkpoint_path().read_text())


class HostTierMapTest(unittest.TestCase):
    def test_map_names_every_tier_for_both_hosts_with_skill_false_only_for_claude_mechanical(self):
        tiers = json.loads(MAP_PATH.read_text())
        self.assertEqual("planning-host-tiers-v1", tiers["schema"])
        self.assertEqual({"claude-code", "codex"}, set(tiers["hosts"]))
        for host, entry in tiers["hosts"].items():
            self.assertEqual(set(ledger.PORTABLE_TIERS), set(entry["tiers"]), host)
            self.assertEqual({"plan-verify-standard", "plan-verify-analytical"}, set(entry["verifiers"]))
        without_skill = [
            (host, tier) for host, entry in tiers["hosts"].items()
            for tier, value in entry["tiers"].items() if not value["skill"]
        ]
        self.assertEqual([("claude-code", "mechanical")], without_skill)


class DerivedInitTest(DerivedHarness):
    def test_host_derives_assignments_and_binding_from_the_map(self):
        code, result = self.init_derived(
            [leaf("alpha", "owner-a"), skill_leaf("beta", "analytical"), leaf("gamma", "owner-c")],
            "--host", "claude-code", "--evidence", f"{EVIDENCE}\nsecond line",
        )
        self.assertEqual(0, code, result)
        data = self.checkpoint()
        self.assertEqual("claude-code", data["host"])
        alpha, beta = data["steps"]["alpha"], data["steps"]["beta"]
        self.assertEqual(
            ("claude-code", "sonnet", "medium", str(self.repo.resolve() / ".worktrees/owner-a")),
            tuple(alpha["assignment"][key] for key in ("harness", "model_or_alias", "effort", "worktree")),
        )
        self.assertEqual(("opus", "high"), (beta["assignment"]["model_or_alias"], beta["assignment"]["effort"]))
        bound = beta["capability_binding"]["bindings"][0]
        self.assertEqual(("claude-code", "opus", [EVIDENCE, "second line"]),
                         (bound["host"], bound["executor"], bound["evidence"]))
        self.assertEqual(skill_leaf("beta", "analytical")["capability_requirements"], bound["requirements"])

    def test_derived_worktrees_resolve_under_the_primary_checkout_from_a_linked_worktree(self):
        primary = self.repo
        linked = primary / ".worktrees/throughput"
        git(primary, "worktree", "add", "-b", "throughput", str(linked), "main")
        self.repo = linked
        try:
            code, result = self.init_derived(
                [leaf("alpha", "owner-a"), leaf("beta", "owner-b")],
                "--host", "claude-code", "--evidence", EVIDENCE,
            )
        finally:
            self.repo = primary
        self.assertEqual(0, code, result)
        for sid, owner in (("alpha", "owner-a"), ("beta", "owner-b")):
            self.assertEqual(
                str(primary.resolve() / ".worktrees" / owner),
                self.checkpoint()["steps"][sid]["assignment"]["worktree"],
            )

    def test_file_and_host_inputs_are_mutually_exclusive(self):
        leaves = [leaf("alpha", "owner-a")]
        for extra in (("--host", "codex", "--evidence", EVIDENCE, "--assignments-file", "x.json"), (), ("--host", "codex"),
                      ("--host", "nowhere", "--evidence", EVIDENCE),
                      ("--host", "codex", "--evidence", "\n".join(["line"] * 9)),
                      ("--host", "codex", "--evidence", "x" * 241)):
            code, result = self.init_derived(leaves, *extra)
            self.assertEqual(2, code, (extra, result))

    def test_skill_requirement_on_a_skill_less_tier_is_unavailable(self):
        leaves = [skill_leaf("alpha", "mechanical"), leaf("beta", "owner-b"), leaf("gamma", "owner-c")]
        code, result = self.init_derived(leaves, "--host", "claude-code", "--evidence", EVIDENCE)
        self.assertEqual((3, "blocked:capability_unavailable"), (code, result["error"]))
        code, result = self.init_derived(leaves, "--host", "codex", "--evidence", EVIDENCE)
        self.assertEqual(0, code, result)


class DerivedDispatchTest(DerivedHarness):
    def start(self, *extra):
        self.init_derived([leaf("alpha", "owner-a")], "--host", "codex", "--evidence", EVIDENCE)
        return self.dispatch("alpha", "--create-from", "main", *extra)

    def test_dispatch_defaults_the_alias_to_the_map_entry(self):
        code, result = self.start()
        self.assertEqual(0, code, result)
        self.assertEqual("gpt-5.6-terra", result["handoffs"][0]["executor"])

    def test_explicit_alias_must_equal_the_map_entry(self):
        code, result = self.start("--model-or-alias", "sonnet")
        self.assertEqual(3, code, result)
        self.assertIn("gpt-5.6-terra", result["error"])
        code, result = self.dispatch("alpha", "--create-from", "main", "--model-or-alias", "gpt-5.6-terra")
        self.assertEqual(0, code, result)


class DerivedRetryRebindingTest(DerivedHarness):
    def escalated_retry(self, *extra):
        self.init_derived([leaf("alpha", "owner-a")], "--host", "claude-code", "--evidence", EVIDENCE)
        packet = self.dispatch("alpha", "--create-from", "main")[1]["handoffs"][0]
        stopped = {
            "schema": "bounded-step-return-v1", "step_id": "alpha", "attempt_id": packet["attempt_id"],
            "agent_id": packet["agent_id"], "status": "blocked", "changed_paths": [],
            "acceptance": {"command": "uv run test", "exit_code": None, "summary": "stuck"},
            "blockers": [{"code": "blocked:needs_higher_tier", "summary": "needs deeper reasoning"}],
            "notes": [], "unstarted_remainder": [], "commit_hash": "",
        }
        (self.scratch / "return.json").write_text(json.dumps(stopped))
        code, result = self.call("record-return", "--actor", "parent", "--run-id", self.run_id,
                                 "--return-file", str(self.scratch / "return.json"))
        self.assertEqual(0, code, result)
        step = self.checkpoint()["steps"]["alpha"]
        (self.scratch / "remediation.json").write_text(json.dumps({
            "schema": "retry-remediation-v1", "step_id": "alpha", "prior_attempt_id": step["attempt_id"],
            "prior_return_sha256": step["return_sha256"], "diagnosis": "needs deeper reasoning",
            "remediation_action": "escalate", "executor_mode": "reuse", "next_agent_id": "worker",
            "next_harness": "claude-code", "target_portable_tier": "analytical",
        }))
        return self.dispatch("alpha", "--retry", "--retry-remediation-file",
                             str(self.scratch / "remediation.json"), *extra)

    def test_host_run_derives_the_binding_for_the_escalated_tier(self):
        code, result = self.escalated_retry()
        self.assertEqual(0, code, result)
        bound = self.checkpoint()["steps"]["alpha"]["capability_binding"]["bindings"][0]
        self.assertEqual(("claude-code", "opus", [EVIDENCE]), (bound["host"], bound["executor"], bound["evidence"]))
        self.assertEqual("opus", result["handoffs"][0]["executor"])


class StrictInitPinTest(DerivedHarness):
    def init_strict(self, *extra):
        return self.init_derived(
            [leaf("alpha", "owner-a")], "--host", "codex", "--evidence", EVIDENCE, *extra, precision="strict"
        )

    def test_strict_plan_requires_pin_roots(self):
        code, result = self.init_strict()
        self.assertEqual(2, code, result)

    def test_unowned_pin_refuses_init_and_names_it(self):
        pin = self.repo / "tests/test_alpha.py"
        pin.parent.mkdir()
        pin.write_text("PATH = 'src/alpha'\n")
        code, result = self.init_strict("--pin-roots", "tests")
        self.assertEqual(3, code, result)
        self.assertIn("PLANSCOPE-UNOWNED-PIN", result["error"])
        self.assertIn("tests/test_alpha.py", result["error"])
        pin.write_text("nothing\n")
        code, result = self.init_strict("--pin-roots", "tests")
        self.assertEqual(0, code, result)
        self.assertEqual("strict_v1", self.checkpoint()["precision_policy"])


if __name__ == "__main__":
    unittest.main()
