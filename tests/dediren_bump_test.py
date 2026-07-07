"""Coverage for scripts/dediren_bump.py — the scoped Dediren pin-bump tool.

Mirrors version_stamp_test.py: load the script module, exercise its pure functions
against a throwaway copy of the real pin surfaces, and drive the CLI via subprocess.
The load-bearing safety property is scope: the bump must never touch the coincidental
souroldgeezer-design / marketplace CalVer that can equal the dediren pin.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
