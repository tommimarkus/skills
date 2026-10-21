"""Planning ledger core: errors, canonical encoding, identifiers, time, validation primitives and path anchors."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .vocabulary import ID, MAX_PATH, PROXY_TOKEN_RE, RETENTION_DAYS, SHA

__all__ = [
    "Error",
    "timestamp",
    "retained_until",
    "bounded_reason",
    "canon",
    "digest",
    "out",
    "ident",
    "uuid4",
    "rel",
    "parent",
    "approved_parent",
    "selected_step",
    "dependency_order",
    "read_json",
    "required_file",
    "require_sha256",
    "proxy_tokens",
    "UsageError",
    "SCRIPTS_DIR",
    "LEDGER_SCRIPT",
    "HOST_TIERS_FILE",
    "WORKTREE_HELPER",
]


# Every script path derives from the one directory that holds the entry shim.
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
LEDGER_SCRIPT = SCRIPTS_DIR / "planning_ledger.py"
HOST_TIERS_FILE = SCRIPTS_DIR.parent / "host-tiers.json"
WORKTREE_HELPER = SCRIPTS_DIR.parents[2] / "git-workflow-policy/references/scripts/planning_worktree.py"


class Error(Exception):
    pass


def now():
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp(value, label="timestamp"):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise Error(f"invalid {label}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise Error(f"invalid {label}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise Error(f"invalid {label}")
    return parsed


def retained_until(closed_at, outcome):
    return (
        (timestamp(closed_at, "closed_at") + timedelta(days=RETENTION_DAYS[outcome]))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def bounded_reason(value, label, required=False):
    if not isinstance(value, str) or len(value) > 480 or (required and not value):
        raise Error(f"{label} requires a bounded reason")
    return value


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(canon(value)).hexdigest()


def out(value, code=0):
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return code


def ident(value, label="id"):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise Error(f"invalid {label}")
    return value


def uuid4(value, label="run id"):
    try:
        parsed = uuid.UUID(value)
    except (TypeError, ValueError) as exc:
        raise Error(f"{label} must be canonical lowercase UUID4") from exc
    if parsed.version != 4 or str(parsed) != value:
        raise Error(f"{label} must be canonical lowercase UUID4")
    return value


def rel(value, label="path", maximum=MAX_PATH):
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or Path(value).is_absolute()
        or ".." in Path(value).parts
    ):
        raise Error(f"invalid relative {label}")
    return value


def parent(actor):
    if actor != "parent":
        raise Error("only actor 'parent' may mutate a ledger")


def approved_parent(args):
    parent(args.actor)
    if not args.approved:
        raise Error("--approved is required")


def selected_step(data, step_id):
    sid = ident(step_id, "step id")
    if sid not in data["steps"]:
        raise Error("unknown step id")
    return sid, data["steps"][sid]


def dependency_order(steps):
    """Reject unknown or cyclic step dependencies."""
    if any(dep not in steps for step in steps.values() for dep in step["dependencies"]):
        raise Error("unknown dependency")
    visiting, visited = set(), set()

    def visit(step_id):
        if step_id in visiting:
            raise Error("dependency cycle")
        if step_id not in visited:
            visiting.add(step_id)
            for dependency in steps[step_id]["dependencies"]:
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

    for step_id in steps:
        visit(step_id)


def read_json(path, message):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise Error(message) from exc


def required_file(directory, name, message):
    path = directory / name
    if not path.is_file():
        raise Error(message)
    return path


def require_sha256(value, message):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise Error(message)


def proxy_tokens(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return len(PROXY_TOKEN_RE.findall(encoded))


class UsageError(Error):
    """A malformed or inapplicable invocation, reported with exit status 2."""
