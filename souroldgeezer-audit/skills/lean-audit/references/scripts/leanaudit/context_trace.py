"""Normalize provider and host token-usage traces without retaining content."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = [
    "UsageEvent",
    "normalize_trace_records",
    "read_trace_file",
    "summarize_trace",
]


@dataclass(frozen=True)
class UsageEvent:
    """Content-free token metadata normalized from one trace record."""

    event_id: str
    adapter: str
    stage: str
    actor: str
    visibility: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    cache_write_tokens: int
    reasoning_tokens: int
    tool_result_tokens: int
    total_tokens: int

    def as_dict(self) -> dict[str, str | int]:
        return {
            "event_id": self.event_id,
            "adapter": self.adapter,
            "stage": self.stage,
            "actor": self.actor,
            "visibility": self.visibility,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "tool_result_tokens": self.tool_result_tokens,
            "total_tokens": self.total_tokens,
        }


def _int_value(mapping: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return max(0, int(value))
    return 0


def _text_value(mapping: dict[str, Any], *keys: str, default: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def _find_mapping(record: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    queue: list[dict[str, Any]] = [record]
    seen: set[int] = set()
    while queue:
        current = queue.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))
        for name in names:
            value = current.get(name)
            if isinstance(value, dict):
                return value
        for value in current.values():
            if isinstance(value, dict):
                queue.append(value)
    return {}


def _attributes(record: dict[str, Any]) -> dict[str, Any]:
    attrs = record.get("attributes")
    return attrs if isinstance(attrs, dict) else {}


def _adapter(record: dict[str, Any], usage: dict[str, Any], attrs: dict[str, Any]) -> str:
    attr_keys = " ".join(str(key) for key in attrs)
    event_name = " ".join(
        str(record.get(key, "")) for key in ("name", "event", "method", "source")
    ).lower()
    if any(str(key).startswith("gen_ai.") for key in attrs):
        if "claude" in event_name or "claude" in attr_keys.lower():
            return "claude-code"
        if "codex" in event_name or "codex" in attr_keys.lower():
            return "codex"
        return "otel"
    if "input_tokens_details" in usage or "output_tokens_details" in usage:
        return "openai"
    if "cache_read_input_tokens" in usage or "cache_creation_input_tokens" in usage:
        return "anthropic"
    if "tokenusage" in event_name or "codex" in event_name:
        return "codex"
    if "claude" in event_name:
        return "claude-code"
    return "generic"


def _visibility(record: dict[str, Any], attrs: dict[str, Any]) -> str:
    value: Any = record.get("visibility", attrs.get("lean_audit.visibility", "unknown"))
    if isinstance(value, bool):
        return "model" if value else "out-of-band"
    normalized = str(value).strip().lower()
    if normalized in {"model", "model-visible", "visible", "in-band"}:
        return "model"
    if normalized in {"out-of-band", "external", "telemetry", "file"}:
        return "out-of-band"
    return "unknown"


def _usage_or_attr(
    usage: dict[str, Any],
    attrs: dict[str, Any],
    usage_names: tuple[str, ...],
    attr_names: tuple[str, ...],
) -> int:
    return _int_value(usage, *usage_names) or _int_value(attrs, *attr_names)


def _one_event(record: dict[str, Any], index: int) -> UsageEvent | None:
    attrs = _attributes(record)
    usage = _find_mapping(record, ("usage", "token_usage", "tokenUsage"))

    input_tokens = _usage_or_attr(
        usage,
        attrs,
        ("input_tokens", "inputTokens", "prompt_tokens", "promptTokens"),
        ("gen_ai.usage.input_tokens", "llm.token_count.prompt"),
    )
    output_tokens = _usage_or_attr(
        usage,
        attrs,
        ("output_tokens", "outputTokens", "completion_tokens", "completionTokens"),
        ("gen_ai.usage.output_tokens", "llm.token_count.completion"),
    )

    input_details = usage.get("input_tokens_details")
    if not isinstance(input_details, dict):
        input_details = {}
    output_details = usage.get("output_tokens_details")
    if not isinstance(output_details, dict):
        output_details = {}

    cached = (
        _int_value(usage, "cached_input_tokens", "cache_read_input_tokens", "cacheReadInputTokens")
        or _int_value(input_details, "cached_tokens", "cachedTokens")
        or _int_value(attrs, "gen_ai.usage.cache_read.input_tokens")
    )
    cache_write = (
        _int_value(
            usage,
            "cache_write_tokens",
            "cache_creation_input_tokens",
            "cacheCreationInputTokens",
        )
        or _int_value(input_details, "cache_write_tokens", "cacheWriteTokens")
        or _int_value(attrs, "gen_ai.usage.cache_write.input_tokens")
    )
    reasoning = (
        _int_value(usage, "reasoning_tokens", "reasoningTokens")
        or _int_value(output_details, "reasoning_tokens", "reasoningTokens")
        or _int_value(attrs, "gen_ai.usage.reasoning_tokens")
    )
    tool_result = _int_value(record, "tool_result_tokens", "result_tokens") or _int_value(
        attrs,
        "tool.result_tokens",
        "tool_result_tokens",
        "claude_code.tool.result_tokens",
        "codex.tool.result_tokens",
    )
    total = _int_value(usage, "total_tokens", "totalTokens") or input_tokens + output_tokens
    if not any((input_tokens, output_tokens, cached, cache_write, reasoning, tool_result, total)):
        return None

    stage = _text_value(record, "stage", default="unknown")
    if stage == "unknown":
        stage = _text_value(attrs, "lean_audit.stage", "workflow.stage", default="unknown")
    actor = _text_value(record, "actor", "subagent_id", "agent_id", default="unknown")
    if actor == "unknown":
        actor = _text_value(
            attrs,
            "lean_audit.actor",
            "gen_ai.agent.id",
            "subagent.id",
            default="unknown",
        )
    event_id = _text_value(record, "id", "event_id", "span_id", default=str(index))
    return UsageEvent(
        event_id=event_id,
        adapter=_adapter(record, usage, attrs),
        stage=stage,
        actor=actor,
        visibility=_visibility(record, attrs),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached,
        cache_write_tokens=cache_write,
        reasoning_tokens=reasoning,
        tool_result_tokens=tool_result,
        total_tokens=total,
    )


def normalize_trace_records(records: list[dict[str, Any]]) -> list[UsageEvent]:
    """Normalize records to metadata-only events; ignore records without usage."""
    events = []
    for index, record in enumerate(records):
        event = _one_event(record, index)
        if event is not None:
            events.append(event)
    return events


def read_trace_file(path: Path) -> list[dict[str, Any]]:
    """Read a JSON object/list or JSONL trace without interpreting content fields."""
    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            nested = payload.get("events")
            records = nested if isinstance(nested, list) else [payload]
        else:
            raise ValueError(f"{path}: trace must contain JSON objects")
    if not all(isinstance(record, dict) for record in records):
        raise ValueError(f"{path}: every trace record must be an object")
    return records


def summarize_trace(events: list[UsageEvent]) -> dict[str, Any]:
    """Aggregate normalized metadata. Raw prompts and tool output never enter it."""
    totals: dict[str, Any] = {
        "event_count": len(events),
        "input_tokens": sum(event.input_tokens for event in events),
        "output_tokens": sum(event.output_tokens for event in events),
        "cached_input_tokens": sum(event.cached_input_tokens for event in events),
        "cache_write_tokens": sum(event.cache_write_tokens for event in events),
        "reasoning_tokens": sum(event.reasoning_tokens for event in events),
        "total_tokens": sum(event.total_tokens for event in events),
    }
    totals.update(
        {
            f"{label}_tool_result_tokens": sum(
                event.tool_result_tokens for event in events if event.visibility == visibility
            )
            for visibility, label in (
                ("model", "model_visible"),
                ("out-of-band", "out_of_band"),
                ("unknown", "unknown_visibility"),
            )
        }
    )
    by_adapter: dict[str, int] = {}
    by_stage: dict[str, int] = {}
    for event in events:
        by_adapter[event.adapter] = by_adapter.get(event.adapter, 0) + event.total_tokens
        by_stage[event.stage] = by_stage.get(event.stage, 0) + event.total_tokens
    totals["by_adapter"] = dict(sorted(by_adapter.items()))
    totals["by_stage"] = dict(sorted(by_stage.items()))
    totals["content_policy"] = "metadata-only"
    return totals
