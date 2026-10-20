import unittest

from tests.surface_test_lib import assert_devsecops_rule_sets, devsecops_codes


ASVS_APP_RULES = {
    "pack": "dotnet-security.md",
    "codes": devsecops_codes("dns.HC", 16, 20) + devsecops_codes("dns.POS", 6, 9),
    "pack_text": ("ASVS 5.0.0 V3.4.3, V3.4.5",),
    "pack_absent": ("ASVS V14",),
    "urls": (
        "https://learn.microsoft.com/en-us/dotnet/api/microsoft.identitymodel.tokens.tokenvalidationparameters",
        "https://learn.microsoft.com/en-us/dotnet/api/microsoft.aspnetcore.http.cookieoptions",
        "https://learn.microsoft.com/en-us/aspnet/core/security/samesite",
        "https://learn.microsoft.com/en-us/dotnet/standard/security/vulnerabilities-cbc-mode",
        "https://learn.microsoft.com/en-us/aspnet/core/security/data-protection/consumer-apis/password-hashing",
        "https://learn.microsoft.com/en-us/dotnet/api/system.net.http.httpclienthandler.dangerousacceptanyservercertificatevalidator",
        "https://learn.microsoft.com/en-us/sql/connect/ado-net/connection-string-syntax",
        "https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md",
    ),
    "urls_in_pack": False,
    "golden_target": "dotnet",
    "golden_cases": {
        "DSO-GOLD-0025": (["dns.HC-20"], [], "block"),
        "DSO-GOLD-0026": (["dns.HC-16"], [], "block"),
        "DSO-GOLD-0027": ([], ["dns.HC-18"], "none"),
    },
    "behavior_case": "devsecops-audit-behavior-dotnet-asvs-app-rules",
    "source_url": "",
    "required_checks": ("dns.HC-16", "dns.HC-20"),
    "forbidden_behaviors": ("emit dns.HC-18 for the ETag",),
}


class DotnetSecurityRulesSurfaceTest(unittest.TestCase):
    def test_rule_sets_keep_catalog_evals_and_grounding(self) -> None:
        assert_devsecops_rule_sets(self, ASVS_APP_RULES)


if __name__ == "__main__":
    unittest.main()
