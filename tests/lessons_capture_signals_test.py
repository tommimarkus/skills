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


def _user(text: str) -> dict:
    return {"type": "user", "message": {"role": "user",
            "content": [{"type": "text", "text": text}]}}


def _assistant(text: str) -> dict:
    return {"type": "assistant", "message": {"role": "assistant",
            "content": [{"type": "text", "text": text}]}}


class DetectorTest(unittest.TestCase):
    def _detect_user_turn(self, text: str) -> list[str]:
        sig = load_signals()
        with tempfile.TemporaryDirectory() as tmp:
            t = _transcript(Path(tmp), _user(text))
            return sig.detect_corrections(t)

    def test_strong_phrase_in_user_turn_is_detected(self):
        self.assertEqual(
            self._detect_user_turn("please revert that, not what I asked"), ["not-what-i", "revert"]
        )

    def test_plain_request_yields_nothing(self):
        self.assertEqual(self._detect_user_turn("add a new validation case to the rubric"), [])

    def test_phrase_only_in_assistant_turn_is_ignored(self):
        sig = load_signals()
        with tempfile.TemporaryDirectory() as tmp:
            t = _transcript(Path(tmp), _assistant("I will revert that now"))
            self.assertEqual(sig.detect_corrections(t), [])

    def test_bare_no_is_not_a_signal(self):
        self.assertEqual(self._detect_user_turn("no, add another one please"), [])

    def test_missing_file_yields_nothing(self):
        sig = load_signals()
        self.assertEqual(sig.detect_corrections(Path("/nonexistent/x.jsonl")), [])


if __name__ == "__main__":
    unittest.main()
