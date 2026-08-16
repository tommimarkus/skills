"""Finding-emitting skills must have a committed fidelity floor.

`load_cost_guard.py` soft-blocks edits that make a smell code, section, or
Load-Map pointer unreachable in a guarded skill's closure — but it ALWAYS allows
on a **missing baseline**. A skill with no `baselines/<skill>.json` is therefore
silently unguarded, and a green test run looks identical either way.

Scope is every skill that emits finding codes: the audit, design, and
architecture plugins. The `souroldgeezer-ops` and `souroldgeezer-policy` skills
are exempt and asserted to stay that way — they emit no finding codes at all, so
a code floor would protect nothing, and only a section floor would apply. If one
of them ever gains a code namespace, `test_exempt_plugins_still_emit_no_codes`
fails and the exemption gets re-decided rather than silently inherited.

The companion `skill_load_cost_floor_test.py` checks that each committed baseline
is still a valid floor; this file checks that one exists and is not empty.
"""

import json
import re
import unittest

from tests.surface_test_lib import REPO_ROOT


BASELINES = REPO_ROOT / "tests/skill_load_cost/baselines"
CODE_PATTERNS = REPO_ROOT / "tests/skill_load_cost/code_patterns.json"

GUARDED_PLUGINS = ("souroldgeezer-audit", "souroldgeezer-design", "souroldgeezer-architecture")
EXEMPT_PLUGINS = ("souroldgeezer-ops", "souroldgeezer-policy")


def skills_in(plugin: str) -> list[str]:
    root = REPO_ROOT / plugin / "skills"
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "SKILL.md").is_file())


def guarded_skills() -> list[str]:
    return sorted(s for plugin in GUARDED_PLUGINS for s in skills_in(plugin))


class LoadCostCoverageTest(unittest.TestCase):
    def test_the_guarded_skill_set_is_what_we_think(self) -> None:
        """Guards the loops below: an added/renamed skill must be a deliberate change."""
        self.assertEqual(
            guarded_skills(),
            [
                "api-design",
                "app-design",
                "architecture-design",
                "devsecops-audit",
                "infra-design",
                "ip-hygiene",
                "lean-audit",
                "software-design",
                "test-quality-audit",
            ],
        )

    def test_every_finding_emitting_skill_has_a_committed_baseline(self) -> None:
        for skill in guarded_skills():
            with self.subTest(skill=skill):
                self.assertTrue(
                    (BASELINES / f"{skill}.json").is_file(),
                    f"{skill} has no baseline — the per-use guard fails open for it",
                )

    def test_every_baseline_protects_codes_and_sections(self) -> None:
        """A baseline with zero codes reads as coverage while protecting nothing.

        `ip-hygiene` produced exactly that until `code_patterns.json` gained its
        `IP-*` entries: 103 sections, 0 codes.
        """
        for skill in guarded_skills():
            baseline = json.loads((BASELINES / f"{skill}.json").read_text(encoding="utf-8"))
            with self.subTest(skill=skill):
                self.assertTrue(baseline.get("codes"), f"{skill} baseline protects no finding codes")
                self.assertTrue(baseline.get("sections"), f"{skill} baseline protects no sections")

    def test_exempt_plugins_still_emit_no_codes(self) -> None:
        """The ops/policy exemption rests on them having no code namespace. Verify it holds."""
        patterns = json.loads(CODE_PATTERNS.read_text(encoding="utf-8"))
        for plugin in EXEMPT_PLUGINS:
            for skill in skills_in(plugin):
                text = (REPO_ROOT / plugin / "skills" / skill / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                found = {c for pattern in patterns for c in re.findall(pattern, text)}
                with self.subTest(skill=skill):
                    self.assertEqual(
                        found,
                        set(),
                        f"{skill} now emits finding codes {sorted(found)} — it is no longer "
                        f"exempt from the baseline requirement; re-decide the exemption",
                    )


if __name__ == "__main__":
    unittest.main()
