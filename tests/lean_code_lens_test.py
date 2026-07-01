import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LENS = REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit" / "references" / "scripts" / "code_lens.py"
LEDGER = REPO_ROOT / "tests" / "lean_code_ledger.jsonl"


def load_lens():
    spec = importlib.util.spec_from_file_location("code_lens", LENS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_lens(*args, stdin=None):
    return subprocess.run([sys.executable, str(LENS), *args],
                          cwd=REPO_ROOT, input=stdin, capture_output=True, text=True, check=False)


class Tokenizer(unittest.TestCase):
    def test_strips_line_and_block_comments(self):
        lens = load_lens()
        prof = lens.profile_for(".js")
        toks = [t for t, _ in lens.strip_and_tokenize("a = 1 // hi\n/* x */ b = 2\n", prof)]
        self.assertEqual(toks, ["a", "=", "NUM", "b", "=", "NUM"])

    def test_string_and_number_normalized(self):
        lens = load_lens()
        prof = lens.profile_for(".py")
        toks = [t for t, _ in lens.strip_and_tokenize('x = "hello" + 42', prof)]
        self.assertEqual(toks, ["x", "=", "STR", "+", "NUM"])

    def test_line_numbers_tracked(self):
        lens = load_lens()
        prof = lens.profile_for(".py")
        pairs = lens.strip_and_tokenize("a\n\nb", prof)
        self.assertEqual(pairs, [("a", 1), ("b", 3)])

    def test_unknown_extension_uses_generic_profile(self):
        lens = load_lens()
        self.assertEqual(lens.profile_for(".zzz"), lens.GENERIC_PROFILE)
