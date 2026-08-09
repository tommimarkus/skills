#!/usr/bin/env python3
"""Manage clone-local software-design native-tool evidence state.

Every command emits one JSON object.  State is deliberately stored only through
``git config --local`` so linked worktrees of one clone see it while unrelated
clones do not.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1"
CACHE_PREFIX = "softwaredesign.tool-cache-"
DECISION_PREFIX = "softwaredesign.tool-decision-"
CAPABILITY_RE = re.compile(r"[a-z][a-z0-9-]{0,79}\Z")
DATE_FIELDS = ("validated-on", "refresh-after", "purge-after")
REQUIRED_FIELDS = (
    "schema-version",
    "tool",
    "reported-version",
    "source",
    "validated-on",
    "refresh-after",
    "purge-after",
    "state",
)
MAX_OUTPUT_ITEMS = 100
MAX_FIELD_LENGTH = 512
OVERSIZED_VALUE = "<omitted:oversized-value>"
SAFE_RECORD_FIELDS = frozenset(REQUIRED_FIELDS + ("stale-on",))


def utc_today() -> date:
    """Return the current UTC calendar date (separate for deterministic tests)."""
    return datetime.now(timezone.utc).date()


def date_text(value: date) -> str:
    return value.isoformat()


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def capability(value: str) -> str:
    if not CAPABILITY_RE.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "capability must use lowercase letters, digits, and hyphens; it is not a path"
        )
    return value


def bounded_text(value: str) -> str:
    if not value:
        raise argparse.ArgumentTypeError("text fields must not be empty")
    if len(value) > MAX_FIELD_LENGTH:
        raise argparse.ArgumentTypeError(f"text fields must be at most {MAX_FIELD_LENGTH} characters")
    return value


def safe_identifier(value: str) -> str:
    return value if len(value) <= 80 else "<omitted:oversized-identifier>"


def git_config(repo: Path, *args: str, allow_missing: bool = False) -> str:
    command = ["git", "-C", str(repo), "config", "--local", *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    # ``git config --unset-all`` reports 5 when the key did not exist, while
    # ``--get``/``--get-regexp`` use 1.  Both mean an idempotent no-op here.
    if result.returncode and not (allow_missing and result.returncode in {1, 5}):
        raise RuntimeError(result.stderr.strip() or "git config failed")
    return result.stdout


def cache_section(name: str) -> str:
    return f"{CACHE_PREFIX}{name}"


def read_pairs(repo: Path, prefix: str) -> list[tuple[str, str]]:
    output = git_config(repo, "--get-regexp", f"^{re.escape(prefix)}", allow_missing=True)
    pairs: list[tuple[str, str]] = []
    for line in output.splitlines():
        key, separator, value = line.partition(" ")
        if not separator:
            continue
        pairs.append((key, value))
    return pairs


def cache_records(repo: Path) -> dict[str, dict[str, list[str]]]:
    records: dict[str, dict[str, list[str]]] = {}
    for key, value in read_pairs(repo, CACHE_PREFIX):
        suffix = key.removeprefix(CACHE_PREFIX)
        name, separator, field = suffix.rpartition(".")
        if not separator:
            continue
        records.setdefault(name, {}).setdefault(field, []).append(value)
    return records


def assess(name: str, values: dict[str, list[str]], today: date) -> tuple[str, dict[str, str], list[str]]:
    problems: list[str] = []
    record: dict[str, str] = {}
    if not CAPABILITY_RE.fullmatch(name):
        problems.append("invalid:capability")
    for field in SAFE_RECORD_FIELDS:
        options = values.get(field, [])
        if not options:
            continue
        if len(options) != 1:
            problems.append(f"duplicate:{field}")
        elif len(options[0]) > MAX_FIELD_LENGTH:
            problems.append(f"oversized:{field}")
            record[field] = OVERSIZED_VALUE
        else:
            record[field] = options[0]
    if any(field not in SAFE_RECORD_FIELDS for field in values):
        problems.append("unexpected:field")
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    problems.extend(f"missing:{field}" for field in missing)
    if record.get("schema-version") not in (None, SCHEMA_VERSION):
        return "unknown_schema", record, sorted(problems)
    if record.get("state") not in (None, "valid", "stale"):
        problems.append("invalid:state")
    for field in DATE_FIELDS + (("stale-on",) if "stale-on" in record else ()):
        if field in record:
            try:
                parse_date(record[field])
            except ValueError:
                problems.append(f"invalid:{field}")
    if record.get("state") == "stale" and "stale-on" not in record:
        problems.append("missing:stale-on")
    if problems:
        return "malformed", record, sorted(problems)
    if today >= parse_date(record["purge-after"]):
        return "expired", record, []
    if record["state"] == "stale":
        return "stale", record, []
    if today >= parse_date(record["refresh-after"]):
        return "refresh_due", record, []
    return "valid", record, []


def response(command: str, status: str, **data: Any) -> int:
    print(json.dumps({"command": command, "status": status, **data}, sort_keys=True, separators=(",", ":")))
    return 0


def bounded(items: list[Any]) -> tuple[list[Any], int]:
    """Keep a JSON array bounded while disclosing exactly what was omitted."""
    return items[:MAX_OUTPUT_ITEMS], max(0, len(items) - MAX_OUTPUT_ITEMS)


def sort_reports(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(reports, key=lambda report: json.dumps(report, sort_keys=True, separators=(",", ":")))


def decision_summary(key: str, values: list[str], today: date) -> dict[str, str]:
    name = key.removeprefix(DECISION_PREFIX)
    summary = {"capability": safe_identifier(name), "status": "malformed"}
    if not name or len(values) != 1 or len(values[0]) > MAX_FIELD_LENGTH:
        return summary
    value = values[0]
    if not value.startswith("defer-until:"):
        return summary
    try:
        summary["status"] = "expired" if today >= parse_date(value.removeprefix("defer-until:")) else "deferred"
    except ValueError:
        pass
    return summary


def put(args: argparse.Namespace, repo: Path) -> int:
    existing = cache_records(repo).get(args.capability)
    if existing is not None:
        existing_state, existing_record, problems = assess(args.capability, existing, utc_today())
        if existing_state in {"malformed", "unknown_schema"}:
            return response(
                "put", existing_state, capability=args.capability, record=existing_record, problems=problems
            )
    validated = parse_date(args.validated_on) if args.validated_on else utc_today()
    record = {
        "schema-version": SCHEMA_VERSION,
        "tool": args.tool,
        "reported-version": args.reported_version,
        "source": args.source,
        "validated-on": date_text(validated),
        "refresh-after": date_text(validated + timedelta(days=30)),
        "purge-after": date_text(validated + timedelta(days=60)),
        "state": "valid",
    }
    section = cache_section(args.capability)
    for field, value in record.items():
        git_config(repo, "--replace-all", f"{section}.{field}", value)
    # A successful local revalidation also removes a prior failure marker.
    git_config(repo, "--unset-all", f"{section}.stale-on", allow_missing=True)
    return response("put", "ok", capability=args.capability, record=record)


def get(args: argparse.Namespace, repo: Path) -> int:
    values = cache_records(repo).get(args.capability)
    if values is None:
        return response("get", "absent", capability=args.capability)
    state, record, problems = assess(args.capability, values, utc_today())
    return response("get", state, capability=args.capability, record=record, problems=problems)


def stale(args: argparse.Namespace, repo: Path) -> int:
    values = cache_records(repo).get(args.capability)
    if values is None:
        return response("stale", "absent", capability=args.capability)
    state, record, problems = assess(args.capability, values, utc_today())
    if state in {"malformed", "unknown_schema"}:
        return response("stale", state, capability=args.capability, record=record, problems=problems)
    stale_on = parse_date(args.stale_on) if args.stale_on else utc_today()
    section = cache_section(args.capability)
    git_config(repo, "--replace-all", f"{section}.state", "stale")
    git_config(repo, "--replace-all", f"{section}.stale-on", date_text(stale_on))
    git_config(repo, "--replace-all", f"{section}.purge-after", date_text(stale_on + timedelta(days=7)))
    record.update({"state": "stale", "stale-on": date_text(stale_on), "purge-after": date_text(stale_on + timedelta(days=7))})
    return response("stale", "ok", capability=args.capability, record=record)


def clear(args: argparse.Namespace, repo: Path) -> int:
    values = cache_records(repo).get(args.capability)
    if values is None:
        return response("clear", "absent", capability=args.capability)
    state, record, problems = assess(args.capability, values, utc_today())
    if state in {"malformed", "unknown_schema"}:
        return response("clear", state, capability=args.capability, record=record, problems=problems)
    git_config(repo, "--remove-section", cache_section(args.capability))
    return response("clear", "ok", capability=args.capability)


def list_records(args: argparse.Namespace, repo: Path) -> int:
    today = utc_today()
    records = []
    for name, values in sorted(cache_records(repo).items()):
        state, record, problems = assess(name, values, today)
        records.append({"capability": safe_identifier(name), "problems": problems, "record": record, "status": state})
    records, omitted_count = bounded(records)
    decisions = [decision_summary(key, values, today) for key, values in sorted(decision_records(repo).items())]
    decisions, decisions_omitted_count = bounded(decisions)
    return response(
        "list",
        "ok",
        records=records,
        omitted_count=omitted_count,
        decisions=decisions,
        decisions_omitted_count=decisions_omitted_count,
        truncated=bool(omitted_count or decisions_omitted_count),
    )


def clear_all(args: argparse.Namespace, repo: Path) -> int:
    cleared: list[str] = []
    reported: list[dict[str, Any]] = []
    if args.kind in {"cache", "all"}:
        for name, values in sorted(cache_records(repo).items()):
            state, record, problems = assess(name, values, utc_today())
            if state in {"malformed", "unknown_schema"}:
                reported.append({"capability": safe_identifier(name), "problems": problems, "status": state})
            else:
                git_config(repo, "--remove-section", cache_section(name))
                cleared.append(f"cache:{name}")
    if args.kind in {"decisions", "all"}:
        for key, values in sorted(decision_records(repo).items()):
            name = key.removeprefix(DECISION_PREFIX)
            if name and len(values) == 1 and values[0].startswith("defer-until:"):
                git_config(repo, "--unset-all", key)
                cleared.append(f"decision:{name}")
            else:
                reported.append(decision_summary(key, values, utc_today()))
    cleared, cleared_omitted_count = bounded(sorted(cleared))
    reported, reported_omitted_count = bounded(sort_reports(reported))
    return response(
        "clear-all",
        "ok",
        cleared=cleared,
        cleared_omitted_count=cleared_omitted_count,
        reported=reported,
        reported_omitted_count=reported_omitted_count,
        truncated=bool(cleared_omitted_count or reported_omitted_count),
    )


def gc(args: argparse.Namespace, repo: Path) -> int:
    today = utc_today()
    removed: list[str] = []
    retained: list[str] = []
    reported: list[dict[str, Any]] = []
    for name, values in sorted(cache_records(repo).items()):
        state, record, problems = assess(name, values, today)
        if state in {"malformed", "unknown_schema"}:
            reported.append({"capability": safe_identifier(name), "problems": problems, "status": state})
        elif state == "expired":
            removed.append(f"cache:{name}")
            if not args.dry_run:
                git_config(repo, "--remove-section", cache_section(name))
        else:
            retained.append(f"cache:{name}")
    for key, values in sorted(decision_records(repo).items()):
        name = key.removeprefix(DECISION_PREFIX)
        if not name or len(values) != 1 or not values[0].startswith("defer-until:"):
            reported.append(decision_summary(key, values, today))
            continue
        try:
            expired = today >= parse_date(values[0].removeprefix("defer-until:"))
        except ValueError:
            reported.append(decision_summary(key, values, today))
            continue
        if expired:
            removed.append(f"decision:{name}")
            if not args.dry_run:
                git_config(repo, "--unset-all", key)
        else:
            retained.append(f"decision:{name}")
    removed, removed_omitted_count = bounded(sorted(removed))
    retained, retained_omitted_count = bounded(sorted(retained))
    reported, reported_omitted_count = bounded(sort_reports(reported))
    return response(
        "gc",
        "ok",
        dry_run=args.dry_run,
        removed=removed,
        removed_omitted_count=removed_omitted_count,
        retained=retained,
        retained_omitted_count=retained_omitted_count,
        reported=reported,
        reported_omitted_count=reported_omitted_count,
        truncated=bool(removed_omitted_count or retained_omitted_count or reported_omitted_count),
    )


def decision_records(repo: Path) -> dict[str, list[str]]:
    records: dict[str, list[str]] = {}
    for key, value in read_pairs(repo, DECISION_PREFIX):
        records.setdefault(key, []).append(value)
    return records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("get", get), ("stale", stale), ("clear", clear)):
        child = commands.add_parser(name)
        child.add_argument("capability", type=capability)
        if name == "stale":
            child.add_argument("--stale-on")
        child.set_defaults(handler=handler)
    child = commands.add_parser("put")
    child.add_argument("capability", type=capability)
    child.add_argument("--tool", required=True, type=bounded_text)
    child.add_argument("--reported-version", required=True, type=bounded_text)
    child.add_argument("--source", required=True, type=bounded_text)
    child.add_argument("--validated-on")
    child.set_defaults(handler=put)
    commands.add_parser("list").set_defaults(handler=list_records)
    child = commands.add_parser("clear-all")
    child.add_argument("--kind", choices=("cache", "decisions", "all"), required=True)
    child.set_defaults(handler=clear_all)
    child = commands.add_parser("gc")
    child.add_argument("--dry-run", action="store_true")
    child.set_defaults(handler=gc)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return args.handler(args, args.repo_root)
    except (RuntimeError, ValueError) as error:
        return response(getattr(locals().get("args", None), "command", "unknown"), "error", error=str(error))


if __name__ == "__main__":
    raise SystemExit(main())
