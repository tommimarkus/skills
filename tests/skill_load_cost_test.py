# tests/skill_load_cost_test.py
import glob
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

# Load the script by path — repo convention (no `scripts/__init__.py`), matching
# tests/skill_architecture_report_test.py and tests/lessons_ledger_test.py.
REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "skill_load_cost",
    REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit"
    / "references" / "scripts" / "skill_load_cost.py",
)
slc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(slc)


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


class TestQualityAuditBaselineTest(unittest.TestCase):
    def test_current_files_satisfy_committed_baseline(self):
        repo = Path(__file__).resolve().parents[1]
        base = json.loads(
            (repo / "tests/skill_load_cost/baselines/test-quality-audit.json").read_text()
        )
        patterns = json.loads(
            (repo / "tests/skill_load_cost/code_patterns.json").read_text()
        )
        roots = [
            "souroldgeezer-audit/skills/test-quality-audit/references",
            "souroldgeezer-audit/docs/quality-reference",
            "souroldgeezer-audit/docs/audit-reference",
        ]
        files = []
        for r in roots:
            files += glob.glob(str(repo / r / "**" / "*.md"), recursive=True)
        current = slc.union_inventory(
            [slc.extract_inventory(Path(f).read_text(), patterns) for f in files]
        )
        self.assertEqual(slc.diff_inventory(base, current), [])


class ApiDesignBaselineTest(unittest.TestCase):
    def test_current_files_satisfy_committed_baseline(self):
        repo = Path(__file__).resolve().parents[1]
        base = json.loads(
            (repo / "tests/skill_load_cost/baselines/api-design.json").read_text()
        )
        patterns = json.loads(
            (repo / "tests/skill_load_cost/code_patterns.json").read_text()
        )
        roots = [
            "souroldgeezer-design/skills/api-design",
            "souroldgeezer-design/docs/api-reference",
        ]
        files = []
        for r in roots:
            files += glob.glob(str(repo / r / "**" / "*.md"), recursive=True)
        current = slc.union_inventory(
            [slc.extract_inventory(Path(f).read_text(), patterns) for f in files]
        )
        self.assertEqual(slc.diff_inventory(base, current), [])


if __name__ == "__main__":
    unittest.main()
