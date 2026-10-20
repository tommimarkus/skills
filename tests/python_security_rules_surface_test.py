import unittest

from tests.surface_test_lib import assert_devsecops_rule_sets, devsecops_codes


TRUST_BOUNDARY_RULES = {
    "pack": "python-security.md",
    "codes": devsecops_codes("pys.HC", 1, 9),
    "pack_text": (
        "visible trust-boundary/taint path",
        "trusted input",
        "non-security",
        "https://docs.python.org/3/library/security_warnings.html",
    ),
    "grounding_text": ("OWASP SSRF Prevention Cheat Sheet",),
    "behavior_case": "devsecops-audit-behavior-python-trust-boundaries",
    "required_checks": ("pys.HC-9",),
}

ASVS_APP_RULES = {
    "pack": "python-security.md",
    "codes": devsecops_codes("pys.HC", 10, 14),
    "inline_codes": devsecops_codes("pys.POS", 6, 9),
    "pack_text": (
        "Emit a `pys.*` finding only when both the risky sink and a\nvisible trust-boundary/taint path are present.",
        "stored password verifier",
    ),
    "urls": (
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
    ),
    "golden_target": "python",
    "golden_cases": {
        "DSO-GOLD-0028": (["pys.HC-13"], [], "block"),
        "DSO-GOLD-0029": (["pys.HC-14"], [], "block"),
        "DSO-GOLD-0030": ([], ["pys.HC-14"], "none"),
    },
    "behavior_case": "devsecops-audit-behavior-python-asvs-app-rules",
    "source_url": "",
    "required_checks": ("pys.HC-10", "pys.HC-14"),
    "forbidden_behaviors": ("emit pys.HC-12 for the usedforsecurity=False call",),
}


class PythonSecurityRulesSurfaceTest(unittest.TestCase):
    def test_rule_sets_keep_catalog_evals_and_grounding(self) -> None:
        assert_devsecops_rule_sets(self, TRUST_BOUNDARY_RULES, ASVS_APP_RULES)


if __name__ == "__main__":
    unittest.main()
