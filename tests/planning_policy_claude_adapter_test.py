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

    def test_agents_match_mapping_and_stop_on_load_bearing_gaps(self):
        for tier, (model, effort) in EXPECTED_TIERS.items():
            content = (AGENTS / f"{tier}.md").read_text(encoding="utf-8")

            self.assertRegex(content, rf"(?m)^model: {model}$")
            self.assertRegex(content, rf"(?m)^effort: {effort}$")
            self.assertIn("`blocked:missing_input`", content)
            self.assertIn("ask the parent to re-cut", content)
            self.assertIn("Return (bounded):", content)
            self.assertRegex(
                content,
                re.compile(r"parent owns\s+integration and final verification", re.I),
            )

    def test_standard_agent_does_not_allow_load_bearing_assumptions(self):
        standard = (AGENTS / "plan-step-standard.md").read_text(encoding="utf-8")

        self.assertNotIn("ask for it or state the assumption", standard)


if __name__ == "__main__":
    unittest.main()
