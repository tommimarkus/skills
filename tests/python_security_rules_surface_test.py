import json
import unittest

from tests.surface_test_lib import REPO_ROOT


PACK = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-extensions/python-security.md"
CATALOG = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-smell-catalog.md"
GROUNDING = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/source-grounding.md"
CASES = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/evals/behavior-cases.jsonl"
GOLDEN = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/golden-corpus/devsecops-audit-cases.jsonl"
ASVS_URLS = (
    "https://pyjwt.readthedocs.io/en/stable/api.html",
    "https://docs.djangoproject.com/en/stable/ref/settings/",
    "https://docs.djangoproject.com/en/stable/topics/auth/passwords/",
    "https://docs.djangoproject.com/en/stable/ref/middleware/",
    "https://flask.palletsprojects.com/en/stable/web-security/",
    "https://docs.python.org/3/library/hashlib.html",
    "https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/",
    "https://fastapi.tiangolo.com/tutorial/security/",
    "https://www.django-rest-framework.org/api-guide/permissions/",
    "https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md",
)


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

    def test_asvs_app_rules_catalog_evals_and_grounding(self) -> None:
        pack = PACK.read_text(encoding="utf-8")
        catalog = CATALOG.read_text(encoding="utf-8")
        grounding = GROUNDING.read_text(encoding="utf-8")
        golden = {
            item["id"]: item
            for item in (
                json.loads(line)
                for line in GOLDEN.read_text(encoding="utf-8").splitlines()
                if line
            )
        }
        cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line]
        case = next(item for item in cases if item["id"] == "devsecops-audit-behavior-python-asvs-app-rules")

        for code in range(10, 15):
            self.assertIn(f"### `pys.HC-{code}`", pack)
            self.assertIn(f"| `pys.HC-{code}` |", catalog)
        for code in range(6, 10):
            self.assertIn(f"`pys.POS-{code}`", pack)
            self.assertIn(f"| `pys.POS-{code}` |", catalog)
        self.assertIn(
            "Emit a `pys.*` finding only when both the risky sink and a\nvisible trust-boundary/taint path are present.",
            pack,
        )
        self.assertIn("stored password verifier", pack)
        expected = {
            "DSO-GOLD-0028": (["pys.HC-13"], [], "block"),
            "DSO-GOLD-0029": (["pys.HC-14"], [], "block"),
            "DSO-GOLD-0030": ([], ["pys.HC-14"], "none"),
        }
        for case_id, (codes, forbidden, severity) in expected.items():
            self.assertEqual("python", golden[case_id]["target"])
            self.assertEqual(codes, golden[case_id]["expected_codes"])
            self.assertEqual(forbidden, golden[case_id]["forbidden_codes"])
            self.assertEqual(severity, golden[case_id]["expected_severity"])
        self.assertEqual("synthetic", case["source_kind"])
        self.assertEqual("", case["source_url"])
        self.assertFalse(case["contains_third_party_text"])
        self.assertIn("pys.HC-10", case["required_checks"])
        self.assertIn("pys.HC-14", case["required_checks"])
        self.assertIn("emit pys.HC-12 for the usedforsecurity=False call", case["forbidden_behaviors"])
        for url in ASVS_URLS:
            self.assertIn(url, pack)
            self.assertIn(url, grounding)


if __name__ == "__main__":
    unittest.main()
