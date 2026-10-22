"""Planning ledger store: ledger root, run layout, atomic writes and the append-only event log."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

from . import core, gitops
from .core import Error, JsonObject, JsonValue, canon, ident, read_json, uuid4
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
    "safe_step_json_tree",
    "validate_usage_dir",
    "valid_usage_summary",
]


def root(args: argparse.Namespace) -> Path:
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


def plan_dir(args: argparse.Namespace) -> Path:
    return root(args) / ident(args.plan_id, "plan id")


def run_dir(args: argparse.Namespace) -> Path:
    return plan_dir(args) / uuid4(args.run_id)


def write(path: Path, value: object, maximum: int = MAX_CHECKPOINT) -> None:
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


def event(directory: Path, data: JsonObject, action: str, **facts: object) -> None:
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


def initial_event(
    directory: Path, timestamp: str, action: str, plan_id: str, **facts: object
) -> None:
    payload = {
        "sequence": 1,
        "at": timestamp,
        "actor": "parent",
        "action": action,
        "plan_id": plan_id,
        **facts,
    }
    (directory / "events.jsonl").write_bytes(canon(payload) + b"\n")


def safe_run_contents(directory: Path) -> None:
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
    safe_step_json_tree(directory / "returns", "returns", "return step id", "return attempt id")
    safe_step_json_tree(
        directory / "verifies", "verifies", "verify step id", "verify id", "parent-review"
    )
    safe_step_json_tree(directory / "handoffs", "handoffs", "handoff step id", "handoff attempt id")
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


def safe_step_json_tree(
    root: Path, name: str, step_label: str, child_label: str, tag: str = ""
) -> None:
    """Fail closed unless `root` is absent or holds only step dirs of `<uuid4>.json` files.

    With `tag`, a child may also be named `<uuid4>.<tag>.json`.
    """
    if not root.exists():
        return
    if root.is_symlink() or not root.is_dir():
        raise Error(f"unexpected {name} contents")
    for step_dir in root.iterdir():
        if step_dir.is_symlink() or not step_dir.is_dir():
            raise Error(f"unexpected {name} contents")
        ident(step_dir.name, step_label)
        for child in step_dir.iterdir():
            if child.is_symlink() or not child.is_file() or child.suffix != ".json":
                raise Error(f"unexpected {name} contents")
            uuid4(child.stem.removesuffix(f".{tag}") if tag else child.stem, child_label)


def validate_usage_dir(usage: Path) -> None:
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


def valid_usage_summary(value: JsonValue) -> JsonObject:
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
