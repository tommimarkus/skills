# lean-audit:dup-intentional — per-flag CLI behavior cases kept as named short tests; the flagged-category body is extracted to _assert_flagged
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "souroldgeezer-audit/skills/ip-hygiene/references/scripts/ip-prefilter.sh"


def run(*args, stdin=None):
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        input=stdin, capture_output=True, text=not isinstance(stdin, bytes), cwd=REPO,
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

    def _assert_flagged(self, rel, body, category):
        p = self._touch(rel, body)
        r = run(str(p))
        self.assertEqual(r.returncode, 1)
        self.assertIn(category, r.stdout)

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
        self._assert_flagged("assets/logo.png", "", "asset-binary")

    def test_vendored_without_license_flagged(self):
        self._assert_flagged("vendor/lib/index.js", "// synthetic\n", "vendored-no-license")

    def test_vendored_with_license_not_flagged(self):
        self._touch("vendor/ok/LICENSE", "MIT synthetic\n")
        p = self._touch("vendor/ok/index.js", "// synthetic\n")
        r = run(str(p))
        self.assertEqual(r.returncode, 1)
        self.assertIn("vendored-component", r.stdout)
        self.assertIn("LICENSE/COPYING/NOTICE present", r.stdout)

    def test_schema_spec_flagged(self):
        self._assert_flagged("api/thing.schema.json", "{}\n", "schema-spec")

    def test_source_license_or_copyright_marker_is_evidence(self):
        self._assert_flagged("src/widget.py", "# SPDX-License-Identifier: MIT\n", "source-notice")

    def test_json_format_parses(self):
        p = self._touch("assets/logo.png", "")
        r = run("--format", "json", str(p))
        data = json.loads(r.stdout)
        self.assertTrue(any(h["category"] == "asset-binary" for h in data))

    def test_stdin_paths(self):
        p = self._touch("assets/icon.svg", "<svg></svg>")
        r = run(stdin=f"{p}".encode() + b"\0")
        self.assertEqual(r.returncode, 1)
        self.assertIn(b"asset-binary", r.stdout)

    def test_nul_input_preserves_newline_in_path_as_json(self):
        p = self._touch("assets/line\nbreak.png", "")
        r = run("--format", "json", stdin=str(p).encode() + b"\0")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn(str(p), [hit["path"] for hit in json.loads(r.stdout)])

    def test_overlapping_inputs_are_stable_and_deduplicated(self):
        one = self._touch("assets/z.png", "")
        two = self._touch("assets/a.png", "")
        r = run("--format", "json", str(self.root / "assets"), str(one), str(self.root / "assets"))
        self.assertEqual(r.returncode, 1, r.stderr)
        paths = [hit["path"] for hit in json.loads(r.stdout) if hit["category"] == "asset-binary"]
        self.assertEqual(paths, sorted({str(one), str(two)}))

    def test_symlink_is_reported_without_following_it(self):
        target = self._touch("outside/logo.png", "")
        link = self.root / "assets" / "linked-logo"
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)
        r = run("--format", "json", str(link))
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertEqual(json.loads(r.stdout), [{
            "path": str(link), "category": "symlink", "reason": "symbolic link; inspect target and provenance"
        }])

    def test_repository_metadata_is_excluded(self):
        self._touch(".git/objects/blob.png", "")
        r = run(str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_missing_path_is_input_error(self):
        r = run(str(self.root / "missing"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("missing path", r.stderr)

    def test_bad_format_exits_two(self):
        r = run("--format", "bogus", "x")
        self.assertEqual(r.returncode, 2)

    def test_unknown_option_exits_two(self):
        r = run("--nope")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
