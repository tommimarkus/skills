# lean-audit:dup-intentional — identifier-rich parallel test bodies (CLAUDE.md § Repo-local Python® tooling)
import importlib.util
import subprocess
import sys
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
    / "svg-accessible-name.py"
)

SVG_NS = "http://www.w3.org/2000/svg"
# A supported render: the runtime named it (role="img" + <title>) from the view's
# own presentation, as every release >= 2026.07.28 does. No background rect, so
# the band-theming path is not exercised here (DARK_BG_SVG / LIGHT_BG_SVG cover it).
RENDERED_SVG = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<svg xmlns="{SVG_NS}" role="img" viewBox="0 0 400 300" width="400" height="300">\n'
    "<title>order-flow</title>\n"
    '<g data-dediren-node-id="n1"><rect x="10" y="10" width="80" height="40"/></g>\n'
    '<path data-dediren-edge-id="e1" d="M10 10 L90 50"/>\n'
    "</svg>\n"
)
# Out-of-support input: a render with no accessible name at all. Only reachable
# from render output committed before 2026.07.28 — the documented support floor refuses to
# resolve such a runtime now, but this step takes a file path, not a runtime.
UNNAMED_SVG = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<svg xmlns="{SVG_NS}" viewBox="0 0 400 300" width="400" height="300">\n'
    '<g data-dediren-node-id="n1"><rect x="10" y="10" width="80" height="40"/></g>\n'
    "</svg>\n"
)
NATIVE_SVG = (
    f'<svg xmlns="{SVG_NS}" role="img" viewBox="0 0 10 10">\n'
    "<title>Native name</title><rect/>\n"
    "</svg>"
)
# Native renders that carry a full-viewBox background rect, as dediren emits.
# The band background and title fill are derived from that rect, so these cover
# the theme-matching that RENDERED_SVG (no background rect) cannot. Dediren
# emits float geometry (400.0) against an integer viewBox; the detection must
# match numerically. Node rects carry stroke + a dediren marker and must not be
# mistaken for the background.
DARK_BG_SVG = (
    f'<svg xmlns="{SVG_NS}" role="img" viewBox="0 0 400 300" width="400" height="300">\n'
    "<title>Native name</title>\n"
    '<rect x="0.0" y="0.0" width="400.0" height="300.0" fill="#0B1021"/>\n'
    '<g data-dediren-node-id="n1"><rect x="10" y="10" width="80" height="40"'
    ' fill="#123456" stroke="#8899aa"/></g>\n'
    "</svg>\n"
)
LIGHT_BG_SVG = DARK_BG_SVG.replace("#0B1021", "#ffffff")
# An artifact a former version of this step injected a synthesised name into,
# in the two-id `aria-labelledby` form. Kept as a fixture because `_strip_prior`
# still has to undo that shape cleanly.
V1_INJECTED_SVG = (
    f'<svg xmlns="{SVG_NS}" viewBox="0 -32 400 332" data-arch-a11y="root"'
    ' data-arch-a11y-viewbox="0 0 400 300" role="img"'
    ' aria-labelledby="arch-a11y-title arch-a11y-desc">\n'
    '<title id="arch-a11y-title">Old</title>\n'
    '<desc id="arch-a11y-desc">Old question?</desc>\n'
    '<text data-arch-a11y="visible-title" x="8" y="-12" font-family="sans-serif"'
    ' font-size="16" font-weight="bold">Old</text>\n'
    "<rect/></svg>"
)


def load_script_module():
    """Import the step as a module for direct unit tests. The filename has a
    hyphen, so it is not importable by name; load it from its path."""
    spec = importlib.util.spec_from_file_location("svg_accessible_name", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(*args: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
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

    @staticmethod
    def _band_rects(root: ET.Element) -> list[ET.Element]:
        return [
            el
            for el in root.iter(f"{{{SVG_NS}}}rect")
            if el.get("data-arch-a11y") == "band-bg"
        ]

    @staticmethod
    def _visible_titles(root: ET.Element) -> list[ET.Element]:
        return [
            el
            for el in root.iter(f"{{{SVG_NS}}}text")
            if el.get("data-arch-a11y") == "visible-title"
        ]

    def test_apply_sets_accessible_name_and_adds_visible_title(self) -> None:
        self.apply("--title", "Order flow", "--desc", "Which components serve checkout?")
        content = self.svg.read_text(encoding="utf-8")

        root = ET.fromstring(content)
        # The runtime's own markup is kept and retitled — never re-labelled
        # through injected ids and aria-*, which this step no longer emits.
        self.assertEqual(root.get("role"), "img")
        self.assertIsNone(root.get("aria-labelledby"))
        self.assertIsNone(root.get("aria-describedby"))
        title = root.find(f"{{{SVG_NS}}}title")
        assert title is not None
        self.assertEqual(title.text, "Order flow")
        self.assertIsNone(title.get("id"))
        desc = root.find(f"{{{SVG_NS}}}desc")
        assert desc is not None
        self.assertEqual(desc.text, "Which components serve checkout?")
        self.assertIsNone(desc.get("id"))

        visible = [
            el
            for el in root.iter(f"{{{SVG_NS}}}text")
            if el.get("data-arch-a11y") == "visible-title"
        ]
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].text, "Order flow")

        self.assertEqual(root.get("viewBox"), "0 -32 400 332")
        self.assertEqual(root.get("data-arch-a11y-viewbox"), "0 0 400 300")

        # Defect 1: the root width/height stay in sync with the band-expanded
        # viewBox, or the aspect mismatch letterboxes the diagram. Width is
        # unchanged (the band is added above); height grows by the 32px band;
        # the original height is recorded so reruns restore then re-grow it.
        self.assertEqual(root.get("width"), "400")
        self.assertEqual(root.get("height"), "332")
        self.assertEqual(root.get("data-arch-a11y-height"), "300")

        # RENDERED_SVG has no full-viewBox background rect, so the theme-aware
        # band is not derivable: no band rect is painted and the title keeps the
        # default fill (prior behavior preserved on the fallback path).
        self.assertEqual(self._band_rects(root), [])
        self.assertIsNone(visible[0].get("fill"))

        # Runtime-owned markers must survive untouched.
        self.assertIn('data-dediren-node-id="n1"', content)
        self.assertIn('data-dediren-edge-id="e1"', content)

    def test_apply_without_desc_adds_no_desc_element(self) -> None:
        self.apply("--title", "Order flow")
        root = ET.fromstring(self.svg.read_text(encoding="utf-8"))
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

    def test_rerun_replaces_previous_output_without_stacking(self) -> None:
        self.apply("--title", "Old title", "--desc", "Old question?")
        self.apply("--title", "New title")
        content = self.svg.read_text(encoding="utf-8")
        root = ET.fromstring(content)
        self.assertEqual(root.get("viewBox"), "0 -32 400 332")
        self.assertNotIn("Old title", content)
        titles = root.findall(f"{{{SVG_NS}}}title")
        self.assertEqual(len(titles), 1)
        self.assertEqual(titles[0].text, "New title")
        self.assertEqual(len(self._visible_titles(root)), 1)

        # Ownership rule: the <title>/<desc> belong to the render, not to this
        # step, so omitting --desc means "leave the description alone" — the
        # prior run's <desc> survives rather than being silently dropped. (It
        # carries no marker id, so the step cannot tell it from a runtime one.)
        descs = root.findall(f"{{{SVG_NS}}}desc")
        self.assertEqual(len(descs), 1)
        self.assertEqual(descs[0].text, "Old question?")

    def test_check_fails_on_missing_band_and_passes_after_apply(self) -> None:
        # A supported render already has its accessible name, so check mode is
        # really asking "did this step run?" — the band is the discriminator.
        before = run_script("--check", "--title", "Order flow", self.svg)
        self.assertEqual(before.returncode, 1)
        self.assertIn("accessible-name: present", before.stdout)
        self.assertIn("visible-title: missing", before.stdout)

        self.apply("--title", "Order flow")
        after = run_script("--check", "--title", "Order flow", self.svg)
        self.assertEqual(after.returncode, 0, after.stdout)
        self.assertIn("accessible-name: present", after.stdout)
        self.assertIn("visible-title: present", after.stdout)

    def test_check_reports_missing_name_on_an_unnamed_artifact(self) -> None:
        self.svg.write_text(UNNAMED_SVG, encoding="utf-8")
        result = run_script("--check", "--title", "Order flow", self.svg)
        self.assertEqual(result.returncode, 1)
        self.assertIn("accessible-name: missing", result.stdout)

    def test_check_does_not_modify_the_file(self) -> None:
        before = self.svg.read_text(encoding="utf-8")
        run_script("--check", "--title", "Order flow", self.svg)
        self.assertEqual(before, self.svg.read_text(encoding="utf-8"))

    def test_runtime_native_accessible_name_is_retitled_and_banded(self) -> None:
        self.svg.write_text(NATIVE_SVG, encoding="utf-8")
        result = self.apply("--title", "View label", "--desc", "Which parts cooperate?")
        self.assertIn("visible title block added", result.stdout)

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

    def test_unnamed_artifact_is_refused_and_left_unchanged(self) -> None:
        # Refusing beats banding it: a banded artifact with no accessible name
        # looks processed while still failing SC 1.1.1 (ARCH-R-2).
        self.svg.write_text(UNNAMED_SVG, encoding="utf-8")
        result = run_script("--title", "Order flow", self.svg)
        self.assertEqual(result.returncode, 4)
        self.assertEqual(self.svg.read_text(encoding="utf-8"), UNNAMED_SVG)

    def test_v1_injected_artifact_is_refused_after_stripping_to_unnamed(self) -> None:
        # An artifact a former version of this step injected into: strip removes
        # the synthesised name, leaving genuinely unnamed input, which is refused.
        self.svg.write_text(V1_INJECTED_SVG, encoding="utf-8")
        result = run_script("--title", "New", self.svg)
        self.assertEqual(result.returncode, 4)
        self.assertEqual(self.svg.read_text(encoding="utf-8"), V1_INJECTED_SVG)

    def test_strip_prior_drops_role_and_aria_it_once_injected(self) -> None:
        """`_strip_prior` must key the role/aria cleanup on the id-marked nodes it
        removed, not on an `aria-labelledby` string. The injected form varied —
        "arch-a11y-title" alone, or the two-id "arch-a11y-title arch-a11y-desc"
        used below — so the old string match missed the two-id case and left
        `role` and `aria-*` pointing at ids that no longer existed. Exercised
        directly: on the refusal path nothing is written, so the stripped tree is
        not observable through the file."""
        root = ET.fromstring(V1_INJECTED_SVG)
        load_script_module()._strip_prior(root)

        self.assertIsNone(root.get("role"))
        self.assertIsNone(root.get("aria-labelledby"))
        self.assertIsNone(root.get("aria-describedby"))
        # The owned nodes and markers are gone and the viewBox is restored.
        self.assertEqual(root.get("viewBox"), "0 0 400 300")
        self.assertIsNone(root.get("data-arch-a11y"))
        self.assertIsNone(root.get("data-arch-a11y-viewbox"))
        self.assertEqual(root.findall(f"{{{SVG_NS}}}title"), [])
        self.assertEqual(root.findall(f"{{{SVG_NS}}}desc"), [])
        self.assertEqual(self._visible_titles(root), [])


    def test_width_height_synced_keeps_aspect_ratio(self) -> None:
        # The rendered aspect ratio is preserved: width/height agree with the
        # band-expanded viewBox, so browsers don't letterbox with transparent
        # bars that read as a border on light surfaces (issue #99, defect 1).
        before = ET.fromstring(RENDERED_SVG)
        self.apply("--title", "Order flow")
        after = ET.fromstring(self.svg.read_text(encoding="utf-8"))
        self.assertEqual(after.get("width"), before.get("width"))
        self.assertEqual(int(after.get("height") or 0), int(before.get("height") or 0) + 32)
        vb = [float(n) for n in (after.get("viewBox") or "").split()]
        self.assertEqual(float(after.get("width") or 0), vb[2])
        self.assertEqual(float(after.get("height") or 0), vb[3])

    def test_dark_background_paints_matching_band_and_light_title(self) -> None:
        # Dark render policy: the band is painted with the diagram's own dark
        # background and the title takes a light, contrasting fill, so it is not
        # a black-on-dark invisible title (issue #99, defect 2).
        self.svg.write_text(DARK_BG_SVG, encoding="utf-8")
        self.apply("--title", "Amber CRT model", "--desc", "What cooperates?")
        content = self.svg.read_text(encoding="utf-8")
        root = ET.fromstring(content)

        band = self._band_rects(root)
        self.assertEqual(len(band), 1)
        # Band matches the diagram background verbatim, and spans the band above.
        self.assertEqual(band[0].get("fill"), "#0B1021")
        self.assertEqual(band[0].get("y"), "-32")
        self.assertEqual(band[0].get("height"), "32")
        self.assertEqual(band[0].get("width"), "400")

        visible = self._visible_titles(root)
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].get("fill"), "#ffffff")

        # Paint order: the band rect precedes the title text so it sits under it.
        self.assertLess(
            content.index('data-arch-a11y="band-bg"'),
            content.index('data-arch-a11y="visible-title"'),
        )
        # The node rect (stroke + dediren marker) is never taken for the bg.
        self.assertNotIn('fill="#123456"', content.split("band-bg", 1)[0])

    def test_light_background_paints_matching_band_and_dark_title(self) -> None:
        self.svg.write_text(LIGHT_BG_SVG, encoding="utf-8")
        self.apply("--title", "Light view")
        root = ET.fromstring(self.svg.read_text(encoding="utf-8"))

        band = self._band_rects(root)
        self.assertEqual(len(band), 1)
        self.assertEqual(band[0].get("fill"), "#ffffff")
        visible = self._visible_titles(root)
        self.assertEqual(visible[0].get("fill"), "#000000")

    def test_background_fixture_rerun_is_idempotent(self) -> None:
        self.svg.write_text(DARK_BG_SVG, encoding="utf-8")
        self.apply("--title", "Amber CRT model", "--desc", "What cooperates?")
        first = self.svg.read_text(encoding="utf-8")
        self.apply("--title", "Amber CRT model", "--desc", "What cooperates?")
        self.assertEqual(first, self.svg.read_text(encoding="utf-8"))

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
