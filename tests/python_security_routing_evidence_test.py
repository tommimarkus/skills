import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT

SKILL = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/SKILL.md"
ROUTER = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/extensions/python-security.md"
AUTHORING = (
    REPO_ROOT
    / "souroldgeezer-audit/skills/devsecops-audit/references/procedures/extension-authoring.md"
)
TRIGGERS = (
    REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/evals/trigger-cases.jsonl"
)
BEHAVIORS = (
    REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/evals/behavior-cases.jsonl"
)
GOLDEN = (
    REPO_ROOT
    / "souroldgeezer-audit/skills/devsecops-audit/references/"
    "golden-corpus/devsecops-audit-cases.jsonl"
)
PACK = (
    REPO_ROOT
    / "souroldgeezer-audit/docs/security-reference/devsecops-extensions/python-security.md"
)


def load_jsonl(path: Path) -> dict[str, dict]:
    return {
        item["id"]: item
        for item in (
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


class PythonSecurityRoutingEvidenceTest(unittest.TestCase):
    def test_router_is_thin_and_load_map_points_to_full_pack(self) -> None:
        router = ROUTER.read_text(encoding="utf-8")
        skill = SKILL.read_text(encoding="utf-8")
        authoring = AUTHORING.read_text(encoding="utf-8")

        self.assertLessEqual(len(router.splitlines()), 24)
        self.assertIn(
            "../../../docs/security-reference/devsecops-extensions/python-security.md",
            router,
        )
        self.assertIn("extensions/python-security.md", skill)
        self.assertIn("docs/security-reference/devsecops-extensions/python-security.md", skill)
        self.assertIn("visible trust-boundary/taint-path evidence rule", skill)
        self.assertIn("python-security.md", authoring)
        self.assertIn("full `pys.*` rules in docs", authoring)
        for code in ("pys.HC-1", "pys.HC-4", "pys.HC-9", "pys.POS-5"):
            self.assertNotIn(f"### `{code}`", router)

    def test_router_keeps_security_and_sibling_boundaries_explicit(self) -> None:
        router = ROUTER.read_text(encoding="utf-8")

        for phrase in (
            "visible trust-boundary/taint-path evidence",
            "Variable names alone are not provenance",
            "project's declared controls",
            "framework or tool choices prescriptive",
            "Delegate Python module/package design to",
            "`software-design`",
            "`api-design`",
            "`test-quality-audit`",
        ):
            self.assertIn(phrase, router)

    def test_trigger_evals_cover_python_activation_and_sibling_delegation(self) -> None:
        triggers = load_jsonl(TRIGGERS)

        for case_id in (
            "devsecops-audit-trigger-yes-python-security",
            "devsecops-audit-trigger-yes-python-cli-security",
        ):
            self.assertIn(case_id, triggers)
            self.assertTrue(triggers[case_id]["expected_activation"])
        for case_id in (
            "devsecops-audit-trigger-no-python-module-design",
            "devsecops-audit-trigger-no-python-test-quality",
        ):
            self.assertIn(case_id, triggers)
            self.assertFalse(triggers[case_id]["expected_activation"])

    def test_behavior_evals_cover_evidence_and_delegation(self) -> None:
        behaviors = load_jsonl(BEHAVIORS)
        routing = behaviors["devsecops-audit-behavior-python-routing-evidence"]
        delegation = behaviors["devsecops-audit-behavior-python-sibling-delegation"]

        routing_checks = " ".join(routing["required_checks"])
        routing_forbidden = " ".join(routing["forbidden_behaviors"])
        self.assertIn("visible trust-boundary/taint path", routing_checks)
        self.assertIn("project documentation", routing_checks)
        self.assertIn("copy the full Python rule pack", routing_forbidden)
        self.assertIn("variable name alone", routing_forbidden)
        delegation_checks = " ".join(delegation["required_checks"])
        delegation_forbidden = " ".join(delegation["forbidden_behaviors"])
        for sibling in ("software-design", "api-design", "test-quality-audit"):
            self.assertIn(sibling, delegation_checks)
        self.assertIn("duplicate software-design rubric", delegation_forbidden)
        self.assertIn("duplicate test-quality rubric", delegation_forbidden)

    def test_golden_corpus_has_minimal_python_positive_and_false_positive(self) -> None:
        golden = load_jsonl(GOLDEN)
        positive = golden["DSO-GOLD-0021"]
        negative = golden["DSO-GOLD-0022"]

        self.assertEqual("python", positive["target"])
        self.assertEqual(["pys.HC-4"], positive["expected_codes"])
        self.assertEqual("misconfig", positive["ground_truth"]["type"])
        self.assertEqual([], negative["expected_codes"])
        self.assertIn("pys.HC-4", negative["forbidden_codes"])
        self.assertEqual("none", negative["ground_truth"]["type"])
        self.assertIn("repository-owned", negative["supporting_context"])

        pack = PACK.read_text(encoding="utf-8")
        self.assertIn("visible trust-boundary/taint path", pack)


if __name__ == "__main__":
    unittest.main()
