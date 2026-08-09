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
        }
        self.assertTrue(required.issubset(self.behavior))
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

    def test_offline_runner_matrix_never_calls_hosts_without_execute(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            exit_code = self.runner.main(["--harness", "both", "--output-dir", str(output)])
            self.assertEqual(exit_code, 0)
            payload = json.loads((output / "planning-policy-forward-eval.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "planning-policy-forward-eval/v1")
        self.assertEqual(len(payload["runs"]), 12)
        self.assertEqual(Counter(run["status"] for run in payload["runs"]), {"not_run:execute_required": 12})
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
        self.assertEqual(claude[claude.index("--permission-mode") + 1], "acceptEdits")
        self.assertEqual(claude[claude.index("--output-format") + 1], "json")
        self.assertIn("--json-schema", claude)
        self.assertEqual(claude[claude.index("--max-budget-usd") + 1], "0.5")
        self.assertEqual(claude[-1], "prompt")
        self.assertIn("--ephemeral", codex)
        self.assertIn("--approve-for-me", codex)
        self.assertEqual(codex[codex.index("--sandbox") + 1], "workspace-write")
        self.assertNotIn("--reasoning-effort", codex)
        self.assertEqual(codex[codex.index("-c") + 1], 'model_reasoning_effort="medium"')
        self.assertIn("--output-schema", codex)
        self.assertIn("--output-last-message", codex)

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


if __name__ == "__main__":
    unittest.main()
