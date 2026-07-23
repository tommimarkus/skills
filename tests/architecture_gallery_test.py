# lean-audit:dup-intentional — identifier-rich parallel test bodies (CLAUDE.md § Repo-local Python® tooling)
import importlib.util
import json as _json
import os
import re
import shutil
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(
    REPO, "souroldgeezer-architecture", "skills", "architecture-design",
    "references", "scripts", "build-gallery.py")


def _load():
    spec = importlib.util.spec_from_file_location("build_gallery", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ClassifyTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def test_archimate_any_kind_is_A(self):
        self.assertEqual(self.m.classify("archimate", "Application Cooperation")[3], "A")
        self.assertEqual(self.m.classify("archimate", "Technology")[3], "A")

    def test_uml_families(self):
        self.assertEqual(self.m.classify("uml", "UML Sequence")[3], "S")
        self.assertEqual(self.m.classify("uml", "UML Communication")[3], "S")
        self.assertEqual(self.m.classify("uml", "UML Class")[3], "T")
        self.assertEqual(self.m.classify("uml", "Object")[3], "T")
        self.assertEqual(self.m.classify("uml", "Component")[3], "C")
        self.assertEqual(self.m.classify("uml", "Deployment")[3], "C")
        self.assertEqual(self.m.classify("uml", "Activity")[3], "B")
        self.assertEqual(self.m.classify("uml", "State Machine")[3], "B")
        self.assertEqual(self.m.classify("uml", "Use Case")[3], "B")

    def test_uml_unknown_kind_falls_back_to_U(self):
        self.assertEqual(self.m.classify("uml", "")[3], "U")
        self.assertEqual(self.m.classify("uml", "Timing")[3], "U")

    def test_section_note_tracks_notation(self):
        self.assertEqual(self.m.classify("archimate", "x")[2], "ArchiMate 3.2")
        self.assertEqual(self.m.classify("uml", "UML Class")[2], "UML 2.5")

    def test_density(self):
        self.assertEqual(self.m.status_of(49), "ok")
        self.assertEqual(self.m.status_of(50), "warning")


class ProfileResolverTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def test_v2_reads_models_profile(self):
        proj = {
            "schema": "souroldgeezer.architecture.dediren.project.v2",
            "models": [{"id": "arch", "file": "model.json", "profile": "archimate"},
                       {"id": "uml", "file": "model-uml.json", "profile": "uml"}],
            "views": [{"id": "a", "model": "arch"}, {"id": "b", "model": "uml"}],
        }
        prof = self.m.profile_resolver(proj, "/nonexistent")
        self.assertEqual(prof(proj["views"][0]), "archimate")
        self.assertEqual(prof(proj["views"][1]), "uml")

    def test_v1_reads_model_semantic_profile(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "model.json"), "w", encoding="utf-8") as fh:
                _json.dump({"plugins": {"generic-graph": {"semantic_profile": "uml"}}}, fh)
            proj = {"schema": "souroldgeezer.architecture.dediren.project.v1",
                    "model": "model.json", "views": [{"id": "main"}]}
            prof = self.m.profile_resolver(proj, d)
            self.assertEqual(prof(proj["views"][0]), "uml")

    def test_defaults_to_archimate_when_unresolvable(self):
        proj = {"schema": "...v1", "model": "missing.json", "views": [{"id": "x"}]}
        prof = self.m.profile_resolver(proj, "/nonexistent")
        self.assertEqual(prof(proj["views"][0]), "archimate")

    def test_v1_non_dict_model_defaults_to_archimate(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "model.json"), "w", encoding="utf-8") as fh:
                _json.dump([], fh)  # valid JSON, not an object
            proj = {"schema": "...v1", "model": "model.json", "views": [{"id": "x"}]}
            prof = self.m.profile_resolver(proj, d)
            self.assertEqual(prof(proj["views"][0]), "archimate")


FIXTURE = os.path.join(
    REPO, "souroldgeezer-architecture", "skills", "architecture-design",
    "references", "fixtures", "dediren", "rendered")


class BuildHtmlTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()
        self.html = self.m.build_html(FIXTURE)

    def test_self_contained_no_external_refs(self):
        # No external fetches. Namespace URIs (xmlns / xmlns:xlink) are inert
        # identifiers, never fetched, so they are NOT external references and
        # must not trip this guard. Catch real fetches in any quote style:
        # src/href to an http(s) or protocol-relative URL, @import, and
        # url(...) pointing at http(s).
        external = re.search(
            r'(?:src|href)\s*=\s*["\']?(?:https?:)?//'
            r'|@import'
            r'|url\(\s*["\']?https?:',
            self.html)
        self.assertIsNone(external,
                          "external resource reference found: %r"
                          % (external.group(0) if external else None))

    def test_svgs_inlined_verbatim_keep_namespace(self):
        # Verbatim inlining preserves the renderer's SVG namespace (not stripped).
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', self.html)

    def test_every_svg_inlined_as_template(self):
        self.assertEqual(self.html.count('class="plate"'), 3)
        self.assertIn('data-id="app-cooperation"', self.html)
        self.assertIn('data-id="domain-class"', self.html)
        self.assertIn('data-id="order-sequence"', self.html)
        self.assertIn("data-dediren-node-id", self.html)

    def test_sections_derived_from_real_profiles(self):
        # ArchiMate view -> A/ArchiMate views ; UML class -> T ; UML sequence -> S
        self.assertIn("ArchiMate views", self.html)
        self.assertIn("Structure & data", self.html)
        self.assertIn("Sequences", self.html)
        self.assertIn('"code": "A1"', self.html)
        self.assertIn('"code": "T1"', self.html)
        self.assertIn('"code": "S1"', self.html)

    def test_english_chrome_and_lang(self):
        self.assertIn('lang="en"', self.html)
        self.assertNotIn("tiheä", self.html)
        self.assertNotIn("asettelu", self.html)
        self.assertNotIn("Konteksti", self.html)
        self.assertNotIn("solmua", self.html)

    def test_counts_from_render_metadata(self):
        # Each view's node/edge counts are read from its own render-metadata,
        # not a single global pair. Parse the embedded DATA array and assert
        # every view's counts match its committed metadata exactly.
        match = re.search(r"const DATA = (\[.*?\]);", self.html, re.S)
        self.assertIsNotNone(match, "gallery DATA array not found")
        counts = {v["id"]: (v["nodes"], v["edges"])
                  for v in _json.loads(match.group(1))}
        self.assertEqual(counts, {
            "app-cooperation": (2, 1),
            "domain-class": (3, 1),
            "order-sequence": (3, 1),
        })

    def test_model_titles_pass_through(self):
        self.assertIn("Message domain model", self.html)

    def test_missing_source_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "project.json"), "w", encoding="utf-8") as fh:
                _json.dump({"schema": "v2", "models": [], "views": [
                    {"id": "x", "model": "m", "title": "X", "diagramKind": "UML Class",
                     "render": {"output": "generated/svg/x.svg"},
                     "metadata": {"output": "generated/render-metadata/x.json"}}]}, fh)
            with self.assertRaises(self.m.SourceMissing):
                self.m.build_html(d)

    def test_empty_views_package_builds_with_guarded_bootstrap(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "project.json"), "w", encoding="utf-8") as fh:
                _json.dump({"schema": "...v2", "feature": "empty",
                            "models": [], "views": []}, fh)
            html = self.m.build_html(d)          # must not raise
            self.assertIn("const DATA = []", html)
            self.assertIn("if (DATA.length)", html)


# A dark-render-policy SVG mirroring the real post-#99 structure: a band rect
# (data-arch-a11y), the full-canvas diagram background rect, and a node rect
# (data-dediren + stroke). Only the diagram background rect should be picked.
_DARK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" role="img" width="200" height="132" '
    'viewBox="0 -32 200 132" data-arch-a11y="root" '
    'data-arch-a11y-viewbox="0 0 200 100" data-arch-a11y-height="100">\n'
    '<rect data-arch-a11y="band-bg" x="0" y="-32" width="200" height="32" fill="#0c0a06"/>\n'
    '<rect x="0" y="0" width="200" height="100" fill="#0C0A06"/>\n'
    '<rect data-dediren-node-shape="uml_class" x="20" y="20" width="80" height="40" '
    'fill="#1a1a1a" stroke="#e8a33d"/>\n'
    '<title id="arch-a11y-title">Dark</title></svg>')


def _mk_pkg(d, svg, theme=None):
    """Write a one-view package (project.json, svg, render-metadata) into d."""
    os.makedirs(os.path.join(d, "generated", "svg"), exist_ok=True)
    os.makedirs(os.path.join(d, "generated", "render-metadata"), exist_ok=True)
    proj = {"schema": "...v2", "feature": "amber",
            "models": [{"id": "u", "file": "m.json", "profile": "uml"}],
            "views": [{"id": "v", "model": "u", "title": "Dark view",
                       "diagramKind": "UML Class",
                       "render": {"output": "generated/svg/v.svg"},
                       "metadata": {"output": "generated/render-metadata/v.json"}}]}
    with open(os.path.join(d, "project.json"), "w", encoding="utf-8") as fh:
        _json.dump(proj, fh)
    with open(os.path.join(d, "generated", "svg", "v.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg)
    with open(os.path.join(d, "generated", "render-metadata", "v.json"), "w",
              encoding="utf-8") as fh:
        _json.dump({"nodes": {"n": 1}, "edges": {}}, fh)
    if theme is not None:
        with open(os.path.join(d, "gallery-theme.json"), "w", encoding="utf-8") as fh:
            _json.dump(theme, fh)


def _data(html):
    return _json.loads(re.search(r"const DATA = (\[.*?\]);", html, re.S).group(1))


def _sheet_derive(html):
    return re.search(r"const SHEET_DERIVE = (\w+);", html).group(1)


def _root_css(html):
    # the three theme-scoped rule blocks, up to the first non-theme rule
    return re.search(r":root\{.*?\*\{box-sizing", html, re.S).group(0)


class SheetDerivationTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def test_original_viewbox_prefers_a11y_marker(self):
        # the pre-band original, not the band-expanded root viewBox
        self.assertEqual(self.m._original_viewbox(_DARK_SVG), [0.0, 0.0, 200.0, 100.0])

    def test_original_viewbox_falls_back_to_root(self):
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-5 -5 50 40"><g/></svg>'
        self.assertEqual(self.m._original_viewbox(svg), [-5.0, -5.0, 50.0, 40.0])

    def test_original_viewbox_unparseable_is_none(self):
        self.assertIsNone(self.m._original_viewbox("<svg><g/></svg>"))

    def test_diagram_fill_picks_background_not_band_or_node(self):
        # verbatim fill of the full-canvas rect (case preserved)
        self.assertEqual(self.m._svg_diagram_fill(_DARK_SVG), "#0C0A06")

    def test_diagram_fill_white_render(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
               '<rect x="0" y="0" width="10" height="10" fill="#ffffff"/></svg>')
        self.assertEqual(self.m._svg_diagram_fill(svg), "#ffffff")

    def test_diagram_fill_transparent_render_is_none(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
               '<circle r="3"/></svg>')
        self.assertIsNone(self.m._svg_diagram_fill(svg))

    def test_luminance_and_mix(self):
        self.assertGreater(self.m._lum("#ffffff"), 128)
        self.assertLess(self.m._lum("#0C0A06"), 128)
        self.assertEqual(self.m._mix("#000000", "#ffffff", 0.5), "#808080")

    def test_derived_sheet_dark_gets_lighter_border(self):
        sheet, line = self.m._derived_sheet("#0C0A06")
        self.assertEqual(sheet, "#0C0A06")            # sheet == diagram bg
        self.assertGreater(self.m._lum(line), self.m._lum(sheet))  # visible edge

    def test_plate_sheet_derives_dark_but_not_white_or_transparent(self):
        self.assertEqual(self.m._plate_sheet(_DARK_SVG)[0], "#0C0A06")
        white = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                 '<rect x="0" y="0" width="10" height="10" fill="#FFFFFF"/></svg>')
        self.assertEqual(self.m._plate_sheet(white), (None, None))  # case-insensitive
        self.assertEqual(self.m._plate_sheet("<svg viewBox='0 0 1 1'/>"), (None, None))

    def test_dark_package_build_pins_sheet_and_keeps_derivation_on(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG)
            html = self.m.build_html(d)
            self.assertEqual(_data(html)[0]["sheet"], "#0C0A06")
            self.assertIsNotNone(_data(html)[0]["sheetLine"])
            self.assertEqual(_sheet_derive(html), "true")

    def test_white_fixture_keeps_default_sheet(self):
        # existing light galleries are visually unchanged: no per-view sheet,
        # default warm sheet-line retained in the :root blocks
        html = self.m.build_html(FIXTURE)
        self.assertTrue(all(v["sheet"] is None for v in _data(html)))
        self.assertIn("--sheet:#ffffff;", _root_css(html))
        self.assertIn("--sheet-line:#e7e3d8;", _root_css(html))


class AuthorThemeTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def test_no_theme_file_is_builtin_palette(self):
        with tempfile.TemporaryDirectory() as d:
            light, dark, pinned = self.m._resolve_theme(d)
            self.assertEqual(light["paper"], "#f1f0ea")
            self.assertEqual(dark["paper"], "#131419")
            self.assertFalse(pinned)

    def test_shared_override_applies_to_both_themes(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"theme": {"accent": "#e8a33d"}})
            light, dark, _ = self.m._resolve_theme(d)
            self.assertEqual(light["accent"], "#e8a33d")
            self.assertEqual(dark["accent"], "#e8a33d")

    def test_per_theme_override_beats_shared_and_default(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"theme": {
                "paper": "#cccccc", "dark": {"paper": "#0C0A06"}}})
            light, dark, _ = self.m._resolve_theme(d)
            self.assertEqual(light["paper"], "#cccccc")   # shared
            self.assertEqual(dark["paper"], "#0C0A06")    # per-theme wins

    def test_pinning_sheet_disables_derivation(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"theme": {"sheet": "#0C0A06"}})
            self.assertTrue(self.m._resolve_theme(d)[2])
            self.assertEqual(_sheet_derive(self.m.build_html(d)), "false")

    def test_pinning_sheet_line_also_disables_derivation(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"theme": {"dark": {"sheet-line": "#333"}}})
            self.assertTrue(self.m._resolve_theme(d)[2])

    def test_shared_override_lands_in_all_three_rule_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"theme": {"accent": "#e8a33d"}})
            css = _root_css(self.m.build_html(d))
            self.assertEqual(css.count("--accent:#e8a33d;"), 3)

    def test_unknown_token_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"theme": {"shet": "#000"}})
            with self.assertRaises(self.m.GalleryThemeError):
                self.m.build_html(d)
            self.assertEqual(self.m.main([d]), 2)  # input error

    def test_non_string_value_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"theme": {"accent": 123}})
            with self.assertRaises(self.m.GalleryThemeError):
                self.m.build_html(d)

    def test_unexpected_top_level_key_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"tehme": {"accent": "#000000"}})
            with self.assertRaises(self.m.GalleryThemeError):
                self.m.build_html(d)

    def test_non_dict_theme_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"theme": ["accent"]})
            with self.assertRaises(self.m.GalleryThemeError):
                self.m.build_html(d)

    def test_build_with_theme_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"theme": {"accent": "#e8a33d",
                                                   "dark": {"paper": "#0C0A06"}}})
            self.assertEqual(self.m.main([d]), 0)
            first = open(os.path.join(d, "gallery.html"), encoding="utf-8").read()
            self.assertEqual(self.m.main(["--check", d]), 0)  # fresh
            self.assertEqual(self.m.main([d]), 0)
            self.assertEqual(open(os.path.join(d, "gallery.html"), encoding="utf-8").read(),
                             first)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def _copy_fixture(self, dst):
        shutil.copytree(FIXTURE, dst)
        return dst

    def test_help_is_zero(self):
        self.assertEqual(self.m.main(["--help"]), 0)

    def test_usage_error_is_two(self):
        self.assertEqual(self.m.main([]), 2)
        self.assertEqual(self.m.main(["a", "b"]), 2)

    def test_build_writes_gallery_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            pkg = self._copy_fixture(os.path.join(d, "pkg"))
            self.assertEqual(self.m.main([pkg]), 0)
            out = os.path.join(pkg, "gallery.html")
            self.assertTrue(os.path.exists(out))
            first = open(out, encoding="utf-8").read()
            self.assertEqual(self.m.main([pkg]), 0)  # rerun
            self.assertEqual(open(out, encoding="utf-8").read(), first)  # idempotent

    def test_check_fresh_then_stale(self):
        with tempfile.TemporaryDirectory() as d:
            pkg = self._copy_fixture(os.path.join(d, "pkg"))
            self.m.main([pkg])
            self.assertEqual(self.m.main(["--check", pkg]), 0)  # fresh
            # mutate a source; the committed gallery is now stale
            svg = os.path.join(pkg, "generated", "svg", "app-cooperation.svg")
            open(svg, "a", encoding="utf-8").write("<!-- changed -->")
            self.assertEqual(self.m.main(["--check", pkg]), 1)  # stale

    def test_check_missing_gallery_is_stale(self):
        with tempfile.TemporaryDirectory() as d:
            pkg = self._copy_fixture(os.path.join(d, "pkg"))
            self.assertEqual(self.m.main(["--check", pkg]), 1)

    def test_incomplete_sources_is_three(self):
        with tempfile.TemporaryDirectory() as d:
            pkg = self._copy_fixture(os.path.join(d, "pkg"))
            os.remove(os.path.join(pkg, "generated", "svg", "domain-class.svg"))
            self.assertEqual(self.m.main([pkg]), 3)


if __name__ == "__main__":
    unittest.main()
