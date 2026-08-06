"""Per-use load-cost measurement and fidelity baseline for skill references.

Stdlib-only (see CLAUDE.md "Repo-local Python tooling"). Token counts are a
deterministic proxy (word/punctuation split), not a model tokenizer; the metric
is the before/after delta on a declared scenario, so a stable proxy suffices.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, NotRequired, TypedDict
from urllib.parse import unquote

__all__ = [
    "COST_TOLERANCE",
    "Inventory",
    "TOKEN_RE",
    "check_pointers",
    "cost_regressions",
    "diff_inventory",
    "estimate_tokens",
    "extract_inventory",
    "guard_tokens",
    "main",
    "marginal_cost_regressions",
    "measure_scenario",
    "resolve_closure",
    "resolve_closure_with_overrides",
    "scenario_uses_path",
    "union_inventory",
]


class Inventory(TypedDict):
    """The code/section/pointer inventory extract_inventory produces. union_inventory
    drops `pointers` (codes/sections are the only fields it unions), so pointers is
    NotRequired rather than always present."""

    codes: list[str]
    sections: list[str]
    pointers: NotRequired[list[str]]


TOKEN_RE = re.compile(r"\w+|[^\w\s]")


def estimate_tokens(text: str) -> int:
    return len(TOKEN_RE.findall(text))


# Per-use cost tolerance, in proxy tokens. Growth beyond this on a scenario is the
# guard's advisory-warning threshold (guard_load_cost.py), and the committed
# cost-snapshot must stay within it of a fresh measurement — the deterministic
# freshness gate in tests/skill_load_cost_freshness_test.py. Single-sourced here so
# the advisory and the freshness gate share one threshold.
COST_TOLERANCE = 200


_SECTION_RE = re.compile(r"^#{1,6}[ \t]+(.*?)[ \t]*$", re.M)
_LINK_RE = re.compile(r"\]\(([^)]+)\)")
_FENCE_RE = re.compile(r"```.*?```", re.S)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*(?:\n|$)", re.M)
_SUPPORTED_SELECTION_METADATA_KINDS = frozenset(
    {"agent-summary", "marketplace-description", "skill-description"}
)


def _required_string(mapping: dict[str, Any], field: str, owner: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner}.{field}: expected a non-empty string")
    return value.strip()


def _route_predicate(route: dict[str, Any], index: int) -> str:
    predicate = _required_string(route, "predicate", f"load_routes[{index}]")
    if predicate in {"always", "unknown"}:
        return predicate
    if predicate.startswith("conditional:") and predicate.removeprefix("conditional:").strip():
        return predicate
    raise ValueError(
        f"load_routes[{index}].predicate: expected always, conditional:<label>, or unknown"
    )


def _heading_slug(heading: str) -> str:
    heading = re.sub(r"[ \t]+#+[ \t]*$", "", heading.strip()).lower()
    heading = re.sub(r"[^\w\s-]", "", heading)
    return re.sub(r"\s+", "-", heading)


def _heading_subtree(text: str, requested_anchor: str) -> tuple[str, str] | None:
    """Return one GitHub-style heading subtree and its normalized anchor.

    A missing anchor is deliberately unresolved: callers then charge the whole
    file instead of guessing which prose the runtime would load.
    """
    anchor = unquote(requested_anchor).strip().lower()
    if not anchor:
        return None
    headings: list[tuple[re.Match[str], int, str]] = []
    slug_counts: dict[str, int] = {}
    heading_text = _FENCE_RE.sub(lambda match: re.sub(r"[^\n]", " ", match.group(0)), text)
    for match in _HEADING_RE.finditer(heading_text):
        base = _heading_slug(match.group(2))
        count = slug_counts.get(base, 0)
        slug_counts[base] = count + 1
        slug = base if count == 0 else f"{base}-{count}"
        headings.append((match, len(match.group(1)), slug))
    target_indexes = [index for index, (_, _, slug) in enumerate(headings) if slug == anchor]
    if len(target_indexes) != 1:
        return None
    index = target_indexes[0]
    match, level, slug = headings[index]
    end = len(text)
    for next_match, next_level, _ in headings[index + 1 :]:
        if next_level <= level:
            end = next_match.start()
            break
    return text[match.start() : end], slug


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _scenario_text(path: Path, overrides: dict[Path, str]) -> str:
    resolved = path.resolve()
    if resolved in overrides:
        return overrides[resolved]
    return path.read_text(encoding="utf-8")


def _measure_load_routes(
    routes: Any, root: Path, overrides: dict[Path, str]
) -> list[dict[str, Any]]:
    if not isinstance(routes, list):
        raise ValueError("load_routes: expected a list")
    units: dict[tuple[Path, str | None], dict[str, Any]] = {}
    for index, raw_route in enumerate(routes):
        if not isinstance(raw_route, dict):
            raise ValueError(f"load_routes[{index}]: expected an object")
        entry = _required_string(raw_route, "entry", f"load_routes[{index}]")
        target = _required_string(raw_route, "target", f"load_routes[{index}]")
        predicate = _route_predicate(raw_route, index)
        rel, separator, requested_anchor = target.partition("#")
        if not rel.strip():
            raise ValueError(f"load_routes[{index}].target: expected a file before #anchor")
        path = (root / rel.strip()).resolve()
        text = _scenario_text(path, overrides)
        anchor: str | None = None
        resolution = "whole-file"
        measured = text
        if separator:
            subtree = _heading_subtree(text, requested_anchor)
            if subtree is None:
                resolution = "whole-file-fallback"
            else:
                measured, anchor = subtree
                resolution = "heading-subtree"
        key = (path, anchor)
        route_evidence = {"entry": entry, "predicate": predicate}
        unit = units.get(key)
        if unit is None:
            unit = {
                "kind": "load",
                "file": _display_path(path, root),
                "anchor": anchor,
                "resolution": resolution,
                "requested_targets": [],
                "routes": [],
                "tokens": estimate_tokens(measured),
            }
            units[key] = unit
        elif resolution == "whole-file-fallback":
            unit["resolution"] = resolution
        if target not in unit["requested_targets"]:
            unit["requested_targets"].append(target)
        if route_evidence not in unit["routes"]:
            unit["routes"].append(route_evidence)
    return list(units.values())


def _measure_selection_metadata(items: Any) -> list[dict[str, Any]]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError("selection_metadata: expected a list")
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, raw_item in enumerate(items):
        owner = f"selection_metadata[{index}]"
        if not isinstance(raw_item, dict):
            raise ValueError(f"{owner}: expected an object")
        entry = _required_string(raw_item, "entry", owner)
        kind = _required_string(raw_item, "kind", owner)
        if kind not in _SUPPORTED_SELECTION_METADATA_KINDS:
            supported = ", ".join(sorted(_SUPPORTED_SELECTION_METADATA_KINDS))
            raise ValueError(f"{owner}.kind: unsupported selection_metadata kind; use {supported}")
        text = _required_string(raw_item, "text", owner)
        key = (entry, kind, text)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"entry": entry, "kind": kind, "tokens": estimate_tokens(text)})
    return rows


def measure_scenario(
    scenario: dict[str, Any],
    root: Path,
    overrides: dict[Path, str] | None = None,
) -> dict[str, Any]:
    """Measure legacy file lists or caller-declared load routes.

    `load_routes` is evidence, not a natural-language inference: every route
    names its entry, target, and `always` / `conditional:<label>` / `unknown`
    predicate. Identical resolved units count once across entries.
    """
    override_map = {Path(path).resolve(): text for path, text in (overrides or {}).items()}
    if "files" in scenario and "load_routes" in scenario:
        raise ValueError("scenario: use files or load_routes, not both")
    if "load_routes" in scenario:
        rows = _measure_load_routes(scenario["load_routes"], root, override_map)
    else:
        files = scenario.get("files")
        if not isinstance(files, list):
            raise ValueError("scenario.files: expected a list")
        rows = []
        for rel in files:
            if not isinstance(rel, str) or not rel.strip():
                raise ValueError("scenario.files: every file must be a non-empty string")
            tokens = estimate_tokens(_scenario_text((root / rel).resolve(), override_map))
            rows.append({"file": rel, "tokens": tokens})
    metadata_rows = _measure_selection_metadata(scenario.get("selection_metadata"))
    load_total = sum(int(row["tokens"]) for row in rows)
    metadata_total = sum(int(row["tokens"]) for row in metadata_rows)
    return {
        "id": scenario["id"],
        "rows": rows,
        "selection_metadata_rows": metadata_rows,
        "load_total": load_total,
        "selection_metadata_total": metadata_total,
        "total": load_total + metadata_total,
    }


def scenario_uses_path(scenario: dict[str, Any], root: Path, target: Path) -> bool:
    """Whether a declared scenario contains target; no host activation inference."""
    target = target.resolve()
    files = scenario.get("files")
    if isinstance(files, list):
        return any(isinstance(rel, str) and (root / rel).resolve() == target for rel in files)
    routes = scenario.get("load_routes")
    if not isinstance(routes, list):
        return False
    for route in routes:
        if not isinstance(route, dict):
            continue
        raw_target = route.get("target")
        if isinstance(raw_target, str):
            rel = raw_target.partition("#")[0].strip()
            if rel and (root / rel).resolve() == target:
                return True
    return False


def _strip_code(text: str) -> str:
    """Remove fenced and inline code so code samples (regex, link-like syntax)
    are not mistaken for Markdown link pointers."""
    return _INLINE_CODE_RE.sub("", _FENCE_RE.sub("", text))


def _local_target(link: str) -> str | None:
    """The link's on-disk target: anchor stripped, or None when nothing remains
    or the link is external (http/https/mailto)."""
    target = link.split("#", 1)[0]
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    return target


def resolve_closure(skill_md: Path) -> list[Path]:
    """Files a skill loads, via transitive Load-Map markdown links from SKILL.md.
    Deterministic (link-following only); the per-mode subset is judgment, not this."""
    return resolve_closure_with_overrides(skill_md, {})


def resolve_closure_with_overrides(skill_md: Path, overrides: dict[Path, str]) -> list[Path]:
    """Like resolve_closure but uses overrides[path] as the link text when reading
    a file, instead of reading from disk.  This makes a pending edit's link removals
    actually shrink the closure (e.g. when decide() tests a not-yet-written edit).

    overrides: mapping of absolute Path -> str (the would-be content of that file).
    Files not in overrides are read from disk as normal.
    Non-existent files without an override entry are skipped (fail-open)."""
    skill_md = skill_md.resolve()
    seen: set[Path] = set()
    queue = [skill_md]
    while queue:
        cur = queue.pop()
        if cur in seen:
            continue
        if cur in overrides:
            text = overrides[cur]
        elif cur.exists():
            text = cur.read_text(encoding="utf-8")
        else:
            continue
        seen.add(cur)
        for link in _LINK_RE.findall(_strip_code(text)):
            target = _local_target(link)
            if target is None:
                continue
            nxt = (cur.parent / target).resolve()
            if nxt.suffix == ".md" and nxt not in seen:
                # Accept override-provided files even if not on disk
                if nxt in overrides or nxt.exists():
                    queue.append(nxt)
    return sorted(seen)


def extract_inventory(text: str, code_patterns: list[str]) -> Inventory:
    codes: set[str] = set()
    for pattern in code_patterns:
        codes.update(re.findall(pattern, text))
    sections = _SECTION_RE.findall(text)
    pointers = _LINK_RE.findall(_strip_code(text))
    return {
        "codes": sorted(codes),
        "sections": sections,
        "pointers": sorted(set(pointers)),
    }


def union_inventory(invs: list[Inventory]) -> Inventory:
    codes: set[str] = set()
    sections: set[str] = set()
    for inv in invs:
        codes.update(inv["codes"])
        sections.update(inv["sections"])
    return {"codes": sorted(codes), "sections": sorted(sections)}


def diff_inventory(baseline: Inventory, current: Inventory) -> list[str]:
    problems = []
    for code in sorted(set(baseline["codes"]) - set(current["codes"])):
        problems.append(f"missing code (unreachable across skill): {code}")
    current_sections = set(current["sections"])
    for section in sorted(s for s in baseline["sections"] if s not in current_sections):
        problems.append(f"missing section (unreachable across skill): {section}")
    return problems


# --- G2v: deterministic guard-token gate for tighten rewrites -------------------
#
# A tighten rewrite carries its own meaning (unlike dedupe, whose content survives
# at the canonical home), so this is the one deterministic backstop against silent
# fidelity loss. It compares the CLOSED token classes of a before/after region: the
# after-region must be a superset for codes/links/inline-code/numbers/normative
# keywords, and must not DROP any negation token's count (the dropped-"not" silent
# inversion). English-keyword based; non-English normative markers ride on the
# judgment gates (G7v/G5v) only — a disclosed evidence limit.
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
_NORMATIVE_RE = re.compile(
    r"\b(?:MUST|MUSTN'T|SHALL|SHOULD|SHOULDN'T|NEVER|ONLY|NOT|NONE|"
    r"REQUIRED|ALWAYS|FORBIDDEN|PROHIBITED)\b"
)
_NEGATION_RE = re.compile(
    r"\b(?:no|not|never|none|without|unless|except|cannot|neither|nor)\b", re.I
)


def _prose_text(text: str, code_patterns: list[str]) -> str:
    """Strip fenced/inline code, link targets, and finding codes so number
    extraction sees prose thresholds, not the digits inside a code like LA-DUP-1."""
    stripped = _LINK_RE.sub(" ", _strip_code(text))
    for pattern in code_patterns:
        stripped = re.sub(pattern, " ", stripped)
    return stripped


def guard_tokens(before: str, after: str, code_patterns: list[str]) -> list[str]:
    """Compare the closed token classes of a before/after region for a tighten
    rewrite. Returns a list of drop messages (empty = the rewrite preserved every
    guarded token). One-directional (before must be preserved in after); adding
    meaning is caught by the judgment two-way-entailment step, not here."""

    def codes(text: str) -> set[str]:
        found: set[str] = set()
        for pattern in code_patterns:
            found.update(re.findall(pattern, text))
        return found

    def normatives(text: str) -> set[str]:
        return set(_NORMATIVE_RE.findall(_strip_code(text)))

    def negations(text: str) -> list[str]:
        return [t.lower() for t in _NEGATION_RE.findall(_strip_code(text))]

    problems: list[str] = []
    checks = [
        ("code", codes(before), codes(after)),
        ("link", set(_LINK_RE.findall(before)), set(_LINK_RE.findall(after))),
        ("inline-code", set(_INLINE_CODE_RE.findall(before)), set(_INLINE_CODE_RE.findall(after))),
        (
            "number",
            set(_NUMBER_RE.findall(_prose_text(before, code_patterns))),
            set(_NUMBER_RE.findall(_prose_text(after, code_patterns))),
        ),
        ("normative keyword", normatives(before), normatives(after)),
    ]
    for label, before_set, after_set in checks:
        for missing in sorted(before_set - after_set):
            problems.append(f"dropped {label}: {missing}")

    before_neg = negations(before)
    after_neg = negations(after)
    for tok in sorted(set(before_neg)):
        b, a = before_neg.count(tok), after_neg.count(tok)
        if a < b:
            problems.append(f"dropped negation: {tok} ({b} -> {a})")
    return problems


def check_pointers(paths: list[Path], code_patterns: list[str]) -> list[str]:
    problems = []
    for path in paths:
        inv = extract_inventory(path.read_text(encoding="utf-8"), code_patterns)
        for pointer in inv["pointers"]:
            target = _local_target(pointer)
            if target is None:
                continue
            if not (path.parent / target).resolve().exists():
                problems.append(f"{path}: dangling pointer: {pointer}")
    return problems


def _read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _emit_json(payload: Any, out_path: str | None) -> None:
    text = json.dumps(payload, indent=2)
    if out_path:
        Path(out_path).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def cost_regressions(
    snapshot: dict[str, int],
    scenarios: list[dict[str, Any]],
    root: str | Path,
    tolerance: int = COST_TOLERANCE,
) -> list[str]:
    """Re-measure each snapshotted scenario's token total against root and flag it
    when growth over the snapshot exceeds tolerance (defaults to COST_TOLERANCE)."""
    by_id = {s["id"]: s for s in scenarios}
    problems = []
    for sid, old in snapshot.items():
        scen = by_id.get(sid)
        if scen is None:
            continue
        cur = measure_scenario(scen, Path(root))["total"]
        if cur - old > tolerance:
            problems.append(
                f"{sid}: per-use cost grew {cur - old} tokens (snapshot {old} -> {cur})"
            )
    return problems


def marginal_cost_regressions(
    scenarios: list[dict[str, Any]],
    root: str | Path,
    overrides: dict[Path, str],
    tolerance: int = COST_TOLERANCE,
) -> list[str]:
    """Warn only for the proposed edit's positive per-scenario marginal cost.

    Committed snapshots are intentionally absent: pre-existing drift cannot be
    attributed to a neutral or reducing pending edit.
    """
    root_path = Path(root)
    override_map = {Path(path).resolve(): text for path, text in overrides.items()}
    messages = []
    for scenario in scenarios:
        if not any(scenario_uses_path(scenario, root_path, path) for path in override_map):
            continue
        before = int(measure_scenario(scenario, root_path)["total"])
        after = int(measure_scenario(scenario, root_path, override_map)["total"])
        delta = after - before
        if delta > tolerance:
            messages.append(
                f"{scenario['id']}: pending edit adds {delta} per-use tokens "
                f"(current {before} -> proposed {after})"
            )
    return messages


def _cmd_measure(args: argparse.Namespace) -> int:
    scenarios = {s["id"]: s for s in _read_json(args.scenarios)}
    if args.id not in scenarios:
        available = ", ".join(sorted(scenarios)) or "(none)"
        print(
            f"skill-load-cost: unknown scenario id {args.id!r} (available: {available})",
            file=sys.stderr,
        )
        return 2
    result = measure_scenario(scenarios[args.id], Path(args.root))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for row in result["rows"]:
            print(f"{row['tokens']:>8}  {row['file']}")
        for row in result["selection_metadata_rows"]:
            print(f"{row['tokens']:>8}  SELECTION METADATA {row['kind']} ({row['entry']})")
        print(f"{result['total']:>8}  TOTAL ({result['id']})")
    return 0


def _cmd_baseline(args: argparse.Namespace) -> int:
    patterns = _read_json(args.code_patterns)
    invs = [extract_inventory(Path(f).read_text(encoding="utf-8"), patterns) for f in args.files]
    out = union_inventory(invs)
    _emit_json(out, args.out)
    return 0


def _report_problems(label: str, problems: list[str]) -> int:
    """Print each problem to stderr under label; exit 1 when any, else 0 — the
    shared gate-subcommand contract."""
    for problem in problems:
        print(f"{label}: {problem}", file=sys.stderr)
    return 1 if problems else 0


def _cmd_diff(args: argparse.Namespace) -> int:
    patterns = _read_json(args.code_patterns)
    baseline = _read_json(args.baseline)
    paths = [Path(f) for f in args.files]
    current = union_inventory(
        [extract_inventory(p.read_text(encoding="utf-8"), patterns) for p in paths]
    )
    problems = diff_inventory(baseline, current) + check_pointers(paths, patterns)
    return _report_problems("FIDELITY REGRESSION", problems)


def _cmd_guard_tokens(args: argparse.Namespace) -> int:
    patterns = _read_json(args.code_patterns)
    before = Path(args.before).read_text(encoding="utf-8")
    after = Path(args.after).read_text(encoding="utf-8")
    return _report_problems("GUARD-TOKEN GATE", guard_tokens(before, after, patterns))


def _cmd_snapshot(args: argparse.Namespace) -> int:
    scenarios = _read_json(args.scenarios)
    out = {s["id"]: measure_scenario(s, Path(args.root))["total"] for s in scenarios}
    _emit_json(out, args.out)
    return 0


def _cmd_resolve_closure(args: argparse.Namespace) -> int:
    paths = [str(p) for p in resolve_closure(Path(args.entry))]
    print(json.dumps(paths, indent=2) if args.json else "\n".join(paths))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Skill per-use load cost + fidelity gate")
    sub = parser.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("measure")
    m.add_argument("--scenarios", required=True)
    m.add_argument("--id", required=True)
    m.add_argument("--root", default=".")
    m.add_argument("--json", action="store_true")
    m.set_defaults(func=_cmd_measure)

    b = sub.add_parser("baseline")
    b.add_argument("--files", nargs="+", required=True)
    b.add_argument("--code-patterns", required=True)
    b.add_argument("--out")
    b.set_defaults(func=_cmd_baseline)

    d = sub.add_parser("diff")
    d.add_argument("--baseline", required=True)
    d.add_argument("--files", nargs="+", required=True)
    d.add_argument("--code-patterns", required=True)
    d.set_defaults(func=_cmd_diff)

    gt = sub.add_parser("guard_tokens")
    gt.add_argument("--before", required=True)
    gt.add_argument("--after", required=True)
    gt.add_argument("--code-patterns", required=True)
    gt.set_defaults(func=_cmd_guard_tokens)

    sn = sub.add_parser("snapshot")
    sn.add_argument("--scenarios", required=True)
    sn.add_argument("--root", default=".")
    sn.add_argument("--out")
    sn.set_defaults(func=_cmd_snapshot)

    rc = sub.add_parser("resolve_closure")
    rc.add_argument("entry")
    rc.add_argument("--json", action="store_true")
    rc.set_defaults(func=_cmd_resolve_closure)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, json.JSONDecodeError, re.error) as exc:
        print(f"skill-load-cost: {exc}", file=sys.stderr)
        return 2
