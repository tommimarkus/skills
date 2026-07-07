#!/usr/bin/env python3
"""Scoped, re-verified bump of the embedded Dediren version pins.

Adopting a new ``tommimarkus/dediren`` release repeats the same mechanical edit across
~14 files: the release-script default, the release test's ``EXPECTED_DEDIREN_VERSION``,
the dediren fixture models, the UML notation worked examples, and the source-grounding
prose claim (see ``docs/maintenance-procedures.md`` § Dediren upstream release adoption).
A repo-wide ``sed`` is unsafe because ``souroldgeezer-design``'s own CalVer and the
architecture plugin's marketplace/README stamp can *coincidentally* equal the dediren pin.

This is repo-maintenance tooling — it lives outside every plugin tree, needs no CalVer
stamp of its own, and mirrors ``scripts/version_stamp.py`` (stdlib-only, ``uv run``).

Three stdlib-only responsibilities:

- ``current``: print the pinned version, read from the single source of truth
  (``DEDIREN_VERSION_DEFAULT`` in the release script).
- ``bump --to X [--check]``: literal-replace the current pin with ``X`` across *only* the
  known dediren-pin surfaces, then re-run the same pin discovery the release test's
  guard uses and fail if any pin still differs. ``--check`` reports the plan without
  writing. Refuses when a pin has already drifted off the SoT.
- ``parity --to X``: fetch the current and target release bundles via the release
  resolver and diff the judgment surfaces (agent-usage guide, plugin manifests, schemas,
  fixtures, bundle manifest) so the human feature-parity classification reads a diff.

The tool performs the *mechanical* bump and feeds the *judgment* steps; it never
classifies breaking/additive/cosmetic, edits architecture.md, or applies the CalVer
stamp (owned by ``version_stamp.py`` at integration).
"""
from __future__ import annotations

import argparse
import difflib
import filecmp
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ARCH_REFS_REL = "souroldgeezer-architecture/skills/architecture-design/references"
RELEASE_SCRIPT_REL = f"{ARCH_REFS_REL}/scripts/dediren-release.sh"
TEST_FILE_REL = "tests/architecture_dediren_release_test.py"
SOURCE_GROUNDING_REL = f"{ARCH_REFS_REL}/source-grounding.md"

CALVER_RE = re.compile(r"^\d{4}\.\d{2}\.\d+$")

_DEFAULT_RE = re.compile(r'DEDIREN_VERSION_DEFAULT="([^"]+)"')
_EXPECTED_RE = re.compile(r'EXPECTED_DEDIREN_VERSION\s*=\s*"([^"]+)"')
# Mirror the release test's pin discovery so this tool and the guard test agree on the
# set of pins that a bump must move.
_REQUIRED_PLUGINS_ARRAY = re.compile(r'"required_plugins"\s*:\s*\[(.*?)\]', re.DOTALL)
_PLUGIN_PIN = re.compile(r'"id"\s*:\s*"([^"]+)"\s*,\s*"version"\s*:\s*"([^"]+)"')

# Release-bundle subpaths whose change between two versions may signal a runtime-contract
# shift the human must classify. Read-only diff surfaces for ``parity``.
PARITY_SURFACES = (
    "bundle.json",
    "docs/agent-usage.md",
    "plugins/*.manifest.json",
    "schemas/*.json",
    "fixtures/*",
)


class PinDriftError(RuntimeError):
    """An existing pin already differs from the release-script default, so a literal
    old->new replace would silently miss it. Fix the drift before bumping."""


@dataclass
class BumpReport:
    old: str
    new: str
    changed_files: list[str] = field(default_factory=list)
    replacements: int = 0


def current_version(repo_root: Path = REPO_ROOT) -> str:
    """Return the pinned version from the single source of truth."""
    text = (repo_root / RELEASE_SCRIPT_REL).read_text(encoding="utf-8")
    match = _DEFAULT_RE.search(text)
    if not match:
        raise RuntimeError(f"{RELEASE_SCRIPT_REL}: DEDIREN_VERSION_DEFAULT not found")
    return match.group(1)


def discover_pins(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    """Discover every ``required_plugins`` pin the same way the release test's guard does:
    fixture model JSON plus the pins embedded in each UML notation worked example. Keyed
    ``<repo-relative-path>::<plugin-id>``."""
    arch_refs = repo_root / ARCH_REFS_REL
    pins: dict[str, str] = {}
    for model_path in sorted((arch_refs / "fixtures" / "dediren").rglob("*.json")):
        document = json.loads(model_path.read_text(encoding="utf-8"))
        relative = model_path.relative_to(repo_root)
        for plugin in document.get("required_plugins", []):
            pins[f"{relative}::{plugin['id']}"] = plugin["version"]
    for example_path in sorted((arch_refs / "notations" / "uml").glob("*.md")):
        relative = example_path.relative_to(repo_root)
        for array_body in _REQUIRED_PLUGINS_ARRAY.findall(example_path.read_text(encoding="utf-8")):
            for plugin_id, version in _PLUGIN_PIN.findall(array_body):
                pins[f"{relative}::{plugin_id}"] = version
    return pins


def target_files(repo_root: Path = REPO_ROOT) -> list[Path]:
    """Every file the bump may edit. Scoped so the coincidental design/marketplace CalVer
    (which can equal the dediren pin) is never in range."""
    arch_refs = repo_root / ARCH_REFS_REL
    files = [
        repo_root / RELEASE_SCRIPT_REL,
        repo_root / TEST_FILE_REL,
        repo_root / SOURCE_GROUNDING_REL,
    ]
    files += sorted((arch_refs / "fixtures" / "dediren").rglob("*.json"))
    files += sorted((arch_refs / "notations" / "uml").glob("*.md"))
    return files


def verify(repo_root: Path, expected: str) -> list[str]:
    """Return human-readable descriptions of every pin surface not equal to ``expected``
    (empty when fully consistent). Covers the release-script default, the discovered
    fixture/notation pins, the release test's expectation, and the source-grounding claim."""
    mismatches: list[str] = []

    current = current_version(repo_root)
    if current != expected:
        mismatches.append(f"{RELEASE_SCRIPT_REL}::DEDIREN_VERSION_DEFAULT = {current}")

    for location, version in discover_pins(repo_root).items():
        if version != expected:
            mismatches.append(f"{location} = {version}")

    test_text = (repo_root / TEST_FILE_REL).read_text(encoding="utf-8")
    expected_match = _EXPECTED_RE.search(test_text)
    if not expected_match:
        mismatches.append(f"{TEST_FILE_REL}::EXPECTED_DEDIREN_VERSION not found")
    elif expected_match.group(1) != expected:
        mismatches.append(f"{TEST_FILE_REL}::EXPECTED_DEDIREN_VERSION = {expected_match.group(1)}")

    grounding = (repo_root / SOURCE_GROUNDING_REL).read_text(encoding="utf-8")
    if expected not in grounding:
        mismatches.append(f"{SOURCE_GROUNDING_REL}: no pinned-{expected} claim")

    return mismatches


def bump(repo_root: Path, new_version: str, *, check: bool = False) -> BumpReport:
    """Move every embedded pin from the current SoT to ``new_version``.

    Validates the target CalVer shape, refuses when the current pins have drifted apart,
    performs a scoped literal replace, and (unless ``check``) re-verifies that no pin was
    missed. ``check`` reports the plan without writing."""
    if not CALVER_RE.match(new_version):
        raise ValueError(f"not a CalVer version: {new_version!r}")

    old = current_version(repo_root)
    report = BumpReport(old=old, new=new_version)
    if new_version == old:
        return report  # already pinned to the target; nothing to do

    drift = verify(repo_root, old)
    if drift:
        raise PinDriftError(
            f"existing pins already differ from the release-script default {old!r}; "
            "fix drift before bumping:\n  " + "\n  ".join(drift)
        )

    for path in target_files(repo_root):
        text = path.read_text(encoding="utf-8")
        occurrences = text.count(old)
        if not occurrences:
            continue
        report.changed_files.append(str(path.relative_to(repo_root)))
        report.replacements += occurrences
        if not check:
            path.write_text(text.replace(old, new_version), encoding="utf-8")

    report.changed_files.sort()

    if not check:
        remaining = verify(repo_root, new_version)
        if remaining:
            raise RuntimeError(
                "post-bump verification failed (a pin was missed):\n  "
                + "\n  ".join(remaining)
            )
    return report


def parity_plan(repo_root: Path, target_version: str) -> dict[str, object]:
    """The plan a ``parity`` run would execute: which two versions to compare and which
    bundle surfaces to diff. Pure, so it is testable without downloading anything."""
    return {
        "current": current_version(repo_root),
        "target": target_version,
        "surfaces": list(PARITY_SURFACES),
    }


def _ensure_bundle(repo_root: Path, version: str) -> Path:
    """Download+extract a release bundle via the release resolver and return its dir."""
    env = os.environ.copy()
    env["DEDIREN_VERSION"] = version
    result = subprocess.run(
        ["bash", str(repo_root / RELEASE_SCRIPT_REL), "--ensure-bundle"],
        cwd=repo_root, env=env, check=True, text=True, capture_output=True,
    )
    return Path(result.stdout.strip())


def _bundle_lines(path: Path) -> list[str]:
    """Read a bundle file as keep-ends lines, or an empty list when it is absent."""
    return path.read_text(encoding="utf-8").splitlines(keepends=True) if path.is_file() else []


def run_parity(repo_root: Path, target_version: str, *, out=sys.stdout) -> int:
    """Fetch the current and target bundles and print a diff of the parity surfaces so the
    human can classify the release. Network + resolver bound; not exercised by unit tests."""
    if not CALVER_RE.match(target_version):
        raise ValueError(f"not a CalVer version: {target_version!r}")
    current = current_version(repo_root)
    if target_version == current:
        print(f"target {target_version} equals the current pin; nothing to compare", file=out)
        return 0

    current_bundle = _ensure_bundle(repo_root, current)
    target_bundle = _ensure_bundle(repo_root, target_version)

    changed: list[str] = []
    for pattern in PARITY_SURFACES:
        names = sorted(
            {p.relative_to(current_bundle).as_posix() for p in current_bundle.glob(pattern)}
            | {p.relative_to(target_bundle).as_posix() for p in target_bundle.glob(pattern)}
        )
        for name in names:
            a = current_bundle / name
            b = target_bundle / name
            if a.is_file() and b.is_file() and filecmp.cmp(a, b, shallow=False):
                continue
            changed.append(name)
            try:
                a_lines = _bundle_lines(a)
                b_lines = _bundle_lines(b)
            except UnicodeDecodeError:
                print(f"(binary) {name} differs", file=out)
                continue
            out.writelines(
                difflib.unified_diff(
                    a_lines, b_lines,
                    fromfile=f"{current}/{name}", tofile=f"{target_version}/{name}",
                )
            )

    summary = f"\n{len(changed)} parity surface(s) changed between {current} and {target_version}:"
    print(summary, file=out)
    for name in changed:
        print(f"  {name}", file=out)
    print(
        "\nClassify breaking/additive/cosmetic and update architecture-design support "
        "before running `bump`.",
        file=out,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo-root", type=Path, default=REPO_ROOT,
                        help="repo root to operate on (default: this repo)")

    parser = argparse.ArgumentParser(
        prog="dediren_bump.py",
        description="Scoped, re-verified bump of the embedded Dediren version pins.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("current", parents=[common],
                   help="print the currently pinned Dediren version")

    bump_parser = sub.add_parser("bump", parents=[common],
                                 help="move every embedded Dediren pin to --to")
    bump_parser.add_argument("--to", required=True, help="target Dediren version (CalVer)")
    bump_parser.add_argument("--check", action="store_true",
                             help="report the plan without writing any files")

    parity_parser = sub.add_parser("parity", parents=[common],
                                   help="diff the current vs target release bundles")
    parity_parser.add_argument("--to", required=True, help="target Dediren version (CalVer)")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root: Path = args.repo_root

    if args.command == "current":
        print(current_version(repo_root))
        return 0

    if args.command == "bump":
        try:
            report = bump(repo_root, args.to, check=args.check)
        except (ValueError, PinDriftError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if not report.changed_files:
            print(f"already pinned to {report.new}; nothing to do")
            return 0
        verb = "would change" if args.check else "changed"
        print(
            f"{report.old} -> {report.new}: {verb} {len(report.changed_files)} file(s), "
            f"{report.replacements} pin occurrence(s)"
        )
        for name in report.changed_files:
            print(f"  {name}")
        if not args.check:
            print("re-verify: all pins consistent")
        return 0

    if args.command == "parity":
        try:
            return run_parity(repo_root, args.to)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    return 1


if __name__ == "__main__":
    sys.exit(main())
