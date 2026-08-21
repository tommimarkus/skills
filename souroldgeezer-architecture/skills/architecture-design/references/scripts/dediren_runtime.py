#!/usr/bin/env python3
"""Resolve, and when needed provision, the Dediren runtime for the MCP adapter.

The plugin installs a pinned, checksum-verified Dediren release into the host's
own plugin data directory. It never installs a Java runtime: the release ships
launch scripts and jars with no bundled JRE, so Java 21+ stays a host
prerequisite and is reported precisely when it is missing.

Everything here runs under whatever ``python3`` the host provides, not the
repository's uv-managed interpreter, so the module stays on a low standard
library floor and avoids interpreter-version-dependent behaviour (notably
``tarfile`` extraction filters, which arrived in 3.11.4).
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import os
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable, Sequence

DEDIREN_REPO_DEFAULT = "tommimarkus/dediren"
DEDIREN_VERSION_DEFAULT = "2026.08.9"
# Oldest supported release. From 2026.07.28 the render lane takes each view's
# <title>/<desc> from its own `presentation`, so each rendered view arrives
# labelled and the repo-owned post-render step requires that native name rather
# than injecting one. Resolving an older bundle would produce artifacts that step
# refuses, so refuse the resolve instead, where the message can be legible.
DEDIREN_VERSION_FLOOR = "2026.07.28"

# Exit codes follow sysexits(3) where one applies, so a host surfacing only the
# status still distinguishes "misconfigured" from "nothing runnable found".
EXIT_USAGE = 64
EXIT_UNAVAILABLE = 69
EXIT_CONFIG = 78
EXIT_NOT_FOUND = 127

CONNECT_TIMEOUT_SECONDS = 30.0
CHECKSUMS_TOTAL_TIMEOUT_SECONDS = 30.0
ARCHIVE_TOTAL_TIMEOUT_SECONDS = 300.0
MAX_DOWNLOAD_BYTES = 256 * 1024 * 1024
DOWNLOAD_ATTEMPTS = 3
LOCK_WAIT_SECONDS = 120.0
CALVER_PATTERN = re.compile(r"(?<![0-9.])([0-9]{4})\.([0-9]{2})\.([0-9]+)(?![0-9.])")

INSTALL_DOC = "references/procedures/dediren-install.md"


class DedirenError(Exception):
    """A resolution or provisioning failure with an operator-facing message."""

    def __init__(self, message: str, code: int = EXIT_UNAVAILABLE) -> None:
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------
# Versions
# --------------------------------------------------------------------------


def calver_key(version: str) -> tuple[int, int, int] | None:
    """Sortable key for a full CalVer string, or None when it is not CalVer."""
    match = re.fullmatch(r"([0-9]{4})\.([0-9]{2})\.([0-9]+)", version.strip())
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def meets_floor(version: str) -> bool:
    key = calver_key(version)
    floor = calver_key(DEDIREN_VERSION_FLOOR)
    assert floor is not None, "the compiled-in floor must be CalVer"
    return key is not None and key >= floor


def pinned_version(env: dict[str, str]) -> str:
    """The release to install: the compiled-in pin unless overridden."""
    version = env.get("DEDIREN_VERSION", "").strip() or DEDIREN_VERSION_DEFAULT
    if calver_key(version) is None:
        raise DedirenError(
            f"DEDIREN_VERSION must be CalVer (YYYY.0M.MICRO); got: {version}",
            EXIT_CONFIG,
        )
    if not meets_floor(version):
        raise DedirenError(
            f"Dediren {version} is older than the supported floor "
            f"{DEDIREN_VERSION_FLOOR}. From {DEDIREN_VERSION_FLOOR} the render "
            "itself supplies each view's accessible name, and the post-render "
            f"step refuses an artifact without one. Use {DEDIREN_VERSION_FLOOR} "
            "or newer.",
            EXIT_CONFIG,
        )
    return version


def reported_version(command: str) -> str | None:
    """The CalVer `command --version` reports, or None when it cannot be read."""
    try:
        completed = subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    match = CALVER_PATTERN.search(completed.stdout.decode("utf-8", "replace"))
    return None if match is None else match.group(0)


# --------------------------------------------------------------------------
# Java
# --------------------------------------------------------------------------


def which(name: str, env: dict[str, str]) -> str | None:
    """`shutil.which` against the supplied environment, not the process's.

    Every lookup here has to read the same environment the caller resolved
    everything else from; falling through to the process environment would make
    resolution depend on state the caller never passed.
    """
    return shutil.which(name, path=env.get("PATH"))


def java_command(env: dict[str, str]) -> str | None:
    """Resolve the Java launcher: JAVACMD, JAVA_HOME, sdkman, then PATH."""
    explicit = env.get("JAVACMD", "").strip()
    if explicit:
        return explicit
    java_home = env.get("JAVA_HOME", "").strip()
    if java_home:
        return str(Path(java_home) / "bin" / "java")
    sdkman = Path(
        env.get("SDKMAN_DIR", "").strip() or Path.home() / ".sdkman"
    ) / "candidates/java/current/bin/java"
    if os.access(sdkman, os.X_OK):
        # sdkman is the recommended provisioner and is usually newer than a bare
        # PATH `java`, which is often an older system JDK. Prefer it only when it
        # actually satisfies the floor.
        if (java_major_version(str(sdkman)) or 0) >= 21:
            return str(sdkman)
    return which("java", env)


def java_major_version(command: str) -> int | None:
    try:
        completed = subprocess.run(
            [command, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    match = re.search(
        r'version "([0-9]+)(?:\.([0-9]+))?', completed.stdout.decode("utf-8", "replace")
    )
    if match is None:
        return None
    major = int(match.group(1))
    if major == 1:  # Legacy 1.8-style version strings.
        return int(match.group(2) or 0)
    return major


_java_verified = False


def require_java_21(env: dict[str, str]) -> None:
    """Fail with a precise diagnostic unless a Java 21+ runtime is resolvable.

    Checked before provisioning (so a missing runtime fails before a download)
    and again before exec (so the warm path still names the cause instead of
    letting Dediren's own launcher die without an envelope). The result is
    memoized so those two call sites cost one probe, not two.
    """
    global _java_verified
    if _java_verified:
        return
    command = java_command(env)
    if command is None:
        raise DedirenError(
            "dediren-mcp: no Java runtime found. Dediren ships jars with no "
            "bundled JRE and needs Java 21 or newer as `java`, or an explicit "
            f"JAVA_HOME / JAVACMD. See {INSTALL_DOC}.",
            EXIT_UNAVAILABLE,
        )
    major = java_major_version(command)
    if major is None:
        raise DedirenError(
            f"dediren-mcp: could not read a Java version from {command}. "
            f"Dediren needs Java 21 or newer. See {INSTALL_DOC}.",
            EXIT_UNAVAILABLE,
        )
    if major < 21:
        raise DedirenError(
            f"dediren-mcp: Dediren needs Java 21 or newer; {command} reports "
            f"Java {major}. Install a JDK 21+ and make it visible to the host "
            f"process, or set JAVA_HOME / JAVACMD. See {INSTALL_DOC}.",
            EXIT_UNAVAILABLE,
        )
    _java_verified = True


# --------------------------------------------------------------------------
# Data directory
# --------------------------------------------------------------------------

# Each maintained harness exposes its own per-plugin writable directory to the
# MCP server process. `DEDIREN_HOME` is the operator override and is also what
# each host manifest sets explicitly, so the path is visible in the manifest
# rather than inferred.
PLUGIN_DATA_VARIABLES = ("CLAUDE_PLUGIN_DATA", "COPILOT_PLUGIN_DATA", "PLUGIN_DATA")


def data_home(env: dict[str, str]) -> Path | None:
    """The plugin data directory to install into, or None when none is offered.

    There is deliberately no invented fallback. A guessed location is worse than
    none: the MCP launcher runs as a host process with the real HOME, while the
    same scripts invoked through an agent's shell tool may run sandboxed with
    HOME read-only, so a fallback can strand a bundle exactly where the
    host-side launcher never looks.
    """
    explicit = env.get("DEDIREN_HOME", "").strip()
    if explicit and not unexpanded(explicit, "DEDIREN_HOME"):
        candidate = Path(explicit).expanduser()
        if not candidate.is_absolute():
            raise DedirenError(
                f"DEDIREN_HOME must be an absolute path; got: {explicit}",
                EXIT_CONFIG,
            )
        return candidate
    for variable in PLUGIN_DATA_VARIABLES:
        value = env.get(variable, "").strip()
        if value and not unexpanded(value, variable):
            candidate = Path(value).expanduser()
            if candidate.is_absolute():
                return candidate / "dediren"
    return None


def unexpanded(value: str, variable: str) -> bool:
    """True when a host passed a substitution token through literally.

    Hosts differ in which config fields interpolate `${...}` tokens, and a
    manifest that names one the host does not expand arrives here verbatim.
    Treating that as a configured path would fail the whole resolve on a value
    the operator never chose, so it is skipped — loudly — and the remaining
    lanes still get their turn, including the host's own exported variable.
    """
    if "${" not in value:
        return False
    print(
        f"dediren-mcp: ignoring {variable}; the host did not expand it: {value}",
        file=sys.stderr,
    )
    return True


def releases_dir(home: Path) -> Path:
    return home / "releases"


def bundle_dir(home: Path, version: str) -> Path:
    return releases_dir(home) / f"dediren-agent-bundle-{version}"


def bundle_launcher(bundle: Path) -> Path:
    return bundle / "bin" / "dediren"


def installed_launcher(home: Path, version: str) -> Path | None:
    """The managed install for `version`, when it is present and complete."""
    bundle = bundle_dir(home, version)
    launcher = bundle_launcher(bundle)
    if os.access(launcher, os.X_OK) and (bundle / "bundle.json").is_file():
        return launcher
    return None


def legacy_launcher(env: dict[str, str]) -> Path | None:
    """Newest executable already present in the pre-2026.08 release cache.

    Migration only: nothing populates this path any more. It exists so a host
    that provisioned through the former adapter is not stranded.
    """
    cache_home = env.get("XDG_CACHE_HOME", "").strip()
    root = Path(cache_home) if cache_home else Path.home() / ".cache"
    root = root / "dediren" / "releases"
    best: tuple[tuple[int, int, int], Path] | None = None
    try:
        entries = sorted(root.iterdir())
    except OSError:
        return None
    for bundle in entries:
        if not bundle.name.startswith("dediren-agent-bundle-"):
            continue
        key = calver_key(bundle.name[len("dediren-agent-bundle-") :])
        launcher = bundle_launcher(bundle)
        if key is None or not os.access(launcher, os.X_OK):
            continue
        if best is None or key > best[0]:
            best = (key, launcher)
    return None if best is None else best[1]


# --------------------------------------------------------------------------
# Download and verification
# --------------------------------------------------------------------------


def release_base_url(repo: str, version: str) -> str:
    return f"https://github.com/{repo}/releases/download/v{version}"


def _fetch_with_urllib(url: str, total_timeout: float) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "souroldgeezer-architecture-dediren"}
    )
    deadline = time.monotonic() + total_timeout
    chunks: list[bytes] = []
    received = 0
    with urllib.request.urlopen(request, timeout=CONNECT_TIMEOUT_SECONDS) as response:
        while True:
            if time.monotonic() > deadline:
                raise DedirenError(
                    f"download exceeded {total_timeout:.0f}s: {url}", EXIT_UNAVAILABLE
                )
            chunk = response.read(64 * 1024)
            if not chunk:
                break
            received += len(chunk)
            if received > MAX_DOWNLOAD_BYTES:
                raise DedirenError(
                    f"download exceeded the {MAX_DOWNLOAD_BYTES} byte ceiling: {url}",
                    EXIT_UNAVAILABLE,
                )
            chunks.append(chunk)
    return b"".join(chunks)


def _fetch_with_external_client(url: str, total_timeout: float) -> bytes:
    """Fallback for hosts where Python has no usable TLS trust store.

    python.org macOS builds ship without the system roots wired up, so urllib
    can fail certificate verification where the platform's own HTTPS clients
    succeed. This lane exists only for that case.
    """
    with tempfile.TemporaryDirectory(prefix="dediren-fetch-") as scratch:
        target = Path(scratch) / "payload"
        clients: list[list[str]] = []
        if shutil.which("curl"):
            clients.append(
                [
                    "curl", "-fsSL", "--retry", "2",
                    "--connect-timeout", str(int(CONNECT_TIMEOUT_SECONDS)),
                    "--max-time", str(int(total_timeout)),
                    "-o", str(target), url,
                ]
            )
        if shutil.which("wget"):
            clients.append(
                [
                    "wget", "--quiet", "--tries=2",
                    f"--timeout={int(CONNECT_TIMEOUT_SECONDS)}",
                    "-O", str(target), url,
                ]
            )
        for client in clients:
            try:
                completed = subprocess.run(client, timeout=total_timeout + 30)
            except (OSError, subprocess.SubprocessError):
                continue
            if completed.returncode == 0 and target.is_file():
                return target.read_bytes()
    return b""


def fetch(url: str, total_timeout: float) -> bytes:
    """Fetch `url` with bounded retries, falling back only on a TLS trust failure."""
    last_error: Exception | None = None
    for attempt in range(DOWNLOAD_ATTEMPTS):
        try:
            return _fetch_with_urllib(url, total_timeout)
        except urllib.error.URLError as exc:
            last_error = exc
            reason = getattr(exc, "reason", None)
            if isinstance(reason, ssl.SSLCertVerificationError):
                payload = _fetch_with_external_client(url, total_timeout)
                if payload:
                    return payload
                raise DedirenError(
                    f"TLS certificate verification failed for {url} ({reason}), and "
                    "no working curl or wget was available. On macOS python.org "
                    "builds, run the bundled 'Install Certificates.command' once, "
                    "or install curl.",
                    EXIT_UNAVAILABLE,
                ) from exc
            if isinstance(exc, urllib.error.HTTPError) and 400 <= exc.code < 500:
                raise DedirenError(
                    f"download failed with HTTP {exc.code}: {url}", EXIT_UNAVAILABLE
                ) from exc
        except OSError as exc:
            last_error = exc
        if attempt + 1 < DOWNLOAD_ATTEMPTS:
            time.sleep(1.0 * (attempt + 1))
    raise DedirenError(f"download failed: {url} ({last_error})", EXIT_UNAVAILABLE)


def archive_name_from_checksums(checksums: str, version: str) -> str:
    """Read the bundle's filename out of SHA256SUMS.

    The release names exactly one agent bundle there, extension included, so the
    compression format is read from the release rather than assumed here.
    """
    prefix = f"dediren-agent-bundle-{version}."
    names = [
        line.split()[-1]
        for line in checksums.splitlines()
        if len(line.split()) >= 2 and line.split()[-1].startswith(prefix)
    ]
    if len(names) != 1:
        raise DedirenError(
            f"expected exactly one {prefix}* entry in SHA256SUMS, found {len(names)}",
            EXIT_UNAVAILABLE,
        )
    return names[0]


def expected_digest(checksums: str, archive_name: str) -> str:
    for line in checksums.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[-1].lstrip("*") == archive_name:
            return fields[0].lower()
    raise DedirenError(
        f"no checksum for {archive_name} in SHA256SUMS", EXIT_UNAVAILABLE
    )


def verify_digest(payload: bytes, expected: str, archive_name: str) -> None:
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise DedirenError(
            f"checksum mismatch for {archive_name}\n"
            f"expected: {expected}\nactual:   {actual}",
            EXIT_UNAVAILABLE,
        )


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------


def _contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def safe_members(archive: tarfile.TarFile, destination: Path) -> Iterable[tarfile.TarInfo]:
    """Yield members that are safe to write under `destination`.

    Written by hand rather than relying on ``tarfile``'s extraction filters,
    which are not available across the whole range of host interpreters this
    runs under. Anything that could escape the destination — an absolute path, a
    parent traversal, a link pointing outside, a device or fifo — is refused
    rather than skipped, so a tampered archive fails loudly.
    """
    for member in archive.getmembers():
        name = member.name
        if name.startswith("/") or Path(name).is_absolute():
            raise DedirenError(
                f"refusing archive member with an absolute path: {name}",
                EXIT_UNAVAILABLE,
            )
        if ".." in Path(name).parts:
            raise DedirenError(
                f"refusing archive member with a parent traversal: {name}",
                EXIT_UNAVAILABLE,
            )
        target = (destination / name).resolve()
        if not _contained(destination.resolve(), target):
            raise DedirenError(
                f"refusing archive member that escapes the destination: {name}",
                EXIT_UNAVAILABLE,
            )
        if member.ischr() or member.isblk() or member.isfifo() or member.isdev():
            raise DedirenError(
                f"refusing non-file archive member: {name}", EXIT_UNAVAILABLE
            )
        if member.issym() or member.islnk():
            link = member.linkname
            if Path(link).is_absolute():
                raise DedirenError(
                    f"refusing archive link to an absolute path: {name} -> {link}",
                    EXIT_UNAVAILABLE,
                )
            base = target.parent if member.issym() else destination
            resolved = (base / link).resolve()
            if not _contained(destination.resolve(), resolved):
                raise DedirenError(
                    f"refusing archive link that escapes the destination: "
                    f"{name} -> {link}",
                    EXIT_UNAVAILABLE,
                )
        yield member


def extract(archive_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path) as archive:
        members = list(safe_members(archive, destination))
        for member in members:
            archive.extract(member, path=destination)


# --------------------------------------------------------------------------
# Provisioning
# --------------------------------------------------------------------------


def _locked(lock_path: Path, wait_seconds: float):
    """Take the bounded cross-session lock around the install, or fail safely."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "w")
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return handle
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN):
                handle.close()
                raise DedirenError(
                    f"could not acquire the install lock {lock_path}: {exc}",
                    EXIT_UNAVAILABLE,
                ) from exc
            if time.monotonic() >= deadline:
                handle.close()
                raise DedirenError(
                    f"timed out waiting for the install lock: {lock_path}",
                    EXIT_UNAVAILABLE,
                )
            time.sleep(0.25)


def validate_staged_bundle(bundle: Path) -> Path:
    """Verify required staged files and launcher mode before publication."""
    manifest = bundle / "bundle.json"
    launcher = bundle_launcher(bundle)
    if not manifest.is_file():
        raise DedirenError(f"staged bundle has no manifest at {manifest}", EXIT_UNAVAILABLE)
    if not launcher.is_file():
        raise DedirenError(f"staged bundle has no launcher at {launcher}", EXIT_UNAVAILABLE)
    launcher.chmod(launcher.stat().st_mode | 0o111)
    if not os.access(launcher, os.X_OK):
        raise DedirenError(f"staged bundle launcher is not executable: {launcher}", EXIT_UNAVAILABLE)
    return launcher


def quarantine_path(target: Path) -> Path:
    """Reserve a unique sibling name for an atomic incomplete-target move."""
    reserved = Path(tempfile.mkdtemp(prefix=f".quarantine-{target.name}-", dir=target.parent))
    reserved.rmdir()
    return reserved


def provision(home: Path, version: str, repo: str) -> Path:
    """Install the pinned release into `home`, returning the launcher path."""
    existing = installed_launcher(home, version)
    if existing is not None:
        return existing

    lock = _locked(releases_dir(home) / f".dediren-{version}.lock", LOCK_WAIT_SECONDS)
    try:
        existing = installed_launcher(home, version)
        if existing is not None:
            return existing

        base = release_base_url(repo, version)
        # Checksums first: they name the archive to fetch, so no compression
        # format is assumed, and nothing large is downloaded before the digest
        # that will verify it is in hand.
        checksums = fetch(f"{base}/SHA256SUMS", CHECKSUMS_TOTAL_TIMEOUT_SECONDS).decode(
            "utf-8", "replace"
        )
        archive_name = archive_name_from_checksums(checksums, version)
        digest = expected_digest(checksums, archive_name)
        payload = fetch(f"{base}/{archive_name}", ARCHIVE_TOTAL_TIMEOUT_SECONDS)
        verify_digest(payload, digest, archive_name)

        target = bundle_dir(home, version)
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(prefix=f".extract-{version}-", dir=str(target.parent))
        )
        try:
            archive_path = staging / archive_name
            archive_path.write_bytes(payload)
            unpacked = staging / "unpacked"
            extract(archive_path, unpacked)
            roots = [entry for entry in unpacked.iterdir() if entry.is_dir()]
            if len(roots) != 1:
                raise DedirenError(
                    f"archive did not contain a single top-level bundle directory: "
                    f"{archive_name}",
                    EXIT_UNAVAILABLE,
                )
            staged_bundle = roots[0]
            launcher = validate_staged_bundle(staged_bundle)
            quarantined: Path | None = None
            if target.exists():
                quarantined = quarantine_path(target)
                try:
                    os.replace(target, quarantined)
                except OSError as exc:
                    raise DedirenError(
                        f"could not quarantine incomplete bundle {target}: {exc}",
                        EXIT_UNAVAILABLE,
                    ) from exc
            try:
                os.replace(staged_bundle, target)
            except OSError as exc:
                if quarantined is not None and quarantined.exists():
                    try:
                        os.replace(quarantined, target)
                    except OSError as restore_exc:
                        raise DedirenError(
                            f"could not publish bundle {target}: {exc}; also could not restore "
                            f"quarantined bundle: {restore_exc}",
                            EXIT_UNAVAILABLE,
                        ) from restore_exc
                raise DedirenError(f"could not publish bundle {target}: {exc}", EXIT_UNAVAILABLE) from exc
            if quarantined is not None:
                shutil.rmtree(quarantined)
            launcher = bundle_launcher(target)
        finally:
            shutil.rmtree(staging, ignore_errors=True)

        return launcher
    finally:
        lock.close()


# --------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------


def auto_install_enabled(env: dict[str, str]) -> bool:
    return env.get("DEDIREN_AUTO_INSTALL", "").strip() not in ("0", "false", "no")


def resolve(env: dict[str, str], *, allow_install: bool = True) -> Path:
    """Resolve a runnable Dediren, provisioning the pin when nothing else serves.

    Order: an explicit DEDIREN_COMMAND, the managed install in the plugin data
    directory, a host `dediren` on PATH that meets the floor, the legacy
    migration cache, then provisioning. Only the managed and provisioning lanes
    need a data directory, so a host without one still resolves through the
    others.
    """
    explicit = env.get("DEDIREN_COMMAND", "").strip()
    if explicit:
        # An explicit command is deliberate operator intent, including the case
        # of pinning one executable for controlled validation, so it is honoured
        # without a floor probe.
        if "/" in explicit:
            candidate = Path(explicit).expanduser()
            if not os.access(candidate, os.X_OK):
                raise DedirenError(
                    f"dediren-mcp: DEDIREN_COMMAND is not executable: {explicit}",
                    EXIT_NOT_FOUND,
                )
            return candidate.resolve()
        found = which(explicit, env)
        if found is None:
            raise DedirenError(
                f"dediren-mcp: DEDIREN_COMMAND was not found on PATH: {explicit}",
                EXIT_NOT_FOUND,
            )
        return Path(found)

    home = data_home(env)
    version = pinned_version(env)

    if home is not None:
        managed = installed_launcher(home, version)
        if managed is not None:
            return managed

    on_path = which("dediren", env)
    if on_path is not None:
        # A host install only wins when it satisfies the floor; an older one must
        # not shadow the pin, because below-floor renders fail the skill's own
        # post-render step rather than failing here.
        version_on_path = reported_version(on_path)
        if version_on_path is not None and meets_floor(version_on_path):
            return Path(on_path)

    legacy = legacy_launcher(env)
    if legacy is not None:
        version_legacy = reported_version(str(legacy))
        if version_legacy is not None and meets_floor(version_legacy):
            return legacy

    if home is None:
        raise DedirenError(
            "dediren-mcp: no plugin data directory was offered by the host and no "
            "runtime was found. Set DEDIREN_HOME to an absolute path for the "
            "managed install, or DEDIREN_COMMAND to an existing Dediren "
            f"executable. See {INSTALL_DOC}.",
            EXIT_CONFIG,
        )
    if not allow_install:
        raise DedirenError(
            "dediren-mcp: no Dediren runtime is installed yet. This mode only "
            f"resolves an existing one; use --ensure to provision. See {INSTALL_DOC}.",
            EXIT_NOT_FOUND,
        )
    if not auto_install_enabled(env):
        raise DedirenError(
            "dediren-mcp: no Dediren runtime is installed and automatic "
            "provisioning is disabled by DEDIREN_AUTO_INSTALL. Install the bundle "
            f"manually, or unset that variable. See {INSTALL_DOC}.",
            EXIT_NOT_FOUND,
        )

    require_java_21(env)
    return provision(home, version, env.get("DEDIREN_REPO", "").strip() or DEDIREN_REPO_DEFAULT)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def exec_upstream(env: dict[str, str], root: str, extra: Sequence[str]) -> int:
    workspace = Path(root)
    if not workspace.is_dir():
        print(
            "dediren-mcp: --exec-upstream requires one workspace directory.",
            file=sys.stderr,
        )
        return EXIT_USAGE
    resolved_root = str(workspace.resolve())
    command = resolve(env)
    require_java_21(env)
    argv = [str(command), "mcp", "--root", resolved_root, *extra]
    print(f"dediren-mcp: exec {' '.join(argv)}", file=sys.stderr)
    os.execv(str(command), argv)  # replaces this process; does not return


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dediren_runtime.py",
        description=(
            "Resolve, and when needed provision, the Dediren runtime used by the "
            "architecture-design MCP adapter."
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--ensure",
        action="store_true",
        help="resolve the runtime, provisioning the pinned release if needed, and print its path",
    )
    group.add_argument(
        "--print-path",
        action="store_true",
        help="print the already-resolvable runtime path without touching the network",
    )
    group.add_argument(
        "--home",
        action="store_true",
        help="print the resolved plugin data directory",
    )
    group.add_argument(
        "--version-pin",
        action="store_true",
        help="print the pinned Dediren release and the supported floor",
    )
    group.add_argument(
        "--exec-upstream",
        metavar="WORKSPACE_ROOT",
        help="resolve, then exec `dediren mcp --root WORKSPACE_ROOT` (used by the launcher)",
    )
    parsed, extra = parser.parse_known_args(list(argv) if argv is not None else None)
    env = dict(os.environ)

    try:
        if parsed.version_pin:
            print(f"{pinned_version(env)} (floor {DEDIREN_VERSION_FLOOR})")
            return 0
        if parsed.home:
            home = data_home(env)
            if home is None:
                raise DedirenError(
                    "dediren-mcp: no plugin data directory; set DEDIREN_HOME to an "
                    "absolute path.",
                    EXIT_CONFIG,
                )
            print(home)
            return 0
        if parsed.exec_upstream is not None:
            return exec_upstream(env, parsed.exec_upstream, extra)
        print(resolve(env, allow_install=parsed.ensure))
        return 0
    except DedirenError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    raise SystemExit(main())
