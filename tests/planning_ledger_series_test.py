import contextlib
import hashlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).parents[1]
    / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py"
)
SPEC = importlib.util.spec_from_file_location("planning_ledger_series", SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(ledger)


class PlanningLedgerSeriesTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def common(self, plan_id="plan"):
        return ["--ledger-root", str(self.root), "--plan-id", plan_id]

    def call(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = ledger.main(arguments)
        return code, json.loads(stream.getvalue())

    def plan(self, plan_id="plan", count=1, series=None):
        path = self.root / f"{plan_id}-plan.json"
        leaves = []
        for number in range(count):
            step_id = f"step{number}"
            leaves.append(
                {
                    "id": step_id,
                    "dependencies": [],
                    "task": "task",
                    "boundary": "boundary",
                    "read_set": ["src"],
                    "write_set": ["src"],
                    "settled_decisions": "settled",
                    "size": "small",
                    "portable_tier": "standard",
                    "worktree_owner": "owner",
                    "acceptance_command": "uv run test",
                    "return_contract": "bounded-step-return-v1",
                    "stop_conditions": ["missing_load_bearing_information"],
                    "work_unit_id": step_id,
                    "max_attempts": 2,
                    "capability_requirements": {
                        "baseline": "plan-step-base-v1",
                        "additional": [],
                    },
                }
            )
        plan = {
            "contract_version": 4,
            "objective": "objective",
            "scope_summary": "scope",
            "approved_decisions": ["settled"],
            "leaves": leaves,
            "work_units": [
                {"id": f"step{number}", "original_size": "small"} for number in range(count)
            ],
        }
        if series is not None:
            plan["series"] = series
        path.write_text(json.dumps(plan))
        return path

    def capability_binding(self, plan_path):
        plan = json.loads(Path(plan_path).read_text())
        plan_sha256 = hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        path = self.root / f"{plan_path.stem}-capability-binding.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "planning-capability-binding-v1",
                    "plan_sha256": plan_sha256,
                    "bindings": [
                        {
                            "step_id": leaf["id"],
                            "host": "codex",
                            "executor": "gpt-5.6-terra",
                            "requirements": leaf["capability_requirements"],
                            "evidence": ["test fixture capability inventory"],
                        }
                        for leaf in plan["leaves"]
                    ],
                }
            )
        )
        return path

    def assignments(self, plan_id="plan", count=1):
        path = self.root / f"{plan_id}-assignments.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "id": f"step{number}",
                        "harness": "codex",
                        "model_or_alias": "gpt-5.6-terra",
                        "effort": "medium",
                        "worktree": f".worktrees/{plan_id}-{number}",
                    }
                    for number in range(count)
                ]
            )
        )
        return path

    def init4(self, plan_id="plan", count=1, series=None):
        selected_plan = self.plan(plan_id, count, series)
        code, result = self.call(
            *self.common(plan_id),
            "init-v4",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(selected_plan),
            "--assignments-file",
            str(self.assignments(plan_id, count)),
            "--capability-binding-file",
            str(self.capability_binding(selected_plan)),
        )
        self.assertEqual(0, code, result)
        return result["run_id"]

    def checkpoint_path(self, plan_id, run_id):
        return self.root / "planning-policy/ledgers" / plan_id / run_id / "checkpoint.json"

    def checkpoint(self, plan_id, run_id):
        return json.loads(self.checkpoint_path(plan_id, run_id).read_text())

    def run_dir(self, plan_id, run_id):
        return self.root / "planning-policy/ledgers" / plan_id / run_id

    def default_series(self):
        return {
            "series_id": "plan-series",
            "slice": 1,
            "final": False,
            "end_verification_commands": ["uv run python -m unittest tests.example"],
        }

    def handoff(self, plan_id, run_id, series_id="plan-series", slice_number=1, **overrides):
        value = {
            "schema": "planning-series-handoff-v1",
            "plan_id": plan_id,
            "run_id": run_id,
            "series_id": series_id,
            "slice": slice_number,
            "landed": ["shipped feature A"],
            "decisions": ["chose approach X"],
            "assumptions_to_revalidate": ["upstream API stays stable"],
            "remaining_scope": ["slice 2 continues cleanup"],
        }
        value.update(overrides)
        return value

    def stamp(self, plan_id, run_id, handoff_value):
        directory = self.run_dir(plan_id, run_id)
        artifact_path = directory / "series-handoff.json"
        artifact_path.write_text(json.dumps(handoff_value))
        checkpoint = self.checkpoint(plan_id, run_id)
        checkpoint["series_handoff_path"] = "series-handoff.json"
        checkpoint["series_handoff_sha256"] = ledger.digest(handoff_value)
        checkpoint["event_sequence"] += 1
        checkpoint["updated_at"] = ledger.now()
        (directory / "checkpoint.json").write_text(
            json.dumps(checkpoint, sort_keys=True, separators=(",", ":")) + "\n"
        )

    def show(self, plan_id, run_id):
        return self.call(*self.common(plan_id), "show", "--run-id", run_id)

    # -- plumbing coverage --------------------------------------------------

    def test_series_handoff_round_trips_through_show(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("plan", run_id))
        code, result = self.show("plan", run_id)
        self.assertEqual(0, code, result)

    def test_plain_non_series_run_has_no_series_keys_in_checkpoint(self):
        run_id = self.init4(series=None)
        checkpoint = self.checkpoint("plan", run_id)
        self.assertNotIn("series_handoff_path", checkpoint)
        self.assertNotIn("series_handoff_sha256", checkpoint)
        code, result = self.show("plan", run_id)
        self.assertEqual(0, code, result)

    def test_rejects_artifact_edited_after_stamping(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("plan", run_id))
        artifact = self.run_dir("plan", run_id) / "series-handoff.json"
        tampered = self.handoff("plan", run_id, landed=["tampered"])
        artifact.write_text(json.dumps(tampered))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_stamp_without_file(self):
        run_id = self.init4(series=self.default_series())
        directory = self.run_dir("plan", run_id)
        checkpoint = self.checkpoint("plan", run_id)
        checkpoint["series_handoff_path"] = "series-handoff.json"
        checkpoint["series_handoff_sha256"] = "a" * 64
        (directory / "checkpoint.json").write_text(
            json.dumps(checkpoint, sort_keys=True, separators=(",", ":")) + "\n"
        )
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_file_without_stamp(self):
        run_id = self.init4(series=self.default_series())
        directory = self.run_dir("plan", run_id)
        (directory / "series-handoff.json").write_text(
            json.dumps(self.handoff("plan", run_id))
        )
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_artifact_on_non_series_run(self):
        run_id = self.init4(series=None)
        self.stamp("plan", run_id, self.handoff("plan", run_id))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_identity_mismatch_slice(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("plan", run_id, slice_number=2))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_identity_mismatch_series_id(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("plan", run_id, series_id="other-series"))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_identity_mismatch_run_id(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("plan", "11111111-1111-4111-8111-111111111111"))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_identity_mismatch_plan_id(self):
        run_id = self.init4(series=self.default_series())
        self.stamp("plan", run_id, self.handoff("other-plan", run_id))
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_oversized_artifact(self):
        run_id = self.init4(series=self.default_series())
        oversized = self.handoff(
            "plan",
            run_id,
            landed=["x" * 480] * 16,
            decisions=["x" * 480] * 16,
            assumptions_to_revalidate=["x" * 480] * 16,
            remaining_scope=["x" * 480] * 16,
        )
        self.assertGreater(len(ledger.canon(oversized)), ledger.MAX_SERIES_HANDOFF)
        self.stamp("plan", run_id, oversized)
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_malformed_schema_unknown_key(self):
        run_id = self.init4(series=self.default_series())
        malformed = self.handoff("plan", run_id)
        malformed["extra"] = "nope"
        self.stamp("plan", run_id, malformed)
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_malformed_schema_overlong_string(self):
        run_id = self.init4(series=self.default_series())
        malformed = self.handoff("plan", run_id, landed=["x" * 481])
        self.stamp("plan", run_id, malformed)
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    def test_rejects_malformed_schema_over_sixteen_entries(self):
        run_id = self.init4(series=self.default_series())
        malformed = self.handoff("plan", run_id, decisions=["entry"] * 17)
        self.stamp("plan", run_id, malformed)
        code, result = self.show("plan", run_id)
        self.assertNotEqual(0, code, result)

    # -- close-path helpers -------------------------------------------------

    def final_series(self):
        return {**self.default_series(), "final": True}

    def content(self, **overrides):
        value = {
            "landed": ["slice 1 shipped the close path"],
            "decisions": ["identity is composed by the ledger"],
            "assumptions_to_revalidate": ["event replay stays tolerant"],
            "remaining_scope": ["slice 2 wires the successor"],
        }
        value.update(overrides)
        return value

    def content_file(self, name, value):
        # Canonical bytes, so a size boundary is decided by the payload rather
        # than by incidental separator whitespace.
        path = self.root / f"{name}-content.json"
        path.write_bytes(ledger.canon(value))
        return str(path)

    def close(self, plan_id, run_id, outcome, handoff_file=None, reason="reason"):
        arguments = [
            *self.common(plan_id),
            "close",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--outcome",
            outcome,
            "--reason",
            reason,
        ]
        if handoff_file is not None:
            arguments += ["--series-handoff-file", handoff_file]
        return self.call(*arguments)

    def reopen(self, plan_id, run_id, reason="more work"):
        return self.call(
            *self.common(plan_id),
            "reopen",
            "--actor",
            "parent",
            "--run-id",
            run_id,
            "--reason",
            reason,
        )

    def validate(self, plan_id, run_id):
        return self.call(*self.common(plan_id), "validate", "--run-id", run_id)

    def artifact_path(self, plan_id, run_id):
        return self.run_dir(plan_id, run_id) / "series-handoff.json"

    def events(self, plan_id, run_id):
        path = self.run_dir(plan_id, run_id) / "events.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()]

    def snapshot(self, plan_id, run_id):
        """Every byte a close could mutate: checkpoint, event log, artifact."""
        directory = self.run_dir(plan_id, run_id)
        artifact = directory / "series-handoff.json"
        return (
            (directory / "checkpoint.json").read_bytes(),
            (directory / "events.jsonl").read_bytes(),
            artifact.read_bytes() if artifact.exists() else None,
        )

    def assert_rejected_intact(self, plan_id, run_id, before, code, result):
        """A refused close changes nothing and leaves the run loadable/active."""
        self.assertNotEqual(0, code, result)
        self.assertEqual(before, self.snapshot(plan_id, run_id))
        self.assertEqual("active", self.checkpoint(plan_id, run_id)["run_status"])
        self.assertEqual(0, self.show(plan_id, run_id)[0])
        self.assertEqual(0, self.validate(plan_id, run_id)[0])

    def drive_to_cleaned(self, plan_id, run_id, step_id="step0"):
        for target in ("ready", "in_progress"):
            arguments = [
                *self.common(plan_id),
                "transition",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--step-id",
                step_id,
                "--to",
                target,
            ]
            if target == "ready":
                arguments += ["--agent-id", f"agent-{step_id}"]
            self.assertEqual(0, self.call(*arguments)[0])
        step = self.checkpoint(plan_id, run_id)["steps"][step_id]
        returned = {
            "schema": "bounded-step-return-v1",
            "step_id": step_id,
            "attempt_id": step["attempt_id"],
            "agent_id": step["agent_id"],
            "status": "completed",
            "changed_paths": [],
            "acceptance": {"command": "uv run test", "exit_code": 0, "summary": "ok"},
            "blockers": [],
            "notes": [],
            "unstarted_remainder": [],
            "commit_hash": "",
        }
        return_path = self.root / f"{plan_id}-{step_id}-return.json"
        return_path.write_text(json.dumps(returned))
        self.assertEqual(
            0,
            self.call(
                *self.common(plan_id),
                "record-return",
                "--actor",
                "parent",
                "--run-id",
                run_id,
                "--return-file",
                str(return_path),
            )[0],
        )
        integrated = "b" * 40
        for target, action in (("integrated", "integrate"), ("cleaned", "cleanup")):
            value = {
                "schema": "planning-worktree-result-v1",
                "ok": True,
                "action": action,
                "repo_root": str(self.root),
                "target": "main",
                "branch": "owner",
                "worktree": str(self.root / f".worktrees/{plan_id}-0"),
                "source_commit": "a" * 40,
                "rebased_commit": integrated,
                "parent_before": "c" * 40,
                "parent_after": integrated,
            }
            if action == "cleanup":
                value["parent_commit"] = integrated
            path = self.root / f"{plan_id}-{step_id}-{action}.json"
            path.write_text(json.dumps(value))
            self.assertEqual(
                0,
                self.call(
                    *self.common(plan_id),
                    "transition",
                    "--actor",
                    "parent",
                    "--run-id",
                    run_id,
                    "--step-id",
                    step_id,
                    "--to",
                    target,
                    "--worktree-result",
                    str(path),
                )[0],
            )

    # -- close reject matrix ------------------------------------------------

    def test_completed_close_without_flag_names_the_missing_flag(self):
        run_id = self.init4(series=self.default_series())
        self.drive_to_cleaned("plan", run_id)
        before = self.snapshot("plan", run_id)
        code, result = self.close("plan", run_id, "completed")
        self.assert_rejected_intact("plan", run_id, before, code, result)
        self.assertIn("--series-handoff-file", json.dumps(result))
        # The run is still closable once the operator supplies the handoff.
        accepted = self.close(
            "plan", run_id, "completed", self.content_file("late", self.content())
        )
        self.assertEqual(0, accepted[0], accepted[1])

    def test_flag_on_a_non_series_run_is_rejected(self):
        run_id = self.init4(series=None)
        before = self.snapshot("plan", run_id)
        code, result = self.close(
            "plan", run_id, "blocked", self.content_file("stray", self.content())
        )
        self.assert_rejected_intact("plan", run_id, before, code, result)
        self.assertIsNone(self.snapshot("plan", run_id)[2])
        self.assertEqual(0, self.close("plan", run_id, "blocked")[0])

    def test_flag_on_a_final_slice_is_rejected(self):
        run_id = self.init4(series=self.final_series())
        before = self.snapshot("plan", run_id)
        code, result = self.close(
            "plan", run_id, "blocked", self.content_file("final", self.content())
        )
        self.assert_rejected_intact("plan", run_id, before, code, result)
        self.assertEqual(0, self.close("plan", run_id, "blocked")[0])

    def test_final_slice_completes_without_a_handoff(self):
        run_id = self.init4(series=self.final_series())
        self.drive_to_cleaned("plan", run_id)
        code, result = self.close("plan", run_id, "completed")
        self.assertEqual(0, code, result)
        self.assertFalse(self.artifact_path("plan", run_id).exists())

    def test_blocked_and_abandoned_treat_the_flag_as_optional(self):
        for outcome in ("blocked", "abandoned"):
            with self.subTest(outcome=outcome, flag=False):
                run_id = self.init4(plan_id=f"bare-{outcome}", series=self.default_series())
                code, result = self.close(f"bare-{outcome}", run_id, outcome)
                self.assertEqual(0, code, result)
                self.assertFalse(self.artifact_path(f"bare-{outcome}", run_id).exists())
            with self.subTest(outcome=outcome, flag=True):
                plan_id = f"flagged-{outcome}"
                run_id = self.init4(plan_id=plan_id, series=self.default_series())
                code, result = self.close(
                    plan_id,
                    run_id,
                    outcome,
                    self.content_file(plan_id, self.content()),
                )
                self.assertEqual(0, code, result)
                self.assertTrue(self.artifact_path(plan_id, run_id).exists())
                self.assertEqual(0, self.show(plan_id, run_id)[0])

    def test_missing_content_file_leaves_the_run_active(self):
        run_id = self.init4(series=self.default_series())
        before = self.snapshot("plan", run_id)
        code, result = self.close(
            "plan", run_id, "blocked", str(self.root / "absent-content.json")
        )
        self.assert_rejected_intact("plan", run_id, before, code, result)

    def test_unparseable_content_file_leaves_the_run_active(self):
        run_id = self.init4(series=self.default_series())
        path = self.root / "broken-content.json"
        path.write_text("{not json")
        before = self.snapshot("plan", run_id)
        code, result = self.close("plan", run_id, "blocked", str(path))
        self.assert_rejected_intact("plan", run_id, before, code, result)

    def test_content_file_cannot_supply_identity(self):
        run_id = self.init4(series=self.default_series())
        for extra in ("plan_id", "run_id", "series_id", "slice", "schema"):
            with self.subTest(field=extra):
                payload = self.content()
                payload[extra] = "smuggled" if extra != "slice" else 9
                before = self.snapshot("plan", run_id)
                code, result = self.close(
                    "plan", run_id, "blocked", self.content_file(f"id-{extra}", payload)
                )
                self.assert_rejected_intact("plan", run_id, before, code, result)

    def test_content_file_missing_a_content_field_is_rejected(self):
        run_id = self.init4(series=self.default_series())
        payload = self.content()
        payload.pop("remaining_scope")
        before = self.snapshot("plan", run_id)
        code, result = self.close(
            "plan", run_id, "blocked", self.content_file("short", payload)
        )
        self.assert_rejected_intact("plan", run_id, before, code, result)

    def test_oversized_content_file_leaves_the_run_active(self):
        run_id = self.init4(series=self.default_series())
        payload = self.content(
            **{field: ["x" * 480] * 16 for field in ledger.SERIES_HANDOFF_LIST_FIELDS}
        )
        self.assertGreater(len(ledger.canon(payload)), ledger.MAX_SERIES_HANDOFF)
        before = self.snapshot("plan", run_id)
        code, result = self.close(
            "plan", run_id, "blocked", self.content_file("oversized", payload)
        )
        self.assert_rejected_intact("plan", run_id, before, code, result)
        self.assertIn("content file exceeds", result["error"])

    def test_content_under_the_cap_whose_composed_artifact_exceeds_it_is_rejected(self):
        run_id = self.init4(series=self.default_series())
        payload = self.content(landed=["x" * 480] * 16, decisions=[])
        for length in range(1, 481):
            candidate = dict(payload, decisions=["x" * length])
            if len(ledger.canon(candidate)) > ledger.MAX_SERIES_HANDOFF:
                break
            payload = candidate
        self.assertLessEqual(len(ledger.canon(payload)), ledger.MAX_SERIES_HANDOFF)
        full = {
            "schema": "planning-series-handoff-v1",
            "plan_id": "plan",
            "run_id": run_id,
            "series_id": "plan-series",
            "slice": 1,
            **payload,
        }
        self.assertGreater(len(ledger.canon(full)), ledger.MAX_SERIES_HANDOFF)
        before = self.snapshot("plan", run_id)
        code, result = self.close(
            "plan", run_id, "blocked", self.content_file("near-cap", payload)
        )
        self.assert_rejected_intact("plan", run_id, before, code, result)
        # The composed artifact is what the cap governs, not the supplied file.
        self.assertIn("planning-series-handoff-v1 exceeds", result["error"])

    # -- accepted close path ------------------------------------------------

    def test_accepted_close_writes_artifact_stamp_and_event_digest(self):
        run_id = self.init4(series=self.default_series())
        self.drive_to_cleaned("plan", run_id)
        code, result = self.close(
            "plan", run_id, "completed", self.content_file("ok", self.content())
        )
        self.assertEqual(0, code, result)
        artifact = json.loads(self.artifact_path("plan", run_id).read_text())
        checkpoint = self.checkpoint("plan", run_id)
        self.assertEqual("series-handoff.json", checkpoint["series_handoff_path"])
        self.assertEqual(ledger.digest(artifact), checkpoint["series_handoff_sha256"])
        self.assertEqual(self.content(), {k: artifact[k] for k in self.content()})
        closes = [e for e in self.events("plan", run_id) if e["action"] == "close-v4"]
        self.assertEqual(1, len(closes))
        self.assertEqual(checkpoint["series_handoff_sha256"], closes[0]["series_handoff_sha256"])
        self.assertEqual("plan-series", closes[0]["series_id"])
        self.assertEqual(1, closes[0]["series_slice"])
        self.assertEqual(0, self.show("plan", run_id)[0])
        self.assertEqual(0, self.validate("plan", run_id)[0])

    def successor_series(self, slice_number=3):
        return {
            **self.default_series(),
            "slice": slice_number,
            "predecessor": {
                "plan_id": "plan",
                "plan_sha256": "a" * 64,
                "run_id": "11111111-1111-4111-8111-111111111111",
                "outcome": "completed",
                "handoff_sha256": "b" * 64,
            },
        }

    def test_identity_is_composed_from_the_closing_run(self):
        run_id = self.init4(series=self.successor_series())
        code, result = self.close(
            "plan", run_id, "blocked", self.content_file("identity", self.content())
        )
        self.assertEqual(0, code, result)
        artifact = json.loads(self.artifact_path("plan", run_id).read_text())
        self.assertEqual("planning-series-handoff-v1", artifact["schema"])
        self.assertEqual("plan", artifact["plan_id"])
        self.assertEqual(run_id, artifact["run_id"])
        self.assertEqual("plan-series", artifact["series_id"])
        self.assertEqual(3, artifact["slice"])

    # -- reopen and supersede ----------------------------------------------

    def test_reopen_retains_the_artifact_and_reclose_supersedes_with_lineage(self):
        run_id = self.init4(series=self.default_series())
        first = self.content(landed=["first close"])
        self.assertEqual(
            0, self.close("plan", run_id, "blocked", self.content_file("first", first))[0]
        )
        original = self.snapshot("plan", run_id)[2]
        first_digest = self.checkpoint("plan", run_id)["series_handoff_sha256"]

        self.assertEqual(0, self.reopen("plan", run_id)[0])
        retained = self.checkpoint("plan", run_id)
        self.assertEqual("active", retained["run_status"])
        self.assertEqual(original, self.snapshot("plan", run_id)[2])
        self.assertEqual(first_digest, retained["series_handoff_sha256"])
        self.assertEqual("series-handoff.json", retained["series_handoff_path"])
        self.assertEqual(0, self.show("plan", run_id)[0])

        second = self.content(landed=["second close supersedes"])
        self.assertEqual(
            0, self.close("plan", run_id, "blocked", self.content_file("second", second))[0]
        )
        artifact = json.loads(self.artifact_path("plan", run_id).read_text())
        self.assertEqual(["second close supersedes"], artifact["landed"])
        second_digest = self.checkpoint("plan", run_id)["series_handoff_sha256"]
        self.assertNotEqual(first_digest, second_digest)
        self.assertEqual(ledger.digest(artifact), second_digest)

        digests = [
            e["series_handoff_sha256"]
            for e in self.events("plan", run_id)
            if e["action"] == "close-v4"
        ]
        self.assertEqual([first_digest, second_digest], digests)
        self.assertEqual(0, self.validate("plan", run_id)[0])
        self.assertEqual(0, self.show("plan", run_id)[0])

    def test_reclose_after_reopen_still_requires_the_flag(self):
        run_id = self.init4(series=self.default_series())
        self.assertEqual(
            0, self.close("plan", run_id, "blocked", self.content_file("one", self.content()))[0]
        )
        self.assertEqual(0, self.reopen("plan", run_id)[0])
        self.drive_to_cleaned("plan", run_id)
        before = self.snapshot("plan", run_id)
        code, result = self.close("plan", run_id, "completed")
        self.assert_rejected_intact("plan", run_id, before, code, result)
        self.assertIn("--series-handoff-file", json.dumps(result))

    # -- init-v4 predecessor cross-check ------------------------------------

    def init4_full(self, plan_id="plan", count=1, series=None):
        """Like `init4`, but returns the full result instead of just run_id."""
        selected_plan = self.plan(plan_id, count, series)
        return self.call(
            *self.common(plan_id),
            "init-v4",
            "--actor",
            "parent",
            "--approved",
            "--plan-file",
            str(selected_plan),
            "--assignments-file",
            str(self.assignments(plan_id, count)),
            "--capability-binding-file",
            str(self.capability_binding(selected_plan)),
        )

    def build_predecessor(self, plan_id="pred", outcome="completed", **series_overrides):
        """Init, drive, and close a real predecessor run, returning its digests."""
        series = {**self.default_series(), **series_overrides}
        run_id = self.init4(plan_id=plan_id, series=series)
        if outcome == "completed":
            self.drive_to_cleaned(plan_id, run_id)
        code, close_result = self.close(
            plan_id, run_id, outcome, self.content_file(f"{plan_id}-handoff", self.content())
        )
        self.assertEqual(0, code, close_result)
        checkpoint = self.checkpoint(plan_id, run_id)
        return {
            "plan_id": plan_id,
            "plan_sha256": checkpoint["plan_hash"],
            "run_id": run_id,
            "outcome": checkpoint["outcome"],
            "handoff_sha256": checkpoint["series_handoff_sha256"],
        }

    def successor_series_from(self, predecessor, slice_number=2, **predecessor_overrides):
        return {
            **self.default_series(),
            "slice": slice_number,
            "predecessor": {**predecessor, **predecessor_overrides},
        }

    def test_predecessor_matched_disclosure(self):
        predecessor = self.build_predecessor()
        code, result = self.init4_full(
            "succ", series=self.successor_series_from(predecessor)
        )
        self.assertEqual(0, code, result)
        self.assertEqual("matched", result["series_predecessor"])

    def test_predecessor_plan_digest_drift_is_mismatch(self):
        predecessor = self.build_predecessor()
        series = self.successor_series_from(predecessor, plan_sha256="c" * 64)
        code, result = self.init4_full("succ", series=series)
        self.assertEqual(0, code, result)
        self.assertEqual("mismatch:plan_digest", result["series_predecessor"])

    def test_predecessor_outcome_drift_is_mismatch(self):
        predecessor = self.build_predecessor()
        series = self.successor_series_from(predecessor, outcome="blocked")
        code, result = self.init4_full("succ", series=series)
        self.assertEqual(0, code, result)
        self.assertEqual("mismatch:outcome", result["series_predecessor"])

    def test_predecessor_handoff_digest_drift_is_mismatch(self):
        predecessor = self.build_predecessor()
        series = self.successor_series_from(predecessor, handoff_sha256="d" * 64)
        code, result = self.init4_full("succ", series=series)
        self.assertEqual(0, code, result)
        self.assertEqual("mismatch:handoff_digest", result["series_predecessor"])

    def test_predecessor_end_command_drift_is_mismatch(self):
        predecessor = self.build_predecessor()
        series = self.successor_series_from(predecessor)
        series["end_verification_commands"] = ["uv run python -m unittest tests.other"]
        code, result = self.init4_full("succ", series=series)
        self.assertEqual(0, code, result)
        self.assertEqual("mismatch:end_commands", result["series_predecessor"])

    def test_gcd_predecessor_is_unresolvable(self):
        predecessor = self.build_predecessor()
        shutil.rmtree(self.run_dir(predecessor["plan_id"], predecessor["run_id"]))
        code, result = self.init4_full(
            "succ", series=self.successor_series_from(predecessor)
        )
        self.assertEqual(0, code, result)
        self.assertEqual("unresolvable", result["series_predecessor"])

    def test_abandoned_predecessor_without_handoff_matches_empty_sentinel(self):
        series = self.default_series()
        run_id = self.init4(plan_id="pred-abandon", series=series)
        code, close_result = self.close("pred-abandon", run_id, "abandoned")
        self.assertEqual(0, code, close_result)
        checkpoint = self.checkpoint("pred-abandon", run_id)
        self.assertNotIn("series_handoff_sha256", checkpoint)
        predecessor = {
            "plan_id": "pred-abandon",
            "plan_sha256": checkpoint["plan_hash"],
            "run_id": run_id,
            "outcome": "abandoned",
            "handoff_sha256": "",
        }
        code, result = self.init4_full(
            "succ", series=self.successor_series_from(predecessor)
        )
        self.assertEqual(0, code, result)
        self.assertEqual("matched", result["series_predecessor"])

    def test_tampered_predecessor_checkpoint_is_unresolvable(self):
        predecessor = self.build_predecessor()
        checkpoint_path = self.checkpoint_path(predecessor["plan_id"], predecessor["run_id"])
        corrupted = self.checkpoint(predecessor["plan_id"], predecessor["run_id"])
        corrupted["plan_hash"] = "e" * 64
        checkpoint_path.write_text(
            json.dumps(corrupted, sort_keys=True, separators=(",", ":")) + "\n"
        )
        code, result = self.init4_full(
            "succ", series=self.successor_series_from(predecessor)
        )
        self.assertEqual(0, code, result)
        self.assertEqual("unresolvable", result["series_predecessor"])

    def test_non_series_init_carries_no_series_predecessor_key(self):
        code, result = self.init4_full("plain", series=None)
        self.assertEqual(0, code, result)
        self.assertNotIn("series_predecessor", result)

    def test_slice_one_init_carries_no_series_predecessor_key(self):
        code, result = self.init4_full("slice-one", series=self.default_series())
        self.assertEqual(0, code, result)
        self.assertNotIn("series_predecessor", result)


if __name__ == "__main__":
    unittest.main()
