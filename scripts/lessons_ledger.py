#!/usr/bin/env python3
"""Pending-ledger contract for the lesson loop (Plan 1).

The ledger is the gitignored, worktree-shared staging area for correction
candidates before they graduate (Plan 3) into committed rules. Stdlib only.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


class LedgerError(ValueError):
    """Raised for any invalid ledger path, record, or operation."""


def resolve_ledger_path(cwd: os.PathLike[str] | str | None = None) -> Path:
    """Return the one shared pending-ledger path for this repo.

    Anchored to the git *common dir* so every worktree resolves the SAME
    physical file (not a per-worktree copy). Lives under the main root's
    gitignored ``.cache/``.
    """
    base = Path(cwd) if cwd is not None else Path.cwd()
    try:
        out = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--git-common-dir"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise LedgerError(f"not a git repository: {base}") from exc
    common = Path(out)
    if not common.is_absolute():
        common = (base / common).resolve()
    main_root = common.parent
    return main_root / ".cache" / "lessons" / "pending.jsonl"
