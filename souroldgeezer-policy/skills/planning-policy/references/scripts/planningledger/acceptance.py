"""Planning ledger run-acceptance: run a leaf's acceptance command with bounded, kept evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import IO

from .checkpoint import load_run, validate_events
from .contract import effective_leaves
from .core import Error, JsonObject, UsageError, ident, selected_step
from .returns import read_bounded_input, valid_worker_handoff
from .store import safe_acceptance_tree
from .vocabulary import (
    ACCEPTANCE_TAIL_BYTES,
    MAX_ACCEPTANCE_EXCERPT,
    MAX_ACCEPTANCE_SUMMARY,
    MAX_WORKER_HANDOFF_RAW,
    NO_ATTEMPT_ID,
)

__all__ = [
    "stored_packet_run_dir",
    "evidence_file",
    "shell_argv",
    "exit_status",
    "file_digest",
    "read_tail",
    "summary_line",
    "excerpt_of",
    "evidence_problem",
    "run_logged",
    "worker_inputs",
    "parent_inputs",
    "run_acceptance",
]


def stored_packet_run_dir(handoff_file: str, packet: JsonObject) -> Path | None:
    """The run directory holding <run>/handoffs/<step>/<attempt>.json for this packet, else None."""
    path = Path(handoff_file).resolve()
    steps, handoffs, run = path.parent, path.parent.parent, path.parent.parent.parent
    if (
        path.name != f"{packet['attempt_id']}.json"
        or steps.name != packet["step_id"]
        or handoffs.name != "handoffs"
        or run.name != packet["run_id"]
        or not (run / "checkpoint.json").is_file()
    ):
        return None
    return run


def evidence_file(log_dir: Path, mode: str) -> tuple[IO[bytes], Path]:
    """Create the next free <mode>-<n>.log exclusively, never overwriting earlier evidence."""
    log_dir.mkdir(parents=True, exist_ok=True)
    number = 1
    while True:
        path = log_dir / f"{mode}-{number}.log"
        try:
            return path.open("xb+"), path
        except FileExistsError:
            number += 1


def shell_argv(command: str) -> list[str]:
    bash = shutil.which("bash")
    return [bash or "/bin/sh", "-c", command]


def exit_status(returncode: int) -> int:
    """A signal death (negative returncode) maps to the shell convention 128 + signal."""
    return 128 - returncode if returncode < 0 else returncode


def file_digest(file: IO[bytes]) -> str:
    file.seek(0)
    digest = hashlib.sha256()
    while chunk := file.read(1 << 16):
        digest.update(chunk)
    return digest.hexdigest()


def read_tail(file: IO[bytes], size: int) -> tuple[bytes, bool]:
    """The file end (at most the tail window); True when earlier bytes were skipped."""
    start = max(0, size - ACCEPTANCE_TAIL_BYTES)
    file.seek(start)
    return file.read(ACCEPTANCE_TAIL_BYTES), start > 0


def summary_line(tail: bytes, code: int) -> str:
    text = tail.decode("utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1][:MAX_ACCEPTANCE_SUMMARY] if lines else f"exit {code}, no output"


def excerpt_of(tail: bytes, skipped: bool) -> tuple[str, bool]:
    """The last MAX_ACCEPTANCE_EXCERPT bytes, starting on a line or character boundary."""
    truncated = skipped or len(tail) > MAX_ACCEPTANCE_EXCERPT
    chunk = tail[-MAX_ACCEPTANCE_EXCERPT:]
    cut = chunk.find(b"\n")
    if truncated and 0 <= cut < len(chunk) - 1:
        chunk = chunk[cut + 1 :]
    elif truncated:
        # Skip UTF-8 continuation bytes so the text starts on a character boundary.
        offset = 0
        while offset < len(chunk) and chunk[offset] & 0xC0 == 0x80:
            offset += 1
        chunk = chunk[offset:]
    text = chunk.decode("utf-8", errors="replace")
    # Invalid bytes decode to 3-byte replacement characters, so re-check the encoded size.
    while len(text.encode("utf-8")) > MAX_ACCEPTANCE_EXCERPT:
        text, truncated = text[1:], True
    return text, truncated


def evidence_problem(log_dir: Path) -> str:
    """Why the evidence tree is unusable (empty when safe); never follows a symlinked directory."""
    try:
        safe_acceptance_tree(log_dir.parents[2] / "acceptance")
    except Error:
        return "unexpected acceptance contents; evidence not recorded"
    if log_dir.is_symlink() or (log_dir.exists() and not log_dir.is_dir()):
        return "unexpected acceptance contents; evidence not recorded"
    return ""


def run_logged(
    command: str, cwd: str, log_dir: Path | None, mode: str
) -> tuple[JsonObject, int, str, bool]:
    """Run the command with output streamed to evidence; return (result, status, excerpt, cut).

    Without a usable evidence directory the output streams to an unlinked temporary file and the
    acceptance object omits evidence_path and sha256.
    """
    if not Path(cwd).is_dir():
        raise Error("acceptance worktree is not a directory")
    path: Path | None = None
    problem = "no run directory is derivable from the handoff file" if log_dir is None else ""
    file: IO[bytes] | None = None
    if log_dir is not None:
        problem = evidence_problem(log_dir)
    if log_dir is not None and not problem:
        try:
            file, path = evidence_file(log_dir, mode)
        except OSError as exc:
            problem = f"cannot create acceptance evidence: {exc.strerror or exc}"
    with file or tempfile.TemporaryFile() as sink:
        run = subprocess.run(
            shell_argv(command),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=sink,
            stderr=subprocess.STDOUT,
            check=False,
        )
        code = exit_status(run.returncode)
        sink.flush()
        size = sink.seek(0, 2)
        tail, skipped = read_tail(sink, size)
        acceptance: JsonObject = {
            "command": command,
            "exit_code": code,
            "summary": summary_line(tail, code),
        }
        if path is not None and log_dir is not None:
            acceptance["evidence_path"] = path.relative_to(log_dir.parents[2]).as_posix()
            acceptance["sha256"] = file_digest(sink)
    excerpt, cut = excerpt_of(tail, skipped)
    result: JsonObject = {"acceptance": acceptance, "output_bytes": size}
    if problem:
        result["evidence_error"] = problem
    return result, code, excerpt, cut


def worker_inputs(args: argparse.Namespace) -> tuple[JsonObject, str, str, Path | None]:
    """(ids, command, cwd, evidence dir) for the stored worker packet."""
    packet = valid_worker_handoff(
        json.loads(read_bounded_input(args.handoff_file, MAX_WORKER_HANDOFF_RAW, "worker handoff"))
    )
    run = stored_packet_run_dir(args.handoff_file, packet)
    ids: JsonObject = {"step_id": packet["step_id"], "attempt_id": packet["attempt_id"]}
    log_dir = run / "acceptance" / packet["step_id"] / packet["attempt_id"] if run else None
    return ids, packet["leaf"]["acceptance_command"], packet["worktree"], log_dir


def parent_inputs(args: argparse.Namespace) -> tuple[JsonObject, str, str, Path | None]:
    """(ids, effective command, cwd, evidence dir) read from the run without mutating it."""
    if not args.worktree or not Path(args.worktree).is_dir():
        raise UsageError("--worktree must name an existing directory")
    directory, data, plan, _leafs = load_run(args)
    validate_events(directory, data)
    sid, step = selected_step(data, args.step_id)
    attempt = ident(step.get("attempt_id") or NO_ATTEMPT_ID, "attempt id")
    command = effective_leaves(plan, data)[sid]["acceptance_command"]
    log_dir = directory / "acceptance" / sid / attempt
    return {"step_id": sid, "attempt_id": attempt}, command, args.worktree, log_dir


def run_acceptance(args: argparse.Namespace) -> JsonObject:
    """Run the acceptance command once; the result's `acceptance` object is paste-ready."""
    parent_mode = bool(args.run_id or args.step_id or args.worktree)
    incomplete = parent_mode and not (args.run_id and args.step_id)
    if bool(args.handoff_file) == parent_mode or incomplete:
        raise UsageError("pass --handoff-file, or --run-id with --step-id and --worktree")
    mode = "parent" if parent_mode else "worker"
    ids, command, cwd, log_dir = (parent_inputs if parent_mode else worker_inputs)(args)
    result, code, excerpt, cut = run_logged(command, cwd, log_dir, mode)
    value: JsonObject = {"ok": True, "action": "run-acceptance", "mode": mode, **ids}
    value.update(exit_code=code, **result)
    if code != 0:
        value.update(excerpt=excerpt, excerpt_truncated=cut)
    return value
