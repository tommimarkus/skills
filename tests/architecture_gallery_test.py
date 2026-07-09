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


if __name__ == "__main__":
    unittest.main()
