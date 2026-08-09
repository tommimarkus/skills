import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = (
    Path(__file__).parents[1]
    / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py"
)
SPEC = importlib.util.spec_from_file_location("ledger", SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(ledger)


class PlanningLedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.common = ["--ledger-root", str(self.root), "--plan-id", "plan"]
        self.assignment = {
            "harness": "codex",
            "tier": "standard",
            "model_or_alias": "inherit",
            "effort": "inherit",
            "worktree": ".worktrees/a",
        }

    def tearDown(self):
        self.temp.cleanup()

    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = ledger.main(args)
        return code, json.loads(stream.getvalue())

    def v1(self):
        return json.dumps(
            [
                {"id": "build", **self.assignment},
                {"id": "verify", "dependencies": ["build"], **self.assignment},
            ]
        )

    def plan(self, count=2, max_attempts=2, portable_tier="standard"):
        leaves = []
        units = []
        for n in range(count):
            sid = f"step{n}"
            leaf = {
                "id": sid,
                "dependencies": [],
                "task": "task",
                "boundary": "boundary",
                "read_set": ["src"],
                "write_set": ["src"],
                "settled_decisions": "decision",
                "size": "small",
                "portable_tier": portable_tier,
                "worktree_owner": "owner",
                "acceptance_command": "uv run test",
                "return_contract": "bounded-step-return-v1",
                "stop_conditions": ["missing_load_bearing_information"],
                "work_unit_id": sid,
                "max_attempts": max_attempts,
            }
            if portable_tier in {"analytical", "deep"}:
                leaf["irreducible_unknown_or_risk"] = "retry behavior at the tier boundary"
            leaves.append(leaf)
            units.append({"id": sid, "original_size": "small"})
        path = self.root / "plan.json"
        plan = {
            "contract_version": 2,
            "objective": "objective",
            "scope_summary": "scope",
            "approved_decisions": ["decision"],
            "leaves": leaves,
            "work_units": units,
        }
        if portable_tier in {"analytical", "deep"}:
            plan["analytical_heavy_exception"] = {
                "rationale": "exercise retry tier boundaries",
                "user_approved_by": "test fixture",
            }
        path.write_text(json.dumps(plan))
        return path

    def assignments(self, count=2):
        path = self.root / "assign.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "id": f"step{n}",
                        "harness": "codex",
                        "model_or_alias": "inherit",
                        "effort": "medium",
                        "worktree": f".worktrees/{n}",
                    }
                    for n in range(count)
                ]
            )
        )
        return path

    def init2(self, count=2, max_attempts=2, plan_path=None, portable_tier="standard"):
        code, data = self.call(
            *self.common,
            "init-v2",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(plan_path or self.plan(count, max_attempts, portable_tier)),
            "--assignments-file",
            str(self.assignments(count)),
        )
        self.assertEqual(0, code)
        return data["run_id"]

    def checkpoint(self, run):
        return json.loads(
            (self.root / "planning-policy/ledgers/plan" / run / "checkpoint.json").read_text()
        )

    def start(self, run, sid="step0", agent="agent"):
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                sid,
                "--to",
                "ready",
                "--agent-id",
                agent,
            )[0],
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                sid,
                "--to",
                "in_progress",
            )[0],
        )
        return self.checkpoint(run)["steps"][sid]

    def blocker(self, code="blocked_reason", summary="reason"):
        return {"code": code, "summary": summary}

    def returned(
        self, step, status="completed", changed=None, code=0, blockers=None, remainder=None
    ):
        return {
            "schema": "bounded-step-return-v1",
            "step_id": step["id"],
            "attempt_id": step["attempt_id"],
            "agent_id": step["agent_id"],
            "status": status,
            "changed_paths": changed or [],
            "acceptance": {"command": "uv run test", "exit_code": code, "summary": "summary"},
            "blockers": blockers or [],
            "notes": [{"type": "finding", "message": "ok"}],
            "unstarted_remainder": remainder or [],
            "commit_hash": "a" * 40 if status == "completed" and changed else "",
        }

    def worktree_result(self, step, action="integrate", ok=True):
        source = step.get("returned_commit", "") or "a" * 40
        integrated = "b" * 40
        return {
            "schema": "planning-worktree-result-v1",
            "ok": ok,
            "action": action,
            "repo_root": "/repo",
            "target": "main",
            "branch": "owner",
            "worktree": str(Path("/repo") / step["assignment"]["worktree"]),
            "source_commit": source,
            "rebased_commit": integrated,
            "parent_before": "c" * 40,
            "parent_after": integrated,
        }

    def transition_result(self, run, sid, target, value):
        path = self.root / f"{sid}-{target}.json"
        path.write_text(json.dumps(value))
        return self.call(
            *self.common,
            "transition",
            "--actor",
            "parent",
            "--run-id",
            run,
            "--step-id",
            sid,
            "--to",
            target,
            "--worktree-result",
            str(path),
        )

    def record(self, run, value):
        path = self.root / "return.json"
        path.write_text(json.dumps(value))
        return self.call(
            *self.common,
            "record-return",
            "--actor",
            "parent",
            "--run-id",
            run,
            "--return-file",
            str(path),
        )

    def remediation(
        self,
        step,
        target_tier=None,
        executor_mode="fresh",
        next_agent_id="next-agent",
        next_harness="codex",
        prior_return_sha256=None,
        evidence=False,
    ):
        value = {
            "schema": "retry-remediation-v1",
            "step_id": step["id"],
            "prior_attempt_id": step["attempt_id"],
            "prior_return_sha256": prior_return_sha256 or step["return_sha256"],
            "diagnosis": "acceptance failure is locally remediable",
            "remediation_action": "apply the bounded correction and rerun acceptance",
            "executor_mode": executor_mode,
            "next_agent_id": next_agent_id,
            "next_harness": next_harness,
            "target_portable_tier": target_tier or step["current_tier"],
        }
        if evidence:
            value.update(evidence_path="evidence/retry.json", sha256="d" * 64)
        return value

    def retry(self, run, remediation, agent_id=""):
        path = self.root / "retry-remediation.json"
        path.write_text(json.dumps(remediation))
        arguments = [
            *self.common,
            "transition",
            "--actor",
            "parent",
            "--run-id",
            run,
            "--step-id",
            remediation["step_id"],
            "--to",
            "ready",
            "--retry",
            "--retry-remediation-file",
            str(path),
        ]
        if agent_id:
            arguments += ["--agent-id", agent_id]
        return self.call(*arguments)

    def test_new_v2_stamps_escalating_retry_state(self):
        run = self.init2()
        checkpoint = self.checkpoint(run)
        self.assertEqual("escalating_remediation_v1", checkpoint["retry_policy"])
        step = checkpoint["steps"]["step0"]
        self.assertEqual("standard", step["current_tier"])
        self.assertFalse(step["same_tier_retry_used"])
        self.assertEqual({"agent_id": "", "harness": "codex"}, step["current_assignment"])
        self.assertEqual("", step["retry_remediation_path"])
        self.assertEqual("", step["retry_remediation_sha256"])

    def test_policyless_v2_keeps_legacy_retry_behavior_without_new_state(self):
        run = self.init2()
        checkpoint_path = self.root / "planning-policy/ledgers/plan" / run / "checkpoint.json"
        checkpoint = json.loads(checkpoint_path.read_text())
        checkpoint.pop("retry_policy")
        for step in checkpoint["steps"].values():
            for field in (
                "current_tier",
                "same_tier_retry_used",
                "current_assignment",
                "retry_remediation_path",
                "retry_remediation_sha256",
            ):
                step.pop(field)
        checkpoint_path.write_text(json.dumps(checkpoint))
        before = checkpoint_path.read_bytes()
        self.assertEqual(0, self.call(*self.common, "show", "--run-id", run)[0])
        self.assertEqual(before, checkpoint_path.read_bytes())

        step = self.start(run)
        blocked = self.returned(step, "blocked", blockers=[self.blocker("arbitrary")])
        self.assertEqual(0, self.record(run, blocked)[0])
        code, _ = self.call(
            *self.common,
            "transition",
            "--actor",
            "parent",
            "--run-id",
            run,
            "--step-id",
            "step0",
            "--to",
            "ready",
            "--agent-id",
            "legacy-next",
            "--retry",
            "--summary",
            "legacy evidence",
        )
        self.assertEqual(0, code)
        current = self.checkpoint(run)
        self.assertNotIn("retry_policy", current)
        self.assertNotIn("current_tier", current["steps"]["step0"])

    def test_same_tier_retry_persists_validated_remediation_and_assignment(self):
        run = self.init2(max_attempts=3)
        first = self.start(run, agent="first-agent")
        returned = self.returned(
            first,
            "failed",
            code=1,
            blockers=[self.blocker("failed:acceptance", "focused acceptance failed")],
        )
        self.assertEqual(0, self.record(run, returned)[0])
        failed = self.checkpoint(run)["steps"]["step0"]
        approved_worktree = failed["assignment"]["worktree"]
        remediation = self.remediation(
            failed,
            next_agent_id="fresh-agent",
            next_harness="claude-code",
            evidence=True,
        )
        code, result = self.retry(run, remediation)
        self.assertEqual(0, code, result)

        state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual("standard", state["current_tier"])
        self.assertTrue(state["same_tier_retry_used"])
        self.assertEqual(
            {"agent_id": "fresh-agent", "harness": "claude-code"},
            state["current_assignment"],
        )
        self.assertEqual("fresh-agent", state["agent_id"])
        self.assertEqual(approved_worktree, state["assignment"]["worktree"])
        artifact_path = (
            self.root / "planning-policy/ledgers/plan" / run / state["retry_remediation_path"]
        )
        self.assertEqual(remediation, json.loads(artifact_path.read_text()))
        self.assertEqual(ledger.digest(remediation), state["retry_remediation_sha256"])
        events = (self.root / "planning-policy/ledgers/plan" / run / "events.jsonl").read_text()
        self.assertNotIn(remediation["diagnosis"], events)

    def test_retry_remediation_rejects_stale_identity_bad_mode_and_tier_decrease(self):
        run = self.init2(max_attempts=3, portable_tier="analytical")
        first = self.start(run, agent="first-agent")
        self.assertEqual(
            0,
            self.record(
                run,
                self.returned(
                    first,
                    "failed",
                    code=1,
                    blockers=[self.blocker("failed:acceptance")],
                ),
            )[0],
        )
        failed = self.checkpoint(run)["steps"]["step0"]
        invalid = (
            self.remediation(failed, prior_return_sha256="0" * 64),
            self.remediation(failed, executor_mode="reuse", next_agent_id="different-agent"),
            self.remediation(failed, target_tier="standard"),
        )
        for remediation in invalid:
            with self.subTest(remediation=remediation):
                self.assertEqual(3, self.retry(run, remediation)[0])
        valid = self.remediation(failed, executor_mode="reuse", next_agent_id="first-agent")
        self.assertEqual(0, self.retry(run, valid)[0])

    def test_needs_higher_tier_escalates_and_later_retry_cannot_stay_same_tier(self):
        run = self.init2(max_attempts=4)
        first = self.start(run, agent="first")
        self.assertEqual(
            0,
            self.record(
                run,
                self.returned(
                    first,
                    "blocked",
                    code=None,
                    blockers=[self.blocker("blocked:needs_higher_tier")],
                ),
            )[0],
        )
        blocked = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(3, self.retry(run, self.remediation(blocked))[0])
        self.assertEqual(
            0,
            self.retry(
                run,
                self.remediation(
                    blocked, target_tier="analytical", next_agent_id="analytical-agent"
                ),
            )[0],
        )
        second = self.start_after_ready(run)
        self.assertEqual(
            0,
            self.record(
                run,
                self.returned(
                    second,
                    "failed",
                    code=1,
                    blockers=[self.blocker("failed:acceptance")],
                ),
            )[0],
        )
        failed = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(
            3,
            self.retry(
                run,
                self.remediation(failed, target_tier="analytical", next_agent_id="same-tier-agent"),
            )[0],
        )
        self.assertEqual(
            0,
            self.retry(
                run,
                self.remediation(failed, target_tier="deep", next_agent_id="deep-agent"),
            )[0],
        )

    def test_v1_lifecycle_byte_shape_and_disclosure(self):
        self.assertEqual(
            0,
            self.call(
                *self.common, "init", "--actor", "parent", "--approved", "--steps-json", self.v1()
            )[0],
        )
        original = json.loads(
            (self.root / "planning-policy/ledgers/plan/checkpoint.json").read_text()
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--step-id",
                "build",
                "--to",
                "ready",
            )[0],
        )
        code, shown = self.call(*self.common, "show")
        self.assertEqual(0, code)
        self.assertEqual(1, shown["legacy_schema"])
        self.assertTrue(shown["rehydration_incomplete"])
        self.assertEqual("legacy_unbounded", shown["retry_policy"])
        current = json.loads(
            (self.root / "planning-policy/ledgers/plan/checkpoint.json").read_text()
        )
        self.assertEqual(set(original), set(current))
        self.assertEqual(1, current["schema_version"])

    def test_v1_full_retry_integration_and_event_validation(self):
        self.assertEqual(
            0,
            self.call(
                *self.common, "init", "--actor", "parent", "--approved", "--steps-json", self.v1()
            )[0],
        )
        for target in ("ready", "in_progress"):
            self.assertEqual(
                0,
                self.call(
                    *self.common,
                    "transition",
                    "--actor",
                    "parent",
                    "--step-id",
                    "build",
                    "--to",
                    target,
                )[0],
            )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--step-id",
                "build",
                "--to",
                "blocked",
                "--blocker-code",
                "blocked:model_unavailable",
            )[0],
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--step-id",
                "build",
                "--to",
                "ready",
                "--retry",
                "--evidence-path",
                "evidence/retry.json",
                "--summary",
                "model restored",
            )[0],
        )
        for target in ("in_progress", "completed", "integrated"):
            arguments = [
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--step-id",
                "build",
                "--to",
                target,
            ]
            if target == "integrated":
                arguments += ["--summary", "integrated"]
            self.assertEqual(0, self.call(*arguments)[0])
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--step-id",
                "verify",
                "--to",
                "ready",
            )[0],
        )
        code, validated = self.call(*self.common, "validate")
        self.assertEqual(0, code)
        self.assertTrue(validated["ok"])
        checkpoint = json.loads(
            (self.root / "planning-policy/ledgers/plan/checkpoint.json").read_text()
        )
        self.assertEqual(2, checkpoint["steps"]["build"]["attempt"])
        self.assertEqual("codex", checkpoint["steps"]["build"]["harness"])
        events = [
            json.loads(line)
            for line in (self.root / "planning-policy/ledgers/plan/events.jsonl")
            .read_text()
            .splitlines()
        ]
        self.assertEqual(list(range(1, len(events) + 1)), [event["sequence"] for event in events])

    def test_v1_init_rejects_dependency_cycles(self):
        cyclic = json.dumps(
            [
                {"id": "build", "dependencies": ["verify"], **self.assignment},
                {"id": "verify", "dependencies": ["build"], **self.assignment},
            ]
        )
        self.assertEqual(
            3,
            self.call(
                *self.common, "init", "--actor", "parent", "--approved", "--steps-json", cyclic
            )[0],
        )

    def test_twenty_isolated_generated_uuid_runs_and_assignment_join(self):
        runs = [self.init2() for _ in range(20)]
        self.assertEqual(20, len(set(runs)))
        base = self.root / "planning-policy/ledgers/plan"
        self.assertEqual(20, len([p for p in base.iterdir() if p.is_dir()]))
        self.assertTrue(all(len(x) == 36 for x in runs))
        bad = self.assignments()
        bad.write_text("[]")
        self.assertEqual(
            3,
            self.call(
                *self.common,
                "init-v2",
                "--actor",
                "parent",
                "--approved",
                "--plan-file",
                str(self.plan()),
                "--assignments-file",
                str(bad),
            )[0],
        )

    def test_run_isolation_independent_steps_and_identity(self):
        one, two = self.init2(), self.init2()
        first = self.start(one, "step0", "agent-one")
        self.start(one, "step1", "agent-two")
        self.assertEqual("pending", self.checkpoint(two)["steps"]["step0"]["status"])
        self.assertEqual(
            3,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                two,
                "--step-id",
                "missing",
                "--to",
                "ready",
                "--agent-id",
                "x",
            )[0],
        )
        stale = self.returned(first)
        stale["agent_id"] = "other"
        self.assertEqual(3, self.record(one, stale)[0])

    def test_return_limits_paths_copy_completion_and_tamper(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, changed=["src/file.py"])
        code, result = self.record(run, value)
        self.assertEqual(0, code)
        self.assertEqual("completed", result["status"])
        self.assertTrue(
            (
                self.root
                / "planning-policy/ledgers/plan"
                / run
                / "returns"
                / "step0"
                / f"{step['attempt_id']}.json"
            ).is_file()
        )
        step = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(
            0, self.transition_result(run, "step0", "integrated", self.worktree_result(step))[0]
        )
        plan = self.root / "planning-policy/ledgers/plan" / run / "plan.json"
        plan.write_text("{}")
        self.assertEqual(3, self.call(*self.common, "show", "--run-id", run)[0])

    def test_retry_fingerprints_exhaustion_and_oversized(self):
        run = self.init2(max_attempts=2)
        step = self.start(run)
        failed = self.returned(step, "failed", code=1, blockers=[self.blocker("failed:acceptance")])
        self.assertEqual(0, self.record(run, failed)[0])
        failed_state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(0, self.retry(run, self.remediation(failed_state))[0])
        step = self.start_after_ready(run)
        self.assertEqual(
            0,
            self.record(
                run,
                self.returned(step, "failed", code=1, blockers=[self.blocker("failed:acceptance")]),
            )[0],
        )
        self.assertEqual("blocked", self.checkpoint(run)["steps"]["step0"]["status"])
        run = self.init2()
        step = self.start(run)
        huge = self.returned(step, "blocked", blockers=[self.blocker("x")])
        huge["notes"] = [{"type": "verification_limit", "message": "x" * 9000}]
        self.assertEqual(3, self.record(run, huge)[0])
        self.assertEqual("oversized", self.checkpoint(run)["steps"]["step0"]["status"])

    def start_after_ready(self, run):
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                "step0",
                "--to",
                "in_progress",
            )[0],
        )
        return self.checkpoint(run)["steps"]["step0"]

    def test_summary_truncation_and_step_detail(self):
        run = self.init2(count=40)
        code, shown = self.call(*self.common, "show", "--run-id", run)
        self.assertEqual(0, code)
        self.assertLessEqual(shown["summary_proxy_tokens"], 1200)
        self.assertIn("omitted_count", shown)
        code, detail = self.call(*self.common, "show", "--run-id", run, "--step-id", "step0")
        self.assertEqual(0, code)
        self.assertEqual("step0", detail["step"]["id"])

    def test_repeated_noncompleted_fingerprint_stops_progress(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "failed", code=1, blockers=[self.blocker("failed:acceptance")])
        self.assertEqual(0, self.record(run, value)[0])
        failed_state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(0, self.retry(run, self.remediation(failed_state))[0])
        step = self.start_after_ready(run)
        value["attempt_id"] = step["attempt_id"]
        value["agent_id"] = step["agent_id"]
        self.assertEqual(0, self.record(run, value)[0])
        state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual("blocked", state["status"])
        self.assertEqual("blocked:no_progress", state["reason"])
        self.assertFalse(state["retry_allowed"])

    def test_reassignment_increments_once_and_requires_retry_remediation(self):
        run = self.init2()
        step = self.start(run)
        self.assertEqual(
            0,
            self.record(
                run,
                self.returned(step, "failed", code=1, blockers=[self.blocker("failed:acceptance")]),
            )[0],
        )
        self.assertEqual(
            3,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                "step0",
                "--to",
                "ready",
                "--agent-id",
                "second",
            )[0],
        )
        failed_state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(
            0,
            self.retry(
                run,
                self.remediation(failed_state, next_agent_id="second"),
                agent_id="second",
            )[0],
        )
        state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(2, state["attempt_count"])
        self.assertNotEqual(step["attempt_id"], state["attempt_id"])

    def test_return_status_and_field_invariants(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "completed", changed=["src/a"])
        value["commit_hash"] = ""
        self.assertEqual(3, self.record(run, value)[0])
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "failed", code=None, blockers=[self.blocker()])
        self.assertEqual(0, self.record(run, value)[0])
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "blocked", blockers=[])
        self.assertEqual(3, self.record(run, value)[0])
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, changed=["other/file"])
        self.assertEqual(3, self.record(run, value)[0])
        self.assertEqual("oversized", self.checkpoint(run)["steps"]["step0"]["status"])

    def test_return_evidence_digest_notes_and_bounded_arrays(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step)
        value["acceptance"]["evidence_path"] = "evidence/x.json"
        self.assertEqual(3, self.record(run, value)[0])
        value = self.returned(step)
        value["notes"] = [{"type": "not-enum", "message": "x"}]
        self.assertEqual(3, self.record(run, value)[0])
        value = self.returned(step)
        value["changed_paths"] = [f"src/{n}" for n in range(33)]
        self.assertEqual(3, self.record(run, value)[0])

    def test_valid_oversized_and_blocker_evidence_contract(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(
            step, "oversized", blockers=[self.blocker("scope", "outside")], remainder=["step1"]
        )
        self.assertEqual(0, self.record(run, value)[0])
        self.assertEqual("oversized", self.checkpoint(run)["steps"]["step0"]["status"])
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "oversized", blockers=[self.blocker()], remainder=[])
        self.assertEqual(3, self.record(run, value)[0])
        run = self.init2()
        step = self.start(run)
        value = self.returned(
            step,
            "blocked",
            blockers=[{"code": "x", "summary": "y", "evidence_path": "../bad", "sha256": "a" * 64}],
        )
        self.assertEqual(3, self.record(run, value)[0])

    def test_completed_without_changes_does_not_need_commit(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step, "completed")
        self.assertEqual("", value["commit_hash"])
        self.assertEqual(0, self.record(run, value)[0])

    def test_v2_tracks_returned_integrated_and_cleaned_commits(self):
        run = self.init2()
        step = self.start(run)
        returned = self.returned(step, changed=["src/file.py"])
        self.assertEqual(0, self.record(run, returned)[0])
        step = self.checkpoint(run)["steps"]["step0"]
        integrated = self.worktree_result(step)
        self.assertEqual(0, self.transition_result(run, "step0", "integrated", integrated)[0])
        cleaned = {**integrated, "action": "cleanup"}
        self.assertEqual(0, self.transition_result(run, "step0", "cleaned", cleaned)[0])

        state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(returned["commit_hash"], state["returned_commit"])
        self.assertEqual(integrated["rebased_commit"], state["integrated_commit"])
        self.assertEqual("cleaned", state["status"])
        self.assertTrue(state["integration_result_sha256"])
        self.assertTrue(state["cleanup_result_sha256"])

    def test_dependency_waits_for_cleanup_and_closeout_requires_cleaned(self):
        plan = self.plan()
        data = json.loads(plan.read_text())
        data["leaves"][1]["dependencies"] = ["step0"]
        plan.write_text(json.dumps(data))
        run = self.init2(plan_path=plan)
        step = self.start(run)
        self.assertEqual(0, self.record(run, self.returned(step))[0])
        step = self.checkpoint(run)["steps"]["step0"]
        integrated = self.worktree_result(step)

        self.assertEqual(3, self.call(*self.common, "validate", "--run-id", run, "--closeout")[0])
        self.assertEqual(0, self.transition_result(run, "step0", "integrated", integrated)[0])
        self.assertEqual(
            3,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                "step1",
                "--to",
                "ready",
                "--agent-id",
                "dependent",
            )[0],
        )
        self.assertEqual(
            0,
            self.transition_result(run, "step0", "cleaned", {**integrated, "action": "cleanup"})[0],
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--step-id",
                "step1",
                "--to",
                "ready",
                "--agent-id",
                "dependent",
            )[0],
        )

    def test_cleanup_failure_is_retryable_without_state_change(self):
        run = self.init2()
        step = self.start(run)
        self.assertEqual(0, self.record(run, self.returned(step))[0])
        step = self.checkpoint(run)["steps"]["step0"]
        integrated = self.worktree_result(step)
        self.assertEqual(0, self.transition_result(run, "step0", "integrated", integrated)[0])
        failure = {**integrated, "ok": False, "action": "cleanup", "error": "still dirty"}
        self.assertEqual(3, self.transition_result(run, "step0", "cleaned", failure)[0])
        self.assertEqual("integrated", self.checkpoint(run)["steps"]["step0"]["status"])
        success = {**integrated, "action": "cleanup"}
        self.assertEqual(0, self.transition_result(run, "step0", "cleaned", success)[0])

    def test_older_v2_checkpoint_backfills_closeout_fields_but_v1_is_unchanged(self):
        run = self.init2()
        checkpoint_path = self.root / "planning-policy/ledgers/plan" / run / "checkpoint.json"
        checkpoint = json.loads(checkpoint_path.read_text())
        for step in checkpoint["steps"].values():
            for field in (
                "returned_commit",
                "integrated_commit",
                "integration_result_path",
                "integration_result_sha256",
                "cleanup_result_path",
                "cleanup_result_sha256",
            ):
                step.pop(field, None)
        checkpoint_path.write_text(json.dumps(checkpoint))
        code, shown = self.call(*self.common, "show", "--run-id", run, "--step-id", "step0")
        self.assertEqual(0, code)
        self.assertEqual("", shown["step"]["returned_commit"])
        self.assertEqual("", shown["step"]["integrated_commit"])

        legacy_common = ["--ledger-root", str(self.root), "--plan-id", "legacy"]
        self.assertEqual(
            0,
            self.call(
                *legacy_common, "init", "--actor", "parent", "--approved", "--steps-json", self.v1()
            )[0],
        )
        legacy_path = self.root / "planning-policy/ledgers/legacy/checkpoint.json"
        legacy = json.loads(legacy_path.read_text())
        self.assertTrue(all("cleaned" not in step for step in legacy["steps"].values()))

    def test_record_return_refuses_omitted_run_and_persists_copy_digest(self):
        run = self.init2()
        step = self.start(run)
        value = self.returned(step)
        path = self.root / "return.json"
        path.write_text(json.dumps(value))
        self.assertEqual(
            3,
            self.call(
                *self.common, "record-return", "--actor", "parent", "--return-file", str(path)
            )[0],
        )
        self.assertEqual(
            0,
            self.call(
                *self.common,
                "record-return",
                "--actor",
                "parent",
                "--run-id",
                run,
                "--return-file",
                str(path),
            )[0],
        )
        self.assertEqual(
            ledger.digest(value), self.checkpoint(run)["steps"]["step0"]["return_sha256"]
        )

    def test_step_detail_is_bounded(self):
        run = self.init2()
        step = self.start(run)
        blockers = [
            {
                "code": f"blocked:{index}",
                "summary": "x " * 120,
                "evidence_path": f"evidence/{index}.json",
                "sha256": f"{index:x}" * 64,
            }
            for index in range(8)
        ]
        self.assertEqual(
            0,
            self.record(run, self.returned(step, "blocked", code=None, blockers=blockers))[0],
        )
        code, detail = self.call(*self.common, "show", "--run-id", run, "--step-id", "step0")
        self.assertEqual(0, code)
        self.assertLessEqual(detail["summary_proxy_tokens"], 1200)
        self.assertGreater(detail["omitted_blockers"], 0)

    def test_validate_unknown_run_and_cross_run_return(self):
        one, two = self.init2(), self.init2()
        step = self.start(one)
        self.assertEqual(
            3,
            self.call(*self.common, "validate", "--run-id", "00000000-0000-4000-8000-000000000000")[
                0
            ],
        )
        self.assertEqual(3, self.record(two, self.returned(step))[0])

    def test_uuid_collision_refuses_second_init_v2(self):
        fixed = ledger.uuid.UUID("12345678-1234-4234-8234-123456789abc")
        with patch.object(ledger.uuid, "uuid4", return_value=fixed):
            self.init2()
            code, _ = self.call(
                *self.common,
                "init-v2",
                "--actor",
                "parent",
                "--approved",
                "--plan-file",
                str(self.plan()),
                "--assignments-file",
                str(self.assignments()),
            )
        self.assertEqual(3, code)

    def test_changed_progress_allows_retry_before_numeric_limit(self):
        run = self.init2(max_attempts=3)
        first = self.start(run)
        self.assertEqual(
            0,
            self.record(
                run,
                self.returned(
                    first,
                    "failed",
                    code=1,
                    blockers=[self.blocker("failed:acceptance", "first")],
                ),
            )[0],
        )
        first_state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(0, self.retry(run, self.remediation(first_state))[0])
        second = self.start_after_ready(run)
        changed = self.returned(
            second,
            "failed",
            code=1,
            blockers=[
                {
                    "code": "failed:acceptance",
                    "summary": "second",
                    "evidence_path": "evidence/two.json",
                    "sha256": "b" * 64,
                }
            ],
        )
        self.assertEqual(0, self.record(run, changed)[0])
        self.assertTrue(self.checkpoint(run)["steps"]["step0"]["retry_allowed"])

    def test_numeric_exhaustion_uses_typed_retry_exhausted_blocker(self):
        run = self.init2(max_attempts=2)
        first = self.start(run)
        self.assertEqual(
            0,
            self.record(
                run,
                self.returned(
                    first,
                    "failed",
                    code=1,
                    blockers=[self.blocker("failed:acceptance", "first")],
                ),
            )[0],
        )
        first_state = self.checkpoint(run)["steps"]["step0"]
        self.assertEqual(0, self.retry(run, self.remediation(first_state))[0])
        second = self.start_after_ready(run)
        self.assertEqual(
            0,
            self.record(
                run,
                self.returned(
                    second,
                    "failed",
                    code=1,
                    blockers=[self.blocker("failed:acceptance", "second")],
                ),
            )[0],
        )
        state = self.checkpoint(run)["steps"]["step0"]
        self.assertFalse(state["retry_allowed"])
        self.assertEqual("blocked:retry_exhausted", state["blockers"][0]["code"])


if __name__ == "__main__":
    unittest.main()
