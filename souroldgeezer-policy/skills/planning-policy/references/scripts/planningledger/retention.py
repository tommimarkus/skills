"""Planning ledger retention: list, gc, purge and run classification."""

from __future__ import annotations

import json
import shutil

from . import core
from .vocabulary import MAX_TOKENS
from .core import (
    Error,
    bounded_reason,
    ident,
    parent,
    proxy_tokens,
    read_json,
    timestamp,
    uuid4,
)
from .store import root, safe_run_contents
from .checkpoint import refuse_retired, retired_contract, validate_events2, validate_run

__all__ = [
    "invalid_entry",
    "unsupported_entry",
    "classify_v2",
    "scan_ledgers",
    "public_entry",
    "bounded_report",
    "remove_entry",
    "collect_ledgers",
    "list_runs",
    "gc",
    "purge",
]


def invalid_entry(base, path, code, summary):
    try:
        relative = str(path.relative_to(base))
    except ValueError:
        relative = path.name
    return {
        "path": relative[:240],
        "code": code,
        "summary": summary[:480],
    }


def unsupported_entry(plan_id, run_id, version, directory):
    """A retained retired-contract run: listed without validation, never collected."""
    return {
        "plan_id": plan_id,
        "run_id": run_id,
        "contract_version": version,
        "run_status": "unsupported",
        "legacy": True,
        "_path": directory,
    }


def classify_v2(plan_id, directory, current):
    safe_run_contents(directory)
    checkpoint = read_json(directory / "checkpoint.json", "malformed v2 checkpoint")
    plan, _ = validate_run(directory, checkpoint, plan_id, directory.name)
    validate_events2(directory, checkpoint)
    entry = {
        "plan_id": plan_id,
        "run_id": directory.name,
        "contract_version": checkpoint["schema"],
        "run_status": checkpoint["run_status"],
        "outcome": checkpoint["outcome"],
        "updated_at": checkpoint["updated_at"],
        "closed_at": checkpoint["closed_at"],
        "purge_after": checkpoint["purge_after"],
        "legacy": False,
        "_path": directory,
        "_step_ids": sorted(checkpoint["steps"]),
    }
    series = plan.get("series")
    if series:
        entry["series_id"] = series["series_id"]
        entry["series_slice"] = series["slice"]
        entry["series_final"] = series["final"]
    if checkpoint["run_status"] == "active":
        entry["retention_state"] = "active"
    else:
        entry["retention_state"] = (
            "eligible" if current >= timestamp(checkpoint["purge_after"], "purge_after") else "kept"
        )
    return entry


def scan_ledgers(base, plan_filter, current):
    entries, invalid = [], []
    if not base.exists():
        return entries, invalid
    if base.is_symlink() or not base.is_dir():
        return entries, [
            invalid_entry(base, base, "invalid_root", "ledger root is not a directory")
        ]
    for plan in sorted(base.iterdir(), key=lambda path: path.name):
        if plan_filter and plan.name != plan_filter:
            continue
        if plan.is_symlink():
            invalid.append(invalid_entry(base, plan, "symlink", "symlink plan entry preserved"))
            continue
        if not plan.is_dir():
            invalid.append(
                invalid_entry(base, plan, "unexpected_contents", "unexpected ledger-root entry")
            )
            continue
        try:
            ident(plan.name, "plan id")
            children = list(plan.iterdir())
        except (Error, OSError) as exc:
            invalid.append(invalid_entry(base, plan, "invalid_plan", str(exc)))
            continue
        if any(child.is_symlink() for child in children):
            invalid.append(invalid_entry(base, plan, "symlink", "symlink ledger content preserved"))
            continue
        names = {child.name for child in children}
        if "checkpoint.json" in names:
            if names != {"checkpoint.json", "events.jsonl"} or any(
                not child.is_file() for child in children
            ):
                invalid.append(
                    invalid_entry(
                        base,
                        plan,
                        "unexpected_contents",
                        "legacy ledger has unexpected or mixed contents",
                    )
                )
                continue
            _retired, version = retired_contract(plan, plan_level=True)
            entries.append(unsupported_entry(plan.name, "", version, plan))
            continue
        if not children or any(not child.is_dir() for child in children):
            invalid.append(
                invalid_entry(base, plan, "unexpected_contents", "v2 plan has unexpected contents")
            )
            continue
        for run in sorted(children, key=lambda path: path.name):
            try:
                uuid4(run.name)
                retired, version = retired_contract(run)
                entries.append(
                    unsupported_entry(plan.name, run.name, version, run)
                    if retired
                    else classify_v2(plan.name, run, current)
                )
            except (Error, OSError, json.JSONDecodeError, TypeError) as exc:
                message = str(exc)
                code = (
                    "unknown_schema"
                    if "unknown checkpoint schema" in message
                    else ("malformed_checkpoint" if "malformed" in message else "invalid_run")
                )
                invalid.append(invalid_entry(base, run, code, message))
    return entries, invalid


def public_entry(entry):
    return {key: value for key, value in entry.items() if not key.startswith("_")}


def bounded_report(action, groups, **facts):
    result = {"ok": True, "action": action, **facts}
    result["counts"] = {name: len(values) for name, values in groups.items()}
    result.update(
        {name: [public_entry(value) for value in values] for name, values in groups.items()}
    )
    result.update(truncated=False, omitted_count=0)
    while proxy_tokens(result) > MAX_TOKENS:
        candidates = [name for name, values in groups.items() if result[name]]
        if not candidates:
            break
        name = max(candidates, key=lambda candidate: len(result[candidate]))
        result[name].pop()
        result["truncated"] = True
        result["omitted_count"] += 1
    result["summary_proxy_tokens"] = proxy_tokens(result)
    return result


def remove_entry(entry):
    path = entry["_path"]
    if path.is_symlink() or not path.is_dir():
        raise Error("refusing changed purge target")
    safe_run_contents(path)
    returns = path / "returns"
    if returns.exists() and any(
        step_dir.name not in entry["_step_ids"] for step_dir in returns.iterdir()
    ):
        raise Error("refusing changed returns purge target")
    parent_path = path.parent
    shutil.rmtree(path)
    try:
        parent_path.rmdir()
    except OSError:
        pass


def collect_ledgers(base, plan_filter, current, remove):
    """Collect eligible closed runs; a retained retired-contract run is only counted."""
    scanned, invalid = scan_ledgers(base, plan_filter, current)
    entries = [entry for entry in scanned if not entry["legacy"]]
    kept = [entry for entry in entries if entry["retention_state"] != "eligible"]
    eligible = [entry for entry in entries if entry["retention_state"] == "eligible"]
    removed = []
    if remove:
        for entry in eligible:
            try:
                remove_entry(entry)
                removed.append(entry)
            except (Error, OSError) as exc:
                invalid.append(invalid_entry(base, entry["_path"], "purge_failed", str(exc)))
    return bounded_report(
        "gc",
        {"kept": kept, "eligible": eligible, "removed": removed, "invalid": invalid},
        dry_run=not remove,
        unsupported_count=len(scanned) - len(entries),
    )


def list_runs(args):
    plan_filter = ident(args.plan_id, "plan id") if args.plan_id else None
    entries, invalid = scan_ledgers(root(args), plan_filter, timestamp(core.now()))
    return bounded_report("list", {"runs": entries, "invalid": invalid})


def gc(args):
    if not args.dry_run:
        parent(args.actor)
    plan_filter = ident(args.plan_id, "plan id") if args.plan_id else None
    return collect_ledgers(root(args), plan_filter, timestamp(core.now()), remove=not args.dry_run)


def purge(args):
    parent(args.actor)
    plan_id = ident(args.plan_id, "plan id")
    target_run = uuid4(args.run_id)
    refuse_retired(args)
    if args.before_retention:
        bounded_reason(args.reason, "--before-retention", required=True)
    else:
        bounded_reason(args.reason, "purge")
    entries, invalid = scan_ledgers(root(args), plan_id, timestamp(core.now()))
    matches = [entry for entry in entries if entry["run_id"] == target_run]
    if not matches:
        detail = invalid[0]["summary"] if invalid else "exact closed run not found"
        raise Error(detail)
    if len(matches) != 1 or matches[0]["run_status"] != "closed":
        raise Error("purge target must be exactly one closed run")
    entry = matches[0]
    early = timestamp(core.now()) < timestamp(entry["purge_after"], "purge_after")
    if early and not args.before_retention:
        raise Error("retention period has not elapsed; use --before-retention with --reason")
    remove_entry(entry)
    return {
        "ok": True,
        "action": "purge",
        "plan_id": entry["plan_id"],
        "run_id": entry["run_id"],
        "contract_version": entry["contract_version"],
        "outcome": entry["outcome"],
        "early": early,
        "reason": args.reason,
    }
