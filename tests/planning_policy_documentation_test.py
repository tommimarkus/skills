"""Keep public planning-policy guidance aligned with the implemented contract."""

from pathlib import Path
import unittest

from tests.surface_test_lib import assert_phrases, load_script_module


ROOT = Path(__file__).resolve().parents[1]
ledger = load_script_module(
    "planning_policy_documentation_ledger",
    ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py",
)


class PlanningPolicyDocumentationTest(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_initialized_scope_controls_trigger(self) -> None:
        import json

        entry = self.text("souroldgeezer-policy/skills/planning-policy/SKILL.md")
        agent = self.text("souroldgeezer-policy/agents/planning-policy.md")
        workflow = self.text("souroldgeezer-policy/skills/planning-policy/references/core-workflow.md")
        description = next(line for line in entry.splitlines() if line.startswith("description:"))
        self.assertIn(description, agent)
        self.assertIn("Apply its stated scope", entry)
        self.assertIn("Explicit scope overrides the bare default", workflow)
        for host in (".claude-plugin", ".codex-plugin"):
            manifest = json.loads(self.text(f"souroldgeezer-policy/{host}/plugin.json"))
            self.assertIn("work covered by initialized guidance", manifest["description"])
        self.assertIn("work covered by initialized guidance", self.text(
            "souroldgeezer-policy/skills/planning-policy/references/source-grounding.md"
        ))
        cases = [json.loads(line) for line in self.text(
            "souroldgeezer-policy/skills/planning-policy/references/evals/trigger-cases.jsonl"
        ).splitlines()]
        fix = next(case for case in cases if case["id"] == "planning-policy-trigger-yes-explicit-scope-fix")
        self.assertTrue(fix["expected_activation"])
        self.assertIn("nontrivial", fix["prompt"])

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
        self.assertIn("show --next-only", ledger)
        self.assertIn("120 proxy tokens", contract)
        self.assertIn("live `next` results", entry)
        self.assertIn("errors, diagnosis, retention operations", entry)
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
                "Versions 1–4 were retired", "approval_ready", "dispatch_ready",
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
                "blocked:contract_migration_required", "souroldgeezer-policy 2026.10.9 or earlier",
                "run_status: unsupported", "unsupported_count", "Do not approve new legacy work",
                "initialize a separate v5 run",
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
            "never silently downgrade", "contract_version: 5",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, claude)

    def test_codex_guidance_has_exact_mapping(self) -> None:
        agents = self.text("AGENTS.md")
        for phrase in (
            "gpt-5.6-luna`/`low", "gpt-5.6-terra`/`medium",
            "gpt-5.6-sol`/`high", "gpt-5.6-sol`/`xhigh",
            "blocked:model_unavailable", "never silently downgrade",
            "contract_version: 5",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agents)
        self.assertNotIn("Copilot execution mapping", agents)

    def test_execution_rules_live_in_their_owning_references(self) -> None:
        root = "souroldgeezer-policy/skills/planning-policy/"
        owners = {
            "references/plan-contract.md": (
                "planning-execution-cost-v1", "planning-cost-advisory-v1",
                "bounded-step-return-v1", "contract_version: 5", "never `version`",
            ),
            "references/core-workflow.md": (
                "tracing: off", "bounded checkpoints", "only the parent creates",
                "`completed` → `integrated` → `cleaned`", "cherry-pick",
            ),
            "references/ledger-contract.md": (
                "<plan-id>/<run-id>", "planning-worktree-result-v1",
                "validate --closeout", "blocked:plan_tampered",
                "retry_policy: escalating_remediation_v1", "retry-remediation-v1",
                "blocked:needs_higher_tier", "`portable_tier` is the initial tier only",
                "amend-v5", "new approved plan",
            ),
            "references/ledger-compatibility.md": ("run_status: unsupported",),
            "references/usage-tracing.md": ("trace-init", "trace-close"),
            "references/approval-handoff.md": (
                "Prose summaries never replace the canonical execution JSON",
                "blocked:plan_tampered",
            ),
            "references/plan-series.md": (
                "series_id", "copied verbatim", "series_predecessor",
                "unresolvable", "series_end:", "behaves exactly as documented",
            ),
            "extensions/claude-code.md": ("busy-poll", "blocked:model_unavailable"),
            "extensions/codex.md": ("busy-poll", "blocked:model_unavailable"),
        }
        for destination, facts in owners.items():
            text = " ".join(self.text(root + destination).split())
            for fact in facts:
                with self.subTest(destination=destination, fact=fact):
                    self.assertIn(fact, text)

    def test_repo_guidance_planning_sections_stay_pointers(self) -> None:
        # Same counter as the cost test: one token per word or punctuation mark.
        counter = ledger.PROXY_TOKEN_RE
        for path, heading in (
            ("CLAUDE.md", "### Planning-policy execution contract (Claude Code)"),
            ("AGENTS.md", "### Planning-policy execution contract (Codex)"),
        ):
            text = self.text(path)
            start = text.index(heading)
            end = text.index("\n## ", start)
            section = text[start:end]
            with self.subTest(path=path):
                self.assertLessEqual(len(counter.findall(section)), 600)
                for pointer in (
                    "planning-policy/SKILL.md", "references/plan-contract.md",
                    "references/ledger-contract.md", "templates/plan-v5.json",
                    "planning_policy_forward_eval.py", "versions 1–4 are retired",
                ):
                    self.assertIn(pointer, section)

    def test_amend_splits_execution_metadata_from_scope(self) -> None:
        root = "souroldgeezer-policy/skills/planning-policy/"
        ledger = " ".join(self.text(root + "references/ledger-contract.md").split())
        for fact in ("amend --actor parent", "`amend-v5` event", "effective leaf", "at most 4"):
            self.assertIn(fact, ledger)
        self.assertIn("`amend`", self.text(root + "SKILL.md"))
        self.assertIn("parent-amendable", self.text(root + "references/plan-contract.md"))
        for adapter in ("claude-code", "codex"):
            text = " ".join(self.text(root + f"extensions/{adapter}.md").split())
            self.assertIn("the parent runs `amend`", text)
        self.assertIn("ledger-corpus execution friction", self.text(root + "references/source-grounding.md"))

    def test_repairable_retry_class_is_documented_everywhere(self) -> None:
        root = "souroldgeezer-policy/skills/planning-policy/"
        ledger = " ".join(self.text(root + "references/ledger-contract.md").split())
        for fact in (
            "retry_class", "Repairable stops are `blocked:environment`",
            "first blocker whose code belongs to its status family",
            "the retry does not set `same-tier-used`, is never forced upward",
        ):
            self.assertIn(fact, ledger)
        for adapter in ("claude-code", "codex"):
            text = " ".join(self.text(root + f"extensions/{adapter}.md").split())
            self.assertIn("Repairable stops (`blocked:environment`", text)
            self.assertIn("only reasoning stops escalate", text)

    def test_environment_stop_rerun_is_one_general_rule(self) -> None:
        root = "souroldgeezer-policy/skills/planning-policy/"
        ledger = " ".join(self.text(root + "references/ledger-contract.md").split())
        for fact in (
            "For any step, single or batch member, the parent repairs a `blocked:environment` return",
            "it re-runs the step's identical acceptance command at the returned commit",
            "a `verification_limit` note disclosing the stop",
        ):
            self.assertIn(fact, ledger)
        adapters = " ".join(self.text(root + f"extensions/{a}.md") for a in ("claude-code", "codex"))
        self.assertEqual(" ".join(adapters.split()).count("environment-stop rule"), 2)

    def test_craft_standard_preserves_declared_value_consumer_loop(self) -> None:
        standard = self.text("docs/skill-architecture.md")
        standard = " ".join(standard.split())
        for principle in (
            "the derivation it comes from", "the consumer that reads it",
            "each enumerated case in guidance gets a behavior eval",
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
            "an external dependency requires `integrated` or `cleaned`",
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
        standard = self.text("docs/skill-architecture.md")
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

    def test_inline_departure_needs_a_stated_case_not_a_cost_citation(self) -> None:
        # No PLANCOST code compares dispatch overhead with the work, so an
        # inline case citing one is uncitable; batching/merging owns overhead.
        core = " ".join(self.text(
            "souroldgeezer-policy/skills/planning-policy/references/core-workflow.md"
        ).split())
        self.assertIn("Delegate unless the plan states one case in one line", core)
        for case in (
            "indivisible/trivial", "needs user mid-flight",
            "context cannot travel", "each result redefines the next",
        ):
            with self.subTest(case=case):
                self.assertIn(case, core)
        self.assertIn("Dispatch overhead is a batching/merge issue", core)
        for retired in ("cites the cost-advisory finding", "dispatch overhead exceeds the work"):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, core.lower())

    def test_v5_authors_are_directed_to_the_canonical_scaffold(self) -> None:
        root = "souroldgeezer-policy/skills/planning-policy/"
        for relative in ("AGENTS.md", "CLAUDE.md"):
            with self.subTest(relative=relative):
                self.assertIn("references/templates/plan-v5.json", self.text(relative))
        contract = self.text(root + "references/plan-contract.md")
        self.assertIn("templates/plan-v5.json", contract)
        self.assertIn("never `version`", contract)

    def test_v5_handoffs_carry_cohesive_outcome_and_decomposition_evidence(self) -> None:
        for relative in ("AGENTS.md", "CLAUDE.md"):
            with self.subTest(relative=relative):
                self.assertIn("versions 1–4 are retired", self.text(relative))
                self.assertNotIn("intermediate_states", self.text(relative))
        for adapter in ("claude-code", "codex"):
            text = self.text(
                f"souroldgeezer-policy/skills/planning-policy/extensions/{adapter}.md"
            )
            with self.subTest(adapter=adapter):
                self.assertIn("Versions 1–4 are retired", " ".join(text.split()))
                self.assertNotIn("init-v4", text)
        contract = self.text(
            "souroldgeezer-policy/skills/planning-policy/references/plan-contract.md"
        )
        for fact in (
            "cohesive_outcome", "decomposition", "work_units",
            "accepts only `contract_version: 5`", "Versions 1–4 were retired",
            "souroldgeezer-policy 2026.10.9", "ledger-compatibility.md",
        ):
            self.assertIn(fact, contract)
        self.assertNotIn("resume_ready", contract)

    def test_persistent_handoff_writer_keeps_inline_fallback_and_read_only_validator(self) -> None:
        handoff = self.text(
            "souroldgeezer-policy/skills/planning-policy/references/approval-handoff.md"
        )
        contract = self.text(
            "souroldgeezer-policy/skills/planning-policy/references/plan-contract.md"
        )
        self.assertIn("persist_plan.py", handoff)
        self.assertIn("blocked:persistence_unavailable", handoff)
        self.assertIn("write probe", handoff)
        self.assertEqual(2, handoff.count("contract.py\" validate - --emit-handoff inline --handoff-format block"))
        self.assertIn("272 KiB", handoff)
        self.assertIn("4,096 characters", handoff)
        self.assertIn("validate_plan_contract.py` remains read-only", contract)


    def test_verify_loop_is_routed_and_documented(self) -> None:
        base = "souroldgeezer-policy/skills/planning-policy/"
        entry = self.text(base + "SKILL.md")
        workflow = self.text(base + "references/core-workflow.md")
        handoff = self.text(base + "references/worker-handoff.md")
        ledger = self.text(base + "references/ledger-contract.md")
        claude = self.text(base + "extensions/claude-code.md")
        codex = self.text(base + "extensions/codex.md")
        self.assertIn("references/verify-handoff.md", entry)
        self.assertIn("check-changeset", entry)
        self.assertIn("Verify: <per-leaf (N verified, M rejected)", workflow)
        self.assertIn("verify:\n> per-leaf | closeout-only", workflow)
        self.assertIn("verify dispatches", workflow)
        self.assertIn("stopping `oversized:changeset`", handoff)
        self.assertIn("leaf_verify_v1", ledger)
        self.assertIn("record-verify", ledger)
        assert_phrases(self, claude, (
            "`souroldgeezer-policy:plan-verify-standard`",
            "`souroldgeezer-policy:plan-verify-analytical`",
            "as named by the packet's `verifier_tier`", "never builder context or notes",
            "An unavailable agent is `blocked:model_unavailable`; never downgrade",
        ), heading="## Capability resolution")
        assert_phrases(self, codex, (
            "`gpt-5.6-sol`", "as named by `verifier_tier`",
            "Never pass builder context", "do not silently downgrade",
        ), heading="## Dispatch and model mapping")


if __name__ == "__main__":
    unittest.main()
