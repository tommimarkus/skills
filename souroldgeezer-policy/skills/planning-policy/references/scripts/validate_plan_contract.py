#!/usr/bin/env python3
"""Validate the runtime-neutral planning-policy executable-plan contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SIZES = {"small": 1, "medium": 2, "large": 3}
TIERS = {"mechanical", "standard", "analytical", "deep"}
BATCHABLE_TIERS = {"mechanical", "standard"}
AUDIT_OWNERS = {"devsecops-audit", "test-quality-audit", "ip-hygiene", "lean-audit"}
STABLE_ID = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
REQUIRED = (
    "id",
    "dependencies",
    "task",
    "boundary",
    "read_set",
    "write_set",
    "settled_decisions",
    "size",
    "portable_tier",
    "worktree_owner",
    "acceptance_command",
    "return_contract",
    "stop_conditions",
    "work_unit_id",
)
V2_REQUIRED = ("contract_version", "objective", "scope_summary", "approved_decisions")
V2_RETURN_CONTRACT = "bounded-step-return-v1"
CAPABILITY_BASELINE = "plan-step-base-v1"
CAPABILITY_BINDING_SCHEMA = "planning-capability-binding-v1"
CAPABILITY_KINDS = {"tool", "skill", "service", "permission", "runtime"}
COST_SCHEMA = "planning-execution-cost-v1"
COST_LANES = (
    "parent_baseline",
    "parent_turns",
    "retained_return_context",
    "final_verification",
)
PROXY_TOKEN_RE = re.compile(r"\w+|[^\w\s]")
GLOB_CHARS = ("*", "?", "[")
PLAN_SCALE_LEAF_LIMIT = 12
PLAN_SCALE_WEIGHT_LIMIT = 20


def proxy_tokens(value: Any) -> int:
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"))
    matches = PROXY_TOKEN_RE.finditer(serialized)
    return sum(map(lambda _match: 1, matches))


def token_range(value: Any) -> dict[str, int] | None:
    if type(value) is not dict:
        return None
    if sorted(value) != ["expected", "high", "low"]:
        return None
    low, expected, high = (value.get(key) for key in ("low", "expected", "high"))
    for item in (low, expected, high):
        if type(item) is not int or item < 0:
            return None
    if not low <= expected <= high:
        return None
    return {"low": low, "expected": expected, "high": high}


def attempt_multiplication(attempts: dict[str, dict[str, int | None]]) -> dict[str, int]:
    totals = {"expected": 0, "maximum": 0}
    for attempt in attempts.values():
        totals["expected"] += attempt["expected"] or 0
        totals["maximum"] += attempt["maximum"] or 0
    return totals


def mechanical_shaped(leaf: dict[str, Any]) -> bool:
    """Report whether a standard leaf's own declared fields already settle its edit."""
    if leaf.get("portable_tier") != "standard":
        return False
    if nonempty(leaf.get("open_implementation_choice")):
        return False
    if leaf.get("size") != "small" or not nonempty(leaf.get("settled_decisions")):
        return False
    if nonempty(leaf.get("irreducible_unknown_or_risk")) or leaf.get("selective_audit") is not None:
        return False
    writes = leaf.get("write_set")
    if not isinstance(writes, list) or not writes:
        return False
    return all(
        isinstance(path, str) and path.strip() and not any(char in path for char in GLOB_CHARS)
        for path in writes
    )


def tier_mix(leaves: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {tier: 0 for tier in sorted(TIERS)}
    over_assigned = 0
    for leaf in leaves:
        if not isinstance(leaf, dict):
            continue
        if leaf.get("portable_tier") in counts:
            counts[leaf["portable_tier"]] += 1
        if mechanical_shaped(leaf):
            over_assigned += 1
    total = sum(counts.values())
    return {
        "counts": counts,
        "mechanical_share": round(counts["mechanical"] / total, 2) if total else 0.0,
        "over_assigned": over_assigned,
    }


def dispatch_groups(leaves: list[dict[str, Any]]) -> list[list[str]]:
    """Group leaf ids into dispatches: batch members share one dispatch, leaf order preserved."""
    groups: list[list[str]] = []
    index: dict[tuple[str, str], int] = {}
    for entry in leaves:
        if not isinstance(entry, dict) or not stable_id(entry.get("id")):
            continue
        leaf_id = entry["id"]
        batch = entry.get("batch")
        key = ("batch", batch) if stable_id(batch) else ("leaf", leaf_id)
        if key not in index:
            index[key] = len(groups)
            groups.append([])
        groups[index[key]].append(leaf_id)
    return groups


def has_unbatched_chain(leaves: list[dict[str, Any]]) -> bool:
    """Report a dependency-consecutive same-owner batchable pair left out of a shared batch."""
    by_id = {
        entry["id"]: entry
        for entry in leaves
        if isinstance(entry, dict) and stable_id(entry.get("id"))
    }
    for entry in leaves:
        if not isinstance(entry, dict) or entry.get("portable_tier") not in BATCHABLE_TIERS:
            continue
        dependencies = entry.get("dependencies")
        if not isinstance(dependencies, list):
            continue
        batch = entry.get("batch")
        owner = entry.get("worktree_owner")
        for dependency in dependencies:
            parent = by_id.get(dependency) if isinstance(dependency, str) else None
            if not isinstance(parent, dict) or parent.get("portable_tier") not in BATCHABLE_TIERS:
                continue
            if parent.get("worktree_owner") != owner:
                continue
            if stable_id(batch) and batch == parent.get("batch"):
                continue
            return True
    return False


def total_declared_weight(plan: dict[str, Any]) -> int:
    units = plan.get("work_units")
    if not isinstance(units, list):
        return 0
    return sum(
        SIZES.get(unit.get("original_size"), 0) for unit in units if isinstance(unit, dict)
    )


def cost_advisory(plan: dict[str, Any], leaves: list[dict[str, Any]]) -> dict[str, Any]:
    """Return bounded cost guidance without contributing contract errors."""
    codes: list[str] = []
    profile = plan.get("execution_cost")
    canonical_plan_tokens = proxy_tokens(plan)
    handoffs: list[int] = []
    handoff_by_id: dict[str, int] = {}
    for leaf in leaves:
        if not isinstance(leaf, dict):
            continue
        handoff = proxy_tokens({key: leaf.get(key) for key in REQUIRED if key in leaf})
        handoffs.append(handoff)
        if stable_id(leaf.get("id")):
            handoff_by_id[leaf["id"]] = handoff
    groups = dispatch_groups(leaves)
    dispatch_handoffs = [sum(handoff_by_id[member] for member in group) for group in groups]
    stable = {
        "canonical_plan": canonical_plan_tokens,
        "largest_handoff": max(dispatch_handoffs, default=0),
        "leaf_count": len(handoffs),
        "handoff_total": sum(handoffs),
    }
    attempts = {
        str(leaf.get("id")): {
            "expected": 1,
            "maximum": leaf.get("max_attempts")
            if isinstance(leaf.get("max_attempts"), int)
            else None,
        }
        for leaf in leaves
        if isinstance(leaf, dict) and stable_id(leaf.get("id"))
    }
    result: dict[str, Any] = {
        "schema": "planning-cost-advisory-v1",
        "mode": "advisory",
        "codes": codes,
        "stable_proxy": stable,
        "attempts": attempts,
        "retry_multiplication": attempt_multiplication(attempts),
        "repeated_shared_prefix_proxy": 0,
        "largest_repeated_context_driver": "canonical_plan",
        "declared_total_run": None,
        "declared_maximum_run": None,
        "retained_context_range": None,
        "final_verification_reserve": "indeterminate",
        "tracing": "off",
        "tier_mix": tier_mix(leaves),
    }
    if result["tier_mix"]["over_assigned"]:
        codes.append("PLANCOST-TIER-OVER-ASSIGNED")
    if has_unbatched_chain(leaves):
        codes.append("PLANCOST-UNBATCHED-CHAIN")
    if (
        stable["leaf_count"] > PLAN_SCALE_LEAF_LIMIT
        or total_declared_weight(plan) > PLAN_SCALE_WEIGHT_LIMIT
    ):
        codes.append("PLANCOST-PLAN-SCALE")
    if profile is None:
        codes.extend(
            (
                "PLANCOST-MISSING-PROFILE",
                "PLANCOST-UNKNOWN-RANGES",
                "PLANCOST-UNBOUNDED-FINAL-VERIFY",
            )
        )
        return result
    if (
        not isinstance(profile, dict)
        or len(json.dumps(profile, separators=(",", ":")).encode()) > 4096
    ):
        codes.append("PLANCOST-INVALID-PROFILE")
        return result
    allowed = {
        "schema",
        "mode",
        "expected_attempts",
        "leaf_attempt_overrides",
        "declared_model_tokens",
        "final_verification_commands",
        "assumptions",
        "unknowns",
    }
    commands = profile.get("final_verification_commands")
    assumptions = profile.get("assumptions", [])
    unknowns = profile.get("unknowns", [])
    valid_profile = (
        not set(profile) - allowed
        and profile.get("schema") == COST_SCHEMA
        and profile.get("mode") == "advisory"
        and isinstance(profile.get("expected_attempts", 1), int)
        and not isinstance(profile.get("expected_attempts", 1), bool)
        and 1 <= profile.get("expected_attempts", 1) <= 5
        and isinstance(commands, list)
        and 1 <= len(commands) <= 4
        and all(nonempty_string_in_range(command, 1, 480) for command in commands)
        and isinstance(assumptions, list)
        and len(assumptions) <= 8
        and all(nonempty_string_in_range(value, 1, 240) for value in assumptions)
        and isinstance(unknowns, list)
        and len(unknowns) <= 8
        and all(nonempty_string_in_range(value, 1, 240) for value in unknowns)
    )
    overrides = profile.get("leaf_attempt_overrides", {})
    if not isinstance(overrides, dict) or set(overrides) - set(attempts):
        valid_profile = False
        overrides = {}
    default_attempts = profile.get("expected_attempts", 1)
    for leaf_id, item in attempts.items():
        expected = overrides.get(leaf_id, default_attempts)
        maximum = item["maximum"]
        if (
            not isinstance(expected, int)
            or isinstance(expected, bool)
            or maximum is None
            or not 1 <= expected <= maximum
        ):
            valid_profile = False
            expected = 1
        item["expected"] = expected
    if not valid_profile:
        codes.append("PLANCOST-INVALID-PROFILE")
        result["retry_multiplication"] = attempt_multiplication(attempts)
        return result
    result["retry_multiplication"] = attempt_multiplication(attempts)
    dispatch_expected_total = sum(
        max(attempts[member]["expected"] for member in group) for group in groups
    )
    repeated_attempts = max(0, dispatch_expected_total - len(groups))
    result["repeated_shared_prefix_proxy"] = canonical_plan_tokens * repeated_attempts
    if repeated_attempts:
        codes.append("PLANCOST-RETRY-MULTIPLICATION")
    if result["repeated_shared_prefix_proxy"] > stable["largest_handoff"]:
        codes.append("PLANCOST-DOMINANT-SHARED-PREFIX")

    declared = profile.get("declared_model_tokens")
    if not isinstance(declared, dict):
        codes.append("PLANCOST-UNKNOWN-RANGES")
        return result
    fixed = {lane: token_range(declared.get(lane)) for lane in COST_LANES}
    workers_raw = declared.get("worker_attempts")
    workers = (
        {leaf_id: token_range(workers_raw.get(leaf_id)) for leaf_id in attempts}
        if isinstance(workers_raw, dict) and not set(workers_raw) - set(attempts)
        else {}
    )
    if (
        any(value is None for value in fixed.values())
        or set(workers) != set(attempts)
        or any(value is None for value in workers.values())
    ):
        codes.append("PLANCOST-UNKNOWN-RANGES")
        if fixed["final_verification"] is None:
            codes.append("PLANCOST-UNBOUNDED-FINAL-VERIFY")
        return result
    result["retained_context_range"] = fixed["retained_return_context"]
    result["final_verification_reserve"] = "known"
    totals = {
        key: sum(fixed[lane][key] for lane in COST_LANES) for key in ("low", "expected", "high")
    }
    maximum = dict(totals)
    for leaf_id, value in workers.items():
        expected_count = attempts[leaf_id]["expected"]
        maximum_count = attempts[leaf_id]["maximum"]
        for key in totals:
            totals[key] += value[key] * expected_count
            maximum[key] += value[key] * maximum_count
    result["declared_total_run"] = totals
    result["declared_maximum_run"] = maximum
    return result


def bounded_cost_advisory(value: dict[str, Any]) -> dict[str, Any]:
    value["attempts_omitted"] = 0
    while proxy_tokens(value) > 600 and value.get("attempts"):
        value["attempts"].pop(next(reversed(value["attempts"])))
        value["attempts_omitted"] += 1
    if proxy_tokens(value) > 600:
        value["codes"] = value["codes"][:8]
    return value


def nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def stable_id(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= 64 and STABLE_ID.fullmatch(value) is not None


def vague_audit_question(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    return normalized in {
        "review risks",
        "review for risks",
        "review the risks",
        "risk review",
        "risks",
    }


def nonempty_string_in_range(value: Any, minimum: int, maximum: int) -> bool:
    return isinstance(value, str) and minimum <= len(value.strip()) <= maximum


def canonical_plan_sha256(plan: Any) -> str:
    """Return the stable digest a capability binding joins to exactly."""
    encoded = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def capability_requirements_valid(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"baseline", "additional"}:
        return False
    if value.get("baseline") != CAPABILITY_BASELINE:
        return False
    additional = value.get("additional")
    if not isinstance(additional, list) or len(additional) > 16:
        return False
    return all(
        isinstance(item, dict)
        and set(item) == {"kind", "name", "reason"}
        and item.get("kind") in CAPABILITY_KINDS
        and nonempty_string_in_range(item.get("name"), 1, 120)
        and nonempty_string_in_range(item.get("reason"), 1, 240)
        for item in additional
    )


def capability_binding_matches(plan: dict[str, Any], leaves: list[dict[str, Any]], binding: Any) -> bool:
    """Require one exact resolved binding for every v4 leaf, without making it a plan error."""
    if not isinstance(binding, dict) or set(binding) != {"schema", "plan_sha256", "bindings"}:
        return False
    if binding.get("schema") != CAPABILITY_BINDING_SCHEMA:
        return False
    if binding.get("plan_sha256") != canonical_plan_sha256(plan):
        return False
    bindings = binding.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != len(leaves):
        return False
    expected = {
        leaf.get("id"): leaf.get("capability_requirements")
        for leaf in leaves
        if isinstance(leaf, dict) and stable_id(leaf.get("id"))
    }
    if len(expected) != len(leaves):
        return False
    observed: dict[str, Any] = {}
    for item in bindings:
        if not isinstance(item, dict) or set(item) != {"step_id", "host", "executor", "requirements", "evidence"}:
            return False
        step_id = item.get("step_id")
        if step_id in observed or step_id not in expected:
            return False
        if not nonempty_string_in_range(item.get("host"), 1, 80):
            return False
        if not nonempty_string_in_range(item.get("executor"), 1, 120):
            return False
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not 1 <= len(evidence) <= 8:
            return False
        if any(not nonempty_string_in_range(value, 1, 240) for value in evidence):
            return False
        if item.get("requirements") != expected[step_id]:
            return False
        observed[step_id] = item["requirements"]
    return set(observed) == set(expected)


def contract_result(
    contract_version: int | None,
    dispatch_ready: bool,
    warnings: list[str],
    errors: list[str],
    approval_ready: bool = False,
    ratio: float = 0.0,
    ready_weight: int = 0,
    total_weight: int = 0,
    exception_valid: bool = False,
    advisory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "valid": not errors,
        "contract_version": contract_version,
        "approval_ready": approval_ready and not errors,
        "dispatch_ready": dispatch_ready and not errors,
        "resume_ready": contract_version in {2, 3} and not errors,
        "warnings": warnings,
        "standard_ready_ratio": ratio,
        "ready_weight": ready_weight,
        "total_weight": total_weight,
        "analytical_heavy_exception": exception_valid,
        "errors": errors,
        "cost_advisory": advisory or cost_advisory({}, []),
    }


def validate(plan: Any, capability_binding: Any = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, dict):
        return contract_result(None, False, warnings, ["plan must be an object"])
    has_version_alias = "version" in plan
    if has_version_alias:
        errors.append("version is not a valid plan discriminator; use `contract_version`")
    raw_version = plan.get("contract_version")
    if raw_version is None:
        if has_version_alias:
            contract_version = None
        else:
            contract_version = 1
            warnings.append(
                "unversioned plan is legacy contract version 1; "
                "migrate to contract_version 4 before approval or dispatch"
            )
    elif raw_version in {2, 3, 4} and isinstance(raw_version, int):
        contract_version = raw_version
        for field in V2_REQUIRED:
            if field not in plan:
                errors.append(f"{field} is required for contract version {contract_version}")
        if not nonempty_string_in_range(plan.get("objective"), 1, 240):
            errors.append("objective must be a non-empty string from 1 to 240 characters")
        if not nonempty_string_in_range(plan.get("scope_summary"), 1, 480):
            errors.append("scope_summary must be a non-empty string from 1 to 480 characters")
        decisions = plan.get("approved_decisions")
        if not isinstance(decisions, list) or not 1 <= len(decisions) <= 8:
            errors.append("approved_decisions must be an array containing 1 to 8 strings")
        elif any(not nonempty_string_in_range(decision, 1, 240) for decision in decisions):
            errors.append(
                "approved_decisions entries must be non-empty strings from 1 to 240 characters"
            )
    else:
        contract_version = None
        errors.append("contract_version must be 2, 3, or 4 when specified")
    leaves = plan.get("leaves")
    units = plan.get("work_units")
    if not isinstance(leaves, list) or not leaves:
        errors.append("leaves must be a non-empty array")
        leaves = []
    if not isinstance(units, list) or not units:
        errors.append("work_units must be a non-empty array")
        units = []

    unit_sizes: dict[str, int] = {}
    for index, unit in enumerate(units):
        prefix = f"work_units[{index}]"
        if not isinstance(unit, dict):
            errors.append(f"{prefix} must be an object")
            continue
        unit_id, size = unit.get("id"), unit.get("original_size")
        if not stable_id(unit_id):
            errors.append(f"{prefix}.id must be a stable bounded identifier")
        elif unit_id in unit_sizes:
            errors.append(f"duplicate work unit id: {unit_id}")
        elif size not in SIZES:
            errors.append(f"{prefix}.original_size must be small, medium, or large")
        else:
            unit_sizes[unit_id] = SIZES[size]

    leaf_ids: set[str] = set()
    unit_leaves: dict[str, list[dict[str, Any]]] = {key: [] for key in unit_sizes}
    dependencies: dict[str, list[str]] = {}
    leaf_records: dict[str, tuple[int, dict[str, Any]]] = {}
    batches: dict[str, list[str]] = {}
    audit_routes = 0
    for index, leaf in enumerate(leaves):
        prefix = f"leaves[{index}]"
        if not isinstance(leaf, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in REQUIRED:
            if field not in leaf:
                errors.append(f"{prefix}.{field} is required")
        for field in (
            "id",
            "task",
            "boundary",
            "settled_decisions",
            "worktree_owner",
            "return_contract",
            "work_unit_id",
        ):
            if not nonempty(leaf.get(field)):
                errors.append(f"{prefix}.{field} is required and non-empty")
        leaf_id = leaf.get("id")
        if stable_id(leaf_id):
            if leaf_id in leaf_ids:
                errors.append(f"duplicate leaf id: {leaf_id}")
            leaf_ids.add(leaf_id)
            dependencies[leaf_id] = []
            leaf_records[leaf_id] = (index, leaf)
        else:
            errors.append(f"{prefix}.id must be a stable bounded identifier")
        if not isinstance(leaf.get("dependencies"), list):
            errors.append(f"{prefix}.dependencies must be an array")
        elif stable_id(leaf_id):
            for dependency_index, dependency in enumerate(leaf["dependencies"]):
                if not stable_id(dependency):
                    errors.append(
                        f"{prefix}.dependencies[{dependency_index}] must be a stable "
                        "bounded identifier"
                    )
                else:
                    dependencies[leaf_id].append(dependency)
        batch = leaf.get("batch")
        if batch is not None:
            if not stable_id(batch):
                errors.append(f"{prefix}.batch must be a stable bounded identifier")
            elif stable_id(leaf_id):
                batches.setdefault(batch, []).append(leaf_id)
        for field in ("read_set", "write_set", "stop_conditions"):
            if not isinstance(leaf.get(field), list):
                errors.append(f"{prefix}.{field} must be an array")
        if (
            isinstance(leaf.get("stop_conditions"), list)
            and "missing_load_bearing_information" not in leaf["stop_conditions"]
        ):
            errors.append(f"{prefix}.stop_conditions must include missing_load_bearing_information")
        if leaf.get("size") not in SIZES:
            errors.append(f"{prefix}.size must be small, medium, or large")
        if leaf.get("portable_tier") not in TIERS:
            errors.append(
                f"{prefix}.portable_tier must be mechanical, standard, analytical, or deep"
            )
        for field in ("model", "model_override", "reasoning_effort", "reasoning_effort_override"):
            if field in leaf:
                errors.append(
                    f"{prefix}.{field} is host-adapter controlled; select portable_tier instead"
                )
        if (
            not isinstance(leaf.get("acceptance_command"), str)
            or not leaf.get("acceptance_command", "").strip()
        ):
            errors.append(
                f"{prefix}.acceptance_command must be exactly one non-empty command string"
            )
        if contract_version in {2, 3, 4}:
            attempts = leaf.get("max_attempts")
            if (
                not isinstance(attempts, int)
                or isinstance(attempts, bool)
                or not 1 <= attempts <= 5
            ):
                errors.append(
                    f"{prefix}.max_attempts must be an integer from 1 to 5 for "
                    f"contract version {contract_version}"
                )
            if leaf.get("return_contract") != V2_RETURN_CONTRACT:
                errors.append(
                    f"{prefix}.return_contract must be exactly {V2_RETURN_CONTRACT} "
                    f"for contract version {contract_version}"
                )
        if contract_version == 4 and not capability_requirements_valid(
            leaf.get("capability_requirements")
        ):
            errors.append(
                f"{prefix}.capability_requirements must be an exact {CAPABILITY_BASELINE} "
                "requirements object"
            )
        if leaf.get("portable_tier") in {"analytical", "deep"} and not nonempty(
            leaf.get("irreducible_unknown_or_risk")
        ):
            errors.append(
                f"{prefix}.irreducible_unknown_or_risk is required for analytical or deep work"
            )
        unit_id = leaf.get("work_unit_id")
        if unit_id not in unit_sizes:
            errors.append(f"{prefix}.work_unit_id must name a declared work unit")
        else:
            unit_leaves[unit_id].append(leaf)
        audit = leaf.get("selective_audit")
        if audit is not None:
            audit_routes += 1
            if not isinstance(audit, dict):
                errors.append(f"{prefix}.selective_audit must be an object")
            else:
                required_audit = ("owner", "question", "evidence_surface")
                for field in required_audit:
                    if not nonempty(audit.get(field)):
                        errors.append(f"{prefix}.selective_audit.{field} is required")
                for field in (
                    "initial_inspection",
                    "domain_match",
                    "materially_changes_approach_or_acceptance",
                    "targeted_inspection_or_focused_tests_cannot_resolve",
                ):
                    if audit.get(field) is not True:
                        errors.append(f"{prefix}.selective_audit.{field} must be true")
                if audit.get("owner") not in AUDIT_OWNERS:
                    errors.append(f"{prefix}.selective_audit.owner must be an owning audit")
                question = audit.get("question")
                if vague_audit_question(question):
                    errors.append(f"{prefix}.selective_audit.question must be bounded")
    if audit_routes > 1:
        errors.append("a plan may route initial inspection to exactly one owning audit")

    for batch_id, members in batches.items():
        if not 2 <= len(members) <= 8:
            errors.append(
                f"batch {batch_id} has {len(members)} members; batches must have 2 to 8 members"
            )
        for member in members:
            if leaf_records[member][1].get("portable_tier") not in BATCHABLE_TIERS:
                errors.append(
                    f"batch {batch_id} member {member} must have portable_tier mechanical "
                    "or standard"
                )
        owners = {leaf_records[member][1].get("worktree_owner") for member in members}
        if len(owners) > 1:
            errors.append(f"batch {batch_id} members must share one worktree_owner")
        member_positions = {member: leaf_records[member][0] for member in members}
        member_set = set(members)
        for member in members:
            for dependency in dependencies.get(member, []):
                if dependency in member_set and member_positions[dependency] >= member_positions[member]:
                    errors.append(
                        f"batch {batch_id} member {member} depends on later-listed batch "
                        f"member {dependency}"
                    )

    for leaf_id, deps in dependencies.items():
        for dep in deps:
            if dep not in leaf_ids:
                errors.append(f"leaf {leaf_id} depends on unknown leaf {dep}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            errors.append(f"cyclic dependency at leaf {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in dependencies.get(node, []):
            if dep in dependencies:
                visit(dep)
        visiting.remove(node)
        visited.add(node)

    for leaf_id in dependencies:
        visit(leaf_id)

    ready_weight = 0
    total_weight = sum(unit_sizes.values())
    for unit_id, weight in unit_sizes.items():
        members = unit_leaves[unit_id]
        if not members:
            errors.append(f"work unit {unit_id} has no leaves")
            continue
        if all(member.get("portable_tier") in {"mechanical", "standard"} for member in members):
            ready_weight += weight
    ratio = ready_weight / total_weight if total_weight else 0.0
    exception = plan.get("analytical_heavy_exception")
    exception_valid = (
        isinstance(exception, dict)
        and nonempty(exception.get("rationale"))
        and nonempty(exception.get("user_approved_by"))
    )
    if ratio < 0.60 and not exception_valid:
        errors.append(
            "standard_ready_ratio is below 0.60 without a user-approved analytical-heavy exception"
        )
    if contract_version in {2, 3}:
        warnings.append("blocked:contract_migration_required")
    binding_matches = contract_version == 4 and capability_binding_matches(plan, leaves, capability_binding)
    if contract_version == 4 and not binding_matches:
        warnings.append("blocked:capability_unavailable")
    advisory = bounded_cost_advisory(cost_advisory(plan, leaves))
    result = contract_result(
        contract_version,
        binding_matches,
        warnings,
        errors,
        contract_version == 4,
        ratio,
        ready_weight,
        total_weight,
        exception_valid,
        advisory,
    )
    result["plan_sha256"] = canonical_plan_sha256(plan)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate a plan JSON file")
    validate_parser.add_argument("plan", type=Path)
    validate_parser.add_argument(
        "--capability-binding",
        type=Path,
        help="optional planning-capability-binding-v1 JSON for dispatch validation",
    )
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        binding = (
            json.loads(args.capability_binding.read_text(encoding="utf-8"))
            if args.capability_binding is not None
            else None
        )
    except (OSError, json.JSONDecodeError) as error:
        print(
            json.dumps(
                contract_result(None, False, [], [str(error)]),
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2
    result = validate(plan, capability_binding=binding)
    result["plan_sha256"] = canonical_plan_sha256(plan)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
