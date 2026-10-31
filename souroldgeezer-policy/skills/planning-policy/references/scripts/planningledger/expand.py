"""Deterministic plan expander: one template plus a JSONL rule index become v5 plan slices.

A pure authoring aid. It never changes the validator, the ledger, approval, or series
semantics: every emitted plan is run through ``plancontract.validate(plan, admission=True)``
and the predecessor run is read through ``series.load_predecessor_run`` without writing.
"""

from __future__ import annotations

import argparse
import heapq
import json
import string
import sys
from dataclasses import dataclass
from pathlib import Path

from . import core, plancontract, series, store
from .core import Error, JsonObject, JsonValue, UsageError

__all__ = [
    "EXPANDER_VERSION",
    "TEMPLATE_SCHEMA",
    "PARTITION_SCHEMA",
    "MAX_TEMPLATE_BYTES",
    "MAX_INDEX_BYTES",
    "InputErrors",
    "Rule",
    "Expansion",
    "load_template",
    "load_index",
    "build",
    "emit_slice",
    "partition_summary",
    "main",
]

EXPANDER_VERSION = "planning-plan-expander-v1"
TEMPLATE_SCHEMA = "planning-expansion-template-v1"
PARTITION_SCHEMA = "planning-expansion-partition-v1"
MAX_TEMPLATE_BYTES = 256 * 1024
MAX_INDEX_BYTES = 8 * 1024 * 1024
MAX_ERRORS = 40
BATCH_MAX = 8
PLACEHOLDERS = frozenset({"id", "type", "spec"})
TEMPLATE_KEYS = {
    "schema",
    "objective",
    "scope_summary",
    "approved_decisions",
    "series",
    "owner_prefix",
    "types",
}
TEMPLATE_OPTIONAL = {"precision", "verification"}
SERIES_TEMPLATE_KEYS = {"series_id", "end_verification_commands", "max_leaves"}
TYPE_REQUIRED = {
    "task",
    "boundary",
    "write_set",
    "read_set_extra",
    "acceptance_command",
    "size",
    "portable_tier",
    "max_attempts",
    "settled_decisions",
    "capability_requirements",
    "batch",
}
TYPE_OPTIONAL = {"irreducible_unknown_or_risk", "exemplar"}
EXEMPLAR_TIERS = {"standard", "analytical"}
RULE_KEYS = {"id", "type", "deps", "spec", "refs"}
# Worst-case predecessor, so the real one can never push an accepted slice over the cap.
STUB_PREDECESSOR: JsonObject = {
    "plan_id": "a" * 64,
    "run_id": "00000000-0000-4000-8000-000000000000",
    "plan_sha256": "0" * 64,
    "outcome": "abandoned",
    "handoff_sha256": "0" * 64,
}


class InputErrors(Error):
    """An input or validation refusal carrying every collected error."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors[:3]))
        self.errors = errors[:MAX_ERRORS]


@dataclass(frozen=True)
class Rule:
    line: int
    id: str
    type: str
    deps: tuple[str, ...]
    spec: str
    refs: tuple[str, ...]
    exemplar: bool


@dataclass
class Expansion:
    template: JsonObject
    raw_rules: list[JsonObject]
    rules: list[Rule]
    order: list[Rule]
    position: dict[str, int]
    exemplars: dict[str, Rule]
    generator_sha256: str
    max_leaves: int
    slices: list[tuple[int, int]]


# -- reading ------------------------------------------------------------------------------


def _read(path: str | Path, limit: int, label: str) -> bytes:
    return core.read_bounded_bytes(
        path, limit, f"cannot read {label} {path}", f"{label} exceeds {limit} bytes"
    )


def load_template(path: str | Path) -> JsonObject:
    raw = _read(path, MAX_TEMPLATE_BYTES, "template")
    try:
        value: JsonValue = json.loads(raw)
    except RecursionError as exc:
        raise InputErrors(["template is nested too deeply"]) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputErrors([f"template is not valid JSON: {exc}"]) from exc
    errors = _template_errors(value)
    if errors:
        raise InputErrors(errors)
    assert isinstance(value, dict)
    return value


def _is_text(value: JsonValue) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_int(value: JsonValue) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _template_text_errors(text: JsonValue, path: str) -> list[str]:
    if not isinstance(text, str):
        return [f"{path} must be a string template"]
    try:
        fields = list(string.Formatter().parse(text))
    except ValueError as exc:
        return [f"{path} is a malformed template: {exc}"]
    errors = []
    for _literal, name, spec, conversion in fields:
        if name is None:
            continue
        if name not in PLACEHOLDERS:
            errors.append(f"{path} has unknown placeholder {{{name}}}; allowed: id, type, spec")
        elif spec or conversion:
            errors.append(f"{path} placeholder {{{name}}} takes no conversion or format spec")
    return errors


def _text_list_errors(value: JsonValue, path: str, allow_empty: bool) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        return [
            f"{path} must be {'an' if allow_empty else 'a non-empty'} array of string templates"
        ]
    return [e for i, item in enumerate(value) for e in _template_text_errors(item, f"{path}[{i}]")]


def _exemplar_errors(exemplar: JsonValue, path: str) -> list[str]:
    if not isinstance(exemplar, dict):
        return [f"{path} must be an object"]
    unknown = set(exemplar) - {"portable_tier", "irreducible_unknown_or_risk"}
    errors = [f"{path} has unknown keys {sorted(unknown)}"] if unknown else []
    tier = exemplar.get("portable_tier")
    if plancontract.hashable(tier) not in EXEMPLAR_TIERS:
        return [*errors, f"{path}.portable_tier must be standard or analytical"]
    return [*errors, *_risk_errors(exemplar, tier == "analytical", path)]


def _risk_errors(spec: JsonObject, required: bool, path: str) -> list[str]:
    key = f"{path}.irreducible_unknown_or_risk"
    if "irreducible_unknown_or_risk" in spec:
        if not required:
            return [f"{key} is forbidden unless the tier is analytical"]
        return _template_text_errors(spec["irreducible_unknown_or_risk"], key)
    return [f"{key} is required for an analytical tier"] if required else []


def _type_errors(name: str, spec: JsonValue) -> list[str]:
    path = f"types.{name}"
    if not plancontract.stable_id(name):
        return [f"{path}: type name must be a stable bounded identifier"]
    if not isinstance(spec, dict):
        return [f"{path} must be an object"]
    errors = []
    if set(spec) - TYPE_REQUIRED - TYPE_OPTIONAL:
        errors.append(
            f"{path} has unknown keys {sorted(set(spec) - TYPE_REQUIRED - TYPE_OPTIONAL)}"
        )
    if TYPE_REQUIRED - set(spec):
        return [*errors, f"{path} is missing keys {sorted(TYPE_REQUIRED - set(spec))}"]
    for key in ("task", "boundary", "acceptance_command"):
        errors += _template_text_errors(spec[key], f"{path}.{key}")
    errors += _text_list_errors(spec["write_set"], f"{path}.write_set", False)
    errors += _text_list_errors(spec["read_set_extra"], f"{path}.read_set_extra", True)
    if plancontract.hashable(spec["size"]) not in plancontract.SIZES:
        errors.append(f"{path}.size must be small, medium, or large")
    tier = plancontract.hashable(spec["portable_tier"])
    if tier not in plancontract.TIERS:
        errors.append(f"{path}.portable_tier is not a known tier")
    if not _is_int(spec["max_attempts"]):
        errors.append(f"{path}.max_attempts must be an integer")
    decisions = spec["settled_decisions"]
    if (
        not isinstance(decisions, dict)
        or not decisions
        or not all(_is_text(v) for v in decisions.values())
    ):
        errors.append(f"{path}.settled_decisions must be a non-empty object of non-empty strings")
    elif "exemplar" in spec and "exemplar_pattern" in decisions:
        errors.append(
            f"{path}.settled_decisions must not contain exemplar_pattern; the expander owns it"
        )
    if not isinstance(spec["batch"], bool):
        errors.append(f"{path}.batch must be a boolean")
    requirements = spec["capability_requirements"]
    if not plancontract.capability_requirements_valid(requirements):
        errors.append(f"{path}.capability_requirements is not a valid requirements object")
    elif spec["portable_tier"] == "mechanical" and any(
        item["kind"] == "skill" for item in requirements["additional"]
    ):
        errors.append(
            f"{path}.capability_requirements lists a skill, but mechanical leaves run in Claude "
            "mechanical wrappers that lack the Skill tool"
        )
    if "exemplar" in spec:
        errors += _exemplar_errors(spec["exemplar"], f"{path}.exemplar")
        if spec["portable_tier"] != "mechanical":
            errors.append(
                f"{path}.portable_tier must be mechanical: followers of an exemplar run at "
                "mechanical"
            )
    if tier in plancontract.TIERS:
        errors += _risk_errors(spec, tier in {"analytical", "deep"}, path)
    return errors


def _template_errors(template: JsonValue) -> list[str]:
    if not isinstance(template, dict):
        return ["template must be an object"]
    errors = []
    unknown = set(template) - TEMPLATE_KEYS - TEMPLATE_OPTIONAL
    if unknown:
        errors.append(f"template has unknown keys {sorted(unknown)}")
    if TEMPLATE_KEYS - set(template):
        return [*errors, f"template is missing keys {sorted(TEMPLATE_KEYS - set(template))}"]
    if template["schema"] != TEMPLATE_SCHEMA:
        errors.append(f"schema must be {TEMPLATE_SCHEMA}")
    if not isinstance(template["objective"], str) or not isinstance(template["scope_summary"], str):
        errors.append("objective and scope_summary must be strings")
    if not isinstance(template["approved_decisions"], list):
        errors.append("approved_decisions must be an array")
    if not isinstance(template["owner_prefix"], str):
        errors.append("owner_prefix must be a string")
    elif not plancontract.valid_branch_name(template["owner_prefix"] + "x"):
        errors.append("owner_prefix does not form a valid git branch name")
    errors += _series_errors(template["series"])
    types = template["types"]
    if not isinstance(types, dict) or not types:
        errors.append("types must be a non-empty object")
    else:
        for name, spec in types.items():
            errors += _type_errors(name, spec)
    return errors


def _series_errors(block: JsonValue) -> list[str]:
    if not isinstance(block, dict) or set(block) - SERIES_TEMPLATE_KEYS:
        return [f"series must be an object with keys {sorted(SERIES_TEMPLATE_KEYS)}"]
    errors = []
    if not plancontract.stable_id(block.get("series_id")):
        errors.append("series.series_id must be a stable bounded identifier")
    if "end_verification_commands" not in block:
        errors.append("series.end_verification_commands is required")
    limit = block.get("max_leaves", plancontract.PLAN_SCALE_LEAF_LIMIT)
    if not _is_int(limit) or not 1 <= limit <= plancontract.PLAN_SCALE_LEAF_LIMIT:
        errors.append(
            f"series.max_leaves must be an integer from 1 to {plancontract.PLAN_SCALE_LEAF_LIMIT}"
        )
    return errors


def load_index(path: str | Path, template: JsonObject) -> list[JsonObject]:
    """Parse the JSONL index into raw rule objects, checking each line against the template."""
    raw = _read(path, MAX_INDEX_BYTES, "index")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputErrors(["index is not valid UTF-8"]) from exc
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    errors: list[str] = []
    rules: list[JsonObject] = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            errors.append(f"line {number}: blank line")
            continue
        try:
            value: JsonValue = json.loads(line)
        except RecursionError:
            errors.append(f"line {number}: nested too deeply")
            continue
        except json.JSONDecodeError as exc:
            errors.append(f"line {number}: not valid JSON: {exc.msg}")
            continue
        problems = _rule_errors(value, template)
        errors += [f"line {number}: {problem}" for problem in problems]
        if not problems:
            rules.append({**value, "_line": number})
    if not lines and not errors:
        errors.append("index has no rules")
    if errors:
        raise InputErrors(errors)
    return rules


def _rule_errors(rule: JsonValue, template: JsonObject) -> list[str]:
    if not isinstance(rule, dict):
        return ["rule must be an object"]
    unknown = set(rule) - RULE_KEYS - {"exemplar"}
    if unknown or RULE_KEYS - set(rule):
        return [
            f"rule has unknown keys {sorted(unknown)} or misses {sorted(RULE_KEYS - set(rule))}"
        ]
    errors = []
    if not plancontract.stable_id(rule["id"]):
        errors.append("id must be a stable bounded identifier")
    elif not plancontract.valid_branch_name(template["owner_prefix"] + rule["id"]):
        errors.append(f"owner_prefix + id {rule['id']} is not a valid git branch name")
    deps = rule["deps"]
    if not isinstance(deps, list) or not all(plancontract.stable_id(d) for d in deps):
        errors.append("deps must be an array of rule ids")
    elif len(set(deps)) != len(deps) or rule["id"] in deps:
        errors.append(f"{rule['id']} depends on itself or lists a dependency twice")
    if not isinstance(rule["type"], str):
        errors.append("type must be a string")
    elif rule["type"] not in template["types"]:
        errors.append(f"unknown type {rule['type']}")
    paths = [rule["spec"], *rule["refs"]] if isinstance(rule["refs"], list) else [rule["spec"]]
    if not isinstance(rule["refs"], list) or not all(
        plancontract.safe_repository_path(p) for p in paths
    ):
        errors.append("spec and refs must be repository-relative path strings")
    if "exemplar" in rule:
        if rule["exemplar"] is not True:
            errors.append("exemplar must be true when present")
        elif isinstance(rule["type"], str) and "exemplar" not in template["types"].get(
            rule["type"], {}
        ):
            errors.append(f"type {rule['type']} declares no exemplar")
    return errors


# -- ordering -----------------------------------------------------------------------------


def _cycle(remaining: dict[str, Rule]) -> list[str]:
    """One concrete cycle: every remaining rule still waits on another remaining rule."""
    node = next(iter(remaining))
    seen: list[str] = []
    while node not in seen:
        seen.append(node)
        node = next(dep for dep in remaining[node].deps if dep in remaining)
    return [*seen[seen.index(node) :], node]


def _base_order(rules: list[Rule]) -> list[Rule]:
    by_id = {rule.id: rule for rule in rules}
    waiting = {rule.id: sum(1 for dep in rule.deps if dep in by_id) for rule in rules}
    dependents: dict[str, list[Rule]] = {}
    for rule in rules:
        for dep in rule.deps:
            dependents.setdefault(dep, []).append(rule)
    ready = [(rule.line, rule.id) for rule in rules if not waiting[rule.id]]
    heapq.heapify(ready)
    ordered: list[Rule] = []
    while ready:
        rule = by_id[heapq.heappop(ready)[1]]
        ordered.append(rule)
        for dependent in dependents.get(rule.id, []):
            waiting[dependent.id] -= 1
            if not waiting[dependent.id]:
                heapq.heappush(ready, (dependent.line, dependent.id))
    if len(ordered) != len(rules):
        done = {rule.id for rule in ordered}
        cycle = _cycle({rule.id: rule for rule in rules if rule.id not in done})
        raise InputErrors([f"dependency cycle: {' -> '.join(cycle)}"])
    return ordered


def _rules(raw_rules: list[JsonObject], template: JsonObject) -> list[Rule]:
    rules = [
        Rule(
            r["_line"],
            r["id"],
            r["type"],
            tuple(r["deps"]),
            r["spec"],
            tuple(r["refs"]),
            r.get("exemplar") is True,
        )
        for r in raw_rules
    ]
    errors, seen = [], set()
    for rule in rules:
        if rule.id in seen:
            errors.append(f"line {rule.line}: duplicate id {rule.id}")
        seen.add(rule.id)
    for rule in rules:
        errors += [f"line {rule.line}: unknown dependency {d}" for d in rule.deps if d not in seen]
    marked: dict[str, int] = {}
    for rule in rules:
        if rule.exemplar:
            if rule.type in marked:
                errors.append(f"line {rule.line}: more than one exemplar for type {rule.type}")
            marked.setdefault(rule.type, rule.line)
    if errors:
        raise InputErrors(errors)
    return rules


def _before_exemplar_error(by_id: dict[str, Rule], rule: Rule, exemplar: Rule) -> str:
    head = f"rule {rule.id} (type {rule.type})"
    pending, seen = list(exemplar.deps), set()
    while pending:
        current = pending.pop()
        if current not in seen:
            seen.add(current)
            pending.extend(by_id[current].deps)
    if rule.id in seen:
        return f"{head} is a dependency of exemplar {exemplar.id}; choose another exemplar"
    return (
        f"{head} is ordered before its exemplar {exemplar.id}; add {exemplar.id} to its deps "
        "or choose another exemplar"
    )


def build(template: JsonObject, raw_rules: list[JsonObject]) -> Expansion:
    """Order, choose exemplars, check renderings, and partition; a pure function of its input."""
    rules = _rules(raw_rules, template)
    base = _base_order(rules)
    exemplars: dict[str, Rule] = {}
    for rule in base:
        if "exemplar" in template["types"][rule.type] and (
            rule.exemplar or rule.type not in exemplars
        ):
            exemplars[rule.type] = rule
        # A marked rule wins; otherwise the first of its type in base order stays.
    by_id = {rule.id: rule for rule in rules}
    front: set[str] = set()
    pending = [rule.id for rule in exemplars.values()]
    while pending:
        current = pending.pop()
        if current not in front:
            front.add(current)
            pending.extend(by_id[current].deps)
    order = [r for r in base if r.id in front] + [r for r in base if r.id not in front]
    position = {rule.id: index for index, rule in enumerate(order)}
    errors = []
    for rule in order:
        ex = exemplars.get(rule.type)
        if ex is not None and ex is not rule and position[rule.id] < position[ex.id]:
            errors.append(_before_exemplar_error(by_id, rule, ex))
    limit = template["series"].get("max_leaves", plancontract.PLAN_SCALE_LEAF_LIMIT)
    expansion = Expansion(
        template,
        raw_rules,
        rules,
        order,
        position,
        exemplars,
        core.digest(
            {
                "expander": EXPANDER_VERSION,
                "template": template,
                "index": [{k: v for k, v in r.items() if k != "_line"} for r in raw_rules],
            }
        ),
        limit,
        [],
    )
    for rule in rules:
        try:
            _render(expansion, rule)
        except InputErrors as exc:
            errors += exc.errors
    if errors:
        raise InputErrors(errors)
    expansion.slices = _partition(expansion)
    errors = _slice_errors(expansion)
    if errors:
        raise InputErrors(errors)
    return expansion


def _slice_errors(expansion: Expansion) -> list[str]:
    """Validator errors of every slice, so a partition never approves a refusable slice."""
    errors: list[str] = []
    count = len(expansion.slices)
    for number, (start, end) in enumerate(expansion.slices, 1):
        stub = STUB_PREDECESSOR if number > 1 else None
        plan = _build_plan(expansion, start, end - start, number, number == count, stub)
        result = plancontract.validate(plan, admission=True)
        errors += [f"slice {number}: {error}" for error in result["errors"]]
    return errors


# -- rendering ----------------------------------------------------------------------------


def _fill(text: str, rule: Rule, path: str) -> str:
    value = text.format(id=rule.id, type=rule.type, spec=rule.spec)
    if not value.strip():
        raise InputErrors([f"{path} renders empty or whitespace-only for rule {rule.id}"])
    return value


def _render(expansion: Expansion, rule: Rule) -> JsonObject:
    spec = expansion.template["types"][rule.type]
    base = f"types.{rule.type}"
    risk_source = spec
    if "exemplar" in spec:
        exemplar = rule is expansion.exemplars[rule.type]
        risk_source = spec["exemplar"] if exemplar else {}
    rendered: JsonObject = {
        "task": _fill(spec["task"], rule, f"{base}.task"),
        "boundary": _fill(spec["boundary"], rule, f"{base}.boundary"),
        "acceptance_command": _fill(spec["acceptance_command"], rule, f"{base}.acceptance_command"),
        "write_set": [
            _fill(t, rule, f"{base}.write_set[{i}]") for i, t in enumerate(spec["write_set"])
        ],
        "read_set_extra": [
            _fill(t, rule, f"{base}.read_set_extra[{i}]")
            for i, t in enumerate(spec["read_set_extra"])
        ],
    }
    if "irreducible_unknown_or_risk" in risk_source:
        rendered["irreducible"] = _fill(
            risk_source["irreducible_unknown_or_risk"], rule, f"{base}.irreducible_unknown_or_risk"
        )
    return rendered


def _tier(expansion: Expansion, rule: Rule) -> str:
    spec = expansion.template["types"][rule.type]
    if "exemplar" not in spec:
        return str(spec["portable_tier"])
    return (
        str(spec["exemplar"]["portable_tier"])
        if rule is expansion.exemplars[rule.type]
        else "mechanical"
    )


def _unique(paths: list[str]) -> list[str]:
    return list(dict.fromkeys(paths))


def _leaf(expansion: Expansion, rule: Rule, start: int, end: int) -> JsonObject:
    spec = expansion.template["types"][rule.type]
    rendered = _render(expansion, rule)
    exemplar = expansion.exemplars.get(rule.type)
    follower = exemplar is not None and exemplar is not rule
    decisions = dict(spec["settled_decisions"])
    reads = [rule.spec, *rule.refs, *rendered["read_set_extra"]]
    dependencies = []
    for dep in rule.deps:
        where = expansion.position[dep]
        if where >= end:
            raise Error(f"internal error: {rule.id} depends on later rule {dep}")
        if where >= start:
            dependencies.append(dep)
    if follower:
        assert exemplar is not None
        paths = _render(expansion, exemplar)["write_set"]
        reads += paths
        decisions["exemplar_pattern"] = (
            f"follow the pattern exemplar {exemplar.id} landed in {', '.join(paths)}; "
            "do not re-derive it"
        )
        if start <= expansion.position[exemplar.id] < end and exemplar.id not in dependencies:
            dependencies.append(exemplar.id)
    leaf: JsonObject = {
        "id": rule.id,
        "work_unit_id": rule.id,
        "dependencies": dependencies,
        "task": rendered["task"],
        "boundary": rendered["boundary"],
        "read_set": _unique(reads),
        "write_set": rendered["write_set"],
        "settled_decisions": decisions,
        "size": spec["size"],
        "portable_tier": _tier(expansion, rule),
        "worktree_owner": expansion.template["owner_prefix"] + rule.id,
        "acceptance_command": rendered["acceptance_command"],
        "return_contract": plancontract.RETURN_CONTRACT,
        "stop_conditions": ["missing_load_bearing_information"],
        "max_attempts": spec["max_attempts"],
        "capability_requirements": spec["capability_requirements"],
    }
    if "irreducible" in rendered:
        leaf["irreducible_unknown_or_risk"] = rendered["irreducible"]
    return leaf


def _leader_runs(indices: list[int], leaves: list[JsonObject]) -> list[list[int]]:
    """Split consecutive leaves so no member waits on anything its run's first member does not.

    Ledger readiness checks only a batch leader's own dependencies, yet dispatch readies every
    member, so a member's dependencies outside the run must be a subset of the leader's.
    """
    runs: list[list[int]] = []
    for index in indices:
        dependencies = set(leaves[index]["dependencies"])
        if runs:
            members = {leaves[member]["id"] for member in runs[-1]}
            if dependencies - members <= set(leaves[runs[-1][0]]["dependencies"]):
                runs[-1].append(index)
                continue
        runs.append([index])
    return runs


def _batch_groups(
    expansion: Expansion, members: list[Rule], leaves: list[JsonObject]
) -> list[list[int]]:
    """Index groups of 2 to 8 same-type batchable leaves that may share one batch."""
    stretches: list[list[int]] = []
    previous = None
    for index, rule in enumerate(members):
        batchable = (
            expansion.template["types"][rule.type]["batch"]
            and leaves[index]["portable_tier"] in plancontract.BATCHABLE_TIERS
            and rule is not expansion.exemplars.get(rule.type)
        )
        if not batchable:
            previous = None
        elif previous == rule.type:
            stretches[-1].append(index)
        else:
            stretches.append([index])
            previous = rule.type
    groups: list[list[int]] = []
    for stretch in stretches:
        for run in _leader_runs(stretch, leaves):
            count = -(-len(run) // BATCH_MAX)
            size, extra = divmod(len(run), count)
            cursor = 0
            for group in range(count):
                take = size + (1 if group < extra else 0)
                for piece in _leader_runs(run[cursor : cursor + take], leaves):
                    groups.append(piece)
                cursor += take
    return [group for group in groups if len(group) > 1]


def _assign_batches(expansion: Expansion, members: list[Rule], leaves: list[JsonObject]) -> None:
    prefix = expansion.template["owner_prefix"]
    names = {leaf["id"] for leaf in leaves}
    owners = {leaf["worktree_owner"] for leaf in leaves}
    for number, group in enumerate(_batch_groups(expansion, members, leaves), 1):
        kind = members[group[0]].type
        for name in (f"{kind}-batch-{members[group[0]].id}", f"{kind}-batch-{number}"):
            if (
                plancontract.stable_id(name)
                and name not in names
                and prefix + name not in owners
                and plancontract.valid_branch_name(prefix + name)
            ):
                break
        else:
            raise InputErrors([f"cannot name a batch for type {kind} in this slice"])
        names.add(name)
        owners.add(prefix + name)
        for index in group:
            leaves[index]["batch"] = name
            leaves[index]["worktree_owner"] = prefix + name


def _build_plan(
    expansion: Expansion,
    start: int,
    take: int,
    number: int,
    final: bool,
    predecessor: JsonObject | None,
) -> JsonObject:
    template = expansion.template
    members = expansion.order[start : start + take]
    leaves = [_leaf(expansion, rule, start, start + take) for rule in members]
    _assign_batches(expansion, members, leaves)
    block: JsonObject = {
        "series_id": template["series"]["series_id"],
        "slice": number,
        "final": final,
        "end_verification_commands": template["series"]["end_verification_commands"],
    }
    if predecessor is not None:
        block["predecessor"] = predecessor
    plan: JsonObject = {
        "contract_version": plancontract.CONTRACT_VERSION,
        "precision": template.get("precision", "strict"),
        "objective": template["objective"],
        "scope_summary": template["scope_summary"],
        "approved_decisions": template["approved_decisions"],
        "work_units": [
            {
                "id": rule.id,
                "original_size": leaf["size"],
                "cohesive_outcome": f"Land rule {rule.id} ({rule.type})",
                "decomposition": {"shape": "single"},
            }
            for rule, leaf in zip(members, leaves, strict=True)
        ],
        "leaves": leaves,
        "series": block,
    }
    if "verification" in template:
        plan["verification"] = template["verification"]
    return plan


def _partition(expansion: Expansion) -> list[tuple[int, int]]:
    total = len(expansion.order)
    slices: list[tuple[int, int]] = []
    start = 0
    while start < total:
        number = len(slices) + 1
        take = min(expansion.max_leaves, total - start)
        stub = STUB_PREDECESSOR if number > 1 else None
        while len(core.canon(_build_plan(expansion, start, take, number, False, stub))) > (
            plancontract.HANDOFF_PLAN_MAX
        ):
            if take == 1:
                raise InputErrors(
                    [
                        f"rule {expansion.order[start].id} alone exceeds the "
                        f"{plancontract.HANDOFF_PLAN_MAX}-byte plan cap"
                    ]
                )
            take -= 1
        slices.append((start, start + take))
        start += take
    return slices


def emit_slice(expansion: Expansion, number: int, predecessor: JsonObject | None) -> JsonObject:
    """The complete v5 plan for slice `number` (1-based); `predecessor` is required past slice 1."""
    if not 1 <= number <= len(expansion.slices):
        raise UsageError(f"slice must be from 1 to {len(expansion.slices)}")
    if (predecessor is None) == (number > 1):
        raise UsageError("a predecessor is required for slice > 1 and forbidden for slice 1")
    start, end = expansion.slices[number - 1]
    return _build_plan(
        expansion, start, end - start, number, number == len(expansion.slices), predecessor
    )


def partition_summary(expansion: Expansion) -> JsonObject:
    count = len(expansion.slices)
    return {
        "schema": PARTITION_SCHEMA,
        "generator_sha256": expansion.generator_sha256,
        "series_id": expansion.template["series"]["series_id"],
        "rule_count": len(expansion.rules),
        "slice_count": count,
        "exemplars": {name: rule.id for name, rule in sorted(expansion.exemplars.items())},
        "slices": [
            {
                "slice": n,
                "final": n == count,
                "leaf_count": end - start,
                "ids": [r.id for r in expansion.order[start:end]],
            }
            for n, (start, end) in enumerate(expansion.slices, 1)
        ],
    }


# -- command line -------------------------------------------------------------------------


def _load_run(ledger_root: Path, plan_id: str, run_id: str) -> tuple[JsonObject, JsonObject]:
    try:
        return series.load_predecessor_run(ledger_root, plan_id, run_id)
    except (Error, OSError, json.JSONDecodeError) as exc:
        raise InputErrors([f"cannot load predecessor run: {exc}"]) from exc


def _chain_errors(
    expansion: Expansion, checkpoint: JsonObject, plan: JsonObject, number: int
) -> str | None:
    """Why run `number` of the predecessor chain cannot be followed, or None."""
    label = f"predecessor slice {number}"
    block = plan.get("series") or {}
    if checkpoint.get("outcome") not in plancontract.SERIES_OUTCOMES:
        return f"{label} is not closed; close it before the next slice"
    wanted = expansion.template["series"]["series_id"]
    if block.get("series_id") != wanted:
        return f"{label} belongs to series {block.get('series_id')}, not {wanted}"
    if block.get("slice") != number:
        return f"{label} is recorded as slice {block.get('slice')}"
    if checkpoint["outcome"] != "completed":
        return (
            f"{label} closed {checkpoint['outcome']}, not completed; later slices assume its "
            "rules landed, so hand-groom the successor per plan-series.md "
            "'Successor on a blocked predecessor'"
        )
    if block.get("final"):
        return f"{label} is final; the series has ended"
    start, end = expansion.slices[number - 1]
    if [leaf["id"] for leaf in plan["leaves"]] != [r.id for r in expansion.order[start:end]]:
        return f"{label} does not match this partition (index changed?)"
    if number == 1 and "predecessor" in block:
        return f"{label} must have no predecessor"
    return None


def _predecessor(args: argparse.Namespace, expansion: Expansion) -> JsonObject:
    """The predecessor block for run k-1, after walking the whole chain back to slice 1."""
    ledger_root = store.root(args)
    plan_id, run_id = args.predecessor_plan_id, args.predecessor_run_id
    first: JsonObject | None = None
    for number in range(args.slice - 1, 0, -1):
        checkpoint, plan = _load_run(ledger_root, plan_id, run_id)
        problem = _chain_errors(expansion, checkpoint, plan, number)
        if problem:
            raise InputErrors([problem])
        if first is None:
            first = {
                "plan_id": args.predecessor_plan_id,
                "run_id": args.predecessor_run_id,
                "plan_sha256": checkpoint["plan_hash"],
                "outcome": checkpoint["outcome"],
                "handoff_sha256": checkpoint.get("series_handoff_sha256") or "",
            }
        link = plan["series"].get("predecessor") or {}
        plan_id, run_id = link.get("plan_id"), link.get("run_id")
    assert first is not None
    return first


def _usage(args: argparse.Namespace) -> None:
    given = (args.predecessor_plan_id is not None, args.predecessor_run_id is not None)
    if args.slice < 1:
        raise UsageError("--slice must be at least 1")
    if args.slice == 1 and any(given):
        raise UsageError("slice 1 takes no predecessor flags")
    if args.slice > 1 and not all(given):
        raise UsageError("slice > 1 requires --predecessor-plan-id and --predecessor-run-id")
    if args.slice > 1:
        if not plancontract.stable_id(args.predecessor_plan_id):
            raise UsageError("--predecessor-plan-id must be a stable id")
        try:
            core.uuid4(args.predecessor_run_id, "predecessor run id")
        except Error as exc:
            raise UsageError(str(exc)) from exc


def _run_slice(args: argparse.Namespace, expansion: Expansion) -> int:
    if args.slice > len(expansion.slices):
        raise UsageError(f"--slice must be from 1 to {len(expansion.slices)}")
    predecessor = _predecessor(args, expansion) if args.slice > 1 else None
    plan = emit_slice(expansion, args.slice, predecessor)
    result = plancontract.validate(plan, admission=True)
    if not result["valid"] or not result["approval_ready"]:
        raise InputErrors(list(result["errors"]) or ["plan is not approval ready"])
    payload = core.canon(plan) + b"\n"
    if not args.out:
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.flush()
        return 0
    try:
        Path(args.out).write_bytes(payload)
    except OSError as exc:
        raise InputErrors([f"cannot write {args.out}: {exc}"]) from exc
    return core.out(
        {
            "ok": True,
            "slice": args.slice,
            "final": plan["series"]["final"],
            "plan_sha256": core.digest(plan),
            "out": str(args.out),
        }
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("partition", "slice"):
        sub = commands.add_parser(name)
        sub.add_argument("--template", required=True)
        sub.add_argument("--index", required=True)
    sub = commands.choices["slice"]
    sub.add_argument("--slice", type=int, required=True)
    sub.add_argument("--predecessor-plan-id")
    sub.add_argument("--predecessor-run-id")
    sub.add_argument("--repo-root")
    sub.add_argument("--ledger-root")
    sub.add_argument("--out")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "slice":
            _usage(args)
        template = load_template(args.template)
        expansion = build(template, load_index(args.index, template))
        if args.command == "slice":
            return _run_slice(args, expansion)
        summary = partition_summary(expansion)
        if len(core.canon(summary)) > plancontract.HANDOFF_PLAN_MAX:
            raise InputErrors(["partition summary exceeds 64 KiB; shrink the index"])
        return core.out(summary)
    except UsageError as exc:
        return core.out({"ok": False, "errors": [str(exc)]}, 2)
    except InputErrors as exc:
        return core.out({"ok": False, "errors": exc.errors}, 1)
    except Error as exc:
        return core.out({"ok": False, "errors": [str(exc)]}, 1)
