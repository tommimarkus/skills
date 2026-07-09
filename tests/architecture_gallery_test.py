import importlib.util
import os
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


if __name__ == "__main__":
    unittest.main()
