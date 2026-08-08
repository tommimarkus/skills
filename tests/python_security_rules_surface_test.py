import json
import unittest

from tests.surface_test_lib import REPO_ROOT


PACK = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-extensions/python-security.md"
CATALOG = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-smell-catalog.md"
GROUNDING = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/source-grounding.md"
CASES = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/evals/behavior-cases.jsonl"


class PythonSecurityRulesSurfaceTest(unittest.TestCase):
    def test_rules_catalog_grounding_and_synthetic_eval_are_complete(self) -> None:
        pack = PACK.read_text(encoding="utf-8")
        catalog = CATALOG.read_text(encoding="utf-8")
        grounding = GROUNDING.read_text(encoding="utf-8")
        cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line]
        case = next(item for item in cases if item["id"] == "devsecops-audit-behavior-python-trust-boundaries")

        for code in range(1, 10):
            self.assertIn(f"### `pys.HC-{code}`", pack)
            self.assertIn(f"| `pys.HC-{code}` |", catalog)
        self.assertIn("visible trust-boundary/taint path", pack)
        self.assertIn("trusted input", pack)
        self.assertIn("non-security", pack)
        self.assertIn("https://docs.python.org/3/library/security_warnings.html", pack)
        self.assertIn("OWASP SSRF Prevention Cheat Sheet", grounding)
        self.assertEqual("synthetic", case["source_kind"])
        self.assertFalse(case["contains_third_party_text"])
        self.assertIn("pys.HC-9", case["required_checks"])


if __name__ == "__main__":
    unittest.main()
