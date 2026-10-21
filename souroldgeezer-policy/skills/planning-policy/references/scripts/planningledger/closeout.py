"""Planning ledger closeout: init, land, close, reopen and validate."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path

from . import contract, core, gitops
from .checkpoint import (
    active_run,
    load_run,
    mutating_run,
    require_no_retained_pipeline,
    retired_contract,
    validate_events,
)
from .contract import (
    assignments,
    binding_for_step,
    capability_bindings,
    checked_assignments,
    checked_binding,
    derived_setup,
    leaves_by_id,
    read_plan,
)
from .core import (
    Error,
    UsageError,
    approved_parent,
    bounded_reason,
    canon,
    digest,
    ident,
    parent,
    proxy_tokens,
    retained_until,
    selected_step,
    timestamp,
)
from .dispatch import apply_worktree_result, next_after_transition, require_verified
from .gitops import helper_error, primary_checkout, repository_top
from .retention import collect_ledgers, scan_ledgers
from .schedule import (
    batch_settled,
    bounded_action_next,
    bounded_next,
    checkpoint_next,
    dependencies_clean,
    dispatch_command,
    land_command,
    ordered_steps,
    ready_candidate,
    ready_status_legal,
    retry_command,
    retryable_steps,
    series_closeout_overlay,
    series_non_final,
    step_batches,
)
from .series import series_close_handoff, series_predecessor_disclosure
from .store import event, initial_event, plan_dir, root, write
from .vocabulary import (
    CLOSEOUT_FIELDS,
    COMMIT,
    ESCALATING_RETRY_POLICY,
    FORWARD_SCHEMA,
    MAX_CHECK_OUTSIDE,
    MAX_CHECKPOINT,
    MAX_NEXT_ONLY_TOKENS,
    MAX_SERIES_HANDOFF,
    MAX_TOKENS,
    REGISTERED_RETURN_CODES,
)

__all__ = [
    "refuse_unowned_pins",
    "init5",
    "land",
    "close_run",
    "reopen_run",
    "summary",
    "bounded_step_summary",
    "show",
    "validate",
]


def refuse_unowned_pins(args, plan):
    """A strict plan must prove no unowned pinning test exists before the run starts."""
    if plan.get("precision") != "strict":
        return
    if not args.pin_roots:
        raise UsageError("a strict plan requires --pin-roots")
    scan = contract.plan_validator()(plan, pin_roots=args.pin_roots, repo_root=repository_top(args))
    pins = [item for item in scan.get("errors", []) if item.startswith("PLANSCOPE-UNOWNED-PIN")]
    if pins:
        raise Error("; ".join(pins[:MAX_CHECK_OUTSIDE])[:480])


def init5(args):
    approved_parent(args)
    plan = read_plan(args.plan_file)
    refuse_unowned_pins(args, plan)
    supplied = (args.assignments_file, args.capability_binding_file)
    if args.host and any(supplied):
        raise UsageError("--host derives the assignments and binding; pass neither file")
    if not args.host and not all(supplied):
        raise UsageError(
            "pass --assignments-file and --capability-binding-file, or --host with --evidence"
        )
    if args.host:
        derived, derived_binding = derived_setup(plan, args.host, args.evidence)
        assigned = checked_assignments(derived, plan)
    else:
        assigned = assignments(args.assignments_file, plan)
    # Resolve a relative worktree once, so every later command and every
    # artifact comparison sees one absolute path whatever its cwd.
    # Git is asked for the checkout only when a worktree is relative.
    anchor = Path()
    if not all(Path(item["worktree"]).is_absolute() for item in assigned.values()):
        top = repository_top(args)
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
    if retired_contract(directory, plan_level=True)[0]:
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
        "verify_policy": "closeout_only"
        if plan.get("verification") == "closeout-only"
        else "leaf_verify_v1",
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


def land(args):
    """Integrate and clean a completed leaf, or a settled batch, through the helper."""
    directory, data, plan, leafs = mutating_run(args)
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
    base = (
        "--repo-root",
        str(repo),
        "--target",
        args.target,
        "--branch",
        leaf["worktree_owner"],
        "--worktree",
        worktree,
    )
    landed = [member for member in group if data["steps"][member]["status"] == "completed"]
    for member in landed:
        require_verified(data, member, data["steps"][member])
    if landed:
        commits = {member: data["steps"][member]["returned_commit"] for member in landed}
        if not all(COMMIT.fullmatch(commit) for commit in commits.values()):
            raise Error("completed step has no returned commit to integrate")
        extra = (
            [f"--batch-commit={member}={commits[member]}" for member in landed]
            if len(group) > 1
            else []
        )
        value, ok = gitops.run_worktree_helper(
            "integrate", *base, "--source-commit", commits[landed[-1]], *extra
        )
        if not ok:
            raise Error(f"integrate failed: {helper_error(value)}")
        with tempfile.TemporaryDirectory() as scratch:
            artifact = Path(scratch) / "integrate.json"
            artifact.write_text(json.dumps(value))
            # Validate every member before persisting any, so a bad artifact leaves the ledger
            # unchanged.
            for member in landed:
                apply_worktree_result(
                    str(artifact),
                    directory,
                    member,
                    data["steps"][member],
                    leafs[member],
                    "integrated",
                    batches,
                    args.summary,
                )
        for member in landed:
            event(
                directory,
                data,
                f"transition-v{data['schema']}",
                step_id=member,
                from_status="completed",
                to_status="integrated",
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
        value, ok = gitops.run_worktree_helper(
            "cleanup", *base, "--integrated-result", str(recorded)
        )
        if ok:
            with tempfile.TemporaryDirectory() as scratch:
                artifact = Path(scratch) / "cleanup.json"
                artifact.write_text(json.dumps(value))
                for member in cleanable:
                    apply_worktree_result(
                        str(artifact),
                        directory,
                        member,
                        data["steps"][member],
                        leafs[member],
                        "cleaned",
                        batches,
                        args.summary,
                    )
            for member in cleanable:
                event(
                    directory,
                    data,
                    f"transition-v{data['schema']}",
                    step_id=member,
                    from_status="integrated",
                    to_status="cleaned",
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


def close_run(args):
    parent(args.actor)
    directory, data, plan, leafs = load_run(args)
    validate_events(directory, data)
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


def reopen_run(args):
    parent(args.actor)
    directory, data, plan, leafs = load_run(args)
    validate_events(directory, data)
    if data["run_status"] != "closed" or data["outcome"] != "blocked":
        raise Error("only a retained blocked run may reopen")
    require_no_retained_pipeline(data)
    if timestamp(core.now()) >= timestamp(data["purge_after"], "purge_after"):
        raise Error("blocked run is no longer retained")
    batches = step_batches(plan)
    pending = [
        step
        for step in ordered_steps(data["steps"])
        if step["status"] == "pending" and ready_candidate(data, step, batches)
    ]
    retryable = pending + [s for s, _outcome, _kind in retryable_steps(directory, data, batches)]
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
    ids = result["retryable_steps"]
    first = data["steps"][ids[0]]
    command = (
        dispatch_command(data["plan_id"], data["run_id"], first["id"])
        if first["status"] == "pending"
        else retry_command(data["plan_id"], data["run_id"], first["id"])
    )
    result["next"] = bounded_action_next(
        {"retryable_step_ids": ids, "command": command},
        "retryable_step_ids",
    )
    return result


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
            "current_tier": s["current_tier"],
            "current_assignment": s["current_assignment"],
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
        "retry_policy": data["retry_policy"],
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
    if args.next_only and args.step_id:
        raise Error("show --next-only does not accept --step-id")
    directory, data, plan, leafs = load_run(args)
    if args.next_only:
        validate_events(directory, data)
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
            "retry_policy": data["retry_policy"],
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
                "current_tier": step["current_tier"],
                "same_tier_retry_used": step["same_tier_retry_used"],
                "current_assignment": step["current_assignment"],
                "retry_remediation_path": step["retry_remediation_path"],
                "retry_remediation_sha256": step["retry_remediation_sha256"],
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


def validate(args):
    directory, data, plan, leafs = load_run(args)
    if args.closeout:
        unfinished = [
            step["id"]
            for step in data["steps"].values()
            if step["status"] in {"completed", "integrated"}
        ]
        if unfinished:
            raise Error("closeout requires every successful step to be cleaned")
    validate_events(directory, data)
    result = {
        "ok": True,
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "plan_hash": data["plan_hash"],
        "retry_policy": data["retry_policy"],
        "run_status": data["run_status"],
        "outcome": data["outcome"],
        "closed_at": data["closed_at"],
        "purge_after": data["purge_after"],
        "errors": [],
        "closeout": bool(args.closeout),
    }
    if (
        args.closeout
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
        result["next"] = bounded_action_next(series_closeout_overlay(plan, {"command": command}))
    return result
