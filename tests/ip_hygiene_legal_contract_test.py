import unittest

from tests.surface_test_lib import read


SKILL = "souroldgeezer-audit/skills/ip-hygiene/SKILL.md"
REFS = "souroldgeezer-audit/skills/ip-hygiene/references"


class IpHygieneLegalContractTest(unittest.TestCase):
    def assertContainsAll(self, text: str, fragments: tuple[str, ...]) -> None:
        for fragment in fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_core_uses_settled_authority_criteria_and_lane_contracts(self) -> None:
        skill = read(SKILL)
        self.assertContainsAll(
            skill,
            (
                "binding law",
                "operative licence term",
                "holder policy",
                "project convention",
                "conservative repository policy",
                "IP-SRC-*",
                "IP-COPY-*",
                "IP-DB-*",
                "IP-LIC-*",
                "IP-MARK-*",
                "prospective decision",
                "limited-assurance triage",
                "reasonable-hygiene in-depth review",
            ),
        )

    def test_in_depth_verdict_remediation_and_assurance_are_bounded(self) -> None:
        skill = read(SKILL)
        self.assertIn(
            "in-depth verdict: <blocked | qualified | no-blocker-identified>", skill
        )
        self.assertNotIn("in-depth verdict: <clean", skill)
        self.assertContainsAll(
            skill,
            (
                "read-only by default",
                "remediated:",
                "fresh rerun",
                "No finding or verdict is legal clearance",
            ),
        )

    def test_finding_contract_requires_decision_complete_evidence(self) -> None:
        skill = read(SKILL)
        self.assertContainsAll(
            skill,
            (
                "criterion and authority class",
                "condition and exact location",
                "source identity and provenance",
                "intended act",
                "mention, link, quote, copy, modify, aggregate, link/import, execute, or redistribute",
                "distribution form and audience",
                "jurisdiction and applicability",
                "fact or inference",
                "confidence and evidence",
                "cause",
                "consequence",
                "recommendation",
                "severity",
                "risk tier",
                "counsel outcome",
            ),
        )

    def test_scope_exclusions_disclaimers_and_counsel_triggers_are_explicit(self) -> None:
        skill = read(SKILL)
        self.assertContainsAll(
            skill,
            (
                "not legal advice",
                "does not provide legal clearance",
                "does not certify compliance",
                "does not perform a freedom-to-operate search",
                "patents",
                "privacy and data protection",
                "trade secrets",
                "publicity and personality rights",
                "defamation",
                "export controls",
                "live or threatened dispute",
                "cease-and-desist",
                "bespoke agreement",
                "contested ownership",
                "combined-work or copyleft classification",
                "country-specific clearance",
                "disputed exception",
            ),
        )

    def test_trademark_reference_separates_the_required_questions(self) -> None:
        trademark = read(f"{REFS}/trademark.md")
        self.assertContainsAll(
            trademark,
            (
                "EU trade marks and harmonized national marks",
                "referential use",
                "artifact branding",
                "registration status",
                "endorsement or commercial connection",
                "holder policy",
                "optional symbols",
                "B2C",
                "transactional decision",
                "factual context",
                "material",
            ),
        )
        self.assertNotIn(
            "A false `®` claim is a misleading commercial practice", trademark
        )

    def test_copyright_reference_distinguishes_permission_and_rights(self) -> None:
        copyright_ref = read(f"{REFS}/copyright.md")
        self.assertContainsAll(
            copyright_ref,
            (
                "Citation records provenance; it is not permission",
                "lawful quotation",
                "original paraphrase",
                "copied expression",
                "functional ideas and interfaces",
                "protected selection or arrangement",
                "database copyright",
                "sui generis database right",
            ),
        )

    def test_licence_reference_requires_act_specific_analysis(self) -> None:
        licence = read(f"{REFS}/licence-assets.md")
        self.assertContainsAll(
            licence,
            (
                "permissive notice and attribution terms",
                "GPL, LGPL, and AGPL",
                "modification, combination, linking or importing, aggregation, distribution, and network interaction",
                "Creative Commons",
                "fonts",
                "documentation",
                "schemas",
                "data",
                "media",
                "dual licensing",
                "exceptions and additional permissions",
                "file-level overrides",
                "Never infer that a repository-wide licence covers third-party material",
            ),
        )
        self.assertNotIn("No licence statement means all rights reserved", licence)
        self.assertNotIn("Do not bundle GPL-family", licence)

    def test_authority_index_classifies_primary_authority(self) -> None:
        authority = read(f"{REFS}/authority-index.md")
        self.assertContainsAll(
            authority,
            (
                "Authority classes",
                "binding law",
                "operative licence term",
                "holder policy",
                "project convention",
                "conservative repository policy",
                "Directive (EU) 2015/2436",
                "Directive 2009/24/EC",
                "Directive 96/9/EC",
                "GNU Affero General Public License 3.0",
                "Creative Commons 4.0 legal code",
            ),
        )


if __name__ == "__main__":
    unittest.main()
