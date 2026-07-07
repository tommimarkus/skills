"""Coverage for scripts/dediren_bump.py — the scoped Dediren pin-bump tool.

Mirrors version_stamp_test.py: load the script module, exercise its pure functions
against a throwaway copy of the real pin surfaces, and drive the CLI via subprocess.
The load-bearing safety property is scope: the bump must never touch the coincidental
souroldgeezer-design / marketplace CalVer that can equal the dediren pin.
"""
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.surface_test_lib import REPO_ROOT, load_script_module

MODULE = REPO_ROOT / "scripts" / "dediren_bump.py"
db = load_script_module("dediren_bump", MODULE)

ARCH_REFS_REL = "souroldgeezer-architecture/skills/architecture-design/references"
RELEASE_SCRIPT_REL = f"{ARCH_REFS_REL}/scripts/dediren-release.sh"
TEST_FILE_REL = "tests/architecture_dediren_release_test.py"
SOURCE_GROUNDING_REL = f"{ARCH_REFS_REL}/source-grounding.md"

# A deliberately-distant, validly-shaped CalVer sentinel that cannot collide with any
# real historical dediren reference embedded in the surfaces.
NEW = "2099.12.7"


def real_current() -> str:
    """Read the current pin from the real release-script SoT, independent of the tool."""
    text = (REPO_ROOT / RELEASE_SCRIPT_REL).read_text(encoding="utf-8")
    match = re.search(r'DEDIREN_VERSION_DEFAULT="([^"]+)"', text)
    assert match, "release script must define DEDIREN_VERSION_DEFAULT"
    return match.group(1)


CURRENT = real_current()


def build_temp_repo(tmp: Path, *, with_decoys: bool = False) -> Path:
    """Copy the real dediren pin surfaces into `tmp`, preserving repo-relative paths."""
    shutil.copytree(REPO_ROOT / ARCH_REFS_REL, tmp / ARCH_REFS_REL)
    (tmp / "tests").mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / TEST_FILE_REL, tmp / TEST_FILE_REL)
    if with_decoys:
        # The coincidental CalVer collision: souroldgeezer-design's own plugin version
        # and the marketplace entry can equal the dediren pin. They must stay untouched.
        design = tmp / "souroldgeezer-design" / ".claude-plugin" / "plugin.json"
        design.parent.mkdir(parents=True, exist_ok=True)
        design.write_text(
            f'{{\n  "name": "souroldgeezer-design",\n  "version": "{CURRENT}"\n}}\n',
            encoding="utf-8",
        )
        marketplace = tmp / ".claude-plugin" / "marketplace.json"
        marketplace.parent.mkdir(parents=True, exist_ok=True)
        marketplace.write_text(
            f'{{\n  "plugins": [\n'
            f'    {{ "name": "souroldgeezer-architecture", "version": "{CURRENT}" }}\n'
            f'  ]\n}}\n',
            encoding="utf-8",
        )
    return tmp


def read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


class CurrentVersionTest(unittest.TestCase):
    def test_reads_release_script_sot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            self.assertEqual(db.current_version(root), CURRENT)


class DiscoverPinsTest(unittest.TestCase):
    def test_covers_fixtures_and_notations_all_at_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            pins = db.discover_pins(root)
            self.assertTrue(pins, "expected discovered pins")
            self.assertTrue(any("fixtures/dediren" in key for key in pins))
            self.assertTrue(any("notations/uml" in key for key in pins))
            self.assertEqual(set(pins.values()), {CURRENT})


class BumpTest(unittest.TestCase):
    def test_rewrites_every_pin_and_reverifies_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            report = db.bump(root, NEW)

            self.assertEqual(report.old, CURRENT)
            self.assertEqual(report.new, NEW)
            self.assertTrue(report.changed_files)

            self.assertEqual(set(db.discover_pins(root).values()), {NEW})
            self.assertEqual(db.current_version(root), NEW)
            self.assertIn(f'EXPECTED_DEDIREN_VERSION = "{NEW}"', read(root, TEST_FILE_REL))
            grounding = read(root, SOURCE_GROUNDING_REL)
            self.assertIn(NEW, grounding)
            self.assertNotIn(CURRENT, grounding)
            self.assertEqual(db.verify(root, NEW), [])

    def test_release_script_default_and_usage_both_bump(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            db.bump(root, NEW)
            script = read(root, RELEASE_SCRIPT_REL)
            self.assertIn(f'DEDIREN_VERSION_DEFAULT="{NEW}"', script)
            self.assertIn(f"default {NEW}", script)
            self.assertNotIn(CURRENT, script)

    def test_leaves_coincidental_calver_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp), with_decoys=True)
            db.bump(root, NEW)
            self.assertIn(CURRENT, read(root, "souroldgeezer-design/.claude-plugin/plugin.json"))
            self.assertNotIn(NEW, read(root, "souroldgeezer-design/.claude-plugin/plugin.json"))
            self.assertIn(CURRENT, read(root, ".claude-plugin/marketplace.json"))

    def test_check_writes_nothing_but_reports_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            before = read(root, RELEASE_SCRIPT_REL)
            report = db.bump(root, NEW, check=True)
            self.assertTrue(report.changed_files)
            self.assertEqual(report.old, CURRENT)
            self.assertEqual(report.new, NEW)
            # Nothing on disk moved.
            self.assertEqual(read(root, RELEASE_SCRIPT_REL), before)
            self.assertEqual(set(db.discover_pins(root).values()), {CURRENT})

    def test_noop_when_already_at_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            report = db.bump(root, CURRENT)
            self.assertEqual(report.changed_files, [])

    def test_rejects_non_calver_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            for bad in ("1.2", "not-a-version", "2026.7.6", "v2026.07.6"):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    db.bump(root, bad)

    def test_rejects_predrifted_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            # Corrupt one notation example so a pin no longer equals the SoT.
            drifted = root / ARCH_REFS_REL / "notations" / "uml" / "class.md"
            drifted.write_text(
                drifted.read_text(encoding="utf-8").replace(CURRENT, "2000.01.0", 1),
                encoding="utf-8",
            )
            with self.assertRaises(db.PinDriftError):
                db.bump(root, NEW)


class VerifyTest(unittest.TestCase):
    def test_reports_mismatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            self.assertEqual(db.verify(root, CURRENT), [])
            mismatches = db.verify(root, NEW)
            self.assertTrue(mismatches)


class ParityPlanTest(unittest.TestCase):
    def test_reports_both_versions_and_surface_globs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            plan = db.parity_plan(root, NEW)
            self.assertEqual(plan["current"], CURRENT)
            self.assertEqual(plan["target"], NEW)
            self.assertTrue(plan["surfaces"])
            self.assertTrue(any("agent-usage" in s for s in plan["surfaces"]))


class CliTest(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MODULE), *args],
            cwd=REPO_ROOT, check=False, text=True, capture_output=True,
        )

    def test_current_prints_pinned_version(self):
        result = self._run("current")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), CURRENT)

    def test_bump_check_is_nonmutating(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            before = read(root, RELEASE_SCRIPT_REL)
            result = self._run("bump", "--to", NEW, "--check", "--repo-root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(read(root, RELEASE_SCRIPT_REL), before)

    def test_bump_rejects_bad_version_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            result = self._run("bump", "--to", "not-a-version", "--repo-root", str(root))
            self.assertNotEqual(result.returncode, 0)

    def test_adopt_help_lists_the_subcommand(self):
        result = self._run("adopt", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("verdict", result.stdout)

    def test_adopt_rejects_bad_version_before_any_network(self):
        # A non-CalVer target fails preflight with exit 2 without touching the resolver.
        result = self._run("adopt", "--to", "not-a-version", "--repo-root", str(REPO_ROOT))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("not CalVer", result.stdout + result.stderr)

    def test_latest_subcommand_is_registered(self):
        # Offline: --help proves the subcommand is wired without resolving the network.
        result = self._run("latest", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)


class CalverOrderTest(unittest.TestCase):
    def test_micro_orders_numerically_not_lexically(self):
        # The bug string comparison would hit: "2026.07.9" > "2026.07.10" lexically.
        self.assertLess(db._calver_tuple("2026.07.9"), db._calver_tuple("2026.07.10"))
        self.assertLess(db._calver_tuple("2026.07.27"), db._calver_tuple("2026.08.0"))
        self.assertEqual(db._calver_tuple("2026.07.9"), (2026, 7, 9))


class ParseReleaseTagTest(unittest.TestCase):
    def test_parses_v_prefixed_calver(self):
        self.assertEqual(
            db._parse_release_tag("https://github.com/o/r/releases/tag/v2026.07.10"),
            "2026.07.10",
        )

    def test_parses_without_v_and_with_trailing_slash(self):
        self.assertEqual(
            db._parse_release_tag("https://github.com/o/r/releases/tag/2026.07.10/"),
            "2026.07.10",
        )

    def test_rejects_url_without_a_tag(self):
        with self.assertRaises(RuntimeError):
            db._parse_release_tag("https://github.com/o/r/releases")

    def test_rejects_non_calver_tag(self):
        with self.assertRaises(RuntimeError):
            db._parse_release_tag("https://github.com/o/r/releases/tag/nightly")


class RepoSlugTest(unittest.TestCase):
    def test_reads_release_script_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            self.assertEqual(db._repo_slug(root), "tommimarkus/dediren")

    def test_env_override_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            with mock.patch.dict(db.os.environ, {"DEDIREN_REPO": "fork/dediren"}):
                self.assertEqual(db._repo_slug(root), "fork/dediren")


class ResolveLatestTest(unittest.TestCase):
    class _Resp:
        def __init__(self, url):
            self._url = url

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def geturl(self):
            return self._url

    def test_follows_redirect_and_parses_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            target = "https://github.com/tommimarkus/dediren/releases/tag/v2027.01.3"
            with mock.patch.object(db.urllib.request, "urlopen",
                                   return_value=self._Resp(target)):
                self.assertEqual(db.resolve_latest(root), "2027.01.3")

    def test_network_failure_raises_runtimeerror(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_temp_repo(Path(tmp))
            with mock.patch.object(db.urllib.request, "urlopen",
                                   side_effect=db.urllib.error.URLError("boom")):
                with self.assertRaises(RuntimeError):
                    db.resolve_latest(root)


class PreflightProblemsTest(unittest.TestCase):
    def test_clean_forward_bump_has_no_problems(self):
        self.assertEqual(
            db.preflight_problems("2026.07.9", "2026.07.10", dirty_pin_paths=[]), []
        )

    def test_flags_non_calver_target(self):
        problems = db.preflight_problems("2026.07.9", "nope", dirty_pin_paths=[])
        self.assertTrue(problems and "not CalVer" in problems[0])

    def test_flags_older_target(self):
        problems = db.preflight_problems("2026.07.10", "2026.07.9", dirty_pin_paths=[])
        self.assertTrue(any("older" in p for p in problems))

    def test_flags_dirty_pin_surfaces(self):
        problems = db.preflight_problems(
            "2026.07.9", "2026.07.10", dirty_pin_paths=["a/pin.md", "b/pin.json"]
        )
        self.assertTrue(any("already modified" in p for p in problems))
        self.assertIn("a/pin.md", " ".join(problems))


class ClassifyBundleChangeTest(unittest.TestCase):
    OLD, NEW_V = "2026.07.9", "2026.07.10"

    def test_version_only_diff_is_cosmetic(self):
        surfaces = [
            ("bundle.json", '{"v":"2026.07.9"}', '{"v":"2026.07.10"}'),
            ("docs/agent-usage.md", "pinned 2026.07.9 here", "pinned 2026.07.10 here"),
            ("schemas/model.json", "identical", "identical"),
        ]
        classification, substantive = db.classify_bundle_change(surfaces, self.OLD, self.NEW_V)
        self.assertEqual(classification, "cosmetic")
        self.assertEqual(substantive, [])

    def test_added_field_is_substantive(self):
        surfaces = [("schemas/model.json", '{"a":1}', '{"a":1,"b":2}')]
        classification, substantive = db.classify_bundle_change(surfaces, self.OLD, self.NEW_V)
        self.assertEqual(classification, "non-cosmetic")
        self.assertEqual(substantive, ["schemas/model.json"])

    def test_added_or_removed_file_is_substantive(self):
        surfaces = [
            ("schemas/new.json", None, "{}"),        # added upstream
            ("schemas/gone.json", "{}", None),       # removed upstream
        ]
        classification, substantive = db.classify_bundle_change(surfaces, self.OLD, self.NEW_V)
        self.assertEqual(classification, "non-cosmetic")
        self.assertEqual(sorted(substantive), ["schemas/gone.json", "schemas/new.json"])

    def test_binary_change_is_substantive_but_equal_binary_is_not(self):
        surfaces = [
            ("fixtures/a.bin", b"\x00\x01", b"\x00\x02"),
            ("fixtures/b.bin", b"\xff\xfe", b"\xff\xfe"),
        ]
        classification, substantive = db.classify_bundle_change(surfaces, self.OLD, self.NEW_V)
        self.assertEqual(classification, "non-cosmetic")
        self.assertEqual(substantive, ["fixtures/a.bin"])

    def test_no_changes_is_cosmetic(self):
        surfaces = [("bundle.json", "same", "same")]
        classification, _ = db.classify_bundle_change(surfaces, self.OLD, self.NEW_V)
        self.assertEqual(classification, "cosmetic")


class IntegrationRecipeTest(unittest.TestCase):
    def test_recipe_stamps_on_main_and_names_the_plugin(self):
        recipe = "\n".join(db.integration_recipe("2026.08.0"))
        self.assertIn("version_stamp.py guard", recipe)
        self.assertIn("version_stamp.py compute --plugin souroldgeezer-architecture", recipe)
        self.assertIn("merge --ff-only dediren-2026.08.0", recipe)
        # It must never propose stamping from the branch.
        self.assertIn("main", recipe)


class NextActionsAndVerifyPlanTest(unittest.TestCase):
    def test_cosmetic_skips_indepth_ip_hygiene(self):
        actions = " ".join(db.next_actions("cosmetic", "2026.08.0"))
        self.assertIn("no in-depth run required", actions)
        self.assertNotIn("IN-DEPTH", actions)

    def test_non_cosmetic_requires_indepth_ip_hygiene_and_capability_review(self):
        actions = " ".join(db.next_actions("non-cosmetic", "2026.08.0"))
        self.assertIn("IN-DEPTH", actions)
        self.assertIn("NEW capability", actions)

    def test_verify_plan_runs_smoke_with_flag_plus_surface_and_diff_checks(self):
        plan = db.verify_plan()
        names = {name for name, _, _ in plan}
        self.assertEqual(names, {"smoke", "surface-tests", "diff-check"})
        smoke = next(spec for spec in plan if spec[0] == "smoke")
        self.assertEqual(smoke[2].get("DEDIREN_RELEASE_SMOKE"), "1")
        self.assertIn("tests.architecture_dediren_release_test", smoke[1])
        diff_check = next(spec for spec in plan if spec[0] == "diff-check")
        self.assertEqual(diff_check[1], ["git", "diff", "--check"])


class EmitVerdictTest(unittest.TestCase):
    def test_json_verdict_is_machine_readable(self):
        verdict = db.AdoptVerdict(
            "2026.07.9", "2026.07.10", "ready", True,
            classification="cosmetic", verify_results=[("smoke", True)],
            next_actions=["do x"], integration=["step y"],
        )
        buffer = io.StringIO()
        db._emit_verdict(verdict, out=buffer, json_out=True)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["classification"], "cosmetic")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["verify"], [{"check": "smoke", "ok": True}])

    def test_text_verdict_shows_result_and_next(self):
        verdict = db.AdoptVerdict(
            "2026.07.9", "2026.07.10", "verify", False,
            problems=["verify gate 'smoke' failed"],
            next_actions=["re-run adopt"],
        )
        buffer = io.StringIO()
        db._emit_verdict(verdict, out=buffer, json_out=False)
        text = buffer.getvalue()
        self.assertIn("result: BLOCKED", text)
        self.assertIn("NEXT:", text)
        self.assertIn("smoke", text)


if __name__ == "__main__":
    unittest.main()
