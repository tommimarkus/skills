# lean-audit:dup-intentional — identifier-rich parallel test bodies (CLAUDE.md § Repo-local Python® tooling)
import base64
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

    def test_density_is_an_edge_count_hint(self):
        self.assertEqual(self.m.density_of(49), "below-threshold")
        self.assertEqual(self.m.density_of(50), "dense")


class ProfileResolverTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    @staticmethod
    def _write_model(d, name, profile):
        with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
            _json.dump({"model_schema_version": "model.schema.v1",
                        "plugins": {"generic-graph": {"semantic_profile": profile}}}, fh)

    def test_multi_model_reads_each_models_own_semantic_profile(self):
        """package.schema.v1 has no per-model profile field: the notation comes from the
        model file itself, which is the authority the retired v2 registry duplicated."""
        with tempfile.TemporaryDirectory() as d:
            self._write_model(d, "model.json", "archimate")
            self._write_model(d, "model-uml.json", "uml")
            pkg = {
                "package_schema_version": "package.schema.v1",
                "models": [{"id": "arch", "source": "model.json"},
                           {"id": "uml", "source": "model-uml.json"}],
                "views": [{"id": "a", "model": "arch"}, {"id": "b", "model": "uml"}],
            }
            prof = self.m.profile_resolver(pkg, d)
            self.assertEqual(prof(pkg["views"][0]), "archimate")
            self.assertEqual(prof(pkg["views"][1]), "uml")

    def test_single_model_view_may_omit_its_model_binding(self):
        """views[].model is optional in package.schema.v1 when the package declares one
        model, so an unbound view must still resolve to that model's notation."""
        with tempfile.TemporaryDirectory() as d:
            self._write_model(d, "model.json", "uml")
            pkg = {"package_schema_version": "package.schema.v1",
                   "models": [{"id": "only", "source": "model.json"}],
                   "views": [{"id": "main"}]}
            prof = self.m.profile_resolver(pkg, d)
            self.assertEqual(prof(pkg["views"][0]), "uml")

    def test_defaults_to_archimate_when_unresolvable(self):
        pkg = {"package_schema_version": "package.schema.v1",
               "models": [{"id": "m", "source": "missing.json"}],
               "views": [{"id": "x", "model": "m"}]}
        prof = self.m.profile_resolver(pkg, "/nonexistent")
        self.assertEqual(prof(pkg["views"][0]), "archimate")

    def test_non_dict_model_defaults_to_archimate(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "model.json"), "w", encoding="utf-8") as fh:
                _json.dump([], fh)  # valid JSON, not an object
            pkg = {"package_schema_version": "package.schema.v1",
                   "models": [{"id": "m", "source": "model.json"}],
                   "views": [{"id": "x", "model": "m"}]}
            prof = self.m.profile_resolver(pkg, d)
            self.assertEqual(prof(pkg["views"][0]), "archimate")


FIXTURE = os.path.join(
    REPO, "souroldgeezer-architecture", "skills", "architecture-design",
    "references", "fixtures", "dediren", "rendered")


class BuildHtmlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # immutable build result shared by the read-only assertions below
        cls.m = _load()
        cls.html = cls.m.build_html(FIXTURE)

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

    def test_svgs_are_inert_base64_images_with_accessible_text(self):
        views = {v["id"]: v for v in _data(self.html)}
        self.assertNotIn('<template class="plate"', self.html)
        self.assertNotIn("data-dediren-node-id", self.html)
        for vid, view in views.items():
            prefix = "data:image/svg+xml;base64,"
            self.assertTrue(view["image"].startswith(prefix))
            decoded = base64.b64decode(view["image"][len(prefix):])
            source = os.path.join(FIXTURE, "generated", "svg", vid + ".svg")
            with open(source, "rb") as fh:
                original = fh.read()
            expected = re.sub(
                rb'<text\b(?=[^>]*\bdata-arch-a11y="visible-title")[^>]*>'
                rb'.*?</text\s*>', b'', original, flags=re.S)
            self.assertEqual(decoded, expected)
            self.assertIn(b'xmlns="http://www.w3.org/2000/svg"', decoded)
            self.assertTrue(view["alt"])
            self.assertGreater(view["width"], 0)
            self.assertGreater(view["height"], 0)

    def test_package_text_is_context_safe_and_ids_never_form_selectors(self):
        with tempfile.TemporaryDirectory(prefix="gallery-<script>") as d:
            _mk_pkg(d, _DARK_SVG)
            package_path = os.path.join(d, "package.json")
            with open(package_path, encoding="utf-8") as fh:
                pkg = _json.load(fh)
            marker = '</script><script id="owned">globalThis.owned=1</script>'
            pkg["presentation"] = {"lang": 'en\" onload="owned()',
                                       "dir": 'rtl\" data-owned="yes'}
            pkg["views"][0]["id"] = 'x\"] button,script[data-x="'
            pkg["views"][0]["presentation"] = {
                "title": marker, "question": marker,
                "diagram_kind": marker,
            }
            with open(package_path, "w", encoding="utf-8") as fh:
                _json.dump(pkg, fh)
            os.rename(os.path.join(d, "generated", "svg", "v.svg"),
                      os.path.join(d, "generated", "svg", 'x\"] button,script[data-x=".svg'))
            os.rename(os.path.join(d, "generated", "render-metadata", "v.json"),
                      os.path.join(d, "generated", "render-metadata",
                                   'x\"] button,script[data-x=".json'))
            pkg["views"][0]["outputs"] = {
                "diagram": 'generated/svg/x\"] button,script[data-x=".svg',
                "render_metadata":
                    'generated/render-metadata/x\"] button,script[data-x=".json',
            }
            with open(package_path, "w", encoding="utf-8") as fh:
                _json.dump(pkg, fh)

            rendered = self.m.build_html(d)
            self.assertEqual(rendered.count("<script>"), 1)
            self.assertNotIn('<script id="owned">', rendered)
            self.assertIn(r"\u003c/script\u003e", rendered)
            self.assertNotIn('data-id="x', rendered)
            self.assertIn("encodeURIComponent(id)", rendered)

    def test_svg_external_reference_remains_only_in_inert_image_bytes(self):
        svg = (_DARK_SVG.replace(
            "</svg>", '<image href="https://attacker.invalid/pixel"/></svg>'))
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, svg)
            rendered = self.m.build_html(d)
            self.assertNotIn("https://attacker.invalid", rendered)
            image = _data(rendered)[0]["image"].split(",", 1)[1]
            self.assertIn(b"https://attacker.invalid", base64.b64decode(image))

    def test_sections_derived_from_real_profiles(self):
        # ArchiMate view -> A/ArchiMate views ; UML class -> T ; UML sequence -> S
        views = {v["id"]: v for v in _data(self.html)}
        self.assertEqual(
            {vid: (v["group"]["key"], v["group"]["title"], v["code"])
             for vid, v in views.items()},
            {"app-cooperation": ("arch", "ArchiMate views", "A1"),
             "domain-class": ("uml-data", "Structure & data", "T1"),
             "order-sequence": ("uml-seq", "Sequences", "S1")})

    def test_english_chrome_and_lang(self):
        self.assertIn('lang="en"', self.html)
        # chrome strings the build derives are English: group titles and
        # density labels come from the DATA payload, not localized copy
        data = _data(self.html)
        self.assertEqual({v["group"]["title"] for v in data},
                         {"ArchiMate views", "Structure & data", "Sequences"})
        self.assertEqual({v["density"] for v in data}, {"below-threshold"})
        for finnish in ("tiheä", "asettelu", "Konteksti", "solmua"):
            self.assertNotIn(finnish, self.html)

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
            with open(os.path.join(d, "package.json"), "w", encoding="utf-8") as fh:
                _json.dump({"package_schema_version": "package.schema.v1",
                            "models": [], "views": [
                                {"id": "x", "model": "m",
                                 "render_policy": "render-policy.json",
                                 "presentation": {"title": "X",
                                                  "diagram_kind": "UML Class"},
                                 "outputs": {
                                     "diagram": "generated/svg/x.svg",
                                     "render_metadata":
                                         "generated/render-metadata/x.json"}}]}, fh)
            with self.assertRaises(self.m.SourceMissing):
                self.m.build_html(d)

    def test_empty_views_package_builds_with_guarded_bootstrap(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "package.json"), "w", encoding="utf-8") as fh:
                _json.dump({"package_schema_version": "package.schema.v1",
                            "models": [], "views": []}, fh)
            html = self.m.build_html(d)          # must not raise
            self.assertEqual(_data(html), [])
            self.assertIn("if (DATA.length)", html)

    def test_untagged_package_takes_en_ltr_and_the_directory_feature(self):
        """A package with no presentation object takes en/ltr — matching the runtime,
        which defaults neither and leaves an untagged SVG root untouched — and names
        the feature from its own directory per docs/architecture/<feature>.dediren/."""
        with tempfile.TemporaryDirectory() as d:
            pkg_dir = os.path.join(d, "orders.dediren")
            os.makedirs(pkg_dir)
            with open(os.path.join(pkg_dir, "package.json"), "w", encoding="utf-8") as fh:
                _json.dump({"package_schema_version": "package.schema.v1",
                            "models": [], "views": []}, fh)
            html = self.m.build_html(pkg_dir)
            self.assertIn('<html lang="en" dir="ltr">', html)
            # The .dediren suffix is package plumbing, not part of the feature name —
            # asserted where the feature is *named* (page title, masthead eyebrow),
            # not repo-wide: the rail footer legitimately prints the full package path.
            self.assertIn("<title>orders · architecture gallery</title>", html)
            self.assertIn('<div class="mast-eyebrow">orders</div>', html)

    def test_retired_sidecar_still_declaring_lang_or_dir_is_refused(self):
        """The migration hazard: a package authored right-to-left before lang/dir went
        native would render ltr with nothing said if the retired sidecar were merely
        ignored. Refuse it instead, and name the move in the message."""
        with tempfile.TemporaryDirectory() as d:
            pkg_dir = os.path.join(d, "legacy.dediren")
            os.makedirs(pkg_dir)
            with open(os.path.join(pkg_dir, "package.json"), "w", encoding="utf-8") as fh:
                _json.dump({"package_schema_version": "package.schema.v1",
                            "models": [], "views": []}, fh)
            with open(os.path.join(pkg_dir, "project.json"), "w", encoding="utf-8") as fh:
                _json.dump({"schema": "souroldgeezer.architecture.dediren"
                                      ".presentation.v1", "feature": "legacy",
                            "lang": "ar-EG", "dir": "rtl"}, fh)
            with self.assertRaises(ValueError) as caught:
                self.m.build_html(pkg_dir)
            self.assertIn("package.json", str(caught.exception))

            # A leftover carrying no live key is harmless — the directory names the
            # feature — so it must not block a build.
            with open(os.path.join(pkg_dir, "project.json"), "w", encoding="utf-8") as fh:
                _json.dump({"schema": "souroldgeezer.architecture.dediren"
                                      ".presentation.v1", "feature": "legacy"}, fh)
            self.assertIn("<title>legacy · architecture gallery</title>",
                          self.m.build_html(pkg_dir))

    def test_package_presentation_drives_html_lang_and_dir(self):
        """lang/dir come from the package's own presentation — the same declaration
        dediren folds into every view's render policy — so the page and the SVGs it
        inlines can never disagree."""
        with tempfile.TemporaryDirectory() as d:
            pkg_dir = os.path.join(d, "tilaukset.dediren")
            os.makedirs(pkg_dir)
            with open(os.path.join(pkg_dir, "package.json"), "w", encoding="utf-8") as fh:
                _json.dump({"package_schema_version": "package.schema.v1",
                            "presentation": {"lang": "ar-EG", "dir": "rtl"},
                            "models": [], "views": []}, fh)
            html = self.m.build_html(pkg_dir)
            self.assertIn('<html lang="ar-EG" dir="rtl">', html)


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


def _mk_pkg(d, svg, theme=None, edge_count=0):
    """Write a one-view package (package.json, svg, render-metadata) into d. The
    model file carries the notation, so it is written too."""
    os.makedirs(os.path.join(d, "generated", "svg"), exist_ok=True)
    os.makedirs(os.path.join(d, "generated", "render-metadata"), exist_ok=True)
    pkg = {"package_schema_version": "package.schema.v1",
           "models": [{"id": "u", "source": "m.json"}],
           "views": [{"id": "v", "model": "u",
                      "render_policy": "render-policy.json",
                      "presentation": {"title": "Dark view",
                                       "diagram_kind": "UML Class"},
                      "outputs": {
                          "diagram": "generated/svg/v.svg",
                          "render_metadata": "generated/render-metadata/v.json"}}]}
    with open(os.path.join(d, "package.json"), "w", encoding="utf-8") as fh:
        _json.dump(pkg, fh)
    with open(os.path.join(d, "m.json"), "w", encoding="utf-8") as fh:
        _json.dump({"model_schema_version": "model.schema.v1",
                    "plugins": {"generic-graph": {"semantic_profile": "uml"}}}, fh)
    with open(os.path.join(d, "generated", "svg", "v.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg)
    with open(os.path.join(d, "generated", "render-metadata", "v.json"), "w",
              encoding="utf-8") as fh:
        nodes = ({"n": 1} if edge_count == 0 else
                 {"n%d" % i: 1 for i in range(edge_count * 2)})
        _json.dump({"nodes": nodes,
                    "edges": {"e%d" % i: {} for i in range(edge_count)}}, fh)
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

    def test_density_hint_does_not_claim_layout_quality(self):
        occluded = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">'
                    '<rect data-dediren-node-shape="uml_class" '
                    'data-dediren-node-id="left" x="5" y="10" width="40" height="25"/>'
                    '<rect data-dediren-node-shape="uml_class" '
                    'data-dediren-node-id="right" x="70" y="10" width="25" height="25"/>'
                    '<path data-dediren="edge" data-dediren-edge-id="e0" '
                    'd="M45 22 L70 22" fill="none" stroke="#333"/>'
                    '<text data-dediren-edge-label-for="e0" x="8" y="25">'
                    'occluded label</text></svg>')
        readable_edges = []
        readable_nodes = []
        for i in range(50):
            y = 20 + i * 36
            readable_nodes.extend((
                '<rect data-dediren-node-shape="uml_class" data-dediren-node-id="l%d" '
                'x="10" y="%d" width="70" height="24"/>' % (i, y),
                '<rect data-dediren-node-shape="uml_class" data-dediren-node-id="r%d" '
                'x="920" y="%d" width="70" height="24"/>' % (i, y),
            ))
            readable_edges.extend((
                '<path data-dediren="edge" data-dediren-edge-id="e%d" '
                'd="M80 %d L450 %d M550 %d L920 %d" '
                'fill="none" stroke="#333"/>' %
                (i, y + 12, y + 12, y + 12, y + 12),
                '<text data-dediren-edge-label-for="e%d" x="480" y="%d">'
                'edge %d label</text>' % (i, y + 8, i),
            ))
        readable = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1820">'
                    + ''.join(readable_nodes + readable_edges) + '</svg>')
        with tempfile.TemporaryDirectory() as d:
            sparse_pkg = os.path.join(d, "sparse")
            dense_pkg = os.path.join(d, "dense")
            os.makedirs(sparse_pkg)
            os.makedirs(dense_pkg)
            _mk_pkg(sparse_pkg, occluded, edge_count=1)
            _mk_pkg(dense_pkg, readable, edge_count=50)

            sparse_html = self.m.build_html(sparse_pkg)
            dense_html = self.m.build_html(dense_pkg)
            sparse = _data(sparse_html)[0]
            dense = _data(dense_html)[0]

        self.assertEqual(sparse["density"], "below-threshold")
        self.assertEqual(dense["density"], "dense")
        self.assertNotIn("status", sparse)
        self.assertNotIn("status", dense)
        sparse_svg = base64.b64decode(_data(sparse_html)[0]["image"].split(",", 1)[1])
        dense_svg = base64.b64decode(_data(dense_html)[0]["image"].split(",", 1)[1])
        self.assertIn(b'data-dediren-edge-label-for="e0"', sparse_svg)
        self.assertIn(b'data-dediren-edge-id="e49"', dense_svg)
        # the rendered hint is static template JS: anchor on the two
        # assignment statements rather than pinning the whole HTML
        density = re.search(r"q\('#p-density'\)\.textContent\s*=\s*([^;\n]+);", sparse_html)
        note = re.search(r"q\('#p-note'\)\.textContent\s*=\s*([^;\n]+;?[^\n]*)", sparse_html)
        self.assertIsNotNone(density, "#p-density assignment not found")
        self.assertIsNotNone(note, "#p-note assignment not found")
        self.assertIn("'dense by edge count'", density.group(1))
        self.assertIn("'below density threshold'", density.group(1))
        self.assertIn("edge-count heuristic", note.group(1))
        self.assertIn("assess layout quality from build diagnostics and the SVG", note.group(1))
        for stmt in (density.group(0), note.group(0)):
            self.assertNotIn("layout ok", stmt.casefold())
            self.assertNotIn("konteksti", stmt.casefold())
        # the payload carries a density bucket and counts only; it never
        # asserts layout quality for either view
        for view in (sparse, dense):
            self.assertEqual(
                set(view),
                {"id", "code", "group", "title", "q", "kind", "nodes", "edges",
                 "density", "sheet", "sheetLine", "image", "alt", "width",
                 "height"})
            self.assertNotIn("layout", _json.dumps(view).casefold())


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

    def test_colour_token_rejects_non_colour_and_css_breakout(self):
        for value in ("10px", "red;}@import url(https://attacker.invalid/x){"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as d:
                _mk_pkg(d, _DARK_SVG, theme={"theme": {"accent": value}})
                with self.assertRaises(self.m.GalleryThemeError):
                    self.m.build_html(d)

    def test_shadow_token_rejects_colour_value_and_accepts_safe_shadow(self):
        with tempfile.TemporaryDirectory() as d:
            _mk_pkg(d, _DARK_SVG, theme={"theme": {"shadow": "#fff"}})
            with self.assertRaises(self.m.GalleryThemeError):
                self.m.build_html(d)
        with tempfile.TemporaryDirectory() as d:
            value = "0 1px 0 rgba(0,0,0,.4), 0 20px 46px -26px #000"
            _mk_pkg(d, _DARK_SVG, theme={"theme": {"shadow": value}})
            self.assertEqual(self.m._resolve_theme(d)[0]["shadow"], value)

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

    def test_external_model_and_output_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            pkg = self._copy_fixture(os.path.join(d, "pkg"))
            outside = os.path.join(d, "outside.json")
            with open(outside, "w", encoding="utf-8") as fh:
                fh.write('{"private":"canary"}')
            package_path = os.path.join(pkg, "package.json")
            with open(package_path, encoding="utf-8") as fh:
                body = _json.load(fh)
            cases = (("model", "../outside.json"),
                     ("diagram", outside),
                     ("render_metadata", "../outside.json"))
            for kind, value in cases:
                with self.subTest(kind=kind):
                    changed = _json.loads(_json.dumps(body))
                    if kind == "model":
                        changed["models"][0]["source"] = value
                    else:
                        changed["views"][0]["outputs"][kind] = value
                    with open(package_path, "w", encoding="utf-8") as fh:
                        _json.dump(changed, fh)
                    self.assertEqual(self.m.main([pkg]), 2)
                    self.assertFalse(os.path.exists(os.path.join(pkg, "gallery.html")))

    def test_escaping_input_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            pkg = self._copy_fixture(os.path.join(d, "pkg"))
            outside = os.path.join(d, "outside.svg")
            with open(outside, "w", encoding="utf-8") as fh:
                fh.write(_DARK_SVG)
            link = os.path.join(pkg, "generated", "svg", "escape.svg")
            os.symlink(outside, link)
            package_path = os.path.join(pkg, "package.json")
            with open(package_path, encoding="utf-8") as fh:
                body = _json.load(fh)
            body["views"][0]["outputs"]["diagram"] = "generated/svg/escape.svg"
            with open(package_path, "w", encoding="utf-8") as fh:
                _json.dump(body, fh)
            self.assertEqual(self.m.main([pkg]), 2)

    def test_gallery_output_symlink_is_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            pkg = self._copy_fixture(os.path.join(d, "pkg"))
            canary = os.path.join(d, "outside.html")
            with open(canary, "w", encoding="utf-8") as fh:
                fh.write("do not overwrite")
            os.symlink(canary, os.path.join(pkg, "gallery.html"))
            self.assertEqual(self.m.main([pkg]), 2)
            with open(canary, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "do not overwrite")


if __name__ == "__main__":
    unittest.main()
