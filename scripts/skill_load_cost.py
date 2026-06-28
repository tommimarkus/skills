#!/usr/bin/env python3
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


def extract_inventory(text: str, code_patterns: list[str]) -> dict:
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


def union_inventory(invs: list[dict]) -> dict:
    codes: set[str] = set()
    sections: set[str] = set()
    for inv in invs:
        codes.update(inv["codes"])
        sections.update(inv["sections"])
    return {"codes": sorted(codes), "sections": sorted(sections)}


def diff_inventory(baseline: dict, current: dict) -> list[str]:
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


def _read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _cmd_measure(args) -> int:
    scenarios = {s["id"]: s for s in _read_json(args.scenarios)}
    result = measure_scenario(scenarios[args.id], Path(args.root))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for row in result["rows"]:
            print(f"{row['tokens']:>8}  {row['file']}")
        print(f"{result['total']:>8}  TOTAL ({result['id']})")
    return 0


def _cmd_baseline(args) -> int:
    patterns = _read_json(args.code_patterns)
    invs = [extract_inventory(Path(f).read_text(encoding="utf-8"), patterns)
            for f in args.files]
    out = union_inventory(invs)
    text = json.dumps(out, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def _cmd_diff(args) -> int:
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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
