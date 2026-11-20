"""Check the TDD policy's published surfaces and declared load routes."""

import json
from pathlib import Path
import re
import unittest

from tests.surface_test_lib import REPO_ROOT as ROOT, eval_ids, read_jsonl, section


TDD_ROOT = ROOT / "souroldgeezer-policy/skills/tdd-policy"
AGENT = ROOT / "souroldgeezer-policy/agents/tdd-policy.md"
LOAD_SCENARIOS = ROOT / "tests/skill_load_cost/scenarios.json"
EVALS = "souroldgeezer-policy/skills/tdd-policy/references/evals"


def description(path: Path) -> str:
    """Read the single-line quoted `description:` from a Markdown frontmatter block."""
    text = path.read_text(encoding="utf-8")
    _, block, _ = text.split("---\n", 2)
    match = re.search(r'^description:\s*"(.*)"\s*$', block, re.M)
    assert match, f"{path} has no single-line quoted description"
    return match.group(1)


class TddPolicyContractTest(unittest.TestCase):
    def test_routine_and_detailed_enforcement_have_separate_load_scenarios(self) -> None:
        scenarios = {
            scenario["id"]: scenario["files"]
            for scenario in json.loads(LOAD_SCENARIOS.read_text(encoding="utf-8"))
            if scenario["skill"] == "tdd-policy"
        }
        entry = (TDD_ROOT / "SKILL.md").relative_to(ROOT).as_posix()
        reference = (TDD_ROOT / "references/core-workflow.md").relative_to(ROOT).as_posix()
        self.assertIn("tdd-enforce-routine", scenarios)
        self.assertEqual(scenarios["tdd-enforce-routine"], [entry])
        self.assertEqual(scenarios["tdd-enforce"], [entry, reference])

    def test_claude_router_and_skill_publish_the_same_description(self) -> None:
        self.assertEqual(description(TDD_ROOT / "SKILL.md"), description(AGENT))

    def test_adoption_template_uses_supported_enforcement_setting(self) -> None:
        core = (TDD_ROOT / "references/core-workflow.md").read_text(encoding="utf-8")
        template = section(core, "## Standing block template")
        self.assertIn("Enforcement model.", template)
        self.assertNotIn("model+gate", template)

    def test_adoption_and_preflight_link_to_the_shared_workflow(self) -> None:
        skill = (TDD_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for anchor in ("standing-block-template", "tdd-preflight"):
            with self.subTest(anchor=anchor):
                self.assertIn(f"(references/core-workflow.md#{anchor})", skill)

    def test_software_design_is_referenced_by_name_never_by_path(self) -> None:
        for path in sorted(TDD_ROOT.rglob("*")):
            if path.is_file():
                with self.subTest(path=path.relative_to(TDD_ROOT).as_posix()):
                    text = path.read_text(encoding="utf-8")
                    self.assertNotIn("souroldgeezer-design", text)
                    self.assertNotRegex(text, r"extensions/\S*test-code")

    def test_behavior_corpus_includes_both_enforcement_routes(self) -> None:
        cases = eval_ids(f"{EVALS}/behavior-cases.jsonl")
        for route in ("routine-enforcement", "detailed-enforcement"):
            with self.subTest(route=route):
                self.assertIn(f"tdd-policy-behavior-{route}", cases)

    def test_trigger_cases_distinguish_opt_in_from_installation_and_audit(self) -> None:
        cases = {
            case["id"]: case["expected_activation"]
            for case in read_jsonl(f"{EVALS}/trigger-cases.jsonl")
        }
        self.assertTrue(cases["tdd-policy-trigger-yes-initialized"])
        self.assertFalse(cases["tdd-policy-trigger-no-install-only"])
        self.assertFalse(cases["tdd-policy-trigger-no-suite-runtime-audit"])


if __name__ == "__main__":
    unittest.main()
