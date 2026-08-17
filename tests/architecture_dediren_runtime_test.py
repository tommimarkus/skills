"""Coverage for the Dediren runtime resolver and provisioner.

These are pure unit tests over `dediren_runtime.py` against a fabricated
release, so they run everywhere without network access. The live-network smoke
lane stays in `architecture_dediren_release_test.py` behind
`DEDIREN_RUNTIME_SMOKE=1`.
"""

import errno
import hashlib
import importlib.util
import io
import os
import subprocess
import tarfile
import tempfile
import threading
import time
import unittest
from unittest import mock
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = (
    REPO_ROOT
    / "souroldgeezer-architecture"
    / "skills"
    / "architecture-design"
    / "references"
    / "scripts"
)
RUNTIME_MODULE_PATH = SCRIPT_DIR / "dediren_runtime.py"
MCP_LAUNCHER = SCRIPT_DIR / "dediren-mcp.sh"


def load_runtime() -> Any:
    """Import the shipped module by path; it is a bundled resource, not a package."""
    spec = importlib.util.spec_from_file_location("dediren_runtime", RUNTIME_MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load_runtime()


def fake_release(
    version: str,
    *,
    members: Callable[[tarfile.TarFile], None] | None = None,
) -> tuple[bytes, str]:
    """Build a release archive and its SHA256SUMS body."""
    archive_name = f"dediren-agent-bundle-{version}.tar.xz"
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:xz") as archive:
        if members is not None:
            members(archive)
        else:
            root = f"dediren-agent-bundle-{version}"
            launcher = b"#!/usr/bin/env bash\nprintf 'FAKE %s\\n' \"$*\"\n"
            info = tarfile.TarInfo(f"{root}/bin/dediren")
            info.size = len(launcher)
            info.mode = 0o755
            archive.addfile(info, io.BytesIO(launcher))
            manifest = b'{"version": "%s"}' % version.encode()
            info = tarfile.TarInfo(f"{root}/bundle.json")
            info.size = len(manifest)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(manifest))
    payload = buffer.getvalue()
    checksums = (
        f"{hashlib.sha256(payload).hexdigest()}  {archive_name}\n"
        f"{'0' * 64}  dediren-{version}.cdx.json\n"
    )
    return payload, checksums


def stub_fetch(payload: bytes, checksums: str) -> Callable[[str, float], bytes]:
    def fetch(url: str, _total_timeout: float) -> bytes:
        if url.endswith("/SHA256SUMS"):
            return checksums.encode()
        return payload

    return fetch


class DataHomeResolutionTest(unittest.TestCase):
    def test_explicit_home_wins_over_every_host_variable(self) -> None:
        env = {
            "DEDIREN_HOME": "/opt/dediren",
            "CLAUDE_PLUGIN_DATA": "/claude",
            "COPILOT_PLUGIN_DATA": "/copilot",
            "PLUGIN_DATA": "/codex",
        }
        self.assertEqual(runtime.data_home(env), Path("/opt/dediren"))

    def test_each_host_variable_resolves_to_its_own_plugin_data_directory(self) -> None:
        for variable, root in (
            ("CLAUDE_PLUGIN_DATA", "/claude/data"),
            ("COPILOT_PLUGIN_DATA", "/copilot/data"),
            ("PLUGIN_DATA", "/codex/data"),
        ):
            with self.subTest(variable=variable):
                self.assertEqual(
                    runtime.data_home({variable: root}), Path(root) / "dediren"
                )

    def test_relative_home_is_refused_rather_than_silently_resolved(self) -> None:
        with self.assertRaises(runtime.DedirenError) as caught:
            runtime.data_home({"DEDIREN_HOME": "relative/path"})
        self.assertEqual(caught.exception.code, runtime.EXIT_CONFIG)

    def test_no_host_directory_yields_none_rather_than_a_guessed_location(self) -> None:
        # A guessed fallback is worse than none: the launcher runs as a host
        # process while the same scripts under an agent's shell tool may be
        # sandboxed, so a fallback can strand the bundle where the host never
        # looks.
        self.assertIsNone(runtime.data_home({}))

    def test_relative_host_variable_is_ignored_rather_than_used(self) -> None:
        self.assertIsNone(runtime.data_home({"CLAUDE_PLUGIN_DATA": "not/absolute"}))

    def test_unexpanded_token_falls_through_instead_of_failing_the_resolve(self) -> None:
        # Hosts differ in which config fields interpolate ${...}; Copilot, for
        # one, documents env substitution for LSP servers only. A manifest value
        # the host passed through verbatim must not poison resolution — the
        # host's own exported variable still gets its turn.
        env = {
            "DEDIREN_HOME": "${COPILOT_PLUGIN_DATA}/dediren",
            "COPILOT_PLUGIN_DATA": "/copilot/data",
        }
        self.assertEqual(runtime.data_home(env), Path("/copilot/data/dediren"))

    def test_every_lane_unexpanded_yields_none_not_a_literal_path(self) -> None:
        env = {
            "DEDIREN_HOME": "${COPILOT_PLUGIN_DATA}/dediren",
            "COPILOT_PLUGIN_DATA": "${SOMETHING_ELSE}",
        }
        self.assertIsNone(runtime.data_home(env))


class VersionFloorTest(unittest.TestCase):
    def test_latest_adopted_release_is_the_shipped_default(self) -> None:
        self.assertEqual(runtime.DEDIREN_VERSION_DEFAULT, "2026.08.6")

    def test_shipped_pin_satisfies_the_shipped_floor(self) -> None:
        self.assertTrue(runtime.meets_floor(runtime.DEDIREN_VERSION_DEFAULT))

    def test_below_floor_override_is_refused_with_the_reason(self) -> None:
        with self.assertRaises(runtime.DedirenError) as caught:
            runtime.pinned_version({"DEDIREN_VERSION": "2026.07.01"})
        self.assertEqual(caught.exception.code, runtime.EXIT_CONFIG)
        self.assertIn(runtime.DEDIREN_VERSION_FLOOR, str(caught.exception))

    def test_non_calver_override_is_refused(self) -> None:
        with self.assertRaises(runtime.DedirenError):
            runtime.pinned_version({"DEDIREN_VERSION": "1.2.3"})


class ProvisioningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_fetch = runtime.fetch
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / "plugin-data" / "dediren"
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(lambda: setattr(runtime, "fetch", self.original_fetch))

    def test_verified_release_installs_into_the_plugin_data_directory(self) -> None:
        version = runtime.DEDIREN_VERSION_DEFAULT
        payload, checksums = fake_release(version)
        runtime.fetch = stub_fetch(payload, checksums)

        launcher = runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)

        self.assertEqual(launcher, runtime.bundle_launcher(runtime.bundle_dir(self.home, version)))
        self.assertTrue(os.access(launcher, os.X_OK))
        self.assertTrue((runtime.bundle_dir(self.home, version) / "bundle.json").is_file())

    def test_second_call_is_a_no_op_that_never_touches_the_network(self) -> None:
        version = runtime.DEDIREN_VERSION_DEFAULT
        payload, checksums = fake_release(version)
        runtime.fetch = stub_fetch(payload, checksums)
        runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)

        def refuse(url: str, _total_timeout: float) -> bytes:
            raise AssertionError(f"warm resolve must not fetch {url}")

        runtime.fetch = refuse
        self.assertIsNotNone(runtime.installed_launcher(self.home, version))
        runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)

    def test_checksum_mismatch_refuses_the_archive_and_installs_nothing(self) -> None:
        version = runtime.DEDIREN_VERSION_DEFAULT
        payload, checksums = fake_release(version)
        tampered = payload + b"tampered"
        runtime.fetch = stub_fetch(tampered, checksums)

        with self.assertRaises(runtime.DedirenError) as caught:
            runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)

        self.assertIn("checksum mismatch", str(caught.exception))
        self.assertIsNone(runtime.installed_launcher(self.home, version))

    def test_checksums_naming_no_bundle_is_refused(self) -> None:
        with self.assertRaises(runtime.DedirenError):
            runtime.archive_name_from_checksums(f"{'0' * 64}  README.md\n", "2026.08.2")

    def test_checksums_naming_two_bundles_is_refused(self) -> None:
        body = (
            f"{'0' * 64}  dediren-agent-bundle-2026.08.2.tar.xz\n"
            f"{'1' * 64}  dediren-agent-bundle-2026.08.2.tar.gz\n"
        )
        with self.assertRaises(runtime.DedirenError):
            runtime.archive_name_from_checksums(body, "2026.08.2")

    def test_concurrent_provisioning_installs_exactly_one_bundle(self) -> None:
        # Several sessions can start against one plugin data directory at once,
        # so the install must be serialised: a lost race would otherwise let one
        # resolver observe another's half-extracted bundle.
        version = runtime.DEDIREN_VERSION_DEFAULT
        payload, checksums = fake_release(version)
        downloads = []
        underlying = stub_fetch(payload, checksums)

        def counting_fetch(url: str, total_timeout: float) -> bytes:
            if not url.endswith("/SHA256SUMS"):
                downloads.append(url)
                time.sleep(0.05)  # widen the window a lost race would exploit
            return underlying(url, total_timeout)

        runtime.fetch = counting_fetch
        results: list[Path] = []
        errors: list[BaseException] = []

        def worker() -> None:
            try:
                results.append(
                    runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)
                )
            except BaseException as exc:  # noqa: BLE001 - surfaced by the assertion below
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)

        self.assertEqual(errors, [])
        self.assertEqual(len(results), 4)
        self.assertEqual(len(set(results)), 1)
        self.assertEqual(len(downloads), 1, "the install ran more than once")
        self.assertTrue(os.access(results[0], os.X_OK))

    def test_archive_without_a_single_top_level_directory_is_refused(self) -> None:
        version = runtime.DEDIREN_VERSION_DEFAULT

        def flat(archive: tarfile.TarFile) -> None:
            body = b"loose"
            info = tarfile.TarInfo("dediren")
            info.size = len(body)
            archive.addfile(info, io.BytesIO(body))

        payload, checksums = fake_release(version, members=flat)
        runtime.fetch = stub_fetch(payload, checksums)

        with self.assertRaises(runtime.DedirenError):
            runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)

    def test_invalid_staged_bundle_does_not_replace_an_incomplete_existing_target(self) -> None:
        """A broken download must not destroy a recoverable incomplete bundle."""
        version = runtime.DEDIREN_VERSION_DEFAULT
        target = runtime.bundle_dir(self.home, version)
        target.mkdir(parents=True)
        marker = target / "keep-me"
        marker.write_text("incomplete", encoding="utf-8")

        def missing_manifest(archive: tarfile.TarFile) -> None:
            launcher = b"#!/usr/bin/env bash\nexit 0\n"
            info = tarfile.TarInfo(f"dediren-agent-bundle-{version}/bin/dediren")
            info.size = len(launcher)
            info.mode = 0o755
            archive.addfile(info, io.BytesIO(launcher))

        payload, checksums = fake_release(version, members=missing_manifest)
        runtime.fetch = stub_fetch(payload, checksums)

        with self.assertRaises(runtime.DedirenError):
            runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)

        self.assertEqual(marker.read_text(encoding="utf-8"), "incomplete")

    def test_launcher_is_made_executable_before_atomic_publication(self) -> None:
        version = runtime.DEDIREN_VERSION_DEFAULT

        def non_executable_launcher(archive: tarfile.TarFile) -> None:
            root = f"dediren-agent-bundle-{version}"
            launcher = b"#!/usr/bin/env bash\nexit 0\n"
            info = tarfile.TarInfo(f"{root}/bin/dediren")
            info.size = len(launcher)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(launcher))
            manifest = b'{}'
            info = tarfile.TarInfo(f"{root}/bundle.json")
            info.size = len(manifest)
            archive.addfile(info, io.BytesIO(manifest))

        payload, checksums = fake_release(version, members=non_executable_launcher)
        runtime.fetch = stub_fetch(payload, checksums)
        target = runtime.bundle_dir(self.home, version)
        replace = runtime.os.replace

        def assert_staged_launcher_is_executable(source: object, destination: object) -> None:
            if Path(destination) == target:
                self.assertTrue(os.access(Path(source) / "bin" / "dediren", os.X_OK))
            replace(source, destination)

        with mock.patch.object(runtime.os, "replace", side_effect=assert_staged_launcher_is_executable):
            runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)

    def test_publish_failure_restores_quarantined_incomplete_target(self) -> None:
        version = runtime.DEDIREN_VERSION_DEFAULT
        target = runtime.bundle_dir(self.home, version)
        target.mkdir(parents=True)
        marker = target / "incomplete-before-publish"
        marker.write_text("recover me", encoding="utf-8")
        payload, checksums = fake_release(version)
        runtime.fetch = stub_fetch(payload, checksums)
        replace = runtime.os.replace
        publication_attempted = False

        def fail_only_the_staged_publication(source: object, destination: object) -> None:
            nonlocal publication_attempted
            if Path(destination) == target and not publication_attempted:
                publication_attempted = True
                raise OSError("simulated publication failure")
            replace(source, destination)

        with mock.patch.object(runtime.os, "replace", side_effect=fail_only_the_staged_publication):
            with self.assertRaises(runtime.DedirenError):
                runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)

        self.assertEqual(marker.read_text(encoding="utf-8"), "recover me")

    def test_lock_timeout_is_fatal_and_never_provisions_unlocked(self) -> None:
        version = runtime.DEDIREN_VERSION_DEFAULT
        payload, checksums = fake_release(version)
        runtime.fetch = stub_fetch(payload, checksums)
        original_wait = runtime.LOCK_WAIT_SECONDS
        runtime.LOCK_WAIT_SECONDS = 0
        self.addCleanup(lambda: setattr(runtime, "LOCK_WAIT_SECONDS", original_wait))

        with mock.patch.object(runtime.fcntl, "flock", side_effect=OSError(errno.EAGAIN, "busy")):
            with self.assertRaises(runtime.DedirenError):
                runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)

        self.assertFalse(runtime.bundle_dir(self.home, version).exists())

    def test_unexpected_lock_error_is_fatal_and_never_provisions_unlocked(self) -> None:
        version = runtime.DEDIREN_VERSION_DEFAULT
        payload, checksums = fake_release(version)
        runtime.fetch = stub_fetch(payload, checksums)

        with mock.patch.object(runtime.fcntl, "flock", side_effect=OSError(errno.EPERM, "not permitted")):
            with self.assertRaises(runtime.DedirenError):
                runtime.provision(self.home, version, runtime.DEDIREN_REPO_DEFAULT)

        self.assertFalse(runtime.bundle_dir(self.home, version).exists())


class ExtractionSafetyTest(unittest.TestCase):
    """A checksum proves the archive is the published one, not that it is safe.

    `tarfile`'s own extraction filters are not available across the range of
    host interpreters this runs under, so the guard is hand-written and has to
    be tested directly.
    """

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.destination = Path(self.temp.name) / "unpacked"
        self.addCleanup(self.temp.cleanup)

    def extract_archive(self, build: Callable[[tarfile.TarFile], None]) -> None:
        archive_path = Path(self.temp.name) / "payload.tar"
        with tarfile.open(archive_path, "w") as archive:
            build(archive)
        runtime.extract(archive_path, self.destination)

    def test_absolute_member_path_is_refused(self) -> None:
        def build(archive: tarfile.TarFile) -> None:
            info = tarfile.TarInfo("/etc/passwd")
            info.size = 0
            archive.addfile(info, io.BytesIO(b""))

        with self.assertRaises(runtime.DedirenError) as caught:
            self.extract_archive(build)
        self.assertIn("absolute path", str(caught.exception))

    def test_parent_traversal_member_is_refused(self) -> None:
        def build(archive: tarfile.TarFile) -> None:
            info = tarfile.TarInfo("bundle/../../escape")
            info.size = 0
            archive.addfile(info, io.BytesIO(b""))

        with self.assertRaises(runtime.DedirenError) as caught:
            self.extract_archive(build)
        self.assertIn("parent traversal", str(caught.exception))

    def test_symlink_escaping_the_destination_is_refused(self) -> None:
        def build(archive: tarfile.TarFile) -> None:
            info = tarfile.TarInfo("bundle/evil")
            info.type = tarfile.SYMTYPE
            info.linkname = "../../../../etc/passwd"
            archive.addfile(info)

        with self.assertRaises(runtime.DedirenError) as caught:
            self.extract_archive(build)
        self.assertIn("escapes the destination", str(caught.exception))

    def test_absolute_symlink_target_is_refused(self) -> None:
        def build(archive: tarfile.TarFile) -> None:
            info = tarfile.TarInfo("bundle/evil")
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            archive.addfile(info)

        with self.assertRaises(runtime.DedirenError):
            self.extract_archive(build)

    def test_device_member_is_refused(self) -> None:
        def build(archive: tarfile.TarFile) -> None:
            info = tarfile.TarInfo("bundle/null")
            info.type = tarfile.CHRTYPE
            info.devmajor = 1
            info.devminor = 3
            archive.addfile(info)

        with self.assertRaises(runtime.DedirenError) as caught:
            self.extract_archive(build)
        self.assertIn("non-file", str(caught.exception))

    def test_contained_symlink_is_allowed(self) -> None:
        # The guard must refuse escapes without breaking a legitimate bundle
        # that ships an internal relative symlink.
        def build(archive: tarfile.TarFile) -> None:
            body = b"real"
            info = tarfile.TarInfo("bundle/lib/real.jar")
            info.size = len(body)
            archive.addfile(info, io.BytesIO(body))
            link = tarfile.TarInfo("bundle/lib/alias.jar")
            link.type = tarfile.SYMTYPE
            link.linkname = "real.jar"
            archive.addfile(link)

        self.extract_archive(build)
        self.assertTrue((self.destination / "bundle" / "lib" / "alias.jar").is_symlink())


class JavaDiagnosticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        runtime._java_verified = False
        self.addCleanup(lambda: setattr(runtime, "_java_verified", False))

    def fake_java(self, version_line: str) -> str:
        java = Path(self.temp.name) / "java"
        java.write_text(
            "#!/usr/bin/env bash\n" f"printf '{version_line}\\n' >&2\n", encoding="utf-8"
        )
        java.chmod(0o755)
        return str(java)

    def test_too_old_runtime_names_the_detected_major_version(self) -> None:
        java = self.fake_java('openjdk version "17.0.9" 2023-10-17')
        with self.assertRaises(runtime.DedirenError) as caught:
            runtime.require_java_21({"JAVACMD": java})
        message = str(caught.exception)
        self.assertIn("Java 17", message)
        self.assertIn("21", message)

    def test_absent_runtime_says_so_precisely(self) -> None:
        env = {
            "JAVACMD": "",
            "PATH": self.temp.name,
            "SDKMAN_DIR": str(Path(self.temp.name) / "absent-sdkman"),
        }
        with self.assertRaises(runtime.DedirenError) as caught:
            runtime.require_java_21(env)
        self.assertIn("no Java runtime found", str(caught.exception))

    def test_supported_runtime_passes(self) -> None:
        java = self.fake_java('openjdk version "21.0.2" 2024-01-16')
        runtime.require_java_21({"JAVACMD": java})

    def test_legacy_dotted_version_string_reads_the_second_field(self) -> None:
        java = self.fake_java('java version "1.8.0_392"')
        self.assertEqual(runtime.java_major_version(java), 8)


class ResolutionOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.empty_path = str(self.root / "empty-bin")
        (self.root / "empty-bin").mkdir()

    def executable(self, path: Path, version: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "#!/usr/bin/env bash\n"
            f"printf 'dediren {version}\\n'\n",
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    def managed_install(self, home: Path, version: str) -> Path:
        bundle = runtime.bundle_dir(home, version)
        (bundle / "bundle.json").parent.mkdir(parents=True, exist_ok=True)
        (bundle / "bundle.json").write_text("{}", encoding="utf-8")
        return self.executable(runtime.bundle_launcher(bundle), version)

    def test_explicit_command_outranks_a_managed_install(self) -> None:
        home = self.root / "data"
        self.managed_install(home, runtime.DEDIREN_VERSION_DEFAULT)
        explicit = self.executable(self.root / "explicit" / "dediren", "2026.08.2")

        resolved = runtime.resolve(
            {"DEDIREN_COMMAND": str(explicit), "DEDIREN_HOME": str(home), "PATH": self.empty_path}
        )

        self.assertEqual(resolved, explicit.resolve())

    def test_managed_install_outranks_a_path_install(self) -> None:
        home = self.root / "data"
        managed = self.managed_install(home, runtime.DEDIREN_VERSION_DEFAULT)
        path_dir = self.root / "path-bin"
        self.executable(path_dir / "dediren", "2026.08.2")

        resolved = runtime.resolve({"DEDIREN_HOME": str(home), "PATH": str(path_dir)})

        self.assertEqual(resolved, managed)

    def test_path_install_below_the_floor_is_skipped(self) -> None:
        path_dir = self.root / "path-bin"
        self.executable(path_dir / "dediren", "2026.07.01")
        env = {
            "DEDIREN_HOME": str(self.root / "data"),
            "PATH": str(path_dir),
            "XDG_CACHE_HOME": str(self.root / "no-cache"),
            "DEDIREN_AUTO_INSTALL": "0",
        }

        with self.assertRaises(runtime.DedirenError) as caught:
            runtime.resolve(env)

        # Reaching the auto-install refusal proves the stale PATH copy did not
        # shadow the pin: a below-floor render fails the skill's post-render step
        # rather than failing here, so it must never win.
        self.assertEqual(caught.exception.code, runtime.EXIT_NOT_FOUND)
        self.assertIn("DEDIREN_AUTO_INSTALL", str(caught.exception))

    def test_path_install_at_or_above_the_floor_is_used(self) -> None:
        path_dir = self.root / "path-bin"
        expected = self.executable(path_dir / "dediren", "2026.08.2")

        resolved = runtime.resolve(
            {"DEDIREN_HOME": str(self.root / "data"), "PATH": str(path_dir)}
        )

        self.assertEqual(resolved, expected)

    def test_legacy_cache_is_still_honoured_for_migrating_hosts(self) -> None:
        cache = self.root / "cache"
        self.executable(
            cache / "dediren" / "releases" / "dediren-agent-bundle-2026.08.1" / "bin" / "dediren",
            "2026.08.1",
        )

        resolved = runtime.resolve(
            {
                "DEDIREN_HOME": str(self.root / "data"),
                "PATH": self.empty_path,
                "XDG_CACHE_HOME": str(cache),
                "HOME": str(self.root),
            }
        )

        self.assertEqual(resolved.name, "dediren")
        self.assertIn("2026.08.1", str(resolved))

    def test_missing_data_directory_and_no_runtime_exits_config(self) -> None:
        env = {
            "PATH": self.empty_path,
            "XDG_CACHE_HOME": str(self.root / "no-cache"),
            "HOME": str(self.root / "no-home"),
        }

        with self.assertRaises(runtime.DedirenError) as caught:
            runtime.resolve(env)

        self.assertEqual(caught.exception.code, runtime.EXIT_CONFIG)
        self.assertIn("DEDIREN_HOME", str(caught.exception))

    def test_resolve_only_mode_never_provisions(self) -> None:
        env = {
            "DEDIREN_HOME": str(self.root / "data"),
            "PATH": self.empty_path,
            "XDG_CACHE_HOME": str(self.root / "no-cache"),
            "HOME": str(self.root / "no-home"),
        }

        with self.assertRaises(runtime.DedirenError) as caught:
            runtime.resolve(env, allow_install=False)

        self.assertEqual(caught.exception.code, runtime.EXIT_NOT_FOUND)
        self.assertFalse((self.root / "data").exists())


class LauncherContractTest(unittest.TestCase):
    def test_launcher_delegates_resolution_to_the_runtime_module(self) -> None:
        script = MCP_LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("dediren_runtime.py", script)
        self.assertIn("--exec-upstream", script)
        # Resolution and provisioning live in one tested place, so the shell
        # launcher must not grow a second copy of either.
        self.assertNotIn("DEDIREN_COMMAND", script)
        self.assertNotIn("curl", script)
        self.assertNotIn("XDG_CACHE_HOME", script)

    def test_router_lane_answers_initialize_without_resolving_dediren(self) -> None:
        # Codex's Agent Plugins lane has no MCP startup-timeout field and falls
        # back to a 30s default, so the handshake must not wait on resolution or
        # provisioning; those happen later, on the first tools/list.
        request = (
            '{"jsonrpc":"2.0","id":1,"method":"initialize","params":'
            '{"protocolVersion":"2025-06-18","capabilities":{},'
            '"clientInfo":{"name":"probe","version":"1"}}}\n'
        )
        # Keep the real PATH so the shell itself resolves; the point of the test
        # is that the handshake completes with no runtime available at all.
        env = {
            **os.environ,
            "DEDIREN_HOME": self.missing_home(),
            "DEDIREN_AUTO_INSTALL": "0",
        }
        env.pop("DEDIREN_COMMAND", None)

        result = subprocess.run(
            ["bash", str(MCP_LAUNCHER)],
            input=request,
            text=True,
            capture_output=True,
            timeout=60,
            env=env,
        )

        self.assertIn('"serverInfo"', result.stdout)
        self.assertIn("dediren-workspace-router", result.stdout)

    def empty_bin(self) -> str:
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: directory.rmdir())
        return str(directory)

    def missing_home(self) -> str:
        base = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: base.rmdir())
        return str(base / "absent")


if __name__ == "__main__":
    unittest.main()
