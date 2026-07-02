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
            "-password = \"oldsecretoldsecret123\"\n"
            "+report rule: keep it general\n"
        )
        self.assertEqual(scan.scan_diff(diff), [])

    def test_added_secret_is_flagged(self):
        scan = load_scanner()
        diff = "+++ b/x\n+api_key = \"abcd1234abcd1234abcd\"\n"
        self.assertIn("secret-assignment", scan.scan_diff(diff))


if __name__ == "__main__":
    unittest.main()
