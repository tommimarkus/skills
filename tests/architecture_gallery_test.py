import importlib.util
import json as _json
import os
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


FIXTURE = os.path.join(
    REPO, "souroldgeezer-architecture", "skills", "architecture-design",
    "references", "fixtures", "dediren", "rendered")


class BuildHtmlTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()
        self.html = self.m.build_html(FIXTURE)

    def test_self_contained_no_external_refs(self):
        # no external stylesheet/script/font/image hosts
        for needle in ("http://", "https://", "src=\"//", "@import"):
            self.assertNotIn(needle, self.html)

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
        self.assertIn('"nodes": 2', self.html)
        self.assertIn('"edges": 1', self.html)

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


if __name__ == "__main__":
    unittest.main()
