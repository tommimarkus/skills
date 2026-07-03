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

__all__ = [
    "TOKEN_RE",
    "Inventory",
    "estimate_tokens",
    "measure_scenario",
    "resolve_closure",
    "resolve_closure_with_overrides",
    "extract_inventory",
    "union_inventory",
    "diff_inventory",
    "check_pointers",
    "cost_regressions",
    "main",
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


def measure_scenario(scenario: dict, root: Path) -> dict:
    rows = []
    total = 0
    for rel in scenario["files"]:
        tokens = estimate_tokens((root / rel).read_text(encoding="utf-8"))
        rows.append({"file": rel, "tokens": tokens})
        total += tokens
    return {"id": scenario["id"], "rows": rows, "total": total}


SECTION_RE = re.compile(r"^#{1,6}[ \t]+(.*?)[ \t]*$", re.M)
LINK_RE = re.compile(r"\]\(([^)]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


def _strip_code(text: str) -> str:
    """Remove fenced and inline code so code samples (regex, link-like syntax)
    are not mistaken for Markdown link pointers."""
    return INLINE_CODE_RE.sub("", FENCE_RE.sub("", text))


def resolve_closure(skill_md: Path) -> list[Path]:
    """Files a skill loads, via transitive Load-Map markdown links from SKILL.md.
    Deterministic (link-following only); the per-mode subset is judgment, not this."""
    return resolve_closure_with_overrides(skill_md, {})


def resolve_closure_with_overrides(skill_md: Path, overrides: dict) -> list[Path]:
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
        for link in LINK_RE.findall(_strip_code(text)):
            target = link.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
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
    sections = SECTION_RE.findall(text)
    pointers = LINK_RE.findall(_strip_code(text))
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


def check_pointers(paths: list[Path], code_patterns: list[str]) -> list[str]:
    problems = []
    for path in paths:
        inv = extract_inventory(path.read_text(encoding="utf-8"), code_patterns)
        for pointer in inv["pointers"]:
            target = pointer.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
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


def cost_regressions(snapshot: dict, scenarios: list[dict], root, tolerance: int) -> list[str]:
    """Re-measure each snapshotted scenario's token total against root and flag it
    when growth over the snapshot exceeds tolerance."""
    by_id = {s["id"]: s for s in scenarios}
    problems = []
    for sid, old in snapshot.items():
        scen = by_id.get(sid)
        if scen is None:
            continue
        cur = measure_scenario(scen, Path(root))["total"]
        if cur - old > tolerance:
            problems.append(
                f"{sid}: per-use cost grew {cur - old} tokens (snapshot {old} -> {cur})")
    return problems


def _cmd_measure(args: argparse.Namespace) -> int:
    scenarios = {s["id"]: s for s in _read_json(args.scenarios)}
    result = measure_scenario(scenarios[args.id], Path(args.root))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for row in result["rows"]:
            print(f"{row['tokens']:>8}  {row['file']}")
        print(f"{result['total']:>8}  TOTAL ({result['id']})")
    return 0


def _cmd_baseline(args: argparse.Namespace) -> int:
    patterns = _read_json(args.code_patterns)
    invs = [extract_inventory(Path(f).read_text(encoding="utf-8"), patterns)
            for f in args.files]
    out = union_inventory(invs)
    _emit_json(out, args.out)
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    patterns = _read_json(args.code_patterns)
    baseline = _read_json(args.baseline)
    paths = [Path(f) for f in args.files]
    current = union_inventory(
        [extract_inventory(p.read_text(encoding="utf-8"), patterns) for p in paths]
    )
    problems = diff_inventory(baseline, current) + check_pointers(paths, patterns)
    for problem in problems:
        print(f"FIDELITY REGRESSION: {problem}", file=sys.stderr)
    return 1 if problems else 0


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
        return args.func(args)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"skill-load-cost: {exc}", file=sys.stderr)
        return 2
