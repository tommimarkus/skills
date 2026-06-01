import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "souroldgeezer-policy"
    / "skills"
    / "release-policy"
    / "references"
    / "scripts"
    / "version-bump"
)


def run_bump(*args: str, cwd: Path | None = None) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd or REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return json.loads(result.stdout)


def run_bump_raw(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class ReleasePolicyVersionBumpTest(unittest.TestCase):
    def test_public_command_is_thin_entrypoint(self) -> None:
        command_lines = SCRIPT.read_text(encoding="utf-8").splitlines()
        package_dir = SCRIPT.with_name("version_bump")

        self.assertLessEqual(len(command_lines), 40)
        self.assertTrue((package_dir / "cli.py").is_file())
        self.assertTrue((package_dir / "strategies.py").is_file())
        self.assertTrue((package_dir / "sources.py").is_file())

    def test_semver_minor_bump_outputs_next_version_and_tag(self) -> None:
        result = run_bump(
            "--strategy",
            "semver",
            "--current",
            "1.2.3",
            "--bump",
            "minor",
        )

        self.assertEqual(result["next_version"], "1.3.0")
        self.assertEqual(result["tag"], "v1.3.0")
        self.assertFalse(result["written"])

    def test_semver_prerelease_bump_increments_existing_label(self) -> None:
        result = run_bump(
            "--strategy",
            "semver",
            "--current",
            "2.0.0-rc.1",
            "--bump",
            "prerelease",
            "--pre-label",
            "rc",
        )

        self.assertEqual(result["next_version"], "2.0.0-rc.2")

    def test_calver_build_bump_uses_existing_tags_for_same_date_bucket(self) -> None:
        result = run_bump(
            "--strategy",
            "calver",
            "--scheme",
            "YYYY.MM.build",
            "--date",
            "2026-05-29",
            "--current",
            "2026.05.4",
            "--existing-tag",
            "v2026.05.7",
            "--existing-tag",
            "v2026.04.99",
        )

        self.assertEqual(result["next_version"], "2026.05.8")
        self.assertEqual(result["tag"], "v2026.05.8")

    def test_calver_build_bump_resets_when_date_bucket_changes(self) -> None:
        result = run_bump(
            "--strategy",
            "calver",
            "--scheme",
            "YYYY.MM.build",
            "--date",
            "2026-05-29",
            "--current",
            "2026.04.9",
        )

        self.assertEqual(result["next_version"], "2026.05.1")

    def test_write_updates_json_version_source_only_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "package.json"
            path.write_text('{"name":"demo","version":"1.2.3"}\n', encoding="utf-8")

            result = run_bump(
                "--strategy",
                "semver",
                "--source",
                str(path),
                "--bump",
                "patch",
                "--write",
            )

            self.assertEqual(result["current_version"], "1.2.3")
            self.assertEqual(result["next_version"], "1.2.4")
            self.assertTrue(result["written"])
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["version"],
                "1.2.4",
            )

    def test_pep440_post_bump_supports_python_package_versions(self) -> None:
        result = run_bump(
            "--strategy",
            "pep440",
            "--current",
            "1.2.3",
            "--bump",
            "post",
        )

        self.assertEqual(result["next_version"], "1.2.3.post1")

    def test_write_updates_toml_project_version_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pyproject.toml"
            path.write_text(
                '[project]\nname = "demo"\nversion = "1.2.3"\n',
                encoding="utf-8",
            )

            result = run_bump(
                "--strategy",
                "pep440",
                "--source",
                str(path),
                "--bump",
                "minor",
                "--write",
            )

            self.assertEqual(result["current_version"], "1.2.3")
            self.assertEqual(result["next_version"], "1.3.0")
            self.assertTrue(result["written"])
            self.assertIn('version = "1.3.0"', path.read_text(encoding="utf-8"))

    def test_invalid_version_uses_stable_policy_error_contract(self) -> None:
        result = run_bump_raw(
            "--strategy",
            "semver",
            "--current",
            "not-semver",
        )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("version-bump:invalid-policy:", result.stderr)

    def test_source_mismatch_uses_stable_source_error_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "package.json"
            path.write_text('{"version":"1.2.3"}\n', encoding="utf-8")

            result = run_bump_raw(
                "--strategy",
                "semver",
                "--source",
                str(path),
                "--current",
                "9.9.9",
            )

            self.assertEqual(result.returncode, 4)
            self.assertEqual(result.stdout, "")
            self.assertIn("version-bump:source-read:", result.stderr)


if __name__ == "__main__":
    unittest.main()
