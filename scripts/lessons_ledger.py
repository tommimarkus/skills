#!/usr/bin/env python3
"""Pending-ledger contract for the lesson loop (Plan 1).

The ledger is the gitignored, worktree-shared staging area for correction
candidates before they graduate (Plan 3) into committed rules. Stdlib only.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


class LedgerError(ValueError):
    """Raised for any invalid ledger path, record, or operation."""


SCHEMA_VERSION = 1
DECISIONS = ("review", "auto-approved")
SUBSTRATES = ("deterministic", "policy", "prose")
STATUSES = ("pending", "applied", "rejected")
_REQUIRED = (
    "schema_version", "captured_at", "layer", "decision", "substrate",
    "status", "trigger", "summary", "proposed_rule", "payload", "candidate_id",
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
        "status": "pending",
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
    if record["status"] not in STATUSES:
        raise LedgerError(f"invalid status: {record['status']!r}")
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


def set_status(candidate_id, status, *, cwd=None, path=None, note=None, now=None) -> bool:
    """Mark one candidate applied/rejected (or pending); rewrite the ledger under lock.

    Returns True if a candidate with that id was found and updated.
    """
    if status not in STATUSES:
        raise LedgerError(f"invalid status: {status!r}")
    ledger = Path(path) if path is not None else resolve_ledger_path(cwd)
    if not ledger.exists():
        return False
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    found = False
    with open(ledger, "r+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            rows = [json.loads(line) for line in handle.read().splitlines() if line.strip()]
            for record in rows:
                if record.get("candidate_id") == candidate_id:
                    record["status"] = status
                    record["resolved_at"] = stamp
                    if note:
                        record["resolve_note"] = note
                    found = True
            handle.seek(0)
            handle.truncate()
            handle.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return found


def pending_candidates(*, cwd=None, path=None) -> list[dict]:
    """Return candidates whose status is pending (default for legacy records)."""
    return [r for r in read_candidates(cwd=cwd, path=path)
            if r.get("status", "pending") == "pending"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="lessons_ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("append", help="append one candidate")
    add.add_argument("--path")
    add.add_argument("--trigger", required=True)
    add.add_argument("--summary", default="")
    add.add_argument("--proposed-rule", required=True, dest="proposed_rule")
    add.add_argument("--substrate", required=True, choices=SUBSTRATES)
    add.add_argument("--decision", default="review", choices=DECISIONS)

    show = sub.add_parser("list", help="summarize or list pending candidates")
    show.add_argument("--path")
    show.add_argument("--pending", action="store_true", help="list each pending candidate")

    res = sub.add_parser("resolve", help="mark a candidate applied or rejected")
    res.add_argument("--path")
    res.add_argument("--id", required=True, dest="candidate_id")
    res.add_argument("--status", required=True, choices=("applied", "rejected"))
    res.add_argument("--note", default=None)

    args = parser.parse_args(argv)
    try:
        if args.command == "append":
            record = build_candidate(
                trigger=args.trigger, summary=args.summary,
                proposed_rule=args.proposed_rule, substrate=args.substrate,
                decision=args.decision)
            ledger = append_candidate(record, path=args.path)
            print(f"appended {record['candidate_id']} -> {ledger}")
            return 0
        if args.command == "resolve":
            ok = set_status(args.candidate_id, args.status, path=args.path, note=args.note)
            if not ok:
                print(f"error: no candidate {args.candidate_id}", file=sys.stderr)
                return 1
            print(f"resolved {args.candidate_id} -> {args.status}")
            return 0
        rows = read_candidates(path=args.path)
        pending = [r for r in rows if r.get("status", "pending") == "pending"]
        if args.pending:
            for r in pending:
                print(f"{r['candidate_id']} [{r['substrate']}] trigger={r['trigger']}")
                print(f"  summary: {r['summary']}")
                print(f"  rule: {r['proposed_rule']}")
            if not pending:
                print("no pending candidates")
            return 0
        applied = sum(1 for r in rows if r.get("status") == "applied")
        rejected = sum(1 for r in rows if r.get("status") == "rejected")
        print(f"{len(rows)} candidate(s): {len(pending)} pending, "
              f"{applied} applied, {rejected} rejected")
        return 0
    except LedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
