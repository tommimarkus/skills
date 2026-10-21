"""Planning ledger store: ledger root, run layout, atomic writes and the append-only event log."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from . import core, gitops
from .core import Error, canon, ident, read_json, uuid4
from .vocabulary import (
    MAX_CHECKPOINT,
    MAX_USAGE,
    RAW_USAGE_FIELDS,
    USAGE_FIELDS,
    USAGE_STAGES,
)

__all__ = [
    "root",
    "plan_dir",
    "run_dir",
    "write",
    "event",
    "initial_event",
    "safe_run_contents",
    "validate_usage_dir",
    "valid_usage_summary",
]


def root(args):
    if args.ledger_root:
        path = Path(args.ledger_root)
        if not path.is_absolute():
            raise Error("--ledger-root must be absolute")
        return path.resolve() / "planning-policy" / "ledgers"
    repo = Path(args.repo_root or Path.cwd()).resolve()
    common = gitops.git_common_dir(repo)
    if common is None:
        raise Error("not a Git worktree; pass --ledger-root")
    return common / "planning-policy" / "ledgers"


def plan_dir(args):
    return root(args) / ident(args.plan_id, "plan id")


def run_dir(args):
    return plan_dir(args) / uuid4(args.run_id)


def write(path, value, maximum=MAX_CHECKPOINT):
    raw = canon(value) + b"\n"
    if len(raw) > maximum:
        raise Error("bounded record exceeds limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".ledger-")
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(raw)
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def event(directory, data, action, **facts):
    data["event_sequence"] += 1
    data["updated_at"] = core.now()
    write(directory / "checkpoint.json", data)
    with (directory / "events.jsonl").open("ab") as file:
        file.write(
            canon(
                {
                    "sequence": data["event_sequence"],
                    "at": data["updated_at"],
                    "actor": "parent",
                    "action": action,
                    "plan_id": data["plan_id"],
                    "run_id": data.get("run_id", ""),
                    **facts,
                }
            )
            + b"\n"
        )


def initial_event(directory, timestamp, action, plan_id, **facts):
    payload = {
        "sequence": 1,
        "at": timestamp,
        "actor": "parent",
        "action": action,
        "plan_id": plan_id,
        **facts,
    }
    (directory / "events.jsonl").write_bytes(canon(payload) + b"\n")


def safe_run_contents(directory):
    allowed = {
        "checkpoint.json",
        "events.jsonl",
        "plan.json",
        "returns",
        "retry-remediations",
        "verifies",
        "worktree-results",
        "handoffs",
        "usage",
        "series-handoff.json",
    }
    children = list(directory.iterdir())
    if any(child.is_symlink() for child in children):
        raise Error("symlink in run directory")
    names = {child.name for child in children}
    if not {"checkpoint.json", "events.jsonl", "plan.json"}.issubset(names):
        raise Error("missing required run contents")
    if names - allowed:
        raise Error("unexpected run contents")
    for name in ("checkpoint.json", "events.jsonl", "plan.json"):
        if not (directory / name).is_file():
            raise Error("unexpected run contents")
    handoff = directory / "series-handoff.json"
    if handoff.exists() and (handoff.is_symlink() or not handoff.is_file()):
        raise Error("unexpected series-handoff.json contents")
    returns = directory / "returns"
    if returns.exists():
        if returns.is_symlink() or not returns.is_dir():
            raise Error("unexpected returns contents")
        for step_dir in returns.iterdir():
            if step_dir.is_symlink() or not step_dir.is_dir():
                raise Error("unexpected returns contents")
            ident(step_dir.name, "return step id")
            for returned in step_dir.iterdir():
                if returned.is_symlink() or not returned.is_file() or returned.suffix != ".json":
                    raise Error("unexpected returns contents")
                uuid4(returned.stem, "return attempt id")
    verifies = directory / "verifies"
    if verifies.exists():
        if verifies.is_symlink() or not verifies.is_dir():
            raise Error("unexpected verifies contents")
        for step_dir in verifies.iterdir():
            if step_dir.is_symlink() or not step_dir.is_dir():
                raise Error("unexpected verifies contents")
            ident(step_dir.name, "verify step id")
            for stored in step_dir.iterdir():
                if stored.is_symlink() or not stored.is_file() or stored.suffix != ".json":
                    raise Error("unexpected verifies contents")
                uuid4(stored.stem, "verify id")
    stored_packets = directory / "handoffs"
    if stored_packets.exists():
        if stored_packets.is_symlink() or not stored_packets.is_dir():
            raise Error("unexpected handoffs contents")
        for step_dir in stored_packets.iterdir():
            if step_dir.is_symlink() or not step_dir.is_dir():
                raise Error("unexpected handoffs contents")
            ident(step_dir.name, "handoff step id")
            for stored in step_dir.iterdir():
                if stored.is_symlink() or not stored.is_file() or stored.suffix != ".json":
                    raise Error("unexpected handoffs contents")
                uuid4(stored.stem, "handoff attempt id")
    results = directory / "worktree-results"
    if results.exists():
        if results.is_symlink() or not results.is_dir():
            raise Error("unexpected worktree-results contents")
        for step_dir in results.iterdir():
            if step_dir.is_symlink() or not step_dir.is_dir():
                raise Error("unexpected worktree-results contents")
            ident(step_dir.name, "worktree-result step id")
            names = {item.name for item in step_dir.iterdir()}
            if names - {"integrated.json", "cleaned.json"} or any(
                item.is_symlink() or not item.is_file() for item in step_dir.iterdir()
            ):
                raise Error("unexpected worktree-results contents")
    remediations = directory / "retry-remediations"
    if remediations.exists():
        if remediations.is_symlink() or not remediations.is_dir():
            raise Error("unexpected retry-remediations contents")
        for step_dir in remediations.iterdir():
            if step_dir.is_symlink() or not step_dir.is_dir():
                raise Error("unexpected retry-remediations contents")
            ident(step_dir.name, "retry-remediation step id")
            for remediation in step_dir.iterdir():
                if (
                    remediation.is_symlink()
                    or not remediation.is_file()
                    or remediation.suffix != ".json"
                ):
                    raise Error("unexpected retry-remediations contents")
                uuid4(remediation.stem, "retry-remediation attempt id")
    usage = directory / "usage"
    if usage.exists():
        validate_usage_dir(usage)


def validate_usage_dir(usage):
    if usage.is_symlink() or not usage.is_dir():
        raise Error("unexpected usage contents")
    names = {item.name for item in usage.iterdir()}
    if names - {"trace.json", "records"} or "trace.json" not in names:
        raise Error("unexpected usage contents")
    metadata = read_json(usage / "trace.json", "invalid usage trace")
    if (
        set(metadata) != {"schema", "initialized_at", "closed_at"}
        or metadata.get("schema") != "planning-usage-trace-v1"
        or not isinstance(metadata.get("initialized_at"), str)
        or not isinstance(metadata.get("closed_at"), str)
    ):
        raise Error("invalid usage trace")
    records = usage / "records"
    if records.exists():
        if records.is_symlink() or not records.is_dir():
            raise Error("unexpected usage contents")
        for record in records.iterdir():
            if record.is_symlink() or not record.is_file() or record.suffix != ".json":
                raise Error("unexpected usage contents")
            uuid4(record.stem, "usage record id")
            value = read_json(record, "invalid usage record")
            valid_usage_summary(value)


def valid_usage_summary(value):
    if not isinstance(value, dict):
        raise Error("invalid planning-usage-summary-v1")
    if len(canon(value)) > MAX_USAGE:
        raise Error("planning-usage-summary-v1 exceeds 4 KiB")
    if set(value) & RAW_USAGE_FIELDS:
        raise Error("raw-content fields are forbidden in planning-usage-summary-v1")
    if set(value) != USAGE_FIELDS or value.get("schema") != "planning-usage-summary-v1":
        raise Error("invalid planning-usage-summary-v1 fields")
    for key in ("run_id", "step_id", "attempt_id", "actor", "harness", "model"):
        if not isinstance(value.get(key), str) or not value[key] or len(value[key]) > 160:
            raise Error(f"invalid usage {key}")
    if value.get("stage") not in USAGE_STAGES:
        raise Error("invalid usage stage")
    counters = [value.get(key) for key in ("input_tokens", "output_tokens", "total_tokens")]
    if any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in counters):
        raise Error("invalid usage token counters")
    if value["input_tokens"] + value["output_tokens"] != value["total_tokens"]:
        raise Error("usage total_tokens must equal input_tokens plus output_tokens")
    return value
