import json
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, load_script_module

MODULE = REPO_ROOT / "scripts" / "lessons_capture_signals.py"


def load_signals():
    return load_script_module("lessons_capture_signals", MODULE)


def _transcript(tmp: Path, *entries: dict) -> Path:
    path = tmp / "transcript.jsonl"
    path.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
    return path


def _entry(role: str, text: str) -> dict:
    return {"type": role, "message": {"role": role,
            "content": [{"type": "text", "text": text}]}}


def _user(text: str) -> dict:
    return _entry("user", text)


def _assistant(text: str) -> dict:
    return _entry("assistant", text)


class DetectorTest(unittest.TestCase):
    def _detect(self, entry: dict) -> list[str]:
        sig = load_signals()
        with tempfile.TemporaryDirectory() as tmp:
            t = _transcript(Path(tmp), entry)
            return sig.detect_corrections(t)

    def _detect_user_turn(self, text: str) -> list[str]:
        return self._detect(_user(text))

    def test_strong_phrase_in_user_turn_is_detected(self):
        self.assertEqual(
            self._detect_user_turn("please revert that, not what I asked"), ["not-what-i", "revert"]
        )

    def test_plain_request_yields_nothing(self):
        self.assertEqual(self._detect_user_turn("add a new validation case to the rubric"), [])

    def test_phrase_only_in_assistant_turn_is_ignored(self):
        self.assertEqual(self._detect(_assistant("I will revert that now")), [])

    def test_bare_no_is_not_a_signal(self):
        self.assertEqual(self._detect_user_turn("no, add another one please"), [])

    def test_missing_file_yields_nothing(self):
        sig = load_signals()
        self.assertEqual(sig.detect_corrections(Path("/nonexistent/x.jsonl")), [])


class AuditRunTest(unittest.TestCase):
    def _detect(self, entry: dict) -> list[str]:
        sig = load_signals()
        with tempfile.TemporaryDirectory() as tmp:
            return sig.detect_audit_runs(_transcript(Path(tmp), entry))

    def test_claude_skill_tool_use_is_detected(self):
        entry = {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "souroldgeezer-audit:ip-hygiene"}}]}}
        self.assertEqual(self._detect(entry), ["ip-hygiene"])

    def test_codex_report_function_call_is_detected(self):
        entry = {"type": "response_item", "payload": {"type": "function_call", "name": "shell",
                 "arguments": json.dumps({"command": ["scripts/skill-architecture-report.sh"]})}}
        self.assertEqual(self._detect(entry), ["skill-architecture-report"])

    def test_codex_audit_skill_read_is_detected(self):
        entry = {"type": "response_item", "payload": {"type": "function_call", "name": "shell",
                 "arguments": json.dumps({"command": ["cat", "skills/lean-audit/SKILL.md"]})}}
        self.assertEqual(self._detect(entry), ["lean-audit"])

    def test_mention_in_user_text_is_not_a_run(self):
        self.assertEqual(self._detect(_user("please run lean-audit and the skill-architecture-report")), [])

    def test_other_skill_is_not_an_audit_run(self):
        entry = {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "software-design"}}]}}
        self.assertEqual(self._detect(entry), [])

    def test_malformed_and_missing_transcripts_fail_open(self):
        sig = load_signals()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text("not json\n[1]\n", encoding="utf-8")
            self.assertEqual(sig.detect_audit_runs(path), [])
        self.assertEqual(sig.detect_audit_runs(Path("/nonexistent/x.jsonl")), [])


if __name__ == "__main__":
    unittest.main()
