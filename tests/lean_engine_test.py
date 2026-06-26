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


if __name__ == "__main__":
    unittest.main()
