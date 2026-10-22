import json
from pathlib import Path
import re
import unittest

from tests.surface_test_lib import assert_phrases, compact, section


REPO_ROOT = Path(__file__).resolve().parents[1]
ADAPTER = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/extensions/claude-code.md"
AGENTS = REPO_ROOT / "souroldgeezer-policy/agents"
HOST_TIERS = json.loads(
    (REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/references/host-tiers.json").read_text()
)["hosts"]["claude-code"]
EXPECTED_TIERS = {
    f"plan-step-{tier}": (entry["model"], entry["effort"]) for tier, entry in HOST_TIERS["tiers"].items()
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
        self.assertEqual(4, len(EXPECTED_TIERS))
        for tier, (model, effort) in EXPECTED_TIERS.items():
            self.assertIn(f"| `{tier}` | `{model}` | `{effort}` |", adapter)
        flat = re.sub(r"\s+", " ", adapter)
        for verifier, entry in HOST_TIERS["verifiers"].items():
            self.assertIn(f"`souroldgeezer-policy:{verifier}` (`{entry['model']}`/`{entry['effort']}`)", flat)

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
            self.assertIn("`cohesive_outcome`", content)
            self.assertIn("`decomposition` context", content)
            self.assertIn("assigned work unit", content)
            self.assertNotIn("v1–v", content)

    def test_standard_agent_does_not_allow_load_bearing_assumptions(self):
        standard = (AGENTS / "plan-step-standard.md").read_text(encoding="utf-8")

        self.assertNotIn("ask for it or state the assumption", standard)

    def test_claude_adapter_uses_v5_for_new_work_and_points_retired_versions_to_compatibility(self):
        adapter = ADAPTER.read_text(encoding="utf-8")
        self.assertIn("init-v5", adapter)
        self.assertNotIn("init-v4", adapter)
        self.assertIn("Versions 1–4 are retired; retained pre-v5 runs are handled per", adapter)
        self.assertIn("ledger-compatibility.md", adapter)
        self.assertNotIn("resume-compatible", adapter)
        self.assertIn("`cohesive_outcome`", adapter)
        self.assertIn("assigned work unit's `cohesive_outcome`", adapter)

    def test_claude_adapter_pins_plan_mode_persistence_and_display_limits(self):
        adapter = ADAPTER.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", adapter)
        for fact in (
            "persist_plan.py",
            ".planning-policy/plans",
            "git check-ignore",
            "blocked:persistence_unavailable",
            "fenced `json` block",
            "4,096",
            "200,000",
            "never approval",
            "call `ExitPlanMode` again",
        ):
            self.assertIn(fact, normalized)
        self.assertNotIn("2.1.284", adapter)

    def test_adapter_and_agents_share_the_bounded_step_return_profile(self):
        # caps, KiB bound, vocabularies, evidence pairs and the commit rule are held to the
        # validator by planning_return_contract_parity_test; this pins the shared profile tokens
        adapter = ADAPTER.read_text(encoding="utf-8")
        agents = [(tier, (AGENTS / f"{tier}.md").read_text(encoding="utf-8")) for tier in EXPECTED_TIERS]
        documents = [("adapter", adapter, "## Bounded step return")]
        documents.extend((tier, text, None) for tier, text in agents)

        for name, text, heading in documents:
            with self.subTest(document=name):
                assert_phrases(self, text, RETURN_PROFILE + (
                    "no Markdown, prose outside the object", "raw logs", "Use `completed` only",
                ), heading=heading)
                scope = compact(section(text, heading) if heading else text)
                self.assertNotIn("`commit_hash` is `null`", scope)
                for rule, pattern in (
                    ("nullable exit code", r"integer\s*(?:/|\||or )\s*null"),
                    ("oversized needs a remainder", r"oversized[^.]*?(?:needs|requires)[^.]*?remainder"),
                    ("empty or 40/64-hex hash", r"\b40(?:/|- or )64-hex hash"),
                    ("completed work needs a commit hash", r"completed[^.]*?commit hash"),
                ):
                    self.assertRegex(scope, pattern, rule)

        assert_phrases(self, adapter, (
            "return itself does not carry `run_id`", "helper-generated assignment value",
            "`completed` → `integrated` → `cleaned`", "current parent tip", "never a routine cherry-pick",
        ), heading="## Bounded step return")
        self.assertNotIn("attempt_id` is a positive integer", adapter)
        for tier, content in agents:
            with self.subTest(agent=tier):
                assert_phrases(self, content, ("do not return it", "helper-generated `attempt_id`"))
                self.assertNotIn("positive integer `attempt_id`", content)


if __name__ == "__main__":
    unittest.main()
