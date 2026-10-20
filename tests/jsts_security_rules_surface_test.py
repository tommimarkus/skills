import json
import unittest

from tests.surface_test_lib import REPO_ROOT


PACK = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-extensions/jsts-security.md"
CATALOG = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-smell-catalog.md"
GROUNDING = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/source-grounding.md"
CASES = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/evals/behavior-cases.jsonl"
GOLDEN = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/golden-corpus/devsecops-audit-cases.jsonl"
ASVS_URLS = (
    "https://github.com/auth0/node-jsonwebtoken",
    "https://github.com/panva/jose/blob/main/docs/jwt/verify/functions/jwtVerify.md",
    "https://github.com/expressjs/session",
    "https://expressjs.com/en/api.html",
    "https://nextjs.org/docs/app/guides/data-security",
    "https://nextjs.org/docs/app/guides/authentication",
    "https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md",
)


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

    def test_asvs_app_rules_catalog_evals_and_grounding(self) -> None:
        pack, catalog, grounding = (path.read_text(encoding="utf-8") for path in (PACK, CATALOG, GROUNDING))
        golden = {
            item["id"]: item
            for item in (
                json.loads(line)
                for line in GOLDEN.read_text(encoding="utf-8").splitlines()
                if line
            )
        }
        cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line]
        case = next(item for item in cases if item["id"] == "devsecops-audit-behavior-jsts-asvs-app-rules")

        for code in range(12, 17):
            self.assertIn(f"### `jsts.HC-{code}`", pack)
            self.assertIn(f"| `jsts.HC-{code}` |", catalog)
        for code in range(12, 16):
            self.assertIn(f"### `jsts.POS-{code}`", pack)
            self.assertIn(f"| `jsts.POS-{code}` |", catalog)
        self.assertIn("Emit a `jsts.*` finding only when a risky sink and visible trust-boundary/taint path are both present.", pack)
        self.assertIn("API names alone are not findings", pack)
        self.assertIn("stored password verifier", pack)
        expected = {
            "DSO-GOLD-0031": (["jsts.HC-13"], [], "block"),
            "DSO-GOLD-0032": (["jsts.HC-12"], [], "block"),
            "DSO-GOLD-0033": ([], ["jsts.HC-12"], "none"),
            "DSO-GOLD-0034": (["jsts.HC-14"], [], "block"),
        }
        for case_id, (codes, forbidden, severity) in expected.items():
            self.assertEqual("jsts", golden[case_id]["target"])
            self.assertEqual(codes, golden[case_id]["expected_codes"])
            self.assertEqual(forbidden, golden[case_id]["forbidden_codes"])
            self.assertEqual(severity, golden[case_id]["expected_severity"])
        self.assertEqual("synthetic", case["source_kind"])
        self.assertEqual("", case["source_url"])
        self.assertFalse(case["contains_third_party_text"])
        self.assertIn("jsts.HC-12", case["required_checks"])
        self.assertTrue(any("jsts.HC-16" in check for check in case["required_checks"]))
        self.assertIn(
            "treat middleware matcher coverage as sufficient Server Action authorization",
            case["forbidden_behaviors"],
        )
        for url in ASVS_URLS:
            self.assertIn(url, pack)
            self.assertIn(url, grounding)


if __name__ == "__main__":
    unittest.main()
