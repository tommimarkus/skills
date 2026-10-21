#!/usr/bin/env python3
"""Parent-owned checkpoint ledger with byte-compatible legacy commands."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from planningledger import contract, core, gitops
from planningledger.vocabulary import *  # noqa: F403
from planningledger.core import *  # noqa: F403
from planningledger.store import *  # noqa: F403
from planningledger.gitops import *  # noqa: F403
from planningledger.contract import *  # noqa: F403
from planningledger.checkpoint import *  # noqa: F403
from planningledger.legacy import *  # noqa: F403
from planningledger.schedule import *  # noqa: F403
from planningledger.series import *  # noqa: F403
from planningledger.returns import *  # noqa: F403


def init1(args):
    approved_parent(args)
    directory = plan_dir(args)
    if directory.exists():
        raise Error("ledger already exists; init is not an overwrite operation")
    steps = parse_v1(args.steps_json)
    collect_ledgers(root(args), None, timestamp(core.now()), remove=True)
    created_at = core.now()
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

def refuse_unowned_pins(args, plan, top):
    """A strict plan must prove no unowned pinning test exists before the run starts."""
    if plan.get("precision") != "strict":
        return
    if not args.pin_roots:
        raise UsageError("a strict plan requires --pin-roots")
    scan = contract.plan_validator()(plan, pin_roots=args.pin_roots, repo_root=top)
    pins = [item for item in scan.get("errors", []) if item.startswith("PLANSCOPE-UNOWNED-PIN")]
    if pins:
        raise Error("; ".join(pins[:MAX_CHECK_OUTSIDE])[:480])

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
    anchor = primary_checkout(top) if args.host else top
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
    collect_ledgers(ledger_root, None, timestamp(core.now()), remove=True)
    series = plan.get("series")
    series_predecessor = (
        series_predecessor_disclosure(ledger_root, series)
        if series and series.get("slice", 1) > 1
        else None
    )
    directory = plan_dir(args)
    existing, invalid = scan_ledgers(ledger_root, args.plan_id, timestamp(core.now()))
    if invalid:
        raise Error("target plan ledger directory is invalid")
    if any(entry["legacy"] for entry in existing):
        raise Error("cannot add a v5 run inside a legacy ledger directory")
    run_id = str(uuid.uuid4())
    run = directory / run_id
    if run.exists():
        raise Error("generated run already exists")
    leaves = leaves_by_id(plan)
    created_at = core.now()
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

def require_verified(data, sid, step):
    if data.get("verify_policy") == "leaf_verify_v1" and not commit_verified(step):
        raise Error(
            f"step {sid} has no pass or inconclusive verification for its returned commit; "
            "run check-changeset, verify-handoff and record-verify first"
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
        value, ok = gitops.run_worktree_helper(
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
        value, ok = gitops.run_worktree_helper("cleanup", *base, "--integrated-result", str(recorded))
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
    require_no_retained_pipeline(data)
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
    closed_at = core.now()
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
    gc_result = collect_ledgers(root(args), None, timestamp(core.now()), remove=True)
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
    require_no_retained_pipeline(data)
    if timestamp(core.now()) >= timestamp(data["purge_after"], "purge_after"):
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
    if changeset_base is not None:
        value["changeset_budget"] = {
            **validator_module().changeset_budget(leaf), "base_commit": changeset_base,
        }
    value["handoff_sha256"] = worker_handoff_digest(value)
    if len(canon(value)) > MAX_WORKER_HANDOFF:
        raise Error("planning-worker-handoff-v1 exceeds 32 KiB")
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
    for member in group:
        step = data["steps"][member]
        old = step["status"]
        ready(args, directory, data, plan, batches, step)
        moves.append((member, old, step["attempt_id"]))
        advance(step, "ready", "ready", "in_progress", args.summary or "in progress")
    repo = repository_top(args)
    for member in group:
        verify_worktree_identity(repo, data["steps"][member], leafs[member], args.create_from)
    if data.get("verify_policy") == "leaf_verify_v1":
        # The first member measures from the worktree HEAD at its first start; a
        # batch follower's base is the previous member's returned commit, which
        # does not exist yet, so it stays empty until the gate resolves it.
        step = data["steps"][group[0]]
        if "base_commit" not in step:
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
    members = unverified_members(data, step_batches(plan), sid)
    if not members:
        raise Error("every completed member already has a verdict for its returned commit")
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
        event(directory, data, "record-changeset", step_id=sid)
        return result2("record-changeset", args, sid, step, changeset=verdict)
    if verdict["verdict"] != "oversized:changeset":
        raise Error(f"the measured changeset verdict for {sid} is {verdict['verdict']}; nothing to record")
    summary = (
        f"{verdict['lines']} changed lines in {verdict['files']} files exceed "
        f"{verdict['limits']['max_changed_lines']} lines / {verdict['limits']['max_files']} files"
    )
    stop_step(step, "oversized", "oversized:changeset", "oversized:changeset", summary)
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
    if bool(args.run_id) == bool(args.legacy):
        raise Error("purge requires exactly one of --run-id or --legacy")
    if args.before_retention:
        bounded_reason(args.reason, "--before-retention", required=True)
    else:
        bounded_reason(args.reason, "purge")
    target_run = "" if args.legacy else uuid4(args.run_id)
    entries, invalid = scan_ledgers(root(args), plan_id, timestamp(core.now()))
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
        {"schema": "planning-usage-trace-v1", "initialized_at": core.now(), "closed_at": ""},
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
    forecast = contract.plan_validator()(plan)["cost_advisory"]
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
    metadata["closed_at"] = core.now()
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
