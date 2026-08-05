# lean-audit:dup-intentional — one-factor detector fixtures; the shared corpus builders (stream/toks/words/run_lens/_discover) are already extracted, and each remaining parallel is a test body varying a single corpus or CLI factor that must stay explicit
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
)

LENS = REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit" / "references" / "scripts" / "code_lens.py"
LEDGER = REPO_ROOT / "tests" / "lean_code_ledger.jsonl"
CLONES = REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit" / "references" / "scripts" / "leanaudit" / "clones.py"


def load_lens():
    return load_script_module("code_lens", LENS)


def load_clones_mod():
    load_lens()  # populates sys.path with scripts/ so `leanaudit.*` package imports resolve
    return load_script_module("leanaudit_clones", CLONES)


def run_lens(*args, stdin=None):
    return subprocess.run([sys.executable, str(LENS), *args],
                          cwd=REPO_ROOT, input=stdin, capture_output=True, text=True, check=False)


def stream(lens, text, ext=".py"):
    """Tokenize text with the profile for ext (the (token, line) pair stream)."""
    return lens.strip_and_tokenize(text, lens.profile_for(ext))


def toks(text, ext):
    """Just the token strings for text under the profile for ext."""
    return [t for t, _ in stream(load_lens(), text, ext)]


def words(n, prefix="t"):
    """A synthetic n-token corpus body of distinct identifiers."""
    return " ".join(f"{prefix}{i}" for i in range(n))


def marker(suffix="", opener="#"):
    """A line comment carrying the dup-intentional marker (+ optional :begin/:end)."""
    return f"{opener} {load_lens().INTENTIONAL_MARKER}{suffix}\n"


def logic_body(name):
    """~64 matched tokens of identifier-rich logic — a block clone at min-tokens 20.
    Mirrors the LCD-T0009+ ledger fixtures so unit and calibration cases agree."""
    return (f"def {name}(items, cfg):\n"
            "    total = 0\n"
            "    for item in items:\n"
            "        value = transform(item.data, cfg.scale)\n"
            "        total = total + value\n"
            "    result = finalize(total, cfg.mode)\n"
            "    logger.record(cfg.name, result)\n"
            "    cache.store(cfg.key, result)\n"
            "    return result\n")


def other_body(name):
    """A second block-clone body sharing no identifiers with logic_body, so the two
    never extend into one another (the `SEP_*` line between them breaks the run)."""
    return (f"def {name}(rows, opts):\n"
            "    out = []\n"
            "    for row in rows:\n"
            "        cell = format_cell(row.text, opts.width)\n"
            "        out.append(cell)\n"
            "    joined = join_all(out, opts.sep)\n"
            "    printer.emit(opts.stream, joined)\n"
            "    buffer.flush(opts.stream, joined)\n"
            "    return joined\n")


def scan_files(contents, min_tokens=20):
    """Run the real scan_dir over a temp tree — discovery, marker handling, region
    post-filter and dedupe included (never a re-implementation of any of them)."""
    clones_mod = load_clones_mod()
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for rel, text in contents.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return clones_mod.scan_dir(root, min_tokens, None)


class Tokenizer(unittest.TestCase):
    def test_strips_line_and_block_comments(self):
        self.assertEqual(toks("a = 1 // hi\n/* x */ b = 2\n", ".js"),
                         ["a", "=", "NUM", "b", "=", "NUM"])

    def test_string_and_number_normalized(self):
        self.assertEqual(toks('x = "hello" + 42', ".py"),
                         ["x", "=", "STR", "+", "NUM"])

    def test_line_numbers_tracked(self):
        lens = load_lens()
        prof = lens.profile_for(".py")
        pairs = lens.strip_and_tokenize("a\n\nb", prof)
        self.assertEqual(pairs, [("a", 1), ("b", 3)])

    def test_unknown_extension_uses_generic_profile(self):
        lens = load_lens()
        self.assertEqual(lens.profile_for(".zzz"), lens.GENERIC_PROFILE)


class Clones(unittest.TestCase):
    def _cross_file_clones(self, n: int, min_tokens: int = 8):
        lens = load_lens()
        body = words(n)
        streams = {"a.py": stream(lens, body), "b.py": stream(lens, body)}
        return lens.find_clones(streams, min_tokens=min_tokens)

    def test_verbatim_cross_file_clone_blocks(self):
        clones = self._cross_file_clones(30)                # 30 >= 2*8
        self.assertTrue(clones)
        c = clones[0]
        self.assertEqual(c.severity, "block")
        self.assertEqual(c.code, "LA-CODE-DUP-1")
        self.assertEqual({c.path, c.matched_path}, {"a.py", "b.py"})
        self.assertEqual(c.tokens, 30)

    def test_midband_clone_is_info(self):
        clones = self._cross_file_clones(10)                # 10 tokens: 8 <= 10 < 16
        self.assertEqual(clones[0].severity, "info")
        self.assertEqual(clones[0].code, "LA-CODE-DUP-2")

    def test_below_threshold_no_clone(self):
        lens = load_lens()
        body = words(5)
        streams = {"a.py": stream(lens, body), "b.py": stream(lens, body)}
        self.assertEqual(lens.find_clones(streams, min_tokens=8), [])

    def test_distinct_files_no_clone(self):
        lens = load_lens()
        streams = {"a.py": stream(lens, words(30, "a")),
                   "b.py": stream(lens, words(30, "b"))}
        self.assertEqual(lens.find_clones(streams, min_tokens=8), [])

    def test_intra_file_nonoverlapping_clone(self):
        lens = load_lens()
        block = words(12)
        streams = {"a.py": stream(lens, block + " sep " + block)}
        clones = lens.find_clones(streams, min_tokens=8)
        self.assertTrue(clones)
        self.assertEqual(clones[0].path, "a.py")
        self.assertEqual(clones[0].matched_path, "a.py")

    def test_comment_only_difference_still_clone(self):
        lens = load_lens()
        body = words(20)
        streams = {"a.py": stream(lens, "# header\n" + body),
                   "b.py": stream(lens, body + "\n# trailer")}
        self.assertTrue(lens.find_clones(streams, min_tokens=8))

    def test_windows_straddling_file_boundaries_do_not_crash(self):
        # Each file is shorter than the window; the global token stream
        # concatenates files, so a naive seed window straddles a file boundary.
        # Must not raise IndexError and must report no (phantom cross-file) clone.
        lens = load_lens()
        streams = {f"f{n}.py": stream(lens, "a b c") for n in range(3)}
        self.assertEqual(lens.find_clones(streams, min_tokens=4), [])


class Discovery(unittest.TestCase):
    def _discover(self, lens, contents: dict[str, str], exempt: tuple = ()) -> dict:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for rel, text in contents.items():
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            return lens.read_sources(root, lens.DEFAULT_EXTENSIONS, exempt)

    def test_reads_only_source_extensions(self):
        lens = load_lens()
        files = self._discover(lens, {"a.py": "x = 1\n", "notes.md": "# md\n"})
        self.assertIn("a.py", files)
        self.assertNotIn("notes.md", files)

    def test_excludes_vendored_dirs(self):
        lens = load_lens()
        files = self._discover(lens, {
            "node_modules/v.js": "var x = 1\n",
            "keep.js": "var y = 2\n",
        })
        self.assertEqual(list(files), ["keep.js"])

    def test_exempt_path_and_marker_suppressed(self):
        lens = load_lens()
        files = self._discover(
            lens,
            {"gen.py": "x = 1\n", "b.py": f"# {lens.INTENTIONAL_MARKER}\ny = 2\n"},
            exempt=("gen.py",),
        )
        self.assertNotIn("gen.py", files)      # exempt_paths
        self.assertNotIn("b.py", files)        # whole-file (suffix-less) inline marker

    def test_bare_marker_string_is_not_a_whole_file_marker(self):
        # The engine's own INTENTIONAL_MARKER = "..." assignment must not exempt
        # the module that defines it (only a LINE COMMENT declares the marker).
        lens = load_lens()
        files = self._discover(lens, {"m.py": f'MARK = "{lens.INTENTIONAL_MARKER}"\n'})
        self.assertIn("m.py", files)

    def test_region_marked_file_stays_in_corpus(self):
        # A :begin/:end pair scopes suppression to a span; the file itself is still
        # tokenized (the post-filter in scan_dir drops only the contained clones).
        lens = load_lens()
        files = self._discover(lens, {"r.py": marker(":begin") + "y = 2\n" + marker(":end")})
        self.assertIn("r.py", files)

    def test_load_config_defaults_when_no_registry(self):
        lens = load_lens()
        exempt, exts = lens.load_config(None)
        self.assertEqual(exempt, ())
        self.assertEqual(exts, lens.DEFAULT_EXTENSIONS)


class Cli(unittest.TestCase):
    def test_json_and_exit1_on_block(self):
        with tempfile.TemporaryDirectory() as d:
            body = words(30) + "\n"
            (Path(d) / "a.py").write_text(body, encoding="utf-8")
            (Path(d) / "b.py").write_text(body, encoding="utf-8")
            r = run_lens(d, "--min-tokens", "8", "--format", "json")
            self.assertEqual(r.returncode, 1)
            codes = {f["code"] for f in json.loads(r.stdout)["findings"]}
            self.assertIn("LA-CODE-DUP-1", codes)

    def test_clean_tree_exit0(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.py").write_text(words(30, "a") + "\n", encoding="utf-8")
            (Path(d) / "b.py").write_text(words(30, "b") + "\n", encoding="utf-8")
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
        # The bar must validate the threshold the tool actually ships with, not an
        # arbitrary one — SKILL.md invokes code_lens.py with no --min-tokens.
        self.assertTrue(all(c["min_tokens"] == lens.DEFAULT_MIN_CLONE_TOKENS for c in cases),
                        "ledger must calibrate at the shipped default min-tokens")
        tp = fp = fn = 0
        for case in cases:
            # Drive the real scan_dir. Re-deriving suppression here would calibrate
            # the ledger against a stand-in instead of the shipped engine.
            clones = scan_files({f["path"]: f["content"] for f in case["files"]},
                                case["min_tokens"])
            fired = any(c.severity == "block" for c in clones)
            tp, fp, fn = classify_tp_fp_fn(case["expect_block"], fired, tp, fp, fn)
        assert_precision_recall_at_least(self, tp, fp, fn)


class TokenizerFixes(unittest.TestCase):
    def test_kotlin_swift_php_scala_have_comment_profiles(self):
        lens = load_lens()
        for ext in (".kt", ".swift", ".php", ".scala"):
            self.assertIsNot(lens.profile_for(ext), lens.GENERIC_PROFILE,
                             f"{ext} must strip comments")
            self.assertEqual(toks("x = 1 // note", ext), ["x", "=", "NUM"])
        # PHP also treats `#` as a line comment.
        self.assertEqual(toks("$x = 1 # note", ".php"), ["$", "x", "=", "NUM"])

    def test_identical_license_header_is_not_a_clone(self):
        lens = load_lens()
        header = "\n".join("// " + w for w in ("Copyright the demo project contributors "
                 "this banner block is repeated verbatim atop every sibling file purely "
                 "as decorative boilerplate and carries no shared program logic").split())
        a = header + "\nfun alpha() { return readAlpha().value }\n"
        b = header + "\nclass Beta { fun gamma() { return this.delta.times(2) } }\n"
        streams = {"a.kt": stream(lens, a, ".kt"), "b.kt": stream(lens, b, ".kt")}
        self.assertEqual(lens.find_clones(streams, 20), [],
                         "shared comment header must not tokenize into a clone")

    def test_go_raw_string_preserves_following_tokens(self):
        got = toks("x = `a\\`\ny = load()\n", ".go")
        self.assertIn("y", got)           # a `\` in a raw string must not swallow the rest
        self.assertIn("load", got)

    def test_triple_quoted_string_value_is_single_token(self):
        self.assertEqual(toks('sql = """SELECT a FROM t"""', ".py"),
                         ["sql", "=", "STR"])
        # a bare docstring collapses to one STR too (not deleted)
        self.assertEqual(toks('"""module doc"""\nx = 1', ".py"),
                         ["STR", "x", "=", "NUM"])

    def test_ruby_begin_midline_is_not_a_block_comment(self):
        got = toks("x=begin\n  risky\nend\nz = 1", ".rb")
        self.assertIn("z", got)           # mid-line =begin must not swallow the file
        # a real column-0 =begin block is still stripped
        self.assertEqual(toks("=begin\n comment\n=end\nz = 1", ".rb"),
                         ["z", "=", "NUM"])

    def test_string_backslash_newline_counts_line(self):
        pairs = stream(load_lens(), 'a = "x\\\ny"\nb = 1\n')
        b_line = next(ln for tok, ln in pairs if tok == "b")
        self.assertEqual(b_line, 3, "line continuation inside a string must advance the line")

    def test_numeric_literals_normalized(self):
        for lit in ("0xFF", "0b1010", "1_000", "1e9"):
            self.assertEqual(toks(f"x = {lit}", ".py"), ["x", "=", "NUM"],
                             f"{lit} should normalize to NUM")
        # identifiers that merely look numeric are left alone
        self.assertEqual(toks("cafe = 1", ".py"), ["cafe", "=", "NUM"])


class ExclusionFixes(unittest.TestCase):
    def test_substring_dir_not_excluded(self):
        clones_mod = load_clones_mod()
        self.assertFalse(clones_mod._is_excluded("src/mydist/a.py"))
        self.assertFalse(clones_mod._is_excluded("app/rebuild/x.py"))
        self.assertFalse(clones_mod._is_excluded("svc/subtarget/y.py"))

    def test_exact_segment_dir_still_excluded(self):
        clones_mod = load_clones_mod()
        self.assertTrue(clones_mod._is_excluded("dist/a.py"))
        self.assertTrue(clones_mod._is_excluded("pkg/node_modules/x.js"))
        self.assertTrue(clones_mod._is_excluded(".claude/worktrees/w/x.py"))


class CloneLogicFixes(unittest.TestCase):
    def test_min_tokens_below_one_raises(self):
        lens = load_lens()
        with self.assertRaises(ValueError):
            lens.find_clones({"a.py": stream(lens, "a b c")}, 0)

    def test_periodic_blocks_reported_once(self):
        lens = load_lens()
        block = words(25)
        streams = {"a.py": stream(lens, "\n".join([block, block, block, block]))}
        clones = lens.find_clones(streams, 25)
        # no smaller clone whose region nests inside a larger one on the same file
        for c in clones:
            lo, hi = (int(x) for x in c.lines.split("-"))
            for o in clones:
                if o is c or o.path != c.path or o.tokens <= c.tokens:
                    continue
                olo, ohi = (int(x) for x in o.lines.split("-"))
                self.assertFalse(olo <= lo and hi <= ohi, "nested duplicate not deduped")

    def test_distinct_crossfile_clones_not_deduped(self):
        lens = load_lens()
        big = words(40)
        small = words(10)                                 # ⊂ big's token run
        streams = {"a.py": stream(lens, big),
                   "b.py": stream(lens, big),
                   "c.py": stream(lens, small)}
        clones = lens.find_clones(streams, 8)
        pairs = {frozenset((c.path, c.matched_path)) for c in clones}
        self.assertIn(frozenset(("a.py", "b.py")), pairs)
        self.assertIn(frozenset(("a.py", "c.py")), pairs)   # distinct pair survives dedup


class CliFixes(unittest.TestCase):
    def test_min_tokens_zero_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.py").write_text("x = 1\n", encoding="utf-8")
            r = run_lens(d, "--min-tokens", "0", "--format", "json")
            self.assertEqual(r.returncode, 2)

    def test_missing_registry_warns_but_scans(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.py").write_text("x = 1\n", encoding="utf-8")
            missing = str(Path(d) / "nope.toml")
            r = run_lens(d, "--registry", missing, "--format", "json")
            self.assertEqual(r.returncode, 0)
            self.assertIn("not found", r.stderr)
            self.assertEqual(json.loads(r.stdout)["findings"], [])

    def test_kotlin_header_only_clone_exits_0(self):
        with tempfile.TemporaryDirectory() as d:
            header = "\n".join("// " + w for w in
                     ("licensed banner text repeated verbatim at the top of every "
                      "source file in this module for legal boilerplate reasons").split())
            (Path(d) / "a.kt").write_text(header + "\nfun a() { return one() }\n", encoding="utf-8")
            (Path(d) / "b.kt").write_text(header + "\nfun b() { return two().x }\n", encoding="utf-8")
            r = run_lens(d, "--format", "json")
            self.assertEqual(r.returncode, 0)
            self.assertEqual(json.loads(r.stdout)["findings"], [])


class MarkerRegionsTest(unittest.TestCase):
    """`:begin`/`:end` region spans, read off the RAW text (markers are comments,
    which the tokenizer strips). Spans are 1-based and inclusive of both markers."""

    def _regions(self, text, ext=".py"):
        clones_mod = load_clones_mod()
        return clones_mod._marked_regions(text, clones_mod.profile_for(ext))

    def test_balanced_pair_spans_both_marker_lines(self):
        self.assertEqual(self._regions(marker(":begin") + "x = 1\n" + marker(":end") + "y = 2\n"),
                         ((1, 3),))

    def test_two_pairs_are_separate_spans(self):
        text = (marker(":begin") + "a = 1\n" + marker(":end")
                + "gap = 2\n" + marker(":begin") + "b = 3\n" + marker(":end"))
        self.assertEqual(self._regions(text), ((1, 3), (5, 7)))

    def test_unbalanced_begin_runs_to_eof(self):
        self.assertEqual(self._regions(marker(":begin") + "a = 1\nb = 2\n"), ((1, 3),))

    def test_nested_begin_closes_only_at_outer_end(self):
        text = (marker(":begin") + "a = 1\n" + marker(":begin") + marker(":end")
                + "b = 2\n" + marker(":end"))
        self.assertEqual(self._regions(text), ((1, 6),))

    def test_stray_end_without_begin_is_ignored(self):
        self.assertEqual(self._regions("a = 1\n" + marker(":end") + "b = 2\n"), ())

    def test_plain_marker_opens_no_region(self):
        self.assertEqual(self._regions(marker(" — rationale") + "a = 1\n"), ())

    def test_bare_string_assignment_opens_no_region(self):
        lens = load_lens()
        self.assertEqual(self._regions(f'MARK = "{lens.INTENTIONAL_MARKER}:begin"\na = 1\n'), ())

    def test_c_family_uses_its_own_line_comment_opener(self):
        text = marker(":begin", "//") + "var a = 1\n" + marker(":end", "//")
        self.assertEqual(self._regions(text, ".js"), ((1, 3),))
        self.assertEqual(self._regions(text, ".py"), (),
                         "a `//` comment is not a marker in a `#`-comment language")


class MarkerSuppressionScopeTest(unittest.TestCase):
    """End-to-end suppression through scan_dir: whole-file markers stay file-wide,
    region markers suppress only clones fully CONTAINED in one marked span, and
    either side of a pair may carry the declaration."""

    def test_whole_file_marker_still_suppresses_everything(self):
        found = scan_files({"a.py": logic_body("process"),
                            "b.py": marker(" — rationale") + logic_body("handle")})
        self.assertEqual(found, [])

    def test_bare_marker_assignment_does_not_suppress(self):
        lens = load_lens()
        found = scan_files({
            "a.py": logic_body("process"),
            "b.py": f'INTENTIONAL_MARKER = "{lens.INTENTIONAL_MARKER}"\n' + logic_body("handle"),
        })
        self.assertTrue(found, "a marker in a string literal must not exempt the file")

    def test_region_suppresses_only_its_own_span(self):
        found = scan_files({
            "a.py": logic_body("process") + "SEP_ALPHA = 1\n" + other_body("render"),
            "b.py": (marker(":begin") + logic_body("handle") + marker(":end")
                     + "SEP_BETA = 2\n" + other_body("draw")),
        })
        paths = {(c.path, c.matched_path) for c in found}
        self.assertEqual(paths, {("a.py", "b.py")}, "one surviving cross-file pair")
        # the surviving clone is the one OUTSIDE the region (the `draw`/`render` body)
        self.assertTrue(all(int(c.matched_lines.split("-")[0]) > 12 for c in found), found)

    def test_region_on_either_side_suppresses_the_pair(self):
        wrapped = marker(":begin") + logic_body("process") + marker(":end")
        self.assertEqual(scan_files({"a.py": wrapped, "b.py": logic_body("handle")}), [])
        self.assertEqual(scan_files({"a.py": logic_body("handle"), "b.py": wrapped}), [])

    def test_clone_only_partly_inside_a_region_is_not_suppressed(self):
        # Containment, not overlap: a one-line marked touch must not kill the clone.
        body = logic_body("handle")
        head, tail = body.split("\n", 1)
        found = scan_files({
            "a.py": logic_body("process"),
            "b.py": marker(":begin") + head + "\n" + marker(":end") + tail,
        })
        self.assertTrue(found, "a region covering only part of the clone must not suppress it")

    def test_unbalanced_begin_suppresses_to_end_of_file(self):
        found = scan_files({"a.py": logic_body("process"),
                            "b.py": marker(":begin") + logic_body("handle")})
        self.assertEqual(found, [])


class LiteralListFalsePositiveTest(unittest.TestCase):
    """Declarative literal lists must not clone-match: __all__ blocks, path lists."""

    def _scan_two(self, body_a: str, body_b: str) -> list:
        return scan_files({"a.py": body_a, "b.py": body_b})

    def test_two_long_string_lists_do_not_match(self) -> None:
        names = ", ".join(f'"name_{i}"' for i in range(30))
        paths = ", ".join(f'"pkg/path/{i}.json"' for i in range(30))
        found = self._scan_two(f"__all__ = [{names}]\n", f"required = [{paths}]\n")
        self.assertEqual(found, [])

    def test_genuine_logic_clone_still_detected(self) -> None:
        logic = (
            "def resolve(root, name, table, fallback):\n"
            "    entry = table.get(name)\n"
            "    if entry is None:\n"
            "        entry = fallback(root, name)\n"
            "        table[name] = entry\n"
            "    for item in entry.parts:\n"
            "        if item.kind == 'dir':\n"
            "            yield item.path\n"
            "    return entry\n"
        )
        found = self._scan_two(logic, logic)
        self.assertTrue(found, "identifier-rich logic clone must still be reported")
