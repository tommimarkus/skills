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


class Clones(unittest.TestCase):
    def _stream(self, lens, text, ext=".py"):
        return lens.strip_and_tokenize(text, lens.profile_for(ext))

    def test_verbatim_cross_file_clone_blocks(self):
        lens = load_lens()
        body = " ".join(f"t{i}" for i in range(30))          # 30 identical tokens
        streams = {"a.py": self._stream(lens, body), "b.py": self._stream(lens, body)}
        clones = lens.find_clones(streams, min_tokens=8)
        self.assertTrue(clones)
        c = clones[0]
        self.assertEqual(c.severity, "block")               # 30 >= 2*8
        self.assertEqual(c.code, "LA-CODE-DUP-1")
        self.assertEqual({c.path, c.matched_path}, {"a.py", "b.py"})
        self.assertEqual(c.tokens, 30)

    def test_midband_clone_is_info(self):
        lens = load_lens()
        body = " ".join(f"t{i}" for i in range(10))          # 10 tokens: 8 <= 10 < 16
        streams = {"a.py": self._stream(lens, body), "b.py": self._stream(lens, body)}
        clones = lens.find_clones(streams, min_tokens=8)
        self.assertEqual(clones[0].severity, "info")
        self.assertEqual(clones[0].code, "LA-CODE-DUP-2")

    def test_below_threshold_no_clone(self):
        lens = load_lens()
        body = " ".join(f"t{i}" for i in range(5))
        streams = {"a.py": self._stream(lens, body), "b.py": self._stream(lens, body)}
        self.assertEqual(lens.find_clones(streams, min_tokens=8), [])

    def test_distinct_files_no_clone(self):
        lens = load_lens()
        streams = {"a.py": self._stream(lens, " ".join(f"a{i}" for i in range(30))),
                   "b.py": self._stream(lens, " ".join(f"b{i}" for i in range(30)))}
        self.assertEqual(lens.find_clones(streams, min_tokens=8), [])

    def test_intra_file_nonoverlapping_clone(self):
        lens = load_lens()
        block = " ".join(f"t{i}" for i in range(12))
        streams = {"a.py": self._stream(lens, block + " sep " + block)}
        clones = lens.find_clones(streams, min_tokens=8)
        self.assertTrue(clones)
        self.assertEqual(clones[0].path, "a.py")
        self.assertEqual(clones[0].matched_path, "a.py")

    def test_comment_only_difference_still_clone(self):
        lens = load_lens()
        body = " ".join(f"t{i}" for i in range(20))
        streams = {"a.py": self._stream(lens, "# header\n" + body),
                   "b.py": self._stream(lens, body + "\n# trailer")}
        self.assertTrue(lens.find_clones(streams, min_tokens=8))


class Discovery(unittest.TestCase):
    def test_reads_only_source_extensions(self):
        lens = load_lens()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.py").write_text("x = 1\n", encoding="utf-8")
            (root / "notes.md").write_text("# md\n", encoding="utf-8")
            files = lens.read_sources(root, lens.DEFAULT_EXTENSIONS, ())
            self.assertIn("a.py", files)
            self.assertNotIn("notes.md", files)

    def test_excludes_vendored_dirs(self):
        lens = load_lens()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "node_modules").mkdir()
            (root / "node_modules" / "v.js").write_text("var x = 1\n", encoding="utf-8")
            (root / "keep.js").write_text("var y = 2\n", encoding="utf-8")
            files = lens.read_sources(root, lens.DEFAULT_EXTENSIONS, ())
            self.assertEqual(list(files), ["keep.js"])

    def test_exempt_path_and_marker_suppressed(self):
        lens = load_lens()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "gen.py").write_text("x = 1\n", encoding="utf-8")
            (root / "b.py").write_text(f"# {lens.INTENTIONAL_MARKER}\ny = 2\n", encoding="utf-8")
            files = lens.read_sources(root, lens.DEFAULT_EXTENSIONS, ("gen.py",))
            self.assertNotIn("gen.py", files)      # exempt_paths
            self.assertNotIn("b.py", files)        # inline marker

    def test_load_config_defaults_when_no_registry(self):
        lens = load_lens()
        exempt, exts = lens.load_config(None)
        self.assertEqual(exempt, ())
        self.assertEqual(exts, lens.DEFAULT_EXTENSIONS)


class Cli(unittest.TestCase):
    def test_json_and_exit1_on_block(self):
        with tempfile.TemporaryDirectory() as d:
            body = " ".join(f"t{i}" for i in range(30)) + "\n"
            (Path(d) / "a.py").write_text(body, encoding="utf-8")
            (Path(d) / "b.py").write_text(body, encoding="utf-8")
            r = run_lens(d, "--min-tokens", "8", "--format", "json")
            self.assertEqual(r.returncode, 1)
            codes = {f["code"] for f in json.loads(r.stdout)["findings"]}
            self.assertIn("LA-CODE-DUP-1", codes)

    def test_clean_tree_exit0(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.py").write_text(" ".join(f"a{i}" for i in range(30)) + "\n", encoding="utf-8")
            (Path(d) / "b.py").write_text(" ".join(f"b{i}" for i in range(30)) + "\n", encoding="utf-8")
            r = run_lens(d, "--min-tokens", "8", "--format", "json")
            self.assertEqual(r.returncode, 0)
            self.assertEqual(json.loads(r.stdout)["findings"], [])

    def test_malformed_registry_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.py").write_text("x = 1\n", encoding="utf-8")
            (Path(d) / ".lean-audit.toml").write_text("this = = bad", encoding="utf-8")
            r = run_lens(d, "--registry", str(Path(d) / ".lean-audit.toml"), "--format", "json")
            self.assertEqual(r.returncode, 2)


class Calibration(unittest.TestCase):
    def test_block_precision_recall_bar(self):
        lens = load_lens()
        cases = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertGreaterEqual(len(cases), 8, "ledger too small to calibrate")
        tp = fp = fn = 0
        for case in cases:
            streams = {}
            skip = False
            for f in case["files"]:
                if lens.INTENTIONAL_MARKER in f["content"]:
                    skip = True                     # marker = file-level opt-out (see read_sources)
                    continue
                streams[f["path"]] = lens.strip_and_tokenize(
                    f["content"], lens.profile_for(Path(f["path"]).suffix))
            clones = [] if skip and not streams else lens.find_clones(streams, case["min_tokens"])
            fired = any(c.severity == "block" for c in clones)
            if case["expect_block"] and fired:
                tp += 1
            elif case["expect_block"] and not fired:
                fn += 1
            elif not case["expect_block"] and fired:
                fp += 1
        precision = tp / (tp + fp) if (tp + fp) else 1.0
        recall = tp / (tp + fn) if (tp + fn) else 1.0
        self.assertGreaterEqual(precision, 0.90, f"precision {precision:.2f}")
        self.assertGreaterEqual(recall, 0.90, f"recall {recall:.2f}")
