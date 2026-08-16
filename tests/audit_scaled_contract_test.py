import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT


AUDIT_REFERENCE = REPO_ROOT / "souroldgeezer-audit/docs/audit-reference"
SCALED_AUDIT = AUDIT_REFERENCE / "scaled-audit.md"
AUDIT_CRAFT = AUDIT_REFERENCE / "audit-craft.md"

AUDIT_SKILLS = (
    "devsecops-audit",
    "ip-hygiene",
    "lean-audit",
    "test-quality-audit",
)

# The cue every capped load must carry (docs/skill-architecture.md, "escalation cue").
ESCALATION_CUE = "load it then rather than continuing"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(path: Path) -> str:
    return " ".join(read(path).split())


class ScaledAuditContractTest(unittest.TestCase):
    def test_shared_reference_exists_and_orders_the_three_rungs(self) -> None:
        self.assertTrue(SCALED_AUDIT.is_file(), f"missing {SCALED_AUDIT}")
        body = flat(SCALED_AUDIT)
        for rung in (
            "**Inline**, with the §2 durability floor.",
            "**Delegated** slices per §3, when the host offers delegation.",
            "**Sampled** per sampling-projection.md, when the subject still exceeds capacity.",
        ):
            with self.subTest(rung=rung):
                self.assertIn(rung, body)
        self.assertIn(
            "Dropping to (c) while (a) or (b) was still available",
            body,
            "the rungs must be ordered, not a menu",
        )

    def test_durability_floor_reuses_an_existing_per_item_record(self) -> None:
        body = flat(SCALED_AUDIT)
        self.assertIn("AS IT GOES", body)
        self.assertIn("references/procedures/per-test-output-fields.md", body)
        self.assertIn("audit-craft.md §3's 5 C's", body)
        self.assertIn("Do not invent a second shape.", body)

    def test_delegation_protocol_states_preconditions_and_the_parent_split(self) -> None:
        body = flat(SCALED_AUDIT)
        for clause in (
            # preconditions, all four
            "Deep/in-depth mode",
            "the host offers delegation",
            "this run is not itself a delegated worker",
            "the subject exceeds comfortable inline enumeration",
            "Any one unmet → rung (a).",
            # parent before dispatch
            "Never delegate these",
            # worker prohibitions
            "must not re-derive the population, re-run the risk survey, sample, or emit a gate, verdict, rollup, or footer",
            # worker return
            "never raw content, file dumps, or transcripts",
            # parent after collection
            "Reconcile coverage FIRST",
            "never relabel it as a sample",
            # degradation
            "Never reduce scope silently because delegation was unavailable.",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, body)

    def test_lane_table_covers_every_audit_skill(self) -> None:
        body = flat(SCALED_AUDIT)
        for skill in AUDIT_SKILLS:
            with self.subTest(skill=skill):
                self.assertIn(f"`{skill}`", body)
        self.assertIn(
            "**not divisible by file**",
            body,
            "lean-audit's clone-pair carve-out is the entry most likely to prevent damage",
        )

    def test_audit_craft_routes_to_the_shared_reference(self) -> None:
        craft = flat(AUDIT_CRAFT)
        self.assertIn("## §6a Scaled audits", craft)
        self.assertIn("See scaled-audit.md", craft)
        # §6a must not renumber the sections existing citations depend on.
        for existing in ("## §6 Sampling and projection", "## §7 Extension pattern"):
            with self.subTest(existing=existing):
                self.assertIn(existing, craft)

    def test_every_audit_skill_loads_it_conditionally_with_an_escalation_cue(self) -> None:
        for skill in AUDIT_SKILLS:
            path = REPO_ROOT / f"souroldgeezer-audit/skills/{skill}/SKILL.md"
            body = flat(path)
            with self.subTest(skill=skill):
                self.assertIn("scaled-audit.md", body, f"{skill} does not cite the shared reference")
                self.assertIn(
                    ESCALATION_CUE,
                    body,
                    f"{skill} caps the load without naming an escalation cue",
                )

    def test_the_load_is_never_unconditional(self) -> None:
        """A bare 'Load scaled-audit.md.' would put it on every audit's floor."""
        for skill in AUDIT_SKILLS:
            path = REPO_ROOT / f"souroldgeezer-audit/skills/{skill}/SKILL.md"
            for line in read(path).splitlines():
                if "scaled-audit.md" not in line:
                    continue
                with self.subTest(skill=skill, line=line.strip()):
                    self.assertFalse(
                        line.rstrip().endswith("(delegation + evidence durability)."),
                        "citing line reads as an unconditional load",
                    )


if __name__ == "__main__":
    unittest.main()
