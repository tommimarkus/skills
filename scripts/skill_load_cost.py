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
