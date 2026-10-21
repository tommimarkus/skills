"""Planning ledger legacy: version-1 checkpoint paths."""

from __future__ import annotations

import json
import re

from .vocabulary import MAX_LEGACY_CHECKPOINT, TRANS, V1_STATES
from .core import Error, canon, dependency_order, ident, parent, rel, required_file, selected_step
from .store import event, plan_dir

__all__ = [
    "parse_v1",
    "load1",
    "legacy_fields",
    "validate_events1",
    "transition1",
]


# Legacy state is deliberately byte-compatible; these paths never load a v2 run.
def parse_v1(raw):
    try:
        records = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise Error("invalid --steps-json") from exc
    if not isinstance(records, list) or len(records) < 2:
        raise Error("--steps-json must contain at least two steps")
    steps = {}
    for record in records:
        if not isinstance(record, dict):
            raise Error("each step must be an object")
        sid = ident(record.get("id"), "step id")
        if sid in steps:
            raise Error("duplicate step id")
        deps = record.get("dependencies", [])
        if not isinstance(deps, list) or not all(isinstance(x, str) for x in deps):
            raise Error("invalid dependencies")
        fields = {}
        for key in ("harness", "tier", "model_or_alias", "effort", "worktree"):
            value = record.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > 160:
                raise Error(f"step {sid} requires {key}")
            fields[key] = value
        steps[sid] = {
            "id": sid,
            "state": "pending",
            "attempt": 1,
            "dependencies": deps,
            "summary": str(record.get("summary", ""))[:240],
            "evidence_paths": [],
            "blocker_code": "",
            **fields,
        }
    dependency_order(steps)
    return steps


def load1(directory):
    if directory.is_symlink() or not directory.is_dir():
        raise Error("ledger checkpoint does not exist")
    path = required_file(directory, "checkpoint.json", "ledger checkpoint does not exist")
    data = json.loads(path.read_text())
    if (
        data.get("schema_version") != 1
        or data.get("approved") is not True
        or not isinstance(data.get("steps"), dict)
        or len(data["steps"]) < 2
    ):
        raise Error("invalid legacy checkpoint")
    if len(canon(data) + b"\n") > MAX_LEGACY_CHECKPOINT:
        raise Error("legacy checkpoint exceeds 16 KiB")
    for sid, step in data["steps"].items():
        if (
            not isinstance(step, dict)
            or step.get("id") != sid
            or step.get("state") not in V1_STATES
            or not isinstance(step.get("attempt"), int)
            or step["attempt"] < 1
        ):
            raise Error("invalid legacy step")
        if not isinstance(step.get("dependencies"), list) or any(
            dep not in data["steps"] for dep in step["dependencies"]
        ):
            raise Error("invalid legacy dependencies")
        if sid in step["dependencies"]:
            raise Error("legacy dependency cycle")
        for field in ("harness", "tier", "model_or_alias", "effort", "worktree"):
            if (
                not isinstance(step.get(field), str)
                or not step[field].strip()
                or len(step[field]) > 160
            ):
                raise Error("invalid legacy assignment")
        if not isinstance(step.get("blocker_code"), str) or (
            step["blocker_code"]
            and not re.fullmatch(r"blocked:[a-z][a-z0-9_]{0,63}", step["blocker_code"])
        ):
            raise Error("invalid legacy blocker")
    try:
        dependency_order(data["steps"])
    except Error as exc:
        raise Error("invalid legacy dependencies") from exc
    return data


def legacy_fields():
    return {
        "legacy_schema": 1,
        "contract_version": 1,
        "dispatch_ready": False,
        "warnings": ["migrate to contract version 2 before dispatch"],
        "rehydration_incomplete": True,
        "retry_policy": "legacy_unbounded",
    }


def validate_events1(directory, data):
    path = required_file(directory, "events.jsonl", "legacy events.jsonl does not exist")
    previous = 0
    for line in path.read_text().splitlines():
        event = json.loads(line)
        if (
            not isinstance(event, dict)
            or event.get("sequence") != previous + 1
            or event.get("actor") != "parent"
            or event.get("plan_id") != data["plan_id"]
            or event.get("action") not in {"init", "transition"}
            or not isinstance(event.get("at"), str)
        ):
            raise Error("invalid legacy event")
        previous += 1
    if previous != data.get("event_sequence"):
        raise Error("legacy event sequence mismatch")


def transition1(args):
    parent(args.actor)
    directory = plan_dir(args)
    data = load1(directory)
    sid, step = selected_step(data, args.step_id)
    old, new = step["state"], args.to
    if new not in TRANS[old]:
        raise Error(f"transition {old} -> {new} is not allowed")
    if new == "ready" and old in {"blocked", "failed"}:
        if not args.retry or not args.evidence_path or not args.summary:
            raise Error("retry requires --retry, --evidence-path, and --summary")
        step["attempt"] += 1
    elif new == "ready" and any(
        data["steps"][d]["state"] != "integrated" for d in step["dependencies"]
    ):
        raise Error("dependencies must be integrated")
    if new == "integrated" and not args.summary:
        raise Error("integration requires --summary")
    if new == "blocked":
        if not re.fullmatch(r"blocked:[a-z][a-z0-9_]{0,63}", args.blocker_code):
            raise Error("blocked transition requires --blocker-code")
        step["blocker_code"] = args.blocker_code
    elif new == "ready":
        step["blocker_code"] = ""
    if args.evidence_path:
        step["evidence_paths"] = (
            step["evidence_paths"] + [rel(args.evidence_path, "evidence path", 512)]
        )[-8:]
    if args.summary:
        step["summary"] = args.summary[:240]
    step["state"] = new
    event(
        directory,
        data,
        "transition",
        step_id=sid,
        from_state=old,
        to_state=new,
        attempt=step["attempt"],
    )
    return {
        **legacy_fields(),
        "ok": True,
        "action": "transition",
        "step_id": sid,
        "from": old,
        "to": new,
        "attempt": step["attempt"],
    }
