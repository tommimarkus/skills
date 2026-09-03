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
            "`completed` → `integrated` → `cleaned`",
            "current parent tip",
            "never a routine cherry-pick",
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
            "cohesive outcome",
            "`decomposition` context",
            "assigned work unit",
            "run ID, step ID, agent ID, and attempt ID",
            "`bounded-step-return-v1` profile below",
            "`blocked:missing_input`",
            "status `oversized`",
            "`blocked:model_unavailable`",
            "do not silently downgrade",
            "init-v5",
            "Version 1–4 plans and ledger state are resume-compatible only",
            "init-v4",
            "blocked:contract_migration_required",
            "existing v4 records remain\nresumable and mutable",
            "`shape: single` only",
        ):
            self.assertIn(marker, self.text)
        # `oversized` is a bounded-step-return-v1 status, never a `blocked:` code.
        self.assertNotIn("`blocked:oversized`", self.text)

    def test_maps_only_the_ledger_selected_retry_target(self):
        normalized = " ".join(self.text.split())
        for marker in (
            "`retry-remediation-v1`",
            "ledger alone",
            "target portable tier",
            "reuse or fresh",
            "raw history",
            "`blocked:needs_higher_tier`",
            "`blocked:model_unavailable`",
        ):
            self.assertIn(marker, normalized)

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
