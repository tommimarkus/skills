"""Every audit skill must have a committed fidelity floor.

`load_cost_guard.py` soft-blocks edits that make a smell code, section, or
Load-Map pointer unreachable in a guarded skill's closure — but it ALWAYS allows
on a **missing baseline**. A skill with no `baselines/<skill>.json` is therefore
silently unguarded, and a green test run looks identical either way. These tests
close that hole for the audit plugin, where all four skills share one craft core.
"""

import json
import unittest

from tests.surface_test_lib import REPO_ROOT


AUDIT_SKILLS_DIR = REPO_ROOT / "souroldgeezer-audit/skills"
BASELINES = REPO_ROOT / "tests/skill_load_cost/baselines"


def audit_skill_names() -> list[str]:
    return sorted(p.name for p in AUDIT_SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file())


class AuditLoadCostCoverageTest(unittest.TestCase):
    def test_the_audit_plugin_ships_the_four_known_skills(self) -> None:
        """Guards the loop below: a renamed/added skill must be a deliberate change."""
        self.assertEqual(
            audit_skill_names(),
            ["devsecops-audit", "ip-hygiene", "lean-audit", "test-quality-audit"],
        )

    def test_every_audit_skill_has_a_committed_baseline(self) -> None:
        for skill in audit_skill_names():
            with self.subTest(skill=skill):
                self.assertTrue(
                    (BASELINES / f"{skill}.json").is_file(),
                    f"{skill} has no baseline — the per-use guard fails open for it",
                )

    def test_every_audit_baseline_protects_codes_and_sections(self) -> None:
        """A baseline with zero codes reads as coverage while protecting nothing.

        `ip-hygiene` produced exactly that until `code_patterns.json` gained its
        `IP-*` entries: 103 sections, 0 codes.
        """
        for skill in audit_skill_names():
            baseline = json.loads((BASELINES / f"{skill}.json").read_text(encoding="utf-8"))
            with self.subTest(skill=skill):
                self.assertTrue(baseline.get("codes"), f"{skill} baseline protects no finding codes")
                self.assertTrue(baseline.get("sections"), f"{skill} baseline protects no sections")


if __name__ == "__main__":
    unittest.main()
