import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT


SKILL = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit/SKILL.md"
CORPUS = (
    REPO_ROOT
    / "souroldgeezer-audit/skills/devsecops-audit/references/golden-corpus/devsecops-audit-cases.jsonl"
)
RULE_PACKS = REPO_ROOT / "souroldgeezer-audit/docs/security-reference/devsecops-extensions"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def corpus() -> dict[str, dict[str, object]]:
    return {
        entry["id"]: entry
        for line in read(CORPUS).splitlines()
        if line.strip()
        for entry in (json.loads(line),)
    }


class DevSecOpsQuickGateTest(unittest.TestCase):
    def test_quick_gate_has_deterministic_precedence_and_severity_resolution(self) -> None:
        text = " ".join(read(SKILL).split())
        for requirement in (
            "Quick gate: <status>",
            "after Quick findings",
            "fail > not-evaluated > pass-limited",
            "Warn and info never fail the gate",
            "risk tier remains orthogonal",
            "clean rerun is required after remediation",
            "after evidence gates and carve-outs",
            "most-specific applicable loaded rule controls severity",
            "duplicate overlaps use the highest applicable severity",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement.casefold(), text.casefold())

    def test_quick_blocker_corpus_outcomes_match_loaded_rule_packs(self) -> None:
        expected = {
            "DSO-GOLD-0003": {"gha.HC-2"},
            "DSO-GOLD-0005": {"gha.HC-1"},
            "DSO-GOLD-0008": {"gha.HC-5"},
            "DSO-GOLD-0009": set(),
            "DSO-GOLD-0011": {"docker.HC-1"},
            "DSO-GOLD-0013": {"bicep.HC-1"},
        }
        entries = corpus()
        packs = "\n".join(read(path) for path in RULE_PACKS.glob("*.md"))
        for case_id, extension_codes in expected.items():
            with self.subTest(case_id=case_id):
                entry = entries[case_id]
                self.assertEqual("block", entry["expected_severity"])
                self.assertTrue(extension_codes <= set(entry["expected_codes"]))
                for code in extension_codes:
                    self.assertRegex(packs, rf"(?s){code}.*?\*\*Severity:\*\* `block`", msg=code)

        self.assertIn("DSO-HC-7", entries["DSO-GOLD-0009"]["expected_codes"])

    def test_conditional_carve_outs_preserve_or_downgrade_blockers_explicitly(self) -> None:
        packs = {path.name: " ".join(read(path).split()) for path in RULE_PACKS.glob("*.md")}
        expectations = {
            "github-actions.md": (
                "treat the finding as `block`",
                "carve-out is a downgrade, not a suppression",
                "permissions declaration propagates",
            ),
            "dockerfile.md": (
                "downgrade to `warn` **only when all three conditions hold**",
            ),
            "dotnet-security.md": (
                "more specific wins",
                "suppress the duplicate core finding",
                "when the logged value is sanitized",
            ),
            "python-security.md": (
                "Emit a `pys.*` finding only when both the risky sink and a visible trust-boundary/taint path are present",
            ),
            "jsts-security.md": (
                "Emit a `jsts.*` finding only when a risky sink and visible trust-boundary/taint path are both present",
            ),
            "bicep.md": (
                "Band 1 — always-evaluated",
                "Under `free`, the skill emits one `info` suppression line",
            ),
        }
        for filename, snippets in expectations.items():
            for snippet in snippets:
                with self.subTest(filename=filename, snippet=snippet):
                    self.assertIn(snippet, packs[filename])


if __name__ == "__main__":
    unittest.main()
