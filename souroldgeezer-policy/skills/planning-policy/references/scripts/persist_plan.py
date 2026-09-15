#!/usr/bin/env python3
"""Save one approval-ready executable plan beneath an explicit durable root."""

from __future__ import annotations

import argparse
import errno
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

import validate_plan_contract as contract


RAW_PLAN_MAX = 4 * contract.HANDOFF_PLAN_MAX
MKDIR_SUPPORTS_DIR_FD = os.mkdir in os.supports_dir_fd


class PersistenceError(ValueError):
    """A storage failure that may use the documented inline fallback."""


def error(code: str, message: str) -> dict[str, Any]:
    return {"valid": False, "errors": [f"{code}: {message}"], "blocked": code}


def checked_root(value: str) -> Path:
    root = Path(value)
    if not root.is_absolute() or root == Path("/") or ".." in root.parts:
        raise contract.HandoffError("plan root must be an absolute durable directory")
    try:
        resolved = root.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise contract.HandoffError("plan root is unsafe") from exc
    if any(resolved.is_relative_to(item) for item in contract.temporary_roots()):
        raise contract.HandoffError("temporary plan roots are ineligible")
    return root


def private_directory(path: Path) -> int:
    """Create/open a directory path without following any component symlink."""
    if not hasattr(os, "O_NOFOLLOW") or not MKDIR_SUPPORTS_DIR_FD:
        raise PersistenceError("safe directory-descriptor publication is unavailable")
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            try:
                child = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                child = os.open(part, flags, dir_fd=descriptor)
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise contract.HandoffError("plan root contains an unsafe component") from exc
                raise
            os.close(descriptor)
            descriptor = child
            if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise PersistenceError("storage component is not a directory")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def read_published(directory_fd: int, canonical: bytes) -> bool:
    """Accept only a validated, byte-identical existing publication."""
    try:
        descriptor = os.open(
            "plan.json",
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
            dir_fd=directory_fd,
        )
    except FileNotFoundError:
        return False
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise contract.HandoffError("published plan target is unsafe", "blocked:plan_tampered") from exc
        raise
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise contract.HandoffError("published plan target is not a regular file", "blocked:plan_tampered")
        raw = stream.read(RAW_PLAN_MAX + 1)
    if len(raw) > RAW_PLAN_MAX:
        raise contract.HandoffError("published plan exceeds its byte limit", "blocked:plan_tampered")
    try:
        existing = json.loads(raw)
        contract._approval_validation(existing)
    except (ValueError, contract.HandoffError, UnicodeDecodeError) as exc:
        raise contract.HandoffError("published plan is malformed or invalid", "blocked:plan_tampered") from exc
    if raw != canonical:
        raise contract.HandoffError("published plan conflicts with the canonical digest", "blocked:plan_tampered")
    return True


def publish(root: Path, plan: Any) -> Path:
    """Validate first, then atomically create exactly one canonical final file."""
    contract._approval_validation(plan)
    canonical = contract._encoded(plan)
    digest = contract.canonical_plan_sha256(plan)
    root_fd = private_directory(root)
    plan_fd: int | None = None
    staging_name: str | None = None
    try:
        try:
            os.mkdir(digest, mode=0o700, dir_fd=root_fd)
        except FileExistsError:
            pass
        info = os.stat(digest, dir_fd=root_fd, follow_symlinks=False)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise contract.HandoffError("plan digest directory is unsafe", "blocked:plan_tampered")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        try:
            plan_fd = os.open(digest, flags, dir_fd=root_fd)
        except OSError as exc:
            if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise contract.HandoffError("plan digest directory is unsafe", "blocked:plan_tampered") from exc
            raise
        if read_published(plan_fd, canonical):
            return root / digest / "plan.json"
        staging_name = f".plan-{os.getpid()}-{os.urandom(8).hex()}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        stage_fd = os.open(staging_name, flags, 0o600, dir_fd=plan_fd)
        with os.fdopen(stage_fd, "wb") as stream:
            stream.write(canonical)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(staging_name, "plan.json", src_dir_fd=plan_fd, dst_dir_fd=plan_fd, follow_symlinks=False)
        except FileExistsError:
            if not read_published(plan_fd, canonical):
                raise PersistenceError("published plan disappeared during publication")
        os.unlink(staging_name, dir_fd=plan_fd)
        staging_name = None
        os.fsync(plan_fd)
        return root / digest / "plan.json"
    except (OSError, PersistenceError, contract.HandoffError) as exc:
        if staging_name is not None and plan_fd is not None:
            try:
                os.unlink(staging_name, dir_fd=plan_fd)
            except OSError:
                pass
        if isinstance(exc, PersistenceError):
            raise
        if isinstance(exc, contract.HandoffError):
            raise
        if exc.errno in {errno.EACCES, errno.EDQUOT, errno.EIO, errno.ENOSPC, errno.EROFS, errno.ENOTDIR, errno.ELOOP}:
            raise PersistenceError("persistent plan storage is unavailable") from exc
        raise PersistenceError("persistent plan publication failed") from exc
    finally:
        if plan_fd is not None:
            os.close(plan_fd)
        os.close(root_fd)


def verified_reference(root: Path, plan: Any) -> dict[str, Any]:
    """Return an envelope only while its expected path has no symlink component."""
    expected = root / contract.canonical_plan_sha256(plan) / "plan.json"
    current = Path("/")
    for part in expected.parts[1:]:
        current /= part
        info = os.lstat(current)
        if stat.S_ISLNK(info.st_mode):
            raise contract.HandoffError("published reference path is unsafe", "blocked:plan_tampered")
    handoff = contract.emit_handoff(plan, "reference", str(expected))
    if handoff.get("plan_path") != str(expected):
        raise contract.HandoffError("published reference path changed", "blocked:plan_tampered")
    contract.resolve_handoff(handoff)
    return handoff


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-root", required=True)
    parser.add_argument("plan", help="regular plan JSON file or - for stdin")
    args = parser.parse_args(argv)
    try:
        plan = contract._read_json_source(args.plan, RAW_PLAN_MAX)
        contract._approval_validation(plan)
    except contract.HandoffError as exc:
        print(json.dumps(error(exc.code, str(exc)), sort_keys=True, separators=(",", ":")))
        return 1
    except (OSError, ValueError, RecursionError):
        print(json.dumps(error("blocked:missing_input", "unreadable or invalid plan input"), sort_keys=True, separators=(",", ":")))
        return 1
    try:
        root = checked_root(args.plan_root)
        publish(root, plan)
    except contract.HandoffError as exc:
        print(json.dumps(error(exc.code, str(exc)), sort_keys=True, separators=(",", ":")))
        return 1
    except (PersistenceError, OSError, ValueError, RecursionError) as exc:
        print(json.dumps(error("blocked:persistence_unavailable", str(exc)), sort_keys=True, separators=(",", ":")))
        return 2
    try:
        handoff = verified_reference(root, plan)
    except contract.HandoffError as exc:
        print(json.dumps(error(exc.code, str(exc)), sort_keys=True, separators=(",", ":")))
        return 1
    except (OSError, ValueError, RecursionError):
        print(json.dumps(error("blocked:missing_input", "published reference cannot be verified"), sort_keys=True, separators=(",", ":")))
        return 1
    print(json.dumps(handoff, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    sys.exit(main())
