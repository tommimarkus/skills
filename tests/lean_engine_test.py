import importlib.util
import json
import subprocess
import sys
import tempfile
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

    @unittest.skip("Plan 2 blocker: must_sync needs counterpart (same-skill) semantics, not flat globs")
    def test_must_sync_should_not_exempt_unrelated_skill_files(self):
        eng = load_engine()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".lean-audit.toml"
            p.write_text('[[must_sync]]\nglobs = ["**/SKILL.md", "**/agents/*.md"]\n', encoding="utf-8")
            reg = eng.load_registry(p)
        # Desired (Plan 2): two UNRELATED skills' SKILL.md must NOT be treated as a sync pair.
        self.assertFalse(eng.must_sync_pair(reg, "a/skills/x/SKILL.md", "a/skills/z/SKILL.md"))


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


class Cli(unittest.TestCase):
    def _repo(self, d):
        words = " ".join(f"w{i}" for i in range(40))
        (Path(d) / "CLAUDE.md").write_text(f"# Home\n{words}\n", encoding="utf-8")
        sk = Path(d) / "p/skills/x"
        sk.mkdir(parents=True)
        (sk / "SKILL.md").write_text(f"# A\n{words}\n", encoding="utf-8")
        return d

    def test_full_path_json_and_exit1(self):
        with tempfile.TemporaryDirectory() as d:
            self._repo(d)
            r = run_engine(d, "--format", "json")
            self.assertEqual(r.returncode, 1)
            payload = json.loads(r.stdout)
            codes = {f["code"] for f in payload["findings"]}
            self.assertIn("LA-DUP-1", codes)

    def test_clean_repo_exit0(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "CLAUDE.md").write_text("# Home\nunique alpha bravo charlie\n", encoding="utf-8")
            r = run_engine(d, "--format", "json")
            self.assertEqual(r.returncode, 0)
            self.assertEqual(json.loads(r.stdout)["findings"], [])

    def test_added_text_stdin(self):
        with tempfile.TemporaryDirectory() as d:
            self._repo(d)
            block = "# A\n" + " ".join(f"w{i}" for i in range(40))
            r = run_engine("--added-text", "-", "--source", "p/skills/x/SKILL.md",
                           "--corpus-root", d, "--format", "json", stdin=block)
            self.assertEqual(r.returncode, 1)
            self.assertIn("LA-DUP-1", {f["code"] for f in json.loads(r.stdout)["findings"]})

    def test_added_text_rejects_non_dash(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_engine("--added-text", "x", "--source", "a.md", "--corpus-root", d)
            self.assertEqual(r.returncode, 2)

    def test_file_scope_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            self._repo(d)
            r = run_engine(str(Path(d) / "CLAUDE.md"), "--format", "json")
            self.assertEqual(r.returncode, 1)
            self.assertIn("LA-DUP-1", {f["code"] for f in json.loads(r.stdout)["findings"]})

    def test_malformed_registry_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            self._repo(d)
            (Path(d) / ".lean-audit.toml").write_text("this = = not valid", encoding="utf-8")
            r = run_engine(d, "--format", "json")
            self.assertEqual(r.returncode, 2)


class StaleRefs(unittest.TestCase):
    def test_broken_file_link(self):
        eng = load_engine()
        files = {"a/SKILL.md": "see [guide](../missing/x.md) for details"}
        self.assertIn("LA-STALE-1", {f.code for f in eng.scan_stale_refs(files)})

    def test_resolving_link_ok(self):
        eng = load_engine()
        files = {"a/SKILL.md": "see [t](b.md)", "a/b.md": "# B\nbody"}
        self.assertEqual(eng.scan_stale_refs(files), [])

    def test_broken_anchor(self):
        eng = load_engine()
        files = {"a/SKILL.md": "see [t](b.md#nope)", "a/b.md": "# Real Heading\nx"}
        self.assertIn("LA-STALE-1", {f.code for f in eng.scan_stale_refs(files)})

    def test_valid_anchor_ok(self):
        eng = load_engine()
        files = {"a/SKILL.md": "see [t](b.md#real-heading)", "a/b.md": "# Real Heading\nx"}
        self.assertEqual(eng.scan_stale_refs(files), [])

    def test_url_and_mailto_skipped(self):
        eng = load_engine()
        files = {"a/SKILL.md": "[t](https://example.com/x) [m](mailto:a@b.c)"}
        self.assertEqual(eng.scan_stale_refs(files), [])


class Calibration(unittest.TestCase):
    def test_precision_recall_bar(self):
        eng = load_engine()
        cases = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(cases), 12, "ledger too small to calibrate")
        tp = fp = fn = 0
        for case in cases:
            files = {f["path"]: f["content"] for f in case["files"]}
            reg = eng.load_registry(None)
            if case.get("registry"):
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / ".lean-audit.toml"
                    p.write_text(case["registry"], encoding="utf-8")
                    reg = eng.load_registry(p)
            blocks = [f for f in eng.scan(files, reg)
                      if f.severity == "block" and f.path == case["expect_source"]]
            fired = bool(blocks)
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


class DeadRefs(unittest.TestCase):
    def test_unreferenced_ref_is_dead(self):
        eng = load_engine()
        files = {"x/SKILL.md": "the workflow", "x/references/orphan.md": "# O\nstuff"}
        self.assertIn("LA-DEAD-1", {f.code for f in eng.find_dead_refs(files)})

    def test_referenced_ref_not_dead(self):
        eng = load_engine()
        files = {"x/SKILL.md": "load references/used.md when needed", "x/references/used.md": "# U\nstuff"}
        self.assertEqual(eng.find_dead_refs(files), [])

    def test_non_reference_file_ignored(self):
        eng = load_engine()
        files = {"x/SKILL.md": "body", "CLAUDE.md": "guide"}
        self.assertEqual(eng.find_dead_refs(files), [])


class Bloat(unittest.TestCase):
    def test_oversized_skill_flagged(self):
        eng = load_engine()
        body = "\n".join(f"line {i}" for i in range(eng.BLOAT_BUDGET_LINES + 5))
        files = {"x/SKILL.md": f"---\nname: x\n---\n{body}"}
        self.assertIn("LA-BLOAT-1", {f.code for f in eng.scan_bloat(files)})

    def test_compact_skill_ok(self):
        eng = load_engine()
        files = {"x/SKILL.md": "---\nname: x\n---\n# X\nshort body"}
        self.assertEqual(eng.scan_bloat(files), [])

    def test_frontmatter_excluded(self):
        eng = load_engine()
        fm = "\n".join(f"k{i}: v" for i in range(300))
        files = {"x/SKILL.md": f"---\n{fm}\n---\n# X\nshort"}
        self.assertEqual(eng.scan_bloat(files), [])

    def test_non_skill_ignored(self):
        eng = load_engine()
        big = "\n".join(f"l{i}" for i in range(300))
        files = {"x/references/r.md": big}
        self.assertEqual(eng.scan_bloat(files), [])


if __name__ == "__main__":
    unittest.main()
