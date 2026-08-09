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
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agents)
        self.assertNotIn("Copilot execution mapping", agents)

    def test_craft_standard_preserves_declared_value_consumer_loop(self) -> None:
        standard = self.text("docs/skill-architecture.md")
        self.assertIn("stable\ntop-level work unit", standard)
        self.assertIn("user-approved exception", standard)
        self.assertIn("host overlay may add\ndispatch syntax but cannot rewrite them", standard)


if __name__ == "__main__":
    unittest.main()
