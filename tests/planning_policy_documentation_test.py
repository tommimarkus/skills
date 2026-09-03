"""Keep public planning-policy guidance aligned with the implemented contract."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PlanningPolicyDocumentationTest(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_live_next_chain_is_public_and_exception_routed(self) -> None:
        entry = self.text("souroldgeezer-policy/skills/planning-policy/SKILL.md")
        contract = self.text(
            "souroldgeezer-policy/skills/planning-policy/references/plan-contract.md"
        )
        ledger = self.text(
            "souroldgeezer-policy/skills/planning-policy/references/ledger-contract.md"
        )
        grounding = self.text(
            "souroldgeezer-policy/skills/planning-policy/references/source-grounding.md"
        )
        standard = self.text("docs/skill-architecture.md")
        for path in ("README.md", "CLAUDE.md", "AGENTS.md"):
            public = self.text(path)
            self.assertIn("show --next-only", public)
            self.assertIn("120", public)
        self.assertIn("live `next` results", entry)
        self.assertIn("errors, legacy resumption, diagnosis, retention operations", entry)
        self.assertIn("240 proxy tokens", contract)
        self.assertIn("deterministic highest-priority", contract)
        self.assertIn("exception-only", ledger)
        self.assertIn("24-hour", grounding)
        self.assertIn("live-next chain", standard)

        for adapter in (
            "souroldgeezer-policy/skills/planning-policy/extensions/claude-code.md",
            "souroldgeezer-policy/skills/planning-policy/extensions/codex.md",
        ):
            text = self.text(adapter)
            self.assertIn("live `next`", text)
            self.assertIn("host notification", text)
            self.assertIn("busy-poll", text)

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
            "contract_version: 5", "planning-execution-cost-v1",
            "planning-cost-advisory-v1", "Execution economics", "tracing: off",
            "Versions 1–4 are resume-compatible only",
            "trace-init", "trace-record", "trace-show", "trace-close",
            "Versions 1–4 are resume-compatible only",
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
            "`completed` → `integrated` → `cleaned`",
            "planning-worktree-result-v1", "validate --closeout",
            "terminal `integrated` state remains unchanged",
            "retry_policy: escalating_remediation_v1", "portable_tier` is initial only",
            "retry-remediation-v1", "blocked:needs_higher_tier",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_claude_guidance_uses_aliases_without_version_claim(self) -> None:
        claude = self.text("CLAUDE.md")
        for phrase in (
            "haiku`/`low", "sonnet`/`medium", "opus`/`high", "opus`/`xhigh",
            "not claims about a resolved version", "blocked:model_unavailable",
            "never silently downgrade", "Missing load-bearing information stops",
            "contract_version: 5", "<plan-id>/<run-id>",
            "planning-execution-cost-v1", "planning-cost-advisory-v1",
            "Execution\neconomics", "tracing: off", "trace-init", "trace-close",
            "bounded-step-return-v1", "blocked:plan_tampered",
            "Version-1 ledgers remain readable and mutable",
            "retry_policy: legacy_unbounded",
            "`completed` → `integrated` → `cleaned`",
            "planning-worktree-result-v1", "validate --closeout",
            "Routine integration never cherry-picks",
            "retry_policy: escalating_remediation_v1", "portable_tier` is initial only",
            "retry-remediation-v1", "blocked:needs_higher_tier",
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
            "contract_version: 5", "<plan-id>/<run-id>",
            "planning-execution-cost-v1", "planning-cost-advisory-v1",
            "Execution economics", "tracing: off", "trace-init", "trace-close",
            "bounded-step-return-v1", "blocked:plan_tampered",
            "Version-1 ledgers remain readable and mutable",
            "retry_policy: legacy_unbounded",
            "`completed` → `integrated` → `cleaned`",
            "planning-worktree-result-v1", "validate --closeout",
            "Routine integration never cherry-picks",
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
            "contract_version: 5", "<plan-id>/<run-id>", "lowercase UUID4",
            "Versions 1–4 are resume-compatible only", "declared-model-token",
            "bounded-step-return-v1", "blocked:plan_tampered",
            "Version-1\nledgers remain readable and mutable",
            "retry_policy: legacy_unbounded", "blocked:retry_exhausted",
            "blocked:no_progress", "terminal\n`oversized`",
            "`completed` → `integrated` → `cleaned`",
            "planning-worktree-result-v1", "validate --closeout",
            "terminal `integrated` state remains unchanged",
            "retry_policy: escalating_remediation_v1", "portable_tier` is initial only",
            "retry-remediation-v1", "blocked:needs_higher_tier",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, standard)

    def test_series_summary_is_public_and_orientation_named(self) -> None:
        claude = self.text("CLAUDE.md")
        agents = self.text("AGENTS.md")
        standard = self.text("docs/skill-architecture.md")
        for text in (claude, agents):
            self.assertIn("series_id", text)
            self.assertIn("copied verbatim", text)
            self.assertIn("series_predecessor", text)
            self.assertIn("unresolvable", text)
            self.assertIn("series_end: true", text)
            self.assertIn("byte-identical", text)
        self.assertIn("plan-series", standard)
        self.assertIn("plan-to-plan continuity", standard)

    def test_unresolved_domain_design_routes_before_approval(self) -> None:
        entry = self.text("souroldgeezer-policy/skills/planning-policy/SKILL.md")
        core = self.text("souroldgeezer-policy/skills/planning-policy/references/core-workflow.md")
        self.assertIn("unresolved domain-design", entry)
        self.assertIn("Before approval, invoke the owning design skill", core)

    def test_v5_authors_are_directed_to_the_canonical_scaffold(self) -> None:
        for relative in ("README.md", "AGENTS.md", "CLAUDE.md"):
            with self.subTest(relative=relative):
                self.assertIn("references/templates/plan-v5.json", self.text(relative))

    def test_public_guidance_names_the_v5_scaffold_and_rejects_the_alias(self) -> None:
        for relative in ("README.md", "AGENTS.md", "CLAUDE.md"):
            with self.subTest(relative=relative):
                text = self.text(relative)
                self.assertIn("references/templates/plan-v5.json", text)
                self.assertIn("never `version`", text)

    def test_v5_handoffs_carry_cohesive_outcome_and_decomposition_evidence(self) -> None:
        for relative in ("README.md", "AGENTS.md", "CLAUDE.md", "docs/skill-architecture.md"):
            with self.subTest(relative=relative):
                text = self.text(relative)
                self.assertIn("cohesive_outcome", text)
                self.assertIn("decomposition", text)
                self.assertIn("work unit", text)
                self.assertIn("resume-compatible only", text)
                self.assertIn("init-v5", text)
                self.assertIn("init-v4", text)
                self.assertIn("blocked:contract_migration_required", text)
                self.assertIn("existing v4 records remain", text)
                self.assertNotIn("intermediate_states", text)


if __name__ == "__main__":
    unittest.main()
