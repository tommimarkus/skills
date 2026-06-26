import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "scripts" / "agent-hooks" / "stop-lesson-capture.sh"


def _git(cwd: Path, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True,
                   capture_output=True, text=True)


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
    skill = tmp / ".claude" / "skills" / "x"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")


def _transcript(tmp: Path, text: str) -> Path:
    path = tmp / "t.jsonl"
    entry = {"type": "user", "message": {"role": "user",
             "content": [{"type": "text", "text": text}]}}
    path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    return path


def _run(tmp: Path, transcript: Path):
    stdin = json.dumps({"session_id": "s1", "cwd": str(tmp),
                        "transcript_path": str(transcript), "stop_hook_active": False})
    return subprocess.run(["bash", str(HOOK)], input=stdin,
                          capture_output=True, text=True)


class HookTest(unittest.TestCase):
    def test_fires_on_authoring_change_plus_correction(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            _repo(tmp)
            _authoring_change(tmp)
            out = _run(tmp, _transcript(tmp, "revert that, not what I asked"))
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn('"decision": "block"', out.stdout)
            self.assertIn("lesson-capture", out.stdout)

    def test_fires_on_authoring_change_without_correction(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            _repo(tmp)
            _authoring_change(tmp)
            out = _run(tmp, _transcript(tmp, "add another validation case please"))
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn('"decision": "block"', out.stdout)
            self.assertIn("lesson-capture", out.stdout)

    def test_fires_on_authoring_change_without_transcript(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            _repo(tmp)
            _authoring_change(tmp)
            stdin = json.dumps({"session_id": "s1", "cwd": str(tmp),
                                "stop_hook_active": False})
            out = subprocess.run(["bash", str(HOOK)], input=stdin,
                                 capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn('"decision": "block"', out.stdout)
            self.assertIn("lesson-capture", out.stdout)

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

    def test_codex_hooks_registers_the_hook(self):
        data = json.loads((REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
        hooks = [h
                 for group in data["hooks"]["Stop"]
                 for h in group["hooks"]]
        commands = [h["command"] for h in hooks]
        self.assertTrue(any("stop-lesson-capture.sh" in c for c in commands),
                        "stop-lesson-capture.sh not registered in .codex/hooks.json")
        self.assertTrue(
            any(h.get("statusMessage") == "Checking skill-authoring sessions for lesson-capture prompt"
                for h in hooks),
            "lesson-capture Codex hook statusMessage is missing",
        )


if __name__ == "__main__":
    unittest.main()
