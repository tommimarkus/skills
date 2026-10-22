# lean-audit:dup-intentional — explicit secret-shape and diff fixtures are independent calibration cases; their repeated assertion shell is test boilerplate, not shared production logic.
import unittest

from tests.surface_test_lib import REPO_ROOT, load_script_module

MODULE = REPO_ROOT / "scripts" / "lessons_secret_scan.py"


def load_scanner():
    return load_script_module("lessons_secret_scan", MODULE)


class ScanTextTest(unittest.TestCase):
    def test_detects_known_token_shapes(self):
        scan = load_scanner()
        self.assertIn("github-token", scan.scan_text("token ghp_" + "A" * 36))
        self.assertIn("openai-key", scan.scan_text("key sk-" + "a" * 24))
        self.assertIn("aws-access-key-id", scan.scan_text("AKIA" + "1234567890ABCDEF"))
        self.assertIn("private-key-block", scan.scan_text("-----BEGIN RSA PRIVATE KEY-----"))
        self.assertIn("secret-assignment", scan.scan_text('password = "hunter2hunter2hunter2"'))

    def test_every_pattern_at_and_below_its_length_boundary(self):
        scan = load_scanner()
        seg = "a" * 8
        rows = [
            # (label, at-threshold positive, just-below-threshold negative)
            ("github-token", "ghp_" + "A" * 30, "ghp_" + "A" * 29),
            ("github-token", "gho_" + "A" * 30, "gho_" + "A" * 29),
            ("github-token", "ghs_" + "A" * 30, "ghs_" + "A" * 29),
            ("github-token", "ghr_" + "A" * 30, "ghr_" + "A" * 29),
            ("github-token", "ghu_" + "A" * 30, "ghu_" + "A" * 29),
            ("openai-key", "sk-" + "a" * 20, "sk-" + "a" * 19),
            ("aws-access-key-id", "AKIA" + "A" * 16, "AKIA" + "A" * 15),
            ("slack-token", "xoxb-" + "1" * 10, "xoxb-" + "1" * 9),
            ("google-api-key", "AIza" + "a" * 35, "AIza" + "a" * 34),
            ("jwt", "eyJ" + seg + "." + seg + "." + seg,
             "eyJ" + seg + "." + seg + "." + seg[:-1]),
            ("secret-assignment", "password = " + "a" * 16, "password = " + "a" * 15),
            ("private-key-block", "-----BEGIN PRIVATE KEY-----",
             "-----BEGIN PUBLIC KEY-----"),
        ]
        self.assertEqual({r[0] for r in rows}, {label for label, _ in scan.SECRET_PATTERNS})
        for label, positive, negative in rows:
            with self.subTest(label=label, sample=positive[:6]):
                self.assertIn(label, scan.scan_text(positive))
                self.assertNotIn(label, scan.scan_text(negative))

    def test_clean_prose_is_clean(self):
        scan = load_scanner()
        self.assertEqual(scan.scan_text("report rule: manifest versions must match"), [])

    def test_git_sha_is_not_flagged(self):
        scan = load_scanner()
        self.assertEqual(scan.scan_text("see commit 984874a and f02e2739417b0bbb"), [])


class ScanDiffTest(unittest.TestCase):
    def test_only_added_lines_are_scanned(self):
        scan = load_scanner()
        diff = (
            "+++ b/x\n"
            "@@ -1 +1 @@\n"
            "-password = \"oldsecretoldsecret123\"\n"
            "+report rule: keep it general\n"
        )
        self.assertEqual(scan.scan_diff(diff), [])

    def test_added_secret_is_flagged(self):
        scan = load_scanner()
        diff = "+++ b/x\n@@ -0,0 +1 @@\n+api_key = \"abcd1234abcd1234abcd\"\n"
        self.assertIn("secret-assignment", scan.scan_diff(diff))

    def test_added_line_beginning_with_plus_plus_is_scanned(self):
        scan = load_scanner()
        diff = (
            "diff --git a/x b/x\n"
            "--- a/x\n"
            "+++ b/x\n"
            "@@ -0,0 +1 @@\n"
            "+++api_key = \"abcd1234abcd1234abcd\"\n"
        )
        self.assertIn("secret-assignment", scan.scan_diff(diff))

    def test_file_headers_outside_a_hunk_are_skipped(self):
        scan = load_scanner()
        header_secret = "api_key = abcd1234abcd1234abcd"
        diff = (
            "diff --git a/x b/x\n"
            "--- a/x\n"
            "+++ b/" + header_secret + "\n"
            "@@ -0,0 +1 @@\n"
            "+clean line\n"
            "diff --git a/y b/y\n"
            "+++ b/" + header_secret + "\n"
        )
        self.assertEqual(scan.scan_diff(diff), [])


if __name__ == "__main__":
    unittest.main()
