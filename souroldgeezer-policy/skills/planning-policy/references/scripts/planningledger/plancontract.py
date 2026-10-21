"""Validate the runtime-neutral planning-policy executable-plan contract."""
# Implementation behind the validate_plan_contract.py entry shim; stdlib-only, so it imports no
# other planningledger module.

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any, TypeGuard, cast

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
PRECISION_MODES = ("standard", "strict")
CONTRACT_VERSION = 5
RETIRED_VERSIONS_ERROR = (
    "contract_version must be 5; plan contract versions 1-4 were retired after "
    "souroldgeezer-policy 2026.10.9"
)
PLAN_REQUIRED = ("objective", "scope_summary", "approved_decisions")
RETURN_CONTRACT = "bounded-step-return-v1"
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
PLACEHOLDER_DECISIONS = {"tbd", "todo", "unknown", "unresolved"}
NOOP_ACCEPTANCE_COMMANDS = {"true", ":", "exit 0"}
VERIFICATION_MODES = {"per-leaf", "closeout-only"}
BUDGET_KEYS = {"max_changed_lines", "max_files", "exempt_paths", "reason"}
BUDGET_DEFAULTS = {"small": (150, 6), "medium": (400, 15), "large": (400, 15)}
BUDGET_EXEMPT_LIMIT = 8
PLAN_SCALE_LEAF_LIMIT = 12
PLAN_SCALE_WEIGHT_LIMIT = 20
MICROLEAF_CANDIDATE_LIMIT = 8
SERIES_KEYS = {"series_id", "slice", "final", "end_verification_commands", "predecessor"}
PREDECESSOR_KEYS = {"plan_id", "plan_sha256", "run_id", "outcome", "handoff_sha256"}
SERIES_OUTCOMES = {"completed", "blocked", "abandoned"}
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
UUID4_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
HANDOFF_SCHEMA = "planning-approval-handoff-v1"
HANDOFF_PLAN_MAX = 64 * 1024
HANDOFF_REFERENCE_MAX = 4 * 1024
HANDOFF_INLINE_MAX = 68 * 1024
HANDOFF_BLOCK_LINE_MAX = 4096


def hashable(value: Any) -> Any:
    """Key a JSON array or object by its canonical text so set and dict lookups never raise.

    Every other JSON value is returned unchanged, so lookups keep their exact
    results; a malformed array or object simply matches nothing it should not.
    """
    if isinstance(value, (dict, list)):
        return ("unhashable", json.dumps(value, sort_keys=True, separators=(",", ":")))
    return value


def searchable(value: Any) -> Any:
    """Membership target for a declared field: containers and strings as-is, other scalars
    hold nothing.
    """
    return value if isinstance(value, (dict, list, str)) else ()


def proxy_tokens(value: Any) -> int:
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"))
    matches = PROXY_TOKEN_RE.finditer(serialized)
    return sum(map(lambda _match: 1, matches))


def token_range(value: Any) -> dict[str, int] | None:
    if type(value) is not dict:
        return None
    if sorted(value) != ["expected", "high", "low"]:
        return None
    low, expected, high = (value[key] for key in ("low", "expected", "high"))
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
        if hashable(leaf.get("portable_tier")) in counts:
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


def is_pure_chain_pair(
    parent: dict[str, Any], entry: dict[str, Any], leaves: list[dict[str, Any]]
) -> bool:
    """A distinct-owner unbatched pair where the dependent has one dependency and the
    predecessor one dependent.
    """
    if stable_id(parent.get("batch")) or stable_id(entry.get("batch")):
        return False
    if entry.get("dependencies") != [parent.get("id")]:
        return False
    dependents = [
        other
        for other in leaves
        if isinstance(other, dict)
        and isinstance(other.get("dependencies"), list)
        and parent.get("id") in other["dependencies"]
    ]
    return len(dependents) == 1


def dispatch_depths(leaves: list[dict[str, Any]]) -> list[int]:
    """Depth of each dispatch group: 1 plus the deepest group it depends on."""
    groups = dispatch_groups(leaves)
    group_of = {member: index for index, group in enumerate(groups) for member in group}
    by_id = {
        entry["id"]: entry
        for entry in leaves
        if isinstance(entry, dict) and stable_id(entry.get("id"))
    }
    upstream: list[set[int]] = []
    for index, group in enumerate(groups):
        found: set[int] = set()
        for member in group:
            dependencies = by_id[member].get("dependencies")
            for dependency in dependencies if isinstance(dependencies, list) else []:
                if isinstance(dependency, str) and group_of.get(dependency, index) != index:
                    found.add(group_of[dependency])
        upstream.append(found)
    depths: dict[int, int] = {}

    def depth(index: int, visiting: frozenset[int]) -> int:
        if index not in depths:
            depths[index] = 1 + max(
                (depth(parent, visiting | {index}) for parent in upstream[index] - visiting),
                default=0,
            )
        return depths[index]

    return [depth(index, frozenset()) for index in range(len(groups))]


def has_unbatched_chain(leaves: list[dict[str, Any]]) -> bool:
    """Report a dependency-consecutive same-owner batchable pair left out of a shared batch."""
    by_id = {
        entry["id"]: entry
        for entry in leaves
        if isinstance(entry, dict) and stable_id(entry.get("id"))
    }
    for entry in leaves:
        if (
            not isinstance(entry, dict)
            or hashable(entry.get("portable_tier")) not in BATCHABLE_TIERS
        ):
            continue
        dependencies = entry.get("dependencies")
        if not isinstance(dependencies, list):
            continue
        batch = entry.get("batch")
        owner = entry.get("worktree_owner")
        for dependency in dependencies:
            parent = by_id.get(dependency) if isinstance(dependency, str) else None
            if (
                not isinstance(parent, dict)
                or hashable(parent.get("portable_tier")) not in BATCHABLE_TIERS
            ):
                continue
            if parent.get("worktree_owner") != owner:
                if is_pure_chain_pair(parent, entry, leaves):
                    return True
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
        SIZES.get(hashable(unit.get("original_size")), 0)
        for unit in units
        if isinstance(unit, dict)
    )


def normalized_outcome(value: Any) -> str | None:
    if not nonempty_string_in_range(value, 1, 240):
        return None
    return re.sub(r"\s+", " ", value.strip().lower())


def normalized_writes(leaf: dict[str, Any]) -> set[str]:
    writes = leaf.get("write_set")
    if not isinstance(writes, list):
        return set()
    return {path.strip() for path in writes if isinstance(path, str) and path.strip()}


def safe_exact_write_set(leaf: dict[str, Any]) -> bool:
    writes = leaf.get("write_set")
    if not isinstance(writes, list) or not writes:
        return False
    normalized = normalized_writes(leaf)
    return len(normalized) == len(writes) and all(
        not path.startswith("/")
        and ".." not in path.split("/")
        and not any(character in path for character in GLOB_CHARS)
        for path in normalized
    )


def exact_path_list(value: Any, *, non_empty: bool) -> bool:
    """Strict-precision test for a path list: safe paths, no glob characters, optionally
    non-empty.
    """
    if not isinstance(value, list) or (non_empty and not value):
        return False
    return all(
        isinstance(path, str)
        and bool(path.strip())
        and not path.startswith("/")
        and ".." not in path.split("/")
        and not any(character in path for character in GLOB_CHARS)
        for path in value
    )


def safe_repository_path(value: Any) -> bool:
    """Accept one bounded, repository-relative declaration, including existing glob forms."""
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 240:
        return False
    if (
        value.startswith("/")
        or "\\" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        return False
    return all(segment not in {"", ".", ".."} for segment in value.split("/"))


def repository_glob_matches(path: str, pattern: str) -> bool:
    """Match a repository-relative path with segment-aware ``**`` support."""
    path_parts = path.split("/")
    pattern_parts = pattern.split("/")
    pending = [(0, 0)]
    visited: set[tuple[int, int]] = set()
    while pending:
        path_index, pattern_index = pending.pop()
        state = (path_index, pattern_index)
        if state in visited:
            continue
        visited.add(state)
        if pattern_index == len(pattern_parts):
            if path_index == len(path_parts):
                return True
            continue
        pattern_part = pattern_parts[pattern_index]
        if pattern_part == "**":
            pending.append((path_index, pattern_index + 1))
            if path_index < len(path_parts):
                pending.append((path_index + 1, pattern_index))
        elif path_index < len(path_parts) and fnmatch.fnmatchcase(
            path_parts[path_index], pattern_part
        ):
            pending.append((path_index + 1, pattern_index + 1))
    return False


def write_set_covers(write_set: list[Any], path: str) -> bool:
    """Exact-or-descendant for plain entries, segment-aware glob for glob entries.

    The ledger's changed-path scope check delegates here, so plan admission and
    returned-diff checks share one matcher.
    """
    for allowed in write_set:
        if not isinstance(allowed, str):
            continue
        if any(character in allowed for character in GLOB_CHARS):
            if repository_glob_matches(path, allowed):
                return True
        elif path == allowed or path.startswith(allowed.rstrip("/") + "/"):
            return True
    return False


def _walk_files(base: Path) -> list[Path]:
    """Regular files below base, skipping hidden directories, node_modules, bytecode, and
    symlinks.
    """
    found: list[Path] = []
    for directory, names, files in os.walk(base):
        names[:] = sorted(
            name
            for name in names
            if not name.startswith(".") and name not in {"node_modules", "__pycache__"}
        )
        for name in sorted(files):
            if name.endswith(".pyc"):
                continue
            path = Path(directory) / name
            if path.is_file() and not path.is_symlink():
                found.append(path)
    return found


def _pin_needles(entry: str, basenames: dict[str, int]) -> tuple[str, ...]:
    """Strings whose presence in a file pins one write_set entry."""
    segments = entry.split("/")
    glob_at = next(
        (i for i, part in enumerate(segments) if any(c in part for c in GLOB_CHARS)), None
    )
    if glob_at is not None:
        prefix = "/".join(segments[:glob_at])
        return (prefix,) if prefix else ()
    needles = [entry]
    if basenames.get(segments[-1]) == 1:
        needles.append(segments[-1])
    return tuple(needles)


def pin_scan(
    leaves: list[Any],
    roots: list[str],
    repo_root: Path,
    *,
    limit: int = 8,
    max_bytes: int = 1 << 20,
) -> dict[str, Any]:
    """Report files under roots that mention a leaf's write paths but sit in no leaf's write_set."""
    base = repo_root.resolve()
    basenames: dict[str, int] = {}
    for path in _walk_files(base):
        basenames[path.name] = basenames.get(path.name, 0) + 1
    writes: dict[str, list[str]] = {}
    for entry in leaves:
        if (
            isinstance(entry, dict)
            and stable_id(entry.get("id"))
            and isinstance(entry.get("write_set"), list)
        ):
            writes[entry["id"]] = [
                item for item in entry["write_set"] if safe_repository_path(item)
            ]
    owned_sets = list(writes.values())
    present: list[str] = []
    missing: list[str] = []
    pinning: dict[str, set[str]] = {leaf_id: set() for leaf_id in writes}
    for root in roots:
        target = (base / root).resolve() if safe_repository_path(root) else None
        if target is None or not target.is_dir() or base not in (target, *target.parents):
            missing.append(root)
            continue
        present.append(root)
        for path in _walk_files(target):
            relative = path.relative_to(base).as_posix()
            if path.stat().st_size > max_bytes or any(
                write_set_covers(owned, relative) for owned in owned_sets
            ):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for leaf_id, entries in writes.items():
                if any(
                    needle in text for item in entries for needle in _pin_needles(item, basenames)
                ):
                    pinning[leaf_id].add(relative)
    listed: dict[str, list[str]] = {}
    truncated = False
    for leaf_id, found in pinning.items():
        if found:
            ordered = sorted(found)
            truncated = truncated or len(ordered) > limit
            listed[leaf_id] = ordered[:limit]
    return {"roots": present, "roots_missing": missing, "leaves": listed, "truncated": truncated}


def band_budget(leaf: dict[str, Any]) -> tuple[int, int]:
    return BUDGET_DEFAULTS.get(hashable(leaf.get("size")), BUDGET_DEFAULTS["medium"])


def changeset_budget(leaf: dict[str, Any]) -> dict[str, Any]:
    """The only derivation of a leaf's changeset budget: size-band defaults plus declared
    overrides.
    """
    lines, files = band_budget(leaf)
    declared = leaf.get("changeset_budget")
    declared = declared if isinstance(declared, dict) else {}
    exempt = declared.get("exempt_paths")
    return {
        "max_changed_lines": declared.get("max_changed_lines", lines),
        "max_files": declared.get("max_files", files),
        "exempt_paths": list(exempt) if isinstance(exempt, list) else [],
    }


def changeset_budget_errors(leaf: dict[str, Any]) -> list[str]:
    declared = leaf.get("changeset_budget")
    prefix = "changeset_budget"
    if not isinstance(declared, dict):
        return [f"{prefix} must be an object"]
    errors: list[str] = []
    if set(declared) - BUDGET_KEYS:
        errors.append(f"{prefix} has unknown keys: {sorted(set(declared) - BUDGET_KEYS)}")
    defaults = dict(zip(("max_changed_lines", "max_files"), band_budget(leaf), strict=True))
    raised = False
    for key, default in defaults.items():
        if key not in declared:
            continue
        value = declared[key]
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 2 * default:
            errors.append(f"{prefix}.{key} must be an integer from 1 to {2 * default}")
        elif value > default:
            raised = True
    exempt = declared.get("exempt_paths", [])
    if not isinstance(exempt, list) or len(exempt) > BUDGET_EXEMPT_LIMIT:
        errors.append(
            f"{prefix}.exempt_paths must be an array of at most {BUDGET_EXEMPT_LIMIT} paths"
        )
        exempt = []
    declared_writes = leaf.get("write_set")
    write_set = declared_writes if isinstance(declared_writes, list) else []
    for index, path in enumerate(exempt):
        if not safe_repository_path(path):
            errors.append(f"{prefix}.exempt_paths[{index}] must be a safe repository-relative path")
        elif not write_set_covers(write_set, path):
            errors.append(f"{prefix}.exempt_paths[{index}] must be covered by write_set")
    reason = declared.get("reason")
    if (raised or exempt) and not nonempty_string_in_range(reason, 1, 240):
        errors.append(
            f"{prefix}.reason is required (1 to 240 characters) to raise a limit or exempt paths"
        )
    elif "reason" in declared and not nonempty_string_in_range(reason, 1, 240):
        errors.append(f"{prefix}.reason must be a string from 1 to 240 characters")
    return errors


def declared_path_set_errors(leaf: dict[str, Any], field: str) -> list[str]:
    value = leaf.get(field)
    if not isinstance(value, list):
        return []
    errors: list[str] = []
    seen: set[str] = set()
    for index, path in enumerate(value):
        if not safe_repository_path(path):
            errors.append(
                f"{field}[{index}] must be a unique safe repository-relative path string "
                "from 1 to 240 characters"
            )
            continue
        if path in seen:
            errors.append(f"{field}[{index}] must be unique")
        seen.add(path)
    return errors


def has_placeholder_decision(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in PLACEHOLDER_DECISIONS
    if isinstance(value, dict):
        return any(has_placeholder_decision(item) for item in value.values())
    if isinstance(value, list):
        return any(has_placeholder_decision(item) for item in value)
    return False


def static_path_prefix(path: str) -> tuple[str, ...]:
    """Return only complete literal segments before a glob, avoiding unsound glob parsing."""
    prefix: list[str] = []
    for segment in path.split("/"):
        if any(character in segment for character in GLOB_CHARS):
            break
        prefix.append(segment)
    return tuple(prefix)


def path_coverage_overlaps(first: str, second: str) -> bool:
    first_prefix, second_prefix = static_path_prefix(first), static_path_prefix(second)
    shared = min(len(first_prefix), len(second_prefix))
    return first_prefix[:shared] == second_prefix[:shared]


def write_coverage_overlaps(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_writes, second_writes = first.get("write_set"), second.get("write_set")
    if not isinstance(first_writes, list) or not isinstance(second_writes, list):
        return False
    return any(
        path_coverage_overlaps(first_path, second_path)
        for first_path in first_writes
        if safe_repository_path(first_path)
        for second_path in second_writes
        if safe_repository_path(second_path)
    )


def dependency_orders(first_id: str, second_id: str, dependencies: dict[str, list[str]]) -> bool:
    """Return whether either leaf transitively depends on the other."""

    def reaches(start: str, target: str) -> bool:
        pending = list(dependencies.get(start, []))
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current == target:
                return True
            if current not in visited:
                visited.add(current)
                pending.extend(dependencies.get(current, []))
        return False

    return reaches(first_id, second_id) or reaches(second_id, first_id)


def leaves_are_ordered(
    first_id: str,
    second_id: str,
    dependencies: dict[str, list[str]],
    leaf_records: dict[str, tuple[int, dict[str, Any]]],
) -> bool:
    if dependency_orders(first_id, second_id, dependencies):
        return True
    first_index, first = leaf_records[first_id]
    second_index, second = leaf_records[second_id]
    return (
        stable_id(first.get("batch"))
        and first.get("batch") == second.get("batch")
        and first_index != second_index
    )


def direct_dependency(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_id, second_id = first.get("id"), second.get("id")
    return (
        isinstance(first_id, str)
        and isinstance(second_id, str)
        and (
            first_id in searchable(second.get("dependencies", []))
            or second_id in searchable(first.get("dependencies", []))
        )
    )


def microleaf_candidates(leaves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return at most eight bounded, advisory-only small-leaf merge signals."""
    candidates: list[dict[str, Any]] = []
    for index, first in enumerate(leaves):
        if not isinstance(first, dict) or first.get("size") != "small":
            continue
        for second in leaves[index + 1 :]:
            if not isinstance(second, dict) or second.get("size") != "small":
                continue
            dependent = direct_dependency(first, second)
            same_owner = first.get("worktree_owner") == second.get("worktree_owner")
            same_acceptance = first.get("acceptance_command") == second.get("acceptance_command")
            overlapping_writes = bool(normalized_writes(first) & normalized_writes(second))
            same_owner_tier_dependency = (
                same_owner
                and dependent
                and first.get("portable_tier") == second.get("portable_tier")
            )
            signals: list[str] = []
            if same_acceptance and same_owner:
                signals.append("same_acceptance_same_owner")
            if same_acceptance and dependent:
                signals.append("same_acceptance_direct_dependency")
            if overlapping_writes:
                signals.append("overlapping_writes")
            if same_owner_tier_dependency:
                signals.append("same_owner_same_tier_dependency")
            if signals:
                candidates.append(
                    {
                        "leaf_ids": [first.get("id"), second.get("id")],
                        "signals": signals,
                    }
                )
                if len(candidates) == MICROLEAF_CANDIDATE_LIMIT:
                    return candidates
    return candidates


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
    depths = dispatch_depths(leaves)
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
        "critical_path": max(depths, default=0),
        "max_parallel_width": max((depths.count(level) for level in set(depths)), default=0),
        "verify_dispatches": 0 if plan.get("verification") == "closeout-only" else len(groups),
    }
    candidates = microleaf_candidates(leaves)
    if candidates:
        codes.append("PLANCOST-MICROLEAF-RISK")
        result["microleaf_candidates"] = candidates
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
    # A valid profile left every expected count an int and every maximum known.
    counts = cast(dict[str, dict[str, int]], attempts)
    dispatch_expected_total = sum(
        max(counts[member]["expected"] for member in group) for group in groups
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
    # The check above proved every fixed and worker range known.
    known_fixed = cast(dict[str, dict[str, int]], fixed)
    known_workers = cast(dict[str, dict[str, int]], workers)
    totals = {
        key: sum(known_fixed[lane][key] for lane in COST_LANES)
        for key in ("low", "expected", "high")
    }
    maximum = dict(totals)
    for leaf_id, value in known_workers.items():
        expected_count = counts[leaf_id]["expected"]
        maximum_count = counts[leaf_id]["maximum"]
        for key in totals:
            totals[key] += value[key] * expected_count
            maximum[key] += value[key] * maximum_count
    result["declared_total_run"] = totals
    result["declared_maximum_run"] = maximum
    return result


def bounded_cost_advisory(value: dict[str, Any]) -> dict[str, Any]:
    value["attempts_omitted"] = 0
    value["microleaf_candidates_omitted"] = 0
    while proxy_tokens(value) > 600 and value.get("attempts"):
        value["attempts"].pop(next(reversed(value["attempts"])))
        value["attempts_omitted"] += 1
    while proxy_tokens(value) > 600 and value.get("microleaf_candidates"):
        value["microleaf_candidates"].pop()
        value["microleaf_candidates_omitted"] += 1
    if proxy_tokens(value) > 600:
        value["codes"] = value["codes"][:8]
    return value


def nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def valid_branch_name(value: Any) -> bool:
    """Stdlib mirror of `git check-ref-format --branch` for a leaf branch name."""
    if not isinstance(value, str) or not value or value == "@" or value.startswith(("-", "/")):
        return False
    if value.endswith(("/", ".")) or "//" in value or ".." in value or "@{" in value:
        return False
    if re.search(r"[\x00-\x20\x7f~^:?*\[\\]", value):
        return False
    return all(
        part and not part.startswith(".") and not part.endswith(".lock")
        for part in value.split("/")
    )


def stable_id(value: Any) -> TypeGuard[str]:
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


class HandoffError(ValueError):
    """A bounded approval transport failure; never contains a partial plan."""

    def __init__(self, message: str, code: str = "blocked:missing_input"):
        super().__init__(message)
        self.code = code


def _encoded(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _read_json_source(source: str, limit: int | None = None) -> Any:
    if limit is None:
        text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
        return json.loads(text)
    if source == "-":
        raw = sys.stdin.buffer.read(limit + 1)
    else:
        # Nonblocking open plus fstat rejects devices/FIFOs without waiting for a writer.
        descriptor = os.open(source, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise HandoffError("handoff input must be a regular file or stdin")
            raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise HandoffError("handoff input exceeds its byte limit")
    return json.loads(raw)


def error_result(code: str, message: str) -> dict[str, Any]:
    return {"valid": False, "errors": [f"{code}: {message}"], "blocked": code}


def _approval_validation(plan: Any) -> dict[str, Any]:
    if len(_encoded(plan)) > HANDOFF_PLAN_MAX:
        raise HandoffError("canonical plan exceeds 64 KiB")
    result = validate(plan)
    if not result["valid"] or not result.get("approval_ready"):
        raise HandoffError("handoff requires a complete approval-ready v5 plan")
    return result


def _reference_path(value: Any, *, absolute: bool) -> Path:
    if not isinstance(value, str) or not value or value == "-":
        raise HandoffError("reference requires a persistent plan file")
    candidate = Path(value)
    if absolute and not candidate.is_absolute():
        raise HandoffError("plan_path must be absolute")
    resolved = candidate.resolve(strict=True)
    if any(resolved.is_relative_to(root) for root in temporary_roots()):
        raise HandoffError("temporary-directory references are ineligible")
    return resolved


def temporary_roots() -> tuple[Path, ...]:
    """Return known temporary roots without tempfile's writable discovery probe."""
    values = ["/tmp", "/var/tmp", "/dev/shm", "/run/user"]
    values.extend(os.environ.get(name, "") for name in ("TMPDIR", "TEMP", "TMP"))
    roots: list[Path] = []
    for value in values:
        if value and Path(value).is_absolute():
            root = Path(value).resolve(strict=False)
            if root not in roots:
                roots.append(root)
    return tuple(roots)


def emit_handoff(plan: Any, mode: str, source: str = "-") -> dict[str, Any]:
    _approval_validation(plan)
    handoff = {"schema": HANDOFF_SCHEMA, "plan_sha256": canonical_plan_sha256(plan)}
    if mode == "reference":
        path = _reference_path(source, absolute=False)
        recorded = _read_json_source(str(path), 4 * HANDOFF_PLAN_MAX)
        if canonical_plan_sha256(recorded) != handoff["plan_sha256"]:
            raise HandoffError("plan changed during emission", "blocked:plan_tampered")
        handoff["plan_path"] = str(path)
        limit = HANDOFF_REFERENCE_MAX
    else:
        handoff["plan"] = plan
        limit = HANDOFF_INLINE_MAX
    if len(_encoded(handoff)) > limit:
        raise HandoffError("handoff envelope exceeds its byte limit")
    return handoff


def _overlong_block_path(value: Any, path: str = "$", depth: int = 0) -> str | None:
    """Return the path of the first element whose block line is too long, never its content."""
    if isinstance(value, dict):
        members = [
            (json.dumps(key) + ": ", f"{path}.{key}", child) for key, child in sorted(value.items())
        ]
    elif isinstance(value, list):
        members = [("", f"{path}[{index}]", child) for index, child in enumerate(value)]
    else:
        return None
    for position, (label, child_path, child) in enumerate(members):
        opener = (
            ("[" if isinstance(child, list) else "{")
            if isinstance(child, (dict, list)) and child
            else json.dumps(child)
        )
        comma = "," if position < len(members) - 1 else ""
        if depth + 1 + len(label) + len(opener) + len(comma) > HANDOFF_BLOCK_LINE_MAX:
            return child_path
        found = _overlong_block_path(child, child_path, depth + 1)
        if found:
            return found
    return None


def render_handoff_block(handoff: dict[str, Any]) -> str:
    """Render the envelope one element per line so every line fits the approval dialog."""
    text = json.dumps(handoff, sort_keys=True, indent=1, ensure_ascii=True)
    if any(len(line) > HANDOFF_BLOCK_LINE_MAX for line in text.splitlines()):
        location = (_overlong_block_path(handoff) or "$")[:80]
        raise HandoffError(f"block line exceeds {HANDOFF_BLOCK_LINE_MAX} characters at {location}")
    return text


def resolve_handoff(handoff: Any) -> tuple[Any, dict[str, Any]]:
    expected = {"schema", "plan_sha256"}
    if not isinstance(handoff, dict) or set(handoff) not in (
        expected | {"plan"},
        expected | {"plan_path"},
    ):
        raise HandoffError("expected exactly schema, plan_sha256, and one of plan or plan_path")
    digest = handoff["plan_sha256"]
    if (
        handoff["schema"] != HANDOFF_SCHEMA
        or not isinstance(digest, str)
        or not SHA256_HEX.fullmatch(digest)
    ):
        raise HandoffError("invalid handoff schema or digest")
    reference = "plan_path" in handoff
    limit = HANDOFF_REFERENCE_MAX if reference else HANDOFF_INLINE_MAX
    if len(_encoded(handoff)) > limit:
        raise HandoffError("handoff envelope exceeds its byte limit")
    if reference:
        path = _reference_path(handoff["plan_path"], absolute=True)
        plan = _read_json_source(str(path), 4 * HANDOFF_PLAN_MAX)
    else:
        plan = handoff["plan"]
    if len(_encoded(plan)) > HANDOFF_PLAN_MAX:
        raise HandoffError("canonical plan exceeds 64 KiB")
    if canonical_plan_sha256(plan) != digest:
        raise HandoffError("plan digest does not match", "blocked:plan_tampered")
    return plan, _approval_validation(plan)


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
        and hashable(item.get("kind")) in CAPABILITY_KINDS
        and nonempty_string_in_range(item.get("name"), 1, 120)
        and nonempty_string_in_range(item.get("reason"), 1, 240)
        for item in additional
    )


def capability_binding_matches(
    plan: dict[str, Any], leaves: list[dict[str, Any]], binding: Any
) -> bool:
    """Require one exact resolved binding for every leaf, without making it a plan error."""
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
        if not isinstance(item, dict) or set(item) != {
            "step_id",
            "host",
            "executor",
            "requirements",
            "evidence",
        }:
            return False
        step_id = item["step_id"]
        if hashable(step_id) in observed or hashable(step_id) not in expected:
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


def predecessor_errors(predecessor: Any) -> list[str]:
    prefix = "series.predecessor"
    if not isinstance(predecessor, dict):
        return [f"{prefix} must be an object"]
    errors: list[str] = []
    if set(predecessor) != PREDECESSOR_KEYS:
        errors.append(f"{prefix} must have exactly the keys {sorted(PREDECESSOR_KEYS)}")
    if not stable_id(predecessor.get("plan_id")):
        errors.append(f"{prefix}.plan_id must be a stable bounded identifier")
    plan_sha256 = predecessor.get("plan_sha256")
    if not isinstance(plan_sha256, str) or not SHA256_HEX.fullmatch(plan_sha256):
        errors.append(f"{prefix}.plan_sha256 must be 64 lowercase hex characters")
    run_id = predecessor.get("run_id")
    if not isinstance(run_id, str) or not UUID4_RE.fullmatch(run_id):
        errors.append(f"{prefix}.run_id must be a canonical lowercase UUID4")
    if hashable(predecessor.get("outcome")) not in SERIES_OUTCOMES:
        errors.append(f"{prefix}.outcome must be one of {sorted(SERIES_OUTCOMES)}")
    handoff_sha256 = predecessor.get("handoff_sha256")
    if handoff_sha256 != "" and (
        not isinstance(handoff_sha256, str) or not SHA256_HEX.fullmatch(handoff_sha256)
    ):
        errors.append(
            f"{prefix}.handoff_sha256 must be 64 lowercase hex characters or an empty string"
        )
    return errors


def series_errors(series: Any) -> list[str]:
    """Validate the optional top-level `series` block, present-only like the analytical
    exception.
    """
    prefix = "series"
    if not isinstance(series, dict):
        return [f"{prefix} must be an object"]
    errors: list[str] = []
    if set(series) - SERIES_KEYS:
        errors.append(f"{prefix} has unknown keys: {sorted(set(series) - SERIES_KEYS)}")
    if not stable_id(series.get("series_id")):
        errors.append(f"{prefix}.series_id must be a stable bounded identifier")
    slice_value: Any = series.get("slice")
    valid_slice = (
        isinstance(slice_value, int) and not isinstance(slice_value, bool) and slice_value >= 1
    )
    if not valid_slice:
        errors.append(f"{prefix}.slice must be an integer >= 1")
    if not isinstance(series.get("final"), bool):
        errors.append(f"{prefix}.final must be a boolean")
    commands = series.get("end_verification_commands")
    if (
        not isinstance(commands, list)
        or not 1 <= len(commands) <= 4
        or not all(nonempty_string_in_range(command, 1, 480) for command in commands)
    ):
        errors.append(
            f"{prefix}.end_verification_commands must be an array of 1 to 4 non-empty "
            "strings from 1 to 480 characters"
        )
    has_predecessor = "predecessor" in series
    if valid_slice and slice_value == 1 and has_predecessor:
        errors.append(f"{prefix}.predecessor is forbidden at slice 1")
    elif valid_slice and slice_value > 1 and not has_predecessor:
        errors.append(f"{prefix}.predecessor is required when slice > 1")
    if has_predecessor:
        errors.extend(predecessor_errors(series["predecessor"]))
    return errors


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
        "warnings": warnings,
        "standard_ready_ratio": ratio,
        "ready_weight": ready_weight,
        "total_weight": total_weight,
        "analytical_heavy_exception": exception_valid,
        "errors": errors,
        "cost_advisory": advisory or cost_advisory({}, []),
    }


def is_contract_version(value: Any) -> bool:
    return isinstance(value, int) and value == CONTRACT_VERSION


def _plan_field_errors(plan: dict[str, Any], errors: list[str]) -> None:
    for field in PLAN_REQUIRED:
        if field not in plan:
            errors.append(f"{field} is required for contract version {CONTRACT_VERSION}")
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


def _work_unit_sections(
    units: list[Any], errors: list[str]
) -> tuple[dict[str, int], dict[str, tuple[int, dict[str, Any]]]]:
    unit_sizes: dict[str, int] = {}
    unit_records: dict[str, tuple[int, dict[str, Any]]] = {}
    cohesive_outcomes: set[str] = set()
    for index, unit in enumerate(units):
        prefix = f"work_units[{index}]"
        if not isinstance(unit, dict):
            errors.append(f"{prefix} must be an object")
            continue
        unit_id = unit.get("id")
        size: Any = unit.get("original_size")
        if not stable_id(unit_id):
            errors.append(f"{prefix}.id must be a stable bounded identifier")
        elif unit_id in unit_sizes:
            errors.append(f"duplicate work unit id: {unit_id}")
        elif hashable(size) not in SIZES:
            errors.append(f"{prefix}.original_size must be small, medium, or large")
        else:
            unit_sizes[unit_id] = SIZES[size]
            unit_records[unit_id] = (index, unit)
        outcome = normalized_outcome(unit.get("cohesive_outcome"))
        if outcome is None:
            errors.append(
                f"{prefix}.cohesive_outcome must be a non-empty string from 1 to 240 characters"
            )
        elif outcome in cohesive_outcomes:
            errors.append(f"duplicate normalized cohesive_outcome: {outcome}")
        else:
            cohesive_outcomes.add(outcome)
        if not isinstance(unit.get("decomposition"), dict):
            errors.append(f"{prefix}.decomposition must be an object")
    return unit_sizes, unit_records


def _selective_audit_errors(prefix: str, audit: Any, errors: list[str]) -> None:
    if not isinstance(audit, dict):
        errors.append(f"{prefix}.selective_audit must be an object")
        return
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
    if hashable(audit.get("owner")) not in AUDIT_OWNERS:
        errors.append(f"{prefix}.selective_audit.owner must be an owning audit")
    question = audit.get("question")
    if vague_audit_question(question):
        errors.append(f"{prefix}.selective_audit.question must be bounded")


def _leaf_declaration_errors(
    prefix: str,
    leaf: dict[str, Any],
    strict: bool,
    admission: bool,
    errors: list[str],
) -> None:
    if strict:
        if not safe_exact_write_set(leaf):
            errors.append(
                f"{prefix}.write_set must be a non-empty exact path list without glob characters "
                "under strict precision"
            )
        if not exact_path_list(leaf.get("read_set"), non_empty=True):
            errors.append(
                f"{prefix}.read_set must be a non-empty exact path list without glob characters "
                "under strict precision"
            )
    if admission:
        for field in ("read_set", "write_set"):
            errors.extend(f"{prefix}.{error}" for error in declared_path_set_errors(leaf, field))
        if leaf.get("write_set") == [] and leaf.get("read_set", []) == []:
            errors.append(f"{prefix}.read_set and {prefix}.write_set cannot both be empty")
        if nonempty(leaf.get("worktree_owner")) and not valid_branch_name(
            leaf.get("worktree_owner")
        ):
            errors.append(f"{prefix}.worktree_owner must be a valid git branch name")
        if has_placeholder_decision(leaf.get("settled_decisions")):
            errors.append(f"{prefix}.settled_decisions cannot contain a standalone placeholder")
        command = leaf.get("acceptance_command")
        if isinstance(command, str) and command.strip().lower() in NOOP_ACCEPTANCE_COMMANDS:
            errors.append(f"{prefix}.acceptance_command cannot be a known no-op command")
    if (
        isinstance(leaf.get("stop_conditions"), list)
        and "missing_load_bearing_information" not in leaf["stop_conditions"]
    ):
        errors.append(f"{prefix}.stop_conditions must include missing_load_bearing_information")
    if "changeset_budget" in leaf:
        errors.extend(f"{prefix}.{error}" for error in changeset_budget_errors(leaf))


def _leaf_contract_errors(prefix: str, leaf: dict[str, Any], errors: list[str]) -> None:
    if hashable(leaf.get("size")) not in SIZES:
        errors.append(f"{prefix}.size must be small, medium, or large")
    if hashable(leaf.get("portable_tier")) not in TIERS:
        errors.append(f"{prefix}.portable_tier must be mechanical, standard, analytical, or deep")
    for field in ("model", "model_override", "reasoning_effort", "reasoning_effort_override"):
        if field in leaf:
            errors.append(
                f"{prefix}.{field} is host-adapter controlled; select portable_tier instead"
            )
    if (
        not isinstance(leaf.get("acceptance_command"), str)
        or not leaf.get("acceptance_command", "").strip()
    ):
        errors.append(f"{prefix}.acceptance_command must be exactly one non-empty command string")
    attempts = leaf.get("max_attempts")
    if not isinstance(attempts, int) or isinstance(attempts, bool) or not 1 <= attempts <= 5:
        errors.append(
            f"{prefix}.max_attempts must be an integer from 1 to 5 for "
            f"contract version {CONTRACT_VERSION}"
        )
    if leaf.get("return_contract") != RETURN_CONTRACT:
        errors.append(
            f"{prefix}.return_contract must be exactly {RETURN_CONTRACT} "
            f"for contract version {CONTRACT_VERSION}"
        )
    if not capability_requirements_valid(leaf.get("capability_requirements")):
        errors.append(
            f"{prefix}.capability_requirements must be an exact {CAPABILITY_BASELINE} "
            "requirements object"
        )
    if hashable(leaf.get("portable_tier")) in {"analytical", "deep"} and not nonempty(
        leaf.get("irreducible_unknown_or_risk")
    ):
        errors.append(
            f"{prefix}.irreducible_unknown_or_risk is required for analytical or deep work"
        )


def _leaf_sections(
    leaves: list[Any],
    unit_sizes: dict[str, int],
    strict: bool,
    admission: bool,
    errors: list[str],
) -> tuple[
    set[str],
    dict[str, list[dict[str, Any]]],
    dict[str, list[str]],
    dict[str, tuple[int, dict[str, Any]]],
    dict[str, list[str]],
]:
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
            if field == "read_set" and not strict:
                continue
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
        optional_read = not strict and "read_set" not in leaf
        for field in ("read_set", "write_set", "stop_conditions"):
            if field == "read_set" and optional_read:
                continue
            if not isinstance(leaf.get(field), list):
                errors.append(f"{prefix}.{field} must be an array")
        _leaf_declaration_errors(prefix, leaf, strict, admission, errors)
        _leaf_contract_errors(prefix, leaf, errors)
        unit_id: Any = leaf.get("work_unit_id")
        if hashable(unit_id) not in unit_sizes:
            errors.append(f"{prefix}.work_unit_id must name a declared work unit")
        else:
            unit_leaves[unit_id].append(leaf)
        audit = leaf.get("selective_audit")
        if audit is not None:
            audit_routes += 1
            _selective_audit_errors(prefix, audit, errors)
    if audit_routes > 1:
        errors.append("a plan may route initial inspection to exactly one owning audit")
    return leaf_ids, unit_leaves, dependencies, leaf_records, batches


def _batch_errors(
    batches: dict[str, list[str]],
    leaf_records: dict[str, tuple[int, dict[str, Any]]],
    dependencies: dict[str, list[str]],
    errors: list[str],
) -> None:
    for batch_id, members in batches.items():
        if not 2 <= len(members) <= 8:
            errors.append(
                f"batch {batch_id} has {len(members)} members; batches must have 2 to 8 members"
            )
        for member in members:
            if hashable(leaf_records[member][1].get("portable_tier")) not in BATCHABLE_TIERS:
                errors.append(
                    f"batch {batch_id} member {member} must have portable_tier mechanical "
                    "or standard"
                )
        owners = {hashable(leaf_records[member][1].get("worktree_owner")) for member in members}
        if len(owners) > 1:
            errors.append(f"batch {batch_id} members must share one worktree_owner")
        member_positions = {member: leaf_records[member][0] for member in members}
        member_set = set(members)
        for member in members:
            for dependency in dependencies.get(member, []):
                if (
                    dependency in member_set
                    and member_positions[dependency] >= member_positions[member]
                ):
                    errors.append(
                        f"batch {batch_id} member {member} depends on later-listed batch "
                        f"member {dependency}"
                    )


def _dependency_graph_errors(
    dependencies: dict[str, list[str]], leaf_ids: set[str], errors: list[str]
) -> None:
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


def _leaf_ordering_errors(
    dependencies: dict[str, list[str]],
    leaf_records: dict[str, tuple[int, dict[str, Any]]],
    errors: list[str],
) -> None:
    ordered_records = list(leaf_records.items())
    for first_position, (first_id, (_first_index, first)) in enumerate(ordered_records):
        for second_id, (_second_index, second) in ordered_records[first_position + 1 :]:
            ordered = leaves_are_ordered(first_id, second_id, dependencies, leaf_records)
            if not ordered and first.get("worktree_owner") == second.get("worktree_owner"):
                errors.append(
                    f"leaves {first_id} and {second_id} have shared worktree_owner without "
                    "dependency or batch ordering"
                )
            if not ordered and write_coverage_overlaps(first, second):
                errors.append(
                    f"leaves {first_id} and {second_id} have overlapping write coverage without "
                    "dependency or batch ordering"
                )


def _decomposition_errors(
    unit_leaves: dict[str, list[dict[str, Any]]],
    unit_records: dict[str, tuple[int, dict[str, Any]]],
    dependencies: dict[str, list[str]],
    errors: list[str],
) -> None:
    for unit_id, members in unit_leaves.items():
        unit_index, unit = unit_records[unit_id]
        prefix = f"work_units[{unit_index}].decomposition"
        decomposition = unit.get("decomposition")
        if not isinstance(decomposition, dict):
            continue
        shape = decomposition.get("shape")
        if hashable(shape) not in {"single", "parallel", "checkpointed"}:
            errors.append(f"{prefix}.shape must be single, parallel, or checkpointed")
            continue
        if shape == "single":
            if set(decomposition) != {"shape"}:
                errors.append(f"{prefix} for single must have exactly the key shape")
            if len(members) != 1:
                errors.append(f"work unit {unit_id} single decomposition must map exactly one leaf")
            continue
        if shape == "parallel":
            if set(decomposition) != {"shape", "basis", "rationale"}:
                errors.append(
                    f"{prefix} for parallel must have exactly shape, basis, and rationale"
                )
            if decomposition.get("basis") != "parallel_independence":
                errors.append(f"{prefix}.basis must be parallel_independence for parallel")
            if not nonempty_string_in_range(decomposition.get("rationale"), 1, 240):
                errors.append(
                    f"{prefix}.rationale must be a non-empty string from 1 to 240 characters"
                )
            if len(members) < 2:
                errors.append(
                    f"work unit {unit_id} parallel decomposition must map at least two leaves"
                )
            member_ids = {hashable(member.get("id")) for member in members}
            if any(
                set(dependencies.get(hashable(member.get("id")), [])) & member_ids
                for member in members
            ):
                errors.append(
                    f"work unit {unit_id} parallel leaves must have no intra-unit dependencies"
                )
            if len({hashable(member.get("worktree_owner")) for member in members}) != len(members):
                errors.append(
                    f"work unit {unit_id} parallel leaves must have distinct worktree_owner values"
                )
            for member_index, member in enumerate(members):
                if not safe_exact_write_set(member):
                    errors.append(
                        f"work unit {unit_id} parallel leaves must have exact safe write_set paths"
                    )
                for other in members[member_index + 1 :]:
                    if normalized_writes(member) & normalized_writes(other):
                        errors.append(
                            f"work unit {unit_id} parallel leaves must have pairwise-disjoint "
                            "write_set values"
                        )
            batches_in_unit = [
                member.get("batch") for member in members if stable_id(member.get("batch"))
            ]
            if len(batches_in_unit) != len(set(batches_in_unit)):
                errors.append(f"work unit {unit_id} parallel leaves must not share a batch")
            continue
        if set(decomposition) != {"shape", "basis", "rationale"}:
            errors.append(
                f"{prefix} for checkpointed must have exactly shape, basis, and rationale"
            )
        if hashable(decomposition.get("basis")) not in {"failure_isolation", "rollback_boundary"}:
            errors.append(
                f"{prefix}.basis must be failure_isolation or rollback_boundary for checkpointed"
            )
        if not nonempty_string_in_range(decomposition.get("rationale"), 1, 240):
            errors.append(f"{prefix}.rationale must be a non-empty string from 1 to 240 characters")
        if len(members) < 2:
            errors.append(
                f"work unit {unit_id} checkpointed decomposition must map at least two leaves"
            )
        member_ids = {hashable(item.get("id")) for item in members}
        for member_index, member in enumerate(members):
            intra = [
                dep for dep in dependencies.get(hashable(member.get("id")), []) if dep in member_ids
            ]
            expected = [] if member_index == 0 else [members[member_index - 1].get("id")]
            if intra != expected:
                errors.append(
                    f"work unit {unit_id} checkpointed leaves must form one linear ordered "
                    "dependency chain"
                )
                break


def _standard_ready_ratio(
    plan: dict[str, Any],
    unit_sizes: dict[str, int],
    unit_leaves: dict[str, list[dict[str, Any]]],
    errors: list[str],
) -> tuple[float, int, int, bool]:
    ready_weight = 0
    total_weight = sum(unit_sizes.values())
    for unit_id, weight in unit_sizes.items():
        members = unit_leaves[unit_id]
        if not members:
            errors.append(f"work unit {unit_id} has no leaves")
            continue
        if all(
            hashable(member.get("portable_tier")) in {"mechanical", "standard"}
            for member in members
        ):
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
    return ratio, ready_weight, total_weight, exception_valid


def _pin_findings(
    leaves: list[Any],
    pin_roots: list[str],
    repo_root: Path | None,
    strict: bool,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    scan = pin_scan(leaves, pin_roots, repo_root or Path.cwd())
    for leaf_id, paths in scan["leaves"].items():
        for path in paths:
            message = (
                f"PLANSCOPE-UNOWNED-PIN: {leaf_id}: {path} pins a write path but no leaf write_set "
                "owns it"
            )
            (errors if strict else warnings).append(message)
    return scan


def validate(
    plan: Any,
    capability_binding: Any = None,
    *,
    admission: bool = True,
    pin_roots: list[str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, dict):
        return contract_result(None, False, warnings, ["plan must be an object"])
    if "version" in plan:
        errors.append("version is not a valid plan discriminator; use `contract_version`")
    if not is_contract_version(plan.get("contract_version")):
        errors.append(RETIRED_VERSIONS_ERROR)
        result = contract_result(None, False, warnings, errors)
        result["plan_sha256"] = canonical_plan_sha256(plan)
        return result
    _plan_field_errors(plan, errors)
    if admission and has_placeholder_decision(plan.get("approved_decisions")):
        errors.append("approved_decisions cannot contain a standalone placeholder")
    precision = plan.get("precision", "standard")
    if "precision" in plan and precision not in PRECISION_MODES:
        errors.append("precision must be standard or strict")
    strict = precision == "strict"
    leaves = plan.get("leaves")
    units = plan.get("work_units")
    if not isinstance(leaves, list) or not leaves:
        errors.append("leaves must be a non-empty array")
        leaves = []
    if not isinstance(units, list) or not units:
        errors.append("work_units must be a non-empty array")
        units = []

    unit_sizes, unit_records = _work_unit_sections(units, errors)
    leaf_ids, unit_leaves, dependencies, leaf_records, batches = _leaf_sections(
        leaves, unit_sizes, strict, admission, errors
    )
    _batch_errors(batches, leaf_records, dependencies, errors)
    _dependency_graph_errors(dependencies, leaf_ids, errors)
    if admission:
        _leaf_ordering_errors(dependencies, leaf_records, errors)
    _decomposition_errors(unit_leaves, unit_records, dependencies, errors)
    ratio, ready_weight, total_weight, exception_valid = _standard_ready_ratio(
        plan, unit_sizes, unit_leaves, errors
    )
    if "verification" in plan and not (
        isinstance(plan["verification"], str) and plan["verification"] in VERIFICATION_MODES
    ):
        errors.append("verification must be per-leaf or closeout-only")
    series = plan.get("series")
    if series is not None:
        errors.extend(series_errors(series))
    scan = None
    if pin_roots and not errors:
        scan = _pin_findings(leaves, pin_roots, repo_root, strict, errors, warnings)
    binding_matches = capability_binding_matches(plan, leaves, capability_binding)
    if not binding_matches:
        warnings.append("blocked:capability_unavailable")
    advisory = bounded_cost_advisory(cost_advisory(plan, leaves))
    result = contract_result(
        CONTRACT_VERSION,
        binding_matches,
        warnings,
        errors,
        True,
        ratio,
        ready_weight,
        total_weight,
        exception_valid,
        advisory,
    )
    result["plan_sha256"] = canonical_plan_sha256(plan)
    if scan is not None:
        result["pin_scan"] = scan
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
    validate_parser.add_argument(
        "--pin-roots",
        nargs="+",
        metavar="ROOT",
        help="repository-relative roots to scan for unowned pinning tests",
    )
    validate_parser.add_argument(
        "--repo-root", type=Path, help="repository root for --pin-roots (default: cwd)"
    )
    validate_parser.add_argument("--emit-handoff", choices=("reference", "inline"))
    validate_parser.add_argument("--handoff-format", choices=("json", "block"), default="json")
    resolve_parser = subparsers.add_parser("resolve-handoff", help="resolve an approval handoff")
    resolve_parser.add_argument("handoff", type=str)
    args = parser.parse_args(argv)
    if args.command == "validate" and args.handoff_format == "block" and not args.emit_handoff:
        parser.error("--handoff-format block requires --emit-handoff")
    handoff_mode = args.command == "resolve-handoff" or bool(args.emit_handoff)
    try:
        if args.command == "resolve-handoff":
            handoff = _read_json_source(args.handoff, 4 * HANDOFF_INLINE_MAX)
            plan, validation = resolve_handoff(handoff)
            result = {"plan": plan, "validation": validation}
        else:
            plan = _read_json_source(str(args.plan), 4 * HANDOFF_PLAN_MAX if handoff_mode else None)
            binding = (
                _read_json_source(str(args.capability_binding))
                if args.capability_binding is not None
                else None
            )
            result = validate(
                plan, capability_binding=binding, pin_roots=args.pin_roots, repo_root=args.repo_root
            )
            result["plan_sha256"] = canonical_plan_sha256(plan)
            if args.emit_handoff:
                result["handoff"] = emit_handoff(plan, args.emit_handoff, str(args.plan))
                if args.handoff_format == "block":
                    print(render_handoff_block(result["handoff"]))
                    return 0
    except HandoffError as error:
        print(
            json.dumps(error_result(error.code, str(error)), sort_keys=True, separators=(",", ":"))
        )
        return 1
    except (OSError, ValueError, RecursionError) as error:
        result = (
            error_result("blocked:missing_input", "unreadable or invalid JSON input")
            if handoff_mode
            else contract_result(None, False, [], [str(error)])
        )
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if args.command == "resolve-handoff" or result["valid"] else 1
