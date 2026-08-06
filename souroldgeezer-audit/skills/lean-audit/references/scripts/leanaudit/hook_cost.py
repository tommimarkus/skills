"""Content-free inventory of Claude and Codex hook registrations.

Hook commands are treated as opaque configuration values: this module records
only their presence and never returns or executes them. Runtime observations are
accepted only as explicitly supplied, content-free fixture metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeGuard

from leanaudit.json_rows import read_json_rows

__all__ = [
    "analyze_hook_registrations",
    "is_hook_config_path",
    "read_hook_fixture_file",
]


_UNKNOWN = "unknown"
_SELECTOR_FIELDS = ("path", "event", "registration_index", "hook_index")
_EVIDENCE_FIELDS = ("enabled", "visibility", "frequency", "proxy_tokens")
_ALLOWED_FIXTURE_FIELDS = frozenset((*_SELECTOR_FIELDS, *_EVIDENCE_FIELDS))
_VISIBILITIES = frozenset(("model", "out-of-band"))


def _is_non_negative_int(value: Any) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _runtime_for_path(path: str) -> str | None:
    normalized = path.replace("\\", "/")
    if normalized == ".codex/hooks.json" or normalized.endswith("/.codex/hooks.json"):
        return "codex"
    if normalized == ".claude/settings.json" or normalized.endswith("/.claude/settings.json"):
        return "claude"
    return None


def is_hook_config_path(path: str) -> bool:
    """Return whether path names a recognized project/user hook configuration."""
    return _runtime_for_path(path) is not None


def _unsupported(
    kind: str,
    path: str,
    reason: str,
    *,
    event: str | None = None,
    registration_index: int | None = None,
    hook_index: int | None = None,
) -> dict[str, str | int]:
    row: dict[str, str | int] = {"kind": kind, "path": path, "reason": reason}
    if event is not None:
        row["event"] = event
    if registration_index is not None:
        row["registration_index"] = registration_index
    if hook_index is not None:
        row["hook_index"] = hook_index
    return row


def _parse_config(
    path: str,
    text: str,
    runtime: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str | int]]]:
    registrations: list[dict[str, Any]] = []
    unsupported: list[dict[str, str | int]] = []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        unsupported.append(
            _unsupported(
                "config-json",
                path,
                f"invalid JSON at line {exc.lineno}, column {exc.colno}",
            )
        )
        return registrations, unsupported
    # Config shape failures intentionally share one append-and-return contract.
    # lean-audit:dup-intentional:begin
    if not isinstance(payload, dict):
        unsupported.append(_unsupported("config-format", path, "root must be an object"))
        return registrations, unsupported
    # lean-audit:dup-intentional:end
    hooks = payload.get("hooks")
    if hooks is None:
        return registrations, unsupported
    if not isinstance(hooks, dict):
        unsupported.append(_unsupported("config-format", path, "hooks must be an object"))
        return registrations, unsupported

    for event, event_rows in sorted(hooks.items()):
        # Nested config-shape rejections deliberately preserve explicit location fields.
        # lean-audit:dup-intentional:begin
        if not isinstance(event_rows, list):
            unsupported.append(
                _unsupported(
                    "event-format",
                    path,
                    "event registrations must be a list",
                    event=event,
                )
            )
            continue
        # lean-audit:dup-intentional:end
        for registration_index, registration in enumerate(event_rows):
            if not isinstance(registration, dict):
                unsupported.append(
                    _unsupported(
                        "registration-format",
                        path,
                        "registration must be an object",
                        event=event,
                        registration_index=registration_index,
                    )
                )
                continue
            hook_rows = registration.get("hooks")
            if not isinstance(hook_rows, list):
                unsupported.append(
                    _unsupported(
                        "registration-format",
                        path,
                        "registration hooks must be a list",
                        event=event,
                        registration_index=registration_index,
                    )
                )
                continue
            for hook_index, hook in enumerate(hook_rows):
                location = {
                    "event": event,
                    "registration_index": registration_index,
                    "hook_index": hook_index,
                }
                # Hook-shape/type rejections intentionally share the same safe ledger form.
                # lean-audit:dup-intentional:begin
                if not isinstance(hook, dict):
                    unsupported.append(
                        _unsupported(
                            "hook-format",
                            path,
                            "hook must be an object",
                            **location,
                        )
                    )
                    continue
                # lean-audit:dup-intentional:end
                if hook.get("type") != "command":
                    unsupported.append(
                        _unsupported(
                            "hook-type",
                            path,
                            "only command hooks are recognized",
                            **location,
                        )
                    )
                    continue
                command = hook.get("command")
                if not isinstance(command, str) or not command.strip():
                    unsupported.append(
                        _unsupported(
                            "hook-format",
                            path,
                            "command hook needs a non-empty opaque command",
                            **location,
                        )
                    )
                    continue
                registrations.append(
                    {
                        "runtime": runtime,
                        "path": path,
                        **location,
                        "hook_type": "command",
                        "command_present": True,
                    }
                )
    return registrations, unsupported


def _selector(row: dict[str, Any]) -> tuple[str, str, int, int] | None:
    path = row.get("path")
    event = row.get("event")
    registration_index = row.get("registration_index")
    hook_index = row.get("hook_index")
    if not isinstance(path, str) or not isinstance(event, str):
        return None
    if not _is_non_negative_int(registration_index) or not _is_non_negative_int(hook_index):
        return None
    return path, event, registration_index, hook_index


def _validate_fixture_row(row: dict[str, Any]) -> str | None:
    extra = sorted(set(row) - _ALLOWED_FIXTURE_FIELDS)
    if extra:
        return "unsupported fields: " + ", ".join(extra)
    if _selector(row) is None:
        return "fixture needs string path/event and non-negative integer indices"
    if not any(field in row for field in _EVIDENCE_FIELDS):
        return "fixture supplies no evidence fields"
    if "enabled" in row and not isinstance(row["enabled"], bool):
        return "enabled must be boolean when supplied"
    if "visibility" in row and row["visibility"] not in _VISIBILITIES:
        return "visibility must be model or out-of-band when supplied"
    for field in ("frequency", "proxy_tokens"):
        if field in row and not _is_non_negative_int(row[field]):
            return f"{field} must be a non-negative integer when supplied"
    return None


def _selector_problem(
    kind: str,
    selector: tuple[str, str, int, int],
    reason: str,
) -> dict[str, str | int]:
    return _unsupported(
        kind,
        selector[0],
        reason,
        event=selector[1],
        registration_index=selector[2],
        hook_index=selector[3],
    )


# Analyzer signatures and local result ledgers intentionally mirror sibling analyzers.
# lean-audit:dup-intentional:begin
def analyze_hook_registrations(
    files: dict[str, str],
    fixture_metadata: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Inventory recognized hook configs and join content-free supplied evidence."""
    registrations: list[dict[str, Any]] = []
    unsupported: list[dict[str, str | int]] = []
    # lean-audit:dup-intentional:end
    config_file_count = 0
    for path, body in sorted(files.items()):
        runtime = _runtime_for_path(path)
        if runtime is None:
            continue
        config_file_count += 1
        parsed, rejected = _parse_config(path, body, runtime)
        registrations.extend(parsed)
        unsupported.extend(rejected)

    registrations.sort(
        key=lambda row: (
            str(row["path"]),
            str(row["event"]),
            int(row["registration_index"]),
            int(row["hook_index"]),
        )
    )
    known = {
        (
            str(row["path"]),
            str(row["event"]),
            int(row["registration_index"]),
            int(row["hook_index"]),
        )
        for row in registrations
    }
    supplied: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for index, fixture in enumerate(fixture_metadata or []):
        if not isinstance(fixture, dict):
            unsupported.append(
                _unsupported("fixture-format", f"fixture[{index}]", "fixture row must be an object")
            )
            continue
        reason = _validate_fixture_row(fixture)
        selector = _selector(fixture)
        fixture_path = fixture.get("path")
        safe_path = fixture_path if isinstance(fixture_path, str) else f"fixture[{index}]"
        if reason is not None or selector is None:
            unsupported.append(
                _unsupported("fixture-format", safe_path, reason or "invalid selector")
            )
            continue
        if selector not in known:
            unsupported.append(
                _selector_problem(
                    "fixture-unmatched",
                    selector,
                    "fixture selector matches no recognized registration",
                )
            )
            continue
        if selector in supplied:
            unsupported.append(
                _selector_problem(
                    "fixture-duplicate",
                    selector,
                    "duplicate fixture selector",
                )
            )
            continue
        supplied[selector] = {
            field: fixture[field] for field in _EVIDENCE_FIELDS if field in fixture
        }

    effective_metadata: list[dict[str, Any]] = []
    for registration in registrations:
        key = (
            str(registration["path"]),
            str(registration["event"]),
            int(registration["registration_index"]),
            int(registration["hook_index"]),
        )
        evidence = supplied.get(key, {})
        effective_metadata.append(
            {
                "path": key[0],
                "event": key[1],
                "registration_index": key[2],
                "hook_index": key[3],
                **{field: evidence.get(field, _UNKNOWN) for field in _EVIDENCE_FIELDS},
                "evidence_source": "supplied-fixture" if evidence else _UNKNOWN,
            }
        )

    token_values = [
        int(row["proxy_tokens"])
        for row in effective_metadata
        if _is_non_negative_int(row["proxy_tokens"])
    ]
    model_injected_rows = [
        row
        for row in effective_metadata
        if row["enabled"] is True
        and row["visibility"] == "model"
        and _is_non_negative_int(row["frequency"])
        and _is_non_negative_int(row["proxy_tokens"])
    ]
    model_injected_values = [
        int(row["frequency"]) * int(row["proxy_tokens"]) for row in model_injected_rows
    ]
    events: dict[str, int] = {}
    for registration in registrations:
        event = str(registration["event"])
        events[event] = events.get(event, 0) + 1
    return {
        "config_file_count": config_file_count,
        "registrations": registrations,
        "registrations_by_event": dict(sorted(events.items())),
        "fixture_metadata": effective_metadata,
        "evidenced_proxy_tokens": sum(token_values) if token_values else _UNKNOWN,
        "proxy_token_evidence_count": len(token_values),
        "model_injected_proxy_tokens": (
            sum(model_injected_values) if model_injected_values else _UNKNOWN
        ),
        "model_injected_evidence_count": len(model_injected_values),
        "unsupported": unsupported,
        "content_policy": "metadata-only; hook commands opaque",
        "execution_policy": "configuration parsed; commands never executed",
    }


def read_hook_fixture_file(path: Path) -> list[dict[str, Any]]:
    """Read content-free fixture rows from a JSON object/list or JSONL file."""
    return read_json_rows(
        path,
        scalar_error="every hook fixture row must be an object",
        row_error="every hook fixture row must be an object",
    )
