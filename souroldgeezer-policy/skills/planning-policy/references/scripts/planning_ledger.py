#!/usr/bin/env python3
"""Parent-owned checkpoint ledger; ``init`` and no-run-id operations are v1."""

from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, re, subprocess, sys, tempfile, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_CHECKPOINT = 16 * 1024
MAX_RETURN = 8 * 1024
MAX_TOKENS = 1200
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


class Error(Exception):
    pass


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def rel(value, label="path", maximum=240):
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


def parent(actor):
    if actor != "parent":
        raise Error("only actor 'parent' may mutate a ledger")


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
    if any(d not in steps for s in steps.values() for d in s["dependencies"]):
        raise Error("unknown dependency")
    visiting, visited = set(), set()

    def visit(step_id):
        if step_id in visiting:
            raise Error("legacy dependency cycle")
        if step_id in visited:
            return
        visiting.add(step_id)
        for dependency in steps[step_id]["dependencies"]:
            visit(dependency)
        visiting.remove(step_id)
        visited.add(step_id)

    for step_id in steps:
        visit(step_id)
    return steps


def load1(directory):
    path = directory / "checkpoint.json"
    if not path.is_file():
        raise Error("ledger checkpoint does not exist")
    data = json.loads(path.read_text())
    if (
        data.get("schema_version") != 1
        or data.get("approved") is not True
        or not isinstance(data.get("steps"), dict)
        or len(data["steps"]) < 2
    ):
        raise Error("invalid legacy checkpoint")
    if len(canon(data) + b"\n") > MAX_CHECKPOINT:
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
    visiting, visited = set(), set()

    def visit(step_id):
        if step_id in visiting:
            raise Error("legacy dependency cycle")
        if step_id in visited:
            return
        visiting.add(step_id)
        for dep in data["steps"][step_id]["dependencies"]:
            visit(dep)
        visiting.remove(step_id)
        visited.add(step_id)

    for step_id in data["steps"]:
        visit(step_id)
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
    path = directory / "events.jsonl"
    if not path.is_file():
        raise Error("legacy events.jsonl does not exist")
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
    parent(args.actor)
    if not args.approved:
        raise Error("--approved is required")
    directory = plan_dir(args)
    if directory.exists():
        raise Error("ledger already exists; init is not an overwrite operation")
    timestamp = now()
    data = {
        "schema_version": 1,
        "plan_id": args.plan_id,
        "approved": True,
        "created_at": timestamp,
        "updated_at": timestamp,
        "event_sequence": 1,
        "steps": parse_v1(args.steps_json),
    }
    write(directory / "checkpoint.json", data)
    (directory / "events.jsonl").write_bytes(
        canon(
            {
                "sequence": 1,
                "at": timestamp,
                "actor": "parent",
                "action": "init",
                "plan_id": args.plan_id,
                "step_count": len(data["steps"]),
            }
        )
        + b"\n"
    )
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
    sid = ident(args.step_id, "step id")
    if sid not in data["steps"]:
        raise Error("unknown step id")
    step = data["steps"][sid]
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


def read_plan(path):
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise Error("cannot read plan file") from exc
    result = plan_validator()(data)
    if not result.get("valid") or not result.get("dispatch_ready"):
        raise Error("plan is not dispatch-ready")
    return data


def assignments(path, plan):
    try:
        values = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise Error("cannot read assignments file") from exc
    if not isinstance(values, list):
        raise Error("assignments file must be an array")
    leaves = {x["id"]: x for x in plan["leaves"]}
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
    parent(args.actor)
    if not args.approved:
        raise Error("--approved is required")
    plan = read_plan(args.plan_file)
    assigned = assignments(args.assignments_file, plan)
    directory = plan_dir(args)
    run_id = str(uuid.uuid4())
    run = directory / run_id
    if run.exists():
        raise Error("generated run already exists")
    leaves = {x["id"]: x for x in plan["leaves"]}
    timestamp = now()
    steps = {
        sid: {
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
        }
        for sid, leaf in leaves.items()
    }
    data = {
        "schema": 2,
        "plan_id": args.plan_id,
        "run_id": run_id,
        "plan_hash": digest(plan),
        "objective": plan["objective"][:240],
        "scope_summary": plan["scope_summary"][:480],
        "approved_decisions": plan["approved_decisions"],
        "created_at": timestamp,
        "updated_at": timestamp,
        "event_sequence": 1,
        "steps": steps,
    }
    write(run / "plan.json", plan, 64 * 1024)
    write(run / "checkpoint.json", data)
    (run / "events.jsonl").write_bytes(
        canon(
            {
                "sequence": 1,
                "at": timestamp,
                "actor": "parent",
                "action": "init-v2",
                "plan_id": args.plan_id,
                "run_id": run_id,
                "plan_hash": data["plan_hash"],
            }
        )
        + b"\n"
    )
    return {
        "ok": True,
        "action": "init-v2",
        "plan_id": args.plan_id,
        "run_id": run_id,
        "plan_hash": data["plan_hash"],
    }


def load2(args):
    directory = v2_dir(args)
    path = directory / "checkpoint.json"
    if not path.is_file():
        raise Error("unknown run id")
    data = json.loads(path.read_text())
    if data.get("schema") != 2 or data.get("run_id") != args.run_id:
        raise Error("invalid v2 checkpoint")
    try:
        plan = json.loads((directory / "plan.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise Error("blocked:plan_tampered") from exc
    if digest(plan) != data.get("plan_hash") or not SHA.fullmatch(data.get("plan_hash", "")):
        raise Error("blocked:plan_tampered")
    if not plan_validator()(plan).get("dispatch_ready"):
        raise Error("blocked:plan_tampered")
    leafs = {x["id"]: x for x in plan["leaves"]}
    if set(data.get("steps", {})) != set(leafs):
        raise Error("blocked:plan_tampered")
    for sid, step in data["steps"].items():
        if (
            step.get("dependencies") != leafs[sid]["dependencies"]
            or step.get("max_attempts") != leafs[sid]["max_attempts"]
        ):
            raise Error("blocked:plan_tampered")
        if not 0 <= step.get("attempt_count", -1) <= step["max_attempts"]:
            raise Error("blocked:plan_tampered")
    return directory, data, plan, leafs


def ready(args, data, step):
    if not isinstance(args.agent_id, str) or not 1 <= len(args.agent_id) <= 128:
        raise Error("ready requires bounded --agent-id")
    if step["status"] not in {"pending", "blocked", "failed"} or not step["retry_allowed"]:
        raise Error("step cannot be readied")
    if step["status"] != "pending" and (not args.retry or not args.summary):
        raise Error("retry requires --retry and bounded --summary")
    if any(data["steps"][dep]["status"] != "completed" for dep in step["dependencies"]):
        raise Error("dependencies are not complete")
    if step["attempt_count"] >= step["max_attempts"]:
        raise Error("blocked:retry_exhausted")
    step["attempt_count"] += 1
    step["agent_id"] = args.agent_id
    step["attempt_id"] = str(uuid.uuid4())
    step["status"] = "ready"
    step["reason"] = (args.summary or "ready")[:480]


def transition2(args):
    parent(args.actor)
    directory, data, plan, leafs = load2(args)
    sid = ident(args.step_id, "step id")
    if sid not in data["steps"]:
        raise Error("unknown step id")
    step = data["steps"][sid]
    old = step["status"]
    new = args.to
    if new == "ready":
        ready(args, data, step)
    elif new == "in_progress":
        if old != "ready":
            raise Error("only ready steps can start")
        step["status"] = "in_progress"
        step["reason"] = (args.summary or "in progress")[:480]
    elif new == "integrated":
        if old != "completed":
            raise Error("only completed steps can integrate")
        step["status"] = "integrated"
        step["reason"] = (args.summary or "integrated")[:480]
    else:
        raise Error("v2 transition only permits ready, in_progress, or integrated")
    event(
        directory,
        data,
        "transition-v2",
        step_id=sid,
        from_status=old,
        to_status=step["status"],
        attempt_id=step["attempt_id"],
    )
    return {
        "ok": True,
        "action": "transition",
        "run_id": args.run_id,
        "step_id": sid,
        "status": step["status"],
        "attempt_id": step["attempt_id"],
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
    if value["status"] not in {"completed", "blocked", "failed", "oversized"}:
        raise Error("invalid return status")
    paths = value["changed_paths"]
    if not isinstance(paths, list) or len(paths) > 32 or len(set(paths)) != len(paths):
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
        or len(accept["summary"]) > 480
    ):
        raise Error("invalid acceptance")
    if ("evidence_path" in accept) != ("sha256" in accept):
        raise Error("acceptance evidence digest pair required")
    if "evidence_path" in accept:
        rel(accept["evidence_path"], "acceptance evidence")
        0 if SHA.fullmatch(accept["sha256"]) else (_ for _ in ()).throw(
            Error("invalid acceptance sha256")
        )
    blockers = value["blockers"]
    if not isinstance(blockers, list) or len(blockers) > 8:
        raise Error("invalid blockers")
    for blocker in blockers:
        if (
            not isinstance(blocker, dict)
            or set(blocker) - {"code", "summary", "evidence_path", "sha256"}
            or {"code", "summary"} - set(blocker)
            or not isinstance(blocker["code"], str)
            or not blocker["code"]
            or len(blocker["code"]) > 120
            or not isinstance(blocker["summary"], str)
            or len(blocker["summary"]) > 240
        ):
            raise Error("invalid blocker")
        if ("evidence_path" in blocker) != ("sha256" in blocker):
            raise Error("blocker evidence digest pair required")
        if "evidence_path" in blocker:
            rel(blocker["evidence_path"], "blocker evidence")
            0 if SHA.fullmatch(blocker["sha256"]) else (_ for _ in ()).throw(
                Error("invalid blocker sha256")
            )
    notes = value["notes"]
    if (
        not isinstance(notes, list)
        or len(notes) > 8
        or any(
            not isinstance(x, dict)
            or set(x) != {"type", "message"}
            or x["type"] not in NOTE_TYPES
            or not isinstance(x["message"], str)
            or len(x["message"]) > 480
            for x in notes
        )
    ):
        raise Error("invalid typed notes")
    rem = value["unstarted_remainder"]
    if (
        not isinstance(rem, list)
        or len(rem) > 8
        or any(not isinstance(x, str) or not x or len(x) > 240 for x in rem)
    ):
        raise Error("invalid unstarted_remainder")
    if not isinstance(value["commit_hash"], str) or (
        value["commit_hash"] and not COMMIT.fullmatch(value["commit_hash"])
    ):
        raise Error("invalid commit_hash")
    if value["status"] == "completed" and (
        accept["exit_code"] != 0 or (paths and not value["commit_hash"])
    ):
        raise Error("completed return requires exit 0 and changed work commit hash")
    if value["status"] == "completed" and accept["exit_code"] not in {0, None}:
        raise Error("failed acceptance must be failed")
    if value["status"] in {"blocked", "failed", "oversized"} and not blockers:
        raise Error("non-completed returns require blockers")
    if value["status"] == "oversized" and not rem:
        raise Error("oversized return requires unstarted_remainder")
    return value


def record(args):
    parent(args.actor)
    directory, data, plan, leafs = load2(args)
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
        step["status"] = "oversized"
        step["retry_allowed"] = False
        step["reason"] = "bounded-step-return-v1 exceeds 8 KiB"
        step["blockers"] = [{"code": "oversized_return", "summary": "return exceeds 8 KiB"}]
        event(directory, data, "record-return", step_id=sid, status="oversized")
        raise Error("bounded-step-return-v1 exceeds 8 KiB")
    try:
        value = valid_return(value, data, step, leafs[sid])
    except Error as exc:
        if str(exc) == "changed path outside write_set":
            step["status"] = "oversized"
            step["retry_allowed"] = False
            step["reason"] = "oversized: changed path outside write_set"
            step["blockers"] = [
                {"code": "scope_expanded", "summary": "changed path outside write_set"}
            ]
            event(directory, data, "record-return", step_id=sid, status="oversized")
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
    step["reason"] = (
        value["acceptance"]["summary"]
        or (value["blockers"][0]["summary"] if value["blockers"] else value["status"])
    )[:480]
    previous = step["fingerprints"][-1] if step["fingerprints"] else ""
    step["fingerprints"].append(fingerprint)
    step["fingerprints"] = step["fingerprints"][-5:]
    if value["status"] == "completed":
        step["status"] = "completed"
        step["retry_allowed"] = False
    elif value["status"] == "oversized":
        step["status"] = "oversized"
        step["retry_allowed"] = False
    elif previous == fingerprint:
        step["status"] = "blocked"
        step["retry_allowed"] = False
        step["reason"] = "blocked:no_progress"
    elif step["attempt_count"] >= step["max_attempts"]:
        step["status"] = "blocked"
        step["retry_allowed"] = False
        step["reason"] = "blocked:retry_exhausted"
    else:
        step["status"] = value["status"]
    step["blockers"] = value["blockers"]
    if step["reason"] == "blocked:no_progress":
        step["blockers"] = [
            {
                "code": "blocked:no_progress",
                "summary": "repeated non-completed progress fingerprint",
            }
        ]
    if step["reason"] == "blocked:retry_exhausted":
        step["blockers"] = [
            {
                "code": "blocked:retry_exhausted",
                "summary": "attempt limit reached with differing progress fingerprint",
            }
        ]
    event(
        directory,
        data,
        "record-return",
        step_id=sid,
        status=step["status"],
        attempt_id=step["attempt_id"],
        fingerprint=fingerprint,
    )
    return {
        "ok": True,
        "action": "record-return",
        "run_id": args.run_id,
        "step_id": sid,
        "status": step["status"],
        "progress_fingerprint": fingerprint,
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
        }
        for s in sorted(steps.values(), key=lambda x: x["id"])
    ]
    counts = {
        status: sum(s["status"] == status for s in steps.values())
        for status in sorted({s["status"] for s in steps.values()})
    }
    actions = [
        f"ready:{s['id']}"
        for s in sorted(steps.values(), key=lambda x: x["id"])
        if s["status"] in {"pending", "blocked", "failed"}
        and s["retry_allowed"]
        and all(steps[d]["status"] == "completed" for d in s["dependencies"])
    ]
    result = {
        "ok": True,
        "contract_version": 2,
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "plan_hash": data["plan_hash"],
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
    while (
        len(re.findall(r"\w+|[^\w\s]", json.dumps(result, sort_keys=True, separators=(",", ":"))))
        > MAX_TOKENS
        and result["steps"]
    ):
        result["steps"].pop()
        result["truncated"] = True
        result["omitted_count"] += 1
    result["summary_proxy_tokens"] = len(
        re.findall(r"\w+|[^\w\s]", json.dumps(result, sort_keys=True, separators=(",", ":")))
    )
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
        result["summary_proxy_tokens"] = len(
            re.findall(r"\w+|[^\w\s]", json.dumps(result, sort_keys=True, separators=(",", ":")))
        )
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
            "contract_version": 2,
            "plan_id": data["plan_id"],
            "run_id": data["run_id"],
            "plan_hash": data["plan_hash"],
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
            },
            "omitted_blockers": 0,
        }
        token_count = lambda value: len(
            re.findall(r"\w+|[^\w\s]", json.dumps(value, sort_keys=True, separators=(",", ":")))
        )
        while token_count(result) > MAX_TOKENS and result["step"]["blockers"]:
            result["step"]["blockers"].pop()
            result["omitted_blockers"] += 1
        result["summary_proxy_tokens"] = token_count(result)
        return result
    return summary(data)


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
    return {
        "ok": True,
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "plan_hash": data["plan_hash"],
        "errors": [],
    }


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--ledger-root")
    parser.add_argument("--plan-id", required=True)
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
    trans = commands.add_parser("transition")
    trans.add_argument("--actor", required=True)
    trans.add_argument("--run-id")
    trans.add_argument("--step-id", required=True)
    trans.add_argument("--to", required=True)
    trans.add_argument("--agent-id", default="")
    trans.add_argument("--summary", default="")
    trans.add_argument("--retry", action="store_true")
    trans.add_argument("--evidence-path", default="")
    trans.add_argument("--blocker-code", default="")
    rec = commands.add_parser("record-return")
    rec.add_argument("--actor", required=True)
    rec.add_argument("--run-id")
    rec.add_argument("--return-file", required=True)
    sh = commands.add_parser("show")
    sh.add_argument("--run-id")
    sh.add_argument("--step-id", default="")
    va = commands.add_parser("validate")
    va.add_argument("--run-id")
    return parser


def main(argv=None):
    args = parse().parse_args(argv)
    try:
        if args.command == "init":
            value = init1(args)
        elif args.command == "init-v2":
            value = init2(args)
        elif args.command == "transition":
            value = transition2(args) if args.run_id else transition1(args)
        elif args.command == "record-return":
            value = record(args)
        elif args.command == "show":
            value = show(args)
        else:
            value = validate(args)
        return out(value)
    except Error as exc:
        return out({"ok": False, "error": str(exc)}, 3)
    except OSError as exc:
        return out({"ok": False, "error": f"I/O failure: {exc}"}, 4)


if __name__ == "__main__":
    sys.exit(main())
