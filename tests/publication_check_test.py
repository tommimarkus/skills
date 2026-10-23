"""Public CLI coverage for the local publication receipt and pre-push guard."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
ZERO_OID = "0" * 40


class PublicationCheckCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")
        self._write_fixture()
        self.git("add", ".")
        self.git("commit", "-m", "candidate")
        self.candidate = self.git("rev-parse", "HEAD").stdout.strip()

    def _write_fixture(self) -> None:
        (self.repo / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
        for rel in (
            "scripts/publication_check.py",
            "scripts/git-hooks/pre-push",
        ):
            target = self.repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE_ROOT / rel, target)

        passing_python = "#!/usr/bin/env python3\nraise SystemExit(0)\n"
        gate_paths = (
            "scripts/check-runtime-metadata-parity.py",
            "souroldgeezer-audit/skills/lean-audit/references/scripts/lean_engine.py",
            "scripts/check-runtime-host-smoke.py",
            "scripts/version_stamp.py",
        )
        for rel in gate_paths:
            target = self.repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(passing_python, encoding="utf-8")
            target.chmod(0o755)

        for rel in ("scripts/validate-fragmentation.sh", "scripts/skill-architecture-report.sh"):
            target = self.repo / rel
            target.write_text('#!/bin/sh\nexit "${PUBLICATION_TEST_FAIL:-0}"\n', encoding="utf-8")
            target.chmod(0o755)

        (self.repo / "scripts/validate-fragmentation.sh").write_text(
            '#!/bin/sh\nset -e\npython3 scripts/check-runtime-metadata-parity.py --check .\n'
            'exit "${PUBLICATION_TEST_FAIL:-0}"\n', encoding="utf-8",
        )
        (self.repo / "scripts/check-runtime-metadata-parity.py").write_text(
            "from pathlib import Path\n"
            "with Path('.git/parity-calls').open('a') as stream: stream.write('call\\n')\n",
            encoding="utf-8",
        )
        smoke = self.repo / "tests/smoke_test.py"
        smoke.parent.mkdir(parents=True)
        smoke.write_text(
            "import unittest\n\n"
            "class Smoke(unittest.TestCase):\n"
            "    def test_ok(self): self.assertTrue(True)\n",
            encoding="utf-8",
        )

        fake_uv = self.repo / "bin/uv"
        fake_uv.parent.mkdir()
        fake_uv.write_text('#!/bin/sh\n[ "$1" = run ] && shift\nexec "$@"\n', encoding="utf-8")
        fake_uv.chmod(0o755)

    @property
    def env(self) -> dict[str, str]:
        return {**os.environ, "PATH": f"{self.repo / 'bin'}:{os.environ['PATH']}"}

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            text=True,
            capture_output=True,
            check=True,
        )

    def cli(
        self, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(self.repo / "scripts/publication_check.py"),
                "--repo-root",
                str(self.repo),
                *args,
            ],
            text=True,
            capture_output=True,
            env=env or self.env,
        )

    def record(
        self, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        result = self.cli("record", *args, env=env)
        if not args and env is None:
            self.assertEqual(0, result.returncode, result.stderr)
        return result

    def pre_push(self, update: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.repo / "scripts/git-hooks/pre-push"), "origin", "unused"],
            cwd=self.repo,
            input=update,
            text=True,
            capture_output=True,
            env=self.env,
        )

    def test_matching_raw_sha_passes_and_unchecked_or_malformed_evidence_fails(self) -> None:
        raw_sha_update = f"{self.candidate} {self.candidate} refs/heads/main {ZERO_OID}\n"
        missing = self.pre_push(raw_sha_update)
        self.assertNotEqual(0, missing.returncode)
        self.assertIn("invalid receipt", missing.stderr)

        self.record()
        self.assertEqual(["call"], (self.repo / ".git/parity-calls").read_text().splitlines())
        self.assertEqual(0, self.pre_push(raw_sha_update).returncode)

        (self.repo / "next.txt").write_text("next\n", encoding="utf-8")
        self.git("add", "next.txt")
        self.git("commit", "-m", "unchecked")
        unchecked = self.git("rev-parse", "HEAD").stdout.strip()
        rejected = self.pre_push(f"refs/heads/main {unchecked} refs/heads/main {self.candidate}\n")
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("does not cover", rejected.stderr)

        receipt = self.repo / ".git/publication-check/receipt.json"
        receipt.write_text("{malformed", encoding="utf-8")
        malformed = self.pre_push(raw_sha_update)
        self.assertNotEqual(0, malformed.returncode)
        self.assertIn("invalid receipt", malformed.stderr)

    def test_failed_gate_and_tampered_receipt_are_rejected(self) -> None:
        failed_env = {**self.env, "PUBLICATION_TEST_FAIL": "23"}
        result = self.record(env=failed_env)
        self.assertEqual(23, result.returncode)
        rejected = self.pre_push(f"refs/heads/main {self.candidate} refs/heads/main {ZERO_OID}\n")
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("candidate gates did not pass", rejected.stderr)

        self.record()
        receipt_path = self.repo / ".git/publication-check/receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["candidate"]["tree"] = "f" * 40
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        tampered = self.pre_push(f"refs/heads/main {self.candidate} refs/heads/main {ZERO_OID}\n")
        self.assertNotEqual(0, tampered.returncode)
        self.assertIn("integrity", tampered.stderr)

        (self.repo / "tests/smoke_test.py").write_text("", encoding="utf-8")
        self.git("add", "tests/smoke_test.py")
        self.git("commit", "-m", "zero tests")
        zero = self.cli("record")
        self.assertIn("full suite collected zero tests", zero.stderr)

    def test_deletion_non_fast_forward_and_malformed_input_fail_closed(self) -> None:
        self.record()
        deletion = self.pre_push(f"(delete) {ZERO_OID} refs/heads/main {self.candidate}\n")
        self.assertNotEqual(0, deletion.returncode)
        self.assertIn("deletion", deletion.stderr)

        (self.repo / "descendant.txt").write_text("descendant\n", encoding="utf-8")
        self.git("add", "descendant.txt")
        self.git("commit", "-m", "descendant")
        descendant = self.git("rev-parse", "HEAD").stdout.strip()
        non_ff = self.pre_push(f"refs/heads/main {self.candidate} refs/heads/main {descendant}\n")
        self.assertNotEqual(0, non_ff.returncode)
        self.assertIn("non-fast-forward", non_ff.stderr)

        malformed = self.pre_push("not a pre-push record\n")
        self.assertNotEqual(0, malformed.returncode)
        self.assertIn("malformed pre-push", malformed.stderr)

    def test_version_only_followup_can_extend_candidate_receipt(self) -> None:
        plugin = self.repo / "souroldgeezer-policy"
        for rel, version in (
            (".claude-plugin/plugin.json", "2026.10.15"),
            (".codex-plugin/plugin.json", "2026.10.15"),
        ):
            target = plugin / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"name": "policy", "version": version}), encoding="utf-8")
        (self.repo / "README.md").write_text(
            "| Plugin | Version | Skills |\n|---|---:|---|\n"
            "| `souroldgeezer-policy` | `2026.10.15` | skills |\n",
            encoding="utf-8",
        )
        self.git("add", ".")
        self.git("commit", "-m", "version baseline")
        self.candidate = self.git("rev-parse", "HEAD").stdout.strip()
        self.record()

        for rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            target = plugin / rel
            payload = json.loads(target.read_text(encoding="utf-8"))
            payload["version"] = "2026.10.16"
            target.write_text(json.dumps(payload), encoding="utf-8")
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace("2026.10.15", "2026.10.16"), encoding="utf-8"
        )
        self.git("add", ".")
        self.git("commit", "-m", "stamp versions")
        followup = self.git("rev-parse", "HEAD").stdout.strip()

        extended = self.record("--version-followup")
        self.assertEqual(0, extended.returncode, extended.stderr)
        accepted = self.pre_push(f"refs/heads/main {followup} refs/heads/main {self.candidate}\n")
        self.assertEqual(0, accepted.returncode, accepted.stderr)

    def test_install_and_uninstall_refuse_to_replace_modified_hook(self) -> None:
        installed = self.cli("install-hook")
        self.assertEqual(0, installed.returncode, installed.stderr)
        installed_path = self.repo / ".git/hooks/pre-push"
        removed = self.cli("uninstall-hook")
        self.assertEqual(0, removed.returncode, removed.stderr)
        self.assertFalse(installed_path.exists())
        self.assertEqual(0, self.cli("install-hook").returncode)
        installed_path.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
        self.assertNotEqual(0, self.cli("install-hook").returncode)
        self.assertNotEqual(0, self.cli("uninstall-hook").returncode)
