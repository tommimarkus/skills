import importlib.util
import copy
import json
import shutil
import subprocess
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
            "planning-policy-behavior-approval-inline-reset",
            "planning-policy-behavior-approval-parent-recovery",
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
            "planning-policy-behavior-v5-cost-advisory",
            "planning-policy-behavior-v5-trace-opt-in",
            "planning-policy-behavior-v5-v4-resume-only",
            "planning-policy-behavior-v5-canonical-scaffold",
            "planning-policy-behavior-v5-claude-mechanical-skill-block",
            "planning-policy-behavior-v5-live-next-rehydration",
            "planning-policy-behavior-series-close-requires-flag",
            "planning-policy-behavior-series-successor-gcd-predecessor",
            "planning-policy-behavior-series-final-end-verification",
            "planning-policy-behavior-parent-preparation",
            "planning-policy-behavior-v5-size-from-bounded-evidence",
        }
        self.assertTrue(required.issubset(self.behavior))
        scaffold = self.behavior["planning-policy-behavior-v5-canonical-scaffold"]
        self.assertIn("plan-v5.json", " ".join(scaffold["expected_artifacts"]))
        self.assertIn("contract_version", " ".join(scaffold["required_checks"]))
        self.assertIn("version", " ".join(scaffold["forbidden_behaviors"]))
        capability_block = self.behavior["planning-policy-behavior-v5-claude-mechanical-skill-block"]
        self.assertIn("Claude mechanical wrapper lacks Skill", " ".join(capability_block["required_checks"]))
        self.assertIn("blocked:capability_unavailable", " ".join(capability_block["expected_artifacts"]))
        live_next = self.behavior["planning-policy-behavior-v5-live-next-rehydration"]
        self.assertIn("show --next-only", " ".join(live_next["expected_artifacts"]))
        self.assertIn("busy polling", live_next["forbidden_behaviors"])
        self.assertTrue(any("240 proxy tokens" in check for check in live_next["required_checks"]))
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

    def test_v5_outcome_first_cases_cover_rejections_and_permitted_controls(self):
        rejected = self.behavior["planning-policy-behavior-v5-reject-microleaf-shapes"]
        self.assertIn("cohesive outcome", " ".join(rejected["required_checks"]))
        self.assertIn("tier gaming", " ".join(rejected["required_checks"]))
        self.assertIn("batch", " ".join(rejected["forbidden_behaviors"]))

    def test_grooming_prepares_one_complete_handoff_per_cohesive_outcome(self):
        preparation = self.behavior["planning-policy-behavior-parent-preparation"]
        text = " ".join(
            preparation[field]
            if isinstance(preparation[field], str)
            else " ".join(preparation[field])
            for field in ("expected_artifacts", "required_checks", "forbidden_behaviors")
        ).lower()
        for concept in ("after convergence", "call sites", "write sets", "existing acceptance", "worker judgment"):
            with self.subTest(concept=concept):
                self.assertIn(concept, text)

        sizing = self.behavior["planning-policy-behavior-v5-size-from-bounded-evidence"]
        sizing_text = " ".join(
            sizing[field]
            if isinstance(sizing[field], str)
            else " ".join(sizing[field])
            for field in ("expected_artifacts", "required_checks", "forbidden_behaviors")
        ).lower()
        for concept in ("bounded read", "acceptance", "irreducible", "two checks"):
            with self.subTest(concept=concept):
                self.assertIn(concept, sizing_text)
        parallel = self.behavior["planning-policy-behavior-v5-parallel-control"]
        self.assertIn("one cohesive outcome", " ".join(parallel["expected_artifacts"]))
        self.assertIn("basis: parallel_independence", " ".join(parallel["expected_artifacts"]))
        self.assertIn("independent acceptance", " ".join(parallel["required_checks"]))
        checkpointed = self.behavior["planning-policy-behavior-v5-checkpointed-control"]
        self.assertIn("checkpointed decomposition with shape, basis, and rationale", " ".join(checkpointed["expected_artifacts"]))
        self.assertIn("intermediate_states", " ".join(checkpointed["forbidden_behaviors"]))

    def test_forward_matrix_uses_identical_fixtures_and_exact_mappings(self):
        by_id = {case["id"]: case for case in self.forward}
        self.assertEqual(by_id["standard-implementation"]["attempts"], 2)
        self.assertEqual(by_id["missing-load-bearing-input"]["expected_status"], "blocked:missing_input")
        self.assertEqual(by_id["oversized-standard"]["expected_status"], "oversized")
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
        self.assertEqual(missing["intentionally_missing_input"], ["settled_decisions"])
        self.assertIn("settled_decisions", missing)
        self.assertEqual(by_id["oversized-standard"]["size"], "small")
        chained = by_id["synthetic-chained-escalation"]
        self.assertEqual(chained["attempts"], 2)
        initial = chained["attempt_sequence"][0]
        self.assertEqual(initial["tier"], chained["tier"])
        self.assertEqual(chained["attempt_sequence"][0]["expected_status"], "blocked:needs_higher_tier")
        retry = chained["attempt_sequence"][1]["retry_remediation"]
        ledger_next = self.runner.ledger.next_after_return(
            self.runner.argparse.Namespace(plan_id="synthetic", run_id="synthetic"),
            None, {}, {}, chained["id"],
            {"current_tier": initial["tier"], "same_tier_retry_used": False},
            {"status": "blocked", "blockers": [{"code": initial["expected_status"]}]},
            "retry_eligible", {},
        )
        self.assertEqual(retry["target_portable_tier"], ledger_next["next_tier"])
        self.assertEqual(chained["attempt_sequence"][1]["tier"], ledger_next["next_tier"])
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
        with tempfile.TemporaryDirectory() as temporary, patch.object(self.runner.subprocess, "run", side_effect=AssertionError("offline evaluation must not launch a host")):
            output = Path(temporary)
            exit_code = self.runner.main(["--harness", "both", "--output-dir", str(output)])
            self.assertEqual(exit_code, 0)
            payload = json.loads((output / "planning-policy-forward-eval.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "planning-policy-forward-eval/v1")
        self.assertEqual(len(payload["runs"]), 20)
        self.assertEqual(Counter(run["status"] for run in payload["runs"]), {"not_run:execute_required": 20})
        self.assertTrue(all("evidence_paths" in run and "raw_log" not in run for run in payload["runs"]))
        self.assertFalse((output / ".forward-workdirs").exists())

    def test_trivial_docstring_case_uses_logged_exception(self):
        case = self.behavior["planning-policy-behavior-trivial-docstring-exemption"]
        self.assertIn("one typo in one docstring", case["prompt"])
        self.assertIn("trivial edit", " ".join(case["expected_artifacts"]))
        self.assertIn("entering Plan mode", " ".join(case["forbidden_behaviors"]))

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
        for prompt in (claude_prompt, codex_prompt):
            for field in ("contract_version", "plan_sha256", "capability_binding", "attempt_id", "cohesive_outcome", "decomposition"):
                self.assertIn(field, prompt)

    def test_synthetic_assignments_are_dispatch_ready_and_only_omit_declared_input(self):
        for case in self.forward:
            assignment = self.runner.handoff_for(case, "codex", 1)
            verdict = self.contract.validate(assignment["plan"], assignment["capability_binding"])
            self.assertTrue(verdict["dispatch_ready"], (case["id"], verdict["errors"]))
            self.assertEqual(assignment["contract_version"], 5)
            self.assertEqual(assignment["step_id"], case["id"])
            self.assertEqual(assignment["capability_binding"]["bindings"][0]["step_id"], case["id"])
            omitted = set(assignment["plan"]["leaves"][0]) - set(assignment["leaf"])
            self.assertEqual(omitted, set(case.get("intentionally_missing_input", [])))

    def test_full_return_is_validated_before_comparison_facts_are_selected(self):
        case = next(case for case in self.forward if case["id"] == "standard-implementation")
        assignment = self.runner.handoff_for(case, "codex", 1)
        returned = {
            "schema": "bounded-step-return-v1", "step_id": assignment["step_id"],
            "agent_id": assignment["agent_id"], "attempt_id": assignment["attempt_id"],
            "status": "completed", "changed_paths": ["slug.py"],
            "acceptance": {"command": case["acceptance_command"], "exit_code": 0, "summary": "passed"},
            "blockers": [], "notes": [], "commit_hash": "a" * 40, "unstarted_remainder": [],
        }
        with tempfile.TemporaryDirectory() as temporary:
            last = Path(temporary) / "last.json"
            last.write_text(json.dumps(returned), encoding="utf-8")
            self.assertEqual(self.runner.extract_return("codex", "", last, assignment), returned)
            self.assertEqual(self.runner.return_summary(returned)["acceptance"]["summary"], "passed")
            for change in ({"agent_id": "foreign"}, {"acceptance": {"command": "wrong", "exit_code": 0, "summary": "passed"}}, {"blockers": None}):
                invalid = dict(returned, **change)
                last.write_text(json.dumps(invalid), encoding="utf-8")
                self.assertIsNone(self.runner.extract_return("codex", "", last, assignment))
            missing = dict(returned)
            missing.pop("notes")
            last.write_text(json.dumps(missing), encoding="utf-8")
            self.assertIsNone(self.runner.extract_return("codex", "", last, assignment))

    def test_oversized_return_and_output_cap_follow_ledger_validator(self):
        case = next(case for case in self.forward if case["id"] == "oversized-standard")
        assignment = self.runner.handoff_for(case, "claude", 1)
        returned = {
            "schema": "bounded-step-return-v1", "step_id": assignment["step_id"],
            "agent_id": assignment["agent_id"], "attempt_id": assignment["attempt_id"],
            "status": "oversized", "changed_paths": [],
            "acceptance": {"command": case["acceptance_command"], "exit_code": None, "summary": "not run"},
            "blockers": [{"code": "oversized", "summary": "too much work"}], "notes": [],
            "commit_hash": "", "unstarted_remainder": ["remaining modules"],
        }
        self.assertEqual(self.runner.bounded_return(returned, assignment), returned)
        returned["notes"] = [{"type": "finding", "message": "x" * 9000}]
        self.assertIsNone(self.runner.bounded_return(returned, assignment))
        returned["notes"] = [{"type": "finding", "message": "x" * self.runner.ledger.MAX_NOTE_MESSAGE} for _ in range(self.runner.ledger.MAX_NOTES)]
        returned["blockers"] = [{"code": "oversized", "summary": "x" * self.runner.ledger.MAX_BLOCKER_SUMMARY} for _ in range(self.runner.ledger.MAX_BLOCKERS)]
        returned["unstarted_remainder"] = ["x" * self.runner.ledger.MAX_REMAINDER_ITEM for _ in range(self.runner.ledger.MAX_REMAINDER)]
        returned["acceptance"]["summary"] = "x" * self.runner.ledger.MAX_ACCEPTANCE_SUMMARY
        self.assertGreater(len(self.runner.ledger.canon(returned)), self.runner.ledger.MAX_RETURN)
        self.assertIsNone(self.runner.bounded_return(returned, assignment))

    def test_fake_host_success_uses_current_contract_without_persisting_transcript(self):
        case = next(case for case in self.forward if case["id"] == "standard-implementation")
        assignment = self.runner.handoff_for(case, "codex", 1)
        real_run = subprocess.run

        def fake_run(args, **kwargs):
            if args[:2] != ["codex", "exec"]:
                return real_run(args, **kwargs)
            workdir = Path(kwargs["cwd"])
            (workdir / "slug.py").write_text("def slug(value: str) -> str:\n    return '-'.join(value.lower().split())\n", encoding="utf-8")
            returned = {"schema": "bounded-step-return-v1", "step_id": assignment["step_id"], "agent_id": assignment["agent_id"], "attempt_id": assignment["attempt_id"], "status": "completed", "changed_paths": ["slug.py"], "acceptance": {"command": case["acceptance_command"], "exit_code": 0, "summary": "one unittest passed"}, "blockers": [], "notes": [], "commit_hash": "a" * 40, "unstarted_remainder": []}
            Path(args[args.index("--output-last-message") + 1]).write_text(json.dumps(returned), encoding="utf-8")
            return subprocess.CompletedProcess(args, 0, "private host transcript", "")

        with tempfile.TemporaryDirectory() as temporary, patch.object(self.runner.shutil, "which", return_value="/synthetic/codex"), patch.object(self.runner.subprocess, "run", side_effect=fake_run):
            result = self.runner.run_case(case, "codex", 1, Path(temporary), True, 30, 0.5)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["return_summary"]["acceptance"]["summary"], "one unittest passed")
        self.assertNotIn("private host transcript", json.dumps(result))

    def test_v3_and_v4_resume_shapes_do_not_inherit_v5_work_unit_fields(self):
        case = next(case for case in self.forward if case["id"] == "standard-implementation")
        current = self.runner.handoff_for(case, "codex", 1)["plan"]
        for version in (3, 4):
            with self.subTest(version=version):
                plan = copy.deepcopy(current)
                plan["contract_version"] = version
                plan["work_units"][0].pop("cohesive_outcome")
                plan["work_units"][0].pop("decomposition")
                if version == 3:
                    plan["leaves"][0].pop("capability_requirements")
                verdict = self.contract.validate(plan)
                self.assertTrue(verdict["valid"], verdict["errors"])
                self.assertFalse(verdict["approval_ready"])
                self.assertFalse(verdict["dispatch_ready"])
                if version == 4:
                    binding = {"schema": "planning-capability-binding-v1", "plan_sha256": self.contract.canonical_plan_sha256(plan), "bindings": [{"step_id": case["id"], "host": "codex", "executor": "gpt-5.6-terra", "requirements": plan["leaves"][0]["capability_requirements"], "evidence": ["synthetic resume capability"]}]}
                    self.assertTrue(self.contract.validate(plan, binding)["resume_ready"])

    def test_chained_retry_prompt_carries_only_bounded_ledger_remediation(self):
        case = next(case for case in self.forward if case["id"] == "synthetic-chained-escalation")
        second = self.runner.case_for_attempt(case, 2)
        with tempfile.TemporaryDirectory() as temporary:
            prompt = self.runner.build_prompt(second, "codex", Path(temporary) / "repo", 2)
        self.assertIn('"schema":"retry-remediation-v1"', prompt)
        self.assertIn('"target_portable_tier":"analytical"', prompt)
        self.assertIn('"executor_mode":"fresh"', prompt)
        self.assertIn(f'"prior_attempt_id":"{self.runner.synthetic_id(case["id"], "codex", 1)}"', prompt)
        self.assertIn('"prior_return_sha256":', prompt)
        self.assertIn('"remediation_action":', prompt)
        self.assertIn('"next_agent_id":"forward-codex-synthetic-chained-escalation-2"', prompt)
        self.assertIn('"next_harness":"codex"', prompt)
        self.assertNotIn('"prior_return":', prompt)
        self.assertEqual(self.runner.MAPPINGS["codex"][second["tier"]], ("gpt-5.6-sol", "high"))

    def test_schema_extraction_uses_claude_structured_output_and_codex_last_message(self):
        case = next(case for case in self.forward if case["id"] == "standard-implementation")
        assignment = self.runner.handoff_for(case, "codex", 1)
        returned = {"schema": "bounded-step-return-v1", "step_id": assignment["step_id"], "agent_id": assignment["agent_id"], "attempt_id": assignment["attempt_id"], "status": "completed", "changed_paths": ["slug.py"], "acceptance": {"command": case["acceptance_command"], "exit_code": 0, "summary": "passed"}, "blockers": [], "notes": [], "commit_hash": "a" * 40, "unstarted_remainder": []}
        with tempfile.TemporaryDirectory() as temporary:
            last = Path(temporary) / "last.json"
            last.write_text(json.dumps(returned), encoding="utf-8")
            claude = self.runner.extract_return("claude", json.dumps({"structured_output": returned}), last, assignment)
            codex = self.runner.extract_return("codex", "ignored raw stdout", last, assignment)
        self.assertEqual(claude, returned)
        self.assertEqual(codex, returned)
        self.assertTrue(self.runner.FINAL_SCHEMA["additionalProperties"] is False)
        self.assertEqual(set(self.runner.FINAL_SCHEMA["required"]), set(returned))
        self.assertEqual(set(self.runner.FINAL_SCHEMA["properties"]["status"]["enum"]), self.runner.ledger.RETURN_STATUSES)

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
