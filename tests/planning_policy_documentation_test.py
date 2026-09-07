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
        for path in ("CLAUDE.md", "AGENTS.md"):
            public = self.text(path)
            self.assertIn("show --next-only", public)
            self.assertIn("120", public)
        self.assertIn("live `next` results", entry)
        self.assertIn("errors, legacy resumption, diagnosis, retention operations", entry)
        self.assertIn("240 proxy tokens", contract)
        self.assertIn("deterministic highest-priority", contract)
        self.assertIn("exception-only", ledger)
        self.assertIn("24-hour", grounding)
        self.assertIn(
            "](../souroldgeezer-policy/skills/planning-policy/references/ledger-contract.md)",
            standard,
        )
        self.assertIn("execution diagnosis", standard)
        self.assertIn("successful transitions add bounded live guidance", ledger)

        for adapter in (
            "souroldgeezer-policy/skills/planning-policy/extensions/claude-code.md",
            "souroldgeezer-policy/skills/planning-policy/extensions/codex.md",
        ):
            text = self.text(adapter)
            self.assertIn("live `next`", text)
            self.assertIn("host notification", text)
            self.assertIn("busy-poll", text)

    def test_runtime_neutral_contract_is_public(self) -> None:
        # The concise entry links each authority; facts stay checked at that
        # destination instead of requiring a second full contract in README.
        root = "souroldgeezer-policy/skills/planning-policy/"
        entry = self.text(root + "SKILL.md")
        expectations = {
            "references/plan-contract.md": (
                "contract_version", "IDs/dependencies", "task", "boundary", "read_set",
                "write_set", "settled_decisions", "acceptance_command", "stop_conditions",
                "must be at least `0.60`", "analytical_heavy_exception",
                "planning-execution-cost-v1", "planning-cost-advisory-v1",
                "Versions 1–4 are resume-only", "approval_ready", "dispatch_ready",
                "planning-capability-binding-v1", "max_attempts", "1–5",
            ),
            "references/core-workflow.md": (
                "Execution economics", "tracing: off", "scoped acceptance",
                "`completed` → `integrated` → `cleaned`", "only the parent creates",
                "bounded checkpoints", "never raw logs", "select an owning audit",
            ),
            "references/ledger-contract.md": (
                "<git-common-dir>/planning-policy/ledgers/<plan-id>/<run-id>/",
                "canonical lowercase UUID4", "bounded-step-return-v1", "at most 8 KiB",
                "The return does not list `run_id`", "blocked:plan_tampered",
                "blocked:retry_exhausted", "blocked:no_progress", "`oversized`",
                "planning-worktree-result-v1", "validate --closeout",
                "retry_policy: escalating_remediation_v1", "retry-remediation-v1",
                "blocked:needs_higher_tier", "parent re-runs only that leaf's own scoped acceptance",
            ),
            "references/ledger-compatibility.md": (
                "retry_policy: legacy_unbounded", "terminal `integrated` state is unchanged",
                "does not gain `cleaned`", "Do not approve new legacy work",
                "initialize a separate v5 run", "Existing ledgers remain mutable",
            ),
            "references/usage-tracing.md": (
                "trace-init", "trace-record", "trace-show", "trace-close",
            ),
            "extensions/codex.md": (
                "blocked:model_unavailable", "do not silently downgrade",
                "blocked:missing_input", "end-to-end verification",
                "The ledger alone decides retry eligibility", "stable step ID and dependency IDs",
            ),
        }
        for destination, facts in expectations.items():
            self.assertIn(f"]({destination})", entry)
            text = " ".join(self.text(root + destination).split())
            for fact in facts:
                with self.subTest(destination=destination, fact=fact):
                    self.assertIn(fact.lower(), text.lower())

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
        standard = " ".join(standard.split())
        for principle in (
            "the derivation it comes from", "the consumer that reads it",
            "size band from its read-set and acceptance check",
            "host overlay may add dispatch syntax but cannot rewrite",
        ):
            self.assertIn(principle, standard)
        for destination, condition in (
            ("core-workflow.md", "When authoring an executable plan"),
            ("plan-contract.md", "When authoring an executable plan"),
            ("ledger-contract.md", "For execution diagnosis"),
        ):
            with self.subTest(destination=destination):
                self.assertIn(
                    f"](../souroldgeezer-policy/skills/planning-policy/references/{destination})",
                    standard,
                )
                self.assertIn(condition, standard)
        self.assertNotIn("Dependencies wait for `cleaned`", standard)
        ledger = " ".join(self.text(
            "souroldgeezer-policy/skills/planning-policy/references/ledger-contract.md"
        ).split())
        for fact in (
            "an external dependency still requires `cleaned`",
            "an in-batch dependency on an earlier-listed same-batch member",
            "readiness at `ready`, `in_progress`, or `completed`",
        ):
            self.assertIn(fact, ledger)
        for principle in (
            "optional expensive lens", "explicit opt-in",
            "zero extra agent or network calls for that lens",
            "Calls required by the requested core workflow",
            "existing task authority and applicable policy",
        ):
            self.assertIn(principle, standard)

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
        self.assertIn(
            "](../souroldgeezer-policy/skills/planning-policy/references/plan-series.md)",
            standard,
        )
        self.assertIn("When slicing work into successive plans", standard)
        series = self.text(
            "souroldgeezer-policy/skills/planning-policy/references/plan-series.md"
        )
        for fact in ("series_predecessor", "unresolvable", "end_verification_commands"):
            self.assertIn(fact, series)
        self.assertIn("plan-to-plan continuity", standard)

    def test_unresolved_domain_design_routes_before_approval(self) -> None:
        entry = self.text("souroldgeezer-policy/skills/planning-policy/SKILL.md")
        core = self.text("souroldgeezer-policy/skills/planning-policy/references/core-workflow.md")
        self.assertIn("unresolved domain-design", entry)
        self.assertIn("Before approval, invoke the owning design skill", core)

    def test_v5_authors_are_directed_to_the_canonical_scaffold(self) -> None:
        for relative in ("AGENTS.md", "CLAUDE.md"):
            with self.subTest(relative=relative):
                self.assertIn("references/templates/plan-v5.json", self.text(relative))

    def test_public_guidance_names_the_v5_scaffold_and_rejects_the_alias(self) -> None:
        for relative in ("AGENTS.md", "CLAUDE.md"):
            with self.subTest(relative=relative):
                text = self.text(relative)
                self.assertIn("references/templates/plan-v5.json", text)
                self.assertIn("never `version`", text)

    def test_v5_handoffs_carry_cohesive_outcome_and_decomposition_evidence(self) -> None:
        for relative in ("AGENTS.md", "CLAUDE.md"):
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
        contract = self.text(
            "souroldgeezer-policy/skills/planning-policy/references/plan-contract.md"
        )
        for fact in (
            "cohesive_outcome", "decomposition", "work_units",
            "Versions 1–4 are resume-only", "init-v4",
            "blocked:contract_migration_required", "Existing v1–v4 ledgers",
        ):
            self.assertIn(fact, contract)


if __name__ == "__main__":
    unittest.main()
