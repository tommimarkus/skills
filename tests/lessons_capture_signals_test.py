import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "scripts" / "lessons_capture_signals.py"


def load_signals():
    spec = importlib.util.spec_from_file_location("lessons_capture_signals", MODULE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["lessons_capture_signals"] = module
    spec.loader.exec_module(module)
    return module


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
    def test_strong_phrase_in_user_turn_is_detected(self):
        sig = load_signals()
        with tempfile.TemporaryDirectory() as tmp:
            t = _transcript(Path(tmp), _user("please revert that, not what I asked"))
            self.assertEqual(sig.detect_corrections(t), ["not-what-i", "revert"])

    def test_plain_request_yields_nothing(self):
        sig = load_signals()
        with tempfile.TemporaryDirectory() as tmp:
            t = _transcript(Path(tmp), _user("add a new validation case to the rubric"))
            self.assertEqual(sig.detect_corrections(t), [])

    def test_phrase_only_in_assistant_turn_is_ignored(self):
        sig = load_signals()
        with tempfile.TemporaryDirectory() as tmp:
            t = _transcript(Path(tmp), _assistant("I will revert that now"))
            self.assertEqual(sig.detect_corrections(t), [])

    def test_bare_no_is_not_a_signal(self):
        sig = load_signals()
        with tempfile.TemporaryDirectory() as tmp:
            t = _transcript(Path(tmp), _user("no, add another one please"))
            self.assertEqual(sig.detect_corrections(t), [])

    def test_missing_file_yields_nothing(self):
        sig = load_signals()
        self.assertEqual(sig.detect_corrections(Path("/nonexistent/x.jsonl")), [])


if __name__ == "__main__":
    unittest.main()
