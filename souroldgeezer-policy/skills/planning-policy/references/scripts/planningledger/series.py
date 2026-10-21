"""Planning ledger series: series handoff artifacts and the predecessor cross-check."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .checkpoint import valid_series_handoff, validate_events, validate_run
from .core import Error, JsonObject, JsonValue, ident, read_bounded_json, read_json, uuid4
from .store import safe_run_contents
from .vocabulary import MAX_SERIES_HANDOFF, SERIES_HANDOFF_LIST_FIELDS, SERIES_HANDOFF_SCHEMA

__all__ = [
    "load_predecessor_run",
    "series_predecessor_disclosure",
    "read_series_handoff_content",
    "composed_series_handoff",
    "series_close_handoff",
]


def load_predecessor_run(
    ledger_root: Path, plan_id: str, run_id: str
) -> tuple[JsonObject, JsonObject]:
    """Load and fully re-validate a predecessor run's checkpoint and plan.

    Any failure here is the predecessor's fault, never the successor's, so every
    caller treats this raising as "unresolvable" rather than propagating the error.
    """
    directory = ledger_root / plan_id / run_id
    if directory.is_symlink() or not directory.is_dir():
        raise Error("unresolvable predecessor run")
    safe_run_contents(directory)
    checkpoint = read_json(directory / "checkpoint.json", "unresolvable predecessor checkpoint")
    plan, _ = validate_run(directory, checkpoint, plan_id, run_id)
    validate_events(directory, checkpoint)
    return checkpoint, plan


def series_predecessor_disclosure(ledger_root: Path, series: JsonObject) -> str:
    """Compute the init-v5 predecessor cross-check for a slice > 1 successor.

    Never raises: a gc'd, purged, unreadable, or tampered predecessor is
    disclosed as "unresolvable" rather than failing the successor's init.
    """
    predecessor: JsonValue = series.get("predecessor")
    try:
        plan_id = ident(predecessor["plan_id"], "predecessor plan id")
        run_id = uuid4(predecessor["run_id"], "predecessor run id")
        checkpoint, predecessor_plan = load_predecessor_run(ledger_root, plan_id, run_id)
    except (Error, OSError, json.JSONDecodeError, TypeError, KeyError):
        return "unresolvable"
    if checkpoint["plan_hash"] != predecessor["plan_sha256"]:
        return "mismatch:plan_digest"
    if checkpoint["outcome"] != predecessor["outcome"]:
        return "mismatch:outcome"
    if (checkpoint.get("series_handoff_sha256") or "") != predecessor["handoff_sha256"]:
        return "mismatch:handoff_digest"
    predecessor_series = predecessor_plan.get("series") or {}
    if predecessor_series.get("end_verification_commands") != series.get(
        "end_verification_commands"
    ):
        return "mismatch:end_commands"
    return "matched"


def read_series_handoff_content(path: str) -> JsonObject:
    """Read the parent-supplied content file for a series close.

    The caller supplies exactly the four bounded content fields. Identity is
    never caller-supplied, so a previous slice's artifact cannot be pasted into
    this close; `composed_series_handoff` binds it from the closing run.
    """
    value = read_bounded_json(
        path,
        MAX_SERIES_HANDOFF,
        "invalid series handoff content file",
        "series handoff content file exceeds 8 KiB",
    )
    if not isinstance(value, dict) or set(value) != set(SERIES_HANDOFF_LIST_FIELDS):
        raise Error("series handoff content file must carry exactly the four content fields")
    return value


def composed_series_handoff(path: str, data: JsonObject, series: JsonObject) -> JsonObject:
    return valid_series_handoff(
        {
            "schema": SERIES_HANDOFF_SCHEMA,
            "plan_id": data["plan_id"],
            "run_id": data["run_id"],
            "series_id": series.get("series_id"),
            "slice": series.get("slice"),
            **read_series_handoff_content(path),
        }
    )


def series_close_handoff(
    args: argparse.Namespace, data: JsonObject, plan: JsonObject
) -> JsonObject | None:
    """Resolve the series close matrix before `close_run` mutates anything.

    Returns the composed artifact, or None when this close stamps no handoff.
    Every rejection raises here, ahead of the first lifecycle mutation, so a
    refused close leaves the run exactly as it was found.
    """
    series = plan.get("series")
    supplied = getattr(args, "series_handoff_file", "")
    if series is None:
        if supplied:
            raise Error("--series-handoff-file requires a plan with a series block")
        return None
    if series.get("final"):
        if supplied:
            raise Error("a final series slice hands nothing on and takes no --series-handoff-file")
        return None
    if not supplied:
        if args.outcome == "completed":
            raise Error(
                "completed close of a non-final series slice requires --series-handoff-file"
            )
        return None
    return composed_series_handoff(supplied, data, series)
