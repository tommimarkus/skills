import importlib.util
import json
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "souroldgeezer-policy/skills/planning-policy/references/evals"
FIXTURES = ROOT / "tests/planning_policy_forward"
RUNNER = ROOT / "scripts/planning_policy_forward_eval.py"
CONTRACT = ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts/validate_plan_contract.py"


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def leaf(identifier, unit, tier="standard"):
    value = {
        "id": identifier, "dependencies": [], "task": "One bounded concern", "boundary": "No adjacent edits",
        "read_set": ["input.py"], "write_set": ["output.py"], "settled_decisions": {"shape": "set"},
        "size": "medium", "portable_tier": tier, "worktree_owner": "task/eval",
        "acceptance_command": "uv run python -m unittest tests.example", "return_contract": "bounded result",
        "stop_conditions": ["missing_load_bearing_information"], "work_unit_id": unit,
    }
    if tier in {"analytical", "deep"}:
        value["irreducible_unknown_or_risk"] = "A bounded unresolved compatibility question"
    return value


class PlanningPolicyBehaviorEvalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.behavior = {case["id"]: case for case in load_jsonl(EVALS / "behavior-cases.jsonl")}
        cls.forward = load_jsonl(EVALS / "forward-cases.jsonl")
        cls.runner = load_module("planning_policy_forward_eval", RUNNER)
        cls.contract = load_module("planning_policy_contract_eval", CONTRACT)

    def test_required_contract_and_audit_cases_are_evidence_backed(self):
        required = {
            "planning-policy-behavior-readiness-weighted-floor",
            "planning-policy-behavior-readiness-no-leaf-gaming",
            "planning-policy-behavior-audit-ordinary-design",
            "planning-policy-behavior-audit-vague-risk",
            "planning-policy-behavior-audit-bounded-owner",
            "planning-policy-behavior-claude-clean-closeout",
            "planning-policy-behavior-codex-clean-closeout",
            "planning-policy-behavior-retry-same-tier-remediation",
            "planning-policy-behavior-retry-immediate-escalation",
            "planning-policy-behavior-retry-terminal-precedence",
            "planning-policy-behavior-retry-legacy-compatibility",
            "planning-policy-behavior-v3-cost-advisory",
            "planning-policy-behavior-v3-trace-opt-in",
            "planning-policy-behavior-v3-v2-resume-only",
            "planning-policy-behavior-v4-canonical-scaffold",
            "planning-policy-behavior-v4-claude-mechanical-skill-block",
        }
        self.assertTrue(required.issubset(self.behavior))
        scaffold = self.behavior["planning-policy-behavior-v4-canonical-scaffold"]
        self.assertIn("plan-v4.json", " ".join(scaffold["expected_artifacts"]))
        self.assertIn("contract_version", " ".join(scaffold["required_checks"]))
        self.assertIn("version", " ".join(scaffold["forbidden_behaviors"]))
        capability_block = self.behavior["planning-policy-behavior-v4-claude-mechanical-skill-block"]
        self.assertIn("Claude mechanical wrapper lacks Skill", " ".join(capability_block["required_checks"]))
        self.assertIn("blocked:capability_unavailable", " ".join(capability_block["expected_artifacts"]))
        for host in ("claude", "codex"):
            closeout = self.behavior[f"planning-policy-behavior-{host}-clean-closeout"]
            self.assertIn("routine cherry-pick", closeout["forbidden_behaviors"])
            self.assertTrue(any("cleaned before" in check for check in closeout["required_checks"]))
        accepted = self.contract.validate({"work_units": [{"id": "ordinary", "original_size": "medium"}, {"id": "unknown", "original_size": "small"}], "leaves": [leaf("ordinary-work", "ordinary"), leaf("unknown-work", "unknown", "analytical")]})
        self.assertTrue(accepted["valid"])
        self.assertGreaterEqual(accepted["standard_ready_ratio"], 0.60)
        split = self.contract.validate({"work_units": [{"id": "one-unit", "original_size": "small"}], "leaves": [leaf("known-half", "one-unit"), leaf("unknown-half", "one-unit", "analytical")]})
        self.assertFalse(split["valid"])
        ordinary = leaf("ordinary-design", "design")
        ordinary["selective_audit"] = {"owner": "software-design", "initial_inspection": True, "domain_match": True, "materially_changes_approach_or_acceptance": True, "targeted_inspection_or_focused_tests_cannot_resolve": True, "question": "Which module owns state?", "evidence_surface": "src/"}
        vague = leaf("vague-risk", "risk")
        vague["selective_audit"] = {"owner": "lean-audit", "initial_inspection": True, "domain_match": True, "materially_changes_approach_or_acceptance": True, "targeted_inspection_or_focused_tests_cannot_resolve": True, "question": "review for risks", "evidence_surface": "skills/"}
        bounded = leaf("bounded-audit", "audit")
        bounded["selective_audit"] = {"owner": "test-quality-audit", "initial_inspection": True, "domain_match": True, "materially_changes_approach_or_acceptance": True, "targeted_inspection_or_focused_tests_cannot_resolve": True, "question": "Do parameterized tests conceal fixture coupling?", "evidence_surface": "tests/pagination_test.py"}
        self.assertFalse(self.contract.validate({"work_units": [{"id": "design", "original_size": "medium"}], "leaves": [ordinary]})["valid"])
        self.assertFalse(self.contract.validate({"work_units": [{"id": "risk", "original_size": "medium"}], "leaves": [vague]})["valid"])
        self.assertTrue(self.contract.validate({"work_units": [{"id": "audit", "original_size": "medium"}], "leaves": [bounded]})["valid"])

    def test_retry_behavior_cases_bind_remediation_and_preserve_compatibility(self):
        same_tier = self.behavior["planning-policy-behavior-retry-same-tier-remediation"]
        self.assertIn("failed:acceptance", " ".join(same_tier["required_checks"]))
        self.assertIn("one same-tier", " ".join(same_tier["required_checks"]))
        self.assertIn("retry-remediation-v1", " ".join(same_tier["expected_artifacts"]))
        escalation = self.behavior["planning-policy-behavior-retry-immediate-escalation"]
        self.assertIn("blocked:needs_higher_tier", " ".join(escalation["required_checks"]))
        self.assertIn("higher tier", " ".join(escalation["required_checks"]))
        terminal = self.behavior["planning-policy-behavior-retry-terminal-precedence"]
        self.assertIn("exhaustion", " ".join(terminal["required_checks"]))
        self.assertIn("ceiling", " ".join(terminal["required_checks"]))
        legacy = self.behavior["planning-policy-behavior-retry-legacy-compatibility"]
        self.assertIn("legacy_unbounded", " ".join(legacy["required_checks"]))
        self.assertIn("policy-less", " ".join(legacy["required_checks"]))

    def test_forward_matrix_uses_identical_fixtures_and_exact_mappings(self):
        by_id = {case["id"]: case for case in self.forward}
        self.assertEqual(by_id["standard-implementation"]["attempts"], 2)
        self.assertEqual(by_id["missing-load-bearing-input"]["expected_status"], "blocked:missing_input")
        self.assertEqual(by_id["oversized-standard"]["expected_status"], "blocked:oversized")
        self.assertNotIn("deep", {case["tier"] for case in self.forward})
        for case in self.forward:
            self.assertTrue((FIXTURES / case["fixture"]).is_dir())
        self.assertEqual(self.runner.MAPPINGS["claude"]["standard"], ("sonnet", "medium"))
        self.assertEqual(self.runner.MAPPINGS["codex"]["standard"], ("gpt-5.6-terra", "medium"))
        self.assertEqual(self.runner.MAPPINGS["claude"]["mechanical"], ("haiku", "low"))
        self.assertEqual(self.runner.MAPPINGS["codex"]["mechanical"], ("gpt-5.6-luna", "low"))
        self.assertEqual(self.runner.MAPPINGS["claude"]["analytical"], ("opus", "high"))
        self.assertEqual(self.runner.MAPPINGS["codex"]["analytical"], ("gpt-5.6-sol", "high"))
        required = {"id", "dependencies", "task", "boundary", "read_set", "write_set", "size", "tier", "worktree_owner", "acceptance_command", "return_contract", "stop_conditions"}
        for case in self.forward:
            self.assertTrue(required.issubset(case), case["id"])
            self.assertTrue("settled_decisions" in case or "intentionally_missing_input" in case, case["id"])
            self.assertEqual(len(case["acceptance_command"].splitlines()), 1)
        missing = by_id["missing-load-bearing-input"]
        self.assertIn("intentionally_missing_input", missing)
        self.assertNotIn("settled_decisions", missing)
        self.assertEqual(by_id["oversized-standard"]["size"], "small")
        chained = by_id["synthetic-chained-escalation"]
        self.assertEqual(chained["attempts"], 2)
        self.assertEqual(chained["attempt_sequence"][0]["tier"], "mechanical")
        self.assertEqual(chained["attempt_sequence"][0]["expected_status"], "blocked:needs_higher_tier")
        retry = chained["attempt_sequence"][1]["retry_remediation"]
        self.assertEqual(retry["schema"], "retry-remediation-v1")
        self.assertEqual(
            set(retry),
            {
                "schema",
                "step_id",
                "prior_attempt_id",
                "prior_return_sha256",
                "diagnosis",
                "remediation_action",
                "executor_mode",
                "next_agent_id",
                "next_harness",
                "target_portable_tier",
            },
        )
        self.assertEqual(retry["target_portable_tier"], "analytical")
        self.assertEqual(retry["executor_mode"], "fresh")

    def test_offline_runner_matrix_never_calls_hosts_without_execute(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            exit_code = self.runner.main(["--harness", "both", "--output-dir", str(output)])
            self.assertEqual(exit_code, 0)
            payload = json.loads((output / "planning-policy-forward-eval.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "planning-policy-forward-eval/v1")
        self.assertEqual(len(payload["runs"]), 20)
        self.assertEqual(Counter(run["status"] for run in payload["runs"]), {"not_run:execute_required": 20})
        self.assertTrue(all("evidence_paths" in run and "raw_log" not in run for run in payload["runs"]))
        self.assertFalse((output / ".forward-workdirs").exists())

    def test_stale_inheritance_expectation_was_replaced(self):
        case = self.behavior["planning-policy-behavior-delegation-contract"]
        self.assertIn("portable tier", " ".join(case["expected_artifacts"]).lower())
        self.assertIn("exact", case["grader"])
        self.assertNotIn("inherit rather", " ".join(case["required_checks"]))

    def test_host_argv_is_fresh_safe_and_uses_exact_effort_forms(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            claude = self.runner.command_for("claude", "sonnet", "medium", "prompt", root / "schema.json", root / "last.json", 0.5)
            codex = self.runner.command_for("codex", "gpt-5.6-terra", "medium", "prompt", root / "schema.json", root / "last.json", 0.5)
        self.assertIn("--no-session-persistence", claude)
        self.assertEqual(claude[claude.index("--plugin-dir") + 1], str(self.runner.POLICY_PLUGIN))
        self.assertEqual(claude[claude.index("--agent") + 1], "plan-step-standard")
        self.assertEqual(claude[claude.index("--permission-mode") + 1], "acceptEdits")
        self.assertEqual(claude[claude.index("--output-format") + 1], "json")
        self.assertIn("--json-schema", claude)
        self.assertEqual(claude[claude.index("--max-budget-usd") + 1], "0.5")
        self.assertEqual(claude[-1], "prompt")
        self.assertIn("--ephemeral", codex)
        self.assertIn("--approve-for-me", codex)
        self.assertNotIn("--sandbox", codex, "--approve-for-me already selects workspace-write")
        self.assertNotIn("--reasoning-effort", codex)
        self.assertEqual(codex[codex.index("-c") + 1], 'model_reasoning_effort="medium"')
        self.assertIn("--output-schema", codex)
        self.assertIn("--output-last-message", codex)

    def test_host_blockers_are_classified_without_downgrade(self):
        self.assertEqual(
            self.runner.classify_host_blocker("", "requested model is not available"),
            "blocked:model_unavailable",
        )
        self.assertEqual(
            self.runner.classify_host_blocker("You've hit your weekly limit", ""),
            "blocked:host_quota",
        )
        self.assertIsNone(self.runner.classify_host_blocker("", "unrelated host error"))

    def test_generated_prompts_load_shipped_surface_and_complete_handoff(self):
        case = next(case for case in self.forward if case["id"] == "standard-implementation")
        with tempfile.TemporaryDirectory() as temporary:
            workdir = Path(temporary) / "repo"
            claude_prompt = self.runner.build_prompt(case, "claude", workdir)
            codex_prompt = self.runner.build_prompt(case, "codex", workdir)
        for prompt in (claude_prompt, codex_prompt):
            for field in ("standard-implementation", "dependencies", "boundary", "read_set", "write_set", "settled_decisions", "acceptance_command", "return_contract", "stop_conditions"):
                self.assertIn(field, prompt)
        self.assertIn("# Codex execution adapter", codex_prompt)
        self.assertIn("additive adapter", codex_prompt)

    def test_chained_retry_prompt_carries_only_bounded_ledger_remediation(self):
        case = next(case for case in self.forward if case["id"] == "synthetic-chained-escalation")
        second = self.runner.case_for_attempt(case, 2)
        with tempfile.TemporaryDirectory() as temporary:
            prompt = self.runner.build_prompt(second, "codex", Path(temporary) / "repo")
        self.assertIn('"schema":"retry-remediation-v1"', prompt)
        self.assertIn('"target_portable_tier":"analytical"', prompt)
        self.assertIn('"executor_mode":"fresh"', prompt)
        self.assertIn('"prior_attempt_id":"11111111-1111-4111-8111-111111111111"', prompt)
        self.assertIn('"prior_return_sha256":', prompt)
        self.assertIn('"remediation_action":', prompt)
        self.assertIn('"next_agent_id":"synthetic-retry-agent"', prompt)
        self.assertIn('"next_harness":"synthetic-host"', prompt)
        self.assertNotIn('"prior_return":', prompt)
        self.assertEqual(self.runner.MAPPINGS["codex"][second["tier"]], ("gpt-5.6-sol", "high"))

    def test_schema_extraction_uses_claude_structured_output_and_codex_last_message(self):
        returned = {"status": "completed", "changed_paths": ["slug.py"], "acceptance_command": "python -m unittest", "acceptance_result": "passed"}
        with tempfile.TemporaryDirectory() as temporary:
            last = Path(temporary) / "last.json"
            last.write_text(json.dumps(returned), encoding="utf-8")
            claude = self.runner.extract_return("claude", json.dumps({"structured_output": returned}), last)
            codex = self.runner.extract_return("codex", "ignored raw stdout", last)
        self.assertEqual(claude, returned)
        self.assertEqual(codex, returned)
        self.assertTrue(self.runner.FINAL_SCHEMA["additionalProperties"] is False)
        self.assertIn("status", self.runner.FINAL_SCHEMA["required"])

    def test_runner_artifacts_do_not_change_stop_fixture_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workdir = root / "repo"
            shutil.copytree(FIXTURES / "missing-input", workdir)
            before = self.runner.tree_digest(workdir)
            (root / "output-schema.json").write_text(json.dumps(self.runner.FINAL_SCHEMA), encoding="utf-8")
            (root / "last-message.json").write_text("{}", encoding="utf-8")
            self.assertEqual(self.runner.tree_digest(workdir), before)

    def test_execute_returns_nonzero_for_a_verification_failure(self):
        failed = {"case_id": "case", "status": "failed:verification"}
        with tempfile.TemporaryDirectory() as temporary, patch.object(self.runner, "load_cases", return_value=[{"attempts": 1}]), patch.object(self.runner, "run_case", return_value=failed):
            self.assertEqual(self.runner.main(["--harness", "claude", "--output-dir", temporary, "--execute"]), 1)

    def test_live_execution_requires_a_private_existing_output_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            insecure = Path(temporary) / "missing"
            with self.assertRaises(SystemExit):
                self.runner.main(["--harness", "claude", "--output-dir", str(insecure), "--execute"])


if __name__ == "__main__":
    unittest.main()
