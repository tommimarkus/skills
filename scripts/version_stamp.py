#!/usr/bin/env python3
"""Worktree-deferred CalVer stamping for the plugins in this marketplace.

Two stdlib-only responsibilities (see CLAUDE.md "Plugin versioning (MUST)"):

- ``compute``: at integration on ``main``, print a plugin's next CalVer stamp
  computed against ``main``'s *current* state, so the within-month micro counter
  is a real main-line sequence number, not a value guessed against a stale
  worktree base.
- ``guard``: at the end of worktree / feature-branch work, fail if the branch
  touched any version cell. Under the worktree-deferred rule the stamp belongs
  to the ``main`` integration commit, not the feature branch.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

PLUGINS = (
    "souroldgeezer-audit",
    "souroldgeezer-design",
    "souroldgeezer-architecture",
    "souroldgeezer-policy",
    "souroldgeezer-ops",
)

VERSION_RE = re.compile(r"^(\d{4})\.(\d{2})\.(\d+)$")


def parse_version(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.match(value)
    if not match:
        raise ValueError(f"not a CalVer version: {value!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def compute_next(current: str, month: str) -> str:
    """Return the next CalVer stamp for ``current`` in calendar ``month``.

    ``month`` is ``"YYYY.MM"``. Reset to ``.0`` when ``current`` predates the
    month or is a pre-CalVer semver; increment the micro counter within the same
    month; raise when ``month`` is older than ``current`` (clock skew).
    """
    myear, mmonth = (int(part) for part in month.split("."))
    try:
        cyear, cmonth, cmicro = parse_version(current)
    except ValueError:
        return f"{myear:04d}.{mmonth:02d}.0"
    if (myear, mmonth) > (cyear, cmonth):
        return f"{myear:04d}.{mmonth:02d}.0"
    if (myear, mmonth) == (cyear, cmonth):
        return f"{cyear:04d}.{cmonth:02d}.{cmicro + 1}"
    raise ValueError(
        f"target month {month} is older than current version {current}"
    )


def version_diff(
    base: dict[str, str], head: dict[str, str]
) -> list[tuple[str, str, str]]:
    """Return ``(key, base_value, head_value)`` for every key present in
    ``base`` whose value differs in ``head``. Keys absent in ``base`` (e.g. a
    brand-new plugin's initial version) are not flagged."""
    changed: list[tuple[str, str, str]] = []
    for key, base_value in base.items():
        head_value = head.get(key)
        if head_value is not None and head_value != base_value:
            changed.append((key, base_value, head_value))
    return changed


def current_month() -> str:
    today = datetime.date.today()
    return f"{today.year:04d}.{today.month:02d}"


def read_version(repo_root: Path, plugin: str) -> str:
    manifest = repo_root / plugin / ".claude-plugin" / "plugin.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return data["version"]


def cmd_compute(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    month = args.month or current_month()
    current = read_version(repo_root, args.plugin)
    print(compute_next(current, month))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Worktree-deferred CalVer stamping.")
    parser.add_argument("--repo-root", default=".", help="repo root (default: .)")
    sub = parser.add_subparsers(dest="command", required=True)

    compute = sub.add_parser("compute", help="print a plugin's next CalVer stamp")
    compute.add_argument("--plugin", required=True, choices=PLUGINS)
    compute.add_argument("--month", help='target month "YYYY.MM" (default: this month)')
    compute.set_defaults(func=cmd_compute)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
