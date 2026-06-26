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


class Shingles(unittest.TestCase):
    def test_kgram_set(self):
        eng = load_engine()
        self.assertEqual(
            eng.shingle_set(["a", "b", "c", "d", "e"], k=3),
            {("a", "b", "c"), ("b", "c", "d"), ("c", "d", "e")},
        )

    def test_short_token_list_returns_single_shingle(self):
        eng = load_engine()
        self.assertEqual(eng.shingle_set(["a", "b"], k=4), {("a", "b")})
        self.assertEqual(eng.shingle_set([], k=4), set())

    def test_containment_is_asymmetric(self):
        eng = load_engine()
        added = {("a", "b"), ("b", "c")}
        other = {("a", "b"), ("b", "c"), ("x", "y"), ("y", "z")}
        self.assertEqual(eng.containment(added, other), 1.0)   # all of added is in other
        self.assertEqual(eng.containment(other, added), 0.5)   # half of other is in added
        self.assertEqual(eng.containment(set(), other), 0.0)


class Sections(unittest.TestCase):
    def test_split_by_heading(self):
        eng = load_engine()
        text = "pre\n# A\nbody a\n## B\nbody b\n"
        self.assertEqual(
            eng.split_sections(text),
            [("", "pre"), ("A", "body a"), ("B", "body b")],
        )

    def test_build_index_sets_shingles(self):
        eng = load_engine()
        idx = eng.build_index({"f.md": "# H\none two three four five"})
        self.assertEqual(len(idx), 1)  # empty preamble dropped; only the "H" section
        h = [s for s in idx if s.heading == "H"][0]
        self.assertEqual(h.path, "f.md")
        self.assertIn(("one", "two", "three", "four"), h.shingles)


class RegistryAndOverride(unittest.TestCase):
    def test_load_registry(self):
        eng = load_engine()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".lean-audit.toml"
            p.write_text(
                '[[canonical_home]]\npath = "CLAUDE.md"\nheading = "Git ignore hygiene (MUST)"\n'
                '[[must_sync]]\nglobs = ["**/SKILL.md", "**/agents/*.md"]\n',
                encoding="utf-8",
            )
            reg = eng.load_registry(p)
            self.assertIn(("CLAUDE.md", "Git ignore hygiene (MUST)"), reg.canonical_homes)
            self.assertTrue(eng.must_sync_pair(reg, "x/SKILL.md", "x/agents/y.md"))
            self.assertFalse(eng.must_sync_pair(reg, "x/SKILL.md", "x/README.md"))

    def test_missing_registry_is_empty(self):
        eng = load_engine()
        reg = eng.load_registry(None)
        self.assertEqual(reg.canonical_homes, ())
        self.assertEqual(reg.must_sync, ())

    def test_override_marker(self):
        eng = load_engine()
        self.assertTrue(eng.has_override("text <!-- lean-audit:sync-intentional: mirrors manifest -->"))
        self.assertFalse(eng.has_override("plain text"))


class Scoring(unittest.TestCase):
    def _idx(self, eng, body_a, body_b, path_a="a/SKILL.md", path_b="CLAUDE.md"):
        return eng.build_index({path_a: f"# A\n{body_a}", path_b: f"# Home\n{body_b}"})

    def test_high_band_cross_file_is_block_dup1(self):
        eng = load_engine()
        words = " ".join(f"w{i}" for i in range(40))
        idx = self._idx(eng, words, words)
        a = [s for s in idx if s.path == "a/SKILL.md"][0]
        reg = eng.load_registry(None)
        f = eng.score_section(a, idx, reg)
        self.assertIsNotNone(f)
        self.assertEqual(f.code, "LA-DUP-1")
        self.assertEqual(f.severity, "block")
        self.assertEqual(f.matched_path, "CLAUDE.md")

    def test_canonical_home_match_is_dup2_with_cite(self):
        eng = load_engine()
        words = " ".join(f"w{i}" for i in range(40))
        idx = self._idx(eng, words, words)
        a = [s for s in idx if s.path == "a/SKILL.md"][0]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".lean-audit.toml"
            p.write_text('[[canonical_home]]\npath = "CLAUDE.md"\nheading = "Home"\n', encoding="utf-8")
            reg = eng.load_registry(p)
        f = eng.score_section(a, idx, reg)
        self.assertEqual(f.code, "LA-DUP-2")
        self.assertIn("CLAUDE.md", f.action)
        self.assertIn("Home", f.action)

    def test_override_suppresses(self):
        eng = load_engine()
        words = " ".join(f"w{i}" for i in range(40))
        idx = self._idx(eng, words + " <!-- lean-audit:sync-intentional: ok -->", words)
        a = [s for s in idx if s.path == "a/SKILL.md"][0]
        self.assertIsNone(eng.score_section(a, idx, eng.load_registry(None)))

    def test_must_sync_pair_exempt(self):
        eng = load_engine()
        words = " ".join(f"w{i}" for i in range(40))
        idx = eng.build_index({"x/SKILL.md": f"# A\n{words}", "x/agents/y.md": f"# B\n{words}"})
        a = [s for s in idx if s.path == "x/SKILL.md"][0]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".lean-audit.toml"
            p.write_text('[[must_sync]]\nglobs = ["**/SKILL.md", "**/agents/*.md"]\n', encoding="utf-8")
            reg = eng.load_registry(p)
        self.assertIsNone(eng.score_section(a, idx, reg))

    def test_short_block_ignored(self):
        eng = load_engine()
        idx = self._idx(eng, "one two three", "one two three")
        a = [s for s in idx if s.path == "a/SKILL.md"][0]
        self.assertIsNone(eng.score_section(a, idx, eng.load_registry(None)))


if __name__ == "__main__":
    unittest.main()
