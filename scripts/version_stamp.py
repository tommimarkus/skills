#!/usr/bin/env python3
"""Worktree-deferred CalVer stamping for the plugins in this marketplace.

The Claude ``plugin.json#version`` remains the release authority (Claude Code
always resolves the plugin.json value over a marketplace-entry copy without
warning, so a stale marketplace copy is a silent drift risk — see CLAUDE.md
"Plugin versioning (MUST)"). The root README mirrors its zero-padded CalVer;
the additive Codex manifest and any native Copilot manifest mirror the same
semantic version with the month normalized for strict SemVer. Marketplace
``plugins[]`` entries never carry a ``version`` key.

Two stdlib-only responsibilities:

- ``compute``: at integration on ``main``, print a plugin's next CalVer stamp
  computed against ``main``'s *current* state (read from plugin.json only), so
  the within-month micro counter is a real main-line sequence number, not a
  value guessed against a stale worktree base.
- ``guard``: at the end of worktree / feature-branch work, fail if the branch
  touched an existing mirrored version cell, or if any marketplace entry (re)introduces a
  ``version`` key. Under the worktree-deferred rule the stamp belongs to the
  ``main`` integration commit, not the feature branch.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

PLUGINS = (
    "souroldgeezer-audit",
    "souroldgeezer-design",
    "souroldgeezer-architecture",
    "souroldgeezer-policy",
    "souroldgeezer-ops",
)

VERSION_RE = re.compile(r"^(\d{4})\.(\d{1,2})\.(\d+)$")


def parse_version(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.match(value)
    if not match:
        raise ValueError(f"not a CalVer version: {value!r}")
    year, month, micro = (int(match.group(index)) for index in (1, 2, 3))
    if not 1 <= month <= 12:
        raise ValueError(f"not a CalVer version: {value!r}")
    return year, month, micro


def codex_version(value: str) -> str:
    """Normalize a Claude CalVer stamp to Codex's strict-SemVer spelling."""
    year, month, micro = parse_version(value)
    return f"{year}.{month}.{micro}"


def compute_next(current: str, month: str) -> str:
    """Return the next CalVer stamp for ``current`` in calendar ``month``.

    ``month`` is ``"YYYY.M"`` or ``"YYYY.MM"``. Reset to ``.0`` when ``current`` predates the
    month or is a pre-CalVer semver; increment the micro counter within the same
    month; raise when ``month`` is older than ``current`` (clock skew).
    """
    month_match = re.fullmatch(r"(\d{4})\.(\d{1,2})", month)
    if month_match is None:
        raise ValueError(f"not a CalVer month: {month!r}")
    myear, mmonth = int(month_match.group(1)), int(month_match.group(2))
    if not 1 <= mmonth <= 12:
        raise ValueError(f"not a CalVer month: {month!r}")
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


def read_version(repo_root: Path, plugin: str, ref: str = "main") -> str:
    rel = f"{plugin}/.claude-plugin/plugin.json"
    text = _git_show(repo_root, ref, rel)
    if text is None:
        raise FileNotFoundError(f"{rel} not found at ref {ref!r}")
    return json.loads(text)["version"]


# lean-audit:dup-intentional:begin -- subcommands independently resolve the
# explicit repository root before applying their distinct read-only checks.
def cmd_compute(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    month = args.month or current_month()
    current = read_version(repo_root, args.plugin, args.ref)
    print(compute_next(current, month))
    return 0
# lean-audit:dup-intentional:end


def _git_show(repo_root: Path, ref: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{ref}:{path}"],
        capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else None


def merge_base(repo_root: Path, base: str, head: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", base, head],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


# Matches a root README.md version-table row: `| `<plugin>` | `<version>` | ...`.
README_ROW_RE = re.compile(
    r"^\|\s*`(?P<plugin>souroldgeezer-[a-z]+)`\s*\|\s*`(?P<version>[^`]+)`\s*\|",
    re.MULTILINE,
)


def read_readme_versions(text: str) -> dict[str, str]:
    """Pull each plugin's version-table cell out of the root README.md. Tolerant:
    rows for unknown plugins or malformed tables simply don't match."""
    return {match["plugin"]: match["version"] for match in README_ROW_RE.finditer(text)}


def versions_at_ref(repo_root: Path, ref: str) -> dict[str, str]:
    """The mirrored version cells at ``ref``: runtime manifests and each
    plugin's README.md version-table cell. Marketplace
    entries are deliberately excluded — see ``marketplace_version_offenders``."""
    versions: dict[str, str] = {}
    for plugin in PLUGINS:
        try:
            version = read_version(repo_root, plugin, ref)
        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
            continue
        versions[f"{plugin}/.claude-plugin/plugin.json"] = version
        codex_rel = f"{plugin}/.codex-plugin/plugin.json"
        codex_text = _git_show(repo_root, ref, codex_rel)
        if codex_text is not None:
            try:
                versions[codex_rel] = json.loads(codex_text)["version"]
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        copilot_rel = f"{plugin}/plugin.json"
        copilot_text = _git_show(repo_root, ref, copilot_rel)
        if copilot_text is not None:
            try:
                versions[copilot_rel] = json.loads(copilot_text)["version"]
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
    readme_text = _git_show(repo_root, ref, "README.md")
    if readme_text is not None:
        for plugin, version in read_readme_versions(readme_text).items():
            versions[f"readme:{plugin}"] = version
    return versions


def marketplace_version_offenders(repo_root: Path, ref: str) -> list[str]:
    """Plugin names whose marketplace.json entry illegally carries a ``version``
    key at ``ref``. Runtime manifests and README mirror the version identity;
    marketplace copies are drift risks. Fail-open: a missing or malformed
    marketplace.json yields no offenders rather than raising."""
    offenders: list[str] = []
    for path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        market = _git_show(repo_root, ref, path)
        if market is None:
            continue
        try:
            payload = json.loads(market)
        except json.JSONDecodeError:
            continue
        for entry in payload.get("plugins", []):
            if isinstance(entry, dict) and "version" in entry:
                offenders.append(f"{path}:{entry.get('name', '<unnamed>')}")
    return offenders


def cmd_guard(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    base_ref = merge_base(repo_root, args.base, args.head)
    changed = version_diff(
        versions_at_ref(repo_root, base_ref),
        versions_at_ref(repo_root, args.head),
    )
    offenders = marketplace_version_offenders(repo_root, args.head)

    if not changed and not offenders:
        print("OK: this branch changed no version cells.")
        return 0

    if changed:
        print(
            "Version cells were stamped inside this branch/worktree:",
            file=sys.stderr,
        )
        for key, was, now in changed:
            print(f"  {key}: {was} -> {now}", file=sys.stderr)
        print(
            "Under the worktree-deferred rule, revert these and apply the stamp "
            "at integration on main instead. Next stamp: "
            "uv run python scripts/version_stamp.py compute --plugin <name>",
            file=sys.stderr,
        )
    if offenders:
        print(
            "Marketplace entries must never carry a version key; runtime "
            "manifests and the README mirror version identity:",
            file=sys.stderr,
        )
        for name in offenders:
            print(f"  {name}", file=sys.stderr)
        print("Remove the version key from that marketplace entry.", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Worktree-deferred CalVer stamping.")
    parser.add_argument("--repo-root", default=".", help="repo root (default: .)")
    sub = parser.add_subparsers(dest="command", required=True)

    compute = sub.add_parser("compute", help="print a plugin's next CalVer stamp")
    compute.add_argument("--plugin", required=True, choices=PLUGINS)
    compute.add_argument("--month", help='target month "YYYY.MM" (default: this month)')
    compute.add_argument(
        "--ref", default="main",
        help="git ref to read the plugin's current version from (default: main)",
    )
    compute.set_defaults(func=cmd_compute)

    guard = sub.add_parser(
        "guard", help="fail if this branch stamped a version cell"
    )
    guard.add_argument("--base", default="main")
    guard.add_argument("--head", default="HEAD")
    # lean-audit:dup-intentional:begin -- conventional argparse dispatch stays
    # local to this tool; other release tools own different command contracts.
    guard.set_defaults(func=cmd_guard)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
# lean-audit:dup-intentional:end


if __name__ == "__main__":
    sys.exit(main())
