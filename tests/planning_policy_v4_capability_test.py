"""Regressions for v5 capability binding and resumable v4 checkpoints."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "souroldgeezer-policy/skills/planning-policy"
SCRIPTS = POLICY / "references/scripts"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


contract = load("planning_policy_v4_capability_contract", SCRIPTS / "validate_plan_contract.py")
ledger = load("planning_policy_v4_capability_ledger", SCRIPTS / "planning_ledger.py")


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def plan(version: int = 5) -> dict:
    value = {
        "contract_version": version,
        "objective": "Dispatch one capability-bound delegated step",
        "scope_summary": "Only the named worker and focused validation are in scope.",
        "approved_decisions": ["Resolve declared capabilities before dispatch."],
        "work_units": [{"id": "build", "original_size": "small"}],
        "leaves": [
            {
                "id": "build",
                "dependencies": [],
                "task": "Implement the bounded change",
                "boundary": "Do not edit adjacent modules",
                "read_set": ["src/input.py"],
                "write_set": ["src/output.py"],
                "settled_decisions": {"shape": "settled"},
                "size": "small",
                "portable_tier": "standard",
                "worktree_owner": "task/build",
                "acceptance_command": "uv run python -m unittest tests.focused_test",
                "return_contract": "bounded-step-return-v1",
                "stop_conditions": ["missing_load_bearing_information"],
                "work_unit_id": "build",
                "max_attempts": 2,
                "capability_requirements": {
                    "baseline": "plan-step-base-v1",
                    "additional": [
                        {
                            "kind": "skill",
                            "name": "repository-policy",
                            "reason": "The approved task requires its workflow.",
                        }
                    ],
                },
            }
        ],
    }
    if version == 5:
        value["work_units"][0].update(
            cohesive_outcome="Complete the capability-bound delegated step",
            decomposition={"shape": "single"},
        )
    return value


def binding(value: dict, *, executor: str = "gpt-5.6-terra") -> dict:
    return {
        "schema": "planning-capability-binding-v1",
        "plan_sha256": canonical_sha256(value),
        "bindings": [
            {
                "step_id": "build",
                "host": "codex",
                "executor": executor,
                "requirements": copy.deepcopy(value["leaves"][0]["capability_requirements"]),
                "evidence": ["host capability inventory: current assignment"],
            }
        ],
    }


def validate(value: dict, capability_binding: dict | None = None) -> dict:
    """Keep RED failures about absent v4 behavior, not an interim call signature."""
    if capability_binding is None:
        result = contract.validate(value)
        result.setdefault("approval_ready", False)
        return result
    try:
        return contract.validate(value, capability_binding=capability_binding)
    except TypeError:
        return {
            "valid": False,
            "approval_ready": False,
            "dispatch_ready": False,
            "warnings": ["blocked:capability_unavailable"],
            "errors": ["capability binding validation is unavailable"],
        }


class CapabilityPlanContractTest(unittest.TestCase):
    def test_v5_requires_a_structured_baseline_and_additional_requirements(self) -> None:
        valid = validate(plan())
        self.assertTrue(valid["valid"], valid["errors"])
        self.assertTrue(valid["approval_ready"])
        self.assertFalse(valid["dispatch_ready"])

        for malformed in (
            {"baseline": "wrong", "additional": []},
            {"baseline": "plan-step-base-v1", "additional": [{"kind": "skill"}]},
            {
                "baseline": "plan-step-base-v1",
                "additional": [{"kind": "unknown", "name": "x", "reason": "needed"}],
            },
        ):
            candidate = plan()
            candidate["leaves"][0]["capability_requirements"] = malformed
            result = validate(candidate)
            with self.subTest(requirements=malformed):
                self.assertFalse(result["valid"])
                self.assertFalse(result["approval_ready"])

    def test_v5_dispatch_requires_a_complete_binding_joined_to_plan_and_leaves(self) -> None:
        candidate = plan()
        resolved = binding(candidate)
        approved = validate(candidate, capability_binding=resolved)
        self.assertTrue(approved["valid"], approved["errors"])
        self.assertTrue(approved["approval_ready"])
        self.assertTrue(approved["dispatch_ready"])

        for changed in (
            {**resolved, "plan_sha256": "0" * 64},
            {**resolved, "bindings": []},
            {
                **resolved,
                "bindings": [
                    {
                        **resolved["bindings"][0],
                        "requirements": {
                            "baseline": "plan-step-base-v1",
                            "additional": [],
                        },
                    }
                ],
            },
        ):
            result = validate(candidate, capability_binding=changed)
            with self.subTest(binding=changed):
                self.assertTrue(result["valid"], result["errors"])
                self.assertTrue(result["approval_ready"])
                self.assertFalse(result["dispatch_ready"])
                self.assertIn("blocked:capability_unavailable", result["warnings"])

    def test_v4_is_resume_only_when_v5_becomes_the_forward_contract(self) -> None:
        legacy = plan(version=4)
        result = validate(legacy)
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue(result["resume_ready"])
        self.assertFalse(result["approval_ready"])
        self.assertFalse(result["dispatch_ready"])
        self.assertIn("blocked:contract_migration_required", result["warnings"])


class CapabilityLedgerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.common = ["--ledger-root", str(self.root), "--plan-id", "capability-plan"]
        self.plan = plan()
        self.plan_file = self.root / "plan.json"
        self.plan_file.write_text(json.dumps(self.plan), encoding="utf-8")
        self.binding_file = self.root / "binding.json"
        self.binding_file.write_text(json.dumps(binding(self.plan)), encoding="utf-8")
        self.assignments_file = self.root / "assignments.json"
        self.assignments_file.write_text(
            json.dumps(
                [
                    {
                        "id": "build",
                        "harness": "codex",
                        "model_or_alias": "gpt-5.6-terra",
                        "effort": "medium",
                        "worktree": ".worktrees/build",
                    }
                ]
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def call(self, *args: str):
        with (
            contextlib.redirect_stdout(io.StringIO()) as stream,
            contextlib.redirect_stderr(io.StringIO()),
        ):
            try:
                code = ledger.main(args)
            except SystemExit as error:
                return error.code, {"error": "ledger command is unavailable"}
        return code, json.loads(stream.getvalue())

    def init5(self) -> str:
        code, result = self.call(
            *self.common,
            "init-v5",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(self.plan_file),
            "--assignments-file",
            str(self.assignments_file),
            "--capability-binding-file",
            str(self.binding_file),
        )
        self.assertEqual(0, code, result)
        self.assertEqual("init-v5", result["action"])
        return result["run_id"]

    def checkpoint(self, run_id: str) -> dict:
        path = self.root / "planning-policy/ledgers/capability-plan" / run_id / "checkpoint.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_init_v5_retains_binding_with_the_assignment(self) -> None:
        run_id = self.init5()
        checkpoint = self.checkpoint(run_id)
        step = checkpoint["steps"]["build"]
        self.assertEqual(5, checkpoint["schema"])
        self.assertEqual("planning-capability-binding-v1", step["capability_binding"]["schema"])
        self.assertEqual(canonical_sha256(self.plan), step["capability_binding"]["plan_sha256"])
        self.assertEqual("gpt-5.6-terra", step["capability_binding"]["bindings"][0]["executor"])

    def test_retry_assignment_change_requires_a_matching_rebinding_before_ready(self) -> None:
        run_id = self.init5()
        code, blocked = self.call(
            *self.common,
            "transition",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--step-id",
            "build",
            "--to",
            "ready",
            "--agent-id",
            "new-agent",
            "--model-or-alias",
            "gpt-5.6-sol",
        )
        self.assertEqual(3, code)
        self.assertEqual("blocked:capability_unavailable", blocked["error"])

        replacement = binding(self.plan, executor="gpt-5.6-sol")
        replacement_file = self.root / "replacement-binding.json"
        replacement_file.write_text(json.dumps(replacement), encoding="utf-8")
        code, ready = self.call(
            *self.common,
            "transition",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--step-id",
            "build",
            "--to",
            "ready",
            "--agent-id",
            "new-agent",
            "--model-or-alias",
            "gpt-5.6-sol",
            "--capability-binding-file",
            str(replacement_file),
        )
        self.assertEqual(0, code, ready)
        self.assertEqual(
            "gpt-5.6-sol",
            self.checkpoint(run_id)["steps"]["build"]["capability_binding"]["bindings"][0]["executor"],
        )

    def test_init_v4_requires_contract_migration(self) -> None:
        legacy_plan = plan(version=4)
        self.plan_file.write_text(json.dumps(legacy_plan), encoding="utf-8")
        self.binding_file.write_text(json.dumps(binding(legacy_plan)), encoding="utf-8")
        code, result = self.call(
            *self.common,
            "init-v4",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(self.plan_file),
            "--assignments-file",
            str(self.assignments_file),
            "--capability-binding-file",
            str(self.binding_file),
        )
        self.assertEqual(3, code)
        self.assertEqual("blocked:contract_migration_required", result["error"])

    def test_existing_v4_checkpoint_resumes_without_serialized_shape_change(self) -> None:
        run_id = self.init5()
        run = self.root / "planning-policy/ledgers/capability-plan" / run_id
        legacy_plan = plan(version=4)
        legacy_hash = canonical_sha256(legacy_plan)
        checkpoint = json.loads((run / "checkpoint.json").read_text(encoding="utf-8"))
        checkpoint["schema"] = 4
        checkpoint["plan_hash"] = legacy_hash
        stored = checkpoint["steps"]["build"]["capability_binding"]
        stored["plan_sha256"] = legacy_hash
        checkpoint["steps"]["build"]["capability_binding_sha256"] = canonical_sha256(stored)
        (run / "plan.json").write_text(json.dumps(legacy_plan), encoding="utf-8")
        (run / "checkpoint.json").write_text(json.dumps(checkpoint), encoding="utf-8")
        events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
        events[0]["action"] = "init-v4"
        (run / "events.jsonl").write_text(
            "".join(
                json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
                for event in events
            ),
            encoding="utf-8",
        )
        checkpoint_path = run / "checkpoint.json"
        before = checkpoint_path.read_bytes()

        code, result = self.call(*self.common, "show", "--run-id", run_id)

        self.assertEqual(0, code, result)
        self.assertEqual(4, result["contract_version"])
        self.assertEqual(before, checkpoint_path.read_bytes())

        code, next_result = self.call(
            *self.common, "show", "--run-id", run_id, "--next-only"
        )
        self.assertEqual(0, code, next_result)
        self.assertEqual("ready_pending", next_result["next"]["category"])

        code, ready = self.call(
            *self.common,
            "transition",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--step-id",
            "build",
            "--to",
            "ready",
            "--agent-id",
            "legacy-v4-agent",
        )
        self.assertEqual(0, code, ready)
        self.assertIn("next", ready)

        code, listed = self.call(*self.common, "list")
        self.assertEqual(0, code, listed)
        [entry] = listed["runs"]
        self.assertEqual(4, entry["contract_version"])


class CapabilityAdapterTest(unittest.TestCase):
    def test_host_adapters_require_the_exact_binding_in_each_handoff(self) -> None:
        for relative in ("extensions/codex.md", "extensions/claude-code.md"):
            text = (POLICY / relative).read_text(encoding="utf-8")
            with self.subTest(adapter=relative):
                self.assertIn("planning-capability-binding-v1", text)
                self.assertIn("capability_requirements", text)
                self.assertIn("exact resolved binding", text)
                self.assertIn("blocked:capability_unavailable", text)
                self.assertIn("do not silently substitute", text)


class CapabilityDocumentationTest(unittest.TestCase):
    def test_public_runtime_neutral_guidance_has_v4_capability_parity(self) -> None:
        for relative in ("README.md", "AGENTS.md", "CLAUDE.md", "docs/skill-architecture.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(document=relative):
                for phrase in (
                    "contract_version: 4",
                    "capability_requirements",
                    "plan-step-base-v1",
                    "planning-capability-binding-v1",
                    "approval-ready",
                    "dispatch-ready",
                    "blocked:capability_unavailable",
                ):
                    self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
