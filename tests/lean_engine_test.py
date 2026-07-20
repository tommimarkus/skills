import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import (
    REPO_ROOT,
    assert_precision_recall_at_least,
    classify_tp_fp_fn,
    load_script_module,
    run_git,
)

ENGINE = REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit" / "references" / "scripts" / "lean_engine.py"
LEDGER = REPO_ROOT / "tests" / "lean_engine_ledger.jsonl"


def load_engine():
    return load_script_module("lean_engine", ENGINE)


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


class Slugify(unittest.TestCase):
    def test_github_double_hyphen_around_removed_punctuation(self):
        eng = load_engine()
        # GitHub drops "&" then hyphenates EACH space: "A & B" -> "a--b", not "a-b".
        self.assertEqual(eng.slugify("Notation Rendering & Render Metadata"),
                         "notation-rendering--render-metadata")

    def test_plain_heading(self):
        eng = load_engine()
        self.assertEqual(eng.slugify("Git ignore hygiene (MUST)"), "git-ignore-hygiene-must")


class RegistryAndOverride(unittest.TestCase):
    def test_load_registry_carveouts(self):
        eng = load_engine()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".lean-audit.toml"
            p.write_text(
                'exempt_paths = ["vendor/**"]\n'                       # root key MUST precede table-arrays in TOML
                '[[canonical_home]]\npath = "CLAUDE.md"\nheading = "Git ignore hygiene (MUST)"\n'
                '[[carve_out]]\na = "**/skills/{skill}/extensions/**/*.md"\nb = "**/skills/{skill}/extensions/**/*.md"\n',
                encoding="utf-8")
            reg = eng.load_registry(p)
            self.assertIn(("CLAUDE.md", "Git ignore hygiene (MUST)"), reg.canonical_homes)
            self.assertEqual(reg.carve_outs,
                (("**/skills/{skill}/extensions/**/*.md", "**/skills/{skill}/extensions/**/*.md"),))
            self.assertEqual(reg.exempt_paths, ("vendor/**",))

    def test_missing_registry_is_empty(self):
        eng = load_engine()
        reg = eng.load_registry(None)
        self.assertEqual(reg.canonical_homes, ())
        self.assertEqual(reg.carve_outs, ())
        self.assertEqual(reg.exempt_paths, ())

    def test_override_marker(self):
        eng = load_engine()
        self.assertTrue(eng.has_override("text <!-- lean-audit:sync-intentional: mirrors manifest -->"))
        self.assertFalse(eng.has_override("plain text"))


class Scoring(unittest.TestCase):
    def _idx(self, eng, body_a, body_b, path_a="a/SKILL.md", path_b="CLAUDE.md"):
        return eng.build_index({path_a: f"# A\n{body_a}", path_b: f"# Home\n{body_b}"})

    def _section_a(self, eng):
        words = " ".join(f"w{i}" for i in range(40))
        idx = self._idx(eng, words, words)
        a = [s for s in idx if s.path == "a/SKILL.md"][0]
        return a, idx

    def _assert_no_finding_for_pair(self, eng, path_a: str, path_b: str) -> None:
        words = " ".join(f"w{i}" for i in range(40))
        idx = eng.build_index({path_a: f"# A\n{words}", path_b: f"# B\n{words}"})
        a = [s for s in idx if s.path == path_a][0]
        self.assertIsNone(eng.score_section(a, idx, eng.load_registry(None)))

    def test_high_band_cross_file_is_block_dup1(self):
        eng = load_engine()
        a, idx = self._section_a(eng)
        reg = eng.load_registry(None)
        f = eng.score_section(a, idx, reg)
        self.assertIsNotNone(f)
        self.assertEqual(f.code, "LA-DUP-1")
        self.assertEqual(f.severity, "block")
        self.assertEqual(f.matched_path, "CLAUDE.md")

    def test_canonical_home_match_is_dup2_with_cite(self):
        eng = load_engine()
        a, idx = self._section_a(eng)
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

    def test_carveout_exempts(self):
        eng = load_engine()
        # built-in subagent mirror
        self._assert_no_finding_for_pair(eng, "p/skills/x/SKILL.md", "p/agents/x.md")

    def test_wrapper_path_exempt_no_finding(self):
        eng = load_engine()
        self._assert_no_finding_for_pair(eng, ".claude/skills/x/SKILL.md", "internal-skills/x/SKILL.md")

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

    def test_full_path_emits_waste_codes(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "p/skills/x"
            base.mkdir(parents=True)
            body = "\n".join(f"line {i}" for i in range(260))
            (base / "SKILL.md").write_text(f"---\nname: x\n---\nsee [gone](missing.md)\n{body}", encoding="utf-8")
            (base / "references").mkdir()
            (base / "references" / "orphan.md").write_text("# Orphan\nunreferenced content here", encoding="utf-8")
            r = run_engine(d, "--format", "json")
            codes = {f["code"] for f in json.loads(r.stdout)["findings"]}
            self.assertIn("LA-STALE-1", codes)
            self.assertIn("LA-DEAD-1", codes)
            self.assertIn("LA-BLOAT-1", codes)
            self.assertEqual(r.returncode, 0)


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

    def test_github_style_double_hyphen_anchor_ok(self):
        eng = load_engine()
        # Regression: the "&" heading slugs to a double hyphen on GitHub; the
        # engine must resolve that anchor instead of emitting a false LA-STALE-1.
        files = {"a/SKILL.md": "see [t](b.md#notation-rendering--render-metadata)",
                 "a/b.md": "# Notation Rendering & Render Metadata\nx"}
        self.assertEqual(eng.scan_stale_refs(files), [])

    def test_url_and_mailto_skipped(self):
        eng = load_engine()
        files = {"a/SKILL.md": "[t](https://example.com/x) [m](mailto:a@b.c)"}
        self.assertEqual(eng.scan_stale_refs(files), [])

    def test_inline_code_links_skipped(self):
        eng = load_engine()
        files = {"a/SKILL.md": "use the pattern `[x](/nope/missing.md)` in examples"}
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
            tp, fp, fn = classify_tp_fp_fn(case["expect_block"], fired, tp, fp, fn)
        assert_precision_recall_at_least(self, tp, fp, fn)


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

    def test_exempt_path_is_not_dead(self):
        """exempt_paths must silence the dead-file lens too, not only duplication —
        eval corpora are referenced by directory, never by markdown link."""
        eng = load_engine()
        files = {"x/SKILL.md": "the workflow", "x/references/evals/corpus/orphan.md": "# O\nstuff"}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / ".lean-audit.toml"
            path.write_text('exempt_paths = ["x/references/evals/**"]\n', encoding="utf-8")
            reg = eng.load_registry(path)
        self.assertEqual(eng.find_dead_refs(files, reg), [])


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


class GuardGlobs(unittest.TestCase):
    def test_top_level_authoring_docs_are_guarded(self):
        eng = load_engine()
        for p in ("docs/skill-architecture.md", "docs/skill-evaluation.md",
                  "docs/release-checklist.md"):
            self.assertTrue(eng.is_guarded(p), f"{p} should be guarded")

    def test_docs_notes_drafts_not_guarded(self):
        # fnmatch '*' crosses '/', so a blanket docs glob would slurp the draft
        # tree; the authoring docs are listed explicitly so notes stay out.
        eng = load_engine()
        for p in ("docs/notes/2026-05-14-skills-lean-yagni-dry-review.md",
                  "docs/notes/archimate-32-conformity/00-index.md"):
            self.assertFalse(eng.is_guarded(p), f"{p} (draft) should not be guarded")


class CaptureGlob(unittest.TestCase):
    def test_segment_capture(self):
        eng = load_engine()
        self.assertEqual(eng.path_captures("{plugin}/skills/{skill}/SKILL.md",
            "souroldgeezer-audit/skills/lean-audit/SKILL.md"),
            {"plugin": "souroldgeezer-audit", "skill": "lean-audit"})

    def test_no_match(self):
        eng = load_engine()
        self.assertIsNone(eng.path_captures("{plugin}/agents/{skill}.md", "x/skills/y/SKILL.md"))

    def test_doublestar_zero_or_more_dirs(self):
        eng = load_engine()
        self.assertEqual(eng.path_captures("**/skills/{skill}/**/extensions/**/*.md",
            "p/skills/test-quality-audit/references/extensions/dotnet/core.md"),
            {"skill": "test-quality-audit"})
        self.assertEqual(eng.path_captures("**/skills/{skill}/**/extensions/**/*.md",
            "p/skills/api-design/extensions/azure-cosmosdb.md"),
            {"skill": "api-design"})

    def test_no_capture_match_returns_empty_dict(self):
        eng = load_engine()
        self.assertEqual(eng.path_captures(".claude/skills/**", ".claude/skills/lesson-capture/SKILL.md"), {})
        self.assertIsNone(eng.path_captures(".claude/skills/**", "souroldgeezer-audit/skills/x/SKILL.md"))

    def test_unclosed_brace_is_literal_no_crash(self):
        eng = load_engine()
        self.assertEqual(eng.path_captures("{plugin/x.md", "{plugin/x.md"), {})  # no ValueError; literal match
        self.assertIsNone(eng.path_captures("{plugin/x.md", "other/x.md"))


class CarveOuts(unittest.TestCase):
    def test_builtin_subagent_mirror_exempts_same_skill(self):
        eng = load_engine()
        reg = eng.load_registry(None)
        self.assertTrue(eng.carved_out(reg,
            "souroldgeezer-audit/skills/lean-audit/SKILL.md",
            "souroldgeezer-audit/agents/lean-audit.md"))

    def test_builtin_subagent_mirror_does_not_exempt_unrelated(self):
        eng = load_engine()
        reg = eng.load_registry(None)
        self.assertFalse(eng.carved_out(reg,
            "souroldgeezer-audit/skills/lean-audit/SKILL.md",
            "souroldgeezer-audit/agents/devsecops-audit.md"))   # {skill} differs
        self.assertFalse(eng.carved_out(reg,
            "a/skills/x/SKILL.md", "a/skills/z/SKILL.md"))       # two unrelated SKILL.md

    def test_builtin_wrapper_path_exempt(self):
        eng = load_engine()
        reg = eng.load_registry(None)
        self.assertTrue(eng.path_exempt(reg, ".claude/skills/lesson-capture/SKILL.md"))
        self.assertFalse(eng.path_exempt(reg, "souroldgeezer-audit/skills/x/SKILL.md"))

    def test_registry_pair_with_shared_capture(self):
        eng = load_engine()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".lean-audit.toml"
            p.write_text('[[carve_out]]\na = "**/skills/{skill}/**/extensions/**/*.md"\n'
                         'b = "**/skills/{skill}/**/extensions/**/*.md"\n', encoding="utf-8")
            reg = eng.load_registry(p)
        self.assertTrue(eng.carved_out(reg,
            "p/skills/tq/references/extensions/dotnet/core.md",
            "p/skills/tq/references/extensions/nodejs/core.md"))     # same {skill}=tq
        self.assertFalse(eng.carved_out(reg,
            "p/skills/tq/references/extensions/dotnet/core.md",
            "p/skills/other/references/extensions/nodejs/core.md"))  # {skill} differs

    def test_registry_pair_no_capture_any_pair(self):
        eng = load_engine()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".lean-audit.toml"
            p.write_text('[[carve_out]]\na = "**/references/procedures/project-assimilation.md"\n'
                         'b = "**/references/procedures/project-assimilation.md"\n', encoding="utf-8")
            reg = eng.load_registry(p)
        self.assertTrue(eng.carved_out(reg,
            "a/skills/x/references/procedures/project-assimilation.md",
            "b/skills/y/references/procedures/project-assimilation.md"))


class RepoResidual(unittest.TestCase):
    def _scan_repo(self, eng, extra_files: dict[str, str] | None = None):
        root = REPO_ROOT
        files = eng.read_repo(root, root)
        if extra_files:
            files = {**files, **extra_files}
        reg = eng.load_registry(root / ".lean-audit.toml")
        return [f for f in eng.scan(files, reg) if f.severity == "block"]

    def test_carveouts_suppress_intentional_categories(self):
        eng = load_engine()
        blocks = self._scan_repo(eng)
        pairs = {(f.path, f.matched_path) for f in blocks}
        # built-in subagent mirror gone:
        self.assertNotIn(("souroldgeezer-audit/skills/lean-audit/SKILL.md",
                          "souroldgeezer-audit/agents/lean-audit.md"), pairs)
        # wrapper class gone:
        self.assertFalse(any(p.startswith(".claude/skills/") or m.startswith(".claude/skills/")
                             for p, m in pairs))
        # same-skill extension pair gone:
        self.assertFalse(any("/extensions/" in p and "/extensions/" in m
                             and p.split("/skills/")[1].split("/")[0] == m.split("/skills/")[1].split("/")[0]
                             for p, m in pairs if "/skills/" in p and "/skills/" in m))
        # the residual stays bounded (live-repo dedup work drives this toward zero over time)
        self.assertLessEqual(len(blocks), 20)

    def test_scan_detects_injected_synthetic_duplication(self):
        # Positive control, not a live-repo pin: the repo's end-state is ZERO
        # block duplications, so any assertion pinned to a specific live finding
        # (e.g. the old quality-reference rubric family) goes stale the moment
        # that duplication is legitimately remediated (as it was in 1a9be56).
        # Injecting a synthetic guarded pair proves the scan pipeline still
        # detects real duplication without depending on what's currently unfixed.
        eng = load_engine()
        body = (
            "## Shared\n"
            "alpha beta gamma delta epsilon zeta eta theta iota kappa "
            "lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega alpha.\n"
        )
        path_a = "souroldgeezer-audit/docs/quality-reference/zz-synthetic-a.md"
        path_b = "souroldgeezer-audit/docs/quality-reference/zz-synthetic-b.md"
        self.assertTrue(eng.is_guarded(path_a))
        self.assertTrue(eng.is_guarded(path_b))
        blocks = self._scan_repo(eng, extra_files={path_a: body, path_b: body})
        pairs = {(f.path, f.matched_path) for f in blocks}
        self.assertIn((path_a, path_b), pairs)
        self.assertIn((path_b, path_a), pairs)


class EvaluateAddedBlock(unittest.TestCase):
    def _corpus(self, tmp):
        # one guarded SKILL.md with a substantial section
        a = Path(tmp) / "aud" / "skills" / "s1" / "SKILL.md"
        a.parent.mkdir(parents=True, exist_ok=True)
        a.write_text(
            "## Shared\n"
            + "alpha beta gamma delta epsilon zeta eta theta iota kappa "
            "lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega alpha.\n",
            encoding="utf-8",
        )
        return Path(tmp)

    def test_duplicate_added_block_is_block_finding(self):
        import tempfile
        eng = load_engine()
        with tempfile.TemporaryDirectory() as tmp:
            root = self._corpus(tmp)
            block = (
                "## Shared\n"
                "alpha beta gamma delta epsilon zeta eta theta iota kappa "
                "lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega alpha."
            )
            findings = eng.evaluate_added_block(
                root, "aud/skills/s2/SKILL.md", block, None
            )
            self.assertTrue(any(f.severity == "block" for f in findings))

    def test_unique_added_block_has_no_finding(self):
        import tempfile
        eng = load_engine()
        with tempfile.TemporaryDirectory() as tmp:
            root = self._corpus(tmp)
            block = (
                "## Fresh\nThis section introduces entirely original vocabulary covering "
                "deployment pipelines caching strategies network retries observability "
                "dashboards rollout guards and telemetry that overlaps nothing present in "
                "the shared corpus today whatsoever."
            )
            findings = eng.evaluate_added_block(
                root, "aud/skills/s2/SKILL.md", block, None
            )
            self.assertEqual(findings, [])


class MalformedCarveOut(unittest.TestCase):
    def test_bad_carveout_capture_key_exits_2(self):
        """A carve_out with an invalid Python group name ({bad-key}) must exit cleanly, not crash."""
        eng = load_engine()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            # Two guarded files with HIGH-BAND overlap so carved_out() is actually invoked
            words = " ".join(f"w{i}" for i in range(40))
            (root / "CLAUDE.md").write_text(f"# Home\n{words}\n", encoding="utf-8")
            (root / "README.md").write_text(f"# Overview\n{words}\n", encoding="utf-8")
            # Registry with an invalid Python regex group name (hyphen in capture key)
            bad_toml = root / ".lean-audit.toml"
            bad_toml.write_text(
                '[[carve_out]]\na = "{bad-key}/x.md"\nb = "{bad-key}/y.md"\n',
                encoding="utf-8",
            )
            result = eng.main([str(root), "--registry", str(bad_toml)])
            self.assertEqual(result, 2)


class GitAwareReadRepo(unittest.TestCase):
    def test_read_repo_excludes_ignored_nested_worktree(self):
        # Use .claude/worktrees/ as the ghost location: it is in .gitignore in
        # the real repo but NOT in _EXCLUDE, so only the git-membership gate
        # (repo_paths) can exclude it.  This proves the git-aware fix does work;
        # using .worktrees/ (which IS in _EXCLUDE) would pass even without the fix.
        eng = load_engine()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            real = root / "aud" / "skills" / "s1" / "SKILL.md"
            real.parent.mkdir(parents=True)
            real.write_text("## H\n" + "word " * 60 + "\n", encoding="utf-8")
            run_git(root, "init", "-q")
            run_git(root, "add", "-A")
            run_git(root, "-c", "user.email=t@t", "-c", "user.name=t",
                    "-c", "commit.gpgsign=false",
                    "commit", "-qm", "init")
            (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
            ghost = root / ".claude" / "worktrees" / "b" / "aud" / "skills" / "s1" / "SKILL.md"
            ghost.parent.mkdir(parents=True)
            ghost.write_text("## H\n" + "word " * 60 + "\n", encoding="utf-8")
            files = eng.read_repo(root.resolve(), root.resolve())
            self.assertIn("aud/skills/s1/SKILL.md", files)
            self.assertNotIn(".claude/worktrees/b/aud/skills/s1/SKILL.md", files)

    def test_read_repo_falls_back_without_git(self):
        eng = load_engine()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "aud" / "skills" / "s1" / "SKILL.md"
            real.parent.mkdir(parents=True)
            real.write_text("## H\n" + "word " * 60 + "\n", encoding="utf-8")
            ghost = root / ".worktrees" / "b" / "SKILL.md"
            ghost.parent.mkdir(parents=True)
            ghost.write_text("## H\n" + "word " * 60 + "\n", encoding="utf-8")
            files = eng.read_repo(root, root)
            self.assertIn("aud/skills/s1/SKILL.md", files)


class GitEnumerationParityTest(unittest.TestCase):
    """The bundled lean engine cannot import repo tooling, so the git ls-files
    enumeration block is intentionally duplicated with skill_architecture_report.py.
    This test fails when the two copies drift."""

    @staticmethod
    def _enumeration_block(path: Path) -> str:
        text = path.read_text(encoding="utf-8")
        start = text.index('["git", "-C"')
        end = text.index("return frozenset", start)
        block = text[start:end]
        block = block.replace("repo_root_str", "ROOT").replace("str(root)", "ROOT")
        # The report engine takes repo_root_str: str (lru_cache needs a hashable
        # key), so its toplevel check wraps in Path(...); the bundled engine takes
        # root: Path directly and calls .resolve() bare. Same comparison, cosmetic
        # difference driven by the two functions' parameter types, not drift.
        block = block.replace("Path(ROOT).resolve()", "ROOT.resolve()")
        block = block.replace("root.resolve()", "ROOT.resolve()")
        return " ".join(block.split())

    def test_git_enumeration_matches_report_engine(self) -> None:
        engine = REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/references/scripts/leanaudit/discovery.py"
        report = REPO_ROOT / "scripts/skill_architecture_report.py"
        self.assertEqual(self._enumeration_block(engine), self._enumeration_block(report))


class RegistryWarningTest(unittest.TestCase):
    def test_missing_registry_path_warns_on_stderr(self):
        proc = subprocess.run(
            [sys.executable, str(ENGINE), ".", "--registry", "/nonexistent/reg.toml",
             "--format", "json"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        self.assertIn("not found", proc.stderr.lower())

    def test_default_run_without_registry_toml_is_silent(self):
        # Regression: the warning must gate on an EXPLICIT --registry flag only.
        # A default run in a repo without .lean-audit.toml (call sites always
        # compute root/.lean-audit.toml before load_registry) must stay silent,
        # or every downstream run — including the PreToolUse guard hot path —
        # emits noise.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "CLAUDE.md").write_text(
                "# Home\nunique alpha bravo charlie\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(ENGINE), d, "--format", "json"],
                capture_output=True, text=True, cwd=REPO_ROOT,
            )
            self.assertEqual(proc.stderr, "")
            self.assertIn(proc.returncode, (0, 1))

    def test_evaluate_added_block_without_registry_toml_is_silent(self):
        # The guard path (evaluate_added_block with registry=None) defaults to
        # root/.lean-audit.toml internally; a missing toml must not warn.
        eng = load_engine()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sk = root / "aud" / "skills" / "s1" / "SKILL.md"
            sk.parent.mkdir(parents=True)
            sk.write_text("## H\n" + "word " * 60 + "\n", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                eng.evaluate_added_block(
                    root, "aud/skills/s2/SKILL.md", "## Fresh\nnothing shared", None)
            self.assertEqual(buf.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
