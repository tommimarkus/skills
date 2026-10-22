"""Planning ledger schedule: readiness, batches, retry selection and the live next block."""

from __future__ import annotations

import argparse
import uuid
from pathlib import Path
from typing import TypeAlias

from .checkpoint import retained_pipeline_steps, valid_remediation
from .contract import (
    binding_for_step,
    capability_bindings,
    host_entry,
    host_step_binding,
    tier_alias,
)
from .core import (
    Error,
    JsonObject,
    JsonValue,
    digest,
    next_tokens,
    read_bounded_json,
    read_json,
    rel,
)
from .store import write
from .vocabulary import (
    BATCH_ACTIVE_STATES,
    BATCH_DEPENDENCY_STATES,
    EXTERNAL_DEPENDENCY_STATES,
    MAX_CONCURRENT,
    MAX_NEXT_TOKENS,
    MAX_REMEDIATION,
    NON_ACTION_CATEGORIES,
    PORTABLE_TIERS,
    REASONING_STOPS,
    REPAIRABLE_CODES,
    RETURN_CODES,
    TERMINAL_RETRY_REASONS,
    VERIFY_PASSING,
)

__all__ = [
    "trim_collection",
    "bounded_next",
    "bounded_action_next",
    "ordered_steps",
    "transition_scope",
    "dispatch_command",
    "land_command",
    "verify_commands",
    "dependencies_clean",
    "attempt_available",
    "amended_after_return",
    "repair_reopened",
    "retry_open",
    "ready_status_legal",
    "ready_candidate",
    "attempt_return_recorded",
    "step_batches",
    "batch_settled",
    "read_remediation",
    "current_return",
    "primary_code",
    "retry_class",
    "store_remediation",
    "ready",
    "retryable_steps",
    "retry_command",
    "series_non_final",
    "series_final",
    "series_closeout_overlay",
    "startable_step_ids",
    "with_concurrent",
    "checkpoint_next",
    "verify_issued",
    "primary_next",
    "stored_verdict",
    "commit_verified",
    "group_landable",
]


# Each batched step id mapped to its batch's member ids, as step_batches derives them.
Batches: TypeAlias = dict[str, list[str]]


def trim_collection(value: JsonObject, trimmable: str) -> None:
    """Pop the trimmable collection's tail while the block is over budget, keeping one item."""
    while next_tokens(value) > MAX_NEXT_TOKENS and trimmable and len(value.get(trimmable, [])) > 1:
        value[trimmable].pop()
        value["truncated"] = True


def bounded_next(
    value: JsonObject, droppable: tuple[str, ...] = (), trimmable: str = ""
) -> JsonObject:
    """Bound a `next` block, shedding convenience before the state it reports.

    The pre-formatted CLI hint goes first and a listed collection is trimmed
    second, so the eligibility or status a caller acts on always survives.
    """
    for key in droppable:
        if next_tokens(value) <= MAX_NEXT_TOKENS:
            return value
        value.pop(key, None)
    trim_collection(value, trimmable)
    return value


def bounded_action_next(value: JsonObject, trimmable: str = "") -> JsonObject:
    """Keep the first legal command while trimming a convenience collection."""
    trim_collection(value, trimmable)
    if next_tokens(value) > MAX_NEXT_TOKENS and trimmable:
        value.pop(trimmable, None)
        value["truncated"] = True
    if next_tokens(value) > MAX_NEXT_TOKENS:
        raise Error("next block exceeds 120 proxy tokens")
    return value


def ordered_steps(steps: dict[str, JsonObject]) -> list[JsonObject]:
    return sorted(steps.values(), key=lambda value: value["id"])


def transition_scope(plan_id: str, run_id: str) -> str:
    return f"--plan-id {plan_id} transition --actor parent --run-id {run_id}"


def dispatch_command(plan_id: str, run_id: str, step_id: str) -> str:
    return (
        f"--plan-id {plan_id} dispatch --actor parent --run-id {run_id} "
        f"--step-id {step_id} --agent-id <agent-id>"
    )


def land_command(data: JsonObject, step_id: str) -> str:
    """Integrate and clean a step through the composite land."""
    return (
        f"--plan-id {data['plan_id']} land --actor parent --run-id {data['run_id']} "
        f"--step-id {step_id} --target <target-branch>"
    )


def verify_commands(data: JsonObject, step_id: str) -> dict[str, str]:
    """The leaf_verify_v1 gate: check-changeset first, then verify-handoff."""
    scope = f"--plan-id {data['plan_id']}"
    return {
        "command": f"{scope} check-changeset --run-id {data['run_id']} --step-id {step_id}",
        "then": (
            f"{scope} verify-handoff --actor parent --run-id {data['run_id']} --step-id {step_id}"
        ),
    }


def dependencies_clean(data: JsonObject, step: JsonObject, batches: Batches) -> bool:
    """Dependencies are satisfied; an external dependency unblocks at `integrated`."""
    members = batches.get(step["id"], ())
    return all(
        data["steps"][dep]["status"]
        in (BATCH_DEPENDENCY_STATES if dep in members else EXTERNAL_DEPENDENCY_STATES)
        for dep in step["dependencies"]
    )


def attempt_available(step: JsonObject) -> bool:
    return bool(step["attempt_count"] < step["max_attempts"])


def amended_after_return(step: JsonObject) -> bool:
    """True when an amendment was recorded after the current attempt's return."""
    return any(
        item["after_attempt_id"] == step["attempt_id"] and item["return_recorded"]
        for item in step.get("amendments", ())
    )


def repair_reopened(step: JsonObject) -> bool:
    """A non-terminal blocked/failed stop whose cause was amended after its return."""
    return (
        step["status"] in {"blocked", "failed"}
        and step["reason"] not in TERMINAL_RETRY_REASONS
        and attempt_return_recorded(step)
        and amended_after_return(step)
    )


def retry_open(step: JsonObject) -> bool:
    return step["retry_allowed"] or repair_reopened(step)


def ready_status_legal(step: JsonObject) -> bool:
    return step["status"] in {"pending", "blocked", "failed"} and retry_open(step)


def ready_candidate(data: JsonObject, step: JsonObject, batches: Batches) -> bool:
    return (
        ready_status_legal(step)
        and dependencies_clean(data, step, batches)
        and attempt_available(step)
    )


def attempt_return_recorded(step: JsonObject) -> bool:
    """True once the step's current attempt has a stored return."""
    return bool(step["attempt_id"]) and step["return_path"] == str(
        Path("returns") / step["id"] / f"{step['attempt_id']}.json"
    )


def step_batches(plan: JsonObject) -> Batches:
    """Derive each batched leaf's member list from the stored canonical plan."""
    groups: dict[str, list[str]] = {}
    for leaf in plan["leaves"]:
        if leaf.get("batch"):
            groups.setdefault(leaf["batch"], []).append(leaf["id"])
    return {sid: members for members in groups.values() for sid in members}


def batch_settled(data: JsonObject, batches: Batches, step_id: str) -> bool:
    """True once no member of the step's batch can still commit to its worktree."""
    return not any(
        data["steps"][member]["status"] in BATCH_ACTIVE_STATES
        or (
            data["steps"][member]["status"] in {"blocked", "failed"}
            and retry_open(data["steps"][member])
        )
        for member in batches.get(step_id, ())
    )


def read_remediation(path: str) -> JsonObject:
    value = read_bounded_json(
        path, MAX_REMEDIATION, "invalid retry-remediation-v1", "retry-remediation-v1 exceeds 4 KiB"
    )
    return valid_remediation(value)


def current_return(directory: Path, step: JsonObject) -> JsonValue:
    if not step.get("return_path") or not step.get("return_sha256"):
        raise Error("retry requires a current prior return")
    path = directory / rel(step["return_path"], "return path")
    value = read_json(path, "current prior return is missing")
    if digest(value) != step["return_sha256"]:
        raise Error("current prior return digest mismatch")
    return value


def primary_code(value: JsonObject) -> str:
    """The first blocker code that belongs to the return status's own family."""
    status: JsonValue = value.get("status")
    family = RETURN_CODES.get(status, ())
    for blocker in value.get("blockers") or ():
        code = blocker.get("code") if isinstance(blocker, dict) else None
        if isinstance(code, str) and code in family:
            return code
    return ""


def retry_class(data: JsonObject, step: JsonObject, value: JsonObject) -> tuple[str, str]:
    """The one retry-eligibility predicate: (kind, outcome), or ("", "").

    Reasoning stops (`failed:acceptance`, `failed:verification`,
    `blocked:needs_higher_tier`) keep the
    same-tier-then-escalate rules. Repairable stops (`blocked:environment`, or
    any other blocked/failed stop amended after its return) retry at the same
    tier.
    """
    status = value.get("status")
    code = primary_code(value)
    if (status, code) in REASONING_STOPS:
        return "reasoning", code
    if status in {"blocked", "failed"} and (code in REPAIRABLE_CODES or repair_reopened(step)):
        return "repairable", code or status
    return "", ""


def store_remediation(
    args: argparse.Namespace, data: JsonObject, directory: Path, step: JsonObject
) -> tuple[JsonObject, str, str, bool]:
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


def ready(
    args: argparse.Namespace,
    directory: Path,
    data: JsonObject,
    plan: JsonObject,
    batches: Batches,
    step: JsonObject,
) -> None:
    for value, label in ((args.harness, "harness"), (args.model_or_alias, "model_or_alias")):
        if value and (not isinstance(value, str) or not value.strip() or len(value) > 160):
            raise Error(f"invalid {label}")
    if step["status"] == "pending" and (
        not isinstance(args.agent_id, str) or not 1 <= len(args.agent_id) <= 128
    ):
        raise Error("ready requires bounded --agent-id")
    if not ready_status_legal(step):
        raise Error("step cannot be readied")
    retry_state = None
    if step["status"] != "pending":
        if not args.retry:
            raise Error("retry requires --retry")
        retry_state = store_remediation(args, data, directory, step)
    elif args.retry or args.retry_remediation_file:
        raise Error("initial ready transition is not a retry")
    if not dependencies_clean(data, step, batches):
        raise Error("dependencies are not integrated or cleaned")
    if not attempt_available(step):
        raise Error("blocked:retry_exhausted")
    if retry_state:
        remediation, path, remediation_sha, same_tier = retry_state
        current_assignment = {
            "agent_id": remediation["next_agent_id"],
            "harness": remediation["next_harness"],
            "model_or_alias": (
                tier_alias(args, data, remediation["target_portable_tier"])
                or step["current_assignment"]["model_or_alias"]
            ),
        }
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
        step["current_assignment"] = {
            "agent_id": next_agent_id,
            "harness": args.harness or step["assignment"]["harness"],
            "model_or_alias": (
                tier_alias(args, data, step["current_tier"]) or step["assignment"]["model_or_alias"]
            ),
        }
    current = step["current_assignment"]
    stored = step["capability_binding"]["bindings"][0]
    if stored["host"] != current["harness"] or stored["executor"] != current["model_or_alias"]:
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
                leaf,
                data["host"],
                host_entry(data["host"]),
                step["current_tier"],
                stored["evidence"],
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
    step["attempt_count"] += 1
    step["agent_id"] = next_agent_id
    step["attempt_id"] = str(uuid.uuid4())
    step["status"] = "ready"
    step["reason"] = reason[:480]


def retryable_steps(
    directory: Path, data: JsonObject, batches: Batches
) -> list[tuple[JsonObject, str, str]]:
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


def retry_command(plan_id: str, run_id: str, step_id: str) -> str:
    return (
        f"{transition_scope(plan_id, run_id)} --step-id {step_id} --to ready --retry "
        "--retry-remediation-file <retry-remediation-v1.json>"
    )


def series_non_final(plan: JsonObject) -> bool:
    """True for a plan whose series slice hands work on (needs a close handoff)."""
    series: JsonValue = plan.get("series")
    return bool(series) and not series.get("final")


def series_final(plan: JsonObject) -> bool:
    """True for a plan whose series slice is the last (needs end verification)."""
    series: JsonValue = plan.get("series")
    return bool(series) and bool(series.get("final"))


def series_closeout_overlay(plan: JsonObject, block: JsonObject) -> JsonObject:
    """Splice the series-final marker into a closeout-adjacent next block.

    Never inlines `end_verification_commands` — a single 480-char command would
    blow the 120-proxy-token next bound alone, so this stays a compact flag the
    parent resolves against the plan it already holds.
    """
    if series_final(plan):
        block["series_end"] = True
    return block


def startable_step_ids(data: JsonObject, steps: list[JsonObject], batches: Batches) -> list[str]:
    """Steps a parent could start now: ready, readiness candidates, or verify-pending."""
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
            )
        if startable:
            result.append(step["id"])
    return result


def with_concurrent(data: JsonObject, batches: Batches, block: JsonObject) -> JsonObject:
    """List up to four other startable steps beside the one action a block names."""
    if block.get("category") in NON_ACTION_CATEGORIES:
        return block
    named = {
        item
        for value in block.values()
        for item in (value if isinstance(value, list) else [value])
        if isinstance(item, str)
    }
    others = [
        sid
        for sid in startable_step_ids(data, ordered_steps(data["steps"]), batches)
        if sid not in named
    ][:MAX_CONCURRENT]
    while others:
        trial = {**block, "concurrent": others}
        if next_tokens(trial) <= MAX_NEXT_TOKENS:
            return trial
        others = others[:-1]
    return block


def checkpoint_next(
    directory: Path, data: JsonObject, batches: Batches, plan: JsonObject
) -> JsonObject:
    """The one highest-priority legal action, plus other steps that could start now."""
    return with_concurrent(data, batches, primary_next(directory, data, batches, plan))


def verify_issued(step: JsonObject) -> bool:
    """True when verify-handoff issued a packet for the step's returned commit."""
    return bool(step.get("verify_id")) and step.get("verify_commit") == step["returned_commit"]


def primary_next(
    directory: Path, data: JsonObject, batches: Batches, plan: JsonObject
) -> JsonObject:
    """Select one highest-priority legal action from the checkpoint."""
    if data["run_status"] == "closed":
        return bounded_action_next({"category": "terminal_closed", "outcome": data["outcome"]})

    stacked = retained_pipeline_steps(data)
    if stacked:
        # A retained provisional_v1 run with stacked state has no legal mutation left.
        return bounded_action_next(
            {"category": "contract_migration_required", "step_ids": stacked}, "step_ids"
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
                "command": land_command(data, integrated[0]),
            },
            "step_ids",
        )
    # Cleanup waits behind dispatch, which keeps the critical path moving.

    # A batch shares one worktree and integrates its tip once, so a completed
    # member waits until no sibling can still commit to that worktree.
    completed = [
        step["id"]
        for step in steps
        if step["status"] == "completed" and batch_settled(data, batches, step["id"])
    ]
    if data.get("verify_policy") == "leaf_verify_v1":
        undecided = [sid for sid in completed if stored_verdict(data["steps"][sid]) is None]
        # A packet issued by verify-handoff is awaiting its verdict, not unissued.
        issued = [sid for sid in undecided if verify_issued(data["steps"][sid])]
        unverified = [sid for sid in undecided if sid not in issued]
        completed = [sid for sid in completed if sid not in issued]
        if unverified:
            return bounded_action_next(
                {
                    "category": "verify_pending",
                    "step_ids": unverified,
                    **verify_commands(data, unverified[0]),
                },
                "step_ids",
            )
        # A rejected member holds its batch: only a retry routes it onward.
        completed = [sid for sid in completed if group_landable(data, batches, sid)]
    if completed:
        return bounded_action_next(
            {
                "category": "integrate_completed",
                "step_ids": completed,
                "command": land_command(data, completed[0]),
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
                "command": dispatch_command(plan_id, run_id, pending[0]),
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


def stored_verdict(step: JsonObject) -> JsonValue:
    """The verdict recorded for the step's current returned commit, or None."""
    stored = step.get("verify")
    if isinstance(stored, dict) and stored.get("commit") == step.get("returned_commit"):
        return stored.get("verdict")
    return None


def commit_verified(step: JsonObject) -> bool:
    return stored_verdict(step) in VERIFY_PASSING


def group_landable(data: JsonObject, batches: Batches, sid: str) -> bool:
    """Every completed member of the step's batch holds a passing verdict."""
    return all(
        commit_verified(data["steps"][member])
        for member in (batches.get(sid) or (sid,))
        if data["steps"][member]["status"] == "completed"
    )
