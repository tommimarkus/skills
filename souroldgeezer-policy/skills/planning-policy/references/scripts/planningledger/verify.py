"""Planning ledger verify: changeset gate, verify handoff and record-verify."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from . import contract
from .checkpoint import load_run, mutating_run, validate_events
from .contract import standard_precision, validator_module
from .core import (
    Error,
    JsonObject,
    JsonValue,
    UsageError,
    canon,
    digest,
    ident,
    read_json,
    selected_step,
    uuid4,
)
from .gitops import dirty_paths, git_head, git_output, numstat_rows, repository_top
from .returns import (
    next_after_return,
    read_bounded_input,
    return_fingerprint,
    settle_return,
    step_result,
    stop_step,
    valid_worker_handoff,
)
from .schedule import (
    Batches,
    bounded_next,
    checkpoint_next,
    current_return,
    group_landable,
    land_command,
    step_batches,
    stored_verdict,
)
from .store import event, write
from .vocabulary import (
    MAX_BLOCKER_SUMMARY,
    MAX_CHECK_OUTSIDE,
    MAX_PATH,
    MAX_RETURN,
    MAX_VERIFY_HANDOFF,
    MAX_VERIFY_RETURN,
    MAX_WORKER_HANDOFF_RAW,
    SCOPE_REJECTION_REASON,
    VERIFIER_AGENTS,
    VERIFY_CODES,
    VERIFY_FINDING_FIELDS,
    VERIFY_HANDOFF_FIELDS,
    VERIFY_HANDOFF_OPTIONAL,
    VERIFY_PASSING,
    VERIFY_VERDICTS,
)

__all__ = [
    "unverified_members",
    "changeset_verdict",
    "returned_changeset",
    "check_changeset",
    "bounded_verify_return_schema",
    "valid_verify_return",
    "verify_handoff_digest",
    "valid_verify_handoff",
    "prior_verify",
    "verify_handoff_packet",
    "verify_handoff",
    "record_changeset",
    "validate_verify_return",
    "verify_rejection_return",
    "reject_verified_step",
    "record_verify",
]


def unverified_members(data: JsonObject, batches: Batches, sid: str) -> list[str]:
    """Completed members of the step's batch with no verdict yet for their returned commit."""
    steps = data["steps"]
    return [
        member
        for member in (batches.get(sid) or (sid,))
        if steps[member]["status"] == "completed" and stored_verdict(steps[member]) is None
    ]


def changeset_verdict(
    worktree: str,
    base: str,
    commit: str,
    leaf: JsonObject,
    budget: JsonObject,
    standard: bool = False,
) -> JsonObject:
    exempt = budget["exempt_paths"]
    covers = validator_module().write_set_covers
    lines = files = 0
    outside: list[str] = []
    for paths, changed in numstat_rows(worktree, base, commit):
        if all(covers(exempt, path) for path in paths):
            continue
        lines += changed
        files += 1
        outside.extend(
            path
            for path in paths
            if path not in outside and not contract.changed_path_allowed(path, leaf["write_set"])
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


def returned_changeset(
    data: JsonObject, plan: JsonObject, leafs: dict[str, JsonObject], sid: str
) -> tuple[JsonObject, str, str, JsonObject]:
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
        step["assignment"]["worktree"],
        base,
        commit,
        leafs[sid],
        budget,
        standard=standard_precision(data),
    )
    return verdict, base, commit, budget


def check_changeset(args: argparse.Namespace) -> JsonObject:
    """Read-only changeset gate: builder preflight on HEAD, or the parent on a returned commit."""
    if args.handoff_file:
        if not args.worktree:
            raise UsageError("--handoff-file requires --worktree")
        packet = valid_worker_handoff(
            json.loads(
                read_bounded_input(args.handoff_file, MAX_WORKER_HANDOFF_RAW, "worker handoff")
            )
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
        directory, data, plan, leafs = load_run(args)
        validate_events(directory, data)
        sid, _step = selected_step(data, args.step_id)
        return returned_changeset(data, plan, leafs, sid)[0]
    else:
        raise UsageError("pass --handoff-file with --worktree, or --run-id with --step-id")
    return changeset_verdict(
        worktree, base, commit, leaf, budget, standard=packet.get("precision") == "standard"
    )


def bounded_verify_return_schema() -> JsonObject:
    finding = {
        "type": "object",
        "additionalProperties": False,
        "required": sorted(VERIFY_FINDING_FIELDS),
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
        "type": "object",
        "additionalProperties": False,
        "required": ["schema", "step_id", "verify_id", "verdict", "findings", "notes"],
        "properties": {
            "schema": {"const": "bounded-verify-return-v1"},
            "step_id": {"type": "string"},
            "verify_id": {"type": "string", "format": "uuid"},
            "verdict": {"enum": sorted(VERIFY_VERDICTS)},
            "findings": {"type": "array", "maxItems": 8, "items": finding},
            "notes": {
                "type": "array",
                "maxItems": 8,
                "items": {"type": "string", "maxLength": MAX_BLOCKER_SUMMARY},
            },
        },
    }


def valid_verify_return(value: JsonValue) -> JsonObject:
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
    if (
        not isinstance(notes, list)
        or len(notes) > 8
        or any(not isinstance(note, str) or len(note) > MAX_BLOCKER_SUMMARY for note in notes)
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
            or not (
                line is None or (isinstance(line, int) and not isinstance(line, bool) and line >= 1)
            )
        ):
            raise Error("invalid verify finding")
    if (value["verdict"] == "reject") != bool(findings) and value["verdict"] != "inconclusive":
        raise Error("a reject carries a finding and a pass carries none")
    return value


def verify_handoff_digest(value: JsonObject) -> str:
    return digest({key: item for key, item in value.items() if key != "packet_sha256"})


def valid_verify_handoff(value: JsonValue) -> JsonObject:
    if not isinstance(value, dict) or len(canon(value)) > MAX_VERIFY_HANDOFF:
        raise Error("planning-verify-handoff-v1 exceeds 16 KiB")
    keys = set(value) - VERIFY_HANDOFF_OPTIONAL
    schema = value.get("schema") == "planning-verify-handoff-v1"
    if schema and keys == VERIFY_HANDOFF_FIELDS - {"approved_decisions"}:
        # Issued by a ledger before packets carried the plan's decisions.
        raise Error("verify handoff predates approved_decisions; re-run verify-handoff")
    if keys != VERIFY_HANDOFF_FIELDS or not schema:
        raise Error("invalid planning-verify-handoff-v1 schema")
    if not isinstance(value["packet_sha256"], str) or value[
        "packet_sha256"
    ] != verify_handoff_digest(value):
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


def prior_verify(directory: Path, step: JsonObject) -> JsonObject | None:
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


def verify_handoff_packet(
    directory: Path,
    data: JsonObject,
    plan: JsonObject,
    leafs: dict[str, JsonObject],
    sid: str,
    step: JsonObject,
    verify_id: str,
) -> JsonObject:
    """Build one planning-verify-handoff-v1 packet for a completed step, without mutating."""
    verdict, base, commit, budget = returned_changeset(data, plan, leafs, sid)
    if not verdict["ok"]:
        raise Error(
            f"check-changeset verdict for {sid} is {verdict['verdict']}; verification refused"
        )
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
        "approved_decisions": plan["approved_decisions"],
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


def verify_handoff(args: argparse.Namespace) -> JsonObject:
    """Issue verifier packets for a completed step, or every completed member of its batch."""
    directory, data, plan, leafs = mutating_run(args)
    if data.get("verify_policy") != "leaf_verify_v1":
        raise Error("this run does not use leaf verification")
    sid, step = selected_step(data, args.step_id)
    if step["status"] != "completed":
        raise Error("only a completed step can be verified")
    members = unverified_members(data, step_batches(plan), sid)
    if not members:
        raise Error("every completed member already has a verdict for its returned commit")
    packets = []
    for member in members:
        packets.append(
            verify_handoff_packet(
                directory, data, plan, leafs, member, data["steps"][member], str(uuid.uuid4())
            )
        )
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


def record_changeset(args: argparse.Namespace) -> JsonObject:
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
        stop_step(
            step,
            "oversized",
            SCOPE_REJECTION_REASON,
            "scope_expanded",
            "changed path outside write_set",
        )
        event(directory, data, "record-changeset", step_id=sid)
        return step_result("record-changeset", args, sid, step, changeset=verdict)
    if verdict["verdict"] != "oversized:changeset":
        raise Error(
            f"the measured changeset verdict for {sid} is {verdict['verdict']}; nothing to record"
        )
    summary = (
        f"{verdict['lines']} changed lines in {verdict['files']} files exceed "
        f"{verdict['limits']['max_changed_lines']} lines / {verdict['limits']['max_files']} files"
    )
    stop_step(step, "oversized", "oversized:changeset", "oversized:changeset", summary)
    event(directory, data, "record-changeset", step_id=sid)
    return step_result("record-changeset", args, sid, step, changeset=verdict)


def validate_verify_return(args: argparse.Namespace) -> JsonObject:
    try:
        packet = json.loads(
            read_bounded_input(args.handoff_file, MAX_VERIFY_HANDOFF + 1024, "verify handoff")
        )
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


def verify_rejection_return(directory: Path, step: JsonObject, verify: JsonObject) -> JsonObject:
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
        "blockers": [
            {
                "code": "failed:verification",
                "summary": f"verifier rejected the build: {codes}"[:MAX_BLOCKER_SUMMARY],
                "evidence_path": stored["path"],
                "sha256": stored["sha256"],
            }
        ],
        "notes": [
            {
                "type": "finding",
                "message": "the builder's completed return was superseded by a verifier reject",
            }
        ],
        "unstarted_remainder": [],
        "commit_hash": step["returned_commit"],
    }


def reject_verified_step(
    directory: Path, data: JsonObject, step: JsonObject, failure: JsonObject
) -> str:
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
    bare = dict(
        failure, blockers=[{key: failure["blockers"][0][key] for key in ("code", "summary")}]
    )
    return settle_return(data, step, failure, return_fingerprint(bare))


def record_verify(args: argparse.Namespace) -> JsonObject:
    """Store a verifier verdict bound to the step's returned commit."""
    directory, data, plan, leafs = mutating_run(args)
    raw = read_bounded_input(args.return_file, MAX_VERIFY_RETURN, "verify return")
    try:
        value = valid_verify_return(json.loads(raw))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid verify return JSON") from exc
    sid = value["step_id"]
    step = data["steps"].get(sid)
    if (
        data.get("verify_policy") != "leaf_verify_v1"
        or step is None
        or step["status"] != "completed"
    ):
        raise Error("verify return is not for a completed step of a leaf-verification run")
    if not step.get("verify_id") or step["verify_id"] != value["verify_id"]:
        raise Error("stale or foreign verify_id")
    if step.get("verify_commit") != step["returned_commit"]:
        raise Error("the step's returned commit changed since verify-handoff")
    batches = step_batches(plan)
    group = batches.get(sid) or (sid,)
    # A batch shares one worktree, so its HEAD is the tip: the last completed member's commit.
    tip = data["steps"][[m for m in group if data["steps"][m]["status"] == "completed"][-1]][
        "returned_commit"
    ]
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
    failure: JsonObject | None = None
    disposition = ""
    if value["verdict"] == "reject":
        failure = verify_rejection_return(directory, step, value)
        disposition = reject_verified_step(directory, data, step, failure)
    event(directory, data, "record-verify", step_id=sid, verdict=value["verdict"])
    result = step_result("record-verify", args, sid, step, verdict=value["verdict"])
    if failure is not None:
        result["next"] = next_after_return(
            args, directory, data, batches, sid, step, failure, disposition, plan
        )
    elif value["verdict"] in VERIFY_PASSING:
        if group_landable(data, batches, sid) and not unverified_members(data, batches, sid):
            result["next"] = bounded_next({"command": land_command(data, sid)})
        else:
            result["next"] = checkpoint_next(directory, data, batches, plan)
    return result
