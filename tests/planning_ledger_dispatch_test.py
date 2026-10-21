import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = (
    Path(__file__).parents[1]
    / "souroldgeezer-policy/skills/planning-policy/references/scripts"
)


def load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_dispatch", SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


ledger = load("planning_ledger")
validator = load("validate_plan_contract")


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, text=True, capture_output=True
    )


def leaf(sid, owner, dependencies=(), batch=None):
    value = {
        "id": sid,
        "dependencies": list(dependencies),
        "task": "task",
        "boundary": "boundary",
        "read_set": ["src"],
        "write_set": [f"src/{sid}"],
        "settled_decisions": "settled",
        "size": "small",
        "portable_tier": "standard",
        "worktree_owner": owner,
        "acceptance_command": "uv run test",
        "return_contract": "bounded-step-return-v1",
        "stop_conditions": ["missing_load_bearing_information"],
        "work_unit_id": "unit" if batch else sid,
        "max_attempts": 2,
        "capability_requirements": {"baseline": "plan-step-base-v1", "additional": []},
    }
    if batch:
        value["batch"] = batch
    return value


def batch_leaves():
    members = [
        leaf("first", "batch-owner", batch="group"),
        leaf("second", "batch-owner", ["first"], batch="group"),
    ]
    units = [{
        "id": "unit", "original_size": "medium", "cohesive_outcome": "One batch outcome",
        "decomposition": {"basis": "failure_isolation", "rationale": "Separate failure surfaces",
                          "shape": "checkpointed"},
    }]
    return members, units, {"first": ".worktrees/batch", "second": ".worktrees/batch"}


class DispatchHarness(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.scratch = Path(self.temporary.name)
        self.repo = self.scratch / "repo"
        git(self.scratch, "init", "-b", "main", str(self.repo))
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "user.email", "test@example.invalid")
        (self.repo / ".gitignore").write_text(".worktrees/\n")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-m", "base")

    def call(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = ledger.main(
                ["--repo-root", str(self.repo), "--plan-id", "plan", *arguments]
            )
        return code, json.loads(stream.getvalue())

    def init(self, leaves, units=None, worktrees=None, **plan_fields):
        plan = {
            "contract_version": 5,
            "objective": "objective",
            "scope_summary": "scope",
            "approved_decisions": ["settled"],
            "leaves": leaves,
            "work_units": units
            or [
                {
                    "id": item["id"],
                    "original_size": "small",
                    "cohesive_outcome": f"Complete {item['id']}",
                    "decomposition": {"shape": "single"},
                }
                for item in leaves
            ],
            **plan_fields,
        }
        plan_path = self.scratch / "plan.json"
        plan_path.write_text(json.dumps(plan))
        digest = hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        (self.scratch / "binding.json").write_text(
            json.dumps(
                {
                    "schema": "planning-capability-binding-v1",
                    "plan_sha256": digest,
                    "bindings": [
                        {
                            "step_id": item["id"],
                            "host": "claude-code",
                            "executor": "sonnet",
                            "requirements": item["capability_requirements"],
                            "evidence": ["test fixture capability inventory"],
                        }
                        for item in leaves
                    ],
                }
            )
        )
        (self.scratch / "assignments.json").write_text(
            json.dumps(
                [
                    {
                        "id": item["id"],
                        "harness": "claude-code",
                        "model_or_alias": "sonnet",
                        "effort": "medium",
                        "worktree": (worktrees or {}).get(
                            item["id"], f".worktrees/{item['id']}"
                        ),
                    }
                    for item in leaves
                ]
            )
        )
        code, result = self.call(
            "init-v5", "--actor", "parent", "--approved",
            "--plan-file", str(plan_path),
            "--assignments-file", str(self.scratch / "assignments.json"),
            "--capability-binding-file", str(self.scratch / "binding.json"),
        )
        self.assertEqual(0, code, result)
        self.run_id = result["run_id"]
        return result

    def checkpoint_path(self):
        common = Path(git(self.repo, "rev-parse", "--git-common-dir").stdout.strip())
        common = common if common.is_absolute() else self.repo / common
        return common / "planning-policy/ledgers/plan" / self.run_id / "checkpoint.json"

    def dispatch(self, step_id, *extra):
        return self.call(
            "dispatch", "--actor", "parent", "--run-id", self.run_id,
            "--step-id", step_id, "--agent-id", "worker", *extra,
        )


class DispatchCommandTest(DispatchHarness):
    def test_init_stores_absolute_worktrees_and_next_names_dispatch(self):
        result = self.init([leaf("alpha", "leaf-alpha")])
        steps = json.loads(self.checkpoint_path().read_text())["steps"]
        self.assertEqual(
            str(self.repo.resolve() / ".worktrees/alpha"), steps["alpha"]["assignment"]["worktree"]
        )
        self.assertIn(" dispatch ", result["next"]["command"])
        self.assertIn("--step-id alpha", result["next"]["command"])

    def test_create_from_builds_the_branch_worktree_and_returns_the_packet(self):
        self.init([leaf("alpha", "leaf-alpha")])
        code, result = self.dispatch("alpha", "--create-from", "main")
        self.assertEqual(0, code, result)
        self.assertEqual("in_progress", result["status"])
        (packet,) = result["handoffs"]
        self.assertEqual("planning-worker-handoff-v1", packet["schema"])
        self.assertEqual("alpha", packet["step_id"])
        self.assertEqual(str(self.repo.resolve() / ".worktrees/alpha"), packet["worktree"])
        self.assertEqual("leaf-alpha", packet["leaf"]["worktree_owner"])
        self.assertEqual(
            "leaf-alpha",
            git(self.repo / ".worktrees/alpha", "branch", "--show-current").stdout.strip(),
        )
        state = json.loads(self.checkpoint_path().read_text())["steps"]["alpha"]
        self.assertEqual("in_progress", state["status"])
        self.assertEqual(packet["attempt_id"], state["attempt_id"])
        self.assertEqual("alpha", result["next"]["await_step_id"])
        # The granular packet command agrees with the composite result.
        code, granular = self.call("handoff", "--run-id", self.run_id, "--step-id", "alpha")
        self.assertEqual(packet, granular["handoff"])

    def test_branch_mismatch_names_both_and_leaves_state_unchanged(self):
        self.init([leaf("alpha", "leaf-alpha")])
        git(self.repo, "worktree", "add", "-b", "other-branch", str(self.repo / ".worktrees/alpha"), "main")
        before = self.checkpoint_path().read_bytes()
        code, result = self.dispatch("alpha")
        self.assertEqual(3, code)
        self.assertIn("other-branch", result["error"])
        self.assertIn("leaf-alpha", result["error"])
        self.assertEqual(before, self.checkpoint_path().read_bytes())

    def test_unregistered_directory_and_absent_path_fail_unchanged(self):
        self.init([leaf("alpha", "leaf-alpha")])
        before = self.checkpoint_path().read_bytes()
        code, result = self.dispatch("alpha")
        self.assertEqual(3, code)
        self.assertIn("--create-from", result["error"])
        (self.repo / ".worktrees/alpha").mkdir(parents=True)
        code, result = self.dispatch("alpha", "--create-from", "main")
        self.assertEqual(3, code)
        self.assertIn("not a registered worktree", result["error"])
        self.assertEqual(before, self.checkpoint_path().read_bytes())

    def test_creation_failure_leaves_state_unchanged(self):
        self.init([leaf("alpha", "leaf-alpha")])
        before = self.checkpoint_path().read_bytes()
        code, result = self.dispatch("alpha", "--create-from", "no-such-target")
        self.assertEqual(3, code)
        self.assertIn("cannot create worktree", result["error"])
        self.assertEqual(before, self.checkpoint_path().read_bytes())

    def test_unmet_dependency_is_refused_before_a_worktree_is_created(self):
        self.init([leaf("alpha", "leaf-alpha"), leaf("beta", "leaf-beta", ["alpha"])])
        code, result = self.dispatch("beta", "--create-from", "main")
        self.assertEqual(3, code)
        self.assertIn("dependencies", result["error"])
        self.assertFalse((self.repo / ".worktrees/beta").exists())

    def test_batch_dispatch_starts_every_member_in_order_with_one_packet_each(self):
        self.init(*batch_leaves())
        code, result = self.dispatch("first", "--create-from", "main")
        self.assertEqual(0, code, result)
        self.assertEqual(["first", "second"], result["step_ids"])
        self.assertEqual(["first", "second"], [item["step_id"] for item in result["handoffs"]])
        self.assertEqual(2, len({item["attempt_id"] for item in result["handoffs"]}))
        steps = json.loads(self.checkpoint_path().read_text())["steps"]
        self.assertEqual({"in_progress"}, {item["status"] for item in steps.values()})

    def test_next_only_names_dispatch_for_a_pending_step(self):
        self.init([leaf("alpha", "leaf-alpha")])
        code, result = self.call("show", "--run-id", self.run_id, "--next-only")
        self.assertEqual(0, code, result)
        self.assertEqual("ready_pending", result["next"]["category"])
        self.assertIn(" dispatch ", result["next"]["command"])


class WorktreeOwnerAdmissionTest(unittest.TestCase):
    def test_branch_name_rule_accepts_names_git_accepts(self):
        for name in ("leaf", "task/leaf-1", "v1.2", "a_b"):
            self.assertTrue(validator.valid_branch_name(name), name)

    def test_branch_name_rule_rejects_names_git_rejects(self):
        for name in (
            "", "-lead", "/lead", "lead/", "a..b", "a b", "a~b", "a^b", "a:b", "a?b",
            "a*b", "a[b", "a\\b", "a@{b", "@", "a//b", ".hidden", "a/.b", "x.lock",
            "a/x.lock", "trail.",
        ):
            self.assertFalse(validator.valid_branch_name(name), name)

    def test_admission_rejects_but_a_retained_run_still_loads(self):
        plan = {
            "contract_version": 5,
            "objective": "objective",
            "scope_summary": "scope",
            "approved_decisions": ["settled"],
            "leaves": [leaf("alpha", "bad owner")],
            "work_units": [
                {
                    "id": "alpha",
                    "original_size": "small",
                    "cohesive_outcome": "Complete alpha",
                    "decomposition": {"shape": "single"},
                }
            ],
        }
        admitted = validator.validate(plan)
        self.assertTrue(
            any("worktree_owner must be a valid git branch name" in e for e in admitted["errors"]),
            admitted["errors"],
        )
        retained = validator.validate(plan, admission=False)
        self.assertFalse(
            any("valid git branch name" in e for e in retained["errors"]), retained["errors"]
        )


if __name__ == "__main__":
    unittest.main()
