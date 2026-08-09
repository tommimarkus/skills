"""Keep public planning-policy guidance aligned with the implemented contract."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PlanningPolicyDocumentationTest(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_runtime_neutral_contract_is_public(self) -> None:
        readme = self.text("README.md")
        for phrase in (
            "stable IDs, dependencies, task/boundary",
            "at least 0.60",
            "analytical-heavy exception",
            "Missing load-bearing input stops",
            "selective audit routing remains an\n    exceptional",
            "The parent owns\n    integration and end-to-end verification",
            "planning-policy/ledgers/<plan-id>",
            "bounded lifecycle returns",
            "contract_version: 2",
            "dispatch_ready: false",
            "<plan-id>/<run-id>",
            "lowercase\n    UUID4",
            "bounded-step-return-v1",
            "no `run_id` or raw logs",
            "blocked:plan_tampered",
            "Version-1 ledgers remain readable and mutable",
            "retry_policy: legacy_unbounded",
            "cannot approve or dispatch an unversioned version-1\n    plan as new work",
            "blocked:retry_exhausted",
            "blocked:no_progress",
            "terminal `oversized`",
            "blocked:model_unavailable",
            "silent downgrade.",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_claude_guidance_uses_aliases_without_version_claim(self) -> None:
        claude = self.text("CLAUDE.md")
        for phrase in (
            "haiku`/`low", "sonnet`/`medium", "opus`/`high", "opus`/`xhigh",
            "not claims about a resolved version", "blocked:model_unavailable",
            "never silently downgrade", "Missing load-bearing information stops",
            "contract_version: 2", "<plan-id>/<run-id>",
            "bounded-step-return-v1", "blocked:plan_tampered",
            "Version-1 ledgers remain readable and mutable",
            "retry_policy: legacy_unbounded",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, claude)

    def test_codex_guidance_has_exact_mapping_and_parent_boundary(self) -> None:
        agents = self.text("AGENTS.md")
        for phrase in (
            "gpt-5.6-luna`/`low", "gpt-5.6-terra`/`medium",
            "gpt-5.6-sol`/`high", "gpt-5.6-sol`/`xhigh",
            "blocked:model_unavailable", "never silently downgrade",
            "only the parent may", "bounded checkpoint and lifecycle/retry returns",
            "contract_version: 2", "<plan-id>/<run-id>",
            "bounded-step-return-v1", "blocked:plan_tampered",
            "Version-1 ledgers remain readable and mutable",
            "retry_policy: legacy_unbounded",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agents)
        self.assertNotIn("Copilot execution mapping", agents)

    def test_craft_standard_preserves_declared_value_consumer_loop(self) -> None:
        standard = self.text("docs/skill-architecture.md")
        self.assertIn("stable\ntop-level work unit", standard)
        self.assertIn("user-approved exception", standard)
        self.assertIn("host overlay may add\ndispatch syntax but cannot rewrite them", standard)
        for phrase in (
            "contract_version: 2", "<plan-id>/<run-id>", "lowercase UUID4",
            "bounded-step-return-v1", "blocked:plan_tampered",
            "Version-1\nledgers remain readable and mutable",
            "retry_policy: legacy_unbounded", "blocked:retry_exhausted",
            "blocked:no_progress", "terminal\n`oversized`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, standard)

    def test_unresolved_domain_design_routes_before_approval(self) -> None:
        entry = self.text("souroldgeezer-policy/skills/planning-policy/SKILL.md")
        core = self.text("souroldgeezer-policy/skills/planning-policy/references/core-workflow.md")
        self.assertIn("unresolved domain-design", entry)
        self.assertIn("Before approval, invoke the owning design skill", core)


if __name__ == "__main__":
    unittest.main()
