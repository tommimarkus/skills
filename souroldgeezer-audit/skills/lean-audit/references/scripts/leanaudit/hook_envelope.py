"""Shared PreToolUse/Stop hook envelope helpers: payload parsing, decision shaping,
and fail-open diagnostics logging."""

from __future__ import annotations

import json
import sys
from typing import Any, TypedDict

__all__ = ["HookPayload", "fail_open_log", "permission_decision", "read_payload"]


class HookPayload(TypedDict, total=False):
    tool_name: str
    tool_input: dict[str, Any]
    cwd: str
    host: str


def read_payload(stream: Any = None) -> HookPayload:
    """Parse the PreToolUse/Stop JSON envelope from stdin (or a given stream)."""
    raw = (stream or sys.stdin).read()
    data = json.loads(raw)
    tool_call = data.get("toolCall")
    workspace_paths = data.get("workspacePaths")
    is_antigravity = (
        isinstance(tool_call, dict)
        or isinstance(workspace_paths, list)
        or "terminationReason" in data
    )
    if isinstance(tool_call, dict):
        tool_name = str(tool_call.get("name", ""))
        tool_input = dict(tool_call.get("args") or {})
        if "file_path" not in tool_input and isinstance(tool_input.get("Path"), str):
            tool_input["file_path"] = tool_input["Path"]
    else:
        tool_name = str(data.get("tool_name", ""))
        tool_input = dict(data.get("tool_input") or {})
    cwd = str(data.get("cwd", ""))
    if not cwd and isinstance(workspace_paths, list) and workspace_paths:
        first_ws = workspace_paths[0]
        if isinstance(first_ws, str):
            cwd = first_ws
    payload: HookPayload = {
        "tool_name": tool_name,
        "tool_input": tool_input,
        "cwd": cwd,
    }
    if is_antigravity:
        payload["host"] = "antigravity"
    return payload


def permission_decision(decision: str, reason: str, *, host: str | None = None) -> dict[str, Any]:
    """The PreToolUse decision dict for Claude Code / Codex or Antigravity."""
    if host == "antigravity":
        return {"decision": decision, "reason": reason}
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
