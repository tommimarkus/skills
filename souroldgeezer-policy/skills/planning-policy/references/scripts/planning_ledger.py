#!/usr/bin/env python3
"""Parent-owned checkpoint ledger with byte-compatible legacy commands."""

from __future__ import annotations

import argparse
import hashlib
import functools
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

# A v4/v5 checkpoint retains one bounded capability binding per step. Keep the
# record bounded while leaving the established 40-step summary lane viable.
MAX_CHECKPOINT = 64 * 1024
MAX_LEGACY_CHECKPOINT = 16 * 1024
MAX_RETURN = 8 * 1024
MAX_WORKER_HANDOFF = 32 * 1024
MAX_WORKER_HANDOFF_RAW = MAX_WORKER_HANDOFF + 1024
MAX_REMEDIATION = 4 * 1024
MAX_SERIES_HANDOFF = 8 * 1024
MAX_USAGE = 4 * 1024
MAX_TOKENS = 1200
MAX_USAGE_TOKENS = 600
# A `next` block restates what the acting command just decided, so it stays far
# smaller than a summary: enough for the state and one CLI hint, never a report.
MAX_NEXT_TOKENS = 120
MAX_NEXT_ONLY_TOKENS = 240
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
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
# The Git-policy helper always emits `rebased_tree_changed` and adds
# `batch_source_commits` only for a batch integrate, so both stay optional here:
# a result recorded before either existed still validates.
WORKTREE_RESULT_OPTIONAL = {"rebased_tree_changed", "batch_source_commits"}
# A batch is one dispatch in one shared worktree, so a member's dependency on an
# earlier member is satisfied by progress rather than by that member's cleanup.
BATCH_DEPENDENCY_STATES = {"ready", "in_progress", "completed", "cleaned"}
EXTERNAL_DEPENDENCY_STATES = {"integrated", "cleaned"}
BATCH_STOPPED_STATES = {"blocked", "failed", "oversized"}
BATCH_ACTIVE_STATES = {"pending", "ready", "in_progress"}
CLOSEOUT_FIELDS = {
    "returned_commit": "",
    "integrated_commit": "",
    "integration_result_path": "",
    "integration_result_sha256": "",
    "cleanup_result_path": "",
    "cleanup_result_sha256": "",
}
# Execution-metadata amendments: a bounded per-step overlay on the approved leaf.
AMENDMENT_FIELDS = {
    "reason",
    "add_write",
    "add_read",
    "after_attempt_id",
    "after_attempt_count",
    "return_recorded",
}
AMENDMENT_OPTIONAL = {"acceptance_command", "max_attempts"}
MAX_AMENDMENTS = 4
MAX_AMENDMENT_PATHS = 8
MAX_AMENDED_ATTEMPTS = 5
MAX_AMENDED_COMMAND = 2048
AMENDABLE_STATES = {"pending", "ready", "blocked", "failed", "oversized"}
SCOPE_REJECTION_REASON = "oversized: changed path outside write_set"
TERMINAL_RETRY_REASONS = {
    "blocked:no_progress",
    "blocked:retry_exhausted",
    "blocked:retry_ceiling_reached",
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
REGISTERED_RETURN_CODES = "registered_v1"
# The closed blocker-code vocabulary a registered run enforces, by return status.
RETURN_CODES = {
    "blocked": tuple(
        f"blocked:{name}"
        for name in (
            "missing_input",
            "needs_higher_tier",
            "model_unavailable",
            "capability_unavailable",
            "environment",
            "upstream_changed",
        )
    ),
    "failed": ("failed:acceptance", "failed:execution", "failed:verification"),
    "oversized": ("oversized:scope", "oversized:changeset"),
}
# Recorded by the ledger alone (record-verify, restack): a worker return can never carry them.
VERIFIER_ONLY_CODES = {"failed:verification", "blocked:upstream_changed"}
# Repairable stops retry at the same tier without spending the same-tier retry.
REPAIRABLE_CODES = {"blocked:environment", "blocked:upstream_changed"}
# The stops that need reasoning rather than repair, by (status, code).
REASONING_STOPS = {
    ("failed", "failed:acceptance"),
    ("failed", "failed:verification"),
    ("blocked", "blocked:needs_higher_tier"),
}
VERIFY_POLICIES = {"leaf_verify_v1", "closeout_only"}
# Stamped only on leaf_verify_v1 runs: a dependent may start on a completed prerequisite whose verify is issued.
PIPELINE_POLICY = "provisional_v1"
MAX_CONCURRENT = 4
NON_ACTION_CATEGORIES = {"terminal_closed", "terminal_blocked", "validate_closeout"}
# The stamp maps to the plan's precision word; a run without it keeps the hard scope rejection.
PRECISION_POLICIES = {"standard_v1": "standard", "strict_v1": "strict"}
CHANGESET_BUDGET_FIELDS = {"max_changed_lines", "max_files", "exempt_paths", "base_commit"}
MAX_CHECK_OUTSIDE = 8
MAX_VERIFY_HANDOFF = 16 * 1024
MAX_VERIFY_RETURN = 4 * 1024
VERIFY_VERDICTS = {"pass", "reject", "inconclusive"}
VERIFY_PASSING = {"pass", "inconclusive"}
VERIFY_CODES = {
    "verify:coverage", "verify:decision", "verify:regression", "verify:scope_creep",
    "verify:acceptance_gap",
}
VERIFY_FINDING_FIELDS = {"code", "path", "line", "clause", "summary"}
VERIFY_HANDOFF_FIELDS = {
    "schema", "packet_sha256", "plan_id", "run_id", "plan_sha256", "step_id", "attempt_id",
    "agent_id", "verify_id", "verifier_tier", "task", "boundary", "settled_decisions",
    "write_set", "acceptance_command", "cohesive_outcome", "acceptance_exit_code",
    "base_commit", "returned_commit", "budget", "changeset", "prior_verify", "return_schema",
}
# Added to a packet only for a run stamped with a precision policy.
VERIFY_HANDOFF_OPTIONAL = {"outside_write_set", "outside_write_set_count"}
# The verifier is read-only: mechanical and standard builds get the standard
# verifier, analytical and deep builds the analytical one.
VERIFIER_AGENTS = {
    "mechanical": "plan-verify-standard", "standard": "plan-verify-standard",
    "analytical": "plan-verify-analytical", "deep": "plan-verify-analytical",
}
RUN_SCHEMAS = {2, 3, 4, 5}
CAPABILITY_SCHEMAS = {4, 5}
LIVE_NEXT_SCHEMAS = {4, 5}
FORWARD_SCHEMA = 5
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
SERIES_HANDOFF_SCHEMA = "planning-series-handoff-v1"
SERIES_HANDOFF_FIELDS = {
    "schema",
    "plan_id",
    "run_id",
    "series_id",
    "slice",
    "landed",
    "decisions",
    "assumptions_to_revalidate",
    "remaining_scope",
}
SERIES_HANDOFF_LIST_FIELDS = (
    "landed",
    "decisions",
    "assumptions_to_revalidate",
    "remaining_scope",
)
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


def changed_path_allowed(path, write_set):
    return validator_module().write_set_covers(write_set, path)


def standard_precision(data):
    """True for a run stamped standard_v1; an unstamped retained run stays strict."""
    return data.get("precision_policy") == "standard_v1"


def outside_paths(paths, write_set):
    """The returned or committed paths no write_set entry covers, in first-seen order."""
    return [path for path in dict.fromkeys(paths) if not changed_path_allowed(path, write_set)]


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


def repository_top(args):
    """The checkout relative assignment worktrees resolve against."""
    if args.repo_root:
        return Path(args.repo_root).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True
    )
    return Path(result.stdout.strip() if result.returncode == 0 else Path.cwd()).resolve()


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


def bounded_next(value, droppable=(), trimmable=""):
    """Bound a `next` block, shedding convenience before the state it reports.

    The pre-formatted CLI hint goes first and a listed collection is trimmed
    second, so the eligibility or status a caller acts on always survives.
    """
    for key in droppable:
        if proxy_tokens(value) <= MAX_NEXT_TOKENS:
            return value
        value.pop(key, None)
    while (
        proxy_tokens(value) > MAX_NEXT_TOKENS
        and trimmable
        and len(value.get(trimmable, [])) > 1
    ):
        value[trimmable].pop()
        value["truncated"] = True
    return value


def bounded_action_next(value, trimmable=""):
    """Keep the first legal command while trimming a convenience collection."""
    while (
        proxy_tokens(value) > MAX_NEXT_TOKENS
        and trimmable
        and len(value.get(trimmable, [])) > 1
    ):
        value[trimmable].pop()
        value["truncated"] = True
    if proxy_tokens(value) > MAX_NEXT_TOKENS and trimmable:
        value.pop(trimmable, None)
        value["truncated"] = True
    if proxy_tokens(value) > MAX_NEXT_TOKENS:
        raise Error("next block exceeds 120 proxy tokens")
    return value


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


def transition_scope(plan_id, run_id):
    return f"--plan-id {plan_id} transition --actor parent --run-id {run_id}"


def dispatch_command(plan_id, run_id, step_id):
    return (
        f"--plan-id {plan_id} dispatch --actor parent --run-id {run_id} "
        f"--step-id {step_id} --agent-id <agent-id>"
    )


def land_command(data, step_id):
    """Integrate and clean a step: composite land in v5, granular transitions before."""
    return (
        f"--plan-id {data['plan_id']} land --actor parent --run-id {data['run_id']} "
        f"--step-id {step_id} --target <target-branch>"
    )


def verify_commands(data, step_id):
    """The leaf_verify_v1 gate: check-changeset first, then verify-handoff."""
    scope = f"--plan-id {data['plan_id']}"
    return {
        "command": f"{scope} check-changeset --run-id {data['run_id']} --step-id {step_id}",
        "then": (
            f"{scope} verify-handoff --actor parent --run-id {data['run_id']} "
            f"--step-id {step_id}"
        ),
    }


def integrate_command(data, step_id):
    if data.get("schema") == FORWARD_SCHEMA:
        return land_command(data, step_id)
    return (
        f"{transition_scope(data['plan_id'], data['run_id'])} --step-id {step_id} "
        "--to integrated --worktree-result <planning-worktree-result-v1.json>"
    )


def cleanup_command(data, step_id):
    if data.get("schema") == FORWARD_SCHEMA:
        return land_command(data, step_id)
    return (
        f"{transition_scope(data['plan_id'], data['run_id'])} --step-id {step_id} "
        "--to cleaned --worktree-result <planning-worktree-result-v1.json>"
    )


def ready_command(data, step_id):
    """Start a pending step: composite dispatch in v5, granular ready before."""
    if data.get("schema") == FORWARD_SCHEMA:
        return dispatch_command(data["plan_id"], data["run_id"], step_id)
    return (
        f"{transition_scope(data['plan_id'], data['run_id'])} --step-id {step_id} "
        "--to ready --agent-id <agent-id>"
    )


def dependencies_clean(data, step, batches):
    """Dependencies are satisfied; schema-5 externals unblock at `integrated`."""
    members = batches.get(step["id"], ())
    external = EXTERNAL_DEPENDENCY_STATES if data.get("schema") == FORWARD_SCHEMA else {"cleaned"}
    return all(
        data["steps"][dep]["status"]
        in (BATCH_DEPENDENCY_STATES if dep in members else external)
        for dep in step["dependencies"]
    )


def provisional_prerequisite(data, step, batches):
    """The one unlanded prerequisite a pending step may build on, or "".

    Every other dependency must be integrated or cleaned; the unlanded one must
    be completed with a verify packet issued, or a passing verdict, for its
    returned commit. A batch is stacked once, through its first member.
    """
    if data.get("pipeline_policy") != PIPELINE_POLICY or step["status"] != "pending":
        return ""
    members = batches.get(step["id"], ())
    if members and members[0] != step["id"]:
        return ""
    unlanded = [
        dep for dep in step["dependencies"]
        if data["steps"][dep]["status"] not in EXTERNAL_DEPENDENCY_STATES
    ]
    if len(unlanded) != 1:
        return ""
    prerequisite = data["steps"][unlanded[0]]
    commit = prerequisite.get("returned_commit", "")
    issued = prerequisite.get("verify_id") and prerequisite.get("verify_commit") == commit
    if (
        prerequisite["status"] != "completed"
        or not commit
        or prerequisite.get("upstream_stale")
        or not (issued or commit_verified(prerequisite))
    ):
        return ""
    return unlanded[0]


def dependencies_ready(data, step, batches, allow_provisional=True):
    """Dependencies are satisfied, or the step may start provisionally (or resume as such)."""
    if dependencies_clean(data, step, batches):
        return True
    if not allow_provisional:
        return False
    if provisional_prerequisite(data, step, batches):
        return True
    base = step.get("provisional_base")
    return bool(base) and data["steps"][base["step_id"]]["status"] == "completed"


def attempt_available(step):
    return step["attempt_count"] < step["max_attempts"]


def amended_after_return(step):
    """True when an amendment was recorded after the current attempt's return."""
    return any(
        item["after_attempt_id"] == step["attempt_id"] and item["return_recorded"]
        for item in step.get("amendments", ())
    )


def repair_reopened(step):
    """A non-terminal blocked/failed stop whose cause was amended after its return."""
    return (
        step["status"] in {"blocked", "failed"}
        and step["reason"] not in TERMINAL_RETRY_REASONS
        and attempt_return_recorded(step)
        and amended_after_return(step)
    )


def retry_open(step):
    return step["retry_allowed"] or repair_reopened(step)


def ready_status_legal(step):
    return step["status"] in {"pending", "blocked", "failed"} and retry_open(step)


def ready_candidate(data, step, batches):
    return (
        ready_status_legal(step)
        and dependencies_ready(data, step, batches)
        and attempt_available(step)
    )


def leaves_by_id(plan):
    return {leaf["id"]: leaf for leaf in plan["leaves"]}


def attempt_return_recorded(step):
    """True once the step's current attempt has a stored return."""
    return bool(step["attempt_id"]) and step["return_path"] == str(
        Path("returns") / step["id"] / f"{step['attempt_id']}.json"
    )


def valid_amendments(step, approved, schema):
    """Return a step's stored amendments, failing closed on any malformed record."""
    value = step.get("amendments", [])
    if not isinstance(value, list) or len(value) > MAX_AMENDMENTS or (
        value and schema != FORWARD_SCHEMA
    ):
        raise Error("blocked:plan_tampered")
    attempts = approved["max_attempts"]
    try:
        for item in value:
            if (
                not isinstance(item, dict)
                or not AMENDMENT_FIELDS <= set(item) <= AMENDMENT_FIELDS | AMENDMENT_OPTIONAL
                or not isinstance(item["reason"], str)
                or not 1 <= len(item["reason"]) <= 480
                or not isinstance(item["after_attempt_id"], str)
                or not isinstance(item["after_attempt_count"], int)
                or isinstance(item["after_attempt_count"], bool)
                or not isinstance(item["return_recorded"], bool)
            ):
                raise Error("invalid amendment")
            for key in ("add_write", "add_read"):
                paths = item[key]
                if not isinstance(paths, list) or len(paths) > MAX_AMENDMENT_PATHS:
                    raise Error("invalid amendment")
                for path in paths:
                    rel(path, "amendment path")
            if "acceptance_command" in item and (
                not isinstance(item["acceptance_command"], str)
                or not 1 <= len(item["acceptance_command"]) <= MAX_AMENDED_COMMAND
            ):
                raise Error("invalid amendment")
            if "max_attempts" in item:
                number = item["max_attempts"]
                if (
                    not isinstance(number, int)
                    or isinstance(number, bool)
                    or not attempts < number <= MAX_AMENDED_ATTEMPTS
                ):
                    raise Error("invalid amendment")
                attempts = number
    except Error as exc:
        raise Error("blocked:plan_tampered") from exc
    return value


def validate_amendment_events(directory, data):
    """Bind each stored amendment to the digest its `amend-v5` event recorded.

    An amendment widens what a return may change, so a checkpoint record that no
    event vouches for, or an event whose record is gone, fails closed.
    """
    stored = {
        sid: [digest(item) for item in step["amendments"]]
        for sid, step in data.get("steps", {}).items()
        if isinstance(step, dict) and step.get("amendments")
    }
    recorded = {}
    path = directory / "events.jsonl"
    if path.is_file() and not path.is_symlink():
        try:
            lines = path.read_text().splitlines()
        except OSError as exc:
            raise Error("blocked:plan_tampered") from exc
        for line in lines:
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise Error("blocked:plan_tampered") from exc
            if isinstance(value, dict) and value.get("action") == "amend-v5":
                recorded.setdefault(value.get("step_id"), []).append(
                    value.get("amendment_sha256")
                )
    if stored != recorded:
        raise Error("blocked:plan_tampered")


def effective_leaf(leaf, amendments):
    """The approved leaf plus its cumulative amendment overlay."""
    if not amendments:
        return leaf
    value = dict(leaf)
    for field, key in (("write_set", "add_write"), ("read_set", "add_read")):
        paths = list(leaf[field])
        for item in amendments:
            paths.extend(path for path in item[key] if path not in paths)
        value[field] = paths
    for item in amendments:
        for field in AMENDMENT_OPTIONAL:
            if field in item:
                value[field] = item[field]
    return value


def effective_leaves(plan, data):
    """Every consumer of amendable leaf fields reads through this one overlay."""
    steps = data.get("steps", {})
    return {
        sid: effective_leaf(
            leaf,
            valid_amendments(steps[sid], leaf, data.get("schema")) if sid in steps else [],
        )
        for sid, leaf in leaves_by_id(plan).items()
    }


def scope_rejection_state(step):
    """A step stopped on write_set alone, with no stored return, is repairable."""
    return (
        step["status"] == "oversized"
        and step["reason"] == SCOPE_REJECTION_REASON
        and not step["return_path"]
        and not step["return_sha256"]
    )


def step_batches(plan):
    """Derive each batched leaf's member list from the stored canonical plan."""
    groups = {}
    for leaf in plan["leaves"]:
        if leaf.get("batch"):
            groups.setdefault(leaf["batch"], []).append(leaf["id"])
    return {sid: members for members in groups.values() for sid in members}


def batch_settled(data, batches, step_id):
    """True once no member of the step's batch can still commit to its worktree."""
    return not any(
        data["steps"][member]["status"] in BATCH_ACTIVE_STATES
        or (
            data["steps"][member]["status"] in {"blocked", "failed"}
            and retry_open(data["steps"][member])
        )
        for member in batches.get(step_id, ())
    )


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
    if data.get("return_codes") not in {None, REGISTERED_RETURN_CODES}:
        raise Error("invalid v2 return codes")
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
            if data.get("schema") in CAPABILITY_SCHEMAS:
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
            if data.get("schema") in CAPABILITY_SCHEMAS:
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
    for sid, step in steps.items():
        for field, keys in (
            ("upstream_stale", {"step_id", "commit"}),
            ("upstream_change", {"old", "new"}),
            ("pending_acceptance", {"old", "new"}),
        ):
            value = step.get(field)
            if value is not None and not (
                isinstance(value, dict)
                and set(value) == keys
                and all(isinstance(item, str) for item in value.values())
                and all(COMMIT.fullmatch(item) or item in steps for item in value.values())
            ):
                raise Error("blocked:plan_tampered")
        base = step.get("provisional_base")
        if base is not None and not (
            isinstance(base, dict)
            and set(base) == {"step_id", "commit"}
            and base["step_id"] in steps
            and base["step_id"] in step["dependencies"]
            and isinstance(base["commit"], str)
            and COMMIT.fullmatch(base["commit"])
        ):
            raise Error("blocked:plan_tampered")
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
    if schema == FORWARD_SCHEMA:
        actions.update({"amend-v5", "verify-handoff", "record-verify", "record-changeset", "restack"})
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


@functools.cache
def validator_module():
    spec = importlib.util.spec_from_file_location(
        "plan_contract", Path(__file__).with_name("validate_plan_contract.py")
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def plan_validator():
    return validator_module().validate


def read_plan(path, contract_version=FORWARD_SCHEMA):
    data = read_json(path, "cannot read plan file")
    result = plan_validator()(data)
    ready_key = "approval_ready" if contract_version == FORWARD_SCHEMA else "resume_ready"
    if (
        not result.get("valid")
        or not result.get(ready_key)
        or result.get("contract_version") != contract_version
    ):
        raise Error("plan is not dispatch-ready")
    return data


def host_tiers():
    """The single host tier map: per host, the tier models, skill support, and verifiers."""
    return read_json(Path(__file__).resolve().parent.parent / "host-tiers.json", "cannot read host tier map")


def host_entry(host):
    entry = host_tiers().get("hosts", {}).get(host)
    if entry is None:
        raise UsageError(f"unknown host {host}; the tier map names {sorted(host_tiers()['hosts'])}")
    return entry


def host_step_binding(leaf, host, entry, tier_name, evidence):
    """One step's binding item for a tier of a host's map; a skill need on a skill-less tier is unavailable."""
    tier = entry["tiers"][tier_name]
    requirements = leaf["capability_requirements"]
    if not tier["skill"] and any(item["kind"] == "skill" for item in requirements["additional"]):
        raise Error("blocked:capability_unavailable")
    return {
        "step_id": leaf["id"], "host": host, "executor": tier["model"],
        "requirements": requirements, "evidence": evidence,
    }


def derived_setup(plan, host, evidence_text):
    """Derive the assignments and capability binding of a host run from the tier map."""
    entry = host_entry(host)
    evidence = [line.strip() for line in evidence_text.splitlines() if line.strip()]
    if not 1 <= len(evidence) <= 8 or any(len(line) > 240 for line in evidence):
        raise UsageError("--evidence needs 1 to 8 lines of at most 240 characters")
    assigned, bound = [], []
    for leaf in plan["leaves"]:
        tier = entry["tiers"][leaf["portable_tier"]]
        bound.append(host_step_binding(leaf, host, entry, leaf["portable_tier"], evidence))
        assigned.append({
            "id": leaf["id"], "harness": host, "model_or_alias": tier["model"],
            "effort": tier["effort"], "worktree": f".worktrees/{leaf['worktree_owner']}",
        })
    binding = {"schema": "planning-capability-binding-v1", "plan_sha256": digest(plan), "bindings": bound}
    return assigned, binding


def tier_alias(args, data, tier):
    """A host run's dispatch alias is the map entry for the tier; an explicit value must equal it."""
    if args.command != "dispatch" or not data.get("host"):
        return args.model_or_alias
    expected = host_entry(data["host"])["tiers"][tier]["model"]
    if args.model_or_alias and args.model_or_alias != expected:
        raise Error(f"model_or_alias must equal the host tier map entry {expected} for tier {tier}")
    return expected


def capability_bindings(path, plan):
    """Load one complete v4/v5 binding and retain assigned-step evidence."""
    return checked_binding(read_json(path, "cannot read capability binding file"), plan)


def checked_binding(value, plan):
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
    return checked_assignments(read_json(path, "cannot read assignments file"), plan)


def checked_assignments(values, plan):
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
    raise Error("blocked:contract_migration_required")


def load_predecessor_run(ledger_root, plan_id, run_id):
    """Load and fully re-validate a predecessor run's checkpoint and plan.

    Mirrors `load2`'s validation depth without depending on `args`, since a
    predecessor's plan_id/run_id differ from the successor's. Any failure here
    is the predecessor's fault, never the successor's, so every caller treats
    this raising as "unresolvable" rather than propagating the error.
    """
    directory = ledger_root / plan_id / run_id
    if directory.is_symlink() or not directory.is_dir():
        raise Error("unresolvable predecessor run")
    safe_run_contents(directory)
    checkpoint = read_json(directory / "checkpoint.json", "unresolvable predecessor checkpoint")
    if (
        checkpoint.get("schema") not in RUN_SCHEMAS
        or checkpoint.get("plan_id") != plan_id
        or checkpoint.get("run_id") != run_id
    ):
        raise Error("unresolvable predecessor checkpoint")
    plan = read_json(directory / "plan.json", "unresolvable predecessor plan")
    if digest(plan) != checkpoint.get("plan_hash") or not SHA.fullmatch(
        checkpoint.get("plan_hash", "")
    ):
        raise Error("unresolvable predecessor plan")
    plan_result = plan_validator()(plan, capability_binding=checkpoint_binding(checkpoint), admission=False)
    ready_key = "dispatch_ready" if checkpoint["schema"] == FORWARD_SCHEMA else "resume_ready"
    if (
        not plan_result.get(ready_key)
        or plan_result.get("contract_version") != checkpoint["schema"]
    ):
        raise Error("unresolvable predecessor plan")
    validate_steps2(checkpoint, leaves_by_id(plan))
    validate_retry_artifacts(directory, checkpoint)
    validate_series_handoff(directory, checkpoint, plan)
    lifecycle(checkpoint)
    validate_events2(directory, checkpoint)
    return checkpoint, plan


def series_predecessor_disclosure(ledger_root, series):
    """Compute the init-v5 predecessor cross-check for a slice > 1 successor.

    Never raises: a gc'd, purged, unreadable, or tampered predecessor is
    disclosed as "unresolvable" rather than failing the successor's init.
    """
    predecessor = series.get("predecessor")
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


def refuse_unowned_pins(args, plan, top):
    """A strict plan must prove no unowned pinning test exists before the run starts."""
    if plan.get("precision") != "strict":
        return
    if not args.pin_roots:
        raise UsageError("a strict plan requires --pin-roots")
    scan = plan_validator()(plan, pin_roots=args.pin_roots, repo_root=top)
    pins = [item for item in scan.get("errors", []) if item.startswith("PLANSCOPE-UNOWNED-PIN")]
    if pins:
        raise Error("; ".join(pins[:MAX_CHECK_OUTSIDE])[:480])


def primary_checkout(args, top):
    """The checkout holding the Git common directory, so a derived worktree is never nested."""
    result = subprocess.run(
        ["git", "-C", str(top), "rev-parse", "--git-common-dir"], text=True, capture_output=True
    )
    if result.returncode:
        return top
    common = Path(result.stdout.strip())
    common = (top / common).resolve() if not common.is_absolute() else common.resolve()
    return common.parent if common.name == ".git" else top


def init5(args):
    approved_parent(args)
    plan = read_plan(args.plan_file, FORWARD_SCHEMA)
    top = repository_top(args)
    refuse_unowned_pins(args, plan, top)
    supplied = (args.assignments_file, args.capability_binding_file)
    if args.host and any(supplied):
        raise UsageError("--host derives the assignments and binding; pass neither file")
    if not args.host and not all(supplied):
        raise UsageError("pass --assignments-file and --capability-binding-file, or --host with --evidence")
    if args.host:
        derived, derived_binding = derived_setup(plan, args.host, args.evidence)
        assigned = checked_assignments(derived, plan)
    else:
        assigned = assignments(args.assignments_file, plan)
    # Resolve a relative worktree once, so every later command and every
    # artifact comparison sees one absolute path whatever its cwd.
    anchor = primary_checkout(args, top) if args.host else top
    assigned = {
        sid: {**item, "worktree": os.path.normpath(anchor / item["worktree"])}
        for sid, item in assigned.items()
    }
    bindings = (
        checked_binding(derived_binding, plan)
        if args.host
        else capability_bindings(args.capability_binding_file, plan)
    )
    ledger_root = root(args)
    collect_ledgers(ledger_root, None, timestamp(now()), remove=True)
    series = plan.get("series")
    series_predecessor = (
        series_predecessor_disclosure(ledger_root, series)
        if series and series.get("slice", 1) > 1
        else None
    )
    directory = plan_dir(args)
    existing, invalid = scan_ledgers(ledger_root, args.plan_id, timestamp(now()))
    if invalid:
        raise Error("target plan ledger directory is invalid")
    if any(entry["legacy"] for entry in existing):
        raise Error("cannot add a v5 run inside a legacy ledger directory")
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
        "schema": FORWARD_SCHEMA,
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
        "return_codes": REGISTERED_RETURN_CODES,
        "verify_policy": "closeout_only" if plan.get("verification") == "closeout-only" else "leaf_verify_v1",
        "precision_policy": "strict_v1" if plan.get("precision") == "strict" else "standard_v1",
        **({} if plan.get("verification") == "closeout-only" else {"pipeline_policy": PIPELINE_POLICY}),
        **({"host": args.host} if args.host else {}),
        "steps": steps,
    }
    write(run / "plan.json", plan, 64 * 1024)
    write(run / "checkpoint.json", data)
    initial_event(
        run,
        created_at,
        "init-v5",
        args.plan_id,
        run_id=run_id,
        plan_hash=data["plan_hash"],
    )
    result = {
        "ok": True,
        "action": "init-v5",
        "plan_id": args.plan_id,
        "run_id": run_id,
        "plan_hash": data["plan_hash"],
        "retry_policy": data["retry_policy"],
    }
    # `ready()` admits a pending step only once every dependency is `integrated`
    # or `cleaned`, so at initialization exactly the dependency-free steps can start.
    startable = [sid for sid in sorted(steps) if not steps[sid]["dependencies"]]
    if startable:
        result["next"] = bounded_next(
            {
                "ready_step_ids": startable,
                "command": dispatch_command(args.plan_id, run_id, startable[0]),
            },
            droppable=("command",),
            trimmable="ready_step_ids",
        )
    if series_predecessor is not None:
        result["series_predecessor"] = series_predecessor
    return result


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
        data.get("schema") not in RUN_SCHEMAS
        or data.get("plan_id") != args.plan_id
        or data.get("run_id") != args.run_id
        or data.get("retry_policy") not in {None, ESCALATING_RETRY_POLICY}
        or data.get("return_codes") not in {None, REGISTERED_RETURN_CODES}
        or data.get("verify_policy") not in {None, *VERIFY_POLICIES}
        or data.get("precision_policy") not in {None, *PRECISION_POLICIES}
        or data.get("pipeline_policy") not in {None, PIPELINE_POLICY}
        or (data.get("host") is not None and data["host"] not in host_tiers().get("hosts", {}))
    ):
        raise Error("invalid run checkpoint")
    plan = read_json(directory / "plan.json", "blocked:plan_tampered")
    if digest(plan) != data.get("plan_hash") or not SHA.fullmatch(data.get("plan_hash", "")):
        raise Error("blocked:plan_tampered")
    plan_result = plan_validator()(plan, capability_binding=checkpoint_binding(data), admission=False)
    ready_key = "dispatch_ready" if data["schema"] == FORWARD_SCHEMA else "resume_ready"
    if not plan_result.get(ready_key) or plan_result.get("contract_version") != data["schema"]:
        raise Error("blocked:plan_tampered")
    leafs = leaves_by_id(plan)
    if set(data.get("steps", {})) != set(leafs):
        raise Error("blocked:plan_tampered")
    validate_amendment_events(directory, data)
    leafs = effective_leaves(plan, data)
    for step in data["steps"].values():
        for field, default in CLOSEOUT_FIELDS.items():
            step.setdefault(field, default)
    validate_steps2(data, leafs)
    validate_retry_artifacts(directory, data)
    validate_series_handoff(directory, data, plan)
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


def primary_code(value):
    """The first blocker code that belongs to the return status's own family."""
    family = RETURN_CODES.get(value.get("status"), ())
    for blocker in value.get("blockers") or ():
        code = blocker.get("code") if isinstance(blocker, dict) else None
        if code in family:
            return code
    return ""


def retry_class(data, step, value):
    """The one retry-eligibility predicate: (kind, outcome), or ("", "").

    Reasoning stops (`failed:acceptance`, `failed:verification`,
    `blocked:needs_higher_tier`) keep the
    same-tier-then-escalate rules. Repairable stops (`blocked:environment`, or
    any other blocked/failed stop amended after its return) retry at the same
    tier. Retained runs below schema 5 keep the exactly-one-blocker rule.
    """
    status = value.get("status")
    if data.get("schema") != FORWARD_SCHEMA:
        blockers = value.get("blockers", [])
        code = ""
        if isinstance(blockers, list) and len(blockers) == 1 and isinstance(blockers[0], dict):
            code = blockers[0].get("code")
        if (status, code) in {("failed", "failed:acceptance"), ("blocked", "blocked:needs_higher_tier")}:
            return "reasoning", code
        return "", ""
    code = primary_code(value)
    if (status, code) in REASONING_STOPS:
        return "reasoning", code
    if status in {"blocked", "failed"} and (code in REPAIRABLE_CODES or repair_reopened(step)):
        return "repairable", code or status
    return "", ""


def needs_higher_tier(step, kind, outcome):
    return kind == "reasoning" and (
        outcome == "blocked:needs_higher_tier"
        or (
            outcome in {"failed:acceptance", "failed:verification"}
            and (step["same_tier_retry_used"] or step["attempt_count"] > 1)
        )
    )


def store_remediation(args, data, directory, step):
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
    kind, outcome = retry_class(data, step, prior)
    if not kind:
        raise Error("prior outcome is not retry eligible")
    if outcome == "failed:verification":
        cited = (step["verify"]["sha256"][:12], step["verify"]["commit"][:12])
        if not all(part in value["diagnosis"] for part in cited):
            raise Error(
                "failed:verification remediation must cite the verify return digest "
                f"({cited[0]}) and the rejected commit ({cited[1]})"
            )
    if outcome == "blocked:upstream_changed":
        change = step.get("upstream_change", {})
        cited = (change.get("old", "")[:12], change.get("new", "")[:12])
        if not all(cited) or not all(part in value["diagnosis"] for part in cited):
            raise Error(
                "blocked:upstream_changed remediation must cite the prerequisite's old "
                f"({cited[0]}) and new ({cited[1]}) commits"
            )
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
    if kind == "reasoning":
        if outcome == "blocked:needs_higher_tier" and target == current:
            raise Error("blocked:needs_higher_tier requires a higher target tier")
        if step["attempt_count"] > 1 and target == current:
            raise Error("later eligible retries require a higher target tier")
        if target == current and step["same_tier_retry_used"]:
            raise Error("same-tier retry already used")
    destination = directory / "retry-remediations" / step["id"] / f"{step['attempt_id']}.json"
    write(destination, value, MAX_REMEDIATION)
    return (
        value,
        str(destination.relative_to(directory)),
        digest(value),
        target == current and kind == "reasoning",
    )


def valid_series_handoff(value):
    if not isinstance(value, dict) or len(canon(value)) > MAX_SERIES_HANDOFF:
        raise Error("planning-series-handoff-v1 exceeds 8 KiB")
    if set(value) != SERIES_HANDOFF_FIELDS or value.get("schema") != SERIES_HANDOFF_SCHEMA:
        raise Error("invalid planning-series-handoff-v1 schema")
    ident(value["plan_id"], "series handoff plan id")
    uuid4(value["run_id"], "series handoff run id")
    ident(value["series_id"], "series handoff series id")
    slice_value = value["slice"]
    if not isinstance(slice_value, int) or isinstance(slice_value, bool) or slice_value < 1:
        raise Error("series handoff slice must be an integer >= 1")
    for field in SERIES_HANDOFF_LIST_FIELDS:
        items = value[field]
        if not isinstance(items, list) or len(items) > 16:
            raise Error(f"series handoff {field} must be a bounded array")
        for item in items:
            if not isinstance(item, str) or not 1 <= len(item) <= 480:
                raise Error(f"series handoff {field} entries must be bounded non-empty strings")
    return value


def read_series_handoff(path):
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid planning-series-handoff-v1") from exc
    if len(raw) > MAX_SERIES_HANDOFF:
        raise Error("planning-series-handoff-v1 exceeds 8 KiB")
    return valid_series_handoff(value)


def read_series_handoff_content(path):
    """Read the parent-supplied content file for a series close.

    The caller supplies exactly the four bounded content fields. Identity is
    never caller-supplied, so a previous slice's artifact cannot be pasted into
    this close; `composed_series_handoff` binds it from the closing run.
    """
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid series handoff content file") from exc
    if len(raw) > MAX_SERIES_HANDOFF:
        raise Error("series handoff content file exceeds 8 KiB")
    if not isinstance(value, dict) or set(value) != set(SERIES_HANDOFF_LIST_FIELDS):
        raise Error("series handoff content file must carry exactly the four content fields")
    return value


def composed_series_handoff(path, data, series):
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


def series_close_handoff(args, data, plan):
    """Resolve the series close matrix before `close2` mutates anything.

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


def validate_series_handoff(directory, data, plan):
    """Sibling of validate_retry_artifacts: re-verify a stamped handoff artifact.

    `load2` calls this but not `validate_events2`, so a plain event-fact record
    of the stamp alone would skip tamper detection; the file's own bytes are
    hashed and re-checked against the checkpoint stamp every load.
    """
    path = data.get("series_handoff_path", "")
    sha256 = data.get("series_handoff_sha256", "")
    if bool(path) != bool(sha256):
        raise Error("series handoff stamp requires both path and sha256")
    artifact = directory / "series-handoff.json"
    file_exists = artifact.is_file() and not artifact.is_symlink()
    if file_exists and not path:
        raise Error("series handoff artifact present without a checkpoint stamp")
    if path and not file_exists:
        raise Error("series handoff checkpoint stamp has no artifact")
    if not path:
        return
    if path != "series-handoff.json":
        raise Error("series handoff path must name the run-level artifact")
    series = plan.get("series")
    if series is None:
        raise Error("series handoff stamp present on a run whose plan has no series block")
    value = read_series_handoff(artifact)
    if (
        digest(value) != sha256
        or value["plan_id"] != data["plan_id"]
        or value["run_id"] != data["run_id"]
        or value["series_id"] != series.get("series_id")
        or value["slice"] != series.get("slice")
    ):
        raise Error("series handoff artifact digest or identity mismatch")


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


def ready(args, directory, data, plan, batches, step, allow_provisional=False):
    for value, label in ((args.harness, "harness"), (args.model_or_alias, "model_or_alias")):
        if value and (not isinstance(value, str) or not value.strip() or len(value) > 160):
            raise Error(f"invalid {label}")
    if not isinstance(args.agent_id, str) or not 1 <= len(args.agent_id) <= 128:
        if step["status"] == "pending" or data.get("retry_policy") != ESCALATING_RETRY_POLICY:
            raise Error("ready requires bounded --agent-id")
    if not ready_status_legal(step):
        raise Error("step cannot be readied")
    retry_state = None
    if step["status"] != "pending":
        if not args.retry:
            raise Error("retry requires --retry")
        if data.get("retry_policy") == ESCALATING_RETRY_POLICY:
            retry_state = store_remediation(args, data, directory, step)
        elif not args.summary:
            raise Error("retry requires --retry and bounded --summary")
    elif args.retry or args.retry_remediation_file:
        raise Error("initial ready transition is not a retry")
    if not dependencies_ready(data, step, batches, allow_provisional):
        raise Error(
            "dependencies are not integrated or cleaned"
            if data.get("schema") == FORWARD_SCHEMA
            else "dependencies are not cleaned"
        )
    if not attempt_available(step):
        raise Error("blocked:retry_exhausted")
    if retry_state:
        remediation, path, remediation_sha, same_tier = retry_state
        current_assignment = {
            "agent_id": remediation["next_agent_id"],
            "harness": remediation["next_harness"],
        }
        if data.get("schema") in CAPABILITY_SCHEMAS:
            current_assignment["model_or_alias"] = (
                tier_alias(args, data, remediation["target_portable_tier"])
                or step["current_assignment"]["model_or_alias"]
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
            if data.get("schema") in CAPABILITY_SCHEMAS:
                current_assignment["model_or_alias"] = (
                    tier_alias(args, data, step["current_tier"]) or step["assignment"]["model_or_alias"]
                )
            step["current_assignment"] = current_assignment
    if data.get("schema") in CAPABILITY_SCHEMAS:
        current = step["current_assignment"]
        stored = step["capability_binding"]["bindings"][0]
        if (
            stored["host"] != current["harness"]
            or stored["executor"] != current["model_or_alias"]
        ):
            if args.capability_binding_file:
                replacement = capability_bindings(args.capability_binding_file, plan)
                resolved = binding_for_step(
                    replacement,
                    step["id"],
                    {
                        "harness": current["harness"],
                        "model_or_alias": current["model_or_alias"],
                    },
                )
            elif data.get("host") and data["host"] == current["harness"]:
                # A host run derives the re-binding exactly as init does, reusing the stored evidence.
                leaf = next(item for item in plan["leaves"] if item["id"] == step["id"])
                item = host_step_binding(
                    leaf, data["host"], host_entry(data["host"]), step["current_tier"], stored["evidence"]
                )
                resolved = {
                    "schema": step["capability_binding"]["schema"],
                    "plan_sha256": step["capability_binding"]["plan_sha256"],
                    "bindings": [item],
                }
            else:
                raise Error("blocked:capability_unavailable")
            step["capability_binding"] = resolved
            step["capability_binding_sha256"] = digest(resolved)
    if step["status"] != "pending":
        # A re-dispatched prerequisite invalidates what was stacked on its old commit.
        mark_dependents_stale(data, step["id"])
    step["attempt_count"] += 1
    step["agent_id"] = next_agent_id
    step["attempt_id"] = str(uuid.uuid4())
    step["status"] = "ready"
    step["reason"] = reason[:480]


def retryable_steps(directory, data, batches):
    """Return retryable failures using the same stored return predicate as record()."""
    result = []
    for step in ordered_steps(data["steps"]):
        if step["status"] not in {"blocked", "failed"} or not ready_candidate(data, step, batches):
            continue
        try:
            kind, outcome = retry_class(data, step, current_return(directory, step))
        except Error:
            continue
        if kind:
            result.append((step, outcome, kind))
    return result


def retry_command(plan_id, run_id, step_id):
    return (
        f"{transition_scope(plan_id, run_id)} --step-id {step_id} --to ready --retry "
        "--retry-remediation-file <retry-remediation-v1.json>"
    )


def series_non_final(plan):
    """True for a plan whose series slice hands work on (needs a close handoff)."""
    series = plan.get("series")
    return bool(series) and not series.get("final")


def series_final(plan):
    """True for a plan whose series slice is the last (needs end verification)."""
    series = plan.get("series")
    return bool(series) and bool(series.get("final"))


def series_closeout_overlay(plan, block):
    """Splice the series-final marker into a closeout-adjacent next block.

    Never inlines `end_verification_commands` — a single 480-char command would
    blow the 120-proxy-token next bound alone, so this stays a compact flag the
    parent resolves against the plan it already holds.
    """
    if series_final(plan):
        block["series_end"] = True
    return block


def startable_step_ids(data, steps, batches):
    """Steps a parent could start now: dispatch-ready, provisionally ready, or verify-pending."""
    leaf_verify = data.get("verify_policy") == "leaf_verify_v1"
    result = []
    for step in steps:
        if step["status"] == "pending":
            startable = ready_candidate(data, step, batches)
        elif step["status"] == "ready":
            startable = True
        else:
            startable = (
                leaf_verify
                and step["status"] == "completed"
                and batch_settled(data, batches, step["id"])
                and stored_verdict(step) is None
                and not step.get("verify_id")
                and not step.get("upstream_stale")
            )
        if startable:
            result.append(step["id"])
    return result


def with_concurrent(data, batches, block):
    """List up to four other startable steps beside the one action a block names."""
    if block.get("category") in NON_ACTION_CATEGORIES:
        return block
    named = {
        item for value in block.values()
        for item in (value if isinstance(value, list) else [value]) if isinstance(item, str)
    }
    others = [
        sid for sid in startable_step_ids(data, ordered_steps(data["steps"]), batches)
        if sid not in named
    ][:MAX_CONCURRENT]
    while others:
        trial = {**block, "concurrent": others}
        if proxy_tokens(trial) <= MAX_NEXT_TOKENS:
            return trial
        others = others[:-1]
    return block


def checkpoint_next(directory, data, batches, plan):
    """The one highest-priority legal action, plus other steps that could start now."""
    return with_concurrent(data, batches, primary_next(directory, data, batches, plan))


def verify_issued(step):
    """True when verify-handoff issued a packet for the step's returned commit."""
    return bool(step.get("verify_id")) and step.get("verify_commit") == step["returned_commit"]


def primary_next(directory, data, batches, plan):
    """Select one highest-priority legal v4/v5 action from the checkpoint."""
    if data["run_status"] == "closed":
        return bounded_action_next(
            {"category": "terminal_closed", "outcome": data["outcome"]}
        )

    plan_id, run_id = data["plan_id"], data["run_id"]
    steps = ordered_steps(data["steps"])
    issued = []
    integrated = [step["id"] for step in steps if step["status"] == "integrated"]
    cleanup = None
    if integrated:
        cleanup = bounded_action_next(
            {
                "category": "cleanup_integrated",
                "step_ids": integrated,
                "command": cleanup_command(data, integrated[0]),
            },
            "step_ids",
        )
    # Schema 5 keeps the critical path moving: cleanup waits behind dispatch.
    if cleanup and data.get("schema") != FORWARD_SCHEMA:
        return cleanup

    # A batch shares one worktree and integrates its tip once, so a completed
    # member waits until no sibling can still commit to that worktree.
    completed = [
        step["id"]
        for step in steps
        if step["status"] == "completed" and batch_settled(data, batches, step["id"])
    ]
    restackable = [sid for sid in completed if restack_ready(data, data["steps"][sid])]
    if restackable:
        pending = bool(data["steps"][restackable[0]].get("pending_acceptance"))
        return bounded_action_next(
            {
                "category": "restack_acceptance" if pending else "restack_stale",
                "step_ids": restackable,
                "command": restack_command(data, restackable[0])
                + (" --acceptance-exit-code N" if pending else ""),
            },
            "step_ids",
        )
    completed = [sid for sid in completed if not data["steps"][sid].get("upstream_stale")]
    if data.get("verify_policy") == "leaf_verify_v1":
        undecided = [sid for sid in completed if stored_verdict(data["steps"][sid]) is None]
        # A packet issued by verify-handoff is awaiting its verdict, not unissued.
        issued = [sid for sid in undecided if verify_issued(data["steps"][sid])]
        unverified = [sid for sid in undecided if sid not in issued]
        completed = [sid for sid in completed if sid not in issued]
        if unverified:
            return bounded_action_next(
                {"category": "verify_pending", "step_ids": unverified,
                 **verify_commands(data, unverified[0])},
                "step_ids",
            )
        # A rejected member holds its batch: only a retry routes it onward.
        completed = [sid for sid in completed if group_landable(data, batches, sid)]
    # A provisional step waits for the prerequisite it stacked on to land first.
    completed = [sid for sid in completed if not unlanded_base(data, data["steps"][sid])]
    if completed:
        return bounded_action_next(
            {
                "category": "integrate_completed",
                "step_ids": completed,
                "command": integrate_command(data, completed[0]),
            },
            "step_ids",
        )

    retryable = retryable_steps(directory, data, batches)
    if retryable:
        ids = [step["id"] for step, _outcome, _kind in retryable]
        return bounded_action_next(
            {
                "category": "remediate_failure",
                "retry_class": retryable[0][2],
                "retryable_step_ids": ids,
                "command": retry_command(plan_id, run_id, ids[0]),
            },
            "retryable_step_ids",
        )

    pending = [
        step["id"]
        for step in steps
        if step["status"] == "pending" and ready_candidate(data, step, batches)
    ]
    if pending:
        return bounded_action_next(
            {
                "category": "ready_pending",
                "ready_step_ids": pending,
                "command": ready_command(data, pending[0]),
            },
            "ready_step_ids",
        )

    ready_steps = [step["id"] for step in steps if step["status"] == "ready"]
    if ready_steps:
        return bounded_action_next(
            {
                "category": "dispatch_ready",
                "ready_step_ids": ready_steps,
                "command": (
                    f"{transition_scope(plan_id, run_id)} --step-id {ready_steps[0]} "
                    "--to in_progress"
                ),
            },
            "ready_step_ids",
        )

    active = [step for step in steps if step["status"] == "in_progress"]
    if active:
        first = active[0]
        return bounded_action_next(
            {
                "category": "await_return",
                "await_step_id": first["id"],
                "agent_id": first["agent_id"],
                "attempt_id": first["attempt_id"],
            }
        )

    if issued:
        return bounded_action_next({"category": "await_verify", "step_ids": issued}, "step_ids")

    if cleanup:
        return cleanup

    if steps and all(step["status"] == "cleaned" for step in steps):
        return bounded_action_next(
            series_closeout_overlay(
                plan,
                {
                    "category": "validate_closeout",
                    "command": f"--plan-id {plan_id} validate --run-id {run_id} --closeout",
                },
            )
        )

    blocked = [step["id"] for step in steps if step["status"] != "cleaned"]
    return bounded_action_next(
        {"category": "terminal_blocked", "blocked_step_ids": blocked},
        "blocked_step_ids",
    )


def next_after_transition(args, directory, data, batches, step, plan):
    scope = transition_scope(args.plan_id, args.run_id)
    sid = step["id"]
    if step["status"] == "ready":
        return bounded_action_next(
            {"command": f"{scope} --step-id {sid} --to in_progress"}
        )
    if step["status"] == "in_progress":
        return bounded_action_next(
            {
                "await_step_id": sid,
                "agent_id": step["agent_id"],
                "attempt_id": step["attempt_id"],
            }
        )
    if step["status"] == "integrated":
        value = {"command": cleanup_command(data, sid)}
        unblocked = [
            candidate["id"]
            for candidate in ordered_steps(data["steps"])
            if data.get("schema") == FORWARD_SCHEMA
            and candidate["status"] == "pending"
            and sid in candidate["dependencies"]
            and ready_candidate(data, candidate, batches)
        ]
        if unblocked:
            # Dispatch keeps the critical path moving; cleanup waits behind it.
            value = {
                "ready_step_ids": unblocked,
                "command": dispatch_command(args.plan_id, args.run_id, unblocked[0]),
                "cleanup_step_id": sid,
            }
        return bounded_action_next(value, "ready_step_ids")
    newly_unblocked = [
        candidate["id"]
        for candidate in ordered_steps(data["steps"])
        if candidate["status"] == "pending"
        and sid in candidate["dependencies"]
        and ready_candidate(data, candidate, batches)
    ]
    if newly_unblocked:
        return bounded_action_next(
            {
                "ready_step_ids": newly_unblocked,
                "command": ready_command(data, newly_unblocked[0]),
            },
            "ready_step_ids",
        )
    if all(candidate["status"] == "cleaned" for candidate in data["steps"].values()):
        return bounded_action_next(
            series_closeout_overlay(
                plan,
                {"command": f"--plan-id {args.plan_id} validate --run-id {args.run_id} --closeout"},
            )
        )
    return checkpoint_next(directory, data, batches, plan)


def unwind(args, data, batches, sid, step):
    """Return a never-run batch member to pending after a sibling stopped the batch.

    The member never ran, so it must neither burn its attempt nor keep the
    identity a later redispatch will mint again.
    """
    if step["status"] != "in_progress":
        raise Error("only in_progress steps can become pending")
    members = batches.get(sid, ())
    if not members:
        raise Error("only a batch member can become pending")
    if not any(data["steps"][member]["status"] in BATCH_STOPPED_STATES for member in members):
        raise Error("pending unwind requires a stopped batch member")
    step.update(
        status="pending",
        reason=(args.summary or "unwound")[:480],
        attempt_count=step["attempt_count"] - 1,
        agent_id="",
        attempt_id="",
    )
    if data.get("retry_policy") == ESCALATING_RETRY_POLICY:
        step["current_assignment"]["agent_id"] = ""


def stored_verdict(step):
    """The verdict recorded for the step's current returned commit, or None."""
    stored = step.get("verify")
    if isinstance(stored, dict) and stored.get("commit") == step.get("returned_commit"):
        return stored.get("verdict")
    return None


def commit_verified(step):
    return stored_verdict(step) in VERIFY_PASSING


def require_not_stale(sid, step):
    stale = step.get("upstream_stale")
    if stale:
        raise Error(
            f"step {sid} is stale: its prerequisite {stale['step_id']} changed after it started; "
            "restack it first"
        )


def require_verified(data, sid, step):
    require_not_stale(sid, step)
    require_prerequisite_landed(data, sid, step)
    if data.get("verify_policy") == "leaf_verify_v1" and not commit_verified(step):
        raise Error(
            f"step {sid} has no pass or inconclusive verification for its returned commit; "
            "run check-changeset, verify-handoff and record-verify first"
        )


def unlanded_base(data, step):
    """The prerequisite a provisionally built step stacked on, while it is not yet landed."""
    base = step.get("provisional_base")
    if base and data["steps"][base["step_id"]]["status"] not in EXTERNAL_DEPENDENCY_STATES:
        return base["step_id"]
    return ""


def require_prerequisite_landed(data, sid, step):
    """A provisionally built step lands only after the prerequisite it stacked on."""
    prerequisite = unlanded_base(data, step)
    if prerequisite:
        raise Error(
            f"step {sid} is built on {prerequisite}, which is not integrated or cleaned; "
            "land the prerequisite first"
        )


def group_landable(data, batches, sid):
    """Every completed member of the step's batch holds a passing verdict."""
    return all(
        commit_verified(data["steps"][member])
        for member in (batches.get(sid) or (sid,))
        if data["steps"][member]["status"] == "completed"
    )


def unverified_members(data, batches, sid):
    """Completed members of the step's batch with no verdict yet for their returned commit."""
    steps = data["steps"]
    return [
        member for member in (batches.get(sid) or (sid,))
        if steps[member]["status"] == "completed" and stored_verdict(steps[member]) is None
    ]


def apply_worktree_result(path, directory, sid, step, leaf, new, batches, summary=""):
    """Validate a helper artifact and move one step to `integrated` or `cleaned`."""
    expected = "completed" if new == "integrated" else "integrated"
    old = step["status"]
    value, result_path, result_sha = worktree_result(
        path, directory, sid, step, leaf, new, batches
    )
    advance(step, old, expected, new, summary or new)
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


def transition2(args):
    directory, data, plan, leafs = mutating_run(args)
    batches = step_batches(plan)
    sid, step = selected_step(data, args.step_id)
    old = step["status"]
    new = args.to
    if new == "ready":
        ready(args, directory, data, plan, batches, step)
    elif new == "in_progress":
        advance(step, old, "ready", new, args.summary or "in progress")
    elif new == "pending":
        unwind(args, data, batches, sid, step)
    elif new in {"integrated", "cleaned"}:
        if new == "integrated":
            require_verified(data, sid, step)
        apply_worktree_result(
            args.worktree_result, directory, sid, step, leafs[sid], new, batches, args.summary
        )
    else:
        raise Error("v2 transition permits pending, ready, in_progress, integrated, or cleaned")
    event(
        directory,
        data,
        f"transition-v{data['schema']}",
        step_id=sid,
        from_status=old,
        to_status=step["status"],
        attempt_id=step["attempt_id"],
    )
    result = result2("transition", args, sid, step, attempt_id=step["attempt_id"])
    if (
        data.get("schema") in LIVE_NEXT_SCHEMAS
        and data.get("retry_policy") == ESCALATING_RETRY_POLICY
    ):
        result["next"] = next_after_transition(args, directory, data, batches, step, plan)
    return result


def batch_source_commits(value):
    batch = value.get("batch_source_commits")
    if batch is None:
        return {}
    if (
        not isinstance(batch, dict)
        or not batch
        or any(
            not isinstance(step_id, str)
            or not step_id
            or not isinstance(sha, str)
            or not SHA40.fullmatch(sha)
            for step_id, sha in batch.items()
        )
    ):
        raise Error("invalid planning worktree batch source commits")
    return batch


def worktree_result(path, directory, sid, step, leaf, target, batches):
    if not path:
        raise Error(f"{target} transition requires --worktree-result")
    source = Path(path)
    try:
        raw = source.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid planning-worktree-result-v1") from exc
    optional = WORKTREE_RESULT_OPTIONAL | ({"parent_commit"} if target == "cleaned" else set())
    if (
        len(raw) > 4096
        or not isinstance(value, dict)
        or set(value) - optional != WORKTREE_RESULT_FIELDS
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
    if "rebased_tree_changed" in value and not isinstance(value["rebased_tree_changed"], bool):
        raise Error("invalid planning worktree tree-change flag")
    member_commits = batch_source_commits(value)
    assigned_worktree = Path(step["assignment"]["worktree"])
    if not assigned_worktree.is_absolute():
        assigned_worktree = Path(value["repo_root"]) / assigned_worktree
    if (
        value["branch"] != leaf["worktree_owner"]
        or Path(value["worktree"]).resolve() != assigned_worktree.resolve()
    ):
        raise Error("planning worktree result does not match assigned owner")
    if target == "integrated":
        # A batch integrates its shared tip once, so a member either owns that
        # tip or is named in the artifact's proven per-member commit map.
        matched = value["source_commit"] == step["returned_commit"] or (
            sid in batches and member_commits.get(sid) == step["returned_commit"]
        )
        if step["returned_commit"] and not matched:
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


WORKTREE_HELPER = (
    Path(__file__).resolve().parents[3]
    / "git-workflow-policy/references/scripts/planning_worktree.py"
)


def run_worktree_helper(*arguments):
    """Run the Git-policy helper; return its parsed result and whether it succeeded."""
    result = subprocess.run(
        [sys.executable, "-B", str(WORKTREE_HELPER), *arguments],
        text=True,
        capture_output=True,
    )
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        value = None
    if not isinstance(value, dict):
        value = {"ok": False, "error": (result.stderr or "helper produced no result").strip()[:240]}
    return value, result.returncode == 0 and value.get("ok") is True


def helper_error(value):
    return str(value.get("error", "helper failed"))[:240]


def land(args):
    """Integrate and clean a completed leaf, or a settled batch, through the helper."""
    directory, data, plan, leafs = mutating_run(args)
    if data.get("schema") != FORWARD_SCHEMA:
        raise Error("land requires a version-5 run")
    batches = step_batches(plan)
    sid, step = selected_step(data, args.step_id)
    group = list(batches.get(sid, ())) or [sid]
    if len(group) > 1 and not batch_settled(data, batches, sid):
        raise Error("batch is not settled: a member can still commit to its worktree")
    if step["status"] not in {"completed", "integrated"}:
        raise Error("only completed or integrated steps can land")
    repo = repository_top(args)
    leaf = leafs[sid]
    worktree = step["assignment"]["worktree"]
    base = ("--repo-root", str(repo), "--target", args.target, "--branch", leaf["worktree_owner"],
            "--worktree", worktree)
    landed = [member for member in group if data["steps"][member]["status"] == "completed"]
    for member in landed:
        require_verified(data, member, data["steps"][member])
    if landed:
        commits = {member: data["steps"][member]["returned_commit"] for member in landed}
        if not all(COMMIT.fullmatch(commit) for commit in commits.values()):
            raise Error("completed step has no returned commit to integrate")
        extra = [f"--batch-commit={member}={commits[member]}" for member in landed] if len(group) > 1 else []
        value, ok = run_worktree_helper(
            "integrate", *base, "--source-commit", commits[landed[-1]], *extra
        )
        if not ok:
            raise Error(f"integrate failed: {helper_error(value)}")
        with tempfile.TemporaryDirectory() as scratch:
            artifact = Path(scratch) / "integrate.json"
            artifact.write_text(json.dumps(value))
            # Validate every member before persisting any, so a bad artifact leaves the ledger unchanged.
            for member in landed:
                apply_worktree_result(
                    str(artifact), directory, member, data["steps"][member],
                    leafs[member], "integrated", batches, args.summary,
                )
        for member in landed:
            event(
                directory, data, f"transition-v{data['schema']}", step_id=member,
                from_status="completed", to_status="integrated",
                attempt_id=data["steps"][member]["attempt_id"],
            )
    cleanable = [member for member in group if data["steps"][member]["status"] == "integrated"]
    result = {
        "ok": True,
        "action": "land",
        "run_id": args.run_id,
        "step_id": sid,
        "integrated": landed,
    }
    if cleanable:
        recorded = directory / data["steps"][cleanable[0]]["integration_result_path"]
        value, ok = run_worktree_helper("cleanup", *base, "--integrated-result", str(recorded))
        if ok:
            with tempfile.TemporaryDirectory() as scratch:
                artifact = Path(scratch) / "cleanup.json"
                artifact.write_text(json.dumps(value))
                for member in cleanable:
                    apply_worktree_result(
                        str(artifact), directory, member, data["steps"][member],
                        leafs[member], "cleaned", batches, args.summary,
                    )
            for member in cleanable:
                event(
                    directory, data, f"transition-v{data['schema']}", step_id=member,
                    from_status="integrated", to_status="cleaned",
                    attempt_id=data["steps"][member]["attempt_id"],
                )
            result["cleaned"] = cleanable
        else:
            result["cleanup_error"] = helper_error(value)
            result["retry_command"] = land_command(data, sid).replace(
                "<target-branch>", args.target
            )
    result["status"] = step["status"]
    result["next"] = next_after_transition(args, directory, data, batches, step, plan)
    return result


def close2(args):
    parent(args.actor)
    directory, data, plan, leafs = load2(args)
    validate_events2(directory, data)
    active_run(data)
    # Resolved before every mutation below, so a refused series close leaves the
    # run active with no event, no stamp, and no artifact written.
    handoff = series_close_handoff(args, data, plan)
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
    facts = {}
    if handoff is not None:
        data["series_handoff_path"] = "series-handoff.json"
        data["series_handoff_sha256"] = digest(handoff)
        # Size the stamped checkpoint before the artifact lands, so the only
        # remaining ordering exposure is the same one every ledger event has.
        if len(canon(data) + b"\n") > MAX_CHECKPOINT:
            raise Error("bounded record exceeds limit")
        write(directory / "series-handoff.json", handoff, MAX_SERIES_HANDOFF)
        facts = {
            "series_handoff_path": data["series_handoff_path"],
            "series_handoff_sha256": data["series_handoff_sha256"],
            "series_id": handoff["series_id"],
            "series_slice": handoff["slice"],
        }
    event(
        directory,
        data,
        f"close-v{data['schema']}",
        outcome=args.outcome,
        purge_after=data["purge_after"],
        reason=data["close_reason"],
        **facts,
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
    if (
        data.get("schema") in LIVE_NEXT_SCHEMAS
        and data.get("retry_policy") == ESCALATING_RETRY_POLICY
    ):
        batches = step_batches(plan)
        pending = [
            step
            for step in ordered_steps(data["steps"])
            if step["status"] == "pending" and ready_candidate(data, step, batches)
        ]
        retryable = pending + [s for s, _outcome, _kind in retryable_steps(directory, data, batches)]
    else:
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
    result = {
        "ok": True,
        "action": "reopen",
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "run_status": "active",
        "retryable_steps": [
            step["id"] for step in ordered_steps(data["steps"]) if step in retryable
        ],
    }
    if (
        data.get("schema") in LIVE_NEXT_SCHEMAS
        and data.get("retry_policy") == ESCALATING_RETRY_POLICY
    ):
        ids = result["retryable_steps"]
        first = data["steps"][ids[0]]
        command = (
            ready_command(data, first["id"])
            if first["status"] == "pending"
            else retry_command(data["plan_id"], data["run_id"], first["id"])
        )
        result["next"] = bounded_action_next(
            {"retryable_step_ids": ids, "command": command},
            "retryable_step_ids",
        )
    return result


def valid_return(value, data, step, leaf, registered=None, standard=False):
    if registered is None:
        registered = data.get("return_codes") == REGISTERED_RETURN_CODES
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
    if not isinstance(value["status"], str) or value["status"] not in RETURN_STATUSES:
        raise Error("invalid return status")
    paths = value["changed_paths"]
    if (
        not isinstance(paths, list)
        or len(paths) > MAX_CHANGED_PATHS
        or any(not isinstance(path, str) for path in paths)
        or len(set(paths)) != len(paths)
    ):
        raise Error("invalid changed_paths")
    for path in paths:
        rel(path, "changed path")
        if not standard and not changed_path_allowed(path, leaf["write_set"]):
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
            or not isinstance(x["type"], str)
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
    if registered:
        if any(blocker["code"] in VERIFIER_ONLY_CODES for blocker in blockers):
            raise Error("failed:verification and blocked:upstream_changed are recorded only by the ledger, never returned by a worker")
        allowed = set().union(*RETURN_CODES.values()) - VERIFIER_ONLY_CODES
        if any(blocker["code"] not in allowed for blocker in blockers):
            raise Error("blocker code is not registered: use " + ", ".join(sorted(allowed)))
        family = RETURN_CODES.get(value["status"], ())
        if family and not any(blocker["code"] in family for blocker in blockers):
            raise Error(f"{value['status']} return requires a code of its own: " + ", ".join(family))
    if value["status"] == "oversized" and not rem:
        raise Error("oversized return requires unstarted_remainder")
    return value


def bounded_return_schema(registered=False):
    """Return structural output guidance; valid_return owns semantic checks."""
    evidence = {
        "evidence_path": {"type": "string", "minLength": 1, "maxLength": MAX_PATH},
        "sha256": {"type": "string", "pattern": SHA.pattern},
    }
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema", "step_id", "attempt_id", "agent_id", "status", "changed_paths",
            "acceptance", "blockers", "notes", "unstarted_remainder", "commit_hash",
        ],
        "properties": {
            "schema": {"const": "bounded-step-return-v1"},
            "step_id": {"type": "string", "pattern": ID.pattern},
            "attempt_id": {"type": "string", "format": "uuid"},
            "agent_id": {"type": "string", "minLength": 1, "maxLength": 128},
            "status": {"type": "string", "enum": sorted(RETURN_STATUSES)},
            "changed_paths": {
                "type": "array", "maxItems": MAX_CHANGED_PATHS, "uniqueItems": True,
                "items": {"type": "string", "minLength": 1, "maxLength": MAX_PATH},
            },
            "acceptance": {
                "type": "object", "additionalProperties": False,
                "required": ["command", "exit_code", "summary"],
                "dependentRequired": {"evidence_path": ["sha256"], "sha256": ["evidence_path"]},
                "properties": {
                    "command": {"type": "string", "minLength": 1},
                    "exit_code": {"type": ["integer", "null"], "minimum": 0, "maximum": 255},
                    "summary": {"type": "string", "maxLength": MAX_ACCEPTANCE_SUMMARY},
                    **evidence,
                },
            },
            "blockers": {
                "type": "array", "maxItems": MAX_BLOCKERS,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["code", "summary"],
                    "dependentRequired": {"evidence_path": ["sha256"], "sha256": ["evidence_path"]},
                    "properties": {
                        "code": {"type": "string", "minLength": 1, "maxLength": MAX_BLOCKER_CODE},
                        "summary": {"type": "string", "maxLength": MAX_BLOCKER_SUMMARY},
                        **evidence,
                    },
                },
            },
            "notes": {
                "type": "array", "maxItems": MAX_NOTES,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["type", "message"],
                    "properties": {
                        "type": {"type": "string", "enum": sorted(NOTE_TYPES)},
                        "message": {"type": "string", "maxLength": MAX_NOTE_MESSAGE},
                    },
                },
            },
            "unstarted_remainder": {
                "type": "array", "maxItems": MAX_REMAINDER,
                "items": {"type": "string", "minLength": 1, "maxLength": MAX_REMAINDER_ITEM},
            },
            "commit_hash": {"type": "string", "pattern": COMMIT.pattern[:-1] + "?$"},
        },
    }
    if registered:
        codes = sorted(set().union(*RETURN_CODES.values()) - VERIFIER_ONLY_CODES)
        schema["properties"]["blockers"]["items"]["properties"]["code"]["enum"] = codes
    return schema


WORKER_HANDOFF_FIELDS = {
    "schema", "contract_version", "handoff_sha256", "plan_id", "run_id", "plan_sha256", "step_id", "agent_id",
    "attempt_id", "plan_context", "leaf", "work_unit", "worktree", "portable_tier", "host",
    "executor", "capability_binding", "retry_remediation", "return_schema",
}


# Added to a dispatch entry beside the packet; never part of the packet's digest.
DISPATCH_ENTRY_FIELDS = {"packet_path", "prompt"}
MAX_WORKER_PROMPT = 1200


def worker_handoff_digest(value):
    return digest({
        key: item for key, item in value.items()
        if key != "handoff_sha256" and key not in DISPATCH_ENTRY_FIELDS
    })


def worker_prompt(packet, packet_path, member=None):
    """Host-neutral worker prompt built only from packet facts.

    member is (position, count, batch) for a batch group, else None.
    """
    script = Path(__file__).resolve()
    text = (
        f"You are the {packet['portable_tier']} builder for step {packet['step_id']} "
        f"(attempt {packet['attempt_id']}).\n"
        f"Read your assignment packet in full: {packet_path}\n"
        f"Work only in the worktree: {packet['worktree']}\n"
        f"Before returning, validate your return read-only by piping it to: "
        f"python3 -B {script} validate-return --handoff-file {packet_path} --return-file -\n"
        + (
            "Your final message is exactly the bounded-step-return-v1 JSON object and nothing else."
            if member is None
            else f"This step is member {member[0]} of {member[1]} of batch {member[2]}, dispatched "
            "together in listed order; your final message is one JSON array holding one "
            "bounded-step-return-v1 object per member you ran, in that order, and nothing else."
        )
    )
    if len(text) > MAX_WORKER_PROMPT:
        raise Error("worker prompt exceeds 1200 characters")
    return text


def store_dispatch_packet(directory, packet, member=None):
    """Persist one issued packet under the run and return its dispatch entry."""
    path = (directory / "handoffs" / packet["step_id"] / f"{packet['attempt_id']}.json").resolve()
    write(path, packet, MAX_WORKER_HANDOFF)
    return {**packet, "packet_path": str(path), "prompt": worker_prompt(packet, path, member)}


def worker_handoff_context(plan):
    if not isinstance(plan, dict):
        raise Error("invalid worker handoff plan context")
    context = {
        "objective": plan.get("objective"),
        "scope_summary": plan.get("scope_summary"),
        "approved_decisions": plan.get("approved_decisions"),
    }
    if (
        not isinstance(context["objective"], str)
        or not 1 <= len(context["objective"]) <= 240
        or not isinstance(context["scope_summary"], str)
        or not 1 <= len(context["scope_summary"]) <= 480
        or not isinstance(context["approved_decisions"], list)
        or not 1 <= len(context["approved_decisions"]) <= 8
        or any(not isinstance(item, str) or not 1 <= len(item) <= 240 for item in context["approved_decisions"])
    ):
        raise Error("invalid worker handoff plan context")
    return context


def build_worker_handoff(
    plan, step, plan_id, run_id, retry_remediation=None, registered=False, changeset_base=None,
    precision=None,
):
    """Build one self-contained v5 worker assignment without mutating a ledger."""
    ident(plan_id, "plan id")
    uuid4(run_id, "run id")
    if not isinstance(plan, dict) or plan.get("contract_version") != FORWARD_SCHEMA:
        raise Error("worker handoff requires a version-5 plan")
    if not isinstance(step, dict) or step.get("status") != "in_progress":
        raise Error("worker handoff requires an in_progress step")
    sid = ident(step.get("id"), "step id")
    leaf = leaves_by_id(plan).get(sid)
    amendments = step.get("amendments") or []
    if leaf is not None:
        leaf = effective_leaf(leaf, valid_amendments(step, leaf, FORWARD_SCHEMA))
    units = {unit.get("id"): unit for unit in plan.get("work_units", []) if isinstance(unit, dict)}
    work_unit = units.get(leaf.get("work_unit_id") if leaf else None)
    if leaf is None or work_unit is None:
        raise Error("worker handoff has no assigned leaf or work unit")
    agent_id = step.get("agent_id")
    if not isinstance(agent_id, str) or not 1 <= len(agent_id) <= 128 or not agent_id.strip():
        raise Error("worker handoff requires a bounded agent_id")
    attempt_id = uuid4(step.get("attempt_id"), "attempt id")
    assignment = step.get("assignment")
    current = step.get("current_assignment")
    if not isinstance(assignment, dict) or not isinstance(current, dict):
        raise Error("worker handoff requires an assignment")
    worktree = assignment.get("worktree")
    if not isinstance(worktree, str) or not Path(worktree).is_absolute():
        raise Error("worker handoff requires an absolute worktree")
    host, executor = current.get("harness"), current.get("model_or_alias")
    if (
        current.get("agent_id") != agent_id
        or not isinstance(host, str) or not 1 <= len(host) <= 160 or not host.strip()
        or not isinstance(executor, str) or not 1 <= len(executor) <= 160 or not executor.strip()
        or step.get("current_tier") not in PORTABLE_TIERS
    ):
        raise Error("worker handoff has an invalid current assignment")
    plan_sha256 = digest(plan)
    binding = step.get("capability_binding")
    if (
        digest(binding) != step.get("capability_binding_sha256")
        or not valid_stored_binding(binding, plan_sha256, sid, leaf, current)
    ):
        raise Error("blocked:capability_unavailable")
    remediation_path = step.get("retry_remediation_path", "")
    if remediation_path:
        if retry_remediation is None or digest(retry_remediation) != step.get("retry_remediation_sha256"):
            raise Error("retry remediation artifact digest mismatch")
        valid_remediation(retry_remediation)
        if (
            retry_remediation["step_id"] != sid
            or retry_remediation["next_agent_id"] != agent_id
            or retry_remediation["next_harness"] != host
            or retry_remediation["target_portable_tier"] != step["current_tier"]
        ):
            raise Error("retry remediation artifact identity mismatch")
    elif retry_remediation is not None:
        raise Error("unexpected retry remediation artifact")
    value = {
        "schema": "planning-worker-handoff-v1",
        "contract_version": FORWARD_SCHEMA,
        "handoff_sha256": "",
        "plan_id": plan_id,
        "run_id": run_id,
        "plan_sha256": plan_sha256,
        "step_id": sid,
        "agent_id": agent_id,
        "attempt_id": attempt_id,
        "plan_context": worker_handoff_context(plan),
        "leaf": leaf,
        "work_unit": work_unit,
        "worktree": worktree,
        "portable_tier": step["current_tier"],
        "host": host,
        "executor": executor,
        "capability_binding": binding,
        "retry_remediation": retry_remediation,
        "return_schema": bounded_return_schema(registered),
    }
    if amendments:
        value["amendments"] = [
            {key: item[key] for key in ("reason", "add_write", "add_read", *AMENDMENT_OPTIONAL) if key in item}
            for item in amendments
        ]
    if precision is not None:
        value["precision"] = precision
    if step.get("provisional_base"):
        value["provisional_base"] = dict(step["provisional_base"])
    if changeset_base is not None:
        value["changeset_budget"] = {
            **validator_module().changeset_budget(leaf), "base_commit": changeset_base,
        }
    value["handoff_sha256"] = worker_handoff_digest(value)
    if len(canon(value)) > MAX_WORKER_HANDOFF:
        raise Error("planning-worker-handoff-v1 exceeds 32 KiB")
    return value


def valid_worker_handoff(value):
    if not isinstance(value, dict) or len(canon(value)) > MAX_WORKER_HANDOFF:
        raise Error("planning-worker-handoff-v1 exceeds 32 KiB")
    if (set(value) - {"amendments", "changeset_budget", "precision", "provisional_base", *DISPATCH_ENTRY_FIELDS} != WORKER_HANDOFF_FIELDS or value.get("schema") != "planning-worker-handoff-v1"
            or value.get("contract_version") != FORWARD_SCHEMA):
        raise Error("invalid planning-worker-handoff-v1 schema")
    if not isinstance(value.get("handoff_sha256"), str) or not SHA.fullmatch(value["handoff_sha256"]):
        raise Error("invalid worker handoff sha256")
    if value["handoff_sha256"] != worker_handoff_digest(value):
        raise Error("worker handoff digest mismatch")
    ident(value.get("plan_id"), "plan id")
    uuid4(value.get("run_id"), "run id")
    require_sha256(value.get("plan_sha256"), "invalid worker handoff plan sha256")
    sid = ident(value.get("step_id"), "step id")
    if not isinstance(value.get("agent_id"), str) or not 1 <= len(value["agent_id"]) <= 128:
        raise Error("invalid worker handoff agent_id")
    uuid4(value.get("attempt_id"), "attempt id")
    worker_handoff_context(value["plan_context"])
    leaf = value.get("leaf")
    unit = value.get("work_unit")
    if (
        not isinstance(leaf, dict) or leaf.get("id") != sid
        or not isinstance(unit, dict) or unit.get("id") != leaf.get("work_unit_id")
    ):
        raise Error("invalid worker handoff assignment")
    if (
        not isinstance(leaf.get("acceptance_command"), str)
        or not isinstance(leaf.get("write_set"), list)
        or not isinstance(leaf.get("capability_requirements"), dict)
    ):
        raise Error("invalid worker handoff leaf")
    if not isinstance(value.get("worktree"), str) or not Path(value["worktree"]).is_absolute():
        raise Error("invalid worker handoff worktree")
    if value.get("portable_tier") not in PORTABLE_TIERS:
        raise Error("invalid worker handoff portable tier")
    current = {"agent_id": value["agent_id"], "harness": value.get("host"), "model_or_alias": value.get("executor")}
    if not valid_stored_binding(value.get("capability_binding"), value["plan_sha256"], sid, leaf, current):
        raise Error("invalid worker handoff capability binding")
    if "precision" in value and value["precision"] not in set(PRECISION_POLICIES.values()):
        raise Error("invalid worker handoff precision")
    base = value.get("provisional_base")
    if "provisional_base" in value and not (
        isinstance(base, dict)
        and set(base) == {"step_id", "commit"}
        and isinstance(base["step_id"], str)
        and ID.fullmatch(base["step_id"])
        and isinstance(base["commit"], str)
        and COMMIT.fullmatch(base["commit"])
    ):
        raise Error("invalid worker handoff provisional base")
    budget = value.get("changeset_budget")
    if "changeset_budget" in value and not (
        isinstance(budget, dict)
        and set(budget) == CHANGESET_BUDGET_FIELDS
        and all(
            isinstance(budget[key], int) and not isinstance(budget[key], bool) and budget[key] >= 1
            for key in ("max_changed_lines", "max_files")
        )
        and isinstance(budget["exempt_paths"], list)
        and all(isinstance(path, str) for path in budget["exempt_paths"])
        and isinstance(budget["base_commit"], str)
        and (not budget["base_commit"] or COMMIT.fullmatch(budget["base_commit"]))
    ):
        raise Error("invalid worker handoff changeset budget")
    amendments = value.get("amendments", [])
    if not isinstance(amendments, list) or len(amendments) > MAX_AMENDMENTS or (
        "amendments" in value and not amendments
    ):
        raise Error("invalid worker handoff amendments")
    remediation = value.get("retry_remediation")
    if remediation is not None:
        valid_remediation(remediation)
        if (
            remediation["step_id"] != sid or remediation["next_agent_id"] != value["agent_id"]
            or remediation["next_harness"] != value["host"]
            or remediation["target_portable_tier"] != value["portable_tier"]
        ):
            raise Error("invalid worker handoff retry remediation")
    if value.get("return_schema") not in (bounded_return_schema(), bounded_return_schema(True)):
        raise Error("invalid worker handoff return schema")
    return value


def step_handoff(directory, data, plan, step):
    remediation = None
    if step.get("retry_remediation_path"):
        remediation = read_json(
            directory / rel(step["retry_remediation_path"], "retry remediation path"),
            "missing retry remediation artifact",
        )
    return build_worker_handoff(
        plan, step, data["plan_id"], data["run_id"], remediation,
        registered=data.get("return_codes") == REGISTERED_RETURN_CODES,
        changeset_base=(
            step.get("base_commit", "") if data.get("verify_policy") == "leaf_verify_v1" else None
        ),
        precision=PRECISION_POLICIES.get(data.get("precision_policy")),
    )


def handoff(args):
    directory, data, plan, _leafs = load2(args)
    validate_events2(directory, data)
    active_run(data)
    sid, step = selected_step(data, args.step_id)
    return {
        "ok": True,
        "action": "handoff",
        "handoff": step_handoff(directory, data, plan, step),
    }


def registered_worktrees(repo):
    """Map each registered worktree path of the repository to its branch name."""
    result = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise Error("cannot list git worktrees")
    entries, path = {}, None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree "):]).resolve()
            entries[path] = ""
        elif line.startswith("branch ") and path is not None:
            entries[path] = line[len("branch "):].removeprefix("refs/heads/")
    return entries


def verify_worktree_identity(repo, step, leaf, create_from):
    """Fail before any state change unless the leaf's worktree carries its branch."""
    path = Path(step["assignment"]["worktree"])
    if not path.is_absolute():
        path = repo / path
    owner = leaf["worktree_owner"]
    if not path.exists() and not path.is_symlink() and create_from:
        created = subprocess.run(
            ["git", "-C", str(repo), "worktree", "add", "-b", owner, str(path), create_from],
            text=True,
            capture_output=True,
        )
        if created.returncode:
            raise Error(f"cannot create worktree {path}: {created.stderr.strip()[:200]}")
    registry = registered_worktrees(repo)
    if path.resolve() not in registry:
        raise Error(
            f"worktree {path} is not a registered worktree of {repo}"
            + ("" if create_from else "; pass --create-from TARGET to create it")
        )
    actual = registry[path.resolve()]
    if actual != owner:
        raise Error(
            f"worktree {path} has branch {actual or 'detached'}, "
            f"expected worktree_owner {owner}"
        )


def git_head(worktree, repo):
    path = Path(worktree)
    result = subprocess.run(
        ["git", "-C", str(path if path.is_absolute() else repo / path), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise Error("cannot read worktree HEAD")
    return result.stdout.strip()


def dispatch(args):
    """Ready and start a leaf, or a whole pending batch, and return its packets."""
    directory, data, plan, leafs = mutating_run(args)
    if data.get("schema") != FORWARD_SCHEMA:
        raise Error("dispatch requires a version-5 run")
    batches = step_batches(plan)
    sid, _step = selected_step(data, args.step_id)
    members = batches.get(sid, ())
    group = (
        list(members)
        if members
        and members[0] == sid
        and all(data["steps"][member]["status"] == "pending" for member in members)
        else [sid]
    )
    # Every change stays in memory until identity and packets are proven, so a
    # failure anywhere leaves the checkpoint untouched.
    moves = []
    prerequisite = provisional_prerequisite(data, data["steps"][group[0]], batches)
    stacked = data["steps"][prerequisite]["returned_commit"] if prerequisite else ""
    for member in group:
        step = data["steps"][member]
        old = step["status"]
        ready(args, directory, data, plan, batches, step, allow_provisional=True)
        moves.append((member, old, step["attempt_id"]))
        advance(step, "ready", "ready", "in_progress", args.summary or "in progress")
    repo = repository_top(args)
    for member in group:
        verify_worktree_identity(
            repo, data["steps"][member], leafs[member], stacked or args.create_from
        )
    if stacked:
        tree = data["steps"][group[0]]["assignment"]["worktree"]
        contained = subprocess.run(
            ["git", "-C", tree if Path(tree).is_absolute() else str(repo / tree),
             "merge-base", "--is-ancestor", stacked, "HEAD"],
            capture_output=True,
        )
        if contained.returncode:
            raise Error(f"worktree {tree} does not contain provisional base {stacked[:12]}")
    if data.get("verify_policy") == "leaf_verify_v1":
        # The first member measures from the worktree HEAD at its first start; a
        # batch follower's base is the previous member's returned commit, which
        # does not exist yet, so it stays empty until the gate resolves it.
        step = data["steps"][group[0]]
        if stacked:
            step["provisional_base"] = {"step_id": prerequisite, "commit": stacked}
            step["base_commit"] = stacked
        elif "base_commit" not in step:
            step["base_commit"] = git_head(step["assignment"]["worktree"], repo)
        for member in group[1:]:
            data["steps"][member].setdefault("base_commit", "")
    packets = [step_handoff(directory, data, plan, data["steps"][member]) for member in group]
    batch = leafs[group[0]].get("batch") if len(group) > 1 else None
    entries = [
        store_dispatch_packet(
            directory, packet, (index, len(group), batch) if batch else None
        )
        for index, packet in enumerate(packets, 1)
    ]
    for member, old, attempt_id in moves:
        for before, after in ((old, "ready"), ("ready", "in_progress")):
            event(
                directory,
                data,
                f"transition-v{data['schema']}",
                step_id=member,
                from_status=before,
                to_status=after,
                attempt_id=attempt_id,
            )
    first = data["steps"][group[0]]
    return {
        "ok": True,
        "action": "dispatch",
        "run_id": args.run_id,
        "step_id": sid,
        "status": first["status"],
        "step_ids": group,
        "handoffs": entries,
        "next": bounded_action_next(
            {
                "await_step_id": first["id"],
                "agent_id": first["agent_id"],
                "attempt_id": first["attempt_id"],
            }
        ),
    }


def validate_return(args):
    try:
        handoff_raw = read_bounded_input(args.handoff_file, MAX_WORKER_HANDOFF_RAW, "worker handoff")
        return_raw = (
            sys.stdin.buffer.read(MAX_RETURN + 1)
            if args.return_file == "-"
            else read_bounded_input(args.return_file, MAX_RETURN, "step return")
        )
        if len(return_raw) > MAX_RETURN:
            raise Error("step return exceeds byte limit")
        handoff_value = json.loads(handoff_raw)
        return_value = json.loads(return_raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid worker handoff or return JSON") from exc
    handoff_value = valid_worker_handoff(handoff_value)
    if len(canon(return_value)) > MAX_RETURN:
        raise Error("bounded-step-return-v1 exceeds 8 KiB")
    step = {
        "id": handoff_value["step_id"],
        "agent_id": handoff_value["agent_id"],
        "attempt_id": handoff_value["attempt_id"],
    }
    valid_return(
        return_value, {}, step, handoff_value["leaf"],
        registered=handoff_value["return_schema"] == bounded_return_schema(True),
        standard=handoff_value.get("precision") == "standard",
    )
    return {
        "ok": True,
        "action": "validate-return",
        "plan_id": handoff_value["plan_id"],
        "run_id": handoff_value["run_id"],
        "step_id": handoff_value["step_id"],
        "agent_id": handoff_value["agent_id"],
        "attempt_id": handoff_value["attempt_id"],
        "status": return_value["status"],
        "handoff_sha256": handoff_value["handoff_sha256"],
        "return_sha256": digest(return_value),
    }


class UsageError(Error):
    """A malformed or inapplicable invocation, reported with exit status 2."""


def git_output(worktree, *arguments):
    result = subprocess.run(
        ["git", "-C", str(worktree), *arguments], text=True, capture_output=True
    )
    if result.returncode:
        raise Error(f"git {arguments[0]} failed in the worktree")
    return result.stdout


def numstat_rows(worktree, base, commit):
    """Rows of (paths, changed lines); a binary row is zero lines, a rename one row."""
    tokens = git_output(worktree, "diff", "--numstat", "-z", "-M", f"{base}..{commit}").split("\0")
    rows, index = [], 0
    while index < len(tokens):
        head = tokens[index]
        index += 1
        if not head:
            continue
        added, deleted, path = head.split("\t", 2)
        paths = [path]
        if not path:
            paths = [tokens[index + 1], tokens[index]]
            index += 2
        rows.append((paths, 0 if added == "-" else int(added) + int(deleted)))
    return rows


def dirty_paths(worktree):
    entries = git_output(worktree, "status", "--porcelain", "-z", "--untracked-files=all").split("\0")
    paths, index = [], 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) > 3:
            paths.append(entry[3:])
            if entry[0] in "RC":
                index += 1
    return paths


def changeset_verdict(worktree, base, commit, leaf, budget, standard=False):
    exempt = budget["exempt_paths"]
    covers = validator_module().write_set_covers
    lines = files = 0
    outside = []
    for paths, changed in numstat_rows(worktree, base, commit):
        if all(covers(exempt, path) for path in paths):
            continue
        lines += changed
        files += 1
        outside.extend(
            path for path in paths
            if path not in outside and not changed_path_allowed(path, leaf["write_set"])
        )
    # Uncommitted work is outside what the measured commit records, so it fails
    # the same way a path outside the write set does.
    stray = dirty_paths(worktree)
    # Standard precision lists committed outside paths for the verifier without failing the gate.
    if stray or (outside and not standard):
        verdict, listed = "outside_write_set", outside or stray
    elif lines > budget["max_changed_lines"] or files > budget["max_files"]:
        verdict, listed = "oversized:changeset", []
    else:
        verdict, listed = "pass", outside
    return {
        "ok": verdict == "pass",
        "verdict": verdict,
        "lines": lines,
        "files": files,
        "limits": {key: budget[key] for key in ("max_changed_lines", "max_files")},
        "outside": listed[:MAX_CHECK_OUTSIDE],
        "outside_count": len(listed),
    }


def returned_changeset(data, plan, leafs, sid):
    """Measure a step's returned commit: (verdict, base, commit, budget)."""
    step = data["steps"][sid]
    if data.get("verify_policy") != "leaf_verify_v1":
        raise UsageError("this run does not use leaf verification")
    commit = step["returned_commit"]
    if not commit:
        raise UsageError("the step has no returned commit")
    base = step.get("base_commit", "")
    members = step_batches(plan).get(sid, ())
    if not base and sid in members and members.index(sid) > 0:
        base = data["steps"][members[members.index(sid) - 1]]["returned_commit"]
    if not base:
        raise UsageError("the step has no recorded base commit")
    budget = validator_module().changeset_budget(leafs[sid])
    verdict = changeset_verdict(
        step["assignment"]["worktree"], base, commit, leafs[sid], budget,
        standard=standard_precision(data),
    )
    return verdict, base, commit, budget


def check_changeset(args):
    """Read-only changeset gate: builder preflight on HEAD, or the parent on a returned commit."""
    if args.handoff_file:
        if not args.worktree:
            raise UsageError("--handoff-file requires --worktree")
        packet = valid_worker_handoff(
            json.loads(read_bounded_input(args.handoff_file, MAX_WORKER_HANDOFF_RAW, "worker handoff"))
        )
        budget = packet.get("changeset_budget")
        if budget is None:
            raise UsageError("this handoff carries no changeset budget")
        base = args.base or budget["base_commit"]
        if not base:
            raise UsageError("base commit unknown for this batch member; pass --base")
        worktree, leaf = args.worktree, packet["leaf"]
        commit = git_output(worktree, "rev-parse", "HEAD").strip()
    elif args.run_id and args.step_id:
        directory, data, plan, leafs = load2(args)
        validate_events2(directory, data)
        sid, _step = selected_step(data, args.step_id)
        return returned_changeset(data, plan, leafs, sid)[0]
    else:
        raise UsageError("pass --handoff-file with --worktree, or --run-id with --step-id")
    return changeset_verdict(
        worktree, base, commit, leaf, budget, standard=packet.get("precision") == "standard"
    )


def bounded_verify_return_schema():
    finding = {
        "type": "object", "additionalProperties": False, "required": sorted(VERIFY_FINDING_FIELDS),
        "properties": {
            "code": {"enum": sorted(VERIFY_CODES)},
            "path": {"type": "string", "minLength": 1, "maxLength": MAX_PATH},
            "line": {"type": ["integer", "null"], "minimum": 1},
            "clause": {"type": "string", "minLength": 1, "maxLength": MAX_BLOCKER_SUMMARY},
            "summary": {"type": "string", "minLength": 1, "maxLength": MAX_BLOCKER_SUMMARY},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object", "additionalProperties": False,
        "required": ["schema", "step_id", "verify_id", "verdict", "findings", "notes"],
        "properties": {
            "schema": {"const": "bounded-verify-return-v1"},
            "step_id": {"type": "string"},
            "verify_id": {"type": "string", "format": "uuid"},
            "verdict": {"enum": sorted(VERIFY_VERDICTS)},
            "findings": {"type": "array", "maxItems": 8, "items": finding},
            "notes": {
                "type": "array", "maxItems": 8,
                "items": {"type": "string", "maxLength": MAX_BLOCKER_SUMMARY},
            },
        },
    }


def valid_verify_return(value):
    """Shape-check one bounded-verify-return-v1 object."""
    if not isinstance(value, dict) or len(canon(value)) > MAX_VERIFY_RETURN:
        raise Error("bounded-verify-return-v1 exceeds 4 KiB")
    if (
        set(value) != {"schema", "step_id", "verify_id", "verdict", "findings", "notes"}
        or value["schema"] != "bounded-verify-return-v1"
    ):
        raise Error("invalid bounded-verify-return-v1 schema")
    ident(value["step_id"], "step id")
    uuid4(value["verify_id"], "verify id")
    findings, notes = value["findings"], value["notes"]
    if value["verdict"] not in VERIFY_VERDICTS:
        raise Error("invalid verify verdict")
    if not isinstance(findings, list) or len(findings) > 8:
        raise Error("verify return carries at most 8 findings")
    if not isinstance(notes, list) or len(notes) > 8 or any(
        not isinstance(note, str) or len(note) > MAX_BLOCKER_SUMMARY for note in notes
    ):
        raise Error("verify return carries at most 8 notes of 240 characters")
    for finding in findings:
        line = finding.get("line") if isinstance(finding, dict) else 0
        if (
            not isinstance(finding, dict)
            or set(finding) != VERIFY_FINDING_FIELDS
            or finding["code"] not in VERIFY_CODES
            or not all(
                isinstance(finding[key], str) and finding[key].strip()
                for key in ("path", "clause", "summary")
            )
            or len(finding["path"]) > MAX_PATH
            or len(finding["clause"]) > MAX_BLOCKER_SUMMARY
            or len(finding["summary"]) > MAX_BLOCKER_SUMMARY
            or not (line is None or (isinstance(line, int) and not isinstance(line, bool) and line >= 1))
        ):
            raise Error("invalid verify finding")
    if (value["verdict"] == "reject") != bool(findings) and value["verdict"] != "inconclusive":
        raise Error("a reject carries a finding and a pass carries none")
    return value


def verify_handoff_digest(value):
    return digest({key: item for key, item in value.items() if key != "packet_sha256"})


def valid_verify_handoff(value):
    if not isinstance(value, dict) or len(canon(value)) > MAX_VERIFY_HANDOFF:
        raise Error("planning-verify-handoff-v1 exceeds 16 KiB")
    if set(value) - VERIFY_HANDOFF_OPTIONAL != VERIFY_HANDOFF_FIELDS or value["schema"] != "planning-verify-handoff-v1":
        raise Error("invalid planning-verify-handoff-v1 schema")
    if not isinstance(value["packet_sha256"], str) or value["packet_sha256"] != verify_handoff_digest(value):
        raise Error("verify handoff digest mismatch")
    ident(value["step_id"], "step id")
    uuid4(value["verify_id"], "verify id")
    prior = value["prior_verify"]
    if prior is not None and (
        not isinstance(prior, dict)
        or set(prior) != {"verify_id", "rejected_commit", "findings"}
        or not isinstance(prior["findings"], list)
        or len(prior["findings"]) > 8
    ):
        raise Error("invalid prior_verify")
    return value


def prior_verify(directory, step):
    """The step's earlier rejection, so re-verification checks the delta and each finding."""
    stored = step.get("verify")
    if not isinstance(stored, dict) or stored.get("verdict") != "reject":
        return None
    findings = read_json(directory / stored["path"], "missing stored verify return")["findings"]
    return {
        "verify_id": stored["verify_id"],
        "rejected_commit": stored["commit"],
        "findings": findings,
    }


def verify_handoff_packet(directory, data, plan, leafs, sid, step, verify_id):
    """Build one planning-verify-handoff-v1 packet for a completed step, without mutating."""
    verdict, base, commit, budget = returned_changeset(data, plan, leafs, sid)
    if not verdict["ok"]:
        raise Error(f"check-changeset verdict for {sid} is {verdict['verdict']}; verification refused")
    leaf = leafs[sid]
    unit = next(item for item in plan["work_units"] if item["id"] == leaf["work_unit_id"])
    returned = json.loads((directory / step["return_path"]).read_text())
    value = {
        "schema": "planning-verify-handoff-v1",
        "packet_sha256": "",
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "plan_sha256": data["plan_hash"],
        "step_id": sid,
        "attempt_id": step["attempt_id"],
        "agent_id": step["agent_id"],
        "verify_id": verify_id,
        "verifier_tier": VERIFIER_AGENTS[step["current_tier"]],
        "task": leaf["task"],
        "boundary": leaf["boundary"],
        "settled_decisions": leaf["settled_decisions"],
        "write_set": leaf["write_set"],
        "acceptance_command": leaf["acceptance_command"],
        "cohesive_outcome": unit["cohesive_outcome"],
        "acceptance_exit_code": returned["acceptance"]["exit_code"],
        "base_commit": base,
        "returned_commit": commit,
        "budget": budget,
        "changeset": verdict,
        "prior_verify": prior_verify(directory, step),
        "return_schema": bounded_verify_return_schema(),
    }
    if data.get("precision_policy") is not None:
        value["outside_write_set"] = verdict["outside"]
        value["outside_write_set_count"] = verdict["outside_count"]
    value["packet_sha256"] = verify_handoff_digest(value)
    if len(canon(value)) > MAX_VERIFY_HANDOFF:
        raise Error("planning-verify-handoff-v1 exceeds 16 KiB")
    return value


def verify_handoff(args):
    """Issue verifier packets for a completed step, or every completed member of its batch."""
    directory, data, plan, leafs = mutating_run(args)
    if data.get("verify_policy") != "leaf_verify_v1":
        raise Error("this run does not use leaf verification")
    sid, step = selected_step(data, args.step_id)
    if step["status"] != "completed":
        raise Error("only a completed step can be verified")
    require_not_stale(sid, step)
    members = unverified_members(data, step_batches(plan), sid)
    if not members:
        raise Error("every completed member already has a verdict for its returned commit")
    for member in members:
        require_not_stale(member, data["steps"][member])
    packets = []
    for member in members:
        packets.append(verify_handoff_packet(
            directory, data, plan, leafs, member, data["steps"][member], str(uuid.uuid4())
        ))
    for packet in packets:
        issued_step = data["steps"][packet["step_id"]]
        issued_step["verify_id"] = packet["verify_id"]
        issued_step["verify_commit"] = packet["returned_commit"]
    event(directory, data, "verify-handoff", step_id=sid, verify_step_ids=members)
    return {
        "ok": True,
        "action": "verify-handoff",
        "run_id": args.run_id,
        "step_id": sid,
        "step_ids": members,
        "handoffs": packets,
    }


def record_changeset(args):
    """Record a measured changeset failure on a completed step.

    Over budget stops oversized:changeset, never retried. A path outside the
    write set takes record-return's repairable scope rejection: the stored
    return is released so the parent can amend and re-record it.
    """
    directory, data, plan, leafs = mutating_run(args)
    sid, step = selected_step(data, args.step_id)
    if step["status"] != "completed":
        raise Error("only a completed step can have its changeset recorded")
    verdict = returned_changeset(data, plan, leafs, sid)[0]
    if verdict["verdict"] == "outside_write_set":
        step.update(return_path="", return_sha256="")
        stop_step(step, "oversized", SCOPE_REJECTION_REASON, "scope_expanded",
                  "changed path outside write_set")
        mark_dependents_stale(data, sid)
        event(directory, data, "record-changeset", step_id=sid)
        return result2("record-changeset", args, sid, step, changeset=verdict)
    if verdict["verdict"] != "oversized:changeset":
        raise Error(f"the measured changeset verdict for {sid} is {verdict['verdict']}; nothing to record")
    summary = (
        f"{verdict['lines']} changed lines in {verdict['files']} files exceed "
        f"{verdict['limits']['max_changed_lines']} lines / {verdict['limits']['max_files']} files"
    )
    stop_step(step, "oversized", "oversized:changeset", "oversized:changeset", summary)
    mark_dependents_stale(data, sid)
    event(directory, data, "record-changeset", step_id=sid)
    return result2("record-changeset", args, sid, step, changeset=verdict)


def validate_verify_return(args):
    try:
        packet = json.loads(read_bounded_input(args.handoff_file, MAX_VERIFY_HANDOFF + 1024, "verify handoff"))
        value = json.loads(read_bounded_input(args.return_file, MAX_VERIFY_RETURN, "verify return"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid verify handoff or return JSON") from exc
    packet = valid_verify_handoff(packet)
    valid_verify_return(value)
    if value["step_id"] != packet["step_id"] or value["verify_id"] != packet["verify_id"]:
        raise Error("stale or foreign verify return identity")
    return {
        "ok": True,
        "action": "validate-verify-return",
        "step_id": packet["step_id"],
        "verify_id": packet["verify_id"],
        "verdict": value["verdict"],
        "packet_sha256": packet["packet_sha256"],
        "return_sha256": digest(value),
    }


def verify_rejection_return(directory, step, verify):
    """Synthesize the failed:verification return a reject stands for.

    The builder's changed paths, acceptance, and commit carry over; the blocker
    cites the stored verify return and its digest as evidence. The builder's own
    completed return is superseded; the note carries no digest so a repeated
    reject keeps the same progress fingerprint.
    """
    original = current_return(directory, step)
    stored = step["verify"]
    codes = ", ".join(dict.fromkeys(finding["code"] for finding in verify["findings"]))
    return {
        "schema": "bounded-step-return-v1",
        "step_id": step["id"],
        "attempt_id": step["attempt_id"],
        "agent_id": step["agent_id"],
        "status": "failed",
        "changed_paths": original["changed_paths"],
        "acceptance": original["acceptance"],
        "blockers": [{
            "code": "failed:verification",
            "summary": f"verifier rejected the build: {codes}"[:MAX_BLOCKER_SUMMARY],
            "evidence_path": stored["path"],
            "sha256": stored["sha256"],
        }],
        "notes": [{
            "type": "finding",
            "message": "the builder's completed return was superseded by a verifier reject",
        }],
        "unstarted_remainder": [],
        "commit_hash": step["returned_commit"],
    }


def reject_verified_step(directory, data, step, failure):
    """Move a rejected completed step to failed through the one retry predicate."""
    copy = directory / step["return_path"]
    write(copy, failure, MAX_RETURN)
    step["return_sha256"] = digest(failure)
    step["reason"] = failure["blockers"][0]["summary"]
    step["retry_allowed"] = True
    # The superseded completed return left its fingerprint last; drop it so a
    # repeated reject compares with the previous reject, not with that success.
    step["fingerprints"].pop()
    # Each verify return has its own digest, so fingerprint the codes alone.
    bare = dict(failure, blockers=[{key: failure["blockers"][0][key] for key in ("code", "summary")}])
    return settle_return(data, step, failure, return_fingerprint(bare))


def record_verify(args):
    """Store a verifier verdict bound to the step's returned commit."""
    directory, data, plan, leafs = mutating_run(args)
    raw = read_bounded_input(args.return_file, MAX_VERIFY_RETURN, "verify return")
    try:
        value = valid_verify_return(json.loads(raw))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid verify return JSON") from exc
    sid = value["step_id"]
    step = data["steps"].get(sid)
    if data.get("verify_policy") != "leaf_verify_v1" or step is None or step["status"] != "completed":
        raise Error("verify return is not for a completed step of a leaf-verification run")
    if not step.get("verify_id") or step["verify_id"] != value["verify_id"]:
        raise Error("stale or foreign verify_id")
    if step.get("verify_commit") != step["returned_commit"]:
        raise Error("the step's returned commit changed since verify-handoff")
    batches = step_batches(plan)
    group = batches.get(sid) or (sid,)
    # A batch shares one worktree, so its HEAD is the tip: the last completed member's commit.
    tip = data["steps"][[m for m in group if data["steps"][m]["status"] == "completed"][-1]]["returned_commit"]
    worktree = step["assignment"]["worktree"]
    if git_head(worktree, repository_top(args)) != tip or dirty_paths(worktree):
        raise Error("worktree changed since the returned commit: verifier mutation refused")
    copy = directory / "verifies" / sid / f"{value['verify_id']}.json"
    write(copy, value, MAX_VERIFY_RETURN)
    step["verify"] = {
        "verdict": value["verdict"],
        "commit": step["returned_commit"],
        "verify_id": value["verify_id"],
        "path": str(copy.relative_to(directory)),
        "sha256": digest(value),
    }
    step["verify_id"] = ""
    disposition, failure = "", None
    if value["verdict"] == "reject":
        failure = verify_rejection_return(directory, step, value)
        disposition = reject_verified_step(directory, data, step, failure)
        mark_dependents_stale(data, sid)
    event(directory, data, "record-verify", step_id=sid, verdict=value["verdict"])
    result = result2("record-verify", args, sid, step, verdict=value["verdict"])
    if disposition:
        result["next"] = next_after_return(
            args, directory, data, batches, sid, step, failure, disposition, plan
        )
    elif value["verdict"] in VERIFY_PASSING:
        if group_landable(data, batches, sid) and not unverified_members(data, batches, sid):
            result["next"] = bounded_next({"command": land_command(data, sid)})
        else:
            result["next"] = checkpoint_next(directory, data, batches, plan)
    return result


def mark_dependents_stale(data, sid):
    """Flag each step stacked on `sid`'s commit, which `sid` no longer stands behind."""
    for other in data["steps"].values():
        base = other.get("provisional_base")
        if (
            base
            and base["step_id"] == sid
            and not other.get("upstream_stale")
            and other["status"] not in EXTERNAL_DEPENDENCY_STATES
        ):
            other["upstream_stale"] = {"step_id": sid, "commit": base["commit"]}


def restack_target(data, step):
    """The prerequisite and its new base for a stale step, or ("", "") while it must wait.

    A completed prerequisite supplies its new returned commit; an integrated one
    leaves the parent tip as the base, which the caller resolves.
    """
    stale = step.get("upstream_stale")
    base = step.get("provisional_base")
    if not stale or not base:
        return "", ""
    prerequisite = data["steps"][stale["step_id"]]
    if prerequisite["status"] in EXTERNAL_DEPENDENCY_STATES:
        return stale["step_id"], "parent"
    if (
        prerequisite["status"] == "completed"
        and not prerequisite.get("upstream_stale")
        and prerequisite["returned_commit"] not in {"", base["commit"]}
    ):
        return stale["step_id"], prerequisite["returned_commit"]
    return "", ""


def restack_ready(data, step):
    return step["status"] == "completed" and bool(restack_target(data, step)[0])


def restack_command(data, step_id):
    return (
        f"--plan-id {data['plan_id']} restack --actor parent --run-id {data['run_id']} "
        f"--step-id {step_id}"
    )


def patch_id(worktree, base, commit):
    """Stable patch-id of the diff between two commits; "" when the diff is empty."""
    diff = git_output(worktree, "diff", base, commit)
    result = subprocess.run(
        ["git", "-C", str(worktree), "patch-id", "--stable"],
        input=diff, text=True, capture_output=True,
    )
    return result.stdout.split()[0] if result.returncode == 0 and result.stdout.split() else ""


def restack_failure(directory, data, step, old, new, why):
    """Route a failed restack to the repairable blocked:upstream_changed through the retry predicate."""
    original = current_return(directory, step)
    summary = f"restack onto {new[:12]} from {old[:12]} failed: {why}"[:MAX_BLOCKER_SUMMARY]
    failure = {
        "schema": "bounded-step-return-v1",
        "step_id": step["id"],
        "attempt_id": step["attempt_id"],
        "agent_id": step["agent_id"],
        "status": "blocked",
        "changed_paths": original["changed_paths"],
        "acceptance": original["acceptance"],
        "blockers": [{"code": "blocked:upstream_changed", "summary": summary}],
        "notes": [{
            "type": "finding",
            "message": "the builder's completed return was superseded by a failed restack",
        }],
        "unstarted_remainder": [],
        "commit_hash": step["returned_commit"],
    }
    step["upstream_change"] = {"old": old, "new": new}
    write(directory / step["return_path"], failure, MAX_RETURN)
    step.update(return_sha256=digest(failure), reason=summary, retry_allowed=True, verify_id="")
    step["fingerprints"].pop()
    return settle_return(data, step, failure, digest(failure))


def restack(args):
    """Rebase a completed stale step onto its prerequisite's new base, keeping its verdict only for an unchanged patch."""
    directory, data, plan, _leafs = mutating_run(args)
    if data.get("pipeline_policy") != PIPELINE_POLICY:
        raise Error("restack requires a run with provisional starts")
    sid, step = selected_step(data, args.step_id)
    if step["status"] != "completed" or not step.get("upstream_stale"):
        raise Error("only a completed stale step can be restacked")
    batches = step_batches(plan)
    if sid in batches:
        raise Error("restack does not support batch members")
    prerequisite, new = restack_target(data, step)
    if not prerequisite:
        raise Error("the prerequisite has no new completed commit and is not integrated")
    repo = repository_top(args)
    worktree = Path(step["assignment"]["worktree"])
    if not worktree.is_absolute():
        worktree = repo / worktree
    if new == "parent":
        new = git_output(repo, "rev-parse", "HEAD").strip()
    if dirty_paths(worktree):
        raise Error("the step's worktree has uncommitted changes")
    old, returned = step["provisional_base"]["commit"], step["returned_commit"]
    head = git_output(worktree, "rev-parse", "HEAD").strip()
    contained = subprocess.run(
        ["git", "-C", str(worktree), "merge-base", "--is-ancestor", new, "HEAD"], capture_output=True
    ).returncode == 0
    blocked = ""
    anchor = ""
    if not contained:
        # A recorded pending restack moves the target again from its rebased base, not the returned commit.
        anchor = (step.get("pending_acceptance") or {}).get("new", "")
        if anchor:
            if subprocess.run(
                ["git", "-C", str(worktree), "merge-base", "--is-ancestor", anchor, "HEAD"],
                capture_output=True,
            ).returncode:
                raise Error("the step's worktree no longer contains its pending restack base")
        elif head != returned:
            raise Error("the step's worktree is not at its returned commit")
        if args.acceptance_exit_code is not None:
            raise Error(
                "restack rebases first: run it without --acceptance-exit-code, re-run the scoped "
                "acceptance in the rebased worktree, then repeat with the code"
            )
        rebased = subprocess.run(
            ["git", "-C", str(worktree), "rebase", "--onto", new, anchor or old], text=True, capture_output=True
        )
        if rebased.returncode:
            subprocess.run(["git", "-C", str(worktree), "rebase", "--abort"], capture_output=True)
            blocked = "rebase conflict"
            if anchor:
                # The aborted worktree still sits on the earlier rebase, so record that base.
                step["base_commit"] = step["provisional_base"]["commit"] = anchor
    if not blocked:
        head = git_output(worktree, "rev-parse", "HEAD").strip()
        if git_output(worktree, "rev-parse", f"{head}^{{tree}}") != git_output(
            worktree, "rev-parse", f"{returned}^{{tree}}"
        ):
            if args.acceptance_exit_code is None:
                # The rebase landed: record what acceptance must re-run against, never fail after changing the worktree.
                step["pending_acceptance"] = {"old": old, "new": new}
                event(directory, data, "restack", step_id=sid, outcome="acceptance_pending")
                return result2(
                    "restack", args, sid, step, outcome="acceptance_pending", verdict_carried=False,
                    next=bounded_action_next(
                        {
                            "category": "restack_acceptance",
                            "step_ids": [sid],
                            "command": restack_command(data, sid) + " --acceptance-exit-code N",
                        },
                        "step_ids",
                    ),
                )
            if args.acceptance_exit_code != 0:
                blocked = f"acceptance exit {args.acceptance_exit_code} after the rebase"
                step["base_commit"] = new
                step["provisional_base"]["commit"] = new
    carried = False
    step.pop("pending_acceptance", None)
    if blocked:
        disposition = restack_failure(directory, data, step, old, new, blocked)
    else:
        same = patch_id(worktree, old, returned) == patch_id(worktree, new, head)
        carried = same and commit_verified(step)
        if carried:
            step["verify"]["commit"] = head
        else:
            step.pop("verify", None)
        step.update(
            returned_commit=head, base_commit=new, verify_id="", verify_commit="",
        )
        step["provisional_base"]["commit"] = new
        del step["upstream_stale"]
        step.pop("upstream_change", None)
        disposition = "restacked"
    mark_dependents_stale(data, sid)
    event(directory, data, "restack", step_id=sid, outcome=disposition)
    return result2(
        "restack", args, sid, step, outcome=disposition, verdict_carried=carried,
        next=checkpoint_next(directory, data, batches, plan),
    )


def read_bounded_input(path, maximum, label):
    """Read at most one byte beyond a fixed input bound before JSON parsing."""
    try:
        with Path(path).open("rb") as file:
            raw = file.read(maximum + 1)
    except OSError as exc:
        raise Error(f"cannot read {label}") from exc
    if len(raw) > maximum:
        raise Error(f"{label} exceeds byte limit")
    return raw


def next_after_return(args, directory, data, batches, sid, step, value, disposition, plan):
    """Report the retry decision `record` just made under the escalating policy."""
    scope = f"--plan-id {args.plan_id} transition --actor parent --run-id {args.run_id}"
    if disposition == "completed" and not batch_settled(data, batches, sid):
        return checkpoint_next(directory, data, batches, plan)
    if disposition == "retry_eligible":
        tier = step["current_tier"]
        kind, outcome = retry_class(data, step, value)
        if needs_higher_tier(step, kind, outcome):
            tier = PORTABLE_TIERS[PORTABLE_TIERS.index(tier) + 1]
        return bounded_next(
            {
                "retry_eligible": True,
                "retry_class": kind,
                "outcome": outcome,
                "next_tier": tier,
                "command": (
                    f"{scope} --step-id {sid} --to ready --retry "
                    "--retry-remediation-file <retry-remediation-v1.json>"
                ),
            },
            droppable=("command",),
        )
    block = {"retry_eligible": False, "outcome": disposition}
    if disposition == "completed":
        if step.get("scope_notes"):
            block["outside_paths"] = list(step["scope_notes"])
        if data.get("verify_policy") == "leaf_verify_v1":
            # The gate is not droppable convenience: it is the next legal action.
            block.update(verify_commands(data, sid))
            return bounded_action_next(block, "outside_paths")
        block["command"] = integrate_command(data, sid)
    return bounded_next(block, droppable=("command",), trimmable="outside_paths")


def amend(args):
    """Parent-only execution-metadata amendment; plan.json and plan_hash never change."""
    directory, data, plan, leafs = mutating_run(args)
    if data.get("schema") != FORWARD_SCHEMA:
        raise Error("amend requires a version-5 run")
    sid, step = selected_step(data, args.step_id)
    if step["status"] not in AMENDABLE_STATES:
        raise Error(f"a {step['status']} step cannot be amended")
    reason = bounded_reason(args.reason, "amend", required=True)
    current = leafs[sid]
    # Operator input errors are named plainly; `valid_amendments` below stays the
    # fail-closed check that reports any stored-state mismatch as tampering.
    if len(step.get("amendments", [])) >= MAX_AMENDMENTS:
        raise Error(f"a step carries at most {MAX_AMENDMENTS} amendments")
    if args.max_attempts is not None and not (
        current["max_attempts"] < args.max_attempts <= MAX_AMENDED_ATTEMPTS
    ):
        raise Error(
            f"--max-attempts must raise max_attempts above {current['max_attempts']}"
            f" and stay at most {MAX_AMENDED_ATTEMPTS}"
        )
    if args.acceptance_command is not None and not (
        1 <= len(args.acceptance_command) <= MAX_AMENDED_COMMAND
    ):
        raise Error(f"--acceptance-command must be 1 to {MAX_AMENDED_COMMAND} characters")
    requested = {"add_write": args.add_write, "add_read": args.add_read}
    amendment = {"reason": reason}
    for key, field in (("add_write", "write_set"), ("add_read", "read_set")):
        paths = list(dict.fromkeys(requested[key]))
        if len(paths) > MAX_AMENDMENT_PATHS:
            raise Error("amendment exceeds 8 paths per list")
        amendment[key] = [rel(path, "amendment path") for path in paths if path not in current[field]]
    if args.acceptance_command is not None and args.acceptance_command != current["acceptance_command"]:
        amendment["acceptance_command"] = args.acceptance_command
    if args.max_attempts is not None:
        amendment["max_attempts"] = args.max_attempts
    if not (
        amendment["add_write"]
        or amendment["add_read"]
        or {"acceptance_command", "max_attempts"} & set(amendment)
    ):
        raise Error("amendment changes nothing")
    amendment.update(
        after_attempt_id=step["attempt_id"],
        after_attempt_count=step["attempt_count"],
        return_recorded=attempt_return_recorded(step),
    )
    amendments = [*step.get("amendments", []), amendment]
    approved = leaves_by_id(plan)[sid]
    valid_amendments({"amendments": amendments}, approved, data["schema"])
    candidate = {**leafs, sid: effective_leaf(current, [amendment])}
    admitted = plan_validator()(
        {**plan, "leaves": [candidate[leaf["id"]] for leaf in plan["leaves"]]},
        capability_binding=None,
        admission=True,
    )
    if not admitted.get("valid") or not admitted.get("approval_ready"):
        raise Error("amended plan is not approval-ready: " + "; ".join(admitted.get("errors", []))[:200])
    step["amendments"] = amendments
    if "max_attempts" in amendment:
        step["max_attempts"] = amendment["max_attempts"]
    event(directory, data, "amend-v5", step_id=sid, amendment_sha256=digest(amendment), amendment_count=len(amendments))
    if scope_rejection_state(step) and amendment["add_write"]:
        following = bounded_action_next(
            {
                "category": "rerecord_return",
                "step_id": sid,
                "command": (
                    f"--plan-id {args.plan_id} record-return --actor parent "
                    f"--run-id {args.run_id} --return-file <bounded-step-return-v1.json>"
                ),
            }
        )
    else:
        following = checkpoint_next(directory, data, step_batches(plan), plan)
    return result2(
        "amend-v5", args, sid, step,
        amendment_count=len(amendments), amendment_sha256=digest(amendment), next=following,
    )


def return_fingerprint(value):
    return digest(
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


def settle_return(data, step, value, fingerprint):
    """Apply the retry policy to a stored return and name the branch that fired."""
    previous = step["fingerprints"][-1] if step["fingerprints"] else ""
    retry = retry_class(data, step, value)
    step["fingerprints"].append(fingerprint)
    step["fingerprints"] = step["fingerprints"][-5:]
    # `disposition` names the branch that actually fired, so a `next` block
    # reports this decision instead of modelling the precedence a second time.
    if value["status"] in {"completed", "oversized"}:
        step.update(status=value["status"], retry_allowed=False)
        disposition = value["status"]
    elif previous == fingerprint:
        stop_step(
            step,
            "blocked",
            "blocked:no_progress",
            "blocked:no_progress",
            "repeated non-completed progress fingerprint",
        )
        disposition = "blocked:no_progress"
    elif data.get("retry_policy") == ESCALATING_RETRY_POLICY and not retry[0]:
        step.update(status=value["status"], retry_allowed=False)
        disposition = "ineligible_outcome"
    elif step["attempt_count"] >= step["max_attempts"]:
        stop_step(
            step,
            "blocked",
            "blocked:retry_exhausted",
            "blocked:retry_exhausted",
            "attempt limit reached with differing progress fingerprint",
        )
        disposition = "blocked:retry_exhausted"
    elif (
        data.get("retry_policy") == ESCALATING_RETRY_POLICY
        and needs_higher_tier(step, *retry)
        and step["current_tier"] == PORTABLE_TIERS[-1]
    ):
        stop_step(
            step,
            "blocked",
            "blocked:retry_ceiling_reached",
            "blocked:retry_ceiling_reached",
            "eligible retry requires a tier above deep",
        )
        disposition = "blocked:retry_ceiling_reached"
    else:
        step["status"] = value["status"]
        disposition = "retry_eligible"
    if step["reason"] not in {
        "blocked:no_progress",
        "blocked:retry_exhausted",
        "blocked:retry_ceiling_reached",
    }:
        step["blockers"] = value["blockers"]
    return disposition


def record(args):
    directory, data, plan, leafs = mutating_run(args)
    raw = Path(args.return_file).read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid step return JSON") from exc
    sid = value.get("step_id") if isinstance(value, dict) else ""
    step = data["steps"].get(sid)
    repairable_scope_rejection = step is not None and scope_rejection_state(step)
    if step is None or (step["status"] != "in_progress" and not repairable_scope_rejection):
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
        value = valid_return(value, data, step, leafs[sid], standard=standard_precision(data))
    except Error as exc:
        if str(exc) == "changed path outside write_set":
            reject_return(
                directory,
                data,
                step,
                sid,
                SCOPE_REJECTION_REASON,
                "scope_expanded",
                "changed path outside write_set",
            )
        raise
    fingerprint = return_fingerprint(value)
    if standard_precision(data):
        outside = outside_paths(value["changed_paths"], leafs[sid]["write_set"])
        step["scope_notes_count"] = len(outside)
        if outside:
            step["scope_notes"] = outside[:MAX_CHECK_OUTSIDE]
        else:
            step.pop("scope_notes", None)
    copy = directory / "returns" / sid / f"{step['attempt_id']}.json"
    write(copy, value, MAX_RETURN)
    step["return_path"] = str(copy.relative_to(directory))
    step["return_sha256"] = digest(value)
    step["returned_commit"] = value["commit_hash"]
    step["reason"] = (
        value["acceptance"]["summary"]
        or (value["blockers"][0]["summary"] if value["blockers"] else value["status"])
    )[:480]
    disposition = settle_return(data, step, value, fingerprint)
    event(
        directory,
        data,
        "record-return",
        step_id=sid,
        status=step["status"],
        attempt_id=step["attempt_id"],
        fingerprint=fingerprint,
    )
    result = result2("record-return", args, sid, step, progress_fingerprint=fingerprint)
    if "scope_notes_count" in step:
        result["scope_notes_count"] = step["scope_notes_count"]
    # Only the escalating policy owns retries, so only it can state eligibility.
    # A policy-less v2/v3 run keeps its original silent result.
    if data.get("retry_policy") == ESCALATING_RETRY_POLICY:
        result["next"] = next_after_return(
            args, directory, data, step_batches(plan), sid, step, value, disposition, plan
        )
    return result


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
        raise Error("missing required v2 contents")
    if names - allowed:
        raise Error("unexpected v2 contents")
    for name in ("checkpoint.json", "events.jsonl", "plan.json"):
        if not (directory / name).is_file():
            raise Error("unexpected v2 contents")
    handoff = directory / "series-handoff.json"
    if handoff.exists() and (handoff.is_symlink() or not handoff.is_file()):
        raise Error("unexpected series-handoff.json contents")
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
    verifies = directory / "verifies"
    if verifies.exists():
        if verifies.is_symlink() or not verifies.is_dir():
            raise Error("unexpected verifies contents")
        for step_dir in verifies.iterdir():
            if step_dir.is_symlink() or not step_dir.is_dir():
                raise Error("unexpected verifies contents")
            ident(step_dir.name, "verify step id")
            for stored in step_dir.iterdir():
                if stored.is_symlink() or not stored.is_file() or stored.suffix != ".json":
                    raise Error("unexpected verifies contents")
                uuid4(stored.stem, "verify id")
    stored_packets = directory / "handoffs"
    if stored_packets.exists():
        if stored_packets.is_symlink() or not stored_packets.is_dir():
            raise Error("unexpected handoffs contents")
        for step_dir in stored_packets.iterdir():
            if step_dir.is_symlink() or not step_dir.is_dir():
                raise Error("unexpected handoffs contents")
            ident(step_dir.name, "handoff step id")
            for stored in step_dir.iterdir():
                if stored.is_symlink() or not stored.is_file() or stored.suffix != ".json":
                    raise Error("unexpected handoffs contents")
                uuid4(stored.stem, "handoff attempt id")
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
    if checkpoint.get("schema") not in RUN_SCHEMAS:
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
    plan_result = plan_validator()(plan, capability_binding=checkpoint_binding(checkpoint), admission=False)
    ready_key = "dispatch_ready" if checkpoint["schema"] == FORWARD_SCHEMA else "resume_ready"
    if (
        not plan_result.get(ready_key)
        or plan_result.get("contract_version") != checkpoint["schema"]
    ):
        raise Error("blocked:plan_tampered")
    validate_steps2(checkpoint, leaves_by_id(plan))
    validate_retry_artifacts(directory, checkpoint)
    validate_series_handoff(directory, checkpoint, plan)
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
    if entry["contract_version"] in RUN_SCHEMAS:
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
    if entry["contract_version"] in RUN_SCHEMAS:
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


def summary(data, batches):
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
        if ready_status_legal(s) and dependencies_clean(data, s, batches)
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
    if args.next_only:
        if not args.run_id:
            raise Error("show --next-only requires a version-4 or version-5 run")
        if args.step_id:
            raise Error("show --next-only does not accept --step-id")
        directory, data, plan, _leafs = load2(args)
        if (
            data.get("schema") not in LIVE_NEXT_SCHEMAS
            or data.get("retry_policy") != ESCALATING_RETRY_POLICY
        ):
            raise Error("show --next-only requires a version-4 or version-5 run")
        validate_events2(directory, data)
        result = {
            "ok": True,
            "action": "show-next",
            "plan_id": data["plan_id"],
            "run_id": data["run_id"],
            "next": checkpoint_next(directory, data, step_batches(plan), plan),
        }
        if proxy_tokens(result) > MAX_NEXT_ONLY_TOKENS:
            raise Error("show --next-only exceeds 240 proxy tokens")
        return result
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
                **({"amendment_count": len(step["amendments"])} if step.get("amendments") else {}),
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
    result = summary(data, step_batches(plan))
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
    if data["schema"] != 3 and data["schema"] not in LIVE_NEXT_SCHEMAS:
        raise Error("tracing requires a contract version 3, 4, or 5 run")
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
    result = {
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
    if (
        args.closeout
        and data.get("schema") in LIVE_NEXT_SCHEMAS
        and data.get("retry_policy") == ESCALATING_RETRY_POLICY
        and data["steps"]
        and all(step["status"] == "cleaned" for step in data["steps"].values())
    ):
        command = (
            f"--plan-id {data['plan_id']} close --actor parent "
            f"--run-id {data['run_id']} --outcome completed"
        )
        # A final series slice hands nothing on and takes no handoff file; a
        # non-final slice's completed close always requires one (see
        # `series_close_handoff`), so the hinted command names it up front.
        if series_non_final(plan):
            command += " --series-handoff-file <path>"
        result["next"] = bounded_action_next(
            series_closeout_overlay(plan, {"command": command})
        )
    return result


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
    init5_parser = commands.add_parser("init-v5")
    init5_parser.add_argument("--actor", required=True)
    init5_parser.add_argument("--approved", action="store_true")
    init5_parser.add_argument("--plan-file", required=True)
    init5_parser.add_argument("--assignments-file")
    init5_parser.add_argument("--capability-binding-file")
    init5_parser.add_argument("--host")
    init5_parser.add_argument("--evidence", default="")
    init5_parser.add_argument("--pin-roots", nargs="+", metavar="ROOT")
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
    dispatching = commands.add_parser("dispatch")
    dispatching.add_argument("--actor", required=True)
    dispatching.add_argument("--run-id", required=True)
    dispatching.add_argument("--step-id", required=True)
    dispatching.add_argument("--agent-id", default="")
    dispatching.add_argument("--harness", default="")
    dispatching.add_argument("--model-or-alias", default="")
    dispatching.add_argument("--capability-binding-file", default="")
    dispatching.add_argument("--summary", default="")
    dispatching.add_argument("--retry", action="store_true")
    dispatching.add_argument("--retry-remediation-file", default="")
    dispatching.add_argument("--create-from", default="")
    landing = commands.add_parser("land")
    landing.add_argument("--actor", required=True)
    landing.add_argument("--run-id", required=True)
    landing.add_argument("--step-id", required=True)
    landing.add_argument("--target", required=True)
    landing.add_argument("--summary", default="")
    amending = commands.add_parser("amend")
    amending.add_argument("--actor", required=True)
    amending.add_argument("--run-id", required=True)
    amending.add_argument("--step-id", required=True)
    amending.add_argument("--reason", required=True)
    amending.add_argument("--add-write", action="append", default=[])
    amending.add_argument("--add-read", action="append", default=[])
    amending.add_argument("--acceptance-command")
    amending.add_argument("--max-attempts", type=int)
    rec = commands.add_parser("record-return")
    rec.add_argument("--actor", required=True)
    rec.add_argument("--run-id")
    rec.add_argument("--return-file", required=True)
    sh = commands.add_parser("show")
    sh.add_argument("--run-id")
    sh.add_argument("--step-id", default="")
    sh.add_argument("--next-only", action="store_true")
    va = commands.add_parser("validate")
    va.add_argument("--run-id")
    va.add_argument("--closeout", action="store_true")
    worker_handoff = commands.add_parser("handoff")
    worker_handoff.add_argument("--run-id", required=True)
    worker_handoff.add_argument("--step-id", required=True)
    validate_return_parser = commands.add_parser("validate-return")
    validate_return_parser.add_argument("--handoff-file", required=True)
    validate_return_parser.add_argument("--return-file", required=True)
    check_parser = commands.add_parser("check-changeset")
    check_parser.add_argument("--handoff-file")
    check_parser.add_argument("--worktree")
    check_parser.add_argument("--base")
    check_parser.add_argument("--run-id")
    check_parser.add_argument("--step-id")
    verify_parser = commands.add_parser("verify-handoff")
    verify_parser.add_argument("--actor", required=True)
    verify_parser.add_argument("--run-id", required=True)
    verify_parser.add_argument("--step-id", required=True)
    validate_verify_parser = commands.add_parser("validate-verify-return")
    validate_verify_parser.add_argument("--handoff-file", required=True)
    validate_verify_parser.add_argument("--return-file", required=True)
    record_verify_parser = commands.add_parser("record-verify")
    record_verify_parser.add_argument("--actor", required=True)
    record_verify_parser.add_argument("--run-id", required=True)
    record_verify_parser.add_argument("--return-file", required=True)
    restack_parser = commands.add_parser("restack")
    restack_parser.add_argument("--actor", required=True)
    restack_parser.add_argument("--run-id", required=True)
    restack_parser.add_argument("--step-id", required=True)
    restack_parser.add_argument("--acceptance-exit-code", type=int)
    record_changeset_parser = commands.add_parser("record-changeset")
    record_changeset_parser.add_argument("--actor", required=True)
    record_changeset_parser.add_argument("--run-id", required=True)
    record_changeset_parser.add_argument("--step-id", required=True)
    commands.add_parser("list")
    close = commands.add_parser("close")
    close.add_argument("--actor", required=True)
    close.add_argument("--run-id", required=True)
    close.add_argument("--outcome", choices=("completed", "blocked", "abandoned"), required=True)
    close.add_argument("--reason", default="")
    close.add_argument("--series-handoff-file", default="")
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
        elif args.command == "init-v5":
            value = init5(args)
        elif args.command == "transition":
            value = transition2(args) if args.run_id else transition1(args)
        elif args.command == "dispatch":
            value = dispatch(args)
        elif args.command == "land":
            value = land(args)
        elif args.command == "amend":
            value = amend(args)
        elif args.command == "record-return":
            value = record(args)
        elif args.command == "show":
            value = show(args)
        elif args.command == "validate":
            value = validate(args)
        elif args.command == "handoff":
            value = handoff(args)
        elif args.command == "validate-return":
            value = validate_return(args)
        elif args.command == "verify-handoff":
            value = verify_handoff(args)
        elif args.command == "validate-verify-return":
            value = validate_verify_return(args)
        elif args.command == "record-verify":
            value = record_verify(args)
        elif args.command == "record-changeset":
            value = record_changeset(args)
        elif args.command == "restack":
            value = restack(args)
        elif args.command == "check-changeset":
            value = check_changeset(args)
            return out(value, 0 if value["ok"] else 1)
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
    except UsageError as exc:
        return out({"ok": False, "error": str(exc)}, 2)
    except Error as exc:
        return out({"ok": False, "error": str(exc)}, 3)
    except OSError as exc:
        return out({"ok": False, "error": f"I/O failure: {exc}"}, 4)


if __name__ == "__main__":
    sys.exit(main())
