import unittest

from tests.surface_test_lib import assert_devsecops_rule_sets, devsecops_codes


TRUST_BOUNDARY_RULES = {
    "pack": "jsts-security.md",
    "codes": devsecops_codes("jsts.HC", 1, 11) + devsecops_codes("jsts.POS", 1, 11),
    "pack_text": (
        "visible trust-boundary/taint path",
        "API names alone are not findings",
        "https://nodejs.org/api/child_process.html",
    ),
    "grounding_text": ("Vite server options",),
    "behavior_case": "devsecops-audit-behavior-jsts-trust-boundaries",
    "required_checks": ("jsts.HC-11",),
}

ASVS_APP_RULES = {
    "pack": "jsts-security.md",
    "codes": devsecops_codes("jsts.HC", 12, 16) + devsecops_codes("jsts.POS", 12, 15),
    "pack_text": (
        "Emit a `jsts.*` finding only when a risky sink and visible trust-boundary/taint path are both present.",
        "API names alone are not findings",
        "stored password verifier",
    ),
    "urls": (
        "https://github.com/auth0/node-jsonwebtoken",
        "https://github.com/panva/jose/blob/main/docs/jwt/verify/functions/jwtVerify.md",
        "https://github.com/expressjs/session",
        "https://expressjs.com/en/api.html",
        "https://nextjs.org/docs/app/guides/data-security",
        "https://nextjs.org/docs/app/guides/authentication",
        "https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md",
    ),
    "golden_target": "jsts",
    "golden_cases": {
        "DSO-GOLD-0031": (["jsts.HC-13"], [], "block"),
        "DSO-GOLD-0032": (["jsts.HC-12"], [], "block"),
        "DSO-GOLD-0033": ([], ["jsts.HC-12"], "none"),
        "DSO-GOLD-0034": (["jsts.HC-14"], [], "block"),
    },
    "behavior_case": "devsecops-audit-behavior-jsts-asvs-app-rules",
    "source_url": "",
    "required_checks": ("jsts.HC-12",),
    "check_mentions": ("jsts.HC-16",),
    "forbidden_behaviors": ("treat middleware matcher coverage as sufficient Server Action authorization",),
}


class JstsSecurityRulesSurfaceTest(unittest.TestCase):
    def test_rule_sets_keep_catalog_evals_and_grounding(self) -> None:
        assert_devsecops_rule_sets(self, TRUST_BOUNDARY_RULES, ASVS_APP_RULES)


if __name__ == "__main__":
    unittest.main()
