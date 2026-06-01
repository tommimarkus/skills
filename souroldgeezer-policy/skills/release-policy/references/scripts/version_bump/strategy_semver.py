from __future__ import annotations

import re

from .errors import invalid_policy


SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z][0-9A-Za-z.-]*))?"
    r"(?:\+(?P<build>[0-9A-Za-z][0-9A-Za-z.-]*))?$"
)


def bump_semver(request):
    current = require_current(request, "SemVer")
    match = SEMVER_RE.match(current)
    if not match:
        raise invalid_policy(f"invalid SemVer version: {current}")
    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))
    stable = f"{major}.{minor}.{patch}"
    simple = {
        "major": f"{major + 1}.0.0",
        "minor": f"{major}.{minor + 1}.0",
        "patch": f"{major}.{minor}.{patch + 1}",
        "release": stable,
    }
    intent = request.bump or "patch"
    if intent in simple:
        return simple[intent]
    if intent == "prerelease":
        return f"{stable}-{next_prerelease(match.group('pre'), request.pre_label)}"
    if intent == "build":
        suffix = f"-{match.group('pre')}" if match.group("pre") else ""
        return f"{stable}{suffix}+{next_build(match.group('build'))}"
    raise invalid_policy(f"unsupported SemVer bump: {intent}")


def require_current(request, strategy_name):
    if not request.current:
        raise invalid_policy(f"{strategy_name} requires --current or readable --source")
    return request.current


def next_prerelease(existing, label):
    if not existing:
        return f"{label}.1"
    match = re.match(r"^" + re.escape(label) + r"\.(?P<num>\d+)$", existing)
    return f"{label}.{int(match.group('num')) + 1}" if match else f"{label}.1"


def next_build(existing):
    if not existing:
        return "build.1"
    match = re.match(r"^build\.(?P<num>\d+)$", existing)
    return f"build.{int(match.group('num')) + 1}" if match else "build.1"
