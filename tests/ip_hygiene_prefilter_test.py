# lean-audit:dup-intentional — per-flag CLI behavior cases kept as named short tests; the flagged-category body is extracted to _assert_flagged
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "souroldgeezer-audit/skills/ip-hygiene/references/scripts/ip-prefilter.sh"
# Every external command the script invokes, so a PATH without git can still run it.
SCRIPT_TOOLS = (
    "bash", "mktemp", "find", "sort", "grep", "jq", "tr", "head", "comm", "sed",
    "dirname", "rm", "cat",
)


def run(*args, stdin=None, env=None):
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        input=stdin, capture_output=True, text=not isinstance(stdin, bytes), cwd=REPO,
        env=env,
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

    def _categories(self, rel, body):
        p = self._touch(rel, body)
        r = run("--format", "json", str(p))
        self.assertIn(r.returncode, (0, 1), r.stderr)
        return sorted({hit["category"] for hit in json.loads(r.stdout)})

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

    def test_spdx_line_flagged(self):
        self._assert_flagged("src/spdx.py", "# SPDX-License-Identifier: Apache-2.0\n", "source-spdx")

    def test_authorship_tags_flagged(self):
        self._assert_flagged(
            "src/tagged.ts", "/**\n * @author A. Synthetic\n * @license MIT\n */\n", "source-authorship")

    def test_authorship_tag_not_matched_inside_a_word(self):
        self.assertEqual(self._categories("src/mail.py", "# reach us at team@licenses.invalid\n"), [])

    def test_attribution_provenance_comment_flagged(self):
        self._assert_flagged(
            "src/port.py", "# Adapted from the synthetic upstream recipe\ndef f():\n    pass\n",
            "source-attribution")

    def test_attribution_based_on_counts_only_with_a_locator(self):
        self.assertEqual(
            self._categories("src/loose.py", "# value is chosen based on the caller's options\n"), [])
        self._assert_flagged(
            "src/tight.py", "# based on https://acme.invalid/notes/9\n", "source-attribution")

    def test_attribution_docstring_provenance_flagged(self):
        self._assert_flagged(
            "src/doc.py", '"""Originally from the synthetic cookbook."""\n', "source-attribution")

    def test_attribution_code_host_url_in_comment_flagged(self):
        self._assert_flagged(
            "src/snippet.js", "// see https://stackoverflow.com/questions/1 for the trick\n",
            "source-attribution")

    def test_attribution_ignores_prose_and_non_code_host_urls(self):
        body = (
            "# derived from first principles\n"
            "x = 1  # the source: of truth lives elsewhere\n"
            "# spec at https://example.invalid/docs\n"
            "# already imported from the helper module\n"
        )
        self.assertEqual(self._categories("src/prose.py", body), [])

    def test_licence_block_flagged(self):
        # Synthetic licence wording, like every other fixture here: generic
        # boilerplate phrases the detector keys on, under an invented licence
        # name, rather than a real licence's distinctive grant text.
        body = (
            "/*\n"
            " * Fictional Cormorant Licence v1 -- All rights reserved.\n"
            ' * This component is provided "as is" under the terms above.\n'
            " */\n"
            "int main(void) { return 0; }\n"
        )
        self._assert_flagged("src/licensed.c", body, "source-licence-block")

    def test_single_licence_phrase_is_not_a_licence_block(self):
        self.assertEqual(
            self._categories("src/mention.py", "# see the vendor's Mozilla Public License page\n"), [])

    def test_licence_block_not_reported_for_vendored_file(self):
        body = (
            "// Fictional Cormorant Licence v1 -- All rights reserved.\n"
            '// This component is provided "as is" under the terms above.\n'
        )
        self.assertNotIn("source-licence-block", self._categories("vendor/dep/index.js", body))

    def test_generated_banner_flagged(self):
        self._assert_flagged(
            "src/pb.go", "// Code generated by protoc-gen-go. DO NOT EDIT.\n", "source-generated")

    def test_generated_banner_in_yaml_comment_flagged(self):
        self._assert_flagged("ci/build.yml", "# @generated\njobs: {}\n", "source-generated")

    def test_generated_phrase_outside_a_header_comment_is_not_a_banner(self):
        body = '{"boundary": "Do not edit other concerns"}\n' + "\n" * 60 + "# DO NOT EDIT\n"
        self.assertEqual(self._categories("src/fixture.py", body), [])

    def test_widened_source_extensions_are_scanned(self):
        self._assert_flagged("infra/main.tf", "# Copyright 2020 Synthetic\n", "source-notice")
        self._assert_flagged("infra/main.bicep", "// SPDX-License-Identifier: MIT\n", "source-spdx")

    def test_extensionless_build_files_are_scanned(self):
        self._assert_flagged("build/Dockerfile", "# Copyright 2020 Synthetic\nFROM scratch\n", "source-notice")
        self._assert_flagged("build/Makefile", "# SPDX-License-Identifier: MIT\nall:\n", "source-spdx")

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


class IpPrefilterBaseLaneTest(unittest.TestCase):
    """--base REF diff lane: notice loss, and degradation that never reads as clean."""

    NOTICED = "// Copyright 2020 Synthetic\n// SPDX-License-Identifier: MIT\nfunction f() {}\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel, body):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
        return p

    def _git(self, *args):
        subprocess.run(
            ["git", "-c", "user.email=t@synthetic.invalid", "-c", "user.name=t",
             "-c", "commit.gpgsign=false", *args],
            cwd=self.root, capture_output=True, text=True, check=True,
        )

    def _repo_with_committed(self, rel, body):
        self._git("init", "-q", "-b", "main", ".")
        p = self._write(rel, body)
        self._git("add", "-A")
        self._git("commit", "-qm", "base")
        return p

    def test_notice_loss_reported_when_marker_removed(self):
        p = self._repo_with_committed("src/util.js", self.NOTICED)
        p.write_text("function f() {}\n")
        r = run("--format", "json", "--base", "HEAD", str(p))
        self.assertEqual(r.returncode, 1, r.stderr)
        losses = [h for h in json.loads(r.stdout) if h["category"] == "notice-loss"]
        self.assertEqual(len(losses), 1, r.stdout)
        self.assertIn("copyright", losses[0]["reason"])
        self.assertIn("spdx-license-identifier", losses[0]["reason"])

    def test_no_notice_loss_when_marker_survives(self):
        p = self._repo_with_committed("src/util.js", self.NOTICED)
        p.write_text(self.NOTICED + "function g() {}\n")
        r = run("--format", "json", "--base", "HEAD", str(p))
        self.assertNotIn("notice-loss", r.stdout)

    def test_file_absent_from_base_warns_and_static_scan_continues(self):
        self._repo_with_committed("src/util.js", self.NOTICED)
        fresh = self._write("src/new.js", "// Copyright 2020 Synthetic\n")
        r = run("--base", "HEAD", str(fresh))
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("does not exist in 'HEAD'", r.stderr)
        self.assertIn("source-notice", r.stdout)
        self.assertNotIn("notice-loss", r.stdout)

    def test_non_repository_input_degrades_without_changing_exit_code(self):
        clean = self._write("plain.txt", "synthetic original text\n")
        r = run("--base", "HEAD", str(clean))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("not a git repository", r.stderr)
        self.assertEqual(r.stdout, "")

    def test_unresolvable_ref_degrades_without_changing_exit_code(self):
        p = self._repo_with_committed("src/util.js", self.NOTICED)
        r = run("--base", "no/such/ref", str(p))
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("does not resolve", r.stderr)
        self.assertIn("source-notice", r.stdout)
        self.assertNotIn("notice-loss", r.stdout)

    def test_missing_git_degrades_without_changing_exit_code(self):
        resolved = {t: shutil.which(t, path="/usr/bin:/bin") for t in SCRIPT_TOOLS}
        missing = sorted(t for t, found in resolved.items() if not found)
        if missing:
            self.skipTest(f"tool(s) not resolvable for a git-free PATH: {missing}")
        tools = {t: found for t, found in resolved.items() if found}
        shim = self.root / "nogit-bin"
        shim.mkdir()
        for tool, found in tools.items():
            (shim / tool).symlink_to(found)
        p = self._repo_with_committed("src/util.js", self.NOTICED)
        p.write_text("function f() {}\n")
        env = dict(os.environ, PATH=str(shim))
        r = run("--base", "HEAD", str(p), env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("git not available", r.stderr)
        self.assertEqual(r.stdout, "")

    def test_base_without_a_ref_is_input_error(self):
        r = run("--base")
        self.assertEqual(r.returncode, 2)
        self.assertIn("missing REF", r.stderr)


if __name__ == "__main__":
    unittest.main()
