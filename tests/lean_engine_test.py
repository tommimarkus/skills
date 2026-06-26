import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE = REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit" / "references" / "scripts" / "lean_engine.py"
LEDGER = REPO_ROOT / "tests" / "lean_engine_ledger.jsonl"


def load_engine():
    spec = importlib.util.spec_from_file_location("lean_engine", ENGINE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_engine(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENGINE), *args],
        cwd=REPO_ROOT, input=stdin, capture_output=True, text=True, check=False,
    )


class EngineLoads(unittest.TestCase):
    def test_module_imports(self):
        self.assertIsNotNone(load_engine())


class Normalize(unittest.TestCase):
    def test_strips_markdown_and_lowercases(self):
        eng = load_engine()
        out = eng.normalize("See [the Guide](CLAUDE.md) for `jq` Rules! ")
        self.assertEqual(out, ["see", "the", "guide", "for", "rules"])

    def test_drops_code_fences(self):
        eng = load_engine()
        out = eng.normalize("intro\n```\nrm -rf /\n```\ntail")
        self.assertEqual(out, ["intro", "tail"])


if __name__ == "__main__":
    unittest.main()
