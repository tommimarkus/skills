import unittest

from tests.surface_test_lib import compact, read


PROCEDURE = (
    "souroldgeezer-design/skills/software-design/references/procedures/"
    "native-tool-evidence.md"
)


class SoftwareDesignNativeToolEvidenceTest(unittest.TestCase):
    def test_evidence_protocol_is_project_owned_and_optional(self) -> None:
        procedure = compact(read(PROCEDURE))

        for marker in (
            "Native Tool Evidence shows repeatable evidence from tools this project already uses. It does not require the project to adopt or configure a tool.",
            "manifests, configuration, documented scripts, and CI",
            "project's invocation and settings",
            "`detected-not-run`",
            "never invent configuration",
            "at most one concise optional suggestion",
            "demonstrated evidence gap",
            "never a prerequisite",
            "Equivalent tools share one capability key",
            "30 UTC calendar days after the explicit decision",
            "eligible again on its stored UTC date",
            "missing optional tooling never blocks",
            "never makes the design concern `not-assessed`",
            "Tool findings remain candidates",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, procedure)

    def test_evidence_section_has_a_narrow_rendering_rule(self) -> None:
        procedure = compact(read(PROCEDURE))

        self.assertIn(
            "Render `## Native Tool Evidence` only when there is configured evidence, "
            "`detected-not-run`, or an actually offered suggestion.",
            procedure,
        )
        self.assertIn("Do not render the section when none of those cases applies.", procedure)

    def test_quiet_decision_disclosure_and_deadline_rules_are_exact(self) -> None:
        procedure = compact(read(PROCEDURE))

        self.assertIn("Persist only an explicit `no`, `not now`, or `defer`.", procedure)
        self.assertIn(
            "I’ll remember only this optional tool suggestion in this clone until "
            "`<date>` so it is not repeatedly offered. Fragility findings remain active.",
            procedure,
        )
        for marker in (
            "An active record means total silence: no suggestion and no suppression reminder.",
            "Reading never slides the deadline.",
            "eligible again on its stored UTC date",
            "Renew it only after a new explicit `no`, `not now`, or `defer`.",
            "do not escalate or retry merely to save the preference",
            "keep it conversation-local and disclose that once",
            "no fallback persistence",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, procedure)


if __name__ == "__main__":
    unittest.main()
