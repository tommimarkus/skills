import json
import unittest

from tests.surface_test_lib import REPO_ROOT


PACK = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-extensions/jsts-security.md"
CATALOG = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-smell-catalog.md"
GROUNDING = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/source-grounding.md"
CASES = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/evals/behavior-cases.jsonl"


class JstsSecurityRulesSurfaceTest(unittest.TestCase):
    def test_rules_catalog_grounding_and_synthetic_eval_are_complete(self) -> None:
        pack, catalog, grounding = (path.read_text(encoding="utf-8") for path in (PACK, CATALOG, GROUNDING))
        cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line]
        case = next(item for item in cases if item["id"] == "devsecops-audit-behavior-jsts-trust-boundaries")
        for code in range(1, 12):
            self.assertIn(f"### `jsts.HC-{code}`", pack)
            self.assertIn(f"### `jsts.POS-{code}`", pack)
            self.assertIn(f"| `jsts.HC-{code}` |", catalog)
            self.assertIn(f"| `jsts.POS-{code}` |", catalog)
        self.assertIn("visible trust-boundary/taint path", pack)
        self.assertIn("API names alone are not findings", pack)
        self.assertIn("https://nodejs.org/api/child_process.html", pack)
        self.assertIn("Vite server options", grounding)
        self.assertEqual("synthetic", case["source_kind"])
        self.assertFalse(case["contains_third_party_text"])
        self.assertIn("jsts.HC-11", case["required_checks"])
