#!/usr/bin/env python3
"""Validate the runtime-neutral planning-policy executable-plan contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SIZES = {"small": 1, "medium": 2, "large": 3}
TIERS = {"mechanical", "standard", "analytical", "deep"}
AUDIT_OWNERS = {"devsecops-audit", "test-quality-audit", "ip-hygiene", "lean-audit"}
STABLE_ID = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
REQUIRED = (
    "id", "dependencies", "task", "boundary", "read_set", "write_set",
    "settled_decisions", "size", "portable_tier", "worktree_owner",
    "acceptance_command", "return_contract", "stop_conditions", "work_unit_id",
)


def nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def stable_id(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= 64 and STABLE_ID.fullmatch(value) is not None


def vague_audit_question(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    return normalized in {"review risks", "review for risks", "review the risks", "risk review", "risks"}


def validate(plan: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return {"valid": False, "standard_ready_ratio": 0.0, "errors": ["plan must be an object"]}
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
    audit_routes = 0
    for index, leaf in enumerate(leaves):
        prefix = f"leaves[{index}]"
        if not isinstance(leaf, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in REQUIRED:
            if field not in leaf:
                errors.append(f"{prefix}.{field} is required")
        for field in ("id", "task", "boundary", "settled_decisions", "worktree_owner", "return_contract", "work_unit_id"):
            if not nonempty(leaf.get(field)):
                errors.append(f"{prefix}.{field} is required and non-empty")
        leaf_id = leaf.get("id")
        if stable_id(leaf_id):
            if leaf_id in leaf_ids:
                errors.append(f"duplicate leaf id: {leaf_id}")
            leaf_ids.add(leaf_id)
            dependencies[leaf_id] = []
        else:
            errors.append(f"{prefix}.id must be a stable bounded identifier")
        if not isinstance(leaf.get("dependencies"), list):
            errors.append(f"{prefix}.dependencies must be an array")
        elif stable_id(leaf_id):
            for dependency_index, dependency in enumerate(leaf["dependencies"]):
                if not stable_id(dependency):
                    errors.append(f"{prefix}.dependencies[{dependency_index}] must be a stable bounded identifier")
                else:
                    dependencies[leaf_id].append(dependency)
        for field in ("read_set", "write_set", "stop_conditions"):
            if not isinstance(leaf.get(field), list):
                errors.append(f"{prefix}.{field} must be an array")
        if isinstance(leaf.get("stop_conditions"), list) and "missing_load_bearing_information" not in leaf["stop_conditions"]:
            errors.append(f"{prefix}.stop_conditions must include missing_load_bearing_information")
        if leaf.get("size") not in SIZES:
            errors.append(f"{prefix}.size must be small, medium, or large")
        if leaf.get("portable_tier") not in TIERS:
            errors.append(f"{prefix}.portable_tier must be mechanical, standard, analytical, or deep")
        for field in ("model", "model_override", "reasoning_effort", "reasoning_effort_override"):
            if field in leaf:
                errors.append(f"{prefix}.{field} is host-adapter controlled; select portable_tier instead")
        if not isinstance(leaf.get("acceptance_command"), str) or not leaf.get("acceptance_command", "").strip():
            errors.append(f"{prefix}.acceptance_command must be exactly one non-empty command string")
        if leaf.get("portable_tier") in {"analytical", "deep"} and not nonempty(leaf.get("irreducible_unknown_or_risk")):
            errors.append(f"{prefix}.irreducible_unknown_or_risk is required for analytical or deep work")
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
                for field in ("initial_inspection", "domain_match", "materially_changes_approach_or_acceptance", "targeted_inspection_or_focused_tests_cannot_resolve"):
                    if audit.get(field) is not True:
                        errors.append(f"{prefix}.selective_audit.{field} must be true")
                if audit.get("owner") not in AUDIT_OWNERS:
                    errors.append(f"{prefix}.selective_audit.owner must be an owning audit")
                question = audit.get("question")
                if vague_audit_question(question):
                    errors.append(f"{prefix}.selective_audit.question must be bounded")
    if audit_routes > 1:
        errors.append("a plan may route initial inspection to exactly one owning audit")

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
    exception_valid = isinstance(exception, dict) and nonempty(exception.get("rationale")) and nonempty(exception.get("user_approved_by"))
    if ratio < 0.60 and not exception_valid:
        errors.append("standard_ready_ratio is below 0.60 without a user-approved analytical-heavy exception")
    return {
        "valid": not errors,
        "standard_ready_ratio": ratio,
        "ready_weight": ready_weight,
        "total_weight": total_weight,
        "analytical_heavy_exception": exception_valid,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate a plan JSON file")
    validate_parser.add_argument("plan", type=Path)
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "standard_ready_ratio": 0.0, "errors": [str(error)]}, sort_keys=True))
        return 2
    result = validate(plan)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
