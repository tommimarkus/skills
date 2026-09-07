# lean-audit:dup-intentional — public-contract phrases, source URLs, finding codes, and eval IDs are the assertion payload
import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, read, read_jsonl


APP_SKILL = "souroldgeezer-design/skills/app-design"
PROCEDURE = f"{APP_SKILL}/references/procedures/layout-and-flow.md"


def compact(text: str) -> str:
    return " ".join(text.split())


class AppDesignLayoutFlowSurfaceTest(unittest.TestCase):
    def test_skill_routes_layout_and_flow_only_for_matching_work(self) -> None:
        skill = compact(read(f"{APP_SKILL}/SKILL.md"))

        self.assertTrue((REPO_ROOT / PROCEDURE).is_file())
        self.assertIn("references/procedures/layout-and-flow.md", skill)
        for route in (
            "multi-screen flow",
            "material layout redesign",
            "dashboard/workspace composition",
            "unresolved layout direction",
            "explicitly concerns layout or flow mechanics",
            "routine component/state work",
            "narrow approved-layout changes",
            "Approved direction skips alternatives",
        ):
            self.assertIn(route, skill)

        for output in (
            "target flow map",
            "rough alternatives",
            "selected layout contract",
            "responsive transformation",
            "entry/exit points",
            "dead ends",
            "recovery and resumption",
            "flow-step IDs or layout regions",
        ):
            self.assertIn(output, skill)

    def test_alternatives_rubric_and_settled_routing_are_consistent(self) -> None:
        cases = {r["id"]: r for r in read_jsonl(f"{APP_SKILL}/references/evals/behavior-cases.jsonl")}
        case = cases["app-design-behavior-layout-alternatives-checkpoint"]
        for field in ("expected_artifacts", "required_checks", "grader"):
            wording = compact(str(case[field]))
            self.assertIn("two or three", wording)
            self.assertNotIn("exactly three", wording)
        for requirement in ("wide and narrow", "tradeoffs", "selection"):
            self.assertIn(requirement, str(case["required_checks"]))
        for missing in ("missing tradeoffs", "missing selection checkpoint"):
            self.assertIn(missing, str(case["forbidden_behaviors"]))
        for count in ("two", "three"):
            response = cases[f"app-design-behavior-layout-{count}-option-response"]
            self.assertIn(f"{count} meaningful", response["prompt"])
            self.assertIn("accept", response["grader"])
            self.assertIn("tradeoffs", response["grader"])
            self.assertIn("selection checkpoint", response["grader"])
        substantial = cases["app-design-behavior-settled-layout-flow-routing"]
        self.assertIn("dashboard", substantial["prompt"])
        self.assertIn("load the layout-and-flow procedure", str(substantial["required_checks"]))
        narrow = cases["app-design-behavior-narrow-approved-layout"]
        self.assertIn("skip the whole procedure", str(narrow["required_checks"]))
        for path in ("AGENTS.md", "CLAUDE.md", "README.md"):
            with self.subTest(path=path):
                guidance = compact(read(path))
                self.assertIn("Approved direction skips alternatives", guidance)
                self.assertIn("narrow approved-layout changes", guidance)

    def test_core_defines_flow_layout_primitives_and_findings(self) -> None:
        core = compact(read("souroldgeezer-design/docs/app-reference/app-design.md"))

        for primitive in (
            "User-flow map",
            "actor, goal, entry, preconditions, and observable completion",
            "Flow-step contract",
            "stable ID, route/screen, user action, system feedback/state, next paths, and recovery",
            "Layout contract",
            "region priority, wide placement, narrow order, adaptive operation",
            "DOM/reading/focus order",
            "Screen-state matrix",
            "destructive-confirmation",
        ):
            self.assertIn(primitive, core)

        for code in ("APP-FLOW-1", "APP-FLOW-2", "APP-LAYOUT-1", "APP-LAYOUT-2"):
            self.assertIn(code, core)

    def test_procedure_covers_flow_layout_checkpoint_and_evidence(self) -> None:
        procedure = compact(read(PROCEDURE))

        for flow_rule in (
            "actor and outcome",
            "current versus target journey",
            "branches and loops",
            "cancellation, abandonment, help, and resumption",
            "error, offline, and authentication recovery",
            "external touchpoints",
            "dead ends and duplicate steps",
            "compact table",
            "flow diagram",
        ):
            self.assertIn(flow_rule, procedure)

        for layout_rule in (
            "single-task",
            "list-detail",
            "supporting-pane",
            "feed/dashboard",
            "two or three",
            "unapproved",
            "pause for user selection or combination",
            "reflow",
            "reveal",
            "reposition",
            "presentation",
            "320 CSS pixels",
            "400% zoom",
            "RTL",
            "DOM, reading, and focus order",
        ):
            self.assertIn(layout_rule, procedure)

        for boundary in (
            "Static evidence",
            "DOM, behaviour, and visual claims",
            "human/user evidence",
        ):
            self.assertIn(boundary, procedure)

    def test_project_assimilation_and_primary_source_anchors_are_extended(self) -> None:
        assimilation = compact(
            read(f"{APP_SKILL}/references/procedures/project-assimilation.md")
        )
        grounding = compact(read(f"{APP_SKILL}/references/source-grounding.md"))

        for signal in (
            "current user flows",
            "recovery and resumption",
            "layout family",
            "adaptive order",
        ):
            self.assertIn(signal, assimilation)

        for source in (
            "https://www.w3.org/WAI/WCAG22/Understanding/reflow.html",
            "https://www.w3.org/WAI/WCAG22/Understanding/meaningful-sequence.html",
            "https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html",
            "https://www.gov.uk/service-manual/design/map-a-users-whole-problem",
            "https://design-system.service.gov.uk/patterns/",
            "https://developer.android.com/develop/adaptive-apps/guides/canonical-layouts",
        ):
            self.assertIn(source, grounding)
        self.assertIn("original paraphrase", grounding)
        self.assertIn("no examples, layouts, or source prose are copied", grounding)

    def test_public_metadata_and_documentation_are_synchronized(self) -> None:
        publication_surfaces = (
            f"{APP_SKILL}/SKILL.md",
            "souroldgeezer-design/agents/app-design.md",
            "souroldgeezer-design/.claude-plugin/plugin.json",
            "souroldgeezer-design/.codex-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
            "README.md",
            "CLAUDE.md",
            "AGENTS.md",
        )
        for path in publication_surfaces:
            with self.subTest(path=path):
                text = compact(read(path))
                self.assertIn("user-flow mapping", text)
                self.assertIn("adaptive screen layout", text)

    def test_evals_cover_triggers_checkpoints_recovery_and_evidence_limits(self) -> None:
        triggers = {
            record["id"]: record
            for record in read_jsonl(f"{APP_SKILL}/references/evals/trigger-cases.jsonl")
        }
        behaviors = {
            record["id"]: record
            for record in read_jsonl(f"{APP_SKILL}/references/evals/behavior-cases.jsonl")
        }

        for case_id in (
            "app-design-trigger-yes-user-flow-map",
            "app-design-trigger-yes-adaptive-layout-proposals",
            "app-design-trigger-no-backend-orchestration",
            "app-design-trigger-no-aesthetic-direction",
        ):
            self.assertIn(case_id, triggers)
        self.assertTrue(triggers["app-design-trigger-yes-user-flow-map"]["expected_activation"])
        self.assertTrue(
            triggers["app-design-trigger-yes-adaptive-layout-proposals"]["expected_activation"]
        )
        self.assertFalse(
            triggers["app-design-trigger-no-backend-orchestration"]["expected_activation"]
        )

        for case_id in (
            "app-design-behavior-layout-alternatives-checkpoint",
            "app-design-behavior-branching-flow-recovery",
            "app-design-behavior-supporting-pane-narrow-flow",
            "app-design-behavior-decline-screenshot-flow-verdict",
            "app-design-behavior-modal-and-popover-semantics",
            "app-design-behavior-server-function-props",
            "app-design-behavior-settled-layout-flow-routing",
            "app-design-behavior-layout-alternatives-two-or-three",
        ):
            self.assertIn(case_id, behaviors)

        required_behavior_fields = {
            "expected_artifacts",
            "required_checks",
            "forbidden_behaviors",
            "grader",
            "source_kind",
            "source_url",
            "ip_handling",
            "contains_third_party_text",
        }
        for case_id, record in behaviors.items():
            with self.subTest(case_id=case_id):
                self.assertTrue(required_behavior_fields <= record.keys())
                self.assertFalse(record["contains_third_party_text"])

    def test_load_cost_routes_and_fidelity_baseline_cover_the_new_surface(self) -> None:
        scenarios = {
            item["id"]: item
            for item in json.loads(read("tests/skill_load_cost/scenarios.json"))
        }
        self.assertIn("app-build-layout-flow", scenarios)
        build_targets = {route["target"] for route in scenarios["app-build-layout-flow"]["load_routes"]}
        review_targets = {route["target"] for route in scenarios["app-review-react-vite"]["load_routes"]}
        self.assertIn(PROCEDURE, build_targets)
        self.assertNotIn(PROCEDURE, review_targets)
        for case_id, expected in (("app-build-approved-dashboard", True), ("app-review-narrow-approved-layout", False)):
            targets = {route["target"] for route in scenarios[case_id]["load_routes"]}
            self.assertEqual(PROCEDURE in targets, expected)

        baseline = json.loads(read("tests/skill_load_cost/baselines/app-design.json"))
        for code in ("APP-FLOW-1", "APP-FLOW-2", "APP-LAYOUT-1", "APP-LAYOUT-2"):
            self.assertIn(code, baseline["codes"])
        for section in (
            "Layout And Flow Procedure",
            "Flow Mapping",
            "Layout Direction And Alternatives",
            "Selected Layout Contract",
            "Evidence Boundaries",
        ):
            self.assertIn(section, baseline["sections"])


if __name__ == "__main__":
    unittest.main()
