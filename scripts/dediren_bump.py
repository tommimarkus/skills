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

Stdlib-only responsibilities:

- ``current``: print the pinned version, read from the single source of truth
  (``DEDIREN_VERSION_DEFAULT`` in the release script).
- ``latest``: print the newest published release, resolved by following GitHub's
  ``/releases/latest`` redirect (stdlib-only, no API token). ``bump`` / ``parity`` /
  ``adopt`` also accept ``--to latest`` to target it without a lookup.
- ``bump --to X [--check]``: replace the current pin with ``X`` across *only* the known
  dediren-pin surfaces — and, within those, only the live pins, leaving historical
  ``Dediren <version>`` release markers (the version a capability landed in) fixed — then
  re-run the same pin discovery the release test's guard uses and fail if any pin still
  differs. ``--check`` reports the plan without writing. Refuses when a pin has already
  drifted off the SoT.
- ``parity --to X``: fetch the current and target release bundles via the release
  resolver and diff the judgment surfaces (agent-usage guide, plugin manifests, schemas,
  fixtures, bundle manifest) so the human feature-parity classification reads a diff.
- ``adopt --to X [--plan] [--json]``: the one-shot, non-interactive driver a weak model
  can run end to end. Preflight → parity + *auto-classification* (cosmetic when the
  upstream bundle changed only version strings, else non-cosmetic) → bump → a parallel
  verify gate (smoke pipeline + surface tests + whitespace check) → a single verdict
  with the exact next actions and the on-``main`` integration recipe. It never prompts:
  the two irreducibly human/model steps (in-depth ip-hygiene, new-capability skill
  support) are emitted as ``NEXT`` lines, not interactive gates. Exit 0 = ready to
  integrate, 1 = a verify gate failed, 2 = preflight/parity could not proceed.

The tool performs the *mechanical* bump, *auto-classifies* against the bundle diff, and
feeds the residual *judgment* steps as next actions; it never edits architecture.md,
never applies the CalVer stamp, and never mutates ``main`` (both owned by
``version_stamp.py`` at integration).
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ARCH_REFS_REL = "souroldgeezer-architecture/skills/architecture-design/references"
RELEASE_SCRIPT_REL = f"{ARCH_REFS_REL}/scripts/dediren-release.sh"
TEST_FILE_REL = "tests/architecture_dediren_release_test.py"
SOURCE_GROUNDING_REL = f"{ARCH_REFS_REL}/source-grounding.md"

# The plugin whose CalVer stamp a dediren adoption re-stamps at integration.
INTEGRATION_PLUGIN = "souroldgeezer-architecture"

CALVER_RE = re.compile(r"^\d{4}\.\d{2}\.\d+$")

_DEFAULT_RE = re.compile(r'DEDIREN_VERSION_DEFAULT="([^"]+)"')
_EXPECTED_RE = re.compile(r'EXPECTED_DEDIREN_VERSION\s*=\s*"([^"]+)"')
# Mirror the release test's pin discovery so this tool and the guard test agree on the
# set of pins that a bump must move.
_REQUIRED_PLUGINS_ARRAY = re.compile(r'"required_plugins"\s*:\s*\[(.*?)\]', re.DOTALL)
_PLUGIN_PIN = re.compile(r'"id"\s*:\s*"([^"]+)"\s*,\s*"version"\s*:\s*"([^"]+)"')

# Latest-release resolution: follow GitHub's ``/releases/latest`` redirect (stdlib-only,
# no API token) so ``--to latest`` / the ``latest`` command can target the newest release
# without the caller having to look it up. Host and repo are overridable for tests / forks.
GITHUB_HOST = os.environ.get("DEDIREN_GITHUB_HOST", "https://github.com").rstrip("/")
_RELEASE_TAG_RE = re.compile(r"/releases/tag/v?([^/]+)/?$")
_REPO_SLUG_RE = re.compile(r'DEDIREN_REPO_DEFAULT="([^"]+)"')

# Release-bundle subpaths whose change between two versions may signal a runtime-contract
# shift the human must classify. Read-only diff surfaces for ``parity`` / ``adopt``.
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


def _repo_slug(repo_root: Path = REPO_ROOT) -> str:
    """The GitHub ``owner/repo`` of the pinned runtime: ``DEDIREN_REPO`` env override, else
    the release script's single source of truth (``DEDIREN_REPO_DEFAULT``)."""
    env = os.environ.get("DEDIREN_REPO")
    if env:
        return env
    text = (repo_root / RELEASE_SCRIPT_REL).read_text(encoding="utf-8")
    match = _REPO_SLUG_RE.search(text)
    if not match:
        raise RuntimeError(f"{RELEASE_SCRIPT_REL}: DEDIREN_REPO_DEFAULT not found")
    return match.group(1)


def _parse_release_tag(url: str) -> str:
    """Extract a CalVer version from a GitHub ``/releases/tag/v<version>`` URL. Pure."""
    match = _RELEASE_TAG_RE.search(url)
    if not match:
        raise RuntimeError(f"cannot parse a release tag from {url!r}")
    version = match.group(1)
    if not CALVER_RE.match(version):
        raise RuntimeError(f"latest release tag {version!r} is not CalVer (YYYY.0M.MICRO)")
    return version


def resolve_latest(repo_root: Path = REPO_ROOT) -> str:
    """Resolve the newest published release version by following GitHub's
    ``/releases/latest`` redirect. Stdlib-only, no API token; raises ``RuntimeError`` when
    the network is unavailable or the redirect target is not a CalVer tag."""
    url = f"{GITHUB_HOST}/{_repo_slug(repo_root)}/releases/latest"
    request = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": "dediren_bump"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            final_url = response.geturl()
    except (urllib.error.URLError, OSError) as exc:
        raise RuntimeError(f"could not resolve latest release from {url}: {exc}") from exc
    return _parse_release_tag(final_url)


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


def scoped_pin_replace(text: str, old: str, new: str) -> tuple[str, int]:
    """Replace live-pin occurrences of ``old`` with ``new`` while leaving historical
    ``Dediren <old>`` release markers fixed. Returns ``(new_text, replacements)``.

    A live pin is only ever the bare version string in a machine surface
    (``"version": "<v>"``, ``DEDIREN_VERSION_DEFAULT="<v>"``,
    ``EXPECTED_DEDIREN_VERSION = "<v>"``) or a "pinned <v>" claim — none of them
    runtime-name-qualified. A historical marker names the release a capability landed in
    ("Dediren <v> added/retired ...", "Since dediren <v> ...") and must stay fixed across
    a bump. A blanket ``str.replace`` corrupts those markers the moment one cites the
    currently-pinned version; a negative lookbehind on the runtime name keeps only live
    pins in scope. The lookbehind is case-insensitive on the runtime name because prose
    and code comments lowercase it mid-sentence ("Since dediren <v>")."""
    return re.compile(r"(?<![Dd]ediren )" + re.escape(old)).subn(new, text)


def bump(repo_root: Path, new_version: str, *, check: bool = False) -> BumpReport:
    """Move every embedded pin from the current SoT to ``new_version``.

    Validates the target CalVer shape, refuses when the current pins have drifted apart,
    performs a pin-scoped replace that leaves historical ``Dediren <version>`` release
    markers fixed (see ``scoped_pin_replace``), and (unless ``check``) re-verifies that no
    pin was missed. ``check`` reports the plan without writing."""
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
        replaced, occurrences = scoped_pin_replace(text, old, new_version)
        if not occurrences:
            continue
        report.changed_files.append(str(path.relative_to(repo_root)))
        report.replacements += occurrences
        if not check:
            path.write_text(replaced, encoding="utf-8")

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


def _read_surface(path: Path) -> str | bytes | None:
    """A bundle surface as text (``str``), raw bytes when it is not UTF-8, or ``None``
    when it is absent in that release."""
    if not path.is_file():
        return None
    data = path.read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data


def _bundle_surface_names(current_bundle: Path, target_bundle: Path) -> list[str]:
    """The union of ``PARITY_SURFACES`` matches across both bundles, as posix subpaths."""
    names: set[str] = set()
    for pattern in PARITY_SURFACES:
        names |= {p.relative_to(current_bundle).as_posix() for p in current_bundle.glob(pattern)}
        names |= {p.relative_to(target_bundle).as_posix() for p in target_bundle.glob(pattern)}
    return sorted(names)


def collect_parity(
    repo_root: Path, current: str, target: str
) -> list[tuple[str, str | bytes | None, str | bytes | None]]:
    """Fetch both release bundles (in parallel) and return one ``(name, current, target)``
    triple per parity surface, each side ``str`` / ``bytes`` / ``None``. Shared by the
    ``parity`` diff and the ``adopt`` auto-classifier so the glob/read logic lives once."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        current_future = pool.submit(_ensure_bundle, repo_root, current)
        target_future = pool.submit(_ensure_bundle, repo_root, target)
        current_bundle = current_future.result()
        target_bundle = target_future.result()
    surfaces: list[tuple[str, str | bytes | None, str | bytes | None]] = []
    for name in _bundle_surface_names(current_bundle, target_bundle):
        surfaces.append(
            (name, _read_surface(current_bundle / name), _read_surface(target_bundle / name))
        )
    return surfaces


def run_parity(repo_root: Path, target_version: str, *, out=sys.stdout) -> int:
    """Fetch the current and target bundles and print a diff of the parity surfaces so the
    human (or the ``adopt`` classifier) can classify the release. Network + resolver bound;
    not exercised by unit tests."""
    if not CALVER_RE.match(target_version):
        raise ValueError(f"not a CalVer version: {target_version!r}")
    current = current_version(repo_root)
    if target_version == current:
        print(f"target {target_version} equals the current pin; nothing to compare", file=out)
        return 0

    changed: list[str] = []
    for name, a, b in collect_parity(repo_root, current, target_version):
        if a == b:
            continue
        changed.append(name)
        # ``None`` means added/removed between releases; ``bytes`` means a non-UTF-8
        # (binary) surface. Render a real diff for text (incl. add/remove); label binary.
        if isinstance(a, bytes) or isinstance(b, bytes):
            print(f"(binary) {name} differs", file=out)
            continue
        out.writelines(
            difflib.unified_diff(
                a.splitlines(keepends=True) if a else [],
                b.splitlines(keepends=True) if b else [],
                fromfile=f"{current}/{name}", tofile=f"{target_version}/{name}",
            )
        )

    header = f"\n{len(changed)} parity surface(s) changed between {current} and {target_version}:"
    print(header, file=out)
    for name in changed:
        print(f"  {name}", file=out)
    print(
        "\nClassify breaking/additive/cosmetic and update architecture-design support "
        "before running `bump`.",
        file=out,
    )
    return 0


# ---------------------------------------------------------------------------
# adopt: one-shot, non-interactive orchestration of a release adoption.
# ---------------------------------------------------------------------------


def _calver_tuple(version: str) -> tuple[int, int, int]:
    """Component-wise CalVer order so 2026.07.9 sorts *below* 2026.07.10 (string
    comparison gets this wrong)."""
    year, month, micro = version.split(".")
    return int(year), int(month), int(micro)


@dataclass
class AdoptVerdict:
    current: str
    target: str
    stage: str                              # preflight | parity | ready | verify
    ok: bool
    classification: str | None = None       # cosmetic | non-cosmetic
    substantive_surfaces: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    verify_results: list[tuple[str, bool]] = field(default_factory=list)
    integration: list[str] = field(default_factory=list)


def preflight_problems(current: str, target: str, *, dirty_pin_paths: list[str]) -> list[str]:
    """Blocking reasons an adoption cannot start. Pure; the caller supplies git state."""
    if not CALVER_RE.match(target):
        return [f"target {target!r} is not CalVer (YYYY.0M.MICRO)"]
    problems: list[str] = []
    if _calver_tuple(target) < _calver_tuple(current):
        problems.append(f"target {target} is older than the current pin {current}")
    if dirty_pin_paths:
        problems.append(
            "pin surfaces already modified ("
            + ", ".join(sorted(dirty_pin_paths))
            + "); commit or stash them first so the bump is reviewable in isolation"
        )
    return problems


def classify_bundle_change(
    surfaces: list[tuple[str, str | bytes | None, str | bytes | None]], old: str, new: str
) -> tuple[str, list[str]]:
    """Auto-classify an adoption from the upstream bundle diff.

    A surface whose only difference is the ``old`` -> ``new`` version string is cosmetic
    noise; anything else — added/removed content, an added or removed file, or a binary
    change — is a *substantive* (contract-affecting) surface. The adoption is ``cosmetic``
    only when no surface is substantive. Conservative by construction: a change it cannot
    prove is version-only counts as substantive."""
    substantive: list[str] = []
    for name, a, b in surfaces:
        if a is None or b is None:
            if a != b:
                substantive.append(name)
            continue
        if a == b:
            continue
        if isinstance(a, str) and isinstance(b, str) and a.replace(old, new) == b:
            continue
        substantive.append(name)
    return ("cosmetic" if not substantive else "non-cosmetic", substantive)


def integration_recipe(target: str, *, plugin: str = INTEGRATION_PLUGIN) -> list[str]:
    """The exact steps to stamp + sync on ``main`` at integration — never on the branch
    (CLAUDE.md § Plugin versioning: the feature branch carries content only)."""
    return [
        f"git switch main && git merge --ff-only dediren-{target}",
        "uv run python scripts/version_stamp.py guard   # branch must not have stamped a cell",
        f"uv run python scripts/version_stamp.py compute --plugin {plugin}",
        f"# apply that stamp to the two version-authority cells: {plugin}/.claude-plugin/plugin.json",
        "#   and the root README.md version-table row (equal; marketplace entries never carry version),",
        "#   sync the version-sync test expectation, then commit the stamp on main.",
    ]


def next_actions(classification: str, target: str) -> list[str]:
    """The residual model/human steps, spelled out so no interactive gate is needed."""
    if classification == "cosmetic":
        return [
            "Cosmetic maintenance bump: the upstream bundle changed only version strings.",
            "ip-hygiene: a normal scoped triage is enough (no in-depth run required).",
            f"Commit the bump on branch dediren-{target}, then integrate with the recipe below.",
        ]
    return [
        "Non-cosmetic bump: the upstream bundle changed the contract surfaces listed above.",
        "Run the ip-hygiene skill IN-DEPTH over the changed architecture surface before finishing.",
        "Review each substantive surface for a NEW capability. If one needs architecture-design "
        "support, that is feature work — file a follow-up issue and STOP before integrating.",
        'If no new capability is needed, record "maintenance-only, no contract change", commit, '
        "then integrate with the recipe below.",
    ]


def verify_plan() -> list[tuple[str, list[str], dict[str, str]]]:
    """The parallel gate ``adopt`` runs after a bump: full smoke pipeline + dediren surface
    tests + a whitespace check. Pure ``(name, argv, env-overrides)`` triples so a test can
    assert the smoke flag and scope without running the (slow, Java-bound) checks."""
    unittest = [sys.executable, "-m", "unittest"]
    return [
        ("smoke",
         unittest + ["tests.architecture_dediren_release_test"], {"DEDIREN_RELEASE_SMOKE": "1"}),
        ("surface-tests",
         unittest + ["tests.architecture_dediren_surface_test", "tests.dediren_bump_test"], {}),
        ("diff-check", ["git", "diff", "--check"], {}),
    ]


def run_verify(repo_root: Path) -> list[tuple[str, bool, str]]:
    """Run every verify check concurrently; wall-clock is the slowest (the smoke pipeline).
    Returns ``(name, passed, combined-output)`` per check."""
    plan = verify_plan()

    def _run(spec: tuple[str, list[str], dict[str, str]]) -> tuple[str, bool, str]:
        name, argv, env_overrides = spec
        env = os.environ.copy()
        env.update(env_overrides)
        proc = subprocess.run(argv, cwd=repo_root, env=env, text=True, capture_output=True)
        return name, proc.returncode == 0, proc.stdout + proc.stderr

    with ThreadPoolExecutor(max_workers=len(plan)) as pool:
        return list(pool.map(_run, plan))


def _dirty_pin_paths(repo_root: Path) -> list[str]:
    """Pin surfaces with uncommitted changes, per git. Empty for a clean tree or a non-git
    target — the check degrades gracefully rather than blocking (derive from the authority,
    keep a fallback: skill-architecture.md § Degradation Checks)."""
    rels = [str(path.relative_to(repo_root)) for path in target_files(repo_root)]
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--", *rels],
        text=True, capture_output=True,
    )
    if proc.returncode != 0:
        return []
    return [line[3:].strip() for line in proc.stdout.splitlines() if line.strip()]


def _emit_verdict(verdict: AdoptVerdict, *, out=sys.stdout, json_out: bool = False) -> None:
    if json_out:
        payload = {
            "current": verdict.current,
            "target": verdict.target,
            "stage": verdict.stage,
            "ok": verdict.ok,
            "classification": verdict.classification,
            "substantive_surfaces": verdict.substantive_surfaces,
            "problems": verdict.problems,
            "verify": [{"check": name, "ok": ok} for name, ok in verdict.verify_results],
            "next_actions": verdict.next_actions,
            "integration": verdict.integration,
        }
        print(json.dumps(payload, indent=2), file=out)
        return

    heading = f"dediren adopt: {verdict.current} -> {verdict.target}  [stage: {verdict.stage}]"
    print(heading, file=out)
    if verdict.classification:
        print(f"classification: {verdict.classification}", file=out)
    if verdict.substantive_surfaces:
        print("substantive bundle surfaces:", file=out)
        for name in verdict.substantive_surfaces:
            print(f"  - {name}", file=out)
    if verdict.verify_results:
        cells = (f"{name}={'ok' if ok else 'FAIL'}" for name, ok in verdict.verify_results)
        print(f"verify: {'  '.join(cells)}", file=out)
    if verdict.problems:
        print("PROBLEMS:", file=out)
        for problem in verdict.problems:
            print(f"  - {problem}", file=out)
    if verdict.next_actions:
        print("NEXT:", file=out)
        for action in verdict.next_actions:
            print(f"  - {action}", file=out)
    if verdict.integration:
        print("INTEGRATION (run on main after merge, never on the branch):", file=out)
        for line in verdict.integration:
            print(f"  {line}", file=out)
    print(f"\nresult: {'READY' if verdict.ok else 'BLOCKED'}", file=out)


def run_adopt(
    repo_root: Path, target: str, *, plan_only: bool = False, json_out: bool = False, out=sys.stdout
) -> int:
    """Drive a whole adoption non-interactively and print one verdict. See the module
    docstring for the stage sequence and exit codes."""
    if not CALVER_RE.match(target):
        _emit_verdict(
            AdoptVerdict("?", target, "preflight", ok=False,
                         problems=[f"target {target!r} is not CalVer (YYYY.0M.MICRO)"]),
            out=out, json_out=json_out,
        )
        return 2

    current = current_version(repo_root)

    # Idempotent re-run: already pinned to the target -> re-verify only (no re-classify,
    # since the previous version is gone and parity needs two distinct versions).
    if current == target and not plan_only:
        results = run_verify(repo_root)
        ok = all(passed for _, passed, _ in results)
        problems = [] if ok else [f"verify gate '{n}' failed" for n, p, _ in results if not p]
        _emit_verdict(
            AdoptVerdict(
                current, target, "ready" if ok else "verify", ok,
                verify_results=[(name, passed) for name, passed, _ in results],
                next_actions=[f"Already pinned to {target}; re-verified.",
                              "If integrating, use the recipe below."],
                integration=integration_recipe(target) if ok else [],
                problems=problems,
            ),
            out=out, json_out=json_out,
        )
        return 0 if ok else 1

    problems = preflight_problems(current, target, dirty_pin_paths=_dirty_pin_paths(repo_root))
    if problems:
        _emit_verdict(AdoptVerdict(current, target, "preflight", ok=False, problems=problems),
                      out=out, json_out=json_out)
        return 2

    try:
        surfaces = collect_parity(repo_root, current, target)
    except (subprocess.SubprocessError, OSError) as exc:
        _emit_verdict(
            AdoptVerdict(current, target, "parity", ok=False,
                         problems=[f"could not fetch release bundles: {exc}"]),
            out=out, json_out=json_out,
        )
        return 2
    classification, substantive = classify_bundle_change(surfaces, current, target)

    if plan_only:
        plan_actions = ["Plan only: no bump or verify.", *next_actions(classification, target)]
        _emit_verdict(
            AdoptVerdict(
                current, target, "parity", ok=True, classification=classification,
                substantive_surfaces=substantive,
                next_actions=plan_actions,
                integration=integration_recipe(target),
            ),
            out=out, json_out=json_out,
        )
        return 0

    try:
        bump(repo_root, target)
    except (ValueError, PinDriftError) as exc:
        _emit_verdict(AdoptVerdict(current, target, "preflight", ok=False, problems=[str(exc)]),
                      out=out, json_out=json_out)
        return 2

    results = run_verify(repo_root)
    ok = all(passed for _, passed, _ in results)
    if ok:
        verdict = AdoptVerdict(
            current, target, "ready", True, classification, substantive,
            verify_results=[(name, passed) for name, passed, _ in results],
            next_actions=next_actions(classification, target),
            integration=integration_recipe(target),
        )
    else:
        verdict = AdoptVerdict(
            current, target, "verify", False, classification, substantive,
            verify_results=[(name, passed) for name, passed, _ in results],
            problems=[f"verify gate '{name}' failed" for name, passed, _ in results if not passed],
            next_actions=[f"A verify gate failed. Inspect it, fix the cause, then re-run "
                          f"`adopt --to {target}` (idempotent)."],
        )
    _emit_verdict(verdict, out=out, json_out=json_out)
    return 0 if ok else 1


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

    sub.add_parser("latest", parents=[common],
                   help="print the newest published Dediren release version")

    bump_parser = sub.add_parser("bump", parents=[common],
                                 help="move every embedded Dediren pin to --to")
    bump_parser.add_argument("--to", required=True,
                             help="target Dediren version (CalVer, or 'latest')")
    bump_parser.add_argument("--check", action="store_true",
                             help="report the plan without writing any files")

    parity_parser = sub.add_parser("parity", parents=[common],
                                   help="diff the current vs target release bundles")
    parity_parser.add_argument("--to", required=True,
                               help="target Dediren version (CalVer, or 'latest')")

    adopt_parser = sub.add_parser(
        "adopt", parents=[common],
        help="run the adoption (preflight, parity+classify, bump, verify) and print a verdict",
    )
    adopt_parser.add_argument("--to", required=True,
                              help="target Dediren version (CalVer, or 'latest')")
    adopt_parser.add_argument("--plan", action="store_true",
                              help="preflight + parity + classification only; no bump, no verify")
    adopt_parser.add_argument("--json", action="store_true", help="emit the verdict as JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root: Path = args.repo_root

    if args.command == "current":
        print(current_version(repo_root))
        return 0

    if args.command == "latest":
        try:
            print(resolve_latest(repo_root))
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        return 0

    if getattr(args, "to", None) == "latest":
        try:
            args.to = resolve_latest(repo_root)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"resolved latest release -> {args.to}", file=sys.stderr)

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

    if args.command == "adopt":
        return run_adopt(repo_root, args.to, plan_only=args.plan, json_out=args.json)

    return 1


if __name__ == "__main__":
    sys.exit(main())
