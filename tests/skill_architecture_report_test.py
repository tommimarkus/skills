import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE = REPO_ROOT / "scripts" / "skill_architecture_report.py"
WRAPPER = REPO_ROOT / "scripts" / "skill-architecture-report.sh"
LEDGER = REPO_ROOT / "tests" / "skill_architecture_report_ledger.jsonl"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def load_engine():
    spec = importlib.util.spec_from_file_location("skill_architecture_report", ENGINE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "repo"
            self.make_noisy_fixture(fixture)

            result = run_engine(fixture)

        self.assertEqual(result.returncode, 0, result.stderr)
        output = result.stdout
        self.assertIn("# Skill Architecture Craft Report", output)
        self.assertIn("## Summary", output)
        self.assertIn("## Standard Coverage", output)
        self.assertIn("- Weight policy: `fixed by severity; catalog entries cannot tune weights`", output)
        self.assertIn("- Severity weights: `blocker=13, high=8, medium=5, low=3`", output)
        self.assertIn("- Category floor: `80.0% minimum per report group`", output)
        self.assertIn("- Categories below floor: `none`", output)
        self.assertRegex(output, r"Total weighted coverage: `9[0-9]\.[0-9]%`|Total weighted coverage: `100\.0%`")
        self.assertIn("- Deterministic:", output)
        self.assertIn("- Heuristic:", output)
        self.assertIn("- Manual prompt:", output)
        self.assertIn("- Uncovered:", output)
        self.assertIn("SAC-TRIGGER-AGGRESSIVE (medium)", output)
        self.assertIn("SAC-TRIGGER-MISSING-CONTEXT (high)", output)
        self.assertIn("SAC-WORKFLOW-OUTPUT (high)", output)
        self.assertIn("SAC-REF-BROKEN-LINK (high)", output)
        self.assertIn("SAC-REF-UNADVERTISED-SUPPORT", output)
        self.assertIn("SAC-RUNTIME-DEFAULT-PROMPTS (medium)", output)
        self.assertIn("SAC-RUNTIME-MISSING-OPENAI (high)", output)
        self.assertIn("SAC-DOC-MISSING-ENTRYPOINT (low)", output)
        self.assertIn("Path: `example-plugin/skills/noisy-skill/SKILL.md`", output)
        self.assertIn("Path: `example-plugin/skills/noisy-skill/references/extra.md`", output)
        self.assertIn("references/README.md", output)
        self.assertIn("Claude impact:", output)
        self.assertIn("Codex impact:", output)
        self.assertIn("Next action:", output)
        self.assertIn("Verify/rerun:", output)
        self.assertIn("scripts/skill-architecture-report.sh .", output)
        self.assertIn("## Next Iteration", output)

    def test_clean_fixture_has_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "clean-repo"
            self.make_clean_fixture(fixture)

            result = run_engine(fixture)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Findings: 0 total", result.stdout)
        self.assertIn("No target groups.", result.stdout)
        self.assertIn("No current advisory findings.", result.stdout)

    def test_usage_errors_exit_nonzero(self) -> None:
        missing = run_engine(REPO_ROOT / "does-not-exist")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("Error:", missing.stderr)

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
        self.assertIn("findings", payload)
        self.assertIn("rules", payload)
        self.assertTrue(any(finding["code"] == "SAC-TRIGGER-AGGRESSIVE" for finding in payload["findings"]))
        self.assertEqual("fixed by severity; catalog entries cannot tune weights", payload["coverage"]["weight_policy"])

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
            write(repo / "AGENTS.md", "fixture agents\n")
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

            codex_agent_path = f".codex/agents/{skill_name}.toml"
            if not case.get("omit_codex_agent", False) and codex_agent_path not in explicit_paths:
                write(
                    repo / codex_agent_path,
                    (
                        f"name = \"{skill_name}\"\n"
                        f"description = \"Fixture Codex wrapper for {skill_name}.\"\n"
                        "sandbox_mode = \"workspace-write\"\n"
                        "developer_instructions = \"\"\"\n"
                        f"You are a fixture practitioner. Use the {skill_name} skill as the source of truth.\n"
                        "Always emit the footer disclosure required by the skill.\n"
                        "\"\"\"\n"
                    ),
                )

            openai_path = f"{skill_dir}/agents/openai.yaml"
            if case.get("omit_openai", False) or openai_path in explicit_paths:
                continue
            write(
                repo / openai_path,
                f"name: {skill_name}\ndescription: {description}\n",
            )

    def make_noisy_fixture(self, fixture: Path) -> None:
        write(
            fixture / "example-plugin/.codex-plugin/plugin.json",
            """
            {
              "name": "example-plugin",
              "version": "1.0.0",
              "description": "Fixture plugin",
              "skills": "./skills/",
              "interface": {
                "defaultPrompt": ["one", "two", "three", "four"]
              }
            }
            """,
        )
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
            fixture / "example-plugin/skills/quiet-skill/agents/openai.yaml",
            """
            name: quiet-skill
            description: Fixture metadata.
            """,
        )
        write(
            fixture / ".claude/skills/internal-helper/SKILL.md",
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
        write(fixture / "AGENTS.md", "fixture agents\n")
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

            | Support | Loaded when |
            |---|---|
            | `references/table/entry.md` | Table support behavior is under test |
            """,
        )
        write(
            fixture / "example-plugin/skills/clean-skill/agents/openai.yaml",
            """
            name: clean-skill
            description: Use when validating a clean fixture skill with explicit boundaries, outputs, stop conditions, and rerun guidance.
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
        write(
            fixture / ".codex/agents/clean-skill.toml",
            """
            name = "clean-skill"
            description = "Fixture Codex wrapper for clean-skill."
            sandbox_mode = "workspace-write"
            developer_instructions = \"\"\"
            You are a fixture practitioner. Use the clean-skill skill as the source of truth.
            Always emit the footer disclosure required by the skill.
            \"\"\"
            """,
        )
        write(fixture / "example-plugin/skills/clean-skill/references/group/one.md", "# Grouped Support\n")
        write(fixture / "example-plugin/skills/clean-skill/references/group/README.md", "# Grouped Support Index\n")
        write(fixture / "example-plugin/skills/clean-skill/references/table/entry.md", "# Table Support\n")


if __name__ == "__main__":
    unittest.main()
