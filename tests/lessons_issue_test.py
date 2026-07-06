import json
import subprocess
import sys
import unittest

from tests.surface_test_lib import REPO_ROOT, load_script_module

MODULE = REPO_ROOT / "scripts" / "lessons_issue.py"


def _mod():
    return load_script_module("lessons_issue", MODULE)


class FingerprintTest(unittest.TestCase):
    def test_stable_for_same_content(self):
        m = _mod()
        a = m.fingerprint(substrate="policy", proposed_rule="always X")
        b = m.fingerprint(substrate="policy", proposed_rule="always X")
        self.assertEqual(a, b)
        self.assertEqual(len(a), 16)

    def test_changes_with_rule_and_substrate(self):
        m = _mod()
        base = m.fingerprint(substrate="policy", proposed_rule="always X")
        self.assertNotEqual(base, m.fingerprint(substrate="policy", proposed_rule="always Y"))
        self.assertNotEqual(base, m.fingerprint(substrate="prose", proposed_rule="always X"))


class LabelsTest(unittest.TestCase):
    def test_marker_plus_substrate(self):
        m = _mod()
        self.assertEqual(m.labels(substrate="deterministic"),
                         ["lesson-candidate", "lesson:deterministic"])


class RenderBodyTest(unittest.TestCase):
    def _body(self, substrate):
        m = _mod()
        return m.render_body(trigger="self-correction",
                             proposed_rule="always guard the closure", substrate=substrate)

    def test_contains_fields_and_fingerprint_marker(self):
        m = _mod()
        body = self._body("policy")
        self.assertIn("**Trigger:** self-correction", body)
        self.assertIn("**Proposed rule:** always guard the closure", body)
        self.assertIn("**Substrate:** policy", body)
        self.assertIn("**Layer:** 2", body)
        fp = m.fingerprint(substrate="policy", proposed_rule="always guard the closure")
        self.assertIn(f"<!-- lesson-fp:{fp} -->", body)

    def test_common_definition_of_done_present(self):
        body = self._body("prose")
        self.assertIn("## Definition of Done", body)
        self.assertIn("lessons_secret_scan.py --diff", body)
        self.assertIn("Graduate on **`main`**", body)
        self.assertIn("as completed", body)
        self.assertIn("as not planned", body)

    def test_deterministic_dod_names_fixture_discipline(self):
        body = self._body("deterministic")
        self.assertIn("SAC-T#####", body)
        self.assertIn("only if the report engine already detects this smell", body)
        self.assertIn("never fake a passing test", body)
        self.assertIn("unittest discover -s tests -p '*_test.py'", body)

    def test_prose_dod_marks_last_resort(self):
        self.assertIn("last resort", self._body("prose"))

    def test_policy_dod_names_terse_home(self):
        self.assertIn("terse policy line", self._body("policy"))


class BuildTest(unittest.TestCase):
    def test_returns_all_keys(self):
        m = _mod()
        out = m.build(trigger="self-correction", summary="the delta",
                      proposed_rule="always X", substrate="policy")
        self.assertEqual(set(out), {"title", "labels", "fingerprint", "body"})
        self.assertEqual(out["title"], "the delta")
        self.assertEqual(out["labels"], ["lesson-candidate", "lesson:policy"])

    def test_title_falls_back_to_rule_when_summary_blank(self):
        m = _mod()
        out = m.build(trigger="t", summary="", proposed_rule="always X", substrate="prose")
        self.assertEqual(out["title"], "always X")


class ValidateTest(unittest.TestCase):
    def test_rejects_bad_substrate(self):
        m = _mod()
        with self.assertRaises(m.LessonIssueError):
            m.validate(trigger="t", proposed_rule="r", substrate="nope")

    def test_rejects_empty_trigger(self):
        m = _mod()
        with self.assertRaises(m.LessonIssueError):
            m.validate(trigger="   ", proposed_rule="r", substrate="policy")


class CliTest(unittest.TestCase):
    def test_build_prints_json_line(self):
        out = subprocess.run(
            [sys.executable, str(MODULE), "build", "--trigger", "self-correction",
             "--summary", "the delta", "--proposed-rule", "always X",
             "--substrate", "policy"],
            capture_output=True, text=True, check=True)
        payload = json.loads(out.stdout)
        self.assertEqual(payload["labels"], ["lesson-candidate", "lesson:policy"])
        self.assertIn("<!-- lesson-fp:", payload["body"])


if __name__ == "__main__":
    unittest.main()
