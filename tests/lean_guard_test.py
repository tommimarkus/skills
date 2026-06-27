import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = (
    Path(__file__).resolve().parents[1]
    / "souroldgeezer-audit" / "skills" / "lean-audit" / "references" / "scripts"
)
sys.path.insert(0, str(SCRIPTS))
import lean_guard  # noqa: E402
import lean_engine  # noqa: E402

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
        # the corpus dir is not a git repo; pin the root deterministically
        self._orig = lean_guard._repo_root
        lean_guard._repo_root = lambda cwd: self.root

    def tearDown(self):
        lean_guard._repo_root = self._orig
        self._tmp.cleanup()

    def test_new_duplicate_is_denied(self):
        reason = lean_guard.evaluate(payload(self.root, "aud/skills/s2/SKILL.md", "## Shared\n" + BIG))
        self.assertIsNotNone(reason)
        self.assertIn("lean-audit", reason)
        self.assertIn("sync-intentional", reason)

    def test_unique_content_is_allowed(self):
        reason = lean_guard.evaluate(payload(
            self.root, "aud/skills/s2/SKILL.md",
            "## Fresh\nNothing here repeats any four-word run from the corpus whatsoever today because this content introduces completely original vocabulary never previously encountered in reference material samples test cases validation datasets wherever possible."))
        self.assertIsNone(reason)

    def test_subagent_mirror_carveout_is_allowed(self):
        # built-in carve-out: {plugin}/skills/{skill}/SKILL.md <-> {plugin}/agents/{skill}.md
        reason = lean_guard.evaluate(payload(self.root, "aud/agents/s1.md", "## Shared\n" + BIG))
        self.assertIsNone(reason)

    def test_override_marker_is_allowed(self):
        body = "## Shared\n<!-- lean-audit:sync-intentional: mirror -->\n" + BIG
        reason = lean_guard.evaluate(payload(self.root, "aud/skills/s2/SKILL.md", body))
        self.assertIsNone(reason)

    def test_non_guarded_path_is_allowed_without_engine(self):
        called = {"v": False}
        orig = lean_engine.evaluate_added_block
        lean_engine.evaluate_added_block = lambda *a, **k: called.__setitem__("v", True) or []
        try:
            reason = lean_guard.evaluate(payload(self.root, "notes.txt", "## Shared\n" + BIG))
        finally:
            lean_engine.evaluate_added_block = orig
        self.assertIsNone(reason)
        self.assertFalse(called["v"], "engine must not run for a non-guarded path")

    def test_write_and_multiedit_shapes_are_handled(self):
        for tool in ("Write", "MultiEdit"):
            reason = lean_guard.evaluate(payload(self.root, "aud/skills/s2/SKILL.md", "## Shared\n" + BIG, tool=tool))
            self.assertIsNotNone(reason, tool)

    def test_non_edit_tool_is_allowed(self):
        self.assertIsNone(lean_guard.evaluate({"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": str(self.root)}))

    def test_engine_error_fails_open(self):
        orig = lean_engine.evaluate_added_block
        def boom(*a, **k):
            raise RuntimeError("engine exploded")
        lean_engine.evaluate_added_block = boom
        try:
            reason = lean_guard.evaluate(payload(self.root, "aud/skills/s2/SKILL.md", "## Shared\n" + BIG))
        finally:
            lean_engine.evaluate_added_block = orig
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
