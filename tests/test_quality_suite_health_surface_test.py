import json
import re
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, assert_phrases


SKILL_ROOT = REPO_ROOT / "souroldgeezer-audit/skills/test-quality-audit"
SKILL = SKILL_ROOT / "SKILL.md"
OUTPUT = SKILL_ROOT / "references/procedures/deep-mode-output-format.md"
RECOVERY = SKILL_ROOT / "references/procedures/suite-recovery.md"
CATALOG = SKILL_ROOT / "references/smell-catalog.md"
INTEGRATION = REPO_ROOT / "souroldgeezer-audit/docs/quality-reference/integration-testing.md"
GROUNDING = SKILL_ROOT / "references/source-grounding.md"
BEHAVIORS = SKILL_ROOT / "references/evals/behavior-cases.jsonl"
TRIGGERS = SKILL_ROOT / "references/evals/trigger-cases.jsonl"
GOLDEN = SKILL_ROOT / "references/golden-corpus/test-quality-audit-cases.jsonl"
AGENT = REPO_ROOT / "souroldgeezer-audit/agents/test-quality-audit.md"
SCENARIOS = REPO_ROOT / "tests/skill_load_cost/scenarios.json"
CODE_PATTERNS = REPO_ROOT / "tests/skill_load_cost/code_patterns.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter_description(text: str) -> str:
    frontmatter = text.split("---", 2)[1]
    match = re.search(r"^description:\s*(.*?)(?=^\S|\Z)", frontmatter, flags=re.S | re.M)
    assert match is not None, "frontmatter has no description"
    return " ".join(match.group(1).replace(">-", "", 1).split())


def read_jsonl(path: Path) -> dict[str, dict]:
    return {
        record["id"]: record
        for record in (json.loads(line) for line in read(path).splitlines() if line.strip())
    }


class TestQualitySuiteHealthSurfaceTest(unittest.TestCase):
    def test_extra_execution_behavior_cases_are_synthetic_and_well_formed(self) -> None:
        behaviors = read_jsonl(BEHAVIORS)
        expected = {
            "test-quality-behavior-unapproved-rerun",
            "test-quality-behavior-unapproved-mutation",
            "test-quality-behavior-preauthorized-extra-execution",
            "test-quality-behavior-success-no-installed-skill-write",
        }
        self.assertTrue(expected.issubset(behaviors))

        for case_id in expected:
            with self.subTest(case_id=case_id):
                case = behaviors[case_id]
                self.assertEqual("synthetic", case["source_kind"])
                self.assertFalse(case["contains_third_party_text"])
                self.assertTrue(case["prompt"].strip())
                self.assertTrue(case["grader"].strip())
                for field in ("expected_artifacts", "required_checks", "forbidden_behaviors"):
                    with self.subTest(field=field):
                        self.assertTrue(case[field])
                        self.assertTrue(all(isinstance(item, str) and item.strip() for item in case[field]))

    def test_deep_always_loads_suite_health_without_changing_quick(self) -> None:
        skill = read(SKILL)
        skill_compact = " ".join(skill.split())
        self.assertIn("suite strategy, runtime growth, portfolio maintenance", skill)
        self.assertIn("In every Deep audit, load", skill)
        self.assertIn("deep-mode-output-format.md", skill)
        self.assertIn("references/scripts/suite_health_snapshot.py", skill)
        self.assertIn("when a JUnit XML report is already available", skill)
        self.assertIn("Quick mode remains per-test", skill_compact)
        self.assertLess(
            skill.index("3b. Deep only — mandatory suite-management pass"),
            skill.index("4. Apply core smells"),
        )
        self.assertLess(
            skill.index("3c. Deep only — mandatory setup/teardown lifecycle pass"),
            skill.index("4. Apply core smells"),
        )
        self.assertIn("runner, suite, module/class, worker, and per-test", skill_compact)
        self.assertIn("immutable or safely resettable infrastructure", skill_compact)
        self.assertIn("mutable data and session ownership", skill_compact)
        self.assertIn("Never request new instrumentation during an ordinary audit", skill)

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
        assert_phrases(self, output, (
            "Static snapshot",
            "Current-run evidence",
            "Historical trends",
            "Effectiveness evidence",
        ), heading="## Evidence ladder")
        assert_phrases(self, output, (
            "safe one-shot suite execution",
            "about ten minutes",
            "longer, unknown, browser, external-service, rerun, or mutation",
            "repository discovery",
            "datastore",
            "trend collector",
            "CI adapter",
            'python3 "${CLAUDE_SKILL_DIR}/references/scripts/suite_health_snapshot.py" --junit <report.xml>',
            'python3 "<absolute-loaded-skill-dir>/references/scripts/suite_health_snapshot.py" --junit <report.xml>',
        ), heading="## Management evidence before sampling")
        assert_phrases(self, output, (
            "### Suite health",
            "Evidence sources",
            "Window",
            "Limitations",
            "Current-run evidence is mandatory",
            "Runtime distribution is mandatory",
            "project-declared",
            "collection count",
            "pass/fail/error/skip",
            "elapsed time",
            "duration distribution",
            "lane selection",
            "ownership/cadence",
            "supported-positive",
            "substantiated-finding",
            "unknown-evidence-gap",
            *(f"**{dimension}:**" for dimension in (
                "Feedback", "Current execution", "Efficiency", "Reliability", "Maintainability")),
            "weak — any block",
            "adequate — warnings or material unknowns without blocks",
            "strong — all five dimensions are supported-positive",
            "not assessed — target or runner cannot be established",
            *(f"`{action}`" for action in (
                "keep", "strengthen", "move down", "consolidate", "schedule later", "verify-then-retire")),
            "### Setup/teardown lifecycle",
            "Cost attribution: measured | inferred | unknown",
            "Lifecycle safety: supported-positive | substantiated-finding | unknown-evidence-gap",
            "up to five material resources/hooks",
            "Current scope",
            "Mutability/isolation need",
            "Cost evidence",
            "Cleanup evidence",
            "direct phase/timing evidence",
            "declared-budget breach",
            "static lifecycle evidence",
            "Never request new instrumentation",
            "immutable or safely resettable infrastructure",
            "mutable data, users, sessions, and browser contexts remain per-test",
            "Do not consolidate tests merely because their setup text matches",
        ), heading="## Suite assessment")
        self.assertNotIn("### Pyramid ratio", output)
        self.assertNotIn("### Runtime distribution", output)
        for universal_threshold in ("> 100 ms", "> 2 s", "> 5 min", "70-80%"):
            self.assertNotIn(universal_threshold, output)

        lowered = output.lower()
        self.assertLess(
            lowered.index("## management evidence before sampling"),
            lowered.index("## per-file rollup"),
        )

    def test_suite_health_codes_and_retirement_gate_are_documented(self) -> None:
        catalog = read(CATALOG)
        for code in (
            "SH-HC-1",
            "SH-HC-2",
            "SH-HC-3",
            "SH-HC-4",
            "SH-HC-5",
            "SH-HC-6",
            "SH-HC-7",
            "SH-LC-1",
            "SH-LC-2",
            "SH-LC-3",
            "SH-LC-4",
            "SH-LC-5",
            "SH-LC-6",
            "SH-LC-7",
            "SH-POS-1",
            "SH-POS-2",
            "SH-POS-3",
            "SH-POS-4",
            "SH-POS-5",
            "SH-POS-6",
        ):
            self.assertIn(f"`{code}`", catalog)
        self.assertIn("test-count growth alone is not a smell", " ".join(catalog.lower().split()))
        self.assertIn("distinct-contract review", catalog)
        self.assertIn("controlled-removal evidence", catalog)
        self.assertIn("coverage-only", catalog.lower())
        compact_catalog = " ".join(catalog.split())
        self.assertIn(
            "`SH-HC-6` — The configured current run fails, errors, or exits nonzero.",
            compact_catalog,
        )
        self.assertIn(
            "`SH-LC-4` — Observed cost is material to the intended cadence but lacks a "
            "project-declared budget or comparable baseline; identify whether cost is "
            "tail-concentrated or broadly distributed.",
            compact_catalog,
        )
        self.assertIn(
            "`SH-LC-5` — The routine change path is one mixed full-suite lane with no "
            "faster lane or deliberately lower cadence.",
            compact_catalog,
        )
        self.assertIn(
            "`SH-LC-6` — No visible portfolio owner, overlap/gardening review, or retirement cadence.",
            compact_catalog,
        )
        self.assertIn(
            "`SH-POS-5` — Fast, full, and expensive lanes have distinct purposes and deliberate cadences.",
            compact_catalog,
        )
        self.assertIn("measured lifecycle evidence", compact_catalog.lower())
        self.assertIn("static lifecycle evidence", compact_catalog.lower())
        self.assertIn("safely amortized", compact_catalog.lower())

        integration = " ".join(read(INTEGRATION).split())
        self.assertIn("SH-HC-7", integration)
        self.assertIn("SH-LC-7", integration)
        self.assertIn("SH-POS-6", integration)
        self.assertIn("cheap deterministic setup", integration)
        self.assertIn("distinct assertions", integration)
        self.assertIn("failure-safe cleanup", integration)
        self.assertIn("do not consolidate tests merely because their setup text matches", integration.lower())
        self.assertIn("never request new instrumentation during an ordinary audit", integration.lower())

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
            "test-quality-behavior-lifecycle-measured-budget-breach",
            "test-quality-behavior-lifecycle-static-repetition",
            "test-quality-behavior-lifecycle-safe-amortization",
            "test-quality-behavior-lifecycle-cheap-distinct-tests",
            "test-quality-behavior-lifecycle-success-only-cleanup",
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
        self.assertIn("SH-LC-5", golden["TQA-GOLD-0048"]["expected_suite_health_smells"])
        self.assertIn("SH-LC-4", golden["TQA-GOLD-0049"]["expected_suite_health_smells"])
        self.assertIn("SH-LC-6", golden["TQA-GOLD-0050"]["expected_suite_health_smells"])
        self.assertEqual([], golden["TQA-GOLD-0051"]["expected_suite_health_smells"])
        self.assertIn("SH-POS-5", golden["TQA-GOLD-0051"]["expected_suite_health_positives"])

        lifecycle_cases = {
            "TQA-GOLD-0052": ("measured", "supported-positive", ["SH-HC-1", "SH-HC-7"], []),
            "TQA-GOLD-0053": ("inferred", "unknown-evidence-gap", ["SH-LC-7"], []),
            "TQA-GOLD-0054": ("measured", "supported-positive", [], ["SH-POS-6"]),
            "TQA-GOLD-0055": ("measured", "supported-positive", [], []),
            "TQA-GOLD-0056": ("unknown", "substantiated-finding", [], []),
        }
        for case_id, (attribution, safety, smells, positives) in lifecycle_cases.items():
            with self.subTest(case_id=case_id):
                case = golden[case_id]
                self.assertEqual(attribution, case["expected_cost_attribution"])
                self.assertEqual(safety, case["expected_lifecycle_safety"])
                self.assertEqual(smells, case["expected_suite_health_smells"])
                self.assertEqual(positives, case["expected_suite_health_positives"])
        self.assertEqual(["I-HC-A9"], golden["TQA-GOLD-0056"]["expected_smells"])
        self.assertIn("unsafe-sharing-recommendation", golden["TQA-GOLD-0053"]["forbidden_actions"])
        self.assertIn("setup-text-consolidation", golden["TQA-GOLD-0055"]["forbidden_actions"])

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

        for path in (REPO_ROOT / "docs/using-skills.md", REPO_ROOT / "CLAUDE.md", REPO_ROOT / "AGENTS.md"):
            with self.subTest(path=path.name):
                text = read(path)
                self.assertIn("suite health", text.lower())
                self.assertIn("setup/teardown lifecycle", text.lower())

    def test_suite_recovery_program_is_propose_only_and_deep_gated(self) -> None:
        self.assertTrue(RECOVERY.is_file(), RECOVERY)
        recovery = read(RECOVERY)
        recovery_compact = " ".join(recovery.split())
        recovery_lower = recovery_compact.lower()

        headings = (
            "## Stance",
            "## Inputs",
            "## Program steps",
            "### 1. Baseline",
            "### 2. Lane split first",
            "### 3. Ratchet budget",
            "### 4. Slow tail first",
            "### 5. Runner levers",
            "### 6. Cadence and exit",
            "## Output block",
            "## Forbidden",
        )
        positions = []
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(f"\n{heading}\n", recovery)
                positions.append(recovery.index(f"\n{heading}\n"))
        self.assertEqual(positions, sorted(positions))
        fenced_blocks = re.findall(r"```markdown\n(.*?)```", recovery, flags=re.S)
        self.assertTrue(any("## Suite recovery program" in block for block in fenced_blocks))

        self.assertIn("The audit edits, deletes, quarantines, or reschedules nothing", recovery_compact)
        self.assertIn("runs nothing beyond the Deep evidence ladder's already-authorized runs", recovery_compact)
        self.assertIn("`tdd-policy`", recovery)

        for disposition, gate in (
            ("`move down`", "the lower-level test fails for the same regression"),
            ("`consolidate`", "immutable or safely resettable infrastructure"),
            ("`consolidate`", "never from matching setup text"),
            ("`schedule later`", "cadence, owner, exit criterion"),
            ("`verify-then-retire`", "distinct-contract review"),
            ("`verify-then-retire`", "controlled removal, mutation, or failure attribution"),
        ):
            with self.subTest(disposition=disposition, gate=gate):
                self.assertIn(disposition, recovery)
                self.assertIn(gate, recovery_compact)
        self.assertIn("`strengthen`", recovery)
        self.assertIn("`keep`", recovery)
        for field in ("evidence gate", "acceptance command", "expected impact", "effort", "owner"):
            with self.subTest(field=field):
                self.assertIn(field, recovery_lower)
        for limit in (
            "timing coverage",
            "falls back to static level classification",
            "configured runner's own report flag",
            "never a request for new instrumentation",
        ):
            with self.subTest(limit=limit):
                self.assertIn(limit, recovery_lower)
        for ratchet in (
            "equal to the measured baseline",
            "slower than the last recorded run",
            "`feedback-budget`",
            "the audit proposes the value, the project declares it",
        ):
            with self.subTest(ratchet=ratchet):
                self.assertIn(ratchet, recovery_lower)
        for code in ("SH-LC-5", "SH-POS-5", "SH-HC-1", "SH-HC-3", "SH-POS-3"):
            with self.subTest(code=code):
                self.assertIn(f"`{code}`", recovery)
        self.assertIn("## forbidden", recovery_lower)
        forbidden = recovery_lower[recovery_lower.index("## forbidden"):]
        for term in ("similarity", "count", "ratio", "never failed", "instrumentation", "healthy suite", "pyramid"):
            with self.subTest(term=term):
                self.assertIn(term, forbidden)

        skill = read(SKILL)
        skill_compact = " ".join(skill.split())
        load_start = "In Deep mode only, when the Suite health block substantiates"
        load_end = "a healthy suite does not load it"
        self.assertIn(load_start, skill_compact)
        self.assertIn(load_end, skill_compact)
        begin = skill_compact.index(load_start)
        load_paragraph = skill_compact[begin : skill_compact.index(load_end, begin) + len(load_end)]
        for code in ("SH-HC-1", "SH-HC-2", "SH-HC-7", "SH-LC-2", "SH-LC-4", "SH-LC-5"):
            with self.subTest(code=code):
                self.assertIn(f"`{code}`", load_paragraph)
        self.assertIn("references/procedures/suite-recovery.md", load_paragraph)
        self.assertIn("Quick never loads it", load_paragraph)
        self.assertIn("suite recovery program when its load condition holds", skill_compact)
        self.assertIn("## Rules and Stop Conditions", skill)
        rules_compact = " ".join(skill[skill.index("## Rules and Stop Conditions") :].split())
        self.assertIn("advisory", rules_compact)
        self.assertIn("edits, deletes, quarantines, or reschedules nothing", rules_compact)

        output = read(OUTPUT)
        self.assertIn("## Prioritized remediation worklist", output)
        worklist_compact = " ".join(output[output.index("## Prioritized remediation worklist") :].split())
        self.assertIn("suite-recovery.md", worklist_compact)
        self.assertIn("## Suite recovery program", worklist_compact)
        self.assertIn("propose-only", worklist_compact)
        self.assertIn("The audit remains advisory", worklist_compact)

        grounding_compact = " ".join(read(GROUNDING).split())
        for phrase in ("propose-only", "§2", "lean-audit", "slow-tail", "`feedback-budget`"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, grounding_compact)

        skill_description = frontmatter_description(skill)
        agent_description = frontmatter_description(read(AGENT))
        self.assertEqual(skill_description, agent_description)
        self.assertIn("suite recovery programs", skill_description)
        self.assertIn("suite strategy, runtime growth, portfolio maintenance", skill_description)
        self.assertLess(len(skill_description), 1024)

    def test_suite_recovery_evidence_is_declared(self) -> None:
        scenarios = {row["id"]: row for row in json.loads(read(SCENARIOS))}
        recovery_path = (
            "souroldgeezer-audit/skills/test-quality-audit/"
            "references/procedures/suite-recovery.md"
        )
        self.assertIn("deep-python-suite-recovery", scenarios)
        recovery_files = scenarios["deep-python-suite-recovery"]["files"]
        self.assertIn(recovery_path, recovery_files)
        self.assertTrue(set(scenarios["deep-python-suite"]["files"]).issubset(recovery_files))
        for scenario_id in ("deep-python-suite", "deep-nextjs-suite", "quick-node-unit", "quick-python-unit"):
            with self.subTest(scenario_id=scenario_id):
                self.assertNotIn(recovery_path, scenarios[scenario_id]["files"])

        behaviors = read_jsonl(BEHAVIORS)
        for case_id in (
            "test-quality-behavior-suite-recovery-program",
            "test-quality-behavior-suite-recovery-static-only",
            "test-quality-behavior-suite-recovery-not-emitted-when-healthy",
        ):
            with self.subTest(case_id=case_id):
                self.assertIn(case_id, behaviors)
                case = behaviors[case_id]
                self.assertEqual("synthetic", case["source_kind"])
                self.assertFalse(case["contains_third_party_text"])
                for field in ("expected_artifacts", "required_checks", "forbidden_behaviors"):
                    self.assertTrue(case[field], field)

        triggers = read_jsonl(TRIGGERS)
        self.assertIn("test-quality-trigger-yes-suite-recovery-plan", triggers)
        self.assertTrue(triggers["test-quality-trigger-yes-suite-recovery-plan"]["expected_activation"])

        golden = read_jsonl(GOLDEN)
        self.assertIn("TQA-GOLD-0066", golden)
        case = golden["TQA-GOLD-0066"]
        self.assertEqual("deep", case["mode"])
        self.assertEqual(["SH-LC-5", "SH-LC-4", "SH-LC-2"], case["expected_suite_health_smells"])
        self.assertEqual("move down", case["expected_action"])
        self.assertTrue(
            {"delete-from-coverage-alone", "edit-tests", "add-instrumentation"}.issubset(case["forbidden_actions"])
        )

    def test_structure_coupled_record_is_verify_then_retire_evidence(self) -> None:
        output = " ".join(read(OUTPUT).split())
        self.assertIn("`structure-coupled`", output)
        self.assertIn("stronger than similarity", output)
        self.assertIn("never retires a test by itself", output)
        self.assertIn("accessible history", output)
        self.assertIn("ask for no instrumentation", output)
        recovery = " ".join(read(RECOVERY).split())
        self.assertIn("`structure-coupled`", recovery)
        self.assertIn("deep-mode-output-format.md", recovery)

        case = read_jsonl(BEHAVIORS)["test-quality-behavior-structure-coupled-record"]
        self.assertEqual("synthetic", case["source_kind"])
        self.assertFalse(case["contains_third_party_text"])
        for field in ("expected_artifacts", "required_checks", "forbidden_behaviors"):
            self.assertTrue(case[field], field)
        self.assertIn("verify-then-retire", " ".join(case["required_checks"]))
        self.assertIn("delet", " ".join(case["forbidden_behaviors"]))


if __name__ == "__main__":
    unittest.main()
