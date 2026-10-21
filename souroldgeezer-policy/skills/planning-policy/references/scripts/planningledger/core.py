"""Planning ledger core: errors, canonical encoding, identifiers, time, validation primitives and
path anchors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TypeAlias

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
    "read_bounded_json",
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


# The shared JSON shapes. They are annotation-only aliases, so they stay out of __all__
# and the entry shim never re-exports them.
JsonValue: TypeAlias = Any  # A decoded JSON value no check has narrowed yet.
JsonObject: TypeAlias = dict[str, Any]  # A JSON object: a plan, checkpoint, step or record.


# Every script path derives from the one directory that holds the entry shim.
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
LEDGER_SCRIPT = SCRIPTS_DIR / "planning_ledger.py"
HOST_TIERS_FILE = SCRIPTS_DIR.parent / "host-tiers.json"
WORKTREE_HELPER = (
    SCRIPTS_DIR.parents[2] / "git-workflow-policy/references/scripts/planning_worktree.py"
)


class Error(Exception):
    pass


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp(value: object, label: str = "timestamp") -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise Error(f"invalid {label}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise Error(f"invalid {label}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise Error(f"invalid {label}")
    return parsed


def retained_until(closed_at: str, outcome: str) -> str:
    return (
        (timestamp(closed_at, "closed_at") + timedelta(days=RETENTION_DAYS[outcome]))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def bounded_reason(value: object, label: str, required: bool = False) -> str:
    if not isinstance(value, str) or len(value) > 480 or (required and not value):
        raise Error(f"{label} requires a bounded reason")
    return value


def canon(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canon(value)).hexdigest()


def out(value: object, code: int = 0) -> int:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return code


def ident(value: object, label: str = "id") -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise Error(f"invalid {label}")
    return value


def uuid4(value: JsonValue, label: str = "run id") -> str:
    try:
        parsed = uuid.UUID(value)
    except (TypeError, ValueError) as exc:
        raise Error(f"{label} must be canonical lowercase UUID4") from exc
    canonical = str(parsed)
    if parsed.version != 4 or canonical != value:
        raise Error(f"{label} must be canonical lowercase UUID4")
    return canonical


def rel(value: object, label: str = "path", maximum: int = MAX_PATH) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or Path(value).is_absolute()
        or ".." in Path(value).parts
    ):
        raise Error(f"invalid relative {label}")
    return value


def parent(actor: str) -> None:
    if actor != "parent":
        raise Error("only actor 'parent' may mutate a ledger")


def approved_parent(args: argparse.Namespace) -> None:
    parent(args.actor)
    if not args.approved:
        raise Error("--approved is required")


def selected_step(data: JsonObject, step_id: object) -> tuple[str, JsonObject]:
    sid = ident(step_id, "step id")
    if sid not in data["steps"]:
        raise Error("unknown step id")
    return sid, data["steps"][sid]


def dependency_order(steps: dict[str, JsonObject]) -> None:
    """Reject unknown or cyclic step dependencies."""
    if any(dep not in steps for step in steps.values() for dep in step["dependencies"]):
        raise Error("unknown dependency")
    visiting, visited = set(), set()

    def visit(step_id: str) -> None:
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


def read_json(path: str | Path, message: str) -> JsonValue:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise Error(message) from exc


def read_bounded_json(path: str | Path, limit: int, invalid: str, oversize: str) -> JsonValue:
    """Parse a JSON file, then cap its size: an unparsable file reports `invalid`."""
    try:
        raw = Path(path).read_bytes()
        value: JsonValue = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error(invalid) from exc
    if len(raw) > limit:
        raise Error(oversize)
    return value


def required_file(directory: Path, name: str, message: str) -> Path:
    path = directory / name
    if not path.is_file():
        raise Error(message)
    return path


def require_sha256(value: object, message: str) -> None:
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise Error(message)


def proxy_tokens(value: object) -> int:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return len(PROXY_TOKEN_RE.findall(encoded))


class UsageError(Error):
    """A malformed or inapplicable invocation, reported with exit status 2."""
