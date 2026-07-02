# lean-audit:dup-intentional — parallel per-case test bodies kept literal for readability
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, load_script_module, run_git, write_fixture as write

ENGINE = REPO_ROOT / "scripts" / "skill_architecture_report.py"
WRAPPER = REPO_ROOT / "scripts" / "skill-architecture-report.sh"
LEDGER = REPO_ROOT / "tests" / "skill_architecture_report_ledger.jsonl"


def load_engine():
    return load_script_module("skill_architecture_report", ENGINE)


def run_engine(repo: Path) -> subprocess.CompletedProcess[str]:
    return run_engine_args(str(repo))


def run_engine_args(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENGINE), *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def load_ledger_cases() -> list[dict]:
    cases = []
    with LEDGER.open(encoding="utf-8") as ledger:
        for line_number, line in enumerate(ledger, start=1):
            if line.strip():
                case = json.loads(line)
                case["_line"] = line_number
                cases.append(case)
    return cases


class SkillArchitectureReportTest(unittest.TestCase):
    def _run_engine_on_fixture(self, make_fixture, dirname: str = "repo") -> str:
        """Build a fixture with make_fixture(fixture_path), run the engine on it, and
        return stdout. Shared setup for the report-fixture assertion tests."""
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / dirname
            make_fixture(fixture)
            result = run_engine(fixture)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_replacement_ledger_measures_at_least_500_skill_only_findings(self) -> None:
        module = load_engine()
        cases = load_ledger_cases()

        calibration = module.calculate_replacement_calibration(REPO_ROOT)

        self.assertGreaterEqual(len(cases), 500)
        self.assertGreaterEqual(calibration.gold_finding_count, 500)
        self.assertGreaterEqual(calibration.automated_recall_percentage, 90.0)
        self.assertLessEqual(calibration.manual_only_finding_count, calibration.gold_finding_count * 0.1)

    def test_json_output_reports_empirical_replacement_recall(self) -> None:
        result = run_engine_args("--format", "json", str(REPO_ROOT))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        calibration = payload["replacement_calibration"]
        self.assertEqual("tests/skill_architecture_report_ledger.jsonl", calibration["ledger_path"])
        self.assertGreaterEqual(calibration["case_count"], 500)
        self.assertGreaterEqual(calibration["gold_finding_count"], 500)
        self.assertGreaterEqual(calibration["automated_recall_percentage"], 90.0)

    def test_rule_catalog_has_required_fields_and_coverage_budget(self) -> None:
        module = load_engine()

        rules = module.build_rule_catalog()
        self.assertNotIn("weight", module.Rule.__dataclass_fields__)
        self.assertGreaterEqual(len(rules), 20)
        for rule in rules:
            with self.subTest(rule=rule.id):
                self.assertTrue(rule.id.startswith("SAC-"))
                self.assertIn(rule.category, module.REPORT_GROUPS)
                self.assertIn(rule.severity, {"blocker", "high", "medium", "low"})
                self.assertTrue(rule.standard_anchor.startswith("docs/skill-architecture.md#"))
                self.assertIn(rule.detector_type, {"deterministic", "heuristic", "manual-prompt", "uncovered"})
                self.assertEqual(rule.weight, module.SEVERITY_WEIGHTS[rule.severity])
                self.assertTrue(rule.fixture_cases)
                self.assertTrue(rule.remediation)

        coverage = module.calculate_coverage(rules)
        self.assertGreater(coverage.deterministic_weight, 0)
        self.assertGreater(coverage.heuristic_weight, 0)
        self.assertGreater(coverage.manual_prompt_weight, 0)
        self.assertGreaterEqual(coverage.weighted_percentage, 90.0)

    def test_fixture_report_preserves_existing_findings_and_adds_coverage(self) -> None:
        output = self._run_engine_on_fixture(self.make_noisy_fixture)

        self.assertRegex(output, r"Total weighted coverage: `9[0-9]\.[0-9]%`|Total weighted coverage: `100\.0%`")
        for marker in (
            "# Skill Architecture Craft Report",
            "## Summary",
            "## Standard Coverage",
            "## Behavioral Evidence Adoption",
            "- Weight policy: `fixed by severity; catalog entries cannot tune weights`",
            "- Severity weights: `blocker=13, high=8, medium=5, low=3`",
            "- Category floor: `80.0% minimum per report group`",
            "- Categories below floor: `none`",
            "- Deterministic:",
            "- Heuristic:",
            "- Manual prompt:",
            "- Uncovered:",
            "SAC-TRIGGER-AGGRESSIVE (medium)",
            "SAC-TRIGGER-MISSING-CONTEXT (high)",
            "SAC-WORKFLOW-OUTPUT (high)",
            "SAC-EVAL-HIDDEN-ARTIFACT (high)",
            "SAC-EVAL-TRIGGER-SCHEMA (high)",
            "SAC-REF-BROKEN-LINK (high)",
            "SAC-REF-UNADVERTISED-SUPPORT",
            "SAC-RUNTIME-MISSING-CLAUDE-AGENT (high)",
            "SAC-DOC-MISSING-ENTRYPOINT (low)",
            "Path: `example-plugin/skills/noisy-skill/SKILL.md`",
            "Path: `example-plugin/skills/noisy-skill/references/extra.md`",
            "references/README.md",
            "Claude impact:",
            "Next action:",
            "Verify/rerun:",
            "scripts/skill-architecture-report.sh .",
            "## Next Iteration",
        ):
            self.assertIn(marker, output)

    def test_clean_fixture_has_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "clean-repo"
            self.make_clean_fixture(fixture)

            result = run_engine(fixture)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Findings: 0 total", result.stdout)
        self.assertIn("No target groups.", result.stdout)
        self.assertIn("No current advisory findings.", result.stdout)

    def test_private_plugin_root_reference_is_reported(self) -> None:
        module = load_engine()
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "repo"
            self.make_private_plugin_root_reference_fixture(fixture)

            findings = module.collect_findings(fixture)

        finding_pairs = {(finding.code, finding.path) for finding in findings}
        self.assertIn(
            (
                "SAC-REF-PRIVATE-PLUGIN-ROOT",
                "example-plugin/references/private-skill-procedures/check.md",
            ),
            finding_pairs,
        )

    def test_documented_shared_plugin_root_reference_is_allowed(self) -> None:
        module = load_engine()
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "repo"
            self.make_documented_shared_plugin_root_reference_fixture(fixture)

            findings = module.collect_findings(fixture)

        self.assertNotIn("SAC-REF-PRIVATE-PLUGIN-ROOT", {finding.code for finding in findings})

    def test_behavioral_evidence_adoption_is_reported_without_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "clean-repo"
            self.make_clean_fixture(fixture)

            result = run_engine_args("--format", "json", str(fixture))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        adoption = payload["behavioral_evidence_adoption"]
        self.assertEqual(1, adoption["skill_count"])
        self.assertEqual(1, adoption["trigger_eval_pack_count"])
        self.assertEqual(1, adoption["behavior_eval_pack_count"])
        self.assertEqual(1, adoption["source_grounding_count"])
        self.assertEqual(0, adoption["high_risk_skill_count"])
        self.assertEqual(0, payload["summary"]["finding_count"])

    def test_eval_artifacts_have_specific_findings(self) -> None:
        output = self._run_engine_on_fixture(self.make_eval_issue_fixture)

        self.assertIn("SAC-EVAL-HIDDEN-ARTIFACT (high)", output)
        self.assertIn("SAC-EVAL-TRIGGER-SCHEMA (high)", output)
        self.assertIn("SAC-EVAL-BEHAVIOR-SCHEMA (high)", output)
        self.assertIn("SAC-EVAL-IP-HYGIENE (high)", output)
        self.assertIn("references/evals/trigger-cases.jsonl", output)

    def test_high_risk_skill_requires_rationalization_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "repo"
            self.make_high_risk_issue_fixture(fixture)

            result = run_engine(fixture)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SAC-WORKFLOW-RATIONALIZATION-GATE (high)", result.stdout)

    def test_usage_errors_exit_nonzero(self) -> None:
        missing = run_engine(REPO_ROOT / "does-not-exist")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("Error:", missing.stderr)

    def test_cache_directories_are_ignored_during_discovery(self) -> None:
        module = load_engine()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            write(
                repo / ".cache/plugin/skills/cached-skill/SKILL.md",
                """
                ---
                name: cached-skill
                description: Always use this cached fixture for anything.
                ---

                Cached plugin content should not be discovered.
                """,
            )
            write(
                repo / ".cache/plugin/.claude-plugin/plugin.json",
                """
                {
                  "name": "cached-plugin",
                  "version": "1.0.0",
                  "description": "Cached plugin metadata"
                }
                """,
            )

            self.assertEqual([], module.find_skill_files(repo))

    def test_shell_wrapper_help_smoke(self) -> None:
        result = subprocess.run(
            ["bash", str(WRAPPER), "--help"],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage: scripts/skill-architecture-report.sh [--format markdown|json] [--strict] [repo-root]", result.stdout)

    def test_json_output_is_machine_readable_for_thin_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "repo"
            self.make_noisy_fixture(fixture)

            result = run_engine_args("--format", "json", str(fixture))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(str(fixture.resolve()), payload["scope"]["repo"])
        self.assertIn("coverage", payload)
        self.assertIn("behavioral_evidence_adoption", payload)
        self.assertIn("findings", payload)
        self.assertIn("rules", payload)
        self.assertTrue(any(finding["code"] == "SAC-TRIGGER-AGGRESSIVE" for finding in payload["findings"]))
        self.assertEqual("fixed by severity; catalog entries cannot tune weights", payload["coverage"]["weight_policy"])

    def test_design_skills_have_brownfield_assimilation_contract(self) -> None:
        design_root = REPO_ROOT / "souroldgeezer-design"
        expected_eval_ids = {
            "software-design": "software-design-behavior-brownfield-assimilation",
            "app-design": "app-design-behavior-brownfield-assimilation",
            "infra-design": "infra-design-behavior-brownfield-assimilation",
        }

        for skill_name, expected_eval_id in expected_eval_ids.items():
            with self.subTest(skill=skill_name):
                skill_dir = design_root / "skills" / skill_name
                procedure = skill_dir / "references" / "procedures" / "project-assimilation.md"
                skill_body = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                behavior_cases = (skill_dir / "references" / "evals" / "behavior-cases.jsonl").read_text(encoding="utf-8")

                self.assertTrue(procedure.is_file(), f"missing {procedure.relative_to(REPO_ROOT)}")
                procedure_body = procedure.read_text(encoding="utf-8")
                self.assertIn("Project assimilation:", procedure_body)
                self.assertIn("Reused:", procedure_body)
                self.assertIn("Legacy debt:", procedure_body)
                self.assertIn("Migrations performed:", procedure_body)
                self.assertIn("project-assimilation.md", skill_body)
                self.assertIn(expected_eval_id, behavior_cases)

        claude_manifest = json.loads((design_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        marketplace_plugin = next(plugin for plugin in marketplace["plugins"] if plugin["name"] == "souroldgeezer-design")

        # Cross-surface sync, not a pinned literal: the marketplace entry is the
        # in-test source of truth and the manifest must agree with it. The CalVer
        # value is assigned at integration on main (scripts/version_stamp.py), so
        # pinning it here would only add a hand-edited sibling-sync cell per bump.
        canonical = marketplace_plugin["version"]
        self.assertRegex(canonical, r"^\d{4}\.\d{2}\.\d+$")
        self.assertEqual(claude_manifest["version"], canonical)

    def test_strict_mode_exits_nonzero_when_tool_findings_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "repo"
            self.make_noisy_fixture(fixture)

            result = run_engine_args("--strict", str(fixture))

        self.assertEqual(1, result.returncode)
        self.assertIn("# Skill Architecture Craft Report", result.stdout)

    def test_ledger_cases_are_unique_and_ordered(self) -> None:
        self.assertTrue(LEDGER.is_file(), "missing test ledger")
        complexity_rank = {"simple": 1, "moderate": 2, "complex": 3, "adversarial": 4}
        cases = load_ledger_cases()
        self.assertGreaterEqual(len(cases), 25)

        seen_ids: set[str] = set()
        seen_intents: set[str] = set()
        seen_gold_scenarios: set[tuple[str, str]] = set()
        seen_fingerprints: set[str] = set()
        last_rank = 0
        for index, case in enumerate(cases, start=1):
            with self.subTest(case=case.get("id"), line=case["_line"]):
                self.assertRegex(case["id"], r"^SAC-T\d{5}$")
                self.assertEqual(f"SAC-T{index:05d}", case["id"])
                self.assertNotIn(case["id"], seen_ids)
                seen_ids.add(case["id"])

                self.assertNotIn(case["intent"], seen_intents)
                seen_intents.add(case["intent"])
                if "gold_issue" in case:
                    self.assertIn("code", case["gold_issue"])
                    self.assertIn("scenario", case["gold_issue"])
                    self.assertIn(case["gold_issue"]["code"], case.get("expected_codes", []))
                    gold_scenario = (case["gold_issue"]["code"], case["gold_issue"]["scenario"])
                    self.assertNotIn(gold_scenario, seen_gold_scenarios)
                    seen_gold_scenarios.add(gold_scenario)
                else:
                    self.assertTrue(case.get("guard"), "non-gold ledger cases must be explicit guard cases")
                    self.assertTrue(case.get("absent_codes"), "guard cases must assert absent finding codes")

                rank = complexity_rank[case["complexity"]]
                self.assertGreaterEqual(rank, last_rank)
                last_rank = rank

                fingerprint_payload = {
                    "files": case["files"],
                    "expected_codes": case.get("expected_codes", []),
                    "expected_findings": case.get("expected_findings", []),
                    "absent_codes": case.get("absent_codes", []),
                    "expect_exact_codes": case.get("expect_exact_codes", False),
                }
                fingerprint = hashlib.sha256(
                    json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
                ).hexdigest()
                self.assertNotIn(fingerprint, seen_fingerprints)
                seen_fingerprints.add(fingerprint)

    def test_ledger_cases_execute_expected_findings(self) -> None:
        module = load_engine()
        for case in load_ledger_cases():
            with self.subTest(case=case["id"], intent=case["intent"]):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp) / "repo"
                    self.make_ledger_fixture(repo, case)

                    findings = module.collect_findings(repo)

                finding_pairs = {(finding.code, finding.path) for finding in findings}
                finding_codes = {finding.code for finding in findings}
                if case.get("expect_exact_codes", False):
                    self.assertEqual(set(case.get("expected_codes", [])), finding_codes)
                for code in case.get("expected_codes", []):
                    self.assertIn(code, finding_codes)
                for expected in case.get("expected_findings", []):
                    self.assertIn((expected["code"], expected["path"]), finding_pairs)
                for code in case.get("absent_codes", []):
                    self.assertNotIn(code, finding_codes)

    def make_ledger_fixture(self, repo: Path, case: dict) -> None:
        if not case.get("omit_repo_guidance", False):
            write(repo / "CLAUDE.md", "fixture claude\n")

        explicit_paths = {file["path"] for file in case["files"]}
        skill_dirs = []
        for file in case["files"]:
            write(repo / file["path"], file["content"])
            if file["path"].endswith("/SKILL.md") and "/skills/" in file["path"]:
                skill_dirs.append(file["path"].removesuffix("/SKILL.md"))

        for skill_dir in skill_dirs:
            skill_name = Path(skill_dir).name
            plugin_dir = skill_dir.split("/skills/", 1)[0]
            skill_frontmatter = (repo / skill_dir / "SKILL.md").read_text(encoding="utf-8").split("---", 2)
            description = "Fixture metadata."
            if len(skill_frontmatter) >= 3:
                for line in skill_frontmatter[1].splitlines():
                    if line.startswith("description:"):
                        description = line.split(":", 1)[1].strip()
                        break
            agent_path = f"{plugin_dir}/agents/{skill_name}.md"
            if not case.get("omit_claude_agent", False) and agent_path not in explicit_paths:
                write(
                    repo / agent_path,
                    f"---\nname: {skill_name}\ndescription: {description}\ntools: Skill\nmodel: sonnet\n---\n\nInvoke the skill.\n",
                )

    def make_noisy_fixture(self, fixture: Path) -> None:
        write(
            fixture / "example-plugin/skills/noisy-skill/SKILL.md",
            """
            ---
            name: noisy-skill
            description: Always use this for anything with architecture. This metadata intentionally stays vague.
            ---

            # Noisy Skill

            This skill contains a long reference-like explanation of every possible option.
            Agents should consider results and maybe write an answer.

            See [missing procedure](references/missing.md).
            See [known procedure](references/known.md).
            """,
        )
        write(fixture / "example-plugin/skills/noisy-skill/references/known.md", "# Known Procedure\n")
        write(fixture / "example-plugin/skills/noisy-skill/references/extra.md", "# Extra Procedure\n")
        write(fixture / "example-plugin/skills/noisy-skill/references/README.md", "# Maintainer Notes\n")
        write(
            fixture / "example-plugin/skills/noisy-skill/references/evals/trigger-cases.jsonl",
            """
            {"id":"bad-trigger","prompt":"quoted external prompt","expected_activation":true,"contains_third_party_text":true}
            """,
        )
        write(
            fixture / "example-plugin/skills/noisy-skill/scripts/helper.sh",
            """
            #!/usr/bin/env bash
            echo helper
            """,
        )
        write(
            fixture / "example-plugin/skills/quiet-skill/SKILL.md",
            """
            ---
            name: quiet-skill
            description: >-
              Use when producing quiet fixture output with explicit inputs, outputs,
              stop conditions, rerun guidance, and boundaries.
            ---

            # Quiet Skill

            Use this when fixture tests need a mostly clean skill.

            Inputs: fixture files.
            Output: a short report.
            Stop when the report is complete.
            Rerun the validation command after edits.
            """,
        )
        write(
            fixture / "internal-skills/internal-helper/SKILL.md",
            """
            ---
            name: internal-helper
            description: Use when checking internal fixture guidance with clear boundaries and rerun guidance.
            ---

            # Internal Helper

            Input: fixture.
            Output: advice.
            Stop when evidence is gathered.
            Rerun the report after changing guidance.
            """,
        )

    def make_clean_fixture(self, fixture: Path) -> None:
        write(fixture / "CLAUDE.md", "fixture claude\n")
        write(
            fixture / "example-plugin/skills/clean-skill/SKILL.md",
            """
            ---
            name: clean-skill
            description: Use when validating a clean fixture skill with explicit boundaries, outputs, stop conditions, and rerun guidance.
            ---

            # Clean Skill

            Use this when fixture tests need a no-finding skill.

            Inputs: fixture files.
            Evidence: cite the fixture files and command output inspected.
            Output: a short report.
            Stop when validation is complete.
            If the request is ambiguous, ask the user before proceeding.
            Rerun the report after changing this skill.
            Read references/group when grouped support behavior is under test.
            Read references/evals when changing trigger or behavioral evaluation cases.
            Read references/source-grounding.md when checking source provenance.

            | Support | Loaded when |
            |---|---|
            | `references/table/entry.md` | Table support behavior is under test |
            """,
        )
        write(
            fixture / "example-plugin/agents/clean-skill.md",
            """
            ---
            name: clean-skill
            description: Use when validating a clean fixture skill with explicit boundaries, outputs, stop conditions, and rerun guidance.
            tools: Skill
            model: sonnet
            ---

            Invoke the skill.
            """,
        )
        write(fixture / "example-plugin/skills/clean-skill/references/group/one.md", "# Grouped Support\n")
        write(fixture / "example-plugin/skills/clean-skill/references/group/README.md", "# Grouped Support Index\n")
        write(fixture / "example-plugin/skills/clean-skill/references/table/entry.md", "# Table Support\n")
        write(
            fixture / "example-plugin/skills/clean-skill/references/evals/trigger-cases.jsonl",
            """
            {"id":"clean-trigger-yes","prompt":"User asks for the clean fixture skill by name.","expected_activation":true,"reason":"Direct skill target.","source_kind":"synthetic","source_url":"","ip_handling":"original synthetic prompt; no third-party text","contains_third_party_text":false}
            {"id":"clean-trigger-no","prompt":"User asks for unrelated packaging help.","expected_activation":false,"reason":"Packaging is outside this fixture skill.","source_kind":"synthetic","source_url":"","ip_handling":"original synthetic prompt; no third-party text","contains_third_party_text":false}
            """,
        )
        write(
            fixture / "example-plugin/skills/clean-skill/references/evals/behavior-cases.jsonl",
            """
            {"id":"clean-behavior-report","prompt":"Review the clean fixture skill.","expected_artifacts":["short report"],"required_checks":["inspect SKILL.md","cite command output"],"forbidden_behaviors":["invent missing files"],"grader":"rubric: report cites inspected files and avoids invented evidence","source_kind":"synthetic","source_url":"","ip_handling":"original synthetic prompt; no third-party text","contains_third_party_text":false}
            """,
        )
        write(
            fixture / "example-plugin/skills/clean-skill/references/source-grounding.md",
            """
            # Source Grounding

            - `clean-fixture`: synthetic local fixture used for report-engine tests.
              Handling: original repo-authored scenario; no third-party text, code,
              fixtures, schemas, diagrams, or screenshots are bundled.
            """,
        )

    def make_private_plugin_root_reference_fixture(self, fixture: Path) -> None:
        write(fixture / "CLAUDE.md", "fixture claude\n")
        write(
            fixture / "example-plugin/skills/private-skill/SKILL.md",
            """
            ---
            name: private-skill
            description: Use when checking fixture private support ownership with clear inputs, outputs, and rerun guidance.
            ---

            # Private Skill

            Input: fixture files.
            Output: a short ownership report.
            Stop when validation is complete.
            Rerun the report after changing references.

            Read ../../references/private-skill-procedures/check.md when ownership checks require a detailed procedure.
            """,
        )
        write(
            fixture / "example-plugin/references/private-skill-procedures/check.md",
            "# Private Procedure\n",
        )

    def make_documented_shared_plugin_root_reference_fixture(self, fixture: Path) -> None:
        write(fixture / "CLAUDE.md", "fixture claude\n")
        write(
            fixture / "example-plugin/references/README.md",
            """
            # Plugin References

            `shared-guidance/check.md` is shared plugin-level canonical guidance for every skill in this plugin.
            """,
        )
        write(
            fixture / "example-plugin/references/shared-guidance/check.md",
            "# Shared Guidance\n",
        )
        write(
            fixture / "example-plugin/skills/first-skill/SKILL.md",
            """
            ---
            name: first-skill
            description: Use when checking fixture shared support ownership with clear inputs, outputs, and rerun guidance.
            ---

            # first-skill

            Input: fixture files.
            Output: a short shared support report.
            Stop when validation is complete.
            Rerun the report after changing references.

            Read ../../references/shared-guidance/check.md when shared plugin guidance applies.
            """,
        )

    def make_eval_issue_fixture(self, fixture: Path) -> None:
        write(fixture / "CLAUDE.md", "fixture claude\n")
        write(
            fixture / "example-plugin/skills/eval-issue-skill/SKILL.md",
            """
            ---
            name: eval-issue-skill
            description: Use when validating eval issue fixtures with explicit boundaries, outputs, stop conditions, and rerun guidance.
            ---

            # Eval Issue Skill

            Use this when fixture tests need evaluation issues.

            Inputs: fixture files.
            Evidence: cite the fixture files and command output inspected.
            Output: a short report.
            Stop when validation is complete.
            If the request is ambiguous, ask the user before proceeding.
            Rerun the report after changing this skill.
            """,
        )
        write(
            fixture / "example-plugin/agents/eval-issue-skill.md",
            """
            ---
            name: eval-issue-skill
            description: Use when validating eval issue fixtures with explicit boundaries, outputs, stop conditions, and rerun guidance.
            tools: Skill
            model: sonnet
            ---

            Invoke the skill.
            """,
        )
        write(
            fixture / "example-plugin/skills/eval-issue-skill/references/evals/trigger-cases.jsonl",
            """
            {"id":"bad-trigger","prompt":"copied external prompt","expected_activation":true,"contains_third_party_text":true}
            """,
        )
        write(
            fixture / "example-plugin/skills/eval-issue-skill/references/evals/behavior-cases.jsonl",
            """
            {"id":"bad-behavior","prompt":"missing behavioral fields","source_kind":"synthetic","ip_handling":"unclear","contains_third_party_text":false}
            """,
        )

    def make_high_risk_issue_fixture(self, fixture: Path) -> None:
        write(fixture / "CLAUDE.md", "fixture claude\n")
        write(
            fixture / "example-plugin/skills/security-audit-skill/SKILL.md",
            """
            ---
            name: security-audit-skill
            description: Use when auditing security fixtures with explicit boundaries, outputs, stop conditions, and rerun guidance.
            ---

            # Security Audit Skill

            Use this when fixture tests need a high-risk audit skill.

            Inputs: fixture files.
            Evidence: cite the fixture files and command output inspected.
            Output: a short report.
            Stop when validation is complete.
            If the request is ambiguous, ask the user before proceeding.
            Rerun the report after changing this skill.
            """,
        )
        write(
            fixture / "example-plugin/agents/security-audit-skill.md",
            """
            ---
            name: security-audit-skill
            description: Use when auditing security fixtures with explicit boundaries, outputs, stop conditions, and rerun guidance.
            tools: Skill
            model: sonnet
            ---

            Invoke the skill.
            """,
        )


class GitBackedEnumeration(unittest.TestCase):
    def _init(self, repo):
        run_git(repo, "init", "-q")
        run_git(repo, "add", "-A")
        run_git(repo, "-c", "user.email=t@t", "-c", "user.name=t",
                "-c", "commit.gpgsign=false",
                "commit", "-qm", "init")

    def test_find_skill_files_excludes_ignored_nested_worktree(self):
        module = load_engine()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            write(repo / "example-plugin/skills/real/SKILL.md",
                  "---\nname: real\ndescription: d\n---\n# Real\n")
            self._init(repo)
            write(repo / ".gitignore", ".claude/worktrees/\n")
            write(repo / ".claude/worktrees/b/example-plugin/skills/ghost/SKILL.md",
                  "---\nname: ghost\ndescription: d\n---\n# Ghost\n")
            skills = module.find_skill_files(repo.resolve())
            self.assertIn("example-plugin/skills/real/SKILL.md", skills)
            self.assertNotIn(
                ".claude/worktrees/b/example-plugin/skills/ghost/SKILL.md", skills)

    def test_path_in_repo_falls_back_when_not_git(self):
        module = load_engine()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir(parents=True)
            self.assertTrue(module.path_in_repo(repo.resolve(), "a/SKILL.md"))
            self.assertFalse(module.path_in_repo(repo.resolve(), ".venv/x/SKILL.md"))


if __name__ == "__main__":
    unittest.main()
