#!/usr/bin/env python3
"""Parent-owned checkpoint ledger with byte-compatible legacy commands."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

# A v4 checkpoint retains one bounded capability binding per step. Keep the
# record bounded while leaving the established 40-step summary lane viable.
MAX_CHECKPOINT = 64 * 1024
MAX_LEGACY_CHECKPOINT = 16 * 1024
MAX_RETURN = 8 * 1024
MAX_REMEDIATION = 4 * 1024
MAX_USAGE = 4 * 1024
MAX_TOKENS = 1200
MAX_USAGE_TOKENS = 600
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
PROXY_TOKEN_RE = re.compile(r"\w+|[^\w\s]")
V1_STATES = {
    "pending",
    "ready",
    "in_progress",
    "completed",
    "integrated",
    "blocked",
    "failed",
    "superseded",
    "discarded",
}
TRANS = {
    "pending": {"ready", "superseded", "discarded"},
    "ready": {"in_progress", "blocked", "superseded", "discarded"},
    "in_progress": {"completed", "blocked", "failed", "superseded", "discarded"},
    "blocked": {"ready", "superseded", "discarded"},
    "failed": {"ready", "superseded", "discarded"},
    "completed": {"integrated", "discarded"},
    "integrated": set(),
    "superseded": set(),
    "discarded": set(),
}
NOTE_TYPES = {"finding", "decision_needed", "residual_risk", "untouched", "verification_limit"}
# Single source for the bounded-step-return-v1 contract. Every prose restatement
# of these facts is checked against them by tests/planning_return_contract_parity_test.py.
RETURN_STATUSES = {"completed", "blocked", "failed", "oversized"}
MAX_CHANGED_PATHS = 32
MAX_BLOCKERS = 8
MAX_NOTES = 8
MAX_REMAINDER = 8
MAX_BLOCKER_CODE = 120
MAX_ACCEPTANCE_SUMMARY = 480
MAX_NOTE_MESSAGE = 480
MAX_BLOCKER_SUMMARY = 240
MAX_REMAINDER_ITEM = 240
MAX_PATH = 240
V2_STATES = {
    "pending",
    "ready",
    "in_progress",
    "completed",
    "integrated",
    "cleaned",
    "blocked",
    "failed",
    "oversized",
    "discarded",
}
WORKTREE_RESULT_FIELDS = {
    "schema",
    "ok",
    "action",
    "repo_root",
    "target",
    "branch",
    "worktree",
    "source_commit",
    "rebased_commit",
    "parent_before",
    "parent_after",
}
CLOSEOUT_FIELDS = {
    "returned_commit": "",
    "integrated_commit": "",
    "integration_result_path": "",
    "integration_result_sha256": "",
    "cleanup_result_path": "",
    "cleanup_result_sha256": "",
}
RETENTION_DAYS = {
    "completed": 30,
    "blocked": 90,
    "abandoned": 7,
    "discarded": 7,
    "superseded": 7,
}
LIFECYCLE_FIELDS = {"run_status", "outcome", "closed_at", "purge_after"}
ESCALATING_RETRY_POLICY = "escalating_remediation_v1"
PORTABLE_TIERS = ("mechanical", "standard", "analytical", "deep")
RETRY_STATE_FIELDS = {
    "current_tier",
    "same_tier_retry_used",
    "current_assignment",
    "retry_remediation_path",
    "retry_remediation_sha256",
}
REMEDIATION_FIELDS = {
    "schema",
    "step_id",
    "prior_attempt_id",
    "prior_return_sha256",
    "diagnosis",
    "remediation_action",
    "executor_mode",
    "next_agent_id",
    "next_harness",
    "target_portable_tier",
}
USAGE_FIELDS = {
    "schema",
    "run_id",
    "step_id",
    "attempt_id",
    "actor",
    "stage",
    "harness",
    "model",
    "input_tokens",
    "output_tokens",
    "total_tokens",
}
USAGE_STAGES = {
    "prepare",
    "implement",
    "validate",
    "integrate",
    "final_verify",
    "unknown",
}
RAW_USAGE_FIELDS = {
    "prompt",
    "completion",
    "arguments",
    "results",
    "raw_log",
    "messages",
    "content",
}


class Error(Exception):
    pass


def now():
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp(value, label="timestamp"):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise Error(f"invalid {label}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise Error(f"invalid {label}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise Error(f"invalid {label}")
    return parsed


def retained_until(closed_at, outcome):
    return (
        (timestamp(closed_at, "closed_at") + timedelta(days=RETENTION_DAYS[outcome]))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def bounded_reason(value, label, required=False):
    if not isinstance(value, str) or len(value) > 480 or (required and not value):
        raise Error(f"{label} requires a bounded reason")
    return value


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(canon(value)).hexdigest()


def out(value, code=0):
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return code


def ident(value, label="id"):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise Error(f"invalid {label}")
    return value


def uuid4(value, label="run id"):
    try:
        parsed = uuid.UUID(value)
    except (TypeError, ValueError) as exc:
        raise Error(f"{label} must be canonical lowercase UUID4") from exc
    if parsed.version != 4 or str(parsed) != value:
        raise Error(f"{label} must be canonical lowercase UUID4")
    return value


def rel(value, label="path", maximum=MAX_PATH):
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or Path(value).is_absolute()
        or ".." in Path(value).parts
    ):
        raise Error(f"invalid relative {label}")
    return value


def root(args):
    if args.ledger_root:
        path = Path(args.ledger_root)
        if not path.is_absolute():
            raise Error("--ledger-root must be absolute")
        return path.resolve() / "planning-policy" / "ledgers"
    repo = Path(args.repo_root or Path.cwd()).resolve()
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--git-common-dir"], text=True, capture_output=True
    )
    if result.returncode:
        raise Error("not a Git worktree; pass --ledger-root")
    common = Path(result.stdout.strip())
    common = (repo / common).resolve() if not common.is_absolute() else common.resolve()
    return common / "planning-policy" / "ledgers"


def plan_dir(args):
    return root(args) / ident(args.plan_id, "plan id")


def v2_dir(args):
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
    data["updated_at"] = now()
    write(
        directory / "checkpoint.json",
        data,
        MAX_LEGACY_CHECKPOINT if data.get("schema_version") == 1 else MAX_CHECKPOINT,
    )
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


def parent(actor):
    if actor != "parent":
        raise Error("only actor 'parent' may mutate a ledger")


def approved_parent(args):
    parent(args.actor)
    if not args.approved:
        raise Error("--approved is required")


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


def selected_step(data, step_id):
    sid = ident(step_id, "step id")
    if sid not in data["steps"]:
        raise Error("unknown step id")
    return sid, data["steps"][sid]


def dependency_order(steps):
    """Reject unknown or cyclic dependencies in either ledger schema."""
    if any(dep not in steps for step in steps.values() for dep in step["dependencies"]):
        raise Error("unknown dependency")
    visiting, visited = set(), set()

    def visit(step_id):
        if step_id in visiting:
            raise Error("dependency cycle")
        if step_id not in visited:
            visiting.add(step_id)
            for dependency in steps[step_id]["dependencies"]:
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

    for step_id in steps:
        visit(step_id)


def read_json(path, message):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise Error(message) from exc


def required_file(directory, name, message):
    path = directory / name
    if not path.is_file():
        raise Error(message)
    return path


def require_sha256(value, message):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise Error(message)


def proxy_tokens(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return len(PROXY_TOKEN_RE.findall(encoded))


def stop_step(step, status, reason, code, summary):
    step.update(
        status=status,
        retry_allowed=False,
        reason=reason,
        blockers=[{"code": code, "summary": summary}],
    )


def reject_return(directory, data, step, sid, reason, code, summary):
    stop_step(step, "oversized", reason, code, summary)
    event(directory, data, "record-return", step_id=sid, status="oversized")


def result2(action, args, sid, step, **extra):
    return {
        "ok": True,
        "action": action,
        "run_id": args.run_id,
        "step_id": sid,
        "status": step["status"],
        **extra,
    }


def ordered_steps(steps):
    return sorted(steps.values(), key=lambda value: value["id"])


def leaves_by_id(plan):
    return {leaf["id"]: leaf for leaf in plan["leaves"]}


def checkpoint_binding(data):
    """Rehydrate the complete validator input from bounded per-step bindings."""
    bindings = []
    for step in data.get("steps", {}).values():
        value = step.get("capability_binding") if isinstance(step, dict) else None
        if not isinstance(value, dict) or not isinstance(value.get("bindings"), list):
            return None
        bindings.extend(value["bindings"])
    return {
        "schema": "planning-capability-binding-v1",
        "plan_sha256": data.get("plan_hash"),
        "bindings": bindings,
    }


def lifecycle(data):
    """Validate lifecycle fields, accepting old active v2 checkpoints in memory."""
    present = LIFECYCLE_FIELDS.intersection(data)
    if not present:
        data.update(run_status="active", outcome=None, closed_at=None, purge_after=None)
    elif present != LIFECYCLE_FIELDS:
        raise Error("invalid v2 lifecycle fields")
    status = data["run_status"]
    if status == "active":
        if any(data[key] is not None for key in ("outcome", "closed_at", "purge_after")):
            raise Error("active run has terminal lifecycle fields")
    elif status == "closed":
        outcome = data["outcome"]
        if outcome not in {"completed", "blocked", "abandoned"}:
            raise Error("invalid closed run outcome")
        timestamp(data["closed_at"], "closed_at")
        timestamp(data["purge_after"], "purge_after")
        if data["purge_after"] != retained_until(data["closed_at"], outcome):
            raise Error("invalid closed run retention")
    else:
        raise Error("invalid run_status")
    reason = data.setdefault("close_reason", "")
    if not isinstance(reason, str) or len(reason) > 480:
        raise Error("invalid close_reason")
    return data


def active_run(data):
    if lifecycle(data)["run_status"] != "active":
        raise Error("run is closed")


def validate_steps2(data, leafs):
    if data.get("retry_policy") not in {None, ESCALATING_RETRY_POLICY}:
        raise Error("invalid v2 retry policy")
    steps = data.get("steps")
    if not isinstance(steps, dict) or set(steps) != set(leafs):
        raise Error("blocked:plan_tampered")
    for sid, step in steps.items():
        if (
            not isinstance(step, dict)
            or step.get("id") != sid
            or step.get("status") not in V2_STATES
            or step.get("dependencies") != leafs[sid]["dependencies"]
            or step.get("max_attempts") != leafs[sid]["max_attempts"]
            or not isinstance(step.get("attempt_count"), int)
            or isinstance(step.get("attempt_count"), bool)
            or not 0 <= step["attempt_count"] <= step["max_attempts"]
            or not isinstance(step.get("retry_allowed"), bool)
        ):
            raise Error("blocked:plan_tampered")
        if data.get("retry_policy") == ESCALATING_RETRY_POLICY:
            assignment = step.get("current_assignment")
            assignment_fields = {"agent_id", "harness"}
            if data.get("schema") == 4:
                assignment_fields.add("model_or_alias")
            if (
                not RETRY_STATE_FIELDS.issubset(step)
                or step.get("current_tier") not in PORTABLE_TIERS
                or PORTABLE_TIERS.index(step["current_tier"])
                < PORTABLE_TIERS.index(leafs[sid]["portable_tier"])
                or not isinstance(step.get("same_tier_retry_used"), bool)
                or not isinstance(assignment, dict)
                or set(assignment) != assignment_fields
                or assignment.get("agent_id") != step.get("agent_id")
                or not isinstance(assignment.get("harness"), str)
                or not 1 <= len(assignment["harness"]) <= 160
                or not assignment["harness"].strip()
                or not isinstance(step.get("retry_remediation_path"), str)
                or not isinstance(step.get("retry_remediation_sha256"), str)
                or bool(step["retry_remediation_path"]) != bool(step["retry_remediation_sha256"])
            ):
                raise Error("blocked:plan_tampered")
            if data.get("schema") == 4:
                binding = step.get("capability_binding")
                if (
                    not isinstance(assignment.get("model_or_alias"), str)
                    or not 1 <= len(assignment["model_or_alias"]) <= 160
                    or not assignment["model_or_alias"].strip()
                    or not isinstance(binding, dict)
                    or digest(binding) != step.get("capability_binding_sha256")
                    or not valid_stored_binding(
                        binding,
                        data.get("plan_hash"),
                        sid,
                        leafs[sid],
                        assignment,
                    )
                ):
                    raise Error("blocked:plan_tampered")
            if step["retry_remediation_path"]:
                rel(step["retry_remediation_path"], "retry remediation path")
                require_sha256(
                    step["retry_remediation_sha256"],
                    "blocked:plan_tampered",
                )
    dependency_order(steps)


def validate_events2(directory, data):
    schema = data.get("schema")
    path = required_file(directory, "events.jsonl", "run events.jsonl does not exist")
    previous = 0
    actions = {
        f"init-v{schema}",
        f"transition-v{schema}",
        "record-return",
        f"close-v{schema}",
        f"reopen-v{schema}",
    }
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        raise Error("invalid v2 events") from exc
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Error("invalid v2 event") from exc
        if (
            not isinstance(value, dict)
            or value.get("sequence") != previous + 1
            or value.get("actor") != "parent"
            or value.get("plan_id") != data["plan_id"]
            or value.get("run_id") != data["run_id"]
            or value.get("action") not in actions
            or not isinstance(value.get("at"), str)
        ):
            raise Error("invalid v2 event")
        previous += 1
    if previous != data.get("event_sequence"):
        raise Error("v2 event sequence mismatch")


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


def init1(args):
    approved_parent(args)
    directory = plan_dir(args)
    if directory.exists():
        raise Error("ledger already exists; init is not an overwrite operation")
    steps = parse_v1(args.steps_json)
    collect_ledgers(root(args), None, timestamp(now()), remove=True)
    created_at = now()
    data = {
        "schema_version": 1,
        "plan_id": args.plan_id,
        "approved": True,
        "created_at": created_at,
        "updated_at": created_at,
        "event_sequence": 1,
        "steps": steps,
    }
    write(directory / "checkpoint.json", data, MAX_LEGACY_CHECKPOINT)
    initial_event(directory, created_at, "init", args.plan_id, step_count=len(data["steps"]))
    return {
        **legacy_fields(),
        "ok": True,
        "action": "init",
        "ledger": str(directory),
        "plan_id": args.plan_id,
        "step_count": len(data["steps"]),
    }


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


def plan_validator():
    spec = importlib.util.spec_from_file_location(
        "plan_contract", Path(__file__).with_name("validate_plan_contract.py")
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module.validate


def read_plan(path, contract_version=4):
    data = read_json(path, "cannot read plan file")
    result = plan_validator()(data)
    ready_key = "approval_ready" if contract_version == 4 else "resume_ready"
    if (
        not result.get("valid")
        or not result.get(ready_key)
        or result.get("contract_version") != contract_version
    ):
        raise Error("plan is not dispatch-ready")
    return data


def capability_bindings(path, plan):
    """Load one complete v4 binding and retain only the assigned step's evidence."""
    value = read_json(path, "cannot read capability binding file")
    result = plan_validator()(plan, capability_binding=value)
    if not result.get("valid") or not result.get("dispatch_ready"):
        raise Error("blocked:capability_unavailable")
    return value


def binding_for_step(binding, sid, assignment):
    matches = [item for item in binding["bindings"] if item["step_id"] == sid]
    if len(matches) != 1:
        raise Error("blocked:capability_unavailable")
    item = matches[0]
    if (
        item["host"] != assignment["harness"]
        or item["executor"] != assignment["model_or_alias"]
    ):
        raise Error("blocked:capability_unavailable")
    return {
        "schema": binding["schema"],
        "plan_sha256": binding["plan_sha256"],
        "bindings": [item],
    }


def valid_stored_binding(value, plan_hash, sid, leaf, assignment):
    if (
        not isinstance(value, dict)
        or set(value) != {"schema", "plan_sha256", "bindings"}
        or value.get("schema") != "planning-capability-binding-v1"
        or value.get("plan_sha256") != plan_hash
        or not isinstance(value.get("bindings"), list)
        or len(value["bindings"]) != 1
    ):
        return False
    item = value["bindings"][0]
    return (
        isinstance(item, dict)
        and set(item) == {"step_id", "host", "executor", "requirements", "evidence"}
        and item.get("step_id") == sid
        and item.get("host") == assignment["harness"]
        and item.get("executor") == assignment["model_or_alias"]
        and item.get("requirements") == leaf["capability_requirements"]
        and isinstance(item.get("evidence"), list)
        and 1 <= len(item["evidence"]) <= 8
        and all(
            isinstance(evidence, str) and 1 <= len(evidence.strip()) <= 240
            for evidence in item["evidence"]
        )
    )


def assignments(path, plan):
    values = read_json(path, "cannot read assignments file")
    if not isinstance(values, list):
        raise Error("assignments file must be an array")
    leaves = leaves_by_id(plan)
    result = {}
    for value in values:
        if not isinstance(value, dict) or set(value) != {
            "id",
            "harness",
            "model_or_alias",
            "effort",
            "worktree",
        }:
            raise Error(
                "assignment fields must be exactly id, harness, model_or_alias, effort, worktree"
            )
        sid = ident(value["id"], "assignment id")
        if sid not in leaves or sid in result:
            raise Error("assignments must join each leaf exactly once")
        for key in ("harness", "model_or_alias", "effort", "worktree"):
            if not isinstance(value[key], str) or not value[key].strip() or len(value[key]) > 160:
                raise Error(f"invalid assignment {key}")
        result[sid] = value
    if set(result) != set(leaves):
        raise Error("assignments must join each leaf exactly once")
    return result


def init2(args):
    raise Error("blocked:contract_migration_required")


def init3(args):
    raise Error("blocked:contract_migration_required")


def init4(args):
    approved_parent(args)
    plan = read_plan(args.plan_file, 4)
    assigned = assignments(args.assignments_file, plan)
    bindings = capability_bindings(args.capability_binding_file, plan)
    ledger_root = root(args)
    collect_ledgers(ledger_root, None, timestamp(now()), remove=True)
    directory = plan_dir(args)
    existing, invalid = scan_ledgers(ledger_root, args.plan_id, timestamp(now()))
    if invalid:
        raise Error("target plan ledger directory is invalid")
    if any(entry["legacy"] for entry in existing):
        raise Error("cannot add a v4 run inside a legacy ledger directory")
    run_id = str(uuid.uuid4())
    run = directory / run_id
    if run.exists():
        raise Error("generated run already exists")
    leaves = leaves_by_id(plan)
    created_at = now()
    steps = {}
    for sid, leaf in leaves.items():
        resolved_binding = binding_for_step(bindings, sid, assigned[sid])
        steps[sid] = {
            "id": sid,
            "status": "pending",
            "attempt_count": 0,
            "max_attempts": leaf["max_attempts"],
            "dependencies": leaf["dependencies"],
            "assignment": assigned[sid],
            "agent_id": "",
            "attempt_id": "",
            "fingerprints": [],
            "reason": "",
            "blockers": [],
            "return_path": "",
            "return_sha256": "",
            "retry_allowed": True,
            "current_tier": leaf["portable_tier"],
            "same_tier_retry_used": False,
            "current_assignment": {
                "agent_id": "",
                "harness": assigned[sid]["harness"],
                "model_or_alias": assigned[sid]["model_or_alias"],
            },
            "capability_binding": resolved_binding,
            "capability_binding_sha256": digest(resolved_binding),
            "retry_remediation_path": "",
            "retry_remediation_sha256": "",
            **CLOSEOUT_FIELDS,
        }
    data = {
        "schema": 4,
        "plan_id": args.plan_id,
        "run_id": run_id,
        "plan_hash": digest(plan),
        "objective": plan["objective"][:240],
        "scope_summary": plan["scope_summary"][:480],
        "approved_decisions": plan["approved_decisions"],
        "created_at": created_at,
        "updated_at": created_at,
        "event_sequence": 1,
        "run_status": "active",
        "outcome": None,
        "closed_at": None,
        "purge_after": None,
        "close_reason": "",
        "retry_policy": ESCALATING_RETRY_POLICY,
        "steps": steps,
    }
    write(run / "plan.json", plan, 64 * 1024)
    write(run / "checkpoint.json", data)
    initial_event(
        run,
        created_at,
        "init-v4",
        args.plan_id,
        run_id=run_id,
        plan_hash=data["plan_hash"],
    )
    return {
        "ok": True,
        "action": "init-v4",
        "plan_id": args.plan_id,
        "run_id": run_id,
        "plan_hash": data["plan_hash"],
        "retry_policy": data["retry_policy"],
    }


def load2(args):
    parent_directory = plan_dir(args)
    if parent_directory.is_symlink() or not parent_directory.is_dir():
        raise Error("unknown run id")
    directory = v2_dir(args)
    if directory.is_symlink() or not directory.is_dir():
        raise Error("unknown run id")
    safe_run_contents(directory)
    path = required_file(directory, "checkpoint.json", "unknown run id")
    data = read_json(path, "invalid v2 checkpoint")
    if (
        data.get("schema") not in {2, 3, 4}
        or data.get("plan_id") != args.plan_id
        or data.get("run_id") != args.run_id
        or data.get("retry_policy") not in {None, ESCALATING_RETRY_POLICY}
    ):
        raise Error("invalid run checkpoint")
    plan = read_json(directory / "plan.json", "blocked:plan_tampered")
    if digest(plan) != data.get("plan_hash") or not SHA.fullmatch(data.get("plan_hash", "")):
        raise Error("blocked:plan_tampered")
    plan_result = plan_validator()(plan, capability_binding=checkpoint_binding(data))
    ready_key = "dispatch_ready" if data["schema"] == 4 else "resume_ready"
    if not plan_result.get(ready_key) or plan_result.get("contract_version") != data["schema"]:
        raise Error("blocked:plan_tampered")
    leafs = leaves_by_id(plan)
    if set(data.get("steps", {})) != set(leafs):
        raise Error("blocked:plan_tampered")
    for step in data["steps"].values():
        for field, default in CLOSEOUT_FIELDS.items():
            step.setdefault(field, default)
    validate_steps2(data, leafs)
    validate_retry_artifacts(directory, data)
    lifecycle(data)
    return directory, data, plan, leafs


def mutating_run(args):
    parent(args.actor)
    loaded = load2(args)
    validate_events2(loaded[0], loaded[1])
    active_run(loaded[1])
    return loaded


def advance(step, old, expected, target, summary):
    if old != expected:
        raise Error(f"only {expected} steps can become {target}")
    step.update(status=target, reason=summary[:480])


def valid_remediation(value):
    if not isinstance(value, dict) or len(canon(value)) > MAX_REMEDIATION:
        raise Error("retry-remediation-v1 exceeds 4 KiB")
    optional = {"evidence_path", "sha256"}
    if (
        set(value) - (REMEDIATION_FIELDS | optional)
        or REMEDIATION_FIELDS - set(value)
        or value.get("schema") != "retry-remediation-v1"
        or value.get("executor_mode") not in {"reuse", "fresh"}
        or value.get("target_portable_tier") not in PORTABLE_TIERS
    ):
        raise Error("invalid retry-remediation-v1 schema")
    ident(value["step_id"], "remediation step id")
    uuid4(value["prior_attempt_id"], "prior attempt id")
    require_sha256(value["prior_return_sha256"], "invalid prior return sha256")
    for field in ("diagnosis", "remediation_action"):
        if not isinstance(value[field], str) or not value[field] or len(value[field]) > 480:
            raise Error(f"retry remediation requires bounded {field}")
    if (
        not isinstance(value["next_agent_id"], str)
        or not 1 <= len(value["next_agent_id"]) <= 128
        or not value["next_agent_id"].strip()
    ):
        raise Error("retry remediation requires bounded next_agent_id")
    if (
        not isinstance(value["next_harness"], str)
        or not 1 <= len(value["next_harness"]) <= 160
        or not value["next_harness"].strip()
    ):
        raise Error("retry remediation requires bounded next_harness")
    if ("evidence_path" in value) != ("sha256" in value):
        raise Error("retry remediation evidence digest pair required")
    if "evidence_path" in value:
        rel(value["evidence_path"], "retry remediation evidence")
        require_sha256(value["sha256"], "invalid retry remediation evidence sha256")
    return value


def read_remediation(path):
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid retry-remediation-v1") from exc
    if len(raw) > MAX_REMEDIATION:
        raise Error("retry-remediation-v1 exceeds 4 KiB")
    return valid_remediation(value)


def current_return(directory, step):
    if not step.get("return_path") or not step.get("return_sha256"):
        raise Error("retry requires a current prior return")
    path = directory / rel(step["return_path"], "return path")
    value = read_json(path, "current prior return is missing")
    if digest(value) != step["return_sha256"]:
        raise Error("current prior return digest mismatch")
    return value


def retry_outcome(value):
    blockers = value.get("blockers", [])
    if not isinstance(blockers, list) or len(blockers) != 1:
        return ""
    code = blockers[0].get("code") if isinstance(blockers[0], dict) else ""
    if value.get("status") == "failed" and code == "failed:acceptance":
        return "failed:acceptance"
    if value.get("status") == "blocked" and code == "blocked:needs_higher_tier":
        return "blocked:needs_higher_tier"
    return ""


def needs_higher_tier(step, outcome):
    return outcome == "blocked:needs_higher_tier" or (
        outcome == "failed:acceptance"
        and (step["same_tier_retry_used"] or step["attempt_count"] > 1)
    )


def store_remediation(args, directory, step):
    if not args.retry_remediation_file:
        raise Error("retry requires --retry-remediation-file")
    value = read_remediation(args.retry_remediation_file)
    prior = current_return(directory, step)
    if (
        value["step_id"] != step["id"]
        or value["prior_attempt_id"] != step["attempt_id"]
        or value["prior_return_sha256"] != step["return_sha256"]
        or digest(prior) != value["prior_return_sha256"]
    ):
        raise Error("stale retry remediation identity")
    outcome = retry_outcome(prior)
    if not outcome:
        raise Error("prior outcome is not retry eligible")
    if value["executor_mode"] == "reuse":
        if value["next_agent_id"] != step["agent_id"]:
            raise Error("reuse remediation must keep the current agent identity")
    elif value["next_agent_id"] == step["agent_id"]:
        raise Error("fresh remediation requires a new agent identity")
    if args.agent_id and args.agent_id != value["next_agent_id"]:
        raise Error("--agent-id does not match retry remediation")
    current = PORTABLE_TIERS.index(step["current_tier"])
    target = PORTABLE_TIERS.index(value["target_portable_tier"])
    if target < current:
        raise Error("retry target tier cannot decrease")
    if outcome == "blocked:needs_higher_tier" and target == current:
        raise Error("blocked:needs_higher_tier requires a higher target tier")
    if step["attempt_count"] > 1 and target == current:
        raise Error("later eligible retries require a higher target tier")
    if target == current and step["same_tier_retry_used"]:
        raise Error("same-tier retry already used")
    destination = directory / "retry-remediations" / step["id"] / f"{step['attempt_id']}.json"
    write(destination, value, MAX_REMEDIATION)
    return value, str(destination.relative_to(directory)), digest(value), target == current


def validate_retry_artifacts(directory, data):
    if data.get("retry_policy") != ESCALATING_RETRY_POLICY:
        return
    for step in data["steps"].values():
        path = step["retry_remediation_path"]
        if not path:
            continue
        value = read_json(directory / path, "missing retry remediation artifact")
        valid_remediation(value)
        expected_path = (
            Path("retry-remediations") / step["id"] / f"{value['prior_attempt_id']}.json"
        )
        if (
            value["step_id"] != step["id"]
            or path != str(expected_path)
            or value["target_portable_tier"] != step["current_tier"]
            or value["next_agent_id"] != step["current_assignment"]["agent_id"]
            or value["next_harness"] != step["current_assignment"]["harness"]
            or digest(value) != step["retry_remediation_sha256"]
        ):
            raise Error("retry remediation artifact digest mismatch")


def ready(args, directory, data, plan, step):
    for value, label in ((args.harness, "harness"), (args.model_or_alias, "model_or_alias")):
        if value and (not isinstance(value, str) or not value.strip() or len(value) > 160):
            raise Error(f"invalid {label}")
    if not isinstance(args.agent_id, str) or not 1 <= len(args.agent_id) <= 128:
        if step["status"] == "pending" or data.get("retry_policy") != ESCALATING_RETRY_POLICY:
            raise Error("ready requires bounded --agent-id")
    if step["status"] not in {"pending", "blocked", "failed"} or not step["retry_allowed"]:
        raise Error("step cannot be readied")
    retry_state = None
    if step["status"] != "pending":
        if not args.retry:
            raise Error("retry requires --retry")
        if data.get("retry_policy") == ESCALATING_RETRY_POLICY:
            retry_state = store_remediation(args, directory, step)
        elif not args.summary:
            raise Error("retry requires --retry and bounded --summary")
    elif args.retry or args.retry_remediation_file:
        raise Error("initial ready transition is not a retry")
    if any(data["steps"][dep]["status"] != "cleaned" for dep in step["dependencies"]):
        raise Error("dependencies are not cleaned")
    if step["attempt_count"] >= step["max_attempts"]:
        raise Error("blocked:retry_exhausted")
    if retry_state:
        remediation, path, remediation_sha, same_tier = retry_state
        current_assignment = {
            "agent_id": remediation["next_agent_id"],
            "harness": remediation["next_harness"],
        }
        if data.get("schema") == 4:
            current_assignment["model_or_alias"] = (
                args.model_or_alias or step["current_assignment"]["model_or_alias"]
            )
        step.update(
            current_tier=remediation["target_portable_tier"],
            same_tier_retry_used=step["same_tier_retry_used"] or same_tier,
            current_assignment=current_assignment,
            retry_remediation_path=path,
            retry_remediation_sha256=remediation_sha,
        )
        next_agent_id = remediation["next_agent_id"]
        reason = remediation["diagnosis"]
    else:
        next_agent_id = args.agent_id
        reason = args.summary or "ready"
        if data.get("retry_policy") == ESCALATING_RETRY_POLICY:
            current_assignment = {
                "agent_id": next_agent_id,
                "harness": args.harness or step["assignment"]["harness"],
            }
            if data.get("schema") == 4:
                current_assignment["model_or_alias"] = (
                    args.model_or_alias or step["assignment"]["model_or_alias"]
                )
            step["current_assignment"] = current_assignment
    if data.get("schema") == 4:
        current = step["current_assignment"]
        stored = step["capability_binding"]["bindings"][0]
        if (
            stored["host"] != current["harness"]
            or stored["executor"] != current["model_or_alias"]
        ):
            if not args.capability_binding_file:
                raise Error("blocked:capability_unavailable")
            replacement = capability_bindings(args.capability_binding_file, plan)
            resolved = binding_for_step(
                replacement,
                step["id"],
                {
                    "harness": current["harness"],
                    "model_or_alias": current["model_or_alias"],
                },
            )
            step["capability_binding"] = resolved
            step["capability_binding_sha256"] = digest(resolved)
    step["attempt_count"] += 1
    step["agent_id"] = next_agent_id
    step["attempt_id"] = str(uuid.uuid4())
    step["status"] = "ready"
    step["reason"] = reason[:480]


def transition2(args):
    directory, data, plan, leafs = mutating_run(args)
    sid, step = selected_step(data, args.step_id)
    old = step["status"]
    new = args.to
    if new == "ready":
        ready(args, directory, data, plan, step)
    elif new == "in_progress":
        advance(step, old, "ready", new, args.summary or "in progress")
    elif new in {"integrated", "cleaned"}:
        expected = "completed" if new == "integrated" else "integrated"
        value, result_path, result_sha = worktree_result(
            args.worktree_result, directory, sid, step, leafs[sid], new
        )
        advance(step, old, expected, new, args.summary or new)
        if new == "integrated":
            step.update(
                integrated_commit=value["rebased_commit"],
                integration_result_path=result_path,
                integration_result_sha256=result_sha,
            )
        else:
            step.update(
                cleanup_result_path=result_path,
                cleanup_result_sha256=result_sha,
            )
    else:
        raise Error("v2 transition only permits ready, in_progress, integrated, or cleaned")
    event(
        directory,
        data,
        f"transition-v{data['schema']}",
        step_id=sid,
        from_status=old,
        to_status=step["status"],
        attempt_id=step["attempt_id"],
    )
    return result2("transition", args, sid, step, attempt_id=step["attempt_id"])


def worktree_result(path, directory, sid, step, leaf, target):
    if not path:
        raise Error(f"{target} transition requires --worktree-result")
    source = Path(path)
    try:
        raw = source.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid planning-worktree-result-v1") from exc
    allowed = WORKTREE_RESULT_FIELDS | ({"parent_commit"} if target == "cleaned" else set())
    if (
        len(raw) > 4096
        or not isinstance(value, dict)
        or set(value)
        not in (
            {frozenset(WORKTREE_RESULT_FIELDS), frozenset(allowed)}
            if target == "cleaned"
            else {frozenset(allowed)}
        )
        or value.get("schema") != "planning-worktree-result-v1"
        or value.get("ok") is not True
        or value.get("action") != ("integrate" if target == "integrated" else "cleanup")
    ):
        raise Error("invalid planning-worktree-result-v1")
    for field in ("source_commit", "rebased_commit", "parent_before", "parent_after"):
        if not isinstance(value.get(field), str) or not COMMIT.fullmatch(value[field]):
            raise Error("invalid planning worktree commit identity")
    if "parent_commit" in value and (
        not isinstance(value["parent_commit"], str) or not COMMIT.fullmatch(value["parent_commit"])
    ):
        raise Error("invalid cleanup parent commit identity")
    assigned_worktree = Path(step["assignment"]["worktree"])
    if not assigned_worktree.is_absolute():
        assigned_worktree = Path(value["repo_root"]) / assigned_worktree
    if (
        value["branch"] != leaf["worktree_owner"]
        or Path(value["worktree"]).resolve() != assigned_worktree.resolve()
    ):
        raise Error("planning worktree result does not match assigned owner")
    if target == "integrated":
        if step["returned_commit"] and value["source_commit"] != step["returned_commit"]:
            raise Error("integrated source does not match returned commit")
        if value["rebased_commit"] != value["parent_after"]:
            raise Error("integrated commit does not match parent commit")
    else:
        prior = read_json(directory / step["integration_result_path"], "missing integration result")
        for field in WORKTREE_RESULT_FIELDS - {"action"}:
            if value[field] != prior[field]:
                raise Error("cleanup result does not match integrated identity")
        if value["rebased_commit"] != step["integrated_commit"]:
            raise Error("cleanup result does not match integrated commit")
    destination = directory / "worktree-results" / sid / f"{target}.json"
    write(destination, value, 4096)
    return value, str(destination.relative_to(directory)), digest(value)


def close2(args):
    parent(args.actor)
    directory, data, plan, leafs = load2(args)
    validate_events2(directory, data)
    active_run(data)
    statuses = {step["status"] for step in data["steps"].values()}
    if args.outcome == "completed" and statuses != {"cleaned"}:
        raise Error("completed close requires every step cleaned")
    if args.outcome == "blocked":
        if statuses.intersection({"ready", "in_progress"}):
            raise Error("blocked close refuses live work")
        bounded_reason(args.reason, "blocked close obstruction", required=True)
    if args.outcome == "abandoned":
        if "in_progress" in statuses:
            raise Error("abandoned close refuses in_progress work")
        bounded_reason(args.reason, "abandoned close", required=True)
        for step in data["steps"].values():
            if step["status"] in {"pending", "ready"}:
                step.update(status="discarded", retry_allowed=False, reason="discarded: abandoned")
    closed_at = now()
    data.update(
        run_status="closed",
        outcome=args.outcome,
        closed_at=closed_at,
        purge_after=retained_until(closed_at, args.outcome),
        close_reason=bounded_reason(args.reason, "close"),
    )
    event(
        directory,
        data,
        f"close-v{data['schema']}",
        outcome=args.outcome,
        purge_after=data["purge_after"],
        reason=data["close_reason"],
    )
    gc_result = collect_ledgers(root(args), None, timestamp(now()), remove=True)
    return {
        "ok": True,
        "action": "close",
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "run_status": data["run_status"],
        "outcome": data["outcome"],
        "closed_at": data["closed_at"],
        "purge_after": data["purge_after"],
        "gc_removed_count": gc_result["counts"]["removed"],
        "gc_invalid_count": gc_result["counts"]["invalid"],
    }


def reopen2(args):
    parent(args.actor)
    directory, data, plan, leafs = load2(args)
    validate_events2(directory, data)
    if data["run_status"] != "closed" or data["outcome"] != "blocked":
        raise Error("only a retained blocked run may reopen")
    if timestamp(now()) >= timestamp(data["purge_after"], "purge_after"):
        raise Error("blocked run is no longer retained")
    retryable = [
        step
        for step in data["steps"].values()
        if step["status"] in {"pending", "blocked", "failed"}
        and step["retry_allowed"]
        and step["attempt_count"] < step["max_attempts"]
    ]
    if not retryable:
        raise Error("blocked run has no retryable step")
    bounded_reason(args.reason, "reopen", required=True)
    previous_outcome = data["outcome"]
    data.update(
        run_status="active",
        outcome=None,
        closed_at=None,
        purge_after=None,
        close_reason="",
    )
    event(
        directory,
        data,
        f"reopen-v{data['schema']}",
        previous_outcome=previous_outcome,
        reason=args.reason,
    )
    return {
        "ok": True,
        "action": "reopen",
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "run_status": "active",
        "retryable_steps": [
            step["id"] for step in ordered_steps(data["steps"]) if step in retryable
        ],
    }


def valid_return(value, data, step, leaf):
    if not isinstance(value, dict) or len(canon(value)) > MAX_RETURN:
        raise Error("bounded-step-return-v1 exceeds 8 KiB")
    required = {
        "schema",
        "step_id",
        "attempt_id",
        "agent_id",
        "status",
        "changed_paths",
        "acceptance",
        "blockers",
        "notes",
        "unstarted_remainder",
        "commit_hash",
    }
    if set(value) != required or value["schema"] != "bounded-step-return-v1":
        raise Error("invalid bounded-step-return-v1 schema")
    if (
        value["step_id"] != step["id"]
        or value["attempt_id"] != step["attempt_id"]
        or value["agent_id"] != step["agent_id"]
    ):
        raise Error("stale or foreign return identity")
    if value["status"] not in RETURN_STATUSES:
        raise Error("invalid return status")
    paths = value["changed_paths"]
    if (
        not isinstance(paths, list)
        or len(paths) > MAX_CHANGED_PATHS
        or len(set(paths)) != len(paths)
    ):
        raise Error("invalid changed_paths")
    for path in paths:
        rel(path, "changed path")
        if not any(
            path == allowed or path.startswith(allowed.rstrip("/") + "/")
            for allowed in leaf["write_set"]
            if isinstance(allowed, str)
        ):
            raise Error("changed path outside write_set")
    accept = value["acceptance"]
    if (
        not isinstance(accept, dict)
        or set(accept) - {"command", "exit_code", "summary", "evidence_path", "sha256"}
        or {"command", "exit_code", "summary"} - set(accept)
        or accept["command"] != leaf["acceptance_command"]
        or (
            accept["exit_code"] is not None
            and (
                not isinstance(accept["exit_code"], int)
                or isinstance(accept["exit_code"], bool)
                or not 0 <= accept["exit_code"] <= 255
            )
        )
        or not isinstance(accept["summary"], str)
        or len(accept["summary"]) > MAX_ACCEPTANCE_SUMMARY
    ):
        raise Error("invalid acceptance")
    if ("evidence_path" in accept) != ("sha256" in accept):
        raise Error("acceptance evidence digest pair required")
    if "evidence_path" in accept:
        rel(accept["evidence_path"], "acceptance evidence")
        require_sha256(accept["sha256"], "invalid acceptance sha256")
    blockers = value["blockers"]
    if not isinstance(blockers, list) or len(blockers) > MAX_BLOCKERS:
        raise Error("invalid blockers")
    for blocker in blockers:
        if (
            not isinstance(blocker, dict)
            or set(blocker) - {"code", "summary", "evidence_path", "sha256"}
            or {"code", "summary"} - set(blocker)
            or not isinstance(blocker["code"], str)
            or not blocker["code"]
            or len(blocker["code"]) > MAX_BLOCKER_CODE
            or not isinstance(blocker["summary"], str)
            or len(blocker["summary"]) > MAX_BLOCKER_SUMMARY
        ):
            raise Error("invalid blocker")
        if ("evidence_path" in blocker) != ("sha256" in blocker):
            raise Error("blocker evidence digest pair required")
        if "evidence_path" in blocker:
            rel(blocker["evidence_path"], "blocker evidence")
            require_sha256(blocker["sha256"], "invalid blocker sha256")
    notes = value["notes"]
    if (
        not isinstance(notes, list)
        or len(notes) > MAX_NOTES
        or any(
            not isinstance(x, dict)
            or set(x) != {"type", "message"}
            or x["type"] not in NOTE_TYPES
            or not isinstance(x["message"], str)
            or len(x["message"]) > MAX_NOTE_MESSAGE
            for x in notes
        )
    ):
        raise Error("invalid typed notes")
    rem = value["unstarted_remainder"]
    if (
        not isinstance(rem, list)
        or len(rem) > MAX_REMAINDER
        or any(not isinstance(x, str) or not x or len(x) > MAX_REMAINDER_ITEM for x in rem)
    ):
        raise Error("invalid unstarted_remainder")
    if not isinstance(value["commit_hash"], str) or (
        value["commit_hash"] and not COMMIT.fullmatch(value["commit_hash"])
    ):
        raise Error("invalid commit_hash")
    if value["status"] == "completed" and accept["exit_code"] != 0:
        raise Error("completed return requires exit 0")
    # Any status that changed files must name the commit holding them, so a
    # non-completed stop leaves the worktree in a state the parent can act on.
    if paths and not value["commit_hash"]:
        raise Error("changed work requires a commit hash")
    if value["status"] in RETURN_STATUSES - {"completed"} and not blockers:
        raise Error("non-completed returns require blockers")
    if value["status"] == "oversized" and not rem:
        raise Error("oversized return requires unstarted_remainder")
    return value


def record(args):
    directory, data, plan, leafs = mutating_run(args)
    raw = Path(args.return_file).read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid step return JSON") from exc
    sid = value.get("step_id") if isinstance(value, dict) else ""
    step = data["steps"].get(sid)
    if step is None or step["status"] != "in_progress":
        raise Error("return is not for current in_progress step")
    if len(raw) > MAX_RETURN:
        reject_return(
            directory,
            data,
            step,
            sid,
            "bounded-step-return-v1 exceeds 8 KiB",
            "oversized_return",
            "return exceeds 8 KiB",
        )
        raise Error("bounded-step-return-v1 exceeds 8 KiB")
    try:
        value = valid_return(value, data, step, leafs[sid])
    except Error as exc:
        if str(exc) == "changed path outside write_set":
            reject_return(
                directory,
                data,
                step,
                sid,
                "oversized: changed path outside write_set",
                "scope_expanded",
                "changed path outside write_set",
            )
        raise
    fingerprint = digest(
        {
            key: value[key]
            for key in (
                "status",
                "changed_paths",
                "acceptance",
                "blockers",
                "notes",
                "unstarted_remainder",
            )
        }
    )
    copy = directory / "returns" / sid / f"{step['attempt_id']}.json"
    write(copy, value, MAX_RETURN)
    step["return_path"] = str(copy.relative_to(directory))
    step["return_sha256"] = digest(value)
    step["returned_commit"] = value["commit_hash"]
    step["reason"] = (
        value["acceptance"]["summary"]
        or (value["blockers"][0]["summary"] if value["blockers"] else value["status"])
    )[:480]
    previous = step["fingerprints"][-1] if step["fingerprints"] else ""
    step["fingerprints"].append(fingerprint)
    step["fingerprints"] = step["fingerprints"][-5:]
    if value["status"] in {"completed", "oversized"}:
        step.update(status=value["status"], retry_allowed=False)
    elif previous == fingerprint:
        stop_step(
            step,
            "blocked",
            "blocked:no_progress",
            "blocked:no_progress",
            "repeated non-completed progress fingerprint",
        )
    elif data.get("retry_policy") == ESCALATING_RETRY_POLICY and not retry_outcome(value):
        step.update(status=value["status"], retry_allowed=False)
    elif step["attempt_count"] >= step["max_attempts"]:
        stop_step(
            step,
            "blocked",
            "blocked:retry_exhausted",
            "blocked:retry_exhausted",
            "attempt limit reached with differing progress fingerprint",
        )
    elif (
        data.get("retry_policy") == ESCALATING_RETRY_POLICY
        and needs_higher_tier(step, retry_outcome(value))
        and step["current_tier"] == PORTABLE_TIERS[-1]
    ):
        stop_step(
            step,
            "blocked",
            "blocked:retry_ceiling_reached",
            "blocked:retry_ceiling_reached",
            "eligible retry requires a tier above deep",
        )
    else:
        step["status"] = value["status"]
    if step["reason"] not in {
        "blocked:no_progress",
        "blocked:retry_exhausted",
        "blocked:retry_ceiling_reached",
    }:
        step["blockers"] = value["blockers"]
    event(
        directory,
        data,
        "record-return",
        step_id=sid,
        status=step["status"],
        attempt_id=step["attempt_id"],
        fingerprint=fingerprint,
    )
    return result2("record-return", args, sid, step, progress_fingerprint=fingerprint)


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


def safe_run_contents(directory):
    allowed = {
        "checkpoint.json",
        "events.jsonl",
        "plan.json",
        "returns",
        "retry-remediations",
        "worktree-results",
        "usage",
    }
    children = list(directory.iterdir())
    if any(child.is_symlink() for child in children):
        raise Error("symlink in run directory")
    names = {child.name for child in children}
    if not {"checkpoint.json", "events.jsonl", "plan.json"}.issubset(names):
        raise Error("missing required v2 contents")
    if names - allowed:
        raise Error("unexpected v2 contents")
    for name in ("checkpoint.json", "events.jsonl", "plan.json"):
        if not (directory / name).is_file():
            raise Error("unexpected v2 contents")
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


def classify_legacy(directory, current):
    data = load1(directory)
    validate_events1(directory, data)
    if data["plan_id"] != directory.name:
        raise Error("legacy directory identity mismatch")
    timestamp(data["updated_at"], "legacy updated_at")
    states = {step["state"] for step in data["steps"].values()}
    entry = {
        "plan_id": data["plan_id"],
        "run_id": "",
        "contract_version": 1,
        "updated_at": data["updated_at"],
        "legacy": True,
        "_path": directory,
    }
    if states == {"integrated"}:
        outcome = "completed"
    elif states and states.issubset({"discarded", "superseded"}):
        outcome = (
            "discarded"
            if states == {"discarded"}
            else ("superseded" if states == {"superseded"} else "abandoned")
        )
    elif states.issubset({"integrated", "discarded", "superseded"}):
        raise Error("ambiguous legacy terminal state")
    else:
        entry.update(run_status="active", outcome=None, closed_at=None, purge_after=None)
        entry["retention_state"] = "active"
        return entry
    closed_at = data["updated_at"]
    purge_after = retained_until(closed_at, outcome)
    entry.update(
        run_status="closed",
        outcome=outcome,
        closed_at=closed_at,
        purge_after=purge_after,
        retention_state="eligible" if current >= timestamp(purge_after, "purge_after") else "kept",
    )
    return entry


def classify_v2(plan_id, directory, current):
    safe_run_contents(directory)
    checkpoint = read_json(directory / "checkpoint.json", "malformed v2 checkpoint")
    if checkpoint.get("schema") not in {2, 3, 4}:
        raise Error("unknown checkpoint schema")
    if checkpoint.get("plan_id") != plan_id or checkpoint.get("run_id") != directory.name:
        raise Error("v2 directory identity mismatch")
    if len(canon(checkpoint) + b"\n") > MAX_CHECKPOINT:
        raise Error("v2 checkpoint exceeds bounded limit")
    plan = read_json(directory / "plan.json", "blocked:plan_tampered")
    if digest(plan) != checkpoint.get("plan_hash") or not SHA.fullmatch(
        checkpoint.get("plan_hash", "")
    ):
        raise Error("blocked:plan_tampered")
    plan_result = plan_validator()(plan, capability_binding=checkpoint_binding(checkpoint))
    ready_key = "dispatch_ready" if checkpoint["schema"] == 4 else "resume_ready"
    if (
        not plan_result.get(ready_key)
        or plan_result.get("contract_version") != checkpoint["schema"]
    ):
        raise Error("blocked:plan_tampered")
    validate_steps2(checkpoint, leaves_by_id(plan))
    validate_retry_artifacts(directory, checkpoint)
    returns = directory / "returns"
    if returns.exists() and any(
        step_dir.name not in checkpoint["steps"] for step_dir in returns.iterdir()
    ):
        raise Error("unexpected returns step")
    remediations = directory / "retry-remediations"
    if remediations.exists() and any(
        step_dir.name not in checkpoint["steps"] for step_dir in remediations.iterdir()
    ):
        raise Error("unexpected retry-remediations step")
    lifecycle(checkpoint)
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
            try:
                raw = read_json(plan / "checkpoint.json", "malformed legacy checkpoint")
                if raw.get("schema_version") != 1:
                    raise Error("unknown checkpoint schema")
                entries.append(classify_legacy(plan, current))
            except (Error, OSError, json.JSONDecodeError, TypeError) as exc:
                message = str(exc)
                code = (
                    "ambiguous_legacy"
                    if "ambiguous legacy" in message
                    else (
                        "unknown_schema"
                        if "unknown checkpoint schema" in message
                        else (
                            "malformed_checkpoint"
                            if "malformed" in message
                            else "invalid_checkpoint"
                        )
                    )
                )
                invalid.append(invalid_entry(base, plan, code, message))
            continue
        if not children or any(not child.is_dir() for child in children):
            invalid.append(
                invalid_entry(base, plan, "unexpected_contents", "v2 plan has unexpected contents")
            )
            continue
        for run in sorted(children, key=lambda path: path.name):
            try:
                uuid4(run.name)
                entries.append(classify_v2(plan.name, run, current))
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
    if entry["contract_version"] in {2, 3, 4}:
        safe_run_contents(path)
        returns = path / "returns"
        if returns.exists() and any(
            step_dir.name not in entry["_step_ids"] for step_dir in returns.iterdir()
        ):
            raise Error("refusing changed returns purge target")
    else:
        children = list(path.iterdir())
        if {child.name for child in children} != {"checkpoint.json", "events.jsonl"} or any(
            child.is_symlink() or not child.is_file() for child in children
        ):
            raise Error("refusing changed legacy purge target")
    parent_path = path.parent
    shutil.rmtree(path)
    if entry["contract_version"] in {2, 3, 4}:
        try:
            parent_path.rmdir()
        except OSError:
            pass


def collect_ledgers(base, plan_filter, current, remove):
    entries, invalid = scan_ledgers(base, plan_filter, current)
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
    )


def list_runs(args):
    plan_filter = ident(args.plan_id, "plan id") if args.plan_id else None
    entries, invalid = scan_ledgers(root(args), plan_filter, timestamp(now()))
    return bounded_report("list", {"runs": entries, "invalid": invalid})


def gc(args):
    if not args.dry_run:
        parent(args.actor)
    plan_filter = ident(args.plan_id, "plan id") if args.plan_id else None
    return collect_ledgers(root(args), plan_filter, timestamp(now()), remove=not args.dry_run)


def purge(args):
    parent(args.actor)
    plan_id = ident(args.plan_id, "plan id")
    if bool(args.run_id) == bool(args.legacy):
        raise Error("purge requires exactly one of --run-id or --legacy")
    if args.before_retention:
        bounded_reason(args.reason, "--before-retention", required=True)
    else:
        bounded_reason(args.reason, "purge")
    target_run = "" if args.legacy else uuid4(args.run_id)
    entries, invalid = scan_ledgers(root(args), plan_id, timestamp(now()))
    matches = [
        entry
        for entry in entries
        if (entry["legacy"] if args.legacy else entry["run_id"] == target_run)
    ]
    if not matches:
        detail = invalid[0]["summary"] if invalid else "exact closed run not found"
        raise Error(detail)
    if len(matches) != 1 or matches[0]["run_status"] != "closed":
        raise Error("purge target must be exactly one closed run")
    entry = matches[0]
    early = timestamp(now()) < timestamp(entry["purge_after"], "purge_after")
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


def summary(data):
    steps = data["steps"]
    rows = [
        {
            "id": s["id"],
            "status": s["status"],
            "attempt_id": s["attempt_id"],
            "agent_id": s["agent_id"],
            "progress_fingerprint": s["fingerprints"][-1] if s["fingerprints"] else "",
            "reason": s["reason"][:480],
            **(
                {
                    "current_tier": s["current_tier"],
                    "current_assignment": s["current_assignment"],
                }
                if data.get("retry_policy") == ESCALATING_RETRY_POLICY
                else {}
            ),
        }
        for s in ordered_steps(steps)
    ]
    counts = {
        status: sum(s["status"] == status for s in steps.values())
        for status in sorted({s["status"] for s in steps.values()})
    }
    actions = [
        f"ready:{s['id']}"
        for s in ordered_steps(steps)
        if s["status"] in {"pending", "blocked", "failed"}
        and s["retry_allowed"]
        and all(steps[d]["status"] == "cleaned" for d in s["dependencies"])
    ]
    result = {
        "ok": True,
        "contract_version": data["schema"],
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "plan_hash": data["plan_hash"],
        **(
            {"retry_policy": data["retry_policy"]}
            if data.get("retry_policy") == ESCALATING_RETRY_POLICY
            else {}
        ),
        "run_status": data["run_status"],
        "outcome": data["outcome"],
        "closed_at": data["closed_at"],
        "purge_after": data["purge_after"],
        "objective": data["objective"],
        "scope_summary": data["scope_summary"],
        "approved_decisions": data["approved_decisions"],
        "counts": counts,
        "next_actions": actions,
        "blockers": [
            {"id": s["id"], "reason": s["reason"]}
            for s in rows
            if s["status"] in {"blocked", "failed", "oversized"}
        ],
        "steps": rows,
        "truncated": False,
        "omitted_count": 0,
    }
    return bounded_step_summary(result)


def bounded_step_summary(result):
    result.pop("summary_proxy_tokens", None)
    while proxy_tokens(result) > MAX_TOKENS and result["steps"]:
        result["steps"].pop()
        result["truncated"] = True
        result["omitted_count"] += 1
    result["summary_proxy_tokens"] = proxy_tokens(result)
    return result


def show(args):
    if not args.run_id:
        data = load1(plan_dir(args))
        result = {
            **legacy_fields(),
            "ok": True,
            "plan_id": data["plan_id"],
            "steps": list(data["steps"].values()),
        }
        result["summary_proxy_tokens"] = proxy_tokens(result)
        if result["summary_proxy_tokens"] > MAX_TOKENS:
            raise Error("legacy ledger summary exceeds 1200 proxy tokens")
        return result
    directory, data, plan, leafs = load2(args)
    if args.step_id:
        sid = ident(args.step_id, "step id")
        if sid not in data["steps"]:
            raise Error("unknown step id")
        step = data["steps"][sid]
        result = {
            "ok": True,
            "contract_version": data["schema"],
            "plan_id": data["plan_id"],
            "run_id": data["run_id"],
            "plan_hash": data["plan_hash"],
            **(
                {"retry_policy": data["retry_policy"]}
                if data.get("retry_policy") == ESCALATING_RETRY_POLICY
                else {}
            ),
            "run_status": data["run_status"],
            "outcome": data["outcome"],
            "closed_at": data["closed_at"],
            "purge_after": data["purge_after"],
            "step": {
                "id": step["id"],
                "status": step["status"],
                "attempt_count": step["attempt_count"],
                "max_attempts": step["max_attempts"],
                "agent_id": step["agent_id"],
                "attempt_id": step["attempt_id"],
                "progress_fingerprint": step["fingerprints"][-1] if step["fingerprints"] else "",
                "reason": step["reason"][:480],
                "blockers": step["blockers"],
                "return_path": step["return_path"],
                "return_sha256": step["return_sha256"],
                "retry_allowed": step["retry_allowed"],
                "returned_commit": step["returned_commit"],
                "integrated_commit": step["integrated_commit"],
                "integration_result_path": step["integration_result_path"],
                "integration_result_sha256": step["integration_result_sha256"],
                "cleanup_result_path": step["cleanup_result_path"],
                "cleanup_result_sha256": step["cleanup_result_sha256"],
                **(
                    {
                        "current_tier": step["current_tier"],
                        "same_tier_retry_used": step["same_tier_retry_used"],
                        "current_assignment": step["current_assignment"],
                        "retry_remediation_path": step["retry_remediation_path"],
                        "retry_remediation_sha256": step["retry_remediation_sha256"],
                    }
                    if data.get("retry_policy") == ESCALATING_RETRY_POLICY
                    else {}
                ),
            },
            "omitted_blockers": 0,
        }
        while proxy_tokens(result) > MAX_TOKENS and result["step"]["blockers"]:
            result["step"]["blockers"].pop()
            result["omitted_blockers"] += 1
        result["summary_proxy_tokens"] = proxy_tokens(result)
        return result
    result = summary(data)
    if (directory / "usage").exists():
        result["trace"] = {"initialized": True}
        return bounded_step_summary(result)
    return result


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


def usage_path(directory):
    return directory / "usage"


def trace_run(args, require_usage=True, require_open=False):
    parent(args.actor)
    directory, data, plan, leafs = load2(args)
    if data["schema"] not in {3, 4}:
        raise Error("tracing requires a contract version 3 or 4 run")
    usage = usage_path(directory)
    if require_usage and not usage.exists():
        raise Error("trace-init is required")
    metadata = read_json(usage / "trace.json", "invalid usage trace") if usage.exists() else None
    if require_open and metadata and metadata.get("closed_at"):
        raise Error("usage trace is closed")
    return directory, data, plan, leafs, usage, metadata


def trace_result(action, data, **facts):
    return {
        "ok": True,
        "action": action,
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        **facts,
    }


def trace_init(args):
    directory, data, _plan, _leafs, usage, _metadata = trace_run(args, require_usage=False)
    active_run(data)
    if usage.exists():
        raise Error("tracing is already initialized")
    write(
        usage / "trace.json",
        {"schema": "planning-usage-trace-v1", "initialized_at": now(), "closed_at": ""},
        MAX_USAGE,
    )
    return trace_result("trace-init", data)


def trace_record(args):
    directory, data, _plan, _leafs, _usage, _metadata = trace_run(args, require_open=True)
    value = valid_usage_summary(read_json(args.usage_file, "cannot read usage file"))
    supplied_identity = (value["run_id"],)
    checkpoint_identity = (data["run_id"],)
    if supplied_identity == checkpoint_identity:
        pass
    else:
        raise Error("usage run identity mismatch")
    parent_identity = value["step_id"] == "parent" and value["attempt_id"] == "run"
    if value["actor"] == "parent" and not parent_identity:
        raise Error("parent usage identity must be parent/run")
    if value["actor"] == "worker":
        step = data["steps"].get(value["step_id"])
        if step is None or not step["attempt_id"] or value["attempt_id"] != step["attempt_id"]:
            raise Error("worker usage attempt identity mismatch")
        assignment = step["current_assignment"]
        if value["harness"] != assignment["harness"]:
            raise Error("worker usage harness provenance mismatch")
        if value["model"] != step["assignment"]["model_or_alias"]:
            raise Error("worker usage model provenance mismatch")
    if value["actor"] not in {"parent", "worker"}:
        raise Error("usage actor must be parent or worker")
    record_id = str(uuid.uuid4())
    relative = f"usage/records/{record_id}.json"
    write(directory / relative, value, MAX_USAGE)
    return trace_result(
        "trace-record",
        data,
        record_path=relative,
        record_sha256=digest(value),
    )


def trace_show(args):
    _directory, data, plan, _leafs, usage, _metadata = trace_run(args)
    records_dir = usage / "records"
    values = (
        []
        if not records_dir.exists()
        else [
            valid_usage_summary(read_json(path, "invalid usage record"))
            for path in sorted(records_dir.iterdir())
        ]
    )
    stages = {}
    cycles = set()
    totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    provenance = set()
    for value in values:
        stage = stages.setdefault(value["stage"], {"records": 0, "total_tokens": 0})
        stage["records"] += 1
        stage["total_tokens"] += value["total_tokens"]
        cycles.add((value["step_id"], value["attempt_id"]))
        provenance.add((value["harness"], value["model"]))
        for key in totals:
            totals[key] += value[key]
    forecast = plan_validator()(plan)["cost_advisory"]
    comparison = "indeterminate:forecast"
    findings = []
    declared = plan.get("execution_cost", {}).get("declared_model_tokens", {})
    worker_ranges = declared.get("worker_attempts") if isinstance(declared, dict) else None
    if (
        values
        and all(value["actor"] == "worker" for value in values)
        and isinstance(worker_ranges, dict)
    ):
        cycle_keys = {(value["step_id"], value["attempt_id"]) for value in values}
        ranges = [worker_ranges.get(step_id) for step_id, _attempt_id in cycle_keys]
        if all(
            isinstance(value, dict)
            and set(value) == {"low", "expected", "high"}
            and all(isinstance(value[key], int) for key in value)
            for value in ranges
        ):
            low = sum(value["low"] for value in ranges)
            high = sum(value["high"] for value in ranges)
            observed = totals["total_tokens"]
            comparison = {"lane": "worker_attempts", "low": low, "observed": observed, "high": high}
            if observed < low or observed > high:
                findings.append("PLANCOST-COMPARABLE-OBSERVED-DRIFT")
    result = {
        "ok": True,
        "schema": "planning-usage-advisory-v1",
        "mode": "advisory",
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "records": len(values),
        "cycles": len(cycles),
        "stages": stages,
        "provider_measured": totals,
        "provenance": [
            {"harness": harness, "model": model} for harness, model in sorted(provenance)
        ],
        "forecast_comparison": (
            comparison
            if comparison != "indeterminate:forecast"
            else (
                "indeterminate:provenance"
                if forecast.get("declared_total_run") is not None
                else comparison
            )
        ),
        "findings": findings,
    }
    while proxy_tokens(result) > MAX_USAGE_TOKENS and result["provenance"]:
        result["provenance"].pop()
    result["summary_proxy_tokens"] = proxy_tokens(result)
    return result


def trace_close(args):
    _directory, data, _plan, _leafs, usage, metadata = trace_run(args)
    if metadata.get("closed_at"):
        raise Error("usage trace is already closed")
    metadata["closed_at"] = now()
    write(usage / "trace.json", metadata, MAX_USAGE)
    return trace_result("trace-close", data)


def validate(args):
    if not args.run_id:
        data = load1(plan_dir(args))
        validate_events1(plan_dir(args), data)
        return {
            **legacy_fields(),
            "ok": True,
            "plan_id": data["plan_id"],
            "errors": [],
        }
    directory, data, plan, leafs = load2(args)
    if args.closeout:
        unfinished = [
            step["id"]
            for step in data["steps"].values()
            if step["status"] in {"completed", "integrated"}
        ]
        if unfinished:
            raise Error("closeout requires every successful step to be cleaned")
    validate_events2(directory, data)
    return {
        "ok": True,
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "plan_hash": data["plan_hash"],
        **(
            {"retry_policy": data["retry_policy"]}
            if data.get("retry_policy") == ESCALATING_RETRY_POLICY
            else {}
        ),
        "run_status": data["run_status"],
        "outcome": data["outcome"],
        "closed_at": data["closed_at"],
        "purge_after": data["purge_after"],
        "errors": [],
        "closeout": bool(args.closeout),
    }


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--ledger-root")
    parser.add_argument("--plan-id")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--actor", required=True)
    init.add_argument("--approved", action="store_true")
    init.add_argument("--steps-json", required=True)
    init2 = commands.add_parser("init-v2")
    init2.add_argument("--actor", required=True)
    init2.add_argument("--approved", action="store_true")
    init2.add_argument("--plan-file", required=True)
    init2.add_argument("--assignments-file", required=True)
    init3_parser = commands.add_parser("init-v3")
    init3_parser.add_argument("--actor", required=True)
    init3_parser.add_argument("--approved", action="store_true")
    init3_parser.add_argument("--plan-file", required=True)
    init3_parser.add_argument("--assignments-file", required=True)
    init4_parser = commands.add_parser("init-v4")
    init4_parser.add_argument("--actor", required=True)
    init4_parser.add_argument("--approved", action="store_true")
    init4_parser.add_argument("--plan-file", required=True)
    init4_parser.add_argument("--assignments-file", required=True)
    init4_parser.add_argument("--capability-binding-file", required=True)
    trans = commands.add_parser("transition")
    trans.add_argument("--actor", required=True)
    trans.add_argument("--run-id")
    trans.add_argument("--step-id", required=True)
    trans.add_argument("--to", required=True)
    trans.add_argument("--agent-id", default="")
    trans.add_argument("--harness", default="")
    trans.add_argument("--model-or-alias", default="")
    trans.add_argument("--capability-binding-file", default="")
    trans.add_argument("--summary", default="")
    trans.add_argument("--retry", action="store_true")
    trans.add_argument("--retry-remediation-file", default="")
    trans.add_argument("--evidence-path", default="")
    trans.add_argument("--blocker-code", default="")
    trans.add_argument("--worktree-result", default="")
    rec = commands.add_parser("record-return")
    rec.add_argument("--actor", required=True)
    rec.add_argument("--run-id")
    rec.add_argument("--return-file", required=True)
    sh = commands.add_parser("show")
    sh.add_argument("--run-id")
    sh.add_argument("--step-id", default="")
    va = commands.add_parser("validate")
    va.add_argument("--run-id")
    va.add_argument("--closeout", action="store_true")
    commands.add_parser("list")
    close = commands.add_parser("close")
    close.add_argument("--actor", required=True)
    close.add_argument("--run-id", required=True)
    close.add_argument("--outcome", choices=("completed", "blocked", "abandoned"), required=True)
    close.add_argument("--reason", default="")
    reopen = commands.add_parser("reopen")
    reopen.add_argument("--actor", required=True)
    reopen.add_argument("--run-id", required=True)
    reopen.add_argument("--reason", required=True)
    trace_init_parser = commands.add_parser("trace-init")
    trace_init_parser.add_argument("--actor", required=True)
    trace_init_parser.add_argument("--run-id", required=True)
    trace_record_parser = commands.add_parser("trace-record")
    trace_record_parser.add_argument("--actor", required=True)
    trace_record_parser.add_argument("--run-id", required=True)
    trace_record_parser.add_argument("--usage-file", required=True)
    trace_show_parser = commands.add_parser("trace-show")
    trace_show_parser.add_argument("--actor", required=True)
    trace_show_parser.add_argument("--run-id", required=True)
    trace_close_parser = commands.add_parser("trace-close")
    trace_close_parser.add_argument("--actor", required=True)
    trace_close_parser.add_argument("--run-id", required=True)
    garbage = commands.add_parser("gc")
    garbage.add_argument("--actor", default="")
    garbage.add_argument("--dry-run", action="store_true")
    purging = commands.add_parser("purge")
    purging.add_argument("--actor", required=True)
    purging.add_argument("--run-id")
    purging.add_argument("--legacy", action="store_true")
    purging.add_argument("--before-retention", action="store_true")
    purging.add_argument("--reason", default="")
    return parser


def main(argv=None):
    args = parse().parse_args(argv)
    try:
        if args.command == "init":
            value = init1(args)
        elif args.command == "init-v2":
            value = init2(args)
        elif args.command == "init-v3":
            value = init3(args)
        elif args.command == "init-v4":
            value = init4(args)
        elif args.command == "transition":
            value = transition2(args) if args.run_id else transition1(args)
        elif args.command == "record-return":
            value = record(args)
        elif args.command == "show":
            value = show(args)
        elif args.command == "validate":
            value = validate(args)
        elif args.command == "list":
            value = list_runs(args)
        elif args.command == "close":
            value = close2(args)
        elif args.command == "reopen":
            value = reopen2(args)
        elif args.command == "trace-init":
            value = trace_init(args)
        elif args.command == "trace-record":
            value = trace_record(args)
        elif args.command == "trace-show":
            value = trace_show(args)
        elif args.command == "trace-close":
            value = trace_close(args)
        elif args.command == "gc":
            value = gc(args)
        else:
            value = purge(args)
        return out(value)
    except Error as exc:
        return out({"ok": False, "error": str(exc)}, 3)
    except OSError as exc:
        return out({"ok": False, "error": f"I/O failure: {exc}"}, 4)


if __name__ == "__main__":
    sys.exit(main())
