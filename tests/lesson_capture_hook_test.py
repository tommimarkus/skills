import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, run_git as _git

HOOK = REPO_ROOT / "scripts" / "agent-hooks" / "stop-lesson-capture.sh"


def _repo(tmp: Path):
    _git(tmp, "init", "-q", "-b", "main")
    _git(tmp, "config", "user.email", "t@example.com")
    _git(tmp, "config", "user.name", "t")
    (tmp / ".claude-plugin").mkdir(parents=True)
    (tmp / ".claude-plugin" / "marketplace.json").write_text("{}", encoding="utf-8")
    (tmp / "seed.txt").write_text("x", encoding="utf-8")
    _git(tmp, "add", "-A")
    _git(tmp, "commit", "-qm", "init")


def _authoring_change(tmp: Path):
    skill = tmp / "internal-skills" / "x"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")


def _transcript(tmp: Path, text: str) -> Path:
    path = tmp / "t.jsonl"
    entry = {"type": "user", "message": {"role": "user",
             "content": [{"type": "text", "text": text}]}}
    path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    return path


def _run(tmp: Path, transcript: Path | None):
    payload = {"session_id": "s1", "cwd": str(tmp), "stop_hook_active": False}
    if transcript is not None:
        payload["transcript_path"] = str(transcript)
    return subprocess.run(["bash", str(HOOK)], input=json.dumps(payload),
                          capture_output=True, text=True)


class HookTest(unittest.TestCase):
    def _assert_hook_blocks(self, out) -> None:
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn('"decision": "block"', out.stdout)
        self.assertIn("lesson-capture", out.stdout)
        self.assertIn("lesson-candidate", out.stdout)

    def _run_hook_after_authoring_change(self, text: str | None):
        """Run the hook after an authoring change; None means no transcript at all."""
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            _repo(tmp)
            _authoring_change(tmp)
            transcript = _transcript(tmp, text) if text is not None else None
            return _run(tmp, transcript)

    def test_fires_on_authoring_change_plus_correction(self):
        self._assert_hook_blocks(self._run_hook_after_authoring_change("revert that, not what I asked"))

    def test_fires_on_authoring_change_without_correction(self):
        self._assert_hook_blocks(self._run_hook_after_authoring_change("add another validation case please"))

    def test_fires_on_authoring_change_without_transcript(self):
        self._assert_hook_blocks(self._run_hook_after_authoring_change(None))

    def test_silent_without_authoring_change(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            _repo(tmp)
            (tmp / "notes.txt").write_text("y", encoding="utf-8")
            out = _run(tmp, _transcript(tmp, "revert that, not what I asked"))
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(out.stdout.strip(), "")


class WiringTest(unittest.TestCase):
    def test_settings_registers_the_hook(self):
        data = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        commands = [h["command"]
                    for group in data["hooks"]["Stop"]
                    for h in group["hooks"]]
        self.assertTrue(any("stop-lesson-capture.sh" in c for c in commands),
                        "stop-lesson-capture.sh not registered in .claude/settings.json")


if __name__ == "__main__":
    unittest.main()
