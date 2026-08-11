import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT


SKILL_ROOT = REPO_ROOT / "souroldgeezer-audit/skills/test-quality-audit"
SKILL = SKILL_ROOT / "SKILL.md"
OUTPUT = SKILL_ROOT / "references/procedures/deep-mode-output-format.md"
CATALOG = SKILL_ROOT / "references/smell-catalog.md"
GROUNDING = SKILL_ROOT / "references/source-grounding.md"
BEHAVIORS = SKILL_ROOT / "references/evals/behavior-cases.jsonl"
TRIGGERS = SKILL_ROOT / "references/evals/trigger-cases.jsonl"
GOLDEN = SKILL_ROOT / "references/golden-corpus/test-quality-audit-cases.jsonl"
AGENT = REPO_ROOT / "souroldgeezer-audit/agents/test-quality-audit.md"
SCENARIOS = REPO_ROOT / "tests/skill_load_cost/scenarios.json"
CODE_PATTERNS = REPO_ROOT / "tests/skill_load_cost/code_patterns.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_jsonl(path: Path) -> dict[str, dict]:
    return {
        record["id"]: record
        for record in (json.loads(line) for line in read(path).splitlines() if line.strip())
    }


class TestQualitySuiteHealthSurfaceTest(unittest.TestCase):
    def test_deep_always_loads_suite_health_without_changing_quick(self) -> None:
        skill = read(SKILL)
        skill_compact = " ".join(skill.split())
        self.assertIn("suite strategy, runtime growth, portfolio maintenance", skill)
        self.assertIn("In every Deep audit, load", skill)
        self.assertIn("deep-mode-output-format.md", skill)
        self.assertIn("Quick mode remains per-test", skill_compact)

        scenarios = {row["id"]: row for row in json.loads(read(SCENARIOS))}
        procedure = (
            "souroldgeezer-audit/skills/test-quality-audit/"
            "references/procedures/deep-mode-output-format.md"
        )
        self.assertIn(procedure, scenarios["deep-nextjs-suite"]["files"])
        self.assertIn(procedure, scenarios["deep-python-suite"]["files"])
        self.assertNotIn(procedure, scenarios["quick-node-unit"]["files"])
        self.assertNotIn(procedure, scenarios["quick-python-unit"]["files"])
        self.assertIn(
            r"\bSH-(?:HC|LC|POS)-\d+",
            json.loads(read(CODE_PATTERNS)),
        )

    def test_suite_health_contract_uses_progressive_project_evidence(self) -> None:
        output = read(OUTPUT)
        output_lower = output.lower()
        for phrase in (
            "## suite health",
            "static snapshot",
            "current-run evidence",
            "historical trends",
            "effectiveness evidence",
            "evidence sources",
            "window",
            "limitations",
            "feedback",
            "efficiency",
            "reliability",
            "maintainability",
            "keep",
            "strengthen",
            "move down",
            "consolidate",
            "schedule later",
            "verify-then-retire",
            "management evidence before sampling",
            "safe one-shot suite execution",
            "current-run evidence is mandatory",
            "runtime distribution is mandatory",
            "supported-positive",
            "substantiated-finding",
            "unknown-evidence-gap",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, output_lower)
        self.assertIn("project-declared", output)
        self.assertIn("unknown", output)
        self.assertNotIn("### Pyramid ratio", output)
        self.assertNotIn("### Runtime distribution", output)
        for universal_threshold in ("> 100 ms", "> 2 s", "> 5 min", "70-80%"):
            self.assertNotIn(universal_threshold, output)

        self.assertLess(
            output_lower.index("## management evidence before sampling"),
            output_lower.index("## per-file rollup"),
        )
        for dimension in ("Feedback", "Current execution", "Efficiency", "Reliability", "Maintainability"):
            with self.subTest(dimension=dimension):
                self.assertIn(f"**{dimension}:**", output)
        self.assertIn("weak — any block", output)
        self.assertIn("adequate — warnings or material unknowns without blocks", output)
        self.assertIn("strong — all five dimensions are supported-positive", " ".join(output.split()))
        self.assertIn("not assessed — target or runner cannot be established", " ".join(output.split()))

    def test_suite_health_codes_and_retirement_gate_are_documented(self) -> None:
        catalog = read(CATALOG)
        for code in (
            "SH-HC-1",
            "SH-HC-2",
            "SH-HC-3",
            "SH-HC-4",
            "SH-HC-5",
            "SH-HC-6",
            "SH-LC-1",
            "SH-LC-2",
            "SH-LC-3",
            "SH-LC-4",
            "SH-LC-5",
            "SH-LC-6",
            "SH-POS-1",
            "SH-POS-2",
            "SH-POS-3",
            "SH-POS-4",
            "SH-POS-5",
        ):
            self.assertIn(f"`{code}`", catalog)
        self.assertIn("test-count growth alone is not a smell", " ".join(catalog.lower().split()))
        self.assertIn("distinct-contract review", catalog)
        self.assertIn("controlled-removal evidence", catalog)
        self.assertIn("coverage-only", catalog.lower())

    def test_behavior_and_golden_cases_pin_suite_health_boundaries(self) -> None:
        behaviors = read_jsonl(BEHAVIORS)
        golden = read_jsonl(GOLDEN)
        expected_behavior_ids = {
            "test-quality-behavior-suite-healthy-tdd-growth",
            "test-quality-behavior-suite-cross-layer-duplication",
            "test-quality-behavior-suite-missing-history",
            "test-quality-behavior-suite-unfamiliar-results",
            "test-quality-behavior-suite-selection-and-quarantine",
            "test-quality-behavior-suite-retirement-evidence",
            "test-quality-behavior-suite-healthy-lanes",
            "test-quality-behavior-suite-failed-current-run",
            "test-quality-behavior-suite-monolithic-every-change",
            "test-quality-behavior-suite-broad-unbudgeted-cost",
            "test-quality-behavior-suite-missing-ownership",
            "test-quality-behavior-suite-count-only-neutrality",
        }
        self.assertTrue(expected_behavior_ids.issubset(behaviors))
        for case_id in expected_behavior_ids:
            case = behaviors[case_id]
            self.assertEqual("synthetic", case["source_kind"])
            self.assertFalse(case["contains_third_party_text"])

        expected_golden_ids = {f"TQA-GOLD-{number:04d}" for number in (*range(30, 36), *range(46, 52))}
        self.assertTrue(expected_golden_ids.issubset(golden))
        self.assertEqual([], golden["TQA-GOLD-0030"]["expected_suite_health_smells"])
        self.assertIn("SH-POS-2", golden["TQA-GOLD-0030"]["expected_suite_health_positives"])
        self.assertIn("SH-HC-2", golden["TQA-GOLD-0031"]["expected_suite_health_smells"])
        self.assertEqual("unknown", golden["TQA-GOLD-0032"]["expected_trend_state"])
        self.assertEqual("unknown", golden["TQA-GOLD-0033"]["expected_current_run_state"])
        self.assertIn("SH-HC-3", golden["TQA-GOLD-0034"]["expected_suite_health_smells"])
        self.assertIn("SH-HC-4", golden["TQA-GOLD-0034"]["expected_suite_health_smells"])
        self.assertIn("delete-from-coverage-alone", golden["TQA-GOLD-0035"]["forbidden_actions"])
        self.assertIn("SH-POS-5", golden["TQA-GOLD-0046"]["expected_suite_health_positives"])
        self.assertIn("SH-HC-6", golden["TQA-GOLD-0047"]["expected_suite_health_smells"])
        self.assertIn("SH-LC-4", golden["TQA-GOLD-0048"]["expected_suite_health_smells"])
        self.assertIn("SH-LC-5", golden["TQA-GOLD-0049"]["expected_suite_health_smells"])
        self.assertIn("SH-LC-6", golden["TQA-GOLD-0050"]["expected_suite_health_smells"])
        self.assertEqual([], golden["TQA-GOLD-0051"]["expected_suite_health_smells"])
        self.assertIn("SH-POS-5", golden["TQA-GOLD-0051"]["expected_suite_health_positives"])

    def test_triggers_wrappers_docs_and_sources_cover_the_public_contract(self) -> None:
        triggers = read_jsonl(TRIGGERS)
        for case_id in (
            "test-quality-trigger-yes-test-strategy",
            "test-quality-trigger-yes-runtime-growth",
            "test-quality-trigger-yes-portfolio-maintenance",
            "test-quality-trigger-yes-tdd-suite-pressure",
        ):
            self.assertTrue(triggers[case_id]["expected_activation"])

        agent = read(AGENT)
        self.assertIn("suite strategy", agent)
        self.assertIn("runtime growth", agent)
        self.assertIn("portfolio maintenance", agent)

        grounding = read(GROUNDING)
        for source in (
            "arxiv.org/abs/2105.03312",
            "research.google/pubs/taming-google-scale-continuous-testing",
            "doi.org/10.1155/2010/932686",
            "arxiv.org/abs/1602.01226",
        ):
            self.assertIn(source, grounding)

        for path in (REPO_ROOT / "README.md", REPO_ROOT / "CLAUDE.md", REPO_ROOT / "AGENTS.md"):
            with self.subTest(path=path.name):
                text = read(path)
                self.assertIn("suite health", text.lower())


if __name__ == "__main__":
    unittest.main()
