"""Planning ledger returns: return validation, retry and remediation, record-return and amend."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import contract
from .checkpoint import mutating_run, scope_rejection_state, valid_remediation
from .contract import (
    effective_leaf,
    leaves_by_id,
    outside_paths,
    standard_precision,
    valid_amendments,
    valid_stored_binding,
)
from .core import (
    Error,
    JsonObject,
    JsonValue,
    bounded_reason,
    canon,
    digest,
    ident,
    read_bounded_bytes,
    rel,
    require_sha256,
    selected_step,
    uuid4,
)
from .schedule import (
    Batches,
    attempt_return_recorded,
    batch_settled,
    bounded_action_next,
    bounded_next,
    checkpoint_next,
    land_command,
    retry_class,
    step_batches,
    verify_commands,
)
from .store import event, write
from .vocabulary import (
    AMENDABLE_STATES,
    CHANGESET_BUDGET_FIELDS,
    COMMIT,
    DISPATCH_ENTRY_FIELDS,
    FORWARD_SCHEMA,
    ID,
    MAX_ACCEPTANCE_SUMMARY,
    MAX_AMENDED_ATTEMPTS,
    MAX_AMENDED_COMMAND,
    MAX_AMENDMENT_PATHS,
    MAX_AMENDMENTS,
    MAX_BLOCKER_CODE,
    MAX_BLOCKER_SUMMARY,
    MAX_BLOCKERS,
    MAX_CHANGED_PATHS,
    MAX_CHECK_OUTSIDE,
    MAX_NOTE_MESSAGE,
    MAX_NOTES,
    MAX_PATH,
    MAX_REMAINDER,
    MAX_REMAINDER_ITEM,
    MAX_RETURN,
    MAX_WORKER_HANDOFF,
    MAX_WORKER_HANDOFF_RAW,
    NOTE_TYPES,
    PORTABLE_TIERS,
    PRECISION_POLICIES,
    REGISTERED_RETURN_CODES,
    RETURN_CODES,
    RETURN_STATUSES,
    SCOPE_REJECTION_REASON,
    SHA,
    VERIFIER_ONLY_CODES,
    WORKER_HANDOFF_FIELDS,
)

__all__ = [
    "stop_step",
    "reject_return",
    "step_result",
    "advance",
    "needs_higher_tier",
    "valid_return",
    "bounded_return_schema",
    "worker_handoff_digest",
    "worker_handoff_context",
    "valid_worker_handoff",
    "validate_return",
    "read_bounded_input",
    "next_after_return",
    "amend",
    "return_fingerprint",
    "settle_return",
    "record",
]


def stop_step(step: JsonObject, status: str, reason: str, code: str, summary: str) -> None:
    step.update(
        status=status,
        retry_allowed=False,
        reason=reason,
        blockers=[{"code": code, "summary": summary}],
    )


def reject_return(
    directory: Path,
    data: JsonObject,
    step: JsonObject,
    sid: str,
    reason: str,
    code: str,
    summary: str,
) -> None:
    stop_step(step, "oversized", reason, code, summary)
    event(directory, data, "record-return", step_id=sid, status="oversized")


def step_result(
    action: str, args: argparse.Namespace, sid: str, step: JsonObject, **extra: object
) -> JsonObject:
    return {
        "ok": True,
        "action": action,
        "run_id": args.run_id,
        "step_id": sid,
        "status": step["status"],
        **extra,
    }


def advance(step: JsonObject, old: str, expected: str, target: str, summary: str) -> None:
    if old != expected:
        raise Error(f"only {expected} steps can become {target}")
    step.update(status=target, reason=summary[:480])


def needs_higher_tier(step: JsonObject, kind: str, outcome: str) -> bool:
    return kind == "reasoning" and (
        outcome == "blocked:needs_higher_tier"
        or (
            outcome in {"failed:acceptance", "failed:verification"}
            and (step["same_tier_retry_used"] or step["attempt_count"] > 1)
        )
    )


def valid_return(
    value: JsonValue,
    data: JsonObject,
    step: JsonObject,
    leaf: JsonObject,
    registered: bool | None = None,
    standard: bool = False,
) -> JsonObject:
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
        if not standard and not contract.changed_path_allowed(path, leaf["write_set"]):
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
            raise Error(
                "failed:verification is recorded only by the ledger, never returned by a worker"
            )
        allowed = set().union(*RETURN_CODES.values()) - VERIFIER_ONLY_CODES
        if any(blocker["code"] not in allowed for blocker in blockers):
            raise Error("blocker code is not registered: use " + ", ".join(sorted(allowed)))
        family = RETURN_CODES.get(value["status"], ())
        if family and not any(blocker["code"] in family for blocker in blockers):
            raise Error(
                f"{value['status']} return requires a code of its own: " + ", ".join(family)
            )
    if value["status"] == "oversized" and not rem:
        raise Error("oversized return requires unstarted_remainder")
    return value


def bounded_return_schema(registered: bool = False) -> JsonObject:
    """Return structural output guidance; valid_return owns semantic checks."""
    evidence = {
        "evidence_path": {"type": "string", "minLength": 1, "maxLength": MAX_PATH},
        "sha256": {"type": "string", "pattern": SHA.pattern},
    }
    schema: JsonObject = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
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
        ],
        "properties": {
            "schema": {"const": "bounded-step-return-v1"},
            "step_id": {"type": "string", "pattern": ID.pattern},
            "attempt_id": {"type": "string", "format": "uuid"},
            "agent_id": {"type": "string", "minLength": 1, "maxLength": 128},
            "status": {"type": "string", "enum": sorted(RETURN_STATUSES)},
            "changed_paths": {
                "type": "array",
                "maxItems": MAX_CHANGED_PATHS,
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1, "maxLength": MAX_PATH},
            },
            "acceptance": {
                "type": "object",
                "additionalProperties": False,
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
                "type": "array",
                "maxItems": MAX_BLOCKERS,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
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
                "type": "array",
                "maxItems": MAX_NOTES,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["type", "message"],
                    "properties": {
                        "type": {"type": "string", "enum": sorted(NOTE_TYPES)},
                        "message": {"type": "string", "maxLength": MAX_NOTE_MESSAGE},
                    },
                },
            },
            "unstarted_remainder": {
                "type": "array",
                "maxItems": MAX_REMAINDER,
                "items": {"type": "string", "minLength": 1, "maxLength": MAX_REMAINDER_ITEM},
            },
            "commit_hash": {"type": "string", "pattern": COMMIT.pattern[:-1] + "?$"},
        },
    }
    if registered:
        codes = sorted(set().union(*RETURN_CODES.values()) - VERIFIER_ONLY_CODES)
        schema["properties"]["blockers"]["items"]["properties"]["code"]["enum"] = codes
    return schema


def worker_handoff_digest(value: JsonObject) -> str:
    return digest(
        {
            key: item
            for key, item in value.items()
            if key != "handoff_sha256" and key not in DISPATCH_ENTRY_FIELDS
        }
    )


def worker_handoff_context(plan: JsonValue) -> JsonObject:
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
        or any(
            not isinstance(item, str) or not 1 <= len(item) <= 240
            for item in context["approved_decisions"]
        )
    ):
        raise Error("invalid worker handoff plan context")
    return context


def valid_worker_handoff(value: JsonValue) -> JsonObject:
    if not isinstance(value, dict) or len(canon(value)) > MAX_WORKER_HANDOFF:
        raise Error("planning-worker-handoff-v1 exceeds 32 KiB")
    if (
        set(value) - {"amendments", "changeset_budget", "precision", *DISPATCH_ENTRY_FIELDS}
        != WORKER_HANDOFF_FIELDS
        or value.get("schema") != "planning-worker-handoff-v1"
        or value.get("contract_version") != FORWARD_SCHEMA
    ):
        raise Error("invalid planning-worker-handoff-v1 schema")
    if not isinstance(value.get("handoff_sha256"), str) or not SHA.fullmatch(
        value["handoff_sha256"]
    ):
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
        not isinstance(leaf, dict)
        or leaf.get("id") != sid
        or not isinstance(unit, dict)
        or unit.get("id") != leaf.get("work_unit_id")
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
    current = {
        "agent_id": value["agent_id"],
        "harness": value.get("host"),
        "model_or_alias": value.get("executor"),
    }
    if not valid_stored_binding(
        value.get("capability_binding"), value["plan_sha256"], sid, leaf, current
    ):
        raise Error("invalid worker handoff capability binding")
    if "precision" in value and value["precision"] not in set(PRECISION_POLICIES.values()):
        raise Error("invalid worker handoff precision")
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
    if (
        not isinstance(amendments, list)
        or len(amendments) > MAX_AMENDMENTS
        or ("amendments" in value and not amendments)
    ):
        raise Error("invalid worker handoff amendments")
    remediation = value.get("retry_remediation")
    if remediation is not None:
        valid_remediation(remediation)
        if (
            remediation["step_id"] != sid
            or remediation["next_agent_id"] != value["agent_id"]
            or remediation["next_harness"] != value["host"]
            or remediation["target_portable_tier"] != value["portable_tier"]
        ):
            raise Error("invalid worker handoff retry remediation")
    if value.get("return_schema") not in (bounded_return_schema(), bounded_return_schema(True)):
        raise Error("invalid worker handoff return schema")
    return value


def validate_return(args: argparse.Namespace) -> JsonObject:
    try:
        handoff_raw = read_bounded_input(
            args.handoff_file, MAX_WORKER_HANDOFF_RAW, "worker handoff"
        )
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
        return_value,
        {},
        step,
        handoff_value["leaf"],
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


def read_bounded_input(path: str, maximum: int, label: str) -> bytes:
    """Read at most one byte beyond a fixed input bound before JSON parsing."""
    return read_bounded_bytes(path, maximum, f"cannot read {label}", f"{label} exceeds byte limit")


def next_after_return(
    args: argparse.Namespace,
    directory: Path,
    data: JsonObject,
    batches: Batches,
    sid: str,
    step: JsonObject,
    value: JsonObject,
    disposition: str,
    plan: JsonObject,
) -> JsonObject:
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
        block["command"] = land_command(data, sid)
    return bounded_next(block, droppable=("command",), trimmable="outside_paths")


def amend(args: argparse.Namespace) -> JsonObject:
    """Parent-only execution-metadata amendment; plan.json and plan_hash never change."""
    directory, data, plan, leafs = mutating_run(args)
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
    amendment: JsonObject = {"reason": reason}
    for key, field in (("add_write", "write_set"), ("add_read", "read_set")):
        paths = list(dict.fromkeys(requested[key]))
        if len(paths) > MAX_AMENDMENT_PATHS:
            raise Error("amendment exceeds 8 paths per list")
        amendment[key] = [
            rel(path, "amendment path") for path in paths if path not in current[field]
        ]
    if (
        args.acceptance_command is not None
        and args.acceptance_command != current["acceptance_command"]
    ):
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
    valid_amendments({"amendments": amendments}, approved)
    candidate = {**leafs, sid: effective_leaf(current, [amendment])}
    admitted = contract.plan_validator()(
        {**plan, "leaves": [candidate[leaf["id"]] for leaf in plan["leaves"]]},
        capability_binding=None,
        admission=True,
    )
    if not admitted.get("valid") or not admitted.get("approval_ready"):
        raise Error(
            "amended plan is not approval-ready: " + "; ".join(admitted.get("errors", []))[:200]
        )
    step["amendments"] = amendments
    if "max_attempts" in amendment:
        step["max_attempts"] = amendment["max_attempts"]
    event(
        directory,
        data,
        "amend-v5",
        step_id=sid,
        amendment_sha256=digest(amendment),
        amendment_count=len(amendments),
    )
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
    return step_result(
        "amend-v5",
        args,
        sid,
        step,
        amendment_count=len(amendments),
        amendment_sha256=digest(amendment),
        next=following,
    )


def return_fingerprint(value: JsonObject) -> str:
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


def settle_return(data: JsonObject, step: JsonObject, value: JsonObject, fingerprint: str) -> str:
    """Apply the retry policy to a stored return and name the branch that fired."""
    previous = step["fingerprints"][-1] if step["fingerprints"] else ""
    retry = retry_class(data, step, value)
    step["fingerprints"].append(fingerprint)
    step["fingerprints"] = step["fingerprints"][-5:]
    # `disposition` names the branch that actually fired, so a `next` block
    # reports this decision instead of modelling the precedence a second time.
    disposition: str
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
    elif not retry[0]:
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
    elif needs_higher_tier(step, *retry) and step["current_tier"] == PORTABLE_TIERS[-1]:
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


def record(args: argparse.Namespace) -> JsonObject:
    directory, data, plan, leafs = mutating_run(args)
    raw = Path(args.return_file).read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid step return JSON") from exc
    sid: JsonValue = value.get("step_id") if isinstance(value, dict) else ""
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
    result = step_result("record-return", args, sid, step, progress_fingerprint=fingerprint)
    if "scope_notes_count" in step:
        result["scope_notes_count"] = step["scope_notes_count"]
    result["next"] = next_after_return(
        args, directory, data, step_batches(plan), sid, step, value, disposition, plan
    )
    return result
