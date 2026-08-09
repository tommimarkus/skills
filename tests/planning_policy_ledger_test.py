import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py"
SPEC = importlib.util.spec_from_file_location("planning_ledger", SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ledger)


class PlanningLedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.common = ["--ledger-root", str(self.root), "--plan-id", "approved-plan"]
        assignment = {"harness": "codex", "tier": "standard", "model_or_alias": "inherit", "effort": "inherit", "worktree": ".worktrees/approved-plan"}
        self.steps = json.dumps([{"id": "build", "summary": "Build helper", **assignment}, {"id": "verify", "dependencies": ["build"], **assignment}])

    def tearDown(self): self.temp.cleanup()

    def invoke(self, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return ledger.main(list(args))

    def test_init_requires_approval_multi_step_and_parent(self):
        self.assertEqual(3, self.invoke(*self.common, "init", "--actor", "worker", "--approved", "--steps-json", self.steps))
        self.assertEqual(3, self.invoke(*self.common, "init", "--actor", "parent", "--steps-json", self.steps))
        self.assertEqual(0, self.invoke(*self.common, "init", "--actor", "parent", "--approved", "--steps-json", self.steps))
        checkpoint = self.root / "planning-policy/ledgers/approved-plan/checkpoint.json"
        self.assertTrue(checkpoint.is_file()); self.assertLessEqual(checkpoint.stat().st_size, 16 * 1024)

    def test_lifecycle_retry_parent_only_and_bounded_show(self):
        self.assertEqual(0, self.invoke(*self.common, "init", "--actor", "parent", "--approved", "--steps-json", self.steps))
        self.assertEqual(3, self.invoke(*self.common, "transition", "--actor", "worker", "--step-id", "build", "--to", "ready"))
        for target in ("ready", "in_progress"):
            self.assertEqual(0, self.invoke(*self.common, "transition", "--actor", "parent", "--step-id", "build", "--to", target))
        self.assertEqual(3, self.invoke(*self.common, "transition", "--actor", "parent", "--step-id", "build", "--to", "blocked"))
        self.assertEqual(0, self.invoke(*self.common, "transition", "--actor", "parent", "--step-id", "build", "--to", "blocked", "--blocker-code", "blocked:model_unavailable"))
        blocked = json.loads((self.root / "planning-policy/ledgers/approved-plan/checkpoint.json").read_text())
        self.assertEqual("blocked:model_unavailable", blocked["steps"]["build"]["blocker_code"])
        self.assertEqual(0, self.invoke(*self.common, "transition", "--actor", "parent", "--step-id", "build", "--to", "ready", "--retry", "--evidence-path", "evidence/recovered.json", "--summary", "model restored"))
        self.assertEqual(0, self.invoke(*self.common, "transition", "--actor", "parent", "--step-id", "build", "--to", "in_progress"))
        self.assertEqual(0, self.invoke(*self.common, "transition", "--actor", "parent", "--step-id", "build", "--to", "failed"))
        self.assertEqual(3, self.invoke(*self.common, "transition", "--actor", "parent", "--step-id", "build", "--to", "ready"))
        self.assertEqual(0, self.invoke(*self.common, "transition", "--actor", "parent", "--step-id", "build", "--to", "ready", "--retry", "--evidence-path", "evidence/retry.json", "--summary", "changed handoff"))
        for target in ("in_progress", "completed", "integrated"):
            args = [*self.common, "transition", "--actor", "parent", "--step-id", "build", "--to", target]
            if target == "integrated": args += ["--summary", "integrated"]
            self.assertEqual(0, self.invoke(*args))
        self.assertEqual(0, self.invoke(*self.common, "transition", "--actor", "parent", "--step-id", "verify", "--to", "ready"))
        self.assertEqual(0, self.invoke(*self.common, "show")); self.assertEqual(0, self.invoke(*self.common, "validate"))
        events = (self.root / "planning-policy/ledgers/approved-plan/events.jsonl").read_text().splitlines()
        self.assertGreaterEqual(len(events), 8); self.assertEqual(list(range(1, len(events) + 1)), [json.loads(x)["sequence"] for x in events])
        checkpoint = json.loads((self.root / "planning-policy/ledgers/approved-plan/checkpoint.json").read_text())
        self.assertEqual("codex", checkpoint["steps"]["build"]["harness"])
        self.assertEqual("standard", checkpoint["steps"]["build"]["tier"])
        self.assertEqual("inherit", checkpoint["steps"]["build"]["model_or_alias"])
        self.assertEqual("inherit", checkpoint["steps"]["build"]["effort"])
        self.assertEqual(".worktrees/approved-plan", checkpoint["steps"]["build"]["worktree"])

    def test_non_git_requires_explicit_persistent_root(self):
        self.assertEqual(3, self.invoke("--repo-root", str(self.root), "--plan-id", "no-git", "init", "--actor", "parent", "--approved", "--steps-json", self.steps))
        self.assertEqual(3, self.invoke("--ledger-root", "relative-root", "--plan-id", "no-git", "init", "--actor", "parent", "--approved", "--steps-json", self.steps))


if __name__ == "__main__": unittest.main()
