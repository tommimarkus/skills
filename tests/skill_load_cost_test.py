# lean-audit:dup-intentional — one-factor CLI and guard fixtures; the shared run_cli/_fixture_entry/_run_resolve_closure/_guard helpers are already extracted, and each remaining parallel is a per-subcommand or per-token-class variant whose explicit inline fixture is the assertion
# tests/skill_load_cost_test.py
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, load_script_module

SCRIPT = (REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit"
          / "references" / "scripts" / "skill_load_cost.py")

# Load the script by path — repo convention (no `scripts/__init__.py`), matching
# tests/skill_architecture_report_test.py and tests/lessons_issue_test.py.
slc = load_script_module("skill_load_cost", SCRIPT)


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run the skill_load_cost.py shim CLI in a subprocess with the given args."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
    )


class EstimateTokensTest(unittest.TestCase):
    def test_counts_words_and_punctuation_separately(self):
        # "a, b c." -> a , b c .  == 5 tokens
        self.assertEqual(slc.estimate_tokens("a, b c."), 5)

    def test_is_deterministic_and_empty_safe(self):
        self.assertEqual(slc.estimate_tokens(""), 0)
        self.assertEqual(slc.estimate_tokens("word"), slc.estimate_tokens("word"))


class MeasureScenarioTest(unittest.TestCase):
    def test_sums_tokens_across_declared_files(self):
        root = Path(__file__).parent / "skill_load_cost" / "fixtures"
        scenario = {"id": "t", "files": ["alpha.md", "beta.md"]}
        result = slc.measure_scenario(scenario, root)
        self.assertEqual(result["id"], "t")
        self.assertEqual(len(result["rows"]), 2)
        self.assertEqual(
            result["total"],
            result["rows"][0]["tokens"] + result["rows"][1]["tokens"],
        )


CODE_PATTERNS = [r"nodejs\.(?:HC|LC|POS)-\d+", r"\bHC-\d+"]


class ExtractInventoryTest(unittest.TestCase):
    def test_pulls_codes_sections_and_pointers(self):
        text = (
            "# Title\n\n## Detection signals\n\n"
            "nodejs.HC-1 and HC-2 here.\n\nSee [home](../nodejs/core.md).\n"
        )
        inv = slc.extract_inventory(text, CODE_PATTERNS)
        self.assertIn("nodejs.HC-1", inv["codes"])
        self.assertIn("HC-2", inv["codes"])
        self.assertIn("Detection signals", inv["sections"])
        self.assertIn("../nodejs/core.md", inv["pointers"])

    def test_union_dedupes_across_files(self):
        a = {"codes": ["HC-1"], "sections": ["S"], "pointers": []}
        b = {"codes": ["HC-1", "HC-2"], "sections": ["S", "T"], "pointers": []}
        u = slc.union_inventory([a, b])
        self.assertEqual(u["codes"], ["HC-1", "HC-2"])
        self.assertEqual(u["sections"], ["S", "T"])

    def test_ignores_links_inside_code_spans(self):
        text = (
            "Real [a](real.md).\n"
            "Inline code: `](fake.md)` and `(?P<route>[^)]+)`.\n\n"
            "```\n](fenced.md)\n```\n"
        )
        inv = slc.extract_inventory(text, CODE_PATTERNS)
        self.assertIn("real.md", inv["pointers"])
        self.assertNotIn("fake.md", inv["pointers"])
        self.assertNotIn("fenced.md", inv["pointers"])


class DiffInventoryTest(unittest.TestCase):
    def test_flags_dropped_codes_and_sections(self):
        baseline = {"codes": ["HC-1", "HC-2"], "sections": ["S", "T"]}
        current = {"codes": ["HC-1"], "sections": ["S"]}
        problems = slc.diff_inventory(baseline, current)
        self.assertTrue(any("HC-2" in p for p in problems))
        self.assertTrue(any("T" in p for p in problems))

    def test_clean_when_current_is_superset(self):
        baseline = {"codes": ["HC-1"], "sections": ["S"]}
        current = {"codes": ["HC-1", "HC-9"], "sections": ["S", "Z"]}
        self.assertEqual(slc.diff_inventory(baseline, current), [])


class CheckPointersTest(unittest.TestCase):
    def test_flags_dangling_pointer(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.md"
            p.write_text("See [x](missing.md) and [self](a.md).\n")
            problems = slc.check_pointers([p], CODE_PATTERNS)
            # Only the dangling target is reported; the valid self-link (a.md) is not.
            self.assertEqual(len(problems), 1)
            self.assertIn("missing.md", problems[0])
            # Source-file path is retained in the message (needed for multi-file runs).
            self.assertTrue(problems[0].startswith(str(p)))


class CliTest(unittest.TestCase):
    def setUp(self):
        self.fix = Path(__file__).parent / "skill_load_cost" / "fixtures"
        self.patterns = Path(__file__).parent / "skill_load_cost" / "code_patterns.json"

    def test_diff_passes_against_self(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "base.json"
            self.assertEqual(
                slc.main([
                    "baseline", "--files", str(self.fix / "alpha.md"),
                    "--code-patterns", str(self.patterns), "--out", str(base),
                ]),
                0,
            )
            self.assertEqual(
                slc.main([
                    "diff", "--baseline", str(base),
                    "--files", str(self.fix / "alpha.md"),
                    "--code-patterns", str(self.patterns),
                ]),
                0,
            )


def baseline_skill_md(repo: Path, baseline_name: str) -> Path:
    """Map a committed baseline name to its unique owning SKILL.md — the inverse
    of the guard's `_baseline_for` (skill dir name → baselines/<name>.json)."""
    matches = sorted(repo.glob(f"souroldgeezer-*/skills/{baseline_name}/SKILL.md"))
    if len(matches) != 1:
        raise AssertionError(
            f"baseline {baseline_name!r} must map to exactly one published "
            f"SKILL.md, found {matches}"
        )
    return matches[0]


class CommittedBaselinesClosureTest(unittest.TestCase):
    """Every committed load-cost baseline must be satisfied by the inventory of
    the guard's own link closure (resolve_closure) — the same closure the Stop
    hook enforces. A directory-glob inventory is deliberately NOT used here: a
    baseline built wider than the closure would report permanent phantom
    regressions the guard can never satisfy (issue #75)."""

    def test_committed_baselines_satisfied_by_guard_closure(self):
        repo = REPO_ROOT
        patterns = json.loads(
            (repo / "tests/skill_load_cost/code_patterns.json").read_text()
        )
        baselines = sorted((repo / "tests/skill_load_cost/baselines").glob("*.json"))
        self.assertTrue(baselines, "no committed baselines found")
        for bl in baselines:
            with self.subTest(skill=bl.stem):
                closure = slc.resolve_closure(baseline_skill_md(repo, bl.stem))
                current = slc.union_inventory([
                    slc.extract_inventory(p.read_text(encoding="utf-8"), patterns)
                    for p in closure
                ])
                self.assertEqual(
                    slc.diff_inventory(json.loads(bl.read_text()), current), []
                )


class ResolveClosureWithOverridesTest(unittest.TestCase):
    def _skill_with_ref(self, root: Path) -> tuple:
        skill_md = root / "SKILL.md"
        ref_md = root / "ref.md"
        skill_md.write_text("# S\n[ref](ref.md)\n")
        ref_md.write_text("# R\n")
        return skill_md, ref_md

    def test_override_content_shrinks_closure_when_link_removed(self):
        """If an override removes a link, the linked file must drop from the closure."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            skill_md, ref_md = self._skill_with_ref(root)
            # With the real content, ref.md is in the closure
            base_closure = {p.name for p in slc.resolve_closure(skill_md)}
            self.assertIn("ref.md", base_closure)
            # Override SKILL.md to remove the link — ref.md must be absent
            overrides = {skill_md.resolve(): "# S\n(no link anymore)\n"}
            override_closure = {p.name for p in slc.resolve_closure_with_overrides(
                skill_md, overrides)}
            self.assertNotIn("ref.md", override_closure,
                "link removal in override must shrink the closure")

    def test_override_content_keeps_skill_md_itself(self):
        """SKILL.md is always the closure root; an override of it still includes it."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            skill_md = root / "SKILL.md"
            skill_md.write_text("# S\n")
            overrides = {skill_md.resolve(): "# S override\n"}
            closure = {p.name for p in slc.resolve_closure_with_overrides(
                skill_md, overrides)}
            self.assertIn("SKILL.md", closure)

    # test_no_overrides_matches_resolve_closure was retired: resolve_closure now
    # delegates to resolve_closure_with_overrides(skill_md, {}), so that assertion
    # became a tautology (f(x) == f(x)). Replaced by the discriminating test below.
    def test_overrides_shrink_closure_vs_disk(self):
        """A non-empty override exercises the override read path: links kept in the
        override text are still followed, links removed drop from the closure —
        while plain resolve_closure keeps reflecting the on-disk state."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "refs").mkdir()
            skill_md = root / "SKILL.md"
            skill_md.write_text("[a](refs/a.md) [b](refs/b.md)\n")
            (root / "refs" / "a.md").write_text("# A\n")
            (root / "refs" / "b.md").write_text("# B\n")
            disk = {p.name for p in slc.resolve_closure(skill_md)}
            self.assertEqual(disk, {"SKILL.md", "a.md", "b.md"})
            overrides = {skill_md.resolve(): "[a](refs/a.md)\n"}  # b link removed
            overridden = {p.name for p in slc.resolve_closure_with_overrides(
                skill_md, overrides)}
            self.assertEqual(overridden, {"SKILL.md", "a.md"},
                "override must drop b.md but still follow the kept a.md link")


class ResolveClosureTest(unittest.TestCase):
    def test_follows_load_map_links_transitively(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "SKILL.md").write_text(
                "# S\n[ref](ref.md) [ext](extensions/e.md) "
                "[ext-only](https://x) `](not-a-link.md)`\n")
            (root / "ref.md").write_text("# R\n[deep](deep.md)\n")
            (root / "deep.md").write_text("# D\n")
            (root / "extensions").mkdir()
            (root / "extensions" / "e.md").write_text("# E\n")
            got = {p.name for p in slc.resolve_closure(root / "SKILL.md")}
            self.assertEqual(got, {"SKILL.md", "ref.md", "deep.md", "e.md"})

    def test_ignores_links_in_code_and_missing_targets(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "SKILL.md").write_text("# S\n[gone](missing.md) `[x](nope.md)`\n")
            got = {p.name for p in slc.resolve_closure(root / "SKILL.md")}
            self.assertEqual(got, {"SKILL.md"})


class ResolveClosureCliTest(unittest.TestCase):
    def _fixture_entry(self, root: Path) -> Path:
        (root / "refs").mkdir()
        (root / "SKILL.md").write_text("see [a](refs/a.md)", encoding="utf-8")
        (root / "refs" / "a.md").write_text("leaf, no links", encoding="utf-8")
        return root / "SKILL.md"

    def _run_resolve_closure(self, entry: Path, *extra_args: str) -> tuple:
        """Invoke the resolve_closure subcommand against entry, capturing stdout.
        Returns (exit_code, stdout_text); shared by the JSON and plain-output
        CLI tests below, which differ only in the flag passed and the assertions
        made on the captured output."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = slc.main(["resolve_closure", str(entry), *extra_args])
        return rc, buf.getvalue()

    def test_resolve_closure_subcommand_lists_transitive_links_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            entry = self._fixture_entry(Path(td))
            rc, out = self._run_resolve_closure(entry, "--json")
            self.assertEqual(rc, 0)
            paths = json.loads(out)
            self.assertEqual(sorted(Path(p).name for p in paths), ["SKILL.md", "a.md"])

    def test_resolve_closure_subcommand_plain_output_newline_joined(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            entry = self._fixture_entry(Path(td))
            rc, out = self._run_resolve_closure(entry)
            self.assertEqual(rc, 0)
            lines = out.splitlines()
            self.assertEqual(sorted(Path(p).name for p in lines), ["SKILL.md", "a.md"])
            for line in lines:
                self.assertTrue(Path(line).is_absolute(), line)


class CostRegressionTest(unittest.TestCase):
    def test_flags_growth_past_tolerance_only(self):
        snap = {"a": 100, "b": 200}
        scenarios = [
            {"id": "a", "files": ["a.md"]},
            {"id": "b", "files": ["b.md"]},
        ]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.md").write_text("word " * 130)   # grows past tolerance
            (root / "b.md").write_text("word " * 205)    # within tolerance
            probs = slc.cost_regressions(snap, scenarios, root, tolerance=25)
            self.assertEqual(len(probs), 1)
            self.assertIn("a:", probs[0])


class CliExitContractTest(unittest.TestCase):
    def setUp(self):
        self.fix = Path(__file__).parent / "skill_load_cost" / "fixtures"

    def test_missing_patterns_file_exits_2_without_traceback(self):
        proc = run_cli("baseline", "--files", str(SCRIPT),
                       "--code-patterns", "/nonexistent/patterns.json")
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("patterns", proc.stderr.lower())

    def test_unknown_scenario_id_exits_2_without_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            scenarios = Path(d) / "scenarios.json"
            scenarios.write_text(json.dumps([{"id": "known", "files": ["alpha.md"]}]))
            proc = run_cli("measure", "--scenarios", str(scenarios),
                           "--id", "nope", "--root", str(self.fix))
            self.assertEqual(proc.returncode, 2)
            self.assertNotIn("Traceback", proc.stderr)
            self.assertIn("nope", proc.stderr)
            self.assertIn("known", proc.stderr)

    def test_malformed_regex_pattern_exits_2_without_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            patterns = Path(d) / "patterns.json"
            patterns.write_text(json.dumps(["(unterminated"]))
            proc = run_cli("baseline", "--files", str(self.fix / "alpha.md"),
                           "--code-patterns", str(patterns))
            self.assertEqual(proc.returncode, 2)
            self.assertNotIn("Traceback", proc.stderr)


CODE_PATTERNS = json.loads((REPO_ROOT / "tests/skill_load_cost/code_patterns.json").read_text())

# A before-region carrying one element of every guarded token class.
_BEFORE = (
    "The loader MUST reject `unknown` fields and return a problem for LA-DUP-1 "
    "within 30 ms; see [guide](x.md). It does not retry."
)


class GuardTokensTest(unittest.TestCase):
    """G2v deterministic guard: an after-region must preserve every closed token
    class of the before-region (superset for codes/links/inline-code/numbers/
    normative-keywords; no drop in any negation token's count)."""

    def _guard(self, after: str, before: str = _BEFORE) -> list[str]:
        return slc.guard_tokens(before, after, CODE_PATTERNS)

    def test_faithful_tighten_preserving_all_classes_is_clean(self):
        after = (
            "The loader MUST reject `unknown` fields, returning a problem for "
            "LA-DUP-1 within 30 ms ([guide](x.md)); it does not retry."
        )
        self.assertEqual(self._guard(after), [])

    def test_dropped_finding_code_flagged(self):
        after = "The loader MUST reject `unknown` fields within 30 ms; see [guide](x.md). It does not retry."
        probs = self._guard(after)
        self.assertTrue(any("LA-DUP-1" in p for p in probs), probs)

    def test_dropped_link_target_flagged(self):
        after = "The loader MUST reject `unknown` fields for LA-DUP-1 within 30 ms. It does not retry."
        self.assertTrue(any("x.md" in p for p in self._guard(after)))

    def test_dropped_inline_code_flagged(self):
        after = "The loader MUST reject unknown fields for LA-DUP-1 within 30 ms; see [guide](x.md). It does not retry."
        self.assertTrue(any("unknown" in p for p in self._guard(after)))

    def test_dropped_number_flagged(self):
        after = "The loader MUST reject `unknown` fields for LA-DUP-1 quickly; see [guide](x.md). It does not retry."
        self.assertTrue(any("30" in p for p in self._guard(after)))

    def test_dropped_normative_keyword_flagged(self):
        after = "The loader should reject `unknown` fields for LA-DUP-1 within 30 ms; see [guide](x.md). It does not retry."
        self.assertTrue(any("MUST" in p for p in self._guard(after)))

    def test_dropped_negation_is_hard_fail(self):
        # silent inversion: "does not retry" -> "retries"
        after = "The loader MUST reject `unknown` fields for LA-DUP-1 within 30 ms; see [guide](x.md). It retries."
        self.assertTrue(any("not" in p.lower() for p in self._guard(after)))

    def test_added_content_is_not_flagged(self):
        # guard_tokens is one-directional (before subset of after); adding an
        # extra normative keyword is fine here (two-way entailment is a judgment
        # step, not this deterministic gate).
        after = _BEFORE + " Callers MUST NEVER assume ordering."
        self.assertEqual(self._guard(after), [])

    def test_empty_before_is_clean(self):
        self.assertEqual(slc.guard_tokens("", "anything at all", CODE_PATTERNS), [])


class GuardTokensCliTest(unittest.TestCase):
    def _run(self, before: str, after: str):
        with tempfile.TemporaryDirectory() as d:
            bf, af = Path(d) / "before.md", Path(d) / "after.md"
            pat = Path(d) / "patterns.json"
            bf.write_text(before, encoding="utf-8")
            af.write_text(after, encoding="utf-8")
            pat.write_text(json.dumps(CODE_PATTERNS), encoding="utf-8")
            return run_cli("guard_tokens", "--before", str(bf), "--after", str(af),
                           "--code-patterns", str(pat))

    def test_clean_rewrite_exits_0(self):
        proc = self._run(_BEFORE, _BEFORE)
        self.assertEqual(proc.returncode, 0)

    def test_violation_exits_1(self):
        proc = self._run(_BEFORE, "The loader rejects fields quickly.")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("guard", (proc.stdout + proc.stderr).lower())

    def test_missing_file_exits_2_without_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            pat = Path(d) / "patterns.json"
            pat.write_text(json.dumps(CODE_PATTERNS))
            proc = run_cli("guard_tokens",
                           "--before", "/nonexistent/b.md", "--after", "/nonexistent/a.md",
                           "--code-patterns", str(pat))
            self.assertEqual(proc.returncode, 2)
            self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
