import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT


SKILL = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/SKILL.md"
ROUTER = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/extensions/jsts-security.md"
AUTHORING = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/procedures/extension-authoring.md"
TRIGGERS = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/evals/trigger-cases.jsonl"
BEHAVIORS = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/evals/behavior-cases.jsonl"
GOLDEN = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/golden-corpus/devsecops-audit-cases.jsonl"
PACK = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-extensions/jsts-security.md"


def load_jsonl(path: Path) -> dict[str, dict]:
    return {item["id"]: item for item in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())}


class JstsSecurityRoutingEvidenceTest(unittest.TestCase):
    def test_router_is_thin_and_load_map_points_to_full_pack(self) -> None:
        router = ROUTER.read_text(encoding="utf-8")
        self.assertLessEqual(len(router.splitlines()), 24)
        self.assertIn("../../../docs/security-reference/devsecops-extensions/jsts-security.md", router)
        self.assertIn("extensions/jsts-security.md", SKILL.read_text(encoding="utf-8"))
        self.assertIn("docs/security-reference/devsecops-extensions/jsts-security.md", SKILL.read_text(encoding="utf-8"))
        self.assertIn("jsts-security.md", AUTHORING.read_text(encoding="utf-8"))
        self.assertIn("full `jsts.*` rules in docs", AUTHORING.read_text(encoding="utf-8"))
        self.assertNotIn("### `jsts.HC-1`", router)

    def test_router_requires_observable_provenance_and_preserves_siblings(self) -> None:
        router = ROUTER.read_text(encoding="utf-8")
        for phrase in ("visible trust-boundary/taint-path evidence", "API names alone are not findings", "`software-design`", "`api-design`", "`app-design`", "`test-quality-audit`"):
            self.assertIn(phrase, router)

    def test_evals_and_corpus_cover_activation_evidence_and_clean_case(self) -> None:
        triggers, behaviors, golden = load_jsonl(TRIGGERS), load_jsonl(BEHAVIORS), load_jsonl(GOLDEN)
        self.assertTrue(triggers["devsecops-audit-trigger-yes-jsts-security"]["expected_activation"])
        self.assertFalse(triggers["devsecops-audit-trigger-no-jsts-app-design"]["expected_activation"])
        self.assertIn("visible trust-boundary/taint path", " ".join(behaviors["devsecops-audit-behavior-jsts-routing-evidence"]["required_checks"]))
        self.assertEqual(["jsts.HC-3"], golden["DSO-GOLD-0023"]["expected_codes"])
        self.assertIn("jsts.HC-3", golden["DSO-GOLD-0024"]["forbidden_codes"])
