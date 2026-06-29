import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "scripts" / "version_stamp.py"


def load_module():
    spec = importlib.util.spec_from_file_location("version_stamp", MODULE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["version_stamp"] = module
    spec.loader.exec_module(module)
    return module


vs = load_module()


class ComputeNextTest(unittest.TestCase):
    def test_increments_micro_within_same_month(self):
        self.assertEqual(vs.compute_next("2026.06.3", "2026.06"), "2026.06.4")

    def test_resets_micro_for_new_month(self):
        self.assertEqual(vs.compute_next("2026.05.2", "2026.06"), "2026.06.0")

    def test_resets_for_pre_calver_semver(self):
        self.assertEqual(vs.compute_next("2.8.1", "2026.06"), "2026.06.0")

    def test_first_bump_in_month_from_zero(self):
        self.assertEqual(vs.compute_next("2026.06.0", "2026.06"), "2026.06.1")

    def test_rejects_month_older_than_current(self):
        with self.assertRaises(ValueError):
            vs.compute_next("2026.07.0", "2026.06")


class VersionDiffTest(unittest.TestCase):
    def test_no_change(self):
        a = {"x": "2026.06.0"}
        self.assertEqual(vs.version_diff(a, dict(a)), [])

    def test_detects_bumped_cell(self):
        base = {"x": "2026.06.3"}
        head = {"x": "2026.06.4"}
        self.assertEqual(vs.version_diff(base, head), [("x", "2026.06.3", "2026.06.4")])

    def test_ignores_keys_absent_in_base(self):
        self.assertEqual(vs.version_diff({}, {"new": "2026.06.0"}), [])

    def test_ignores_keys_absent_in_head(self):
        self.assertEqual(vs.version_diff({"x": "2026.06.0"}, {}), [])


class ParseVersionTest(unittest.TestCase):
    def test_parses_calver(self):
        self.assertEqual(vs.parse_version("2026.06.3"), (2026, 6, 3))

    def test_rejects_non_calver(self):
        with self.assertRaises(ValueError):
            vs.parse_version("2.8.1")


class CurrentMonthTest(unittest.TestCase):
    def test_format(self):
        self.assertRegex(vs.current_month(), r"^\d{4}\.\d{2}$")


def _write_plugin_manifest(root: Path, plugin: str, version: str) -> None:
    manifest_dir = root / plugin / ".claude-plugin"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "plugin.json").write_text(
        json.dumps({"name": plugin, "version": version}, indent=2) + "\n",
        encoding="utf-8",
    )


class ComputeCliTest(unittest.TestCase):
    def _run(self, root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = vs.main([
                "--repo-root", str(root),
                "compute", "--plugin", "souroldgeezer-audit", "--month", "2026.06",
            ])
        return rc, buf.getvalue().strip()

    def test_compute_prints_next_stamp_from_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write_plugin_manifest(root, "souroldgeezer-audit", "2026.06.3")
            _git(root, "add", "-A")
            _git(root, "commit", "-qm", "seed")
            rc, out = self._run(root)
            self.assertEqual(rc, 0)
            self.assertEqual(out, "2026.06.4")

    def test_compute_reads_main_not_stale_working_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            _write_plugin_manifest(root, "souroldgeezer-audit", "2026.06.3")
            _git(root, "add", "-A")
            _git(root, "commit", "-qm", "seed")
            # working tree goes ahead, uncommitted — compute must ignore it
            _write_plugin_manifest(root, "souroldgeezer-audit", "2026.06.9")
            rc, out = self._run(root)
            self.assertEqual(rc, 0)
            self.assertEqual(out, "2026.06.4")


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True,
                   capture_output=True, text=True)


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")


def _write_marketplace(root: Path, plugin: str, version: str) -> None:
    mp_dir = root / ".claude-plugin"
    mp_dir.mkdir(parents=True, exist_ok=True)
    (mp_dir / "marketplace.json").write_text(
        json.dumps({"plugins": [{"name": plugin, "version": version}]}, indent=2)
        + "\n",
        encoding="utf-8",
    )


class GuardTest(unittest.TestCase):
    def _seed(self, root: Path) -> None:
        _init_repo(root)
        _write_plugin_manifest(root, "souroldgeezer-audit", "2026.06.3")
        _write_marketplace(root, "souroldgeezer-audit", "2026.06.3")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "seed")

    def _guard(self, root: Path) -> int:
        return vs.main(["--repo-root", str(root), "guard",
                        "--base", "main", "--head", "feature"])

    def test_fails_when_branch_stamps_a_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root)
            _git(root, "checkout", "-q", "-b", "feature")
            _write_plugin_manifest(root, "souroldgeezer-audit", "2026.06.4")
            _git(root, "commit", "-qam", "premature stamp")
            self.assertEqual(self._guard(root), 1)

    def test_passes_for_content_only_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root)
            _git(root, "checkout", "-q", "-b", "feature")
            note = root / "souroldgeezer-audit" / "skills" / "note.md"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text("content\n", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-qm", "content only")
            self.assertEqual(self._guard(root), 0)

    def test_no_false_positive_when_main_advances_independently(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root)
            _git(root, "checkout", "-q", "-b", "feature")
            (root / "f.txt").write_text("x\n", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-qm", "branch work")
            _git(root, "checkout", "-q", "main")
            _write_plugin_manifest(root, "souroldgeezer-audit", "2026.06.4")
            _write_marketplace(root, "souroldgeezer-audit", "2026.06.4")
            _git(root, "commit", "-qam", "stamp on main")
            self.assertEqual(self._guard(root), 0)

    def test_fails_when_branch_stamps_marketplace_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed(root)
            _git(root, "checkout", "-q", "-b", "feature")
            _write_marketplace(root, "souroldgeezer-audit", "2026.06.4")
            _git(root, "commit", "-qam", "stamp marketplace entry")
            self.assertEqual(self._guard(root), 1)


if __name__ == "__main__":
    unittest.main()
