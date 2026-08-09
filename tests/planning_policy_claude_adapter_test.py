from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
ADAPTER = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/extensions/claude-code.md"
AGENTS = REPO_ROOT / "souroldgeezer-policy/agents"
EXPECTED_TIERS = {
    "plan-step-mechanical": ("haiku", "low"),
    "plan-step-standard": ("sonnet", "medium"),
    "plan-step-analytical": ("opus", "high"),
    "plan-step-deep": ("opus", "xhigh"),
}
RETURN_PROFILE = (
    '`"schema": "bounded-step-return-v1"`',
    "`step_id`",
    "`agent_id`",
    "`attempt_id`",
    "`changed_paths`, `acceptance`, `blockers`, `notes`,",
    "`commit_hash`",
    "`unstarted_remainder`",
    "`completed`, `blocked`, `failed`, or `oversized`",
    "32 safe repository-relative",
    "`finding`",
    "`decision_needed`",
    "`residual_risk`",
    "`untouched`",
    "`verification_limit`",
)


class PlanningPolicyClaudeAdapterTest(unittest.TestCase):
    def test_adapter_preserves_portable_claude_tier_mapping(self):
        adapter = ADAPTER.read_text(encoding="utf-8")

        self.assertIn("`Agent` tool", adapter)
        self.assertIn("`blocked:model_unavailable`", adapter)
        self.assertIn("`blocked:missing_input`", adapter)
        self.assertIn("Never substitute a versioned model identifier", adapter)
        self.assertIn("never silently\ndowngrade", adapter)
        for tier, (model, effort) in EXPECTED_TIERS.items():
            self.assertIn(f"| `{tier}` | `{model}` | `{effort}` |", adapter)

    def test_adapter_leaves_retry_targeting_to_the_ledger(self):
        adapter = ADAPTER.read_text(encoding="utf-8")

        for marker in (
            "`retry-remediation-v1`",
            "ledger alone",
            "target portable tier",
            "reuse or fresh",
            "raw history",
            "`blocked:model_unavailable`",
            "never silently downgrade",
        ):
            self.assertIn(marker, adapter)

    def test_agents_match_mapping_and_stop_on_load_bearing_gaps(self):
        for tier, (model, effort) in EXPECTED_TIERS.items():
            content = (AGENTS / f"{tier}.md").read_text(encoding="utf-8")

            self.assertRegex(content, rf"(?m)^model: {model}$")
            self.assertRegex(content, rf"(?m)^effort: {effort}$")
            self.assertIn("`blocked:missing_input`", content)
            self.assertIn("ask the parent to re-cut", content)
            self.assertIn("Return exactly one UTF-8 JSON object", content)
            self.assertRegex(
                content,
                re.compile(r"parent owns\s+integration and final verification", re.I),
            )
            self.assertIn("`retry-remediation-v1`", content)
            self.assertIn("`blocked:needs_higher_tier`", content)
            self.assertIn("ledger", content)

    def test_standard_agent_does_not_allow_load_bearing_assumptions(self):
        standard = (AGENTS / "plan-step-standard.md").read_text(encoding="utf-8")

        self.assertNotIn("ask for it or state the assumption", standard)

    def test_adapter_and_agents_share_the_bounded_step_return_profile(self):
        documents = [ADAPTER.read_text(encoding="utf-8")]
        documents.extend((AGENTS / f"{tier}.md").read_text(encoding="utf-8") for tier in EXPECTED_TIERS)

        for content in documents:
            normalized = re.sub(r"\s+", " ", content)
            for marker in RETURN_PROFILE:
                self.assertIn(marker, normalized)
            self.assertIn("no Markdown, prose outside the object", content)
            self.assertIn("raw logs", content)
            self.assertIn("Use `completed` only", content)
            self.assertNotIn("`commit_hash` is `null`", content)
            self.assertTrue("return <=8 KiB" in content or "at most 8 KiB" in content)
            self.assertTrue("oversized also needs remainder" in content or "oversized` also requires an unstarted remainder" in content)
            self.assertTrue("<=480-character" in content or "at most 480 characters" in content)
            self.assertTrue("<=240-character summary" in content or "at most 240 characters" in content)
            self.assertTrue('"exit_code": integer|null' in content or "integer/null exit code" in content)
            self.assertTrue("eight blockers" in content or "at most eight" in content)
            self.assertTrue("empty string or 40/64-hex hash" in content or "empty\nstring or a 40- or 64-hex hash" in content)
            self.assertTrue("completed changed work needs a commit hash" in content or "completed\nwork with changed paths needs a commit hash" in content)

        self.assertIn("return itself does not carry `run_id`", documents[0])
        self.assertIn("helper-generated assignment value", documents[0])
        self.assertNotIn("attempt_id` is a positive integer", documents[0])
        self.assertIn("`completed` → `integrated` → `cleaned`", documents[0])
        self.assertIn("current parent tip", documents[0])
        self.assertIn("never a routine cherry-pick", documents[0])
        for content in documents[1:]:
            self.assertIn("do not return it", content)
            self.assertIn("helper-generated `attempt_id`", content)
            self.assertNotIn("positive integer `attempt_id`", content)


if __name__ == "__main__":
    unittest.main()
