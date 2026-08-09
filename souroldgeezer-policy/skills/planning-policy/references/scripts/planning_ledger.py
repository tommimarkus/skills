#!/usr/bin/env python3
"""Deterministic, parent-owned checkpoint ledger for approved delegated plans.

The command prints one JSON object to stdout and uses stable exits: 0 success,
2 invalid usage or schema, 3 a refused lifecycle operation, and 4 I/O failure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
CHECKPOINT_MAX_BYTES = 16 * 1024
SHOW_MAX_PROXY_TOKENS = 1200
SHOW_MAX_CHARS = SHOW_MAX_PROXY_TOKENS * 4
PARENT_ACTOR = "parent"
PLAN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
STEP_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
BLOCKER_CODE = re.compile(r"^blocked:[a-z][a-z0-9_]{0,63}$")
PROXY_TOKEN_RE = re.compile(r"\w+|[^\w\s]")
STATES = {"pending", "ready", "in_progress", "completed", "integrated", "blocked", "failed", "superseded", "discarded"}
TRANSITIONS = {
    "pending": {"ready", "superseded", "discarded"},
    "ready": {"in_progress", "blocked", "superseded", "discarded"},
    "in_progress": {"completed", "blocked", "failed", "superseded", "discarded"},
    "blocked": {"ready", "superseded", "discarded"},
    "failed": {"ready", "superseded", "discarded"},
    "completed": {"integrated", "discarded"},
    "integrated": set(), "superseded": set(), "discarded": set(),
}


class LedgerError(Exception):
    """An expected refusal or invalid ledger."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return code


def safe_identifier(value: str, label: str) -> str:
    if not (value and PLAN_ID.fullmatch(value)):
        raise LedgerError(f"invalid {label}: use 1-128 letters, digits, '.', '_' or '-'")
    return value


def git_common_dir(repo_root: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--git-common-dir"],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise LedgerError("not a Git worktree; pass --ledger-root for a persistent non-Git root")
    common = Path(result.stdout.strip())
    return (repo_root / common).resolve() if not common.is_absolute() else common.resolve()


def ledger_root(args: argparse.Namespace) -> Path:
    if args.ledger_root:
        supplied = Path(args.ledger_root).expanduser()
        if not supplied.is_absolute():
            raise LedgerError("--ledger-root must be an absolute persistent path")
        root = supplied.resolve()
        return root / "planning-policy" / "ledgers"
    repo_root = Path(args.repo_root or Path.cwd()).expanduser().resolve()
    return git_common_dir(repo_root) / "planning-policy" / "ledgers"


def ledger_dir(args: argparse.Namespace) -> Path:
    return ledger_root(args) / safe_identifier(args.plan_id, "plan id")


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    content = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(content) > CHECKPOINT_MAX_BYTES:
        raise LedgerError(f"checkpoint exceeds {CHECKPOINT_MAX_BYTES} bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".checkpoint-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_event(path: Path, event: dict[str, Any]) -> None:
    encoded = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    with path.open("ab") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def parse_steps(raw: str) -> dict[str, dict[str, Any]]:
    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LedgerError(f"invalid --steps-json: {exc.msg}") from exc
    if not isinstance(values, list) or len(values) < 2:
        raise LedgerError("--steps-json must be a JSON list with at least two delegated steps")
    steps: dict[str, dict[str, Any]] = {}
    for item in values:
        if not isinstance(item, dict):
            raise LedgerError("each step must be a JSON object")
        step_id = safe_identifier(item.get("id", ""), "step id")
        if step_id in steps:
            raise LedgerError(f"duplicate step id: {step_id}")
        dependencies = item.get("dependencies", [])
        if not isinstance(dependencies, list) or not all(isinstance(dep, str) for dep in dependencies):
            raise LedgerError(f"step {step_id} dependencies must be a list of ids")
        assignment = {}
        for field in ("harness", "tier", "model_or_alias", "effort", "worktree"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > 160:
                raise LedgerError(f"step {step_id} requires bounded {field}")
            assignment[field] = value
        steps[step_id] = {"id": step_id, "state": "pending", "attempt": 1,
                          "dependencies": dependencies,
                          "summary": str(item.get("summary", ""))[:240],
                          "evidence_paths": [], "blocker_code": "", **assignment}
    for step in steps.values():
        if step["id"] in step["dependencies"] or any(dep not in steps for dep in step["dependencies"]):
            raise LedgerError(f"step {step['id']} has unknown or self dependency")
    return steps


def validate_checkpoint(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict): return ["checkpoint is not an object"]
    if data.get("schema_version") != SCHEMA_VERSION: errors.append("unsupported schema_version")
    try: safe_identifier(data.get("plan_id", ""), "plan id")
    except LedgerError as exc: errors.append(str(exc))
    if data.get("approved") is not True: errors.append("ledger is not approval-gated")
    steps = data.get("steps")
    if not isinstance(steps, dict) or len(steps) < 2: errors.append("ledger must have at least two steps")
    elif isinstance(steps, dict):
        for step_id, step in steps.items():
            if not isinstance(step, dict) or step.get("id") != step_id: errors.append(f"invalid step record: {step_id}"); continue
            if step.get("state") not in STATES: errors.append(f"invalid state for {step_id}")
            if not isinstance(step.get("attempt"), int) or step["attempt"] < 1: errors.append(f"invalid attempt for {step_id}")
            dependencies = step.get("dependencies")
            if not isinstance(dependencies, list) or any(dep not in steps for dep in dependencies): errors.append(f"invalid dependencies for {step_id}")
            for field in ("harness", "tier", "model_or_alias", "effort", "worktree"):
                if not isinstance(step.get(field), str) or not step[field].strip() or len(step[field]) > 160:
                    errors.append(f"invalid {field} for {step_id}")
            blocker_code = step.get("blocker_code")
            if not isinstance(blocker_code, str) or (blocker_code and not BLOCKER_CODE.fullmatch(blocker_code)):
                errors.append(f"invalid blocker_code for {step_id}")
        if not errors:
            visiting, visited = set(), set()
            def visit(step_id: str) -> bool:
                if step_id in visiting: return True
                if step_id in visited: return False
                visiting.add(step_id)
                cyclic = any(visit(dep) for dep in steps[step_id]["dependencies"])
                visiting.remove(step_id); visited.add(step_id)
                return cyclic
            if any(visit(step_id) for step_id in steps): errors.append("step dependencies contain a cycle")
    if len((json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()) > CHECKPOINT_MAX_BYTES:
        errors.append("checkpoint exceeds 16 KiB")
    return errors


def load(directory: Path) -> dict[str, Any]:
    checkpoint = directory / "checkpoint.json"
    if not checkpoint.is_file(): raise LedgerError("ledger checkpoint does not exist")
    try: data = json.loads(checkpoint.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise LedgerError(f"cannot read checkpoint: {exc}") from exc
    errors = validate_checkpoint(data)
    if errors: raise LedgerError("invalid checkpoint: " + "; ".join(errors))
    return data


def require_parent(actor: str) -> None:
    if actor != PARENT_ACTOR: raise LedgerError("only actor 'parent' may mutate a ledger")


def init(args: argparse.Namespace) -> dict[str, Any]:
    require_parent(args.actor)
    if not args.approved: raise LedgerError("--approved is required before ledger creation")
    directory = ledger_dir(args)
    if directory.exists(): raise LedgerError("ledger already exists; init is not an overwrite operation")
    steps = parse_steps(args.steps_json)
    timestamp = utc_now()
    data = {"schema_version": SCHEMA_VERSION, "plan_id": args.plan_id, "approved": True,
            "created_at": timestamp, "updated_at": timestamp, "event_sequence": 1, "steps": steps}
    errors = validate_checkpoint(data)
    if errors: raise LedgerError("invalid initial checkpoint: " + "; ".join(errors))
    atomic_json(directory / "checkpoint.json", data)
    append_event(directory / "events.jsonl", {"sequence": 1, "at": timestamp, "actor": PARENT_ACTOR,
                 "action": "init", "plan_id": args.plan_id, "step_count": len(steps)})
    return {"ok": True, "action": "init", "ledger": str(directory), "plan_id": args.plan_id, "step_count": len(steps)}


def transition(args: argparse.Namespace) -> dict[str, Any]:
    require_parent(args.actor)
    directory = ledger_dir(args); data = load(directory)
    step_id = safe_identifier(args.step_id, "step id")
    if step_id not in data["steps"]: raise LedgerError("unknown step id")
    step = data["steps"][step_id]; old, new = step["state"], args.to
    if new not in TRANSITIONS[old]: raise LedgerError(f"transition {old} -> {new} is not allowed")
    if new == "ready":
        if old in {"blocked", "failed"}:
            if not args.retry or not args.evidence_path or not args.summary:
                raise LedgerError("retry from blocked or failed requires --retry, --evidence-path, and --summary")
            step["attempt"] += 1
        elif any(data["steps"][dep]["state"] != "integrated" for dep in step["dependencies"]):
            raise LedgerError("dependencies must be integrated before a step becomes ready")
    if new == "integrated" and not args.summary: raise LedgerError("integration requires --summary")
    if new == "blocked":
        if not BLOCKER_CODE.fullmatch(args.blocker_code):
            raise LedgerError("blocked transition requires --blocker-code like blocked:model_unavailable")
        step["blocker_code"] = args.blocker_code
    elif new == "ready":
        step["blocker_code"] = ""
    if args.evidence_path:
        if Path(args.evidence_path).is_absolute() or ".." in Path(args.evidence_path).parts:
            raise LedgerError("--evidence-path must be a bounded relative path")
        step["evidence_paths"] = (step["evidence_paths"] + [args.evidence_path])[-8:]
    if args.summary: step["summary"] = args.summary[:240]
    step["state"] = new
    timestamp = utc_now(); sequence = data["event_sequence"] + 1
    data["event_sequence"], data["updated_at"] = sequence, timestamp
    errors = validate_checkpoint(data)
    if errors: raise LedgerError("invalid checkpoint after transition: " + "; ".join(errors))
    atomic_json(directory / "checkpoint.json", data)
    append_event(directory / "events.jsonl", {"sequence": sequence, "at": timestamp, "actor": PARENT_ACTOR,
                 "action": "transition", "plan_id": data["plan_id"], "step_id": step_id, "from": old, "to": new,
                 "attempt": step["attempt"], "summary": step["summary"], "evidence_path": args.evidence_path or "",
                 "blocker_code": step["blocker_code"]})
    return {"ok": True, "action": "transition", "step_id": step_id, "from": old, "to": new, "attempt": step["attempt"]}


def show(args: argparse.Namespace) -> dict[str, Any]:
    directory = ledger_dir(args); data = load(directory)
    result = {"ok": True, "plan_id": data["plan_id"], "updated_at": data["updated_at"], "event_sequence": data["event_sequence"],
              "steps": [{"id": step["id"], "state": step["state"], "attempt": step["attempt"], "dependencies": step["dependencies"],
                         "harness": step["harness"], "tier": step["tier"], "model_or_alias": step["model_or_alias"],
                         "effort": step["effort"], "worktree": step["worktree"], "blocker_code": step["blocker_code"],
                         "summary": step["summary"], "evidence_paths": step["evidence_paths"]} for step in data["steps"].values()]}
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    proxy_tokens = len(PROXY_TOKEN_RE.findall(encoded))
    if proxy_tokens > SHOW_MAX_PROXY_TOKENS:
        raise LedgerError("ledger summary exceeds 1200 proxy tokens")
    result["summary_proxy_tokens"] = proxy_tokens
    return result


def validate(args: argparse.Namespace) -> dict[str, Any]:
    directory = ledger_dir(args); data = load(directory); errors = validate_checkpoint(data)
    events = directory / "events.jsonl"
    if not events.is_file(): errors.append("events.jsonl does not exist")
    else:
        previous = 0
        for number, line in enumerate(events.read_text(encoding="utf-8").splitlines(), 1):
            try: event = json.loads(line)
            except json.JSONDecodeError: errors.append(f"invalid event JSON at line {number}"); continue
            if not isinstance(event, dict) or event.get("sequence") != previous + 1:
                errors.append(f"invalid event sequence at line {number}")
            elif event.get("actor") != PARENT_ACTOR or event.get("plan_id") != data["plan_id"]:
                errors.append(f"invalid event ownership at line {number}")
            elif event.get("action") not in {"init", "transition"} or not isinstance(event.get("at"), str):
                errors.append(f"invalid event schema at line {number}")
            previous += 1
        if previous != data["event_sequence"]: errors.append("event sequence does not match checkpoint")
    return {"ok": not errors, "plan_id": data["plan_id"], "errors": errors, "checkpoint_bytes": (directory / "checkpoint.json").stat().st_size}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--repo-root", help="Git worktree to resolve (default: current directory)")
    root.add_argument("--ledger-root", help="absolute persistent root for non-Git runs")
    root.add_argument("--plan-id", required=True)
    commands = root.add_subparsers(dest="command", required=True)
    initial = commands.add_parser("init", help="create an approved multi-step ledger")
    initial.add_argument("--actor", required=True); initial.add_argument("--approved", action="store_true")
    initial.add_argument("--steps-json", required=True)
    change = commands.add_parser("transition", help="make one parent-owned lifecycle transition")
    change.add_argument("--actor", required=True); change.add_argument("--step-id", required=True)
    change.add_argument("--to", required=True, choices=sorted(STATES)); change.add_argument("--retry", action="store_true")
    change.add_argument("--summary", default=""); change.add_argument("--evidence-path", default="")
    change.add_argument("--blocker-code", default="")
    commands.add_parser("show", help="emit a bounded rehydration summary")
    commands.add_parser("validate", help="validate checkpoint and append-only event sequence")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = {"init": init, "transition": transition, "show": show, "validate": validate}[args.command](args)
        return emit(result, 0 if result.get("ok", True) else 2)
    except LedgerError as exc: return emit({"ok": False, "error": str(exc)}, 3)
    except OSError as exc: return emit({"ok": False, "error": f"I/O failure: {exc}"}, 4)


if __name__ == "__main__": raise SystemExit(main())
