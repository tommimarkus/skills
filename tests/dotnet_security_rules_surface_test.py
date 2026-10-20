import json
import unittest

from tests.surface_test_lib import REPO_ROOT


PACK = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-extensions/dotnet-security.md"
CATALOG = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-smell-catalog.md"
REFS = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references"
GROUNDING = REFS / "source-grounding.md"
BEHAVIOR = REFS / "evals/behavior-cases.jsonl"
GOLDEN = REFS / "golden-corpus/devsecops-audit-cases.jsonl"

GROUNDING_URLS = (
    "https://learn.microsoft.com/en-us/dotnet/api/microsoft.identitymodel.tokens.tokenvalidationparameters",
    "https://learn.microsoft.com/en-us/dotnet/api/microsoft.aspnetcore.http.cookieoptions",
    "https://learn.microsoft.com/en-us/aspnet/core/security/samesite",
    "https://learn.microsoft.com/en-us/dotnet/standard/security/vulnerabilities-cbc-mode",
    "https://learn.microsoft.com/en-us/aspnet/core/security/data-protection/consumer-apis/password-hashing",
    "https://learn.microsoft.com/en-us/dotnet/api/system.net.http.httpclienthandler.dangerousacceptanyservercertificatevalidator",
    "https://learn.microsoft.com/en-us/sql/connect/ado-net/connection-string-syntax",
    "https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md",
)


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


class DotnetSecurityRulesSurfaceTest(unittest.TestCase):
    def test_pack_headings_catalog_rows_and_citation(self) -> None:
        pack = PACK.read_text(encoding="utf-8")
        catalog = CATALOG.read_text(encoding="utf-8")
        for code in [f"HC-{n}" for n in range(16, 21)] + [f"POS-{n}" for n in range(6, 10)]:
            self.assertIn(f"### `dns.{code}`", pack)
            self.assertIn(f"| `dns.{code}` |", catalog)
        self.assertIn("ASVS 5.0.0 V3.4.3, V3.4.5", pack)
        self.assertNotIn("ASVS V14", pack)

    def test_golden_cases_expect_codes_and_severities(self) -> None:
        cases = {item["id"]: item for item in _jsonl(GOLDEN)}
        expected = {
            "DSO-GOLD-0025": (["dns.HC-20"], [], "block"),
            "DSO-GOLD-0026": (["dns.HC-16"], [], "block"),
            "DSO-GOLD-0027": ([], ["dns.HC-18"], "none"),
        }
        for case_id, (codes, forbidden, severity) in expected.items():
            case = cases[case_id]
            self.assertEqual("dotnet", case["target"])
            self.assertEqual(codes, case["expected_codes"])
            self.assertEqual(forbidden, case["forbidden_codes"])
            self.assertEqual(severity, case["expected_severity"])

    def test_behavior_case_and_grounding(self) -> None:
        case = next(
            item for item in _jsonl(BEHAVIOR)
            if item["id"] == "devsecops-audit-behavior-dotnet-asvs-app-rules"
        )
        self.assertEqual("synthetic", case["source_kind"])
        self.assertEqual("", case["source_url"])
        self.assertFalse(case["contains_third_party_text"])
        self.assertIn("dns.HC-16", case["required_checks"])
        self.assertIn("dns.HC-20", case["required_checks"])
        self.assertIn("emit dns.HC-18 for the ETag", case["forbidden_behaviors"])
        grounding = GROUNDING.read_text(encoding="utf-8")
        for url in GROUNDING_URLS:
            self.assertIn(url, grounding)


if __name__ == "__main__":
    unittest.main()
