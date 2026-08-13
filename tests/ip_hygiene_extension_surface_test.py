import re
import unittest

from tests.surface_test_lib import REPO_ROOT, read


SKILL_DIR = REPO_ROOT / "souroldgeezer-audit" / "skills" / "ip-hygiene"
AUTHORING = "souroldgeezer-audit/skills/ip-hygiene/references/procedures/extension-authoring.md"

REQUIRED_SECTIONS = (
    "Detection signals",
    "Comment and doc-comment syntax",
    "Header placement and ordering",
    "Ecosystem licence metadata",
    "Vendoring conventions",
    "Generated-code banners",
    "Notice-survival mechanics",
    "Mark surfaces",
    "Criteria",
)

# The transformations IP-LIC-5 (licence-assets.md) already names as covered by
# notice survival. A namespaced extension criterion that only restates one of
# these as the substance of what it covers is a mechanism of IP-LIC-5, not a
# genuinely new question (extension-authoring.md § "In practice a pack usually
# defines no namespaced criterion").
CORE_LIC5_TRANSFORMATIONS = (
    "minification",
    "minify",
    "minifier",
    "bundling",
    "bundle",
    "bundler",
    "transpilation",
    "transpile",
    "vendoring",
    "vendor",
    "generation",
    "generated",
    "move",
    "split",
    "extract",
)


def extract_headings(text: str) -> list[str]:
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def extract_required_section_bullets(text: str) -> list[str]:
    """Section names as declared by extension-authoring.md's own required-sections
    bullet list (`- **<name>** — ...`), not as `##` headings (that document
    describes the pack contract; it does not itself carry those headings)."""
    return [
        match.group(1)
        for match in re.finditer(r"^- \*\*([^*]+)\*\*\s*—", text, re.MULTILINE)
    ]


def extract_current_extensions_table(authoring: str) -> dict[str, str]:
    """Map pack filename -> declared namespace from the Current Extensions table."""
    table: dict[str, str] = {}
    for line in authoring.splitlines():
        match = re.match(r"\|\s*`([\w.-]+\.md)`\s*\|[^|]*\|\s*`([\w.]+)`\s*\|", line)
        if match:
            table[match.group(1)] = match.group(2)
    return table


def criteria_section(pack_text: str) -> str:
    match = re.search(r"^## Criteria\s*$(.*)\Z", pack_text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def assert_namespaced_criterion_does_not_restate_core_transformation(
    tc: unittest.TestCase, pack_name: str, pack_text: str, namespace: str
) -> None:
    """A pack's Criteria section must either explicitly state it defines no
    namespaced criterion, or (if it does add one) that addition must not be
    merely a language-specific mechanism of a transformation IP-LIC-5 already
    names. This is the craft-guard the lesson learned: today no pack adds one,
    and each says so; a future pack that adds one restating minification,
    bundling, transpilation, vendoring, generation, move, split, or extract as
    the substance of its new criterion is not a genuinely new question."""
    section = criteria_section(pack_text)
    tc.assertTrue(section.strip(), f"{pack_name}: no Criteria section body found")

    no_criterion_stated = re.search(
        rf"No\s+`{re.escape(namespace)}IP-\*`\s+numbered criterion is defined", section
    )
    if no_criterion_stated:
        return

    added_ids = set(re.findall(rf"{re.escape(namespace)}IP-[A-Z]+-\d+", section))
    tc.assertTrue(
        added_ids,
        f"{pack_name}: Criteria section neither states 'none' nor names an "
        f"added {namespace}IP-* criterion",
    )
    lowered = section.lower()
    for word in CORE_LIC5_TRANSFORMATIONS:
        tc.assertNotIn(
            word,
            lowered,
            f"{pack_name} declares a namespaced criterion but names "
            f"'{word}', a transformation IP-LIC-5 already covers",
        )


class IpHygieneExtensionSurfaceTest(unittest.TestCase):
    def test_authoring_procedure_declares_nine_required_sections_in_order(self) -> None:
        authoring = read(AUTHORING)
        bullets = extract_required_section_bullets(authoring)
        self.assertEqual(bullets, list(REQUIRED_SECTIONS))

    def test_each_pack_carries_all_nine_required_sections_in_order(self) -> None:
        for pack_path in sorted((SKILL_DIR / "extensions").glob("*.md")):
            with self.subTest(pack=pack_path.name):
                text = pack_path.read_text(encoding="utf-8")
                headings = extract_headings(text)
                normalized = [heading.lower() for heading in headings]
                expected = [section.lower() for section in REQUIRED_SECTIONS]
                self.assertEqual(
                    normalized,
                    expected,
                    f"{pack_path.name} section headings {headings} do not match "
                    f"the required order {list(REQUIRED_SECTIONS)}",
                )

    def test_each_pack_declares_its_reserved_namespace_and_criteria_disposition(self) -> None:
        authoring = read(AUTHORING)
        table = extract_current_extensions_table(authoring)
        self.assertTrue(table, "Current Extensions table did not parse any rows")

        for pack_path in sorted((SKILL_DIR / "extensions").glob("*.md")):
            with self.subTest(pack=pack_path.name):
                text = pack_path.read_text(encoding="utf-8")
                self.assertIn(
                    pack_path.name,
                    table,
                    f"{pack_path.name} is not listed in the Current Extensions table",
                )
                namespace = table[pack_path.name]
                section = criteria_section(text)
                self.assertIn(
                    namespace,
                    section,
                    f"{pack_path.name}'s Criteria section does not mention its "
                    f"reserved namespace `{namespace}`",
                )
                self.assertTrue(
                    re.search(rf"No\s+`{re.escape(namespace)}IP-\*`\s+numbered criterion is defined", section)
                    or re.search(rf"{re.escape(namespace)}IP-[A-Z]+-\d+", section),
                    f"{pack_path.name}'s Criteria section does not state what it "
                    "does to the criteria set (add, carve out, or none)",
                )

    def test_packs_and_authoring_table_agree_on_filenames_and_namespaces(self) -> None:
        authoring = read(AUTHORING)
        table = extract_current_extensions_table(authoring)
        pack_files = {path.name for path in (SKILL_DIR / "extensions").glob("*.md")}

        self.assertEqual(set(table), pack_files)

        for filename, namespace in table.items():
            with self.subTest(pack=filename):
                text = (SKILL_DIR / "extensions" / filename).read_text(encoding="utf-8")
                self.assertIn(
                    namespace,
                    criteria_section(text),
                    f"{filename}'s declared namespace `{namespace}` does not "
                    "appear in its own Criteria section",
                )

    def test_no_pack_currently_adds_a_namespaced_criterion_restating_core_lic5(self) -> None:
        authoring = read(AUTHORING)
        table = extract_current_extensions_table(authoring)
        for pack_path in sorted((SKILL_DIR / "extensions").glob("*.md")):
            with self.subTest(pack=pack_path.name):
                text = pack_path.read_text(encoding="utf-8")
                namespace = table[pack_path.name]
                assert_namespaced_criterion_does_not_restate_core_transformation(
                    self, pack_path.name, text, namespace
                )

    def test_synthetic_pack_restating_core_lic5_transformation_is_rejected(self) -> None:
        namespace = "fake."
        offending_pack = (
            "## Criteria\n\n"
            "This pack adds `fake.IP-LIC-9 Bundler notice loss`, which "
            "requires notices to survive minification and bundling in the "
            "FakeLang toolchain.\n"
        )
        with self.assertRaises(AssertionError):
            assert_namespaced_criterion_does_not_restate_core_transformation(
                self, "fake.md", offending_pack, namespace
            )

    def test_synthetic_pack_adding_a_genuinely_new_criterion_is_accepted(self) -> None:
        namespace = "fake."
        genuine_pack = (
            "## Criteria\n\n"
            "This pack adds `fake.IP-MARK-9 Package-index squatting`, which "
            "records whether a published package name impersonates an "
            "unrelated third-party project on the language's package index. "
            "No core criterion asks this question.\n"
        )
        assert_namespaced_criterion_does_not_restate_core_transformation(
            self, "fake.md", genuine_pack, namespace
        )


if __name__ == "__main__":
    unittest.main()
