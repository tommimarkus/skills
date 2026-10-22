import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import unittest.mock
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
ledger_dispatch = importlib.import_module("planningledger.dispatch")

# Issue #144: 33 characters whose hyphens pushed the raw gate block past the 120 cap.
LONG_PLAN_ID = "tqa-audit-2026-10-22-slice-1-of-2"
# The most token-heavy ids the grammar admits: 128-character plan and agent ids and a
# 64-character step id, each separator a proxy token of its own.
MAX_PLAN_ID = "a" + "-" * 127
MAX_STEP_ID = "a" + "-a" * 31 + "a"
MAX_AGENT_ID = "a" + "-" * 127
# An installed plugin's ledger script sits deep in a cache: 275 characters here.
CACHED_SCRIPT = Path(
    "/" + "/".join(f"plugin-cache-{n:02d}" for n in range(16)) + "/planning_ledger.py"
)


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, text=True, capture_output=True
    )


def bare(entry):
    """A dispatch entry without the fields it carries beside the packet."""
    return {key: value for key, value in entry.items() if key not in ledger.DISPATCH_ENTRY_FIELDS}


def assert_awaits(case, code, result, checkpoint, sid, agent):
    """The command succeeded and its `next` awaits exactly this step's current attempt."""
    attempt = checkpoint["steps"][sid]["attempt_id"]
    case.assertEqual(
        (0, {"await_step_id": sid, "agent_id": agent, "attempt_id": attempt}),
        (code, result.get("next")),
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
    plan_id = "plan"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = tempfile.TemporaryDirectory()
        cls.addClassCleanup(base.cleanup)
        cls.base_repo = Path(base.name) / "repo"
        git(Path(base.name), "init", "-b", "main", str(cls.base_repo))
        git(cls.base_repo, "config", "user.name", "Test User")
        git(cls.base_repo, "config", "user.email", "test@example.invalid")
        (cls.base_repo / ".gitignore").write_text(".worktrees/\n")
        git(cls.base_repo, "add", ".gitignore")
        git(cls.base_repo, "commit", "-m", "base")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.scratch = Path(self.temporary.name)
        self.repo = self.scratch / "repo"
        shutil.copytree(self.base_repo, self.repo, symlinks=True)

    def call(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = ledger.main(
                ["--repo-root", str(self.repo), "--plan-id", self.plan_id, *arguments]
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
        return common / "planning-policy/ledgers" / self.plan_id / self.run_id / "checkpoint.json"

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
        self.assertEqual(bare(packet), granular["handoff"])

    def test_dispatch_stores_the_packet_and_returns_a_bounded_prompt(self):
        self.init([leaf("alpha", "leaf-alpha")])
        code, result = self.dispatch("alpha", "--create-from", "main")
        self.assertEqual(0, code, result)
        (entry,) = result["handoffs"]
        path = Path(entry["packet_path"])
        self.assertTrue(path.is_absolute())
        self.assertEqual(
            f"handoffs/alpha/{entry['attempt_id']}.json",
            str(path.relative_to(self.checkpoint_path().parent)),
        )
        self.assertEqual(bare(entry), json.loads(path.read_text()))
        prompt = entry["prompt"]
        self.assertLessEqual(len(ledger.worker_prompt_fixed_text(bare(entry))), 1200)
        for fact in (str(path), entry["worktree"], "validate-return", "--return-file -", "exactly"):
            self.assertIn(fact, prompt)
        self.assertTrue(prompt.endswith(
            "Your final message is exactly the bounded-step-return-v1 JSON object and nothing else."))
        # The stored layout is admitted by later commands, and the entry still validates as a packet.
        self.assertEqual(0, self.call("show", "--run-id", self.run_id)[0])
        self.assertEqual(entry["handoff_sha256"], ledger.valid_worker_handoff(entry)["handoff_sha256"])

    def test_validate_return_reads_the_return_from_stdin(self):
        self.init([leaf("alpha", "leaf-alpha")])
        _code, result = self.dispatch("alpha", "--create-from", "main")
        (entry,) = result["handoffs"]
        value = {
            "schema": "bounded-step-return-v1", "step_id": "alpha", "attempt_id": entry["attempt_id"],
            "agent_id": entry["agent_id"], "status": "blocked", "changed_paths": [],
            "acceptance": {"command": "uv run test", "exit_code": None, "summary": "stopped"},
            "blockers": [{"code": "blocked:missing_input", "summary": "missing"}], "notes": [],
            "unstarted_remainder": [], "commit_hash": "",
        }
        for raw, expected in ((json.dumps(value), 0), (" " * (8 * 1024 + 1), 3)):
            stdin = io.TextIOWrapper(io.BytesIO(raw.encode()))
            with unittest.mock.patch("sys.stdin", stdin):
                code, output = self.call(
                    "validate-return", "--handoff-file", entry["packet_path"], "--return-file", "-"
                )
            self.assertEqual(expected, code, output)

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

    @unittest.skipIf(os.geteuid() == 0, "root ignores directory permissions")
    def test_failed_worktree_add_rolls_back_the_branch_it_created(self):
        self.init([leaf("alpha", "leaf-alpha")])
        registry = self.repo / ".git/worktrees"
        registry.mkdir()
        registry.chmod(0o555)
        self.addCleanup(registry.chmod, 0o755)
        before = self.checkpoint_path().read_bytes()
        code, result = self.dispatch("alpha", "--create-from", "main")
        self.assertEqual(3, code)
        self.assertIn("cannot create worktree", result["error"])
        self.assertIn("(removed branch leaf-alpha created by this attempt)", result["error"])
        self.assertEqual(before, self.checkpoint_path().read_bytes())
        self.assertEqual("", git(self.repo, "branch", "--list", "leaf-alpha").stdout.strip())

    def test_failed_create_from_keeps_a_pre_existing_owner_branch(self):
        git(self.repo, "branch", "leaf-alpha")
        old = git(self.repo, "rev-parse", "leaf-alpha").stdout.strip()
        git(self.repo, "commit", "--allow-empty", "-m", "advance")
        self.init([leaf("alpha", "leaf-alpha")])
        code, result = self.dispatch("alpha", "--create-from", "main")
        self.assertEqual(3, code)
        self.assertIn("cannot create worktree", result["error"])
        self.assertNotIn("removed branch", result["error"])
        self.assertEqual(old, git(self.repo, "rev-parse", "leaf-alpha").stdout.strip())

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

    def test_batch_prompts_name_their_position_and_ask_for_one_json_array(self):
        self.init(*batch_leaves())
        handoffs = self.dispatch("first", "--create-from", "main")[1]["handoffs"]
        one, two = (item["prompt"] for item in handoffs)
        self.assertIn("member 1 of 2 of batch group", one)
        self.assertIn("member 2 of 2 of batch group", two)
        for index, (item, prompt) in enumerate(zip(handoffs, (one, two)), 1):
            self.assertIn("one JSON array", prompt)
            fixed = ledger.worker_prompt_fixed_text(bare(item), (index, 2, "group"))
            self.assertLessEqual(len(fixed), 1200)
            self.assertNotIn("exactly the bounded-step-return-v1 JSON object", prompt)

    def test_long_script_and_plan_paths_still_dispatch_with_the_full_paths(self):
        self.plan_id = MAX_PLAN_ID
        self.init([leaf("alpha", "leaf-alpha")])
        with unittest.mock.patch.object(ledger_dispatch, "LEDGER_SCRIPT", CACHED_SCRIPT):
            code, result = self.dispatch("alpha", "--create-from", "main")
        self.assertEqual(0, code, result)
        (entry,) = result["handoffs"]
        prompt = entry["prompt"]
        for path in (entry["packet_path"], entry["worktree"], str(CACHED_SCRIPT)):
            self.assertIn(path, prompt)
        self.assertGreater(len(prompt), ledger.MAX_WORKER_PROMPT)
        self.assertLessEqual(
            len(ledger.worker_prompt_fixed_text(bare(entry))), ledger.MAX_WORKER_PROMPT
        )

    def test_next_only_names_dispatch_for_a_pending_step(self):
        self.init([leaf("alpha", "leaf-alpha")])
        code, result = self.call("show", "--run-id", self.run_id, "--next-only")
        self.assertEqual(0, code, result)
        self.assertEqual("ready_pending", result["next"]["category"])
        self.assertIn(" dispatch ", result["next"]["command"])


class WorkerPromptBoundTest(unittest.TestCase):
    """#144: the 1,200-character bound covers the prompt's fixed text, not where files live."""

    def packet(self, step_id, attempt_id, worktree):
        return {"portable_tier": "standard", "step_id": step_id, "attempt_id": attempt_id,
                "worktree": worktree}

    def test_the_measured_fixed_text_ignores_path_and_id_length(self):
        short = self.packet("s", "a", "/w")
        maximal = self.packet(MAX_STEP_ID, "7d6c608b-0925-47cf-9c31-cc5867295b0e", "/" + "w" * 400)
        for small, large in ((None, None), ((1, 2, "b"), (1, 2, MAX_STEP_ID))):
            with self.subTest(member=small):
                fixed = ledger.worker_prompt_fixed_text(short, small)
                self.assertEqual(fixed, ledger.worker_prompt_fixed_text(maximal, large))
                self.assertNotIn(MAX_STEP_ID, fixed)
        # The bound uses that measure, so the full-length maximal prompt is still issued.
        packet_path = Path("/" + "p" * 400)
        prompt = ledger.worker_prompt(maximal, packet_path)
        script = str(ledger_dispatch.LEDGER_SCRIPT)
        self.assertEqual(ledger.worker_prompt_text(maximal, str(packet_path), script), prompt)
        self.assertGreater(len(prompt), ledger.MAX_WORKER_PROMPT)

    def test_the_bound_still_refuses_growth_of_the_fixed_text(self):
        packet = self.packet("s", "a", "/w")
        size = len(ledger.worker_prompt_fixed_text(packet))
        script = str(ledger_dispatch.LEDGER_SCRIPT)
        with unittest.mock.patch.object(ledger_dispatch, "MAX_WORKER_PROMPT", size):
            self.assertEqual(ledger.worker_prompt_text(packet, "/p", script),
                             ledger.worker_prompt(packet, Path("/p")))
        with unittest.mock.patch.object(ledger_dispatch, "MAX_WORKER_PROMPT", size - 1):
            with self.assertRaises(ledger.Error) as raised:
                ledger.worker_prompt(packet, Path("/p"))
        self.assertEqual("worker prompt exceeds 1200 characters", str(raised.exception))


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
