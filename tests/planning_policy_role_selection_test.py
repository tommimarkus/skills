"""Source-contract checks; synthetic rubrics do not measure live host behavior."""
import json
import re
import unittest
from pathlib import Path

from tests.surface_test_lib import compact, section

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "souroldgeezer-policy"
SKILL = POLICY / "skills/planning-policy"
ROLES = ("mechanical", "standard", "analytical", "deep")


class PlanningRoleSelectionTest(unittest.TestCase):
    def test_all_entrypoints_route_lightweight_and_managed_assignments(self):
        for role in ROLES:
            with self.subTest(role=role):
                text = (POLICY / f"agents/plan-step-{role}.md").read_text()
                self.assertLessEqual(len(text.splitlines()), 85)
                self.assertNotIn("Managed v5 execution only.", text)
                for marker in ("workflow: standard", "workflow: strict", "managed-worker.md",
                               "standard-assignment-and-return", "malformed", "conflicting",
                               "run/step/attempt", "before inspection or tool use"):
                    self.assertIn(marker, text)
                self.assertNotIn("Return exactly one UTF-8 JSON object", text)
                self.assertNotIn("check-changeset", text)

    def test_role_selection_is_separate_from_workflow_and_has_no_quota(self):
        core = compact(section((SKILL / "references/core-workflow.md").read_text(), "## Role selection"))
        for role in ROLES:
            self.assertIn(f"plan-step-{role}", core)
        for marker in ("simplest suitable role", "independent of workflow", "no quota",
                       "actual executor", "fallback", "explicit pins", "capabilities"):
            self.assertIn(marker, core)
        brief = compact(section((SKILL / "references/core-workflow.md").read_text(),
                                "## Standard assignment and return"))
        for marker in ("workflow: standard", "role", "outcome", "boundary", "decisions",
                       "prerequisite", "worktree", "acceptance", "escalation", "No managed schema"):
            self.assertIn(marker, brief)

    def test_standard_host_routes_select_existing_roles_without_managed_load(self):
        for host in ("claude-code", "codex"):
            text = section((SKILL / f"extensions/{host}.md").read_text(), "## Standard workflow")
            self.assertIn("role selection", text)
            self.assertIn("fallback", text)
            self.assertIn("explicit pins", text)
            self.assertNotIn("managed-worker.md", text)
            self.assertNotIn("host-tiers.json", text)
            self.assertNotIn("general-purpose assignment, not", text)
            if host == "claude-code":
                self.assertIn("souroldgeezer-policy:plan-step-", text)
            else:
                self.assertIn('fork_turns: "none"', text)
                self.assertIn("role instructions", text)
                self.assertIn("register", text)
        for role in ROLES:
            content = (POLICY / f"agents/plan-step-{role}.md").read_text()
            tools = re.search(r"(?m)^tools: (.+)$", content).group(1)
            expected_tools = "Bash, Read, Grep, Glob, Edit, Write"
            if role != "mechanical":
                expected_tools += ", Skill"
            self.assertEqual(expected_tools, tools)
        for verifier in (POLICY / "agents").glob("plan-verify-*.md"):
            self.assertNotIn("workflow: standard", verifier.read_text())

    def test_managed_contract_remains_available_on_demand(self):
        text = compact((SKILL / "references/managed-worker.md").read_text())
        for marker in ("Assignments use v5", "planning-capability-binding-v1", "cohesive_outcome",
                       "decomposition", "retry-remediation-v1", "ledger alone", "run-acceptance",
                       "check-changeset", "bounded-step-return-v1", "<=8 KiB", "plan_context",
                       "parent owns integration and final verification"):
            self.assertIn(marker, text)

    def test_synthetic_cases_cover_role_host_stop_and_review_boundaries(self):
        cases = [json.loads(line) for line in
                 (SKILL / "references/evals/role-selection-cases.jsonl").read_text().splitlines()]
        ids = {case["id"] for case in cases}
        for role in ROLES:
            for host in ("claude-code", "codex"):
                self.assertIn(f"standard-{host}-{role}", ids)
        for case_id in ("native-fallback", "pin-unavailable", "capability-missing", "material-decision",
                        "managed-valid", "managed-malformed", "workflow-conflict", "workflow-missing",
                        "standard-review-parent-verification"):
            self.assertIn(case_id, ids)
        for case in cases:
            self.assertEqual("synthetic", case["source_kind"])
            self.assertFalse(case["contains_third_party_text"])
            self.assertTrue(case["required_checks"])
            self.assertTrue(case["forbidden_behaviors"])


if __name__ == "__main__":
    unittest.main()
