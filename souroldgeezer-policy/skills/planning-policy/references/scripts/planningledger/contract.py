"""Planning ledger contract: plan validator bridge, leaves, amendments, capability bindings and host tiers."""

from __future__ import annotations

import json

from . import plancontract

from .vocabulary import (
    AMENDMENT_FIELDS,
    AMENDMENT_OPTIONAL,
    FORWARD_SCHEMA,
    MAX_AMENDED_ATTEMPTS,
    MAX_AMENDED_COMMAND,
    MAX_AMENDMENTS,
    MAX_AMENDMENT_PATHS,
)
from .core import (
    Error,
    HOST_TIERS_FILE,
    UsageError,
    digest,
    ident,
    read_json,
    rel,
)

__all__ = [
    "standard_precision",
    "outside_paths",
    "leaves_by_id",
    "valid_amendments",
    "validate_amendment_events",
    "effective_leaf",
    "effective_leaves",
    "checkpoint_binding",
    "validator_module",
    "read_plan",
    "host_tiers",
    "host_entry",
    "host_step_binding",
    "derived_setup",
    "tier_alias",
    "capability_bindings",
    "checked_binding",
    "binding_for_step",
    "valid_stored_binding",
    "assignments",
    "checked_assignments",
]


def changed_path_allowed(path, write_set):
    return validator_module().write_set_covers(write_set, path)


def standard_precision(data):
    """True for a run stamped standard_v1; an unstamped retained run stays strict."""
    return data.get("precision_policy") == "standard_v1"


def outside_paths(paths, write_set):
    """The returned or committed paths no write_set entry covers, in first-seen order."""
    return [path for path in dict.fromkeys(paths) if not changed_path_allowed(path, write_set)]


def leaves_by_id(plan):
    return {leaf["id"]: leaf for leaf in plan["leaves"]}


def valid_amendments(step, approved):
    """Return a step's stored amendments, failing closed on any malformed record."""
    value = step.get("amendments", [])
    if not isinstance(value, list) or len(value) > MAX_AMENDMENTS:
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
            valid_amendments(steps[sid], leaf) if sid in steps else [],
        )
        for sid, leaf in leaves_by_id(plan).items()
    }


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


def validator_module():
    return plancontract


def plan_validator():
    return validator_module().validate


def read_plan(path):
    data = read_json(path, "cannot read plan file")
    result = plan_validator()(data)
    if (
        not result.get("valid")
        or not result.get("approval_ready")
        or result.get("contract_version") != FORWARD_SCHEMA
    ):
        raise Error("plan is not dispatch-ready")
    return data


def host_tiers():
    """The single host tier map: per host, the tier models, skill support, and verifiers."""
    return read_json(HOST_TIERS_FILE, "cannot read host tier map")


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
    """Load one complete binding and retain assigned-step evidence."""
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
