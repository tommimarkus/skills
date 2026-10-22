#!/usr/bin/env python3
"""Bind local-only checks to pushed ``main``; a writer or ``--no-verify`` can bypass them."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

SCHEMA = "publication-check-receipt-v1"
PUBLICATION_REF = "refs/heads/main"
OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
MANIFEST_RE = re.compile(
    r"^souroldgeezer-[a-z-]+/(?:\.claude-plugin/plugin\.json|"
    r"\.codex-plugin/plugin\.json|plugin\.json)$"
)
README_ROW_RE = re.compile(
    r"^(\|\s*`(?P<plugin>souroldgeezer-[a-z-]+)`\s*\|\s*`)"
    r"(?P<version>[^`]+)(`\s*\|.*)$"
)
MAX_RECEIPT_BYTES = 32 * 1024


class Refusal(ValueError):
    """A fail-closed publication refusal suitable for stderr."""


def _run(
    repo: Path, argv: Sequence[str], *, capture: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run([*argv], cwd=repo, text=True, capture_output=capture, check=False)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(repo, ("git", *args))


def _git_value(repo: Path, *args: str) -> str:
    result = _git(repo, *args)
    if result.returncode:
        raise Refusal(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _repo_root(value: str) -> Path:
    root = Path(value).resolve()
    result = _git(root, "rev-parse", "--show-toplevel")
    if result.returncode:
        raise Refusal(f"not a Git worktree: {root}")
    return Path(result.stdout.strip()).resolve()


def _common_dir(repo: Path) -> Path:
    value = Path(_git_value(repo, "rev-parse", "--git-common-dir"))
    return value.resolve() if value.is_absolute() else (repo / value).resolve()


def _receipt_path(repo: Path) -> Path:
    return _common_dir(repo) / "publication-check" / "receipt.json"


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _seal(payload: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(payload)
    sealed["integrity"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return sealed


def _write_receipt(repo: Path, payload: dict[str, Any]) -> None:
    target = _receipt_path(repo)
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temporary.write_bytes(_canonical(_seal(payload)) + b"\n")
    temporary.chmod(0o600)
    os.replace(temporary, target)


def _load_receipt(repo: Path) -> dict[str, Any]:
    path = _receipt_path(repo)
    try:
        if path.stat().st_size > MAX_RECEIPT_BYTES:
            raise Refusal("invalid receipt: file exceeds 32 KiB")
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Refusal(f"invalid receipt: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        raise Refusal("invalid receipt: unsupported schema")
    integrity = receipt.pop("integrity", None)
    expected = hashlib.sha256(_canonical(receipt)).hexdigest()
    receipt["integrity"] = integrity
    if not isinstance(integrity, str) or not hmac.compare_digest(integrity, expected):
        raise Refusal("invalid receipt integrity")
    candidate = receipt.get("candidate")
    if not isinstance(candidate, dict):
        raise Refusal("invalid receipt: candidate is missing")
    if candidate.get("status") != "passed":
        raise Refusal("candidate gates did not pass")
    return receipt


def _gates(*, version_followup: bool = False) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if version_followup:
        return (
            (
                "runtime-metadata-parity",
                (sys.executable, "scripts/check-runtime-metadata-parity.py", "--check", "."),
            ),
            ("version-guard", ("uv", "run", "python", "scripts/version_stamp.py", "guard")),
        )
    return (
        (
            "runtime-metadata-parity",
            (sys.executable, "scripts/check-runtime-metadata-parity.py", "--check", "."),
        ),
        ("fragmentation", ("scripts/validate-fragmentation.sh",)),
        ("skill-architecture", ("scripts/skill-architecture-report.sh", "--strict", ".")),
        (
            "lean-engine",
            (
                "uv",
                "run",
                "python",
                "souroldgeezer-audit/skills/lean-audit/references/scripts/lean_engine.py",
                ".",
            ),
        ),
        (
            "full-suite",
            ("uv", "run", "python", "-m", "unittest", "discover", "-s", "tests", "-p", "*_test.py"),
        ),
        (
            "host-smoke",
            (
                "scripts/check-runtime-host-smoke.py",
                "--fresh",
                "--assert-profile-isolation",
                ".",
            ),
        ),
        ("diff-check", ("git", "diff", "--check")),
        ("version-guard", ("uv", "run", "python", "scripts/version_stamp.py", "guard")),
    )


def _clean_identity(repo: Path) -> tuple[str, str]:
    if _git_value(repo, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise Refusal("candidate worktree is dirty")
    commit = _git_value(repo, "rev-parse", "--verify", "HEAD^{commit}")
    tree = _git_value(repo, "rev-parse", "--verify", "HEAD^{tree}")
    return commit, tree


def _run_gates(
    repo: Path, gates: Sequence[tuple[str, Sequence[str]]]
) -> tuple[list[dict[str, object]], int]:
    evidence: list[dict[str, object]] = []
    for gate_id, argv in gates:
        print(f"publication-check: running {gate_id}", file=sys.stderr, flush=True)
        result = _run(repo, argv, capture=gate_id == "full-suite")
        if gate_id == "full-suite":
            sys.stdout.write(result.stdout)
            sys.stderr.write(result.stderr)
        code = result.returncode
        if gate_id == "full-suite" and re.search(
            r"\bRan 0 tests?\b", result.stdout + result.stderr
        ):
            print("publication-check: full suite collected zero tests", file=sys.stderr)
            code = 1
        evidence.append({"id": gate_id, "exit_code": code})
        if code:
            return evidence, code if 0 < code < 256 else 1
    return evidence, 0


def _ref_text(repo: Path, ref: str, path: str) -> str:
    result = _git(repo, "show", f"{ref}:{path}")
    if result.returncode:
        raise Refusal(f"version follow-up cannot read {path} at {ref}")
    return result.stdout


def _version_only_followup(repo: Path, candidate: str, head: str) -> None:
    if _git(repo, "merge-base", "--is-ancestor", candidate, head).returncode:
        raise Refusal("version follow-up does not descend from the checked candidate")
    if _git_value(repo, "rev-list", "--count", f"{candidate}..{head}") != "1":
        raise Refusal("version follow-up must be one atomic commit")
    paths = _git_value(repo, "diff", "--name-only", candidate, head).splitlines()
    if not paths:
        raise Refusal("version follow-up changed no version cells")
    for path in paths:
        before, after = _ref_text(repo, candidate, path), _ref_text(repo, head, path)
        if path == "README.md":
            old_lines, new_lines = before.splitlines(), after.splitlines()
            if len(old_lines) != len(new_lines):
                raise Refusal("version follow-up changed README structure")
            for old, new in zip(old_lines, new_lines, strict=True):
                if old == new:
                    continue
                old_match, new_match = README_ROW_RE.match(old), README_ROW_RE.match(new)
                if not old_match or not new_match or old_match.group(1, 4) != new_match.group(1, 4):
                    raise Refusal("version follow-up changed README content outside a version cell")
        elif MANIFEST_RE.match(path):
            try:
                old_json, new_json = json.loads(before), json.loads(after)
                old_version, new_version = old_json.pop("version"), new_json.pop("version")
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise Refusal(f"invalid version manifest: {path}") from exc
            if old_json != new_json or old_version == new_version:
                raise Refusal(f"version follow-up changed non-version content: {path}")
        else:
            raise Refusal(f"version follow-up changed disallowed path: {path}")


def cmd_record(repo: Path, version_followup: bool) -> int:
    commit, tree = _clean_identity(repo)
    prior: dict[str, Any] | None = None
    if version_followup:
        prior = _load_receipt(repo)
        candidate = prior["candidate"]["commit"]
        _version_only_followup(repo, candidate, commit)
    pending = {"commit": commit, "tree": tree, "status": "running", "gates": []}
    if version_followup:
        assert prior is not None
        _write_receipt(
            repo,
            {"schema": SCHEMA, "candidate": prior["candidate"], "version_followup": pending},
        )
    else:
        _write_receipt(repo, {"schema": SCHEMA, "candidate": pending})
    gates, code = _run_gates(repo, _gates(version_followup=version_followup))
    if _clean_identity(repo) != (commit, tree):
        raise Refusal("candidate identity or cleanliness changed while gates ran")
    evidence = {
        "commit": commit,
        "tree": tree,
        "status": "passed" if code == 0 else "failed",
        "gates": gates,
    }
    if version_followup:
        assert prior is not None
        payload = {"schema": SCHEMA, "candidate": prior["candidate"], "version_followup": evidence}
    else:
        payload = {"schema": SCHEMA, "candidate": evidence}
    _write_receipt(repo, payload)
    print(f"publication-check: recorded {evidence['status']} evidence for {commit}")
    return code


def _covered_entry(repo: Path, receipt: dict[str, Any], source: str) -> None:
    entries = [receipt["candidate"]]
    followup = receipt.get("version_followup")
    if isinstance(followup, dict) and followup.get("status") == "passed":
        entries.append(followup)
    for entry in entries:
        if entry.get("commit") == source:
            tree = _git_value(repo, "rev-parse", "--verify", f"{source}^{{tree}}")
            if tree != entry.get("tree"):
                raise Refusal("receipt tree does not match the publication source")
            return
    raise Refusal(f"receipt does not cover publication source {source}")


def cmd_check_push(repo: Path) -> int:
    receipt: dict[str, Any] | None = None
    for number, raw in enumerate(sys.stdin, 1):
        fields = raw.split()
        if len(fields) != 4 or not OID_RE.fullmatch(fields[1]) or not OID_RE.fullmatch(fields[3]):
            raise Refusal(f"malformed pre-push record at line {number}")
        _local_ref, source, remote_ref, remote = fields
        if remote_ref != PUBLICATION_REF:
            continue
        if set(source) == {"0"}:
            raise Refusal(f"deletion of {PUBLICATION_REF} is refused")
        if (
            set(remote) != {"0"}
            and _git(repo, "merge-base", "--is-ancestor", remote, source).returncode
        ):
            raise Refusal(f"non-fast-forward update of {PUBLICATION_REF} is refused")
        receipt = receipt or _load_receipt(repo)
        _covered_entry(repo, receipt, source)
        print(f"publication-check: evidence covers {source}", file=sys.stderr)
    return 0


def _hook_paths(repo: Path) -> tuple[Path, Path]:
    return repo / "scripts/git-hooks/pre-push", _common_dir(repo) / "hooks/pre-push"


def cmd_install(repo: Path) -> int:
    source, target = _hook_paths(repo)
    expected = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o755)
    except FileExistsError as exc:
        if target.is_symlink() or target.read_bytes() != expected:
            raise Refusal(f"refusing to overwrite existing hook: {target}") from exc
        target.chmod(0o755)
        print(f"publication-check: hook already installed at {target}")
        return 0
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(expected)
    print(f"publication-check: installed repository hook at {target}")
    return 0


def cmd_uninstall(repo: Path) -> int:
    source, target = _hook_paths(repo)
    if not target.exists() and not target.is_symlink():
        print(f"publication-check: no repository hook at {target}")
        return 0
    if target.is_symlink() or target.read_bytes() != source.read_bytes():
        raise Refusal(f"refusing to remove modified hook: {target}")
    target.unlink()
    print(f"publication-check: removed repository hook at {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record and enforce bypassable local evidence before publishing main."
    )
    parser.add_argument("--repo-root", default=".")
    commands = parser.add_subparsers(dest="command", required=True)
    record = commands.add_parser("record", help="run gates and record exact candidate evidence")
    record.add_argument("--version-followup", action="store_true")
    check = commands.add_parser("check-push", help="validate pre-push records from stdin")
    check.add_argument("remote_name", nargs="?")
    check.add_argument("remote_location", nargs="?")
    commands.add_parser("install-hook", help="install the repo hook without replacing one")
    commands.add_parser("uninstall-hook", help="remove only an unmodified installed hook")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo = _repo_root(args.repo_root)
        if args.command == "record":
            return cmd_record(repo, args.version_followup)
        if args.command == "check-push":
            return cmd_check_push(repo)
        if args.command == "install-hook":
            return cmd_install(repo)
        return cmd_uninstall(repo)
    except (OSError, Refusal) as exc:
        print(f"publication-check: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
