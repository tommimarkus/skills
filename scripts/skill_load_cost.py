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


def extract_inventory(text: str, code_patterns: list[str]) -> dict:
    codes: set[str] = set()
    for pattern in code_patterns:
        codes.update(re.findall(pattern, text))
    sections = SECTION_RE.findall(text)
    pointers = LINK_RE.findall(text)
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
