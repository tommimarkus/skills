from __future__ import annotations

import re

from .errors import invalid_policy
from .strategy_semver import require_current


PEP440_RE = re.compile(
    r"^(?P<release>\d+(?:\.\d+)*)"
    r"(?:(?P<pre_label>a|b|rc)(?P<pre_num>\d+))?"
    r"(?:\.post(?P<post>\d+))?"
    r"(?:\.dev(?P<dev>\d+))?$"
)


def bump_pep440(request):
    current = require_current(request, "PEP 440")
    match = PEP440_RE.match(current)
    if not match:
        raise invalid_policy(f"invalid supported PEP 440 version: {current}")
    release = release_triplet(match.group("release"))
    stable = f"{release[0]}.{release[1]}.{release[2]}"
    simple = {
        "major": f"{release[0] + 1}.0.0",
        "minor": f"{release[0]}.{release[1] + 1}.0",
        "patch": f"{release[0]}.{release[1]}.{release[2] + 1}",
        "release": stable,
    }
    intent = request.bump or "patch"
    if intent in simple:
        return simple[intent]
    if intent == "prerelease":
        return f"{stable}{next_pre(match, request.pre_label)}"
    if intent == "post":
        return f"{stable}.post{int(match.group('post') or 0) + 1}"
    if intent == "dev":
        return f"{stable}.dev{int(match.group('dev') or 0) + 1}"
    raise invalid_policy(f"unsupported PEP 440 bump: {intent}")


def release_triplet(value):
    release = [int(part) for part in value.split(".")]
    while len(release) < 3:
        release.append(0)
    return release[:3]


def next_pre(match, pre_label):
    label = pre_label if pre_label in {"a", "b", "rc"} else "rc"
    number = 1
    if match.group("pre_label") == label and match.group("pre_num"):
        number = int(match.group("pre_num")) + 1
    return f"{label}{number}"
