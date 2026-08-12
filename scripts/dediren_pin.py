#!/usr/bin/env python3
"""Report or move the architecture plugin's pinned Dediren release.

``DEDIREN_VERSION_DEFAULT`` in the runtime module below is the release the MCP
adapter provisions and checksum-verifies into the host's plugin data directory;
``DEDIREN_VERSION_FLOOR`` beside it is the oldest release the skill's post-render
step tolerates. This tool only reports and moves that constant — adopting a
release (smoke suite, feature-parity diff, floor decision, re-stamp) is
``docs/maintenance-procedures.md`` § "Dediren upstream release adoption".

The repo root comes from the working directory or an explicit ``--repo-root``,
never from ``Path(__file__)``: this script writes, and a location-derived root
would silently edit the primary checkout when run from a nested worktree.
``scripts/version_stamp.py`` resolves its root the same way.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

RUNTIME_REL = "souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren_runtime.py"
UPSTREAM_REPO = "tommimarkus/dediren"
RELEASE_API = "https://api.github.com/repos/{repo}/releases/{selector}"
TIMEOUT_SECONDS = 30.0

# The runtime module's own pin grammar, restated rather than imported: that module
# is shipped to hosts and runs under their python3, so this tool reads it as text.
CALVER_RE = re.compile(r"^(\d{4})\.(\d{2})\.(\d+)$")
PIN_RE = re.compile(r'^(DEDIREN_VERSION_DEFAULT\s*=\s*")([^"]+)(")', re.MULTILINE)
FLOOR_RE = re.compile(r'^DEDIREN_VERSION_FLOOR\s*=\s*"([^"]+)"', re.MULTILINE)

EXIT_REFUSED = 1  # a rule refused the request
EXIT_UPSTREAM = 3  # GitHub unreachable, or no such release


class PinError(Exception):
    """A refusal or upstream failure carrying its operator-facing exit code."""

    def __init__(self, message: str, code: int = EXIT_REFUSED) -> None:
        super().__init__(message)
        self.code = code


def calver_key(version: str) -> tuple[int, int, int] | None:
    """Sortable key for a ``YYYY.0M.MICRO`` string, or None when it is not one."""
    match = CALVER_RE.match(version.strip())
    if match is None or not 1 <= int(match.group(2)) <= 12:
        return None
    year, month, micro = (int(group) for group in match.groups())
    return year, month, micro


def require_calver(version: str, label: str) -> tuple[int, int, int]:
    """`calver_key`, refusing rather than comparing None.

    Every caller here has already validated its input, but a malformed constant
    in the runtime module would otherwise surface as a TypeError from a `<`
    against None instead of a message naming the bad value.
    """
    key = calver_key(version)
    if key is None:
        raise PinError(f"{label} is not CalVer (YYYY.0M.MICRO): {version!r}")
    return key


def read_pin(repo_root: Path) -> tuple[Path, str, str]:
    """The runtime module, and the ``(pin, floor)`` pair it compiles in."""
    path = repo_root / RUNTIME_REL
    if not path.is_file():
        raise PinError(f"no {RUNTIME_REL} under {repo_root}; is that the repo root?")
    text = path.read_text(encoding="utf-8")
    pin, floor = PIN_RE.search(text), FLOOR_RE.search(text)
    if pin is None or floor is None:
        raise PinError(f"{path} does not declare DEDIREN_VERSION_DEFAULT and "
                       "DEDIREN_VERSION_FLOOR as plain string constants")
    if calver_key(pin.group(2)) is None or calver_key(floor.group(1)) is None:
        raise PinError(f"the compiled-in pin/floor are not CalVer: "
                       f"{pin.group(2)!r} / {floor.group(1)!r}")
    return path, pin.group(2), floor.group(1)


def release(selector: str) -> tuple[str, set[str]]:
    """A release's ``(version, asset names)``; selector is ``latest`` or ``tags/v…``."""
    url = RELEASE_API.format(repo=UPSTREAM_REPO, selector=selector)
    headers = {"User-Agent": "souroldgeezer-dediren-pin", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:  # Optional: raises the anonymous rate limit, never required.
        headers["Authorization"] = f"Bearer {token}"
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise PinError(f"GitHub answered HTTP {exc.code} for {url}", EXIT_UPSTREAM) from exc
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise PinError(f"could not read {url} ({exc})", EXIT_UPSTREAM) from exc
    version = str(payload.get("tag_name", "")).lstrip("v")
    if calver_key(version) is None:
        raise PinError(f"release {selector} has a non-CalVer tag: {version!r}", EXIT_UPSTREAM)
    return version, {str(item.get("name", "")) for item in payload.get("assets", [])}


def check_floor(version: str, floor: str) -> None:
    if require_calver(version, "requested version") < require_calver(floor, "the compiled-in floor"):
        raise PinError(f"Dediren {version} is below the supported floor {floor}. Lowering "
                       "the floor is a support decision, not a pin move — see "
                       'docs/maintenance-procedures.md § "Dediren upstream release adoption".')


def require_assets(version: str, names: set[str]) -> None:
    """Refuse a release that does not publish what provisioning actually fetches."""
    prefix = f"dediren-agent-bundle-{version}."
    missing = [] if any(name.startswith(prefix) for name in names) else [f"{prefix}*"]
    if "SHA256SUMS" not in names:
        missing.append("SHA256SUMS")
    if missing:
        raise PinError(f"Dediren {version} does not publish {' and '.join(missing)}; the "
                       "adapter provisions the bundle SHA256SUMS names and verifies it "
                       "against that digest.")


def cmd_check(repo_root: Path, fmt: str) -> int:
    _, pin, floor = read_pin(repo_root)
    latest, _ = release("latest")
    behind = require_calver(latest, "the latest release") > require_calver(pin, "the current pin")
    if fmt == "json":
        print(json.dumps({"repo": UPSTREAM_REPO, "module": RUNTIME_REL, "pin": pin,
                          "floor": floor, "latest": latest, "behind": behind}, indent=2))
        return 0
    for label, value in (("repo", UPSTREAM_REPO), ("pin", pin), ("floor", floor),
                         ("latest", latest), ("status", "behind" if behind else "current")):
        print(f"{label + ':':8}{value}")
    if behind:
        print('adopt via docs/maintenance-procedures.md § "Dediren upstream release adoption"')
    return 0


def cmd_set(repo_root: Path, requested: str | None, dry_run: bool) -> int:
    path, pin, floor = read_pin(repo_root)
    if requested is None:
        version, names = release("latest")
        check_floor(version, floor)
    else:
        version = requested.strip().lstrip("v")
        if calver_key(version) is None:
            raise PinError(f"not a CalVer version (YYYY.0M.MICRO): {requested}")
        # Both local refusals run before any network call, so a below-floor or
        # already-pinned request is answered with its own reason rather than with
        # a confusing lookup failure.
        check_floor(version, floor)
        names = set() if version == pin else release(f"tags/v{version}")[1]

    if version == pin:
        print(f"no change: the pin is already {version}")
        return 0
    require_assets(version, names)
    if dry_run:
        print(f"would move the pin {pin} -> {version} in {RUNTIME_REL}")
        return 0
    text = path.read_text(encoding="utf-8")
    path.write_text(PIN_RE.sub(lambda m: f"{m.group(1)}{version}{m.group(3)}", text, count=1),
                    encoding="utf-8")
    print(f"moved the pin {pin} -> {version} in {RUNTIME_REL}")
    print('next: docs/maintenance-procedures.md § "Dediren upstream release adoption"')
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dediren_pin.py",
        description=f"Report or move the {UPSTREAM_REPO} release the architecture plugin pins.",
        epilog="Exit codes: 0 ok, 1 refused, 2 usage, 3 upstream unreachable. Moving the "
               'pin is one step of docs/maintenance-procedures.md § "Dediren upstream '
               'release adoption".',
    )
    parser.add_argument("--repo-root", default=".", help="repo root to operate on (default: the working directory)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="report the pin, the floor, and the latest release (default; read-only)")
    mode.add_argument("--set", metavar="VERSION", dest="version", help="move the pin to VERSION (CalVer YYYY.0M.MICRO)")
    mode.add_argument("--latest", action="store_true", help="move the pin to the latest release")
    parser.add_argument("--dry-run", action="store_true", help="with --set / --latest, report the move without writing")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="--check output format (default: text)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    mutating = args.version is not None or args.latest
    if args.dry_run and not mutating:
        parser.error("--dry-run applies to --set / --latest")
    repo_root = Path(args.repo_root).resolve()
    try:
        if mutating:
            return cmd_set(repo_root, args.version, args.dry_run)
        return cmd_check(repo_root, args.format)
    except PinError as exc:
        print(f"dediren-pin: {exc}", file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
