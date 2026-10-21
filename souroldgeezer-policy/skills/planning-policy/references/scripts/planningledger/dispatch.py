"""Planning ledger dispatch: worker handoff packets, dispatch and transitions."""

from __future__ import annotations

import json
from pathlib import Path

from .vocabulary import (
    AMENDMENT_OPTIONAL,
    BATCH_STOPPED_STATES,
    COMMIT,
    ESCALATING_RETRY_POLICY,
    FORWARD_SCHEMA,
    MAX_WORKER_HANDOFF,
    MAX_WORKER_PROMPT,
    PORTABLE_TIERS,
    PRECISION_POLICIES,
    REGISTERED_RETURN_CODES,
    SHA40,
    WORKTREE_RESULT_FIELDS,
    WORKTREE_RESULT_OPTIONAL,
)
from .core import Error, LEDGER_SCRIPT, canon, digest, ident, read_json, rel, selected_step, uuid4
from .store import event, write
from .gitops import git_head, repository_top, verify_worktree_identity
from .contract import (
    effective_leaf,
    leaves_by_id,
    valid_amendments,
    valid_stored_binding,
    validator_module,
)
from .checkpoint import active_run, load_run, mutating_run, valid_remediation, validate_events
from .schedule import (
    bounded_action_next,
    checkpoint_next,
    commit_verified,
    dispatch_command,
    land_command,
    ordered_steps,
    ready,
    ready_candidate,
    series_closeout_overlay,
    step_batches,
    transition_scope,
)
from .returns import (
    advance,
    bounded_return_schema,
    step_result,
    worker_handoff_context,
    worker_handoff_digest,
)

__all__ = [
    "next_after_transition",
    "unwind",
    "require_verified",
    "apply_worktree_result",
    "transition_step",
    "batch_source_commits",
    "worktree_result",
    "worker_prompt",
    "store_dispatch_packet",
    "build_worker_handoff",
    "step_handoff",
    "handoff",
    "dispatch",
]


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
        value = {"command": land_command(data, sid)}
        unblocked = [
            candidate["id"]
            for candidate in ordered_steps(data["steps"])
            if candidate["status"] == "pending"
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
                "command": dispatch_command(args.plan_id, args.run_id, newly_unblocked[0]),
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


def transition_step(args):
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
        raise Error("transition permits pending, ready, in_progress, integrated, or cleaned")
    event(
        directory,
        data,
        f"transition-v{data['schema']}",
        step_id=sid,
        from_status=old,
        to_status=step["status"],
        attempt_id=step["attempt_id"],
    )
    result = step_result("transition", args, sid, step, attempt_id=step["attempt_id"])
    if data.get("retry_policy") == ESCALATING_RETRY_POLICY:
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


def worker_prompt(packet, packet_path, member=None):
    """Host-neutral worker prompt built only from packet facts.

    member is (position, count, batch) for a batch group, else None.
    """
    script = LEDGER_SCRIPT
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
        leaf = effective_leaf(leaf, valid_amendments(step, leaf))
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
    directory, data, plan, _leafs = load_run(args)
    validate_events(directory, data)
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
