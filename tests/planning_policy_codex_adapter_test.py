import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ADAPTER = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/extensions/codex.md"


class PlanningPolicyCodexAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = ADAPTER.read_text(encoding="utf-8")

    def test_preserves_the_additive_codex_delegation_contract(self):
        for marker in (
            "additive adapter",
            "does not replace the portable handoff contract",
            "`spawn_agent`",
            '`fork_turns: "none"`',
            "separate persistent worktrees",
            "The parent keeps decomposition,\nintegration, and end-to-end verification.",
        ):
            self.assertIn(marker, self.text)

    def test_has_the_settled_model_and_effort_mapping(self):
        for marker in (
            "`plan-step-mechanical` | `gpt-5.6-luna` / `low`",
            "`plan-step-standard` (default) | `gpt-5.6-terra` / `medium`",
            "`plan-step-analytical` | `gpt-5.6-sol` / `high`",
            "`plan-step-deep` | `gpt-5.6-sol` / `xhigh`",
            "https://developers.openai.com/api/docs/guides/latest-model",
        ):
            self.assertIn(marker, self.text)

    def test_requires_complete_handoff_and_honest_stops(self):
        for marker in (
            "stable step ID and dependency IDs",
            "named reads and writes",
            "settled decisions and constraints",
            "portable tier",
            "worktree owner",
            "one acceptance command",
            "changed paths, acceptance output summary,\n  blockers, and commit hash",
            "`blocked:missing_input`",
            "`blocked:oversized`",
            "`blocked:model_unavailable`",
            "do not silently downgrade",
        ):
            self.assertIn(marker, self.text)
