"""Tests for the LA-VERBOSE-1 deterministic verbosity nominator (engine + registry).

The judgment layer (LA-VERBOSE-2, fuzzy-waste.md) is not code; it is covered by the
synthetic eval packs. This file exercises only the deterministic nomination stage.
"""
import json
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import (
    REPO_ROOT,
    assert_precision_recall_at_least,
    classify_tp_fp_fn,
    load_script_module,
)

ENGINE = REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit" / "references" / "scripts" / "lean_engine.py"
LEDGER = REPO_ROOT / "tests" / "lean_verbosity_ledger.jsonl"

# A wordy paragraph: hedges, meta-discourse scaffolding, and self-restatement.
VERBOSE = (
    "## Overview\n"
    "This section describes the review process. In order to complete the review, it is "
    "important to note that each step must basically be followed in sequence. Due to the "
    "fact that the review is essentially sequential, in order to proceed you must, in order "
    "to move forward, finish every prior step first. It is worth noting that the review is "
    "sequential. It is worth noting that the review is sequential and cannot be skipped. "
    "Basically, obviously, the reviewer should simply follow each step in order.\n"
)

# A dense technical paragraph of the same length: no filler, no scaffolding, low repetition.
CLEAN = (
    "## Config\n"
    "The loader reads thresholds from the registry table and falls back to built-in defaults "
    "when a key is absent or malformed. Numeric fields accept integers or floats; boolean "
    "fields accept only true or false. Invalid entries are skipped, so a single typo never "
    "aborts the scan. The parser ignores unknown tables and preserves forward compatibility "
    "with keys introduced by later releases of the engine and its guard hooks.\n"
)


def load_engine():
    return load_script_module("lean_engine", ENGINE)


class FillerDensity(unittest.TestCase):
    def test_high_on_filler_stuffed_prose(self):
        eng = load_engine()
        tokens = eng.normalize(
            "in order to proceed it is important to note that due to the fact that "
            "we basically must essentially move forward"
        )
        self.assertGreater(eng.filler_density(tokens), 0.15)

    def test_zero_on_dense_prose(self):
        eng = load_engine()
        tokens = eng.normalize(
            "the loader reads thresholds and falls back to defaults when a key is absent"
        )
        self.assertLess(eng.filler_density(tokens), 0.03)

    def test_empty_is_zero(self):
        eng = load_engine()
        self.assertEqual(eng.filler_density([]), 0.0)


class ScaffoldCount(unittest.TestCase):
    def test_counts_meta_discourse_openers(self):
        eng = load_engine()
        body = (
            "This section describes the flow. As mentioned above the flow is linear. "
            "It is worth noting that nothing branches."
        )
        self.assertGreaterEqual(eng.scaffold_count(body), 3)

    def test_zero_on_plain_prose(self):
        eng = load_engine()
        self.assertEqual(eng.scaffold_count("The loader reads thresholds and falls back."), 0)

    def test_ignores_scaffolding_inside_code_fence(self):
        eng = load_engine()
        body = "Real prose here.\n```\nthis section describes the fenced sample\n```\n"
        self.assertEqual(eng.scaffold_count(body), 0)


class RepeatRatio(unittest.TestCase):
    def test_high_on_self_restating_section(self):
        eng = load_engine()
        tokens = eng.normalize(("the review is sequential and cannot be skipped " * 5))
        self.assertGreater(eng.repeat_ratio(tokens), 0.18)

    def test_low_on_varied_prose(self):
        eng = load_engine()
        tokens = eng.normalize(
            "the loader reads thresholds and falls back to built-in defaults when a key "
            "is absent numeric fields accept integers invalid entries are skipped silently"
        )
        self.assertLess(eng.repeat_ratio(tokens), 0.18)

    def test_short_token_list_is_zero(self):
        eng = load_engine()
        self.assertEqual(eng.repeat_ratio(["a", "b"]), 0.0)


class VerboseOverride(unittest.TestCase):
    def test_marker_detected(self):
        eng = load_engine()
        self.assertTrue(
            eng.has_verbose_override("body <!-- lean-audit:verbose-intentional: worked example -->")
        )

    def test_plain_text_not_flagged(self):
        eng = load_engine()
        self.assertFalse(eng.has_verbose_override("plain prose without a marker"))

    def test_sync_marker_is_not_a_verbose_marker(self):
        eng = load_engine()
        self.assertFalse(eng.has_verbose_override("body <!-- lean-audit:sync-intentional: ok -->"))


class VerbosityConfig(unittest.TestCase):
    def test_defaults(self):
        eng = load_engine()
        reg = eng.load_registry(None)
        v = reg.verbosity
        self.assertTrue(v.enabled)
        self.assertEqual(v.min_tokens, 60)
        self.assertAlmostEqual(v.filler_density, 0.09)
        self.assertEqual(v.scaffold_min, 2)
        self.assertAlmostEqual(v.repeat_ratio, 0.18)

    def test_toml_overrides(self):
        eng = load_engine()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".lean-audit.toml"
            p.write_text(
                "[verbosity]\nenabled = false\nmin_tokens = 120\n"
                "filler_density = 0.2\nscaffold_min = 4\nrepeat_ratio = 0.5\n",
                encoding="utf-8",
            )
            reg = eng.load_registry(p)
        v = reg.verbosity
        self.assertFalse(v.enabled)
        self.assertEqual(v.min_tokens, 120)
        self.assertAlmostEqual(v.filler_density, 0.2)
        self.assertEqual(v.scaffold_min, 4)
        self.assertAlmostEqual(v.repeat_ratio, 0.5)

    def test_invalid_keys_fall_back_to_defaults(self):
        eng = load_engine()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".lean-audit.toml"
            # wrong types: min_tokens as string, filler_density as bool
            p.write_text(
                '[verbosity]\nmin_tokens = "lots"\nfiller_density = true\n', encoding="utf-8"
            )
            reg = eng.load_registry(p)
        self.assertEqual(reg.verbosity.min_tokens, 60)
        self.assertAlmostEqual(reg.verbosity.filler_density, 0.09)


class ScanVerbosity(unittest.TestCase):
    def _scan(self, files, reg=None):
        eng = load_engine()
        return eng.scan_verbosity(files, reg if reg is not None else eng.load_registry(None))

    def test_nominates_verbose_section(self):
        eng = load_engine()
        findings = self._scan({"a/SKILL.md": VERBOSE})
        codes = {f.code for f in findings}
        self.assertIn("LA-VERBOSE-1", codes)
        f = [f for f in findings if f.code == "LA-VERBOSE-1"][0]
        self.assertEqual(f.severity, "info")
        self.assertEqual(f.path, "a/SKILL.md")
        self.assertEqual(f.heading, "Overview")

    def test_clean_section_not_nominated(self):
        self.assertEqual(self._scan({"a/SKILL.md": CLEAN}), [])

    def test_below_token_floor_not_nominated(self):
        # verbose phrasing but far under the 60-token floor
        short = "## H\nIn order to note that, basically it is worth noting this simply matters.\n"
        self.assertEqual(self._scan({"a/SKILL.md": short}), [])

    def test_override_marker_suppresses(self):
        marked = VERBOSE.rstrip() + " <!-- lean-audit:verbose-intentional: pedagogy -->\n"
        self.assertEqual(self._scan({"a/SKILL.md": marked}), [])

    def test_path_exempt_suppresses(self):
        eng = load_engine()
        findings = self._scan({".claude/skills/x/SKILL.md": VERBOSE})
        self.assertEqual(findings, [])

    def test_disabled_config_silences(self):
        eng = load_engine()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".lean-audit.toml"
            p.write_text("[verbosity]\nenabled = false\n", encoding="utf-8")
            reg = eng.load_registry(p)
        self.assertEqual(self._scan({"a/SKILL.md": VERBOSE}, reg), [])

    def test_frontmatter_stripped_before_scan(self):
        # a long keyword-rich description in frontmatter must not be scanned
        eng = load_engine()
        fm_only = "---\nname: x\ndescription: " + ("in order to note that " * 40) + "\n---\n# X\nshort body\n"
        self.assertEqual(self._scan({"a/SKILL.md": fm_only}), [])

    def test_repetitive_list_not_nominated(self):
        # Naturally repetitive reference/anchor lists trip the repeat signal alone
        # (high repeat, zero filler/scaffold). The composite >=2 gate is what keeps
        # them silent — the exact false-positive class seen on the live repo corpus
        # (Source Anchors / Authoritative Sources sections).
        lines = "\n".join(
            f"- See the {n} guide at the {n} reference for the {n} details and rules."
            for n in ["auth", "cache", "retry", "quota", "limit", "token", "scope", "audit"]
        )
        self.assertEqual(self._scan({"a/SKILL.md": f"# Sources\n\n{lines}\n"}), [])

    def test_metrics_attached_and_serializable(self):
        eng = load_engine()
        import dataclasses
        f = self._scan({"a/SKILL.md": VERBOSE})[0]
        self.assertTrue(f.metrics)  # non-empty
        metric_keys = {k for k, _ in f.metrics}
        self.assertEqual(metric_keys, {"tokens", "filler_density", "scaffold", "repeat_ratio"})
        # round-trips through asdict (the JSON emit path)
        d = dataclasses.asdict(f)
        self.assertIn("metrics", d)


class CliIntegration(unittest.TestCase):
    def test_verbose_finding_in_json_and_exit_zero(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "p" / "skills" / "x"
            base.mkdir(parents=True)
            (base / "SKILL.md").write_text(VERBOSE, encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(ENGINE), d, "--format", "json"],
                capture_output=True, text=True, cwd=REPO_ROOT, check=False,
            )
            codes = {f["code"] for f in json.loads(r.stdout)["findings"]}
            self.assertIn("LA-VERBOSE-1", codes)
            # info severity never sets the block exit code
            self.assertEqual(r.returncode, 0)


class VerbosityRepoResidual(unittest.TestCase):
    def test_live_nomination_count_is_bounded(self):
        # info-only nominations; the composite >=2 gate keeps this near zero on the
        # repo's own (dense, lean-audited) prose. A regression that floods here — a
        # loosened threshold or a genuinely verbose new section — trips this bound.
        eng = load_engine()
        root = REPO_ROOT
        files = eng.read_repo(root, root)
        reg = eng.load_registry(root / ".lean-audit.toml")
        nominated = [f for f in eng.scan_verbosity(files, reg) if f.code == "LA-VERBOSE-1"]
        self.assertLessEqual(
            len(nominated), 8, [f"{f.path} §{f.heading}" for f in nominated]
        )


class VerbosityCalibration(unittest.TestCase):
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
            nominated = [
                f for f in eng.scan_verbosity(files, reg)
                if f.code == "LA-VERBOSE-1" and f.path == case["expect_source"]
            ]
            fired = bool(nominated)
            tp, fp, fn = classify_tp_fp_fn(case["expect_nominate"], fired, tp, fp, fn)
        assert_precision_recall_at_least(self, tp, fp, fn)


if __name__ == "__main__":
    unittest.main()
