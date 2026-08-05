"""Shared argparse surface of the two analysis-engine CLIs (stdlib-only)."""

from __future__ import annotations

import argparse

__all__ = ["add_shared_flags"]


def add_shared_flags(ap: argparse.ArgumentParser) -> None:
    """Declare the flags `lean_engine.py` and `code_lens.py` both accept.

    The two CLIs publish one shared contract — each reads the repo registry
    `.lean-audit.toml` when present, and emits text or `--format json` — so the
    declarations are single-sourced here instead of kept in step by hand.

    Call this AFTER a CLI's own flags: argparse renders `--help` in declaration
    order, and both engines list these two last.
    """
    ap.add_argument("--registry", help="path to .lean-audit.toml")
    ap.add_argument("--format", choices=("text", "json"), default="text")
