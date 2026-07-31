"""lean-audit PreToolUse guard hook (opt-in, fail-open).

Soft-blocks an Edit/Write/MultiEdit or Codex apply_patch that would introduce a NEW block-severity
duplication into guarded markdown. Reads the PreToolUse JSON on stdin, emits a
`deny` decision on a block hit, and ALWAYS allows (exit 0, no stdout) on any
error, non-match, or non-guarded path. Carve-outs and the sync-intentional
override are inherited from the engine — this hook adds no duplication logic.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from leanaudit import hook_envelope
from leanaudit.discovery import is_guarded
from leanaudit.engine import evaluate_added_block
from leanaudit.hook_envelope import HookPayload

__all__ = ["evaluate", "main"]


# Which tool_input key holds the added text for the single-payload tools.
_ADDED_TEXT_KEY = {"Write": "content", "Edit": "new_string"}


def _added_content(tool_name: str, tool_input: dict[str, Any]) -> str | None:
    key = _ADDED_TEXT_KEY.get(tool_name)
    if key is not None:
        c = tool_input.get(key)
        return c if isinstance(c, str) and c else None
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits")
        if isinstance(edits, list):
            parts = [e.get("new_string", "") for e in edits if isinstance(e, dict)]
            joined = "\n".join(p for p in parts if isinstance(p, str))
            return joined or None
    return None


def _apply_patch_edits(command: str) -> list[tuple[str, str]]:
    """Extract ``(path, added text)`` pairs from Codex apply_patch input.

    This is deliberately narrow: malformed or unfamiliar patch input returns
    fewer/no candidates and therefore preserves the guard's fail-open contract.
    """
    edits: list[tuple[str, str]] = []
    path: str | None = None
    added: list[str] = []

    def flush() -> None:
        nonlocal path, added
        if path and added:
            edits.append((path, "\n".join(added)))
        path = None
        added = []

    for line in command.splitlines():
        if line.startswith(("*** Add File: ", "*** Update File: ")):
            flush()
            path = line.split(": ", 1)[1].strip()
            continue
        if line.startswith(("*** Delete File: ", "*** End Patch")):
            flush()
            continue
        if path and line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
    flush()
    return edits


def _repo_root(cwd: str) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except Exception as exc:
        # A non-repo cwd exits via returncode != 0 without raising; this fires
        # only on real execution failure (git missing, timeout, OSError).
        hook_envelope.fail_open_log("lean-guard", "repo-root", exc)
        return None
    return None


def _evaluate_edit(root: Path, file_path: str, content: str) -> str | None:
    try:
        candidate = Path(file_path)
        if not candidate.is_absolute():
            candidate = root / candidate
        rel = candidate.resolve().relative_to(root).as_posix()
    except Exception:
        return None  # edit is outside the repo or unresolvable path
    try:
        if not is_guarded(rel):
            return None
        findings = evaluate_added_block(root, rel, content, None)
    except Exception as exc:
        hook_envelope.fail_open_log("lean-guard", "engine-evaluate", exc)
        return None  # fail-open on engine error
    blocks = [f for f in findings if f.severity == "block"]
    if not blocks:
        return None
    try:
        f = blocks[0]
        return (
            f"lean-audit: this edit to {rel} duplicates "
            f'{f.matched_path} §"{f.matched_heading}" '
            f"(containment={f.containment}). {f.action} "
            "To override: cite the canonical source, restructure, or add "
            "'<!-- lean-audit:sync-intentional: <reason> -->' to the block."
        )
    except Exception as exc:
        hook_envelope.fail_open_log("lean-guard", "reason-format", exc)
        return None


def evaluate(payload: HookPayload) -> str | None:
    """Return a deny-reason if the edit introduces a block dup, else None."""
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    root = _repo_root(payload.get("cwd") or os.getcwd())
    if root is None:
        return None

    if tool_name == "apply_patch":
        command = tool_input.get("command")
        if not isinstance(command, str):
            return None
        for patch_path, patch_content in _apply_patch_edits(command):
            reason = _evaluate_edit(root, patch_path, patch_content)
            if reason:
                return reason
        return None

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return None
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return None
    content = _added_content(tool_name, tool_input)
    if not content:
        return None
    return _evaluate_edit(root, file_path, content)


def main() -> None:
    try:
        payload = hook_envelope.read_payload()
    except Exception:
        return  # fail-open: unreadable input
    try:
        reason = evaluate(payload) if isinstance(payload, dict) else None
    except Exception as exc:
        hook_envelope.fail_open_log("lean-guard", "main-backstop", exc)
        reason = None  # backstop fail-open
    if reason:
        print(json.dumps(hook_envelope.permission_decision("deny", reason)))
