import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "souroldgeezer-audit/skills/ip-hygiene/references/scripts/ip-prefilter.sh"


def run(*args, stdin=None):
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        input=stdin, capture_output=True, text=True, cwd=REPO,
    )


class IpPrefilterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _touch(self, rel, body=""):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
        return p

    def test_help_exits_zero(self):
        r = run("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage", r.stdout.lower())

    def test_plain_markdown_is_clean(self):
        p = self._touch("docs/note.md", "# synthetic original text\n")
        r = run(str(p))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "")

    def test_binary_asset_flagged(self):
        p = self._touch("assets/logo.png", "")
        r = run(str(p))
        self.assertEqual(r.returncode, 1)
        self.assertIn("asset-binary", r.stdout)

    def test_vendored_without_license_flagged(self):
        p = self._touch("vendor/lib/index.js", "// synthetic\n")
        r = run(str(p))
        self.assertEqual(r.returncode, 1)
        self.assertIn("vendored-no-license", r.stdout)

    def test_vendored_with_license_not_flagged(self):
        self._touch("vendor/ok/LICENSE", "MIT synthetic\n")
        p = self._touch("vendor/ok/index.js", "// synthetic\n")
        r = run(str(p))
        self.assertNotIn("vendored-no-license", r.stdout)

    def test_schema_spec_flagged(self):
        p = self._touch("api/thing.schema.json", "{}\n")
        r = run(str(p))
        self.assertEqual(r.returncode, 1)
        self.assertIn("schema-spec", r.stdout)

    def test_json_format_parses(self):
        p = self._touch("assets/logo.png", "")
        r = run("--format", "json", str(p))
        data = json.loads(r.stdout)
        self.assertTrue(any(h["category"] == "asset-binary" for h in data))

    def test_stdin_paths(self):
        p = self._touch("assets/icon.svg", "<svg></svg>")
        r = run(stdin=f"{p}\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("asset-binary", r.stdout)


if __name__ == "__main__":
    unittest.main()
