import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOTNET_EXTENSION = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-extensions/dotnet-security.md"
SMELL_CATALOG = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-smell-catalog.md"
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


if __name__ == "__main__":
    unittest.main()
