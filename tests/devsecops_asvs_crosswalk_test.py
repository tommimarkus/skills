"""Guard for the devsecops-audit ASVS 5.0.0 requirement-ID crosswalk.

Repository files only, no network: the inventory shape, per-chapter level
counts, the closed class set, code references back to the smell catalog, the
summary table, and that ASVS citations elsewhere in the skill resolve to
inventory IDs.
"""
import re
import unittest

from tests.surface_test_lib import REPO_ROOT

SECURITY_REF = REPO_ROOT / "souroldgeezer-audit/docs/security-reference"
SKILL_DIR = REPO_ROOT / "souroldgeezer-audit/skills/devsecops-audit"
CROSSWALK = SECURITY_REF / "devsecops-asvs-crosswalk.md"
CATALOG = SECURITY_REF / "devsecops-smell-catalog.md"

CLASSES = ("static", "partial", "documentation", "runtime", "uncovered")
CODED_CLASSES = {"static", "partial"}
EXPECTED_LEVELS = {
    "V1": (8, 19, 3), "V2": (4, 7, 2), "V3": (8, 11, 12), "V4": (2, 8, 6),
    "V5": (4, 5, 4), "V6": (13, 22, 12), "V7": (6, 12, 1), "V8": (4, 3, 6),
    "V9": (4, 3, 0), "V10": (5, 24, 7), "V11": (3, 11, 10), "V12": (3, 6, 3),
    "V13": (1, 12, 8), "V14": (2, 7, 4), "V15": (3, 10, 8), "V16": (0, 16, 1),
    "V17": (0, 7, 5),
}
BATCH_CODES = (
    [f"dns.HC-{n}" for n in range(16, 21)] + [f"dns.POS-{n}" for n in range(6, 10)]
    + [f"pys.HC-{n}" for n in range(10, 15)] + [f"pys.POS-{n}" for n in range(6, 10)]
    + [f"jsts.HC-{n}" for n in range(12, 17)] + [f"jsts.POS-{n}" for n in range(12, 16)]
)
SHA256 = "8201b20eec2908c3380ac600c91c8ba746346fbb808859366abb232027532311"

ROW_RE = re.compile(r"^\| (V\d+\.\d+\.\d+) \| L([123]) \| ([a-z]+) \| (.+) \|$", re.M)
SUMMARY_RE = re.compile(r"^\| (V\d+|Total) \|((?: \d+ \|){9})$", re.M)
CITATION_RE = re.compile(r"ASVS 5\.0\.0 (V\d+(?:\.\d+)*(?:, V\d+(?:\.\d+)*)*)")


def parse_rows(text: str) -> list[dict]:
    rows = []
    for rid, level, cls, codes in ROW_RE.findall(text):
        code_list = [] if codes == "—" else re.findall(r"`([^`]+)`", codes)
        rows.append({
            "id": rid, "chapter": rid.split(".")[0], "level": level,
            "class": cls, "codes": code_list, "codes_cell": codes,
        })
    return rows


class DevsecopsAsvsCrosswalkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = CROSSWALK.read_text(encoding="utf-8")
        cls.rows = parse_rows(cls.text)

    def test_inventory_has_345_unique_well_formed_ids(self) -> None:
        ids = [row["id"] for row in self.rows]
        self.assertEqual(345, len(ids))
        self.assertEqual(345, len(set(ids)))
        for rid in ids:
            self.assertRegex(rid, r"^V\d+\.\d+\.\d+$")

    def test_per_chapter_level_counts_match_the_release(self) -> None:
        counts: dict[str, list[int]] = {}
        for row in self.rows:
            counts.setdefault(row["chapter"], [0, 0, 0])[int(row["level"]) - 1] += 1
        self.assertEqual(EXPECTED_LEVELS, {k: tuple(v) for k, v in counts.items()})

    def test_chapter_headings_follow_upstream_order(self) -> None:
        headings = re.findall(r"^## (V\d+) \S", self.text, re.M)
        self.assertEqual(list(EXPECTED_LEVELS), headings)

    def test_classes_are_closed_and_codes_exist_in_the_catalog(self) -> None:
        catalog = CATALOG.read_text(encoding="utf-8")
        for row in self.rows:
            with self.subTest(req=row["id"]):
                self.assertIn(row["class"], CLASSES)
                if row["class"] in CODED_CLASSES:
                    self.assertTrue(row["codes"], "static/partial rows need codes")
                    for code in row["codes"]:
                        self.assertIn(f"| `{code}` |", catalog)
                else:
                    self.assertEqual("—", row["codes_cell"])

    def test_every_batch_code_is_mapped(self) -> None:
        mapped = {code for row in self.rows for code in row["codes"]}
        for code in BATCH_CODES:
            self.assertIn(code, mapped)

    def test_summary_counts_match_rows(self) -> None:
        summary = {
            name: [int(n) for n in cells.replace("|", " ").split()]
            for name, cells in SUMMARY_RE.findall(self.text)
        }
        self.assertEqual(list(EXPECTED_LEVELS) + ["Total"], list(summary))
        total = [0] * 9
        for chapter in EXPECTED_LEVELS:
            rows = [r for r in self.rows if r["chapter"] == chapter]
            expected = [sum(1 for r in rows if r["level"] == lv) for lv in "123"]
            expected += [sum(1 for r in rows if r["class"] == c) for c in CLASSES]
            expected.append(len(rows))
            self.assertEqual(expected, summary[chapter], chapter)
            total = [a + b for a, b in zip(total, expected)]
        self.assertEqual(total, summary["Total"])
        self.assertEqual(345, summary["Total"][-1])

    def test_header_pins_the_edition_and_asset(self) -> None:
        header = self.text.split("## Summary", 1)[0]
        for needle in ("OWASP ASVS 5.0.0", "v5.0.0_release", SHA256, "CC BY-SA 4.0"):
            self.assertIn(needle, header)

    def test_skill_asvs_citations_resolve_and_legacy_forms_are_gone(self) -> None:
        ids = {row["id"] for row in self.rows}
        files = sorted(SECURITY_REF.glob("**/*.md")) + sorted(SKILL_DIR.glob("**/*.md"))
        self.assertTrue(files)
        for path in files:
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(REPO_ROOT)
            with self.subTest(file=str(rel)):
                self.assertNotRegex(text, r"ASVS V\d")
                self.assertNotIn("14 chapters", text)
                for group in CITATION_RE.findall(text):
                    for cited in group.split(", "):
                        self.assertTrue(
                            cited in ids or any(i.startswith(cited + ".") for i in ids),
                            f"{rel}: ASVS 5.0.0 {cited} is not an inventory ID or prefix",
                        )


if __name__ == "__main__":
    unittest.main()
