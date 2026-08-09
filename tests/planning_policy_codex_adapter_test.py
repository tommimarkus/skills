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
            "run ID, step ID, agent ID, and attempt ID",
            "`bounded-step-return-v1` profile below",
            "`blocked:missing_input`",
            "`blocked:oversized`",
            "`blocked:model_unavailable`",
            "do not silently downgrade",
        ):
            self.assertIn(marker, self.text)

    def test_uses_the_shared_bounded_step_return_profile(self):
        for marker in (
            '`"schema": "bounded-step-return-v1"`',
            "`step_id`",
            "`agent_id`",
            "`attempt_id`",
            "`changed_paths`, `acceptance`, `blockers`, `notes`,",
            "`commit_hash`",
            "`unstarted_remainder`",
            "`completed`, `blocked`, `failed`, or `oversized`",
            "32 safe repository-relative",
            '"exit_code": integer|null',
            "at most eight",
            "`finding`",
            "`decision_needed`",
            "`residual_risk`",
            "`untouched`",
            "`verification_limit`",
            "empty\nstring or a 40- or 64-hex hash",
            "at most 8 KiB",
            "completed\nwork with changed paths needs a commit hash",
            "oversized` also requires an unstarted remainder",
            "no Markdown, prose outside the object, or raw logs",
        ):
            self.assertIn(marker, self.text)
        self.assertIn("return itself does not carry `run_id`", self.text)
        self.assertIn("helper-generated assignment value", self.text)
        self.assertNotIn("attempt_id` is a positive integer", self.text)
        self.assertNotIn("`commit_hash` is `null`", self.text)
