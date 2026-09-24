import json
import unittest

from tests.surface_test_lib import REPO_ROOT


DOTNET_EXTENSION = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-extensions/dotnet-security.md"
SMELL_CATALOG = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-smell-catalog.md"
DEVSECOPS_REFERENCE = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops.md"
SOURCE_GROUNDING = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/source-grounding.md"
BEHAVIOR_CASES = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/references/evals/behavior-cases.jsonl"


def load_behavior_case(case_id: str) -> dict:
    with BEHAVIOR_CASES.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            payload = json.loads(line)
            if payload["id"] == case_id:
                return payload
    raise AssertionError(f"Missing behavior eval case: {case_id}")


class DevSecOpsAuditContentTest(unittest.TestCase):
    def test_security_evidence_decision_cases_are_synthetic_and_contract_complete(self) -> None:
        expectations = {
            "devsecops-audit-behavior-release-static-only": (
                "continue independent static inspection using tags, committed release notes, and repository artifacts",
                "stop the entire Deep audit because MCP is unavailable",
            ),
            "devsecops-audit-behavior-hook-presence-unverified": (
                "classify enforcement as unverified when installation and execution evidence are absent",
                "classify the hook as enforcing because it exists and is executable",
            ),
            "devsecops-audit-behavior-pinning-density-95-percent": (
                "reserve DSO-POS-3 for every applicable reference being pinned",
                "emit DSO-POS-3 because pin density exceeds 90 percent",
            ),
            "devsecops-audit-behavior-codex-agents-cost-guidance": (
                "inspect target-repository AGENTS.md and CLAUDE.md regardless of current runtime",
                "skip AGENTS.md because the host is Codex",
            ),
        }
        for case_id, (required, forbidden) in expectations.items():
            with self.subTest(case_id=case_id):
                case = load_behavior_case(case_id)
                self.assertEqual("synthetic", case["source_kind"])
                self.assertFalse(case["contains_third_party_text"])
                self.assertIn(required, case["required_checks"])
                self.assertIn(forbidden, case["forbidden_behaviors"])
                self.assertTrue(case["expected_artifacts"])

    def test_dotnet_log_forging_smell_is_documented_and_eval_backed(self) -> None:
        extension = DOTNET_EXTENSION.read_text(encoding="utf-8")
        catalog = SMELL_CATALOG.read_text(encoding="utf-8")
        grounding = SOURCE_GROUNDING.read_text(encoding="utf-8")
        behavior_case = load_behavior_case("devsecops-audit-behavior-dotnet-log-forging")

        self.assertIn("### `dns.HC-15`", extension)
        self.assertIn("CodeQL `cs/log-forging`", extension)
        self.assertIn("ILogger.Log", extension)
        self.assertIn("AuditLog.Emit", extension)
        self.assertIn("ReplaceLineEndings", extension)
        self.assertIn("hashing/tokenization", extension)
        self.assertIn("strict identifier allowlist", extension)

        self.assertIn("| `dns.HC-15` | Log forging / log injection in structured logs |", catalog)
        self.assertIn("https://codeql.github.com/codeql-query-help/csharp/cs-log-forging/", grounding)

        self.assertEqual("synthetic", behavior_case["source_kind"])
        self.assertFalse(behavior_case["contains_third_party_text"])
        self.assertIn("dns.HC-15", behavior_case["required_checks"])
        self.assertIn(r"run-42\r\nforged=true", behavior_case["prompt"])
        self.assertIn("stays quiet after the safe transform", behavior_case["grader"])

    def test_owasp_cicd_taxonomy_is_referenced_not_reused_verbatim(self) -> None:
        catalog = SMELL_CATALOG.read_text(encoding="utf-8")
        reference = DEVSECOPS_REFERENCE.read_text(encoding="utf-8")
        combined = catalog + "\n" + reference

        self.assertNotIn("Reused verbatim from OWASP", combined)
        self.assertIn("https://owasp.org/www-project-top-10-ci-cd-security-risks/", combined)
        self.assertIn("CC BY-SA 4.0", combined)
        self.assertIn("Do not copy", catalog)
        self.assertIn("upstream risk titles or prose", catalog)
        self.assertIn("uses OWASP's public `CICD-SEC-N` identifiers", reference)


if __name__ == "__main__":
    unittest.main()
