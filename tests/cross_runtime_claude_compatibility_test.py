import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, read_jsonl


AUDIT = REPO_ROOT / "souroldgeezer-audit"
ARCHITECTURE = REPO_ROOT / "souroldgeezer-architecture"
POLICY = REPO_ROOT / "souroldgeezer-policy"


def cases_by_id(path: Path) -> dict[str, dict]:
    return {case["id"]: case for case in read_jsonl(path)}


class CrossRuntimeClaudeCompatibilityTest(unittest.TestCase):
    def test_claude_marketplace_identity_and_plugin_copy_are_preserved(self) -> None:
        marketplace = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            marketplace["description"],
            "Claude Code plugins by Sour Old Geezer: skills for code auditing, review, "
            "and development workflows, with matching Claude Code subagents.",
        )
        entries = {entry["name"]: entry for entry in marketplace["plugins"]}
        for plugin in ["souroldgeezer-audit", "souroldgeezer-design", "souroldgeezer-architecture"]:
            with self.subTest(plugin=plugin):
                manifest = json.loads(
                    (REPO_ROOT / plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
                )
                self.assertIn("matching Claude Code subagent", manifest["description"])
                self.assertEqual(entries[plugin]["description"], manifest["description"])

    def test_claude_runtime_substitutions_remain_documented_beside_codex_resolution(self) -> None:
        surfaces = [
            ARCHITECTURE / "skills" / "architecture-design" / "SKILL.md",
            ARCHITECTURE / "skills" / "architecture-design" / "references" / "gallery.md",
            ARCHITECTURE
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "self-check.md",
            AUDIT / "skills" / "ip-hygiene" / "SKILL.md",
            AUDIT / "skills" / "lean-audit" / "SKILL.md",
        ]
        for surface in surfaces:
            content = surface.read_text(encoding="utf-8")
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                self.assertIn("${CLAUDE_SKILL_DIR}", content)
                self.assertIn("Codex", content)

        lean = (AUDIT / "skills" / "lean-audit" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", lean)

    def test_existing_claude_lean_evals_are_unchanged_and_codex_cases_are_additive(self) -> None:
        trigger_path = AUDIT / "skills" / "lean-audit" / "references" / "evals" / "trigger-cases.jsonl"
        behavior_path = AUDIT / "skills" / "lean-audit" / "references" / "evals" / "behavior-cases.jsonl"
        triggers = cases_by_id(trigger_path)
        behaviors = cases_by_id(behavior_path)

        self.assertEqual(
            triggers["lean-audit-trigger-yes-native-redundancy"]["prompt"],
            "Check whether anything in this repo reinvents features Claude Code now provides natively.",
        )
        self.assertIn("lean-audit-trigger-yes-native-redundancy-codex", triggers)

        claude_case = behaviors["lean-audit-behavior-nat-candidate-verify-cited"]
        self.assertIn("native Claude Code feature", claude_case["prompt"])
        self.assertTrue(any("claude-code-guide" in check for check in claude_case["required_checks"]))
        self.assertIn("lean-audit-behavior-nat-candidate-verify-cited-codex", behaviors)
        self.assertIn("lean-audit-behavior-nat-not-native-nonfinding-codex", behaviors)
        self.assertIn("lean-audit-behavior-nat-degraded-no-docs-codex", behaviors)

    def test_existing_claude_planning_evals_keep_native_tool_contracts(self) -> None:
        trigger_path = POLICY / "skills" / "planning-policy" / "references" / "evals" / "trigger-cases.jsonl"
        behavior_path = POLICY / "skills" / "planning-policy" / "references" / "evals" / "behavior-cases.jsonl"
        triggers = cases_by_id(trigger_path)
        behaviors = cases_by_id(behavior_path)

        self.assertIn("CLAUDE.md", triggers["planning-policy-trigger-yes-initialized"]["prompt"])
        self.assertIn("planning-policy-trigger-yes-initialized-codex", triggers)
        self.assertIn("planning-policy-trigger-yes-adopt-codex", triggers)

        enforce = behaviors["planning-policy-behavior-enforce-initialized"]
        self.assertIn("CLAUDE.md", enforce["prompt"])
        self.assertIn("call EnterPlanMode before asking anything", enforce["required_checks"])
        self.assertIn("present the approach via ExitPlanMode for approval", enforce["required_checks"])
        self.assertIn("planning-policy-behavior-enforce-initialized-codex", behaviors)
        self.assertIn("planning-policy-behavior-adopt-guidance-codex", behaviors)

        workflow = (
            POLICY / "skills" / "planning-policy" / "references" / "core-workflow.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Claude Code lane", workflow)
        self.assertIn("Codex lane", workflow)
        self.assertIn("`EnterPlanMode`", workflow)
        self.assertIn("`ExitPlanMode`", workflow)


if __name__ == "__main__":
    unittest.main()
