#!/usr/bin/env python3
"""Pending-ledger contract for the lesson loop (Plan 1).

The ledger is the gitignored, worktree-shared staging area for correction
candidates before they graduate (Plan 3) into committed rules. Stdlib only.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


class LedgerError(ValueError):
    """Raised for any invalid ledger path, record, or operation."""


SCHEMA_VERSION = 1
DECISIONS = ("review", "auto-approved")
SUBSTRATES = ("deterministic", "policy", "prose")
_REQUIRED = (
    "schema_version", "captured_at", "layer", "decision", "substrate",
    "trigger", "summary", "proposed_rule", "payload", "candidate_id",
)


def _fingerprint(record: dict) -> str:
    basis = json.dumps(
        {k: record[k] for k in ("substrate", "decision", "proposed_rule")},
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def build_candidate(*, trigger, summary, proposed_rule, substrate,
                    decision="review", payload=None, now=None) -> dict:
    """Construct a schema-valid, ID-less candidate record."""
    if substrate not in SUBSTRATES:
        raise LedgerError(f"invalid substrate: {substrate!r}")
    if decision not in DECISIONS:
        raise LedgerError(f"invalid decision: {decision!r}")
    if decision == "auto-approved" and substrate != "deterministic":
        raise LedgerError("auto-approved requires the deterministic substrate")
    for name, value in (("trigger", trigger), ("proposed_rule", proposed_rule)):
        if not isinstance(value, str) or not value.strip():
            raise LedgerError(f"{name} must be a non-empty string")
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    record = {
        "schema_version": SCHEMA_VERSION,
        "captured_at": moment.isoformat(),
        "layer": 2,
        "decision": decision,
        "substrate": substrate,
        "trigger": trigger,
        "summary": summary if isinstance(summary, str) else "",
        "proposed_rule": proposed_rule,
        "payload": payload,
    }
    record["candidate_id"] = _fingerprint(record)
    return record


def validate_candidate(record: dict) -> None:
    """Raise LedgerError unless the record is a well-formed, ID-less candidate."""
    missing = [k for k in _REQUIRED if k not in record]
    if missing:
        raise LedgerError(f"missing fields: {missing}")
    if "sac_id" in record:
        raise LedgerError("candidate must not carry a graduated sac_id")
    if record["decision"] not in DECISIONS:
        raise LedgerError(f"invalid decision: {record['decision']!r}")
    if record["substrate"] not in SUBSTRATES:
        raise LedgerError(f"invalid substrate: {record['substrate']!r}")
    if record["decision"] == "auto-approved" and record["substrate"] != "deterministic":
        raise LedgerError("auto-approved requires the deterministic substrate")


def resolve_ledger_path(cwd: os.PathLike[str] | str | None = None) -> Path:
    """Return the one shared pending-ledger path for this repo.

    Anchored to the git *common dir* so every worktree resolves the SAME
    physical file (not a per-worktree copy). Lives under the main root's
    gitignored ``.cache/``.
    """
    base = Path(cwd) if cwd is not None else Path.cwd()
    try:
        out = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--git-common-dir"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise LedgerError(f"not a git repository: {base}") from exc
    common = Path(out)
    if not common.is_absolute():
        common = (base / common).resolve()
    main_root = common.parent
    return main_root / ".cache" / "lessons" / "pending.jsonl"


def append_candidate(record: dict, *, cwd=None, path=None) -> Path:
    """Validate then append one record as a single line under an exclusive lock.

    The flock spans the whole write, so concurrent appenders (multiple agents,
    any worktree) never interleave or lose a record.
    """
    validate_candidate(record)
    ledger = Path(path) if path is not None else resolve_ledger_path(cwd)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with open(ledger, "a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return ledger


def read_candidates(*, cwd=None, path=None) -> list[dict]:
    """Return all candidate records, or [] if the ledger does not exist yet."""
    ledger = Path(path) if path is not None else resolve_ledger_path(cwd)
    if not ledger.exists():
        return []
    rows = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
