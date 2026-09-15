"""Exercise the explicit-root writer without relying on host state."""

import hashlib
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import shutil
import stat

from tests.planning_policy_shared_contract_test import leaf, v5_plan


ROOT = Path(__file__).resolve().parents[1]
PERSIST = ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts/persist_plan.py"
VALIDATE = ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts/validate_plan_contract.py"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


class PlanningPolicyPersistenceTest(unittest.TestCase):
    def setUp(self):
        cache = ROOT / ".cache"
        cache.mkdir(exist_ok=True)
        directory = tempfile.TemporaryDirectory(dir=cache, prefix="persist-test-")
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.root = self.directory / "durable-plans"
        self.plan = v5_plan(leaf("persist", "u1", tier="mechanical"))
        self.digest = hashlib.sha256(canonical(self.plan)).hexdigest()

    def persist(self, *args, value=None, env=None):
        result = subprocess.run(
            [sys.executable, "-B", str(PERSIST), "--plan-root", str(self.root), *args],
            input=json.dumps(value) if value is not None else None,
            cwd=self.directory / "unrelated-cwd",
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, **(env or {})},
        )
        self.assertNotIn("Traceback", result.stderr)
        return result.returncode, json.loads(result.stdout)

    def resolve(self, handoff):
        result = subprocess.run(
            [sys.executable, "-B", str(VALIDATE), "resolve-handoff", "-"],
            input=json.dumps(handoff),
            cwd=self.directory,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        return json.loads(result.stdout)

    def plan_with_canonical_size(self, size):
        plan = copy.deepcopy(self.plan)
        plan["leaves"][0]["settled_decisions"]["padding"] = "x" * (
            size - len(canonical(plan)) - len(',"padding":""')
        )
        self.assertEqual(len(canonical(plan)), size)
        return plan

    def test_fresh_process_publishes_canonical_reference_and_recovers_exact_plan(self):
        (self.directory / "unrelated-cwd").mkdir()
        code, result = self.persist("-", value=self.plan)
        self.assertEqual(code, 0, result)
        handoff = result
        path = self.root / self.digest / "plan.json"
        self.assertEqual(handoff, {
            "schema": "planning-approval-handoff-v1",
            "plan_sha256": self.digest,
            "plan_path": str(path),
        })
        self.assertEqual(path.read_bytes(), canonical(self.plan))
        self.assertEqual(self.resolve(handoff)["plan"], self.plan)
        self.assertEqual(list((self.directory / "unrelated-cwd").iterdir()), [])

    def test_private_new_artifacts_preserve_existing_root_mode(self):
        (self.directory / "unrelated-cwd").mkdir()
        self.root.mkdir(mode=0o750)
        os.chmod(self.root, 0o750)
        code, _ = self.persist("-", value=self.plan)
        self.assertEqual(code, 0)
        self.assertEqual(stat.S_IMODE(self.root.stat().st_mode), 0o750)
        self.assertEqual(stat.S_IMODE((self.root / self.digest).stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.root / self.digest / "plan.json").stat().st_mode), 0o600)

    def test_repeat_and_concurrent_saves_never_overwrite_or_change_reference(self):
        (self.directory / "unrelated-cwd").mkdir()
        command = [sys.executable, "-B", str(PERSIST), "--plan-root", str(self.root), "-"]
        writers = [
            subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=self.directory / "unrelated-cwd",
            )
            for _ in range(2)
        ]
        try:
            for writer in writers:
                assert writer.stdin is not None
                writer.stdin.write(json.dumps(self.plan))
                writer.stdin.close()
            results = []
            for writer in writers:
                self.assertEqual(writer.wait(timeout=10), 0)
                assert writer.stdout is not None and writer.stderr is not None
                self.assertEqual(writer.stderr.read(), "")
                results.append((writer.returncode, json.loads(writer.stdout.read())))
                writer.stdout.close()
                writer.stderr.close()
        finally:
            for writer in writers:
                if writer.poll() is None:
                    writer.kill()
                    writer.wait(timeout=10)
                for stream in (writer.stdin, writer.stdout, writer.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()
        self.assertEqual(results[0], results[1])
        path = self.root / self.digest / "plan.json"
        before = path.read_bytes()
        path.write_bytes(b"{}")
        code, result = self.persist("-", value=self.plan)
        self.assertEqual(code, 1, result)
        self.assertEqual(result["blocked"], "blocked:plan_tampered")
        self.assertEqual(path.read_bytes(), b"{}")
        self.assertNotEqual(before, path.read_bytes())

    def test_rejects_unsafe_root_and_invalid_plan_without_creating_state(self):
        (self.directory / "unrelated-cwd").mkdir()
        invalid = dict(self.plan)
        invalid["contract_version"] = 4
        code, result = self.persist("-", value=invalid)
        self.assertEqual(code, 1, result)
        self.assertEqual(result["blocked"], "blocked:missing_input")

        unavailable_invalid = subprocess.run(
            [sys.executable, "-B", str(PERSIST), "--plan-root", "/proc/planning-policy-plans", "-"],
            input=json.dumps(invalid), cwd=self.directory / "unrelated-cwd", capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(unavailable_invalid.returncode, 1)
        self.assertEqual(json.loads(unavailable_invalid.stdout)["blocked"], "blocked:missing_input")
        self.assertFalse(self.root.exists())
        self.root.symlink_to(self.directory)
        code, result = self.persist("-", value=self.plan)
        self.assertEqual(code, 1, result)
        self.assertEqual(result["blocked"], "blocked:missing_input")

    def test_denied_explicit_root_is_operationally_unavailable_after_validation(self):
        (self.directory / "unrelated-cwd").mkdir()
        denied = self.directory / "denied"
        denied.mkdir()
        os.chmod(denied, 0o000)
        self.addCleanup(os.chmod, denied, 0o700)
        result = subprocess.run(
            [sys.executable, "-B", str(PERSIST), "--plan-root", str(denied / "plans"), "-"],
            input=json.dumps(self.plan), cwd=self.directory / "unrelated-cwd", capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertEqual(json.loads(result.stdout)["blocked"], "blocked:persistence_unavailable")

    def test_digest_and_final_symlinks_or_fifo_are_integrity_failures(self):
        (self.directory / "unrelated-cwd").mkdir()
        digest_directory = self.root / self.digest
        digest_directory.parent.mkdir()
        digest_directory.symlink_to(self.directory, target_is_directory=True)
        code, result = self.persist("-", value=self.plan)
        self.assertEqual(code, 1, result)
        self.assertEqual(result["blocked"], "blocked:plan_tampered")
        digest_directory.unlink()
        digest_directory.mkdir()
        external = self.directory / "valid-plan.json"
        external.write_bytes(canonical(self.plan))
        (digest_directory / "plan.json").symlink_to(external)
        code, result = self.persist("-", value=self.plan)
        self.assertEqual(code, 1, result)
        self.assertEqual(result["blocked"], "blocked:plan_tampered")
        (digest_directory / "plan.json").unlink()
        if hasattr(os, "mkfifo"):
            os.mkfifo(digest_directory / "plan.json")
            code, result = self.persist("-", value=self.plan)
            self.assertEqual(code, 1, result)
            self.assertEqual(result["blocked"], "blocked:plan_tampered")

    def test_reference_eligibility_has_no_tempfile_probe_writes(self):
        (self.directory / "unrelated-cwd").mkdir()
        blocked_temp = self.directory / "blocked-temp"
        blocked_temp.mkdir(mode=0o500)
        source = self.directory / "source-plan.json"
        source.write_bytes(canonical(self.plan))
        result = subprocess.run(
            [sys.executable, "-B", str(VALIDATE), "validate", str(source), "--emit-handoff", "reference"],
            cwd=self.directory,
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "TMPDIR": str(blocked_temp), "TEMP": str(blocked_temp), "TMP": str(blocked_temp)},
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(list(blocked_temp.iterdir()), [])

    def test_reference_eligibility_never_calls_tempfile_writable_discovery(self):
        import importlib.util
        import tempfile as stdlib_tempfile

        source = self.directory / "source-plan.json"
        source.write_bytes(canonical(self.plan))
        spec = importlib.util.spec_from_file_location("handoff_contract_no_probe", VALIDATE)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        with mock.patch.object(stdlib_tempfile, "gettempdir", side_effect=AssertionError("write probe")):
            handoff = module.emit_handoff(self.plan, "reference", str(source))
        self.assertEqual(handoff["plan_path"], str(source))

    def test_interrupted_publication_cleans_only_its_staging_file(self):
        import importlib.util

        sys.path.insert(0, str(PERSIST.parent))
        self.addCleanup(sys.path.remove, str(PERSIST.parent))
        spec = importlib.util.spec_from_file_location("persist_plan_interrupted", PERSIST)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        with mock.patch.object(module.os, "link", side_effect=OSError(5, "interrupted")):
            with self.assertRaises(module.PersistenceError):
                module.publish(self.root, self.plan)
        target = self.root / self.digest
        self.assertFalse((target / "plan.json").exists())
        self.assertEqual([item.name for item in target.iterdir()], [])

    def test_publication_creates_only_under_explicit_root(self):
        import importlib.util

        sys.path.insert(0, str(PERSIST.parent))
        self.addCleanup(sys.path.remove, str(PERSIST.parent))
        spec = importlib.util.spec_from_file_location("persist_plan_audit", PERSIST)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        observed = []
        original = module.os.mkdir

        def recording_mkdir(path, mode=0o777, *, dir_fd=None):
            observed.append((path, dir_fd))
            return original(path, mode, dir_fd=dir_fd)

        with mock.patch.object(module.os, "mkdir", side_effect=recording_mkdir):
            module.publish(self.root, self.plan)
        self.assertEqual([item[0] for item in observed], [self.root.name, self.digest])
        self.assertTrue(all(item[1] is not None for item in observed))

    def test_killed_process_leaves_no_partial_final_and_fresh_writer_recovers(self):
        (self.directory / "unrelated-cwd").mkdir()
        ready_read, ready_write = os.pipe()
        wrapper = (
            "import os,runpy,signal,sys; fd=int(sys.argv[1]); script=sys.argv[2]; "
            "original=os.link; "
            "os.link=lambda *a,**k:(os.write(fd,b'1'),os.kill(os.getpid(),signal.SIGSTOP),original(*a,**k))[2]; "
            "sys.path.insert(0,os.path.dirname(script)); sys.argv=[script,*sys.argv[3:]]; runpy.run_path(script,run_name='__main__')"
        )
        writer = subprocess.Popen(
            [sys.executable, "-B", "-c", wrapper, str(ready_write), str(PERSIST), "--plan-root", str(self.root), "-"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            cwd=self.directory / "unrelated-cwd",
            pass_fds=(ready_write,),
        )
        os.close(ready_write)
        try:
            assert writer.stdin is not None
            writer.stdin.write(json.dumps(self.plan))
            writer.stdin.close()
            self.assertEqual(os.read(ready_read, 1), b"1")
            target = self.root / self.digest
            self.assertFalse((target / "plan.json").exists())
            writer.kill()
            writer.wait(timeout=10)
        finally:
            if writer.poll() is None:
                writer.kill()
                writer.wait(timeout=10)
            for stream in (writer.stdin, writer.stdout, writer.stderr):
                if stream is not None and not stream.closed:
                    stream.close()
            os.close(ready_read)
        code, result = self.persist("-", value=self.plan)
        self.assertEqual(code, 0, result)
        self.assertTrue((self.root / self.digest / "plan.json").is_file())
        self.assertTrue(list((self.root / self.digest).glob(".plan-*.tmp")))

    def test_size_bound_and_unavailable_storage_have_distinct_inline_decisions(self):
        (self.directory / "unrelated-cwd").mkdir()
        oversized = json.dumps(self.plan) + (" " * (4 * 64 * 1024 + 1))
        result = subprocess.run(
            [sys.executable, "-B", str(PERSIST), "--plan-root", str(self.root), "-"],
            input=oversized, cwd=self.directory / "unrelated-cwd", capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["blocked"], "blocked:missing_input")
        unavailable = subprocess.run(
            [sys.executable, "-B", str(PERSIST), "--plan-root", "/proc/planning-policy-plans", "-"],
            input=json.dumps(self.plan), cwd=self.directory / "unrelated-cwd",
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(unavailable.returncode, 2, unavailable.stdout)
        self.assertEqual(json.loads(unavailable.stdout)["blocked"], "blocked:persistence_unavailable")
        inline = {
            "schema": "planning-approval-handoff-v1",
            "plan_sha256": self.digest,
            "plan": self.plan,
        }
        self.assertEqual(self.resolve(inline)["plan"], self.plan)
        code, unavailable = self.persist("-", value=self.plan, env={"PATH": ""})
        self.assertEqual(code, 0, unavailable)
        self.assertFalse(self.resolve(unavailable)["validation"]["dispatch_ready"])

    def test_exact_raw_and_canonical_limits_accept_then_one_byte_over_rejects(self):
        (self.directory / "unrelated-cwd").mkdir()
        exact_raw = json.dumps(self.plan)
        exact_raw += " " * (4 * 64 * 1024 - len(exact_raw))
        command = [sys.executable, "-B", str(PERSIST), "--plan-root", str(self.root), "-"]
        accepted = subprocess.run(command, input=exact_raw, cwd=self.directory / "unrelated-cwd", capture_output=True, text=True, timeout=10)
        self.assertEqual(accepted.returncode, 0, accepted.stdout)
        too_raw = subprocess.run(command, input=exact_raw + " ", cwd=self.directory / "unrelated-cwd", capture_output=True, text=True, timeout=10)
        self.assertEqual(too_raw.returncode, 1)
        exact_canonical = self.plan_with_canonical_size(64 * 1024)
        root = self.directory / "canonical-root"
        exact = subprocess.run([sys.executable, "-B", str(PERSIST), "--plan-root", str(root), "-"], input=json.dumps(exact_canonical), cwd=self.directory / "unrelated-cwd", capture_output=True, text=True, timeout=10)
        self.assertEqual(exact.returncode, 0, exact.stdout)
        too_canonical = self.plan_with_canonical_size(64 * 1024 + 1)
        rejected = subprocess.run([sys.executable, "-B", str(PERSIST), "--plan-root", str(self.directory / "too-canonical"), "-"], input=json.dumps(too_canonical), cwd=self.directory / "unrelated-cwd", capture_output=True, text=True, timeout=10)
        self.assertEqual(rejected.returncode, 1)
        self.assertEqual(json.loads(rejected.stdout)["blocked"], "blocked:missing_input")

    @unittest.skipUnless(shutil.which("bwrap"), "bwrap is unavailable")
    def test_read_only_install_home_and_git_need_only_the_explicit_bound_root(self):
        (self.directory / "unrelated-cwd").mkdir()
        self.root.mkdir()
        command = [
            "bwrap", "--ro-bind", "/", "/", "--bind", str(self.root), str(self.root),
            "--chdir", str(self.directory / "unrelated-cwd"),
            "--setenv", "PATH", "", sys.executable, "-B", str(PERSIST), "--plan-root", str(self.root), "-",
        ]
        result = subprocess.run(command, input=json.dumps(self.plan), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.resolve(json.loads(result.stdout))["plan"], self.plan)


if __name__ == "__main__":
    unittest.main()
