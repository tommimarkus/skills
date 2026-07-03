from __future__ import annotations

import json
import sys
from typing import Any, TypedDict

__all__ = ["HookPayload", "read_payload", "permission_decision", "fail_open_log"]


class HookPayload(TypedDict, total=False):
    tool_name: str
    tool_input: dict[str, Any]
    cwd: str


def read_payload(stream: Any = None) -> HookPayload:
    """Parse the PreToolUse JSON envelope from stdin (or a given stream)."""
    raw = (stream or sys.stdin).read()
    data = json.loads(raw)
    return {
        "tool_name": str(data.get("tool_name", "")),
        "tool_input": dict(data.get("tool_input") or {}),
        "cwd": str(data.get("cwd", "")),
    }


def permission_decision(decision: str, reason: str) -> dict[str, Any]:
    """The hookSpecificOutput dict Claude Code parses (deny/allow/ask)."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


def fail_open_log(guard: str, branch: str, exc: BaseException) -> None:
    """One stderr line per swallowed exception; stdout stays decision-only."""
    print(
        f"{guard}: fail-open allow — {type(exc).__name__}: {exc} [{branch}]",
        file=sys.stderr,
    )
