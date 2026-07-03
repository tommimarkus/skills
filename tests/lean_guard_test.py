import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, load_script_module

SCRIPTS = (
    Path(__file__).resolve().parents[1]
    / "souroldgeezer-audit" / "skills" / "lean-audit" / "references" / "scripts"
)
sys.path.insert(0, str(SCRIPTS))

GUARD_LEAN = SCRIPTS / "leanaudit" / "guard_lean.py"


def load_guard():
    return load_script_module("leanaudit_guard_lean", GUARD_LEAN)


BIG = (
    "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi "
    "omicron pi rho sigma tau upsilon phi chi psi omega one two three four five."
)


def corpus(tmp):
    root = Path(tmp)
    a = root / "aud" / "skills" / "s1" / "SKILL.md"
    a.parent.mkdir(parents=True, exist_ok=True)
    a.write_text("## Shared\n" + BIG + "\n", encoding="utf-8")
    return root


def payload(root, rel, content, tool="Edit"):
    fp = str(root / rel)
    if tool == "Write":
        ti = {"file_path": fp, "content": content}
    elif tool == "MultiEdit":
        ti = {"file_path": fp, "edits": [{"old_string": "", "new_string": content}]}
    else:
        ti = {"file_path": fp, "old_string": "", "new_string": content}
    return {"tool_name": tool, "tool_input": ti, "cwd": str(root)}


class Evaluate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = corpus(self._tmp.name)
        self.guard = load_guard()
        # the corpus dir is not a git repo; pin the root deterministically
        self._orig = self.guard._repo_root
        self.guard._repo_root = lambda cwd: self.root

    def tearDown(self):
        self.guard._repo_root = self._orig
        self._tmp.cleanup()

    def test_new_duplicate_is_denied(self):
        reason = self.guard.evaluate(payload(self.root, "aud/skills/s2/SKILL.md", "## Shared\n" + BIG))
        self.assertIsNotNone(reason)
        self.assertIn("lean-audit", reason)
        self.assertIn("sync-intentional", reason)

    def test_unique_content_is_allowed(self):
        reason = self.guard.evaluate(payload(
            self.root, "aud/skills/s2/SKILL.md",
            "## Fresh\nNothing here repeats any four-word run from the corpus whatsoever today because this content introduces completely original vocabulary never previously encountered in reference material samples test cases validation datasets wherever possible."))
        self.assertIsNone(reason)

    def test_subagent_mirror_carveout_is_allowed(self):
        # built-in carve-out: {plugin}/skills/{skill}/SKILL.md <-> {plugin}/agents/{skill}.md
        reason = self.guard.evaluate(payload(self.root, "aud/agents/s1.md", "## Shared\n" + BIG))
        self.assertIsNone(reason)

    def test_override_marker_is_allowed(self):
        body = "## Shared\n<!-- lean-audit:sync-intentional: mirror -->\n" + BIG
        reason = self.guard.evaluate(payload(self.root, "aud/skills/s2/SKILL.md", body))
        self.assertIsNone(reason)

    def test_non_guarded_path_is_allowed_without_engine(self):
        called = {"v": False}
        orig = self.guard.evaluate_added_block
        self.guard.evaluate_added_block = lambda *a, **k: called.__setitem__("v", True) or []
        try:
            reason = self.guard.evaluate(payload(self.root, "notes.txt", "## Shared\n" + BIG))
        finally:
            self.guard.evaluate_added_block = orig
        self.assertIsNone(reason)
        self.assertFalse(called["v"], "engine must not run for a non-guarded path")

    def test_write_and_multiedit_shapes_are_handled(self):
        for tool in ("Write", "MultiEdit"):
            reason = self.guard.evaluate(payload(self.root, "aud/skills/s2/SKILL.md", "## Shared\n" + BIG, tool=tool))
            self.assertIsNotNone(reason, tool)

    def test_non_edit_tool_is_allowed(self):
        self.assertIsNone(self.guard.evaluate({"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": str(self.root)}))

    def test_engine_error_fails_open(self):
        orig = self.guard.evaluate_added_block
        def boom(*a, **k):
            raise RuntimeError("engine exploded")
        self.guard.evaluate_added_block = boom
        stderr = io.StringIO()
        try:
            with contextlib.redirect_stderr(stderr):
                reason = self.guard.evaluate(payload(self.root, "aud/skills/s2/SKILL.md", "## Shared\n" + BIG))
        finally:
            self.guard.evaluate_added_block = orig
        self.assertIsNone(reason)
        self.assertIn("[engine-evaluate]", stderr.getvalue())

    def test_reason_format_error_fails_open(self):
        # A finding that reaches the block branch but is missing the attributes the
        # reason string formats (matched_path/matched_heading/containment/action)
        # exercises the second try/except in evaluate() — the "reason-format" label.
        class _BareBlock:
            severity = "block"

        orig = self.guard.evaluate_added_block
        self.guard.evaluate_added_block = lambda *a, **k: [_BareBlock()]
        stderr = io.StringIO()
        try:
            with contextlib.redirect_stderr(stderr):
                reason = self.guard.evaluate(payload(self.root, "aud/skills/s2/SKILL.md", "## Shared\n" + BIG))
        finally:
            self.guard.evaluate_added_block = orig
        self.assertIsNone(reason)
        self.assertIn("[reason-format]", stderr.getvalue())

    def test_is_guarded_error_fails_open(self):
        orig = self.guard.is_guarded
        def boom(*a, **k):
            raise RuntimeError("is_guarded exploded")
        self.guard.is_guarded = boom
        try:
            reason = self.guard.evaluate(payload(self.root, "aud/skills/s2/SKILL.md", "## Shared\n" + BIG))
        finally:
            self.guard.is_guarded = orig
        self.assertIsNone(reason)


class MainSubprocess(unittest.TestCase):
    def _run(self, stdin):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "lean_guard.py")],
            input=stdin, capture_output=True, text=True, timeout=30,
        )

    def test_malformed_json_allows_silently(self):
        r = self._run("not json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_non_edit_allows_silently(self):
        r = self._run(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_deny_emits_pretooluse_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = corpus(tmp)
            # real git repo so the script's _repo_root resolves
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            p = payload(root, "aud/skills/s2/SKILL.md", "## Shared\n" + BIG)
            r = self._run(json.dumps(p))
            self.assertEqual(r.returncode, 0)
            out = json.loads(r.stdout)
            hso = out["hookSpecificOutput"]
            self.assertEqual(hso["hookEventName"], "PreToolUse")
            self.assertEqual(hso["permissionDecision"], "deny")
            self.assertIn("lean-audit", hso["permissionDecisionReason"])


class FailOpenLoggingTest(unittest.TestCase):
    def test_swallowed_exception_writes_stderr_line(self):
        guard_mod = load_script_module(
            "leanaudit_guard_lean",
            REPO_ROOT
            / "souroldgeezer-audit/skills/lean-audit/references/scripts/leanaudit/guard_lean.py",
        )
        # force the engine call to raise inside evaluate()
        with unittest.mock.patch.object(
            guard_mod, "evaluate", side_effect=RuntimeError("boom")
        ):
            stderr = io.StringIO()
            stdin = io.StringIO('{"tool_name": "Write", "tool_input": {}, "cwd": "."}')
            with contextlib.redirect_stderr(stderr), unittest.mock.patch(
                "sys.stdin", stdin
            ):
                guard_mod.main()  # must NOT raise (fail-open)
        self.assertIn("fail-open allow", stderr.getvalue())
        self.assertIn("RuntimeError", stderr.getvalue())

    def test_repo_root_execution_failure_writes_stderr_line(self):
        guard_mod = load_guard()
        # real execution failure (git missing / OSError), not a non-repo cwd
        with unittest.mock.patch.object(
            guard_mod.subprocess, "run", side_effect=OSError("git not found")
        ):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertIsNone(guard_mod._repo_root("."))  # must fail open
        self.assertIn("fail-open allow", stderr.getvalue())
        self.assertIn("repo-root", stderr.getvalue())
        self.assertIn("OSError", stderr.getvalue())
