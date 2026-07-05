# lean-audit:dup-intentional — identifier-rich parallel test bodies (CLAUDE.md § Repo-local Python® tooling)
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "souroldgeezer-architecture"
    / "skills"
    / "architecture-design"
    / "references"
    / "scripts"
    / "svg-accessible-name.sh"
)

SVG_NS = "http://www.w3.org/2000/svg"
RENDERED_SVG = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<svg xmlns="{SVG_NS}" viewBox="0 0 400 300" width="400" height="300">\n'
    '<g data-dediren-node-id="n1"><rect x="10" y="10" width="80" height="40"/></g>\n'
    '<path data-dediren-edge-id="e1" d="M10 10 L90 50"/>\n'
    "</svg>\n"
)
NATIVE_SVG = (
    f'<svg xmlns="{SVG_NS}" role="img" viewBox="0 0 10 10">\n'
    "<title>Native name</title><rect/>\n"
    "</svg>"
)


def run_script(*args: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *map(str, args)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class SvgAccessibleNameTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.svg = Path(self._tmp.name) / "view.svg"
        self.svg.write_text(RENDERED_SVG, encoding="utf-8")

    def apply(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = run_script(*args, self.svg)
        self.assertEqual(
            result.returncode, 0, f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        return result

    def test_apply_injects_accessible_name_and_visible_title(self) -> None:
        self.apply("--title", "Order flow", "--desc", "Which components serve checkout?")
        content = self.svg.read_text(encoding="utf-8")

        root = ET.fromstring(content)
        self.assertEqual(root.get("role"), "img")
        self.assertEqual(root.get("aria-labelledby"), "arch-a11y-title")
        self.assertEqual(root.get("aria-describedby"), "arch-a11y-desc")
        title = root.find(f"{{{SVG_NS}}}title")
        assert title is not None
        self.assertEqual(title.text, "Order flow")
        self.assertEqual(title.get("id"), "arch-a11y-title")
        desc = root.find(f"{{{SVG_NS}}}desc")
        assert desc is not None
        self.assertEqual(desc.text, "Which components serve checkout?")

        visible = [
            el
            for el in root.iter(f"{{{SVG_NS}}}text")
            if el.get("data-arch-a11y") == "visible-title"
        ]
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].text, "Order flow")

        self.assertEqual(root.get("viewBox"), "0 -32 400 332")
        self.assertEqual(root.get("data-arch-a11y-viewbox"), "0 0 400 300")

        # Runtime-owned markers must survive untouched.
        self.assertIn('data-dediren-node-id="n1"', content)
        self.assertIn('data-dediren-edge-id="e1"', content)

    def test_apply_without_desc_labels_by_title_only(self) -> None:
        self.apply("--title", "Order flow")
        root = ET.fromstring(self.svg.read_text(encoding="utf-8"))
        self.assertEqual(root.get("aria-labelledby"), "arch-a11y-title")
        self.assertIsNone(root.get("aria-describedby"))
        self.assertIsNone(root.find(f"{{{SVG_NS}}}desc"))

    def test_apply_escapes_xml_metacharacters(self) -> None:
        self.apply("--title", 'A <b> & "c"', "--desc", "x > y & z")
        content = self.svg.read_text(encoding="utf-8")
        root = ET.fromstring(content)  # would raise if unescaped
        title = root.find(f"{{{SVG_NS}}}title")
        assert title is not None
        self.assertEqual(title.text, 'A <b> & "c"')
        desc = root.find(f"{{{SVG_NS}}}desc")
        assert desc is not None
        self.assertEqual(desc.text, "x > y & z")

    def test_rerun_is_idempotent(self) -> None:
        self.apply("--title", "Order flow", "--desc", "Question?")
        first = self.svg.read_text(encoding="utf-8")
        self.apply("--title", "Order flow", "--desc", "Question?")
        self.assertEqual(first, self.svg.read_text(encoding="utf-8"))

    def test_rerun_replaces_previous_injection_without_stacking(self) -> None:
        self.apply("--title", "Old title", "--desc", "Old question?")
        self.apply("--title", "New title")
        content = self.svg.read_text(encoding="utf-8")
        root = ET.fromstring(content)
        self.assertEqual(root.get("viewBox"), "0 -32 400 332")
        self.assertEqual(root.get("aria-labelledby"), "arch-a11y-title")
        self.assertNotIn("Old title", content)
        self.assertNotIn("Old question?", content)
        self.assertIsNone(root.find(f"{{{SVG_NS}}}desc"))
        titles = root.findall(f"{{{SVG_NS}}}title")
        self.assertEqual(len(titles), 1)
        self.assertEqual(titles[0].text, "New title")

    def test_check_fails_before_apply_and_passes_after(self) -> None:
        before = run_script("--check", "--title", "Order flow", self.svg)
        self.assertEqual(before.returncode, 1)
        self.assertIn("accessible-name: missing", before.stdout)
        self.assertIn("visible-title: missing", before.stdout)

        self.apply("--title", "Order flow")
        after = run_script("--check", "--title", "Order flow", self.svg)
        self.assertEqual(after.returncode, 0, after.stdout)
        self.assertIn("accessible-name: present", after.stdout)
        self.assertIn("visible-title: present", after.stdout)

    def test_check_does_not_modify_the_file(self) -> None:
        before = self.svg.read_text(encoding="utf-8")
        run_script("--check", "--title", "Order flow", self.svg)
        self.assertEqual(before, self.svg.read_text(encoding="utf-8"))

    def test_runtime_native_accessible_name_is_completed(self) -> None:
        self.svg.write_text(NATIVE_SVG, encoding="utf-8")
        result = self.apply("--title", "View label", "--desc", "Which parts cooperate?")
        self.assertIn("completed native accessible name", result.stdout)

        content = self.svg.read_text(encoding="utf-8")
        root = ET.fromstring(content)
        self.assertEqual(root.get("role"), "img")
        # Native markup is kept, not re-labelled through injected ids.
        self.assertIsNone(root.get("aria-labelledby"))
        titles = root.findall(f"{{{SVG_NS}}}title")
        self.assertEqual(len(titles), 1)
        self.assertEqual(titles[0].text, "View label")
        self.assertIsNone(titles[0].get("id"))
        descs = root.findall(f"{{{SVG_NS}}}desc")
        self.assertEqual(len(descs), 1)
        self.assertEqual(descs[0].text, "Which parts cooperate?")
        visible = [
            el
            for el in root.iter(f"{{{SVG_NS}}}text")
            if el.get("data-arch-a11y") == "visible-title"
        ]
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].text, "View label")
        self.assertEqual(root.get("viewBox"), "0 -32 10 42")
        self.assertEqual(root.get("data-arch-a11y-viewbox"), "0 0 10 10")

        check = run_script("--check", "--title", "View label", self.svg)
        self.assertEqual(check.returncode, 0, check.stdout)

    def test_native_completion_is_idempotent(self) -> None:
        self.svg.write_text(NATIVE_SVG, encoding="utf-8")
        self.apply("--title", "View label", "--desc", "Which parts cooperate?")
        first = self.svg.read_text(encoding="utf-8")
        self.apply("--title", "View label", "--desc", "Which parts cooperate?")
        self.assertEqual(first, self.svg.read_text(encoding="utf-8"))

    def test_v1_injected_artifact_upgrades_without_stacking(self) -> None:
        v1 = (
            f'<svg xmlns="{SVG_NS}" viewBox="0 -32 400 332" data-arch-a11y="root"'
            ' data-arch-a11y-viewbox="0 0 400 300" role="img"'
            ' aria-labelledby="arch-a11y-title arch-a11y-desc">\n'
            '<title id="arch-a11y-title">Old</title>\n'
            '<desc id="arch-a11y-desc">Old question?</desc>\n'
            '<text data-arch-a11y="visible-title" x="8" y="-12" font-family="sans-serif"'
            ' font-size="16" font-weight="bold">Old</text>\n'
            "<rect/></svg>"
        )
        self.svg.write_text(v1, encoding="utf-8")
        self.apply("--title", "New")
        content = self.svg.read_text(encoding="utf-8")
        root = ET.fromstring(content)
        self.assertEqual(root.get("viewBox"), "0 -32 400 332")
        self.assertEqual(root.get("aria-labelledby"), "arch-a11y-title")
        self.assertNotIn("Old", content)
        titles = root.findall(f"{{{SVG_NS}}}title")
        self.assertEqual(len(titles), 1)
        self.assertEqual(titles[0].text, "New")

    def test_non_svg_input_exits_3(self) -> None:
        self.svg.write_text("not an svg", encoding="utf-8")
        result = run_script("--title", "x", self.svg)
        self.assertEqual(result.returncode, 3)

    def test_svg_without_viewbox_exits_3(self) -> None:
        self.svg.write_text(f'<svg xmlns="{SVG_NS}"><rect/></svg>', encoding="utf-8")
        result = run_script("--title", "x", self.svg)
        self.assertEqual(result.returncode, 3)
        self.assertIn("<rect/>", self.svg.read_text(encoding="utf-8"))

    def test_usage_errors_exit_2(self) -> None:
        self.assertEqual(run_script().returncode, 2)
        self.assertEqual(run_script(self.svg).returncode, 2)  # apply needs --title
        self.assertEqual(run_script("--bogus", self.svg).returncode, 2)

    def test_help_exits_0_with_usage(self) -> None:
        result = run_script("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertIn("--check", result.stdout)


if __name__ == "__main__":
    unittest.main()
